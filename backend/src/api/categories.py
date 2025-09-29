"""
Category management API endpoints.
Provides CRUD operations for hierarchical component categories.
"""

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from ..auth.dependencies import require_auth
from ..database import get_db
from ..models.category import Category
from ..models.component import Component

router = APIRouter(prefix="/api/v1/categories", tags=["categories"])


class CategoryCreate(BaseModel):
    """Request model for creating a new category."""

    name: str = Field(..., min_length=1, max_length=100, description="Category name")
    description: str | None = Field(None, description="Optional category description")
    parent_id: str | None = Field(None, description="Parent category ID for hierarchy")
    color: str | None = Field(
        None, pattern="^#[0-9A-Fa-f]{6}$", description="Hex color code"
    )
    icon: str | None = Field(None, max_length=50, description="Icon identifier")
    sort_order: int = Field(0, description="Sort order within parent category")


class CategoryUpdate(BaseModel):
    """Request model for updating an existing category."""

    name: str | None = Field(
        None, min_length=1, max_length=100, description="Category name"
    )
    description: str | None = Field(None, description="Category description")
    parent_id: str | None = Field(None, description="Parent category ID for hierarchy")
    color: str | None = Field(
        None, pattern="^#[0-9A-Fa-f]{6}$", description="Hex color code"
    )
    icon: str | None = Field(None, max_length=50, description="Icon identifier")
    sort_order: int | None = Field(
        None, description="Sort order within parent category"
    )


class CategoryResponse(BaseModel):
    """Response model for category data."""

    id: str
    name: str
    description: str | None = None
    parent_id: str | None = None
    color: str | None = None
    icon: str | None = None
    sort_order: int
    created_at: str
    updated_at: str
    component_count: int = 0
    children_count: int = 0
    full_path_names: list[str] = []
    breadcrumb: str = ""
    depth: int = 0

    class Config:
        from_attributes = True


class CategoryTreeResponse(BaseModel):
    """Response model for hierarchical category tree."""

    id: str
    name: str
    description: str | None = None
    color: str | None = None
    icon: str | None = None
    component_count: int = 0
    children: list["CategoryTreeResponse"] = []
    breadcrumb: str = ""
    depth: int = 0

    class Config:
        from_attributes = True


# Fix forward reference
CategoryTreeResponse.model_rebuild()


class ComponentSummary(BaseModel):
    """Summary model for components in category listings."""

    id: str
    name: str
    part_number: str
    manufacturer: str | None = None
    component_type: str | None = None
    value: str | None = None
    package: str | None = None
    quantity_on_hand: int = 0

    class Config:
        from_attributes = True


class CategoryComponentsResponse(BaseModel):
    """Response model for category components listing."""

    category: CategoryResponse
    components: list[ComponentSummary]
    total_count: int


def category_to_response(category: Category) -> CategoryResponse:
    """Convert Category model to response format."""
    return CategoryResponse(
        id=category.id,
        name=category.name,
        description=category.description,
        parent_id=category.parent_id,
        color=category.color,
        icon=category.icon,
        sort_order=category.sort_order,
        created_at=category.created_at.isoformat(),
        updated_at=category.updated_at.isoformat(),
        component_count=category.get_component_count(include_children=False),
        children_count=len(category.children),
        full_path_names=category.full_path_names,
        breadcrumb=category.breadcrumb,
        depth=category.depth,
    )


def category_to_tree_response(category: Category) -> CategoryTreeResponse:
    """Convert Category model to tree response format."""
    return CategoryTreeResponse(
        id=category.id,
        name=category.name,
        description=category.description,
        color=category.color,
        icon=category.icon,
        component_count=category.get_component_count(include_children=True),
        children=[category_to_tree_response(child) for child in category.children],
        breadcrumb=category.breadcrumb,
        depth=category.depth,
    )


