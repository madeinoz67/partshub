"""
Tags API endpoints for component tagging functionality.
"""

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..auth.dependencies import require_auth
from ..database import get_db
from ..models import Tag


# Pydantic schemas
class TagBase(BaseModel):
    name: str
    description: str | None = None
    color: str | None = None


class TagCreate(TagBase):
    pass


class TagUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    color: str | None = None


class TagResponse(TagBase):
    id: str
    is_system_tag: bool = False
    component_count: int = 0
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True


class TagsListResponse(BaseModel):
    tags: list[TagResponse]
    total: int


router = APIRouter(prefix="/api/v1/tags", tags=["tags"])


@router.get("", response_model=TagsListResponse)
def list_tags(
    search: str | None = Query(None, description="Search in tag name"),
    limit: int = Query(100, ge=1, le=200, description="Number of items to return"),
    offset: int = Query(0, ge=0, description="Number of items to skip"),
    db: Session = Depends(get_db),
):
    """List all tags with optional search."""
    query = db.query(Tag)

    if search:
        query = query.filter(Tag.name.ilike(f"%{search}%"))

    # Get total count
    total_count = query.count()

    # Apply pagination
    tags = query.offset(offset).limit(limit).all()

    # Convert to response format
    tag_list = []
    for tag in tags:
        tag_dict = {
            "id": tag.id,
            "name": tag.name,
            "description": tag.description,
            "color": tag.color,
            "is_system_tag": tag.is_system_tag,
            "component_count": len(tag.components),
            "created_at": tag.created_at.isoformat(),
            "updated_at": tag.updated_at.isoformat(),
        }
        tag_list.append(tag_dict)

    return TagsListResponse(tags=tag_list, total=total_count)


@router.post("", response_model=TagResponse, status_code=status.HTTP_201_CREATED)
def create_tag(
    tag: TagCreate, current_user=Depends(require_auth), db: Session = Depends(get_db)
):
    """Create a new tag."""
    # Check if tag with same name already exists
    existing_tag = db.query(Tag).filter(Tag.name == tag.name).first()
    if existing_tag:
        raise HTTPException(
            status_code=409, detail=f"Tag with name '{tag.name}' already exists"
        )

    # Create new tag
    new_tag = Tag(
        id=str(uuid.uuid4()),
        name=tag.name,
        description=tag.description,
        color=tag.color,
    )

    db.add(new_tag)
    db.commit()
    db.refresh(new_tag)

    return {
        "id": new_tag.id,
        "name": new_tag.name,
        "description": new_tag.description,
        "color": new_tag.color,
        "is_system_tag": new_tag.is_system_tag,
        "component_count": 0,
        "created_at": new_tag.created_at.isoformat(),
        "updated_at": new_tag.updated_at.isoformat(),
    }


@router.get("/{tag_id}", response_model=TagResponse)
def get_tag(tag_id: str, db: Session = Depends(get_db)):
    """Get a tag by ID."""
    try:
        uuid.UUID(tag_id)
    except ValueError:
        raise HTTPException(status_code=422, detail="Invalid tag ID format")

    tag = db.query(Tag).filter(Tag.id == tag_id).first()
    if not tag:
        raise HTTPException(status_code=404, detail="Tag not found")

    return {
        "id": tag.id,
        "name": tag.name,
        "description": tag.description,
        "color": tag.color,
        "is_system_tag": tag.is_system_tag,
        "component_count": len(tag.components),
        "created_at": tag.created_at.isoformat(),
        "updated_at": tag.updated_at.isoformat(),
    }


@router.put("/{tag_id}", response_model=TagResponse)
def update_tag(
    tag_id: str,
    tag_update: TagUpdate,
    current_user=Depends(require_auth),
    db: Session = Depends(get_db),
):
    """Update a tag."""
    try:
        uuid.UUID(tag_id)
    except ValueError:
        raise HTTPException(status_code=422, detail="Invalid tag ID format")

    tag = db.query(Tag).filter(Tag.id == tag_id).first()
    if not tag:
        raise HTTPException(status_code=404, detail="Tag not found")

    # Update only provided fields
    update_data = {k: v for k, v in tag_update.model_dump().items() if v is not None}

    if not update_data:
        raise HTTPException(status_code=422, detail="No data provided for update")

    # Check for name conflicts if name is being updated
    if "name" in update_data and update_data["name"] != tag.name:
        existing_tag = db.query(Tag).filter(Tag.name == update_data["name"]).first()
        if existing_tag:
            raise HTTPException(
                status_code=409,
                detail=f"Tag with name '{update_data['name']}' already exists",
            )

    for field, value in update_data.items():
        setattr(tag, field, value)

    db.commit()
    db.refresh(tag)

    return {
        "id": tag.id,
        "name": tag.name,
        "description": tag.description,
        "color": tag.color,
        "is_system_tag": tag.is_system_tag,
        "component_count": len(tag.components),
        "created_at": tag.created_at.isoformat(),
        "updated_at": tag.updated_at.isoformat(),
    }


@router.delete("/{tag_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_tag(
    tag_id: str, current_user=Depends(require_auth), db: Session = Depends(get_db)
):
    """Delete a tag."""
    try:
        uuid.UUID(tag_id)
    except ValueError:
        raise HTTPException(status_code=422, detail="Invalid tag ID format")

    tag = db.query(Tag).filter(Tag.id == tag_id).first()
    if not tag:
        raise HTTPException(status_code=404, detail="Tag not found")

    # Prevent deletion of system tags
    if tag.is_system_tag:
        raise HTTPException(status_code=403, detail="Cannot delete system tags")

    db.delete(tag)
    db.commit()