@router.get("", response_model=list[CategoryTreeResponse])
def get_categories(
    hierarchy: bool = Query(True, description="Return hierarchical tree structure"),
    include_empty: bool = Query(
        True, description="Include categories with no components"
    ),
    db: Session = Depends(get_db),
):
    """
    Get all categories with hierarchy display.
    T150: GET /api/v1/categories endpoint with hierarchy display
    """
    if hierarchy:
        # Get root categories (no parent) and build tree
        root_categories = (
            db.query(Category)
            .filter(Category.parent_id.is_(None))
            .order_by(Category.sort_order, Category.name)
            .all()
        )

        categories_tree = []
        for category in root_categories:
            if include_empty or category.get_component_count(include_children=True) > 0:
                categories_tree.append(category_to_tree_response(category))

        return categories_tree
    else:
        # Return flat list
        categories = db.query(Category).order_by(Category.name).all()

        if not include_empty:
            categories = [
                cat
                for cat in categories
                if cat.get_component_count(include_children=False) > 0
            ]

        return [category_to_tree_response(cat) for cat in categories]


@router.post("", response_model=CategoryResponse, status_code=201)
def create_category(
    category_data: CategoryCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_auth),
):
    """
    Create a new category.
    T151: POST /api/v1/categories endpoint for creating categories
    """
    # Validate parent category exists if specified
    if category_data.parent_id:
        parent = (
            db.query(Category).filter(Category.id == category_data.parent_id).first()
        )
        if not parent:
            raise HTTPException(status_code=404, detail="Parent category not found")

    # Check for duplicate name within the same parent
    existing = (
        db.query(Category)
        .filter(
            Category.name == category_data.name,
            Category.parent_id == category_data.parent_id,
        )
        .first()
    )

    if existing:
        raise HTTPException(
            status_code=409,
            detail=f"Category '{category_data.name}' already exists in this parent category",
        )

    # Create new category
    category = Category(
        id=str(uuid.uuid4()),
        name=category_data.name,
        description=category_data.description,
        parent_id=category_data.parent_id,
        color=category_data.color,
        icon=category_data.icon,
        sort_order=category_data.sort_order,
    )

    db.add(category)
    db.commit()
    db.refresh(category)

    return category_to_response(category)


@router.get("/{category_id}", response_model=CategoryResponse)
def get_category(category_id: str, db: Session = Depends(get_db)):
    """
    Get category details with component count.
    T152: GET /api/v1/categories/{id} endpoint with component count
    """
    # Validate UUID format
    try:
        uuid.UUID(category_id)
    except ValueError:
        raise HTTPException(status_code=422, detail="Invalid category ID format")

    category = db.query(Category).filter(Category.id == category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")

    return category_to_response(category)


@router.put("/{category_id}", response_model=CategoryResponse)
def update_category(
    category_id: str,
    category_data: CategoryUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(require_auth),
):
    """
    Update an existing category.
    T153: PUT /api/v1/categories/{id} endpoint for updating categories
    """
    # Validate UUID format
    try:
        uuid.UUID(category_id)
    except ValueError:
        raise HTTPException(status_code=422, detail="Invalid category ID format")

    category = db.query(Category).filter(Category.id == category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")

    # Validate parent category exists if specified
    if category_data.parent_id:
        if category_data.parent_id == category_id:
            raise HTTPException(
                status_code=400, detail="Category cannot be its own parent"
            )

        parent = (
            db.query(Category).filter(Category.id == category_data.parent_id).first()
        )
        if not parent:
            raise HTTPException(status_code=404, detail="Parent category not found")

        # Check for circular references
        if category.is_ancestor_of(parent):
            raise HTTPException(
                status_code=400, detail="Cannot move category to its own descendant"
            )

    # Check for duplicate name within the same parent (excluding self)
    if category_data.name:
        existing = (
            db.query(Category)
            .filter(
                Category.name == category_data.name,
                Category.parent_id
                == (
                    category_data.parent_id
                    if category_data.parent_id is not None
                    else category.parent_id
                ),
                Category.id != category_id,
            )
            .first()
        )

        if existing:
            raise HTTPException(
                status_code=409,
                detail=f"Category '{category_data.name}' already exists in this parent category",
            )

    # Update fields
    update_data = category_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(category, field, value)

    db.commit()
    db.refresh(category)

    return category_to_response(category)


@router.delete("/{category_id}", status_code=200)
def delete_category(
    category_id: str,
    reassign_to: str | None = Query(
        None, description="Category ID to reassign components to"
    ),
    force: bool = Query(
        False, description="Force delete even with components (reassign_to required)"
    ),
    db: Session = Depends(get_db),
    current_user=Depends(require_auth),
):
    """
    Delete a category with component reassignment.
    T154: DELETE /api/v1/categories/{id} endpoint with component reassignment
    """
    # Validate UUID format
    try:
        uuid.UUID(category_id)
    except ValueError:
        raise HTTPException(status_code=422, detail="Invalid category ID format")

    category = db.query(Category).filter(Category.id == category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")

    # Check for child categories
    if category.children:
        raise HTTPException(
            status_code=400,
            detail=f"Category has {len(category.children)} child categories. Move or delete them first.",
        )

    # Check for components
    component_count = category.get_component_count(include_children=False)
    if component_count > 0:
        if not force:
            raise HTTPException(
                status_code=400,
                detail=f"Category has {component_count} components. Use force=true and reassign_to parameter to proceed.",
            )

        if not reassign_to:
            raise HTTPException(
                status_code=400,
                detail="reassign_to parameter required when force deleting category with components",
            )

        # Validate reassignment target
        try:
            uuid.UUID(reassign_to)
        except ValueError:
            raise HTTPException(
                status_code=422, detail="Invalid reassign_to category ID format"
            )

        reassign_category = (
            db.query(Category).filter(Category.id == reassign_to).first()
        )
        if not reassign_category:
            raise HTTPException(
                status_code=404, detail="Reassignment target category not found"
            )

        if reassign_to == category_id:
            raise HTTPException(
                status_code=400,
                detail="Cannot reassign components to the same category being deleted",
            )

        # Reassign components
        db.query(Component).filter(Component.category_id == category_id).update(
            {"category_id": reassign_to}
        )

    # Delete the category
    db.delete(category)
    db.commit()

    return {
        "message": "Category deleted successfully",
        "reassigned_components": component_count if component_count > 0 else 0,
        "reassigned_to": reassign_to if reassign_to else None,
    }


@router.get("/{category_id}/components", response_model=CategoryComponentsResponse)
def get_category_components(
    category_id: str,
    include_children: bool = Query(
        False, description="Include components from child categories"
    ),
    limit: int = Query(
        50, ge=1, le=1000, description="Maximum number of components to return"
    ),
    offset: int = Query(0, ge=0, description="Number of components to skip"),
    db: Session = Depends(get_db),
):
    """
    Get components in a category with filtering.
    T155: GET /api/v1/categories/{id}/components endpoint for category filtering
    """
    # Validate UUID format
    try:
        uuid.UUID(category_id)
    except ValueError:
        raise HTTPException(status_code=422, detail="Invalid category ID format")

    category = db.query(Category).filter(Category.id == category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")

    # Build component query
    if include_children:
        # Get all descendant category IDs
        descendant_categories = category.get_all_descendants()
        category_ids = [category.id] + [cat.id for cat in descendant_categories]
        components_query = db.query(Component).filter(
            Component.category_id.in_(category_ids)
        )
    else:
        components_query = db.query(Component).filter(
            Component.category_id == category_id
        )

    # Get total count
    total_count = components_query.count()

    # Apply pagination and get components
    components = (
        components_query.order_by(Component.name).offset(offset).limit(limit).all()
    )

    # Convert to response format
    component_summaries = [
        ComponentSummary(
            id=comp.id,
            name=comp.name,
            part_number=comp.part_number,
            manufacturer=comp.manufacturer,
            component_type=comp.component_type,
            value=comp.value,
            package=comp.package,
            quantity_on_hand=comp.quantity_on_hand,
        )
        for comp in components
    ]

    return CategoryComponentsResponse(
        category=category_to_response(category),
        components=component_summaries,
        total_count=total_count,
    )
