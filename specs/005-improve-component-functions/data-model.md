# Data Model: Component Bulk Operations

## Entity Diagram

```
┌─────────────────┐
│   Component     │◄──────┐
│─────────────────│       │
│ id: int (PK)    │       │
│ part_number: str│       │
│ description: str│       │
│ version: int    │       │ Many-to-Many
│ ...existing...  │       │
└─────────────────┘       │
                          │
                    ┌─────┴──────┐
                    │ ComponentTag│
                    │─────────────│
                    │ component_id│
                    │ tag_id      │
                    └─────┬──────┘
                          │
┌─────────────────┐       │
│      Tag        │◄──────┘
│─────────────────│
│ id: int (PK)    │
│ name: str       │
│ type: str       │ (user/auto)
└─────────────────┘

┌─────────────────┐
│    Project      │
│─────────────────│
│ id: int (PK)    │
│ name: str       │
│ description: str│
└─────────────────┘
         ▲
         │ Many-to-Many
         │
┌────────┴────────┐
│ ProjectComponent│
│─────────────────│
│ project_id      │
│ component_id    │
│ quantity: int   │
└─────────────────┘

┌──────────────────────┐
│   BulkOperation      │ (Transient - Not Persisted)
│──────────────────────│
│ operation_type: enum │
│ component_ids: List  │
│ parameters: Dict     │
│ status: enum         │
│ errors: List[Error]  │
└──────────────────────┘

┌──────────────────────┐
│   SelectionState     │ (Frontend Only - localStorage)
│──────────────────────│
│ selectedIds: Set<int>│
└──────────────────────┘
```

## Existing Entities (No Schema Changes)

### Component
**Table**: `components`
**Purpose**: Represents an electronic component in inventory

**Schema**:
```python
class Component(Base):
    __tablename__ = "components"

    id: int                    # Primary key
    part_number: str          # Unique identifier
    description: str          # Component description
    footprint: str | None     # Physical package type
    stock: int                # Current inventory count
    manufacturer: str | None  # Manufacturer name
    mpn: str | None          # Manufacturer part number
    location: str | None     # Storage location
    version: int             # Optimistic concurrency control (NEW)
    created_at: datetime
    updated_at: datetime

    # Relationships
    tags: List[Tag]          # Many-to-many via ComponentTag
    projects: List[Project]  # Many-to-many via ProjectComponent
```

**Validation Rules**:
- `part_number` must be unique
- `stock` must be >= 0
- `version` incremented on each update (for concurrency control)

**State Transitions**: None (CRUD only)

### Project
**Table**: `projects`
**Purpose**: Container for grouping components

**Schema**:
```python
class Project(Base):
    __tablename__ = "projects"

    id: int
    name: str               # Unique project name
    description: str | None
    created_at: datetime
    updated_at: datetime

    # Relationships
    components: List[Component]  # Many-to-many via ProjectComponent
```

**Validation Rules**:
- `name` must be unique
- `name` length: 1-200 characters

### Tag
**Table**: `tags`
**Purpose**: Label for component categorization

**Schema**:
```python
class Tag(Base):
    __tablename__ = "tags"

    id: int
    name: str              # Tag text
    type: str              # 'user' or 'auto'
    created_at: datetime

    # Relationships
    components: List[Component]  # Many-to-many via ComponentTag
```

**Validation Rules**:
- `name` must be unique within `type`
- `type` must be 'user' or 'auto'
- `name` length: 1-50 characters

## New/Modified Entities

### Component (Schema Modification)
**Change**: Add `version` column for optimistic concurrency control

```python
version: int = Column(Integer, nullable=False, default=1)
__mapper_args__ = {"version_id_col": version}
```

**Migration**: Alembic migration to add column with default value 1

### BulkOperation (Transient - Not Persisted)
**Purpose**: Encapsulates a bulk operation request/response

**Schema** (Pydantic):
```python
class BulkOperationRequest(BaseModel):
    operation_type: BulkOperationType
    component_ids: List[int]  # 1-1000 components
    parameters: Dict[str, Any]  # Operation-specific params

class BulkOperationType(str, Enum):
    ADD_TAGS = "add_tags"
    REMOVE_TAGS = "remove_tags"
    ASSIGN_PROJECT = "assign_project"
    DELETE = "delete"
    ADD_META_PART = "add_meta_part"
    ADD_PURCHASE_LIST = "add_purchase_list"
    SET_LOW_STOCK = "set_low_stock"
    SET_ATTRIBUTION = "set_attribution"

class BulkOperationResponse(BaseModel):
    success: bool
    affected_count: int
    errors: List[BulkOperationError] | None

class BulkOperationError(BaseModel):
    component_id: int
    component_name: str
    error_message: str
    error_type: str  # 'not_found', 'concurrent_modification', 'validation', etc.
```

**Validation Rules**:
- `component_ids` length: 1-1000
- All `component_ids` must exist
- `parameters` validated per operation type

**Operation-Specific Parameters**:

**ADD_TAGS / REMOVE_TAGS**:
```python
{
    "tags": List[str]  # Tag names to add/remove
}
```

**ASSIGN_PROJECT**:
```python
{
    "project_id": int,
    "quantities": Dict[int, int]  # component_id -> quantity
}
```

**DELETE**: No parameters

**ADD_META_PART**:
```python
{
    "meta_part_name": str
}
```

**ADD_PURCHASE_LIST**:
```python
{
    "purchase_list_id": int
}
```

**SET_LOW_STOCK**:
```python
{
    "threshold": int
}
```

**SET_ATTRIBUTION**:
```python
{
    "attribution_data": Dict[str, str]
}
```

### SelectionState (Frontend Only)
**Purpose**: Persistent selection state across navigation

**Storage**: Browser localStorage via Pinia plugin

**Schema** (TypeScript):
```typescript
interface SelectionState {
  selectedIds: Set<number>;  // Component IDs
  lastUpdated: Date;
}

interface SelectionStore {
  state: SelectionState;

  // Actions
  addSelection(ids: number[]): void;
  removeSelection(ids: number[]): void;
  toggleSelection(id: number): void;
  selectAll(ids: number[]): void;
  clearSelection(): void;

  // Getters
  hasSelection: boolean;
  selectedCount: number;
  isSelected(id: number): boolean;
}
```

**Persistence Strategy**:
- Auto-save to localStorage on any state mutation
- Auto-load from localStorage on store initialization
- Clear on explicit "Deselect all" action
- Survives page navigation and browser refresh

**Validation Rules**:
- `selectedIds` can contain IDs for components not currently visible (cross-page selection)
- Stale IDs (deleted components) removed on next component list fetch

## Junction Tables (Existing)

### ComponentTag
**Table**: `component_tags`
```python
class ComponentTag(Base):
    __tablename__ = "component_tags"

    component_id: int  # FK to components.id
    tag_id: int        # FK to tags.id

    __table_args__ = (
        PrimaryKeyConstraint('component_id', 'tag_id'),
    )
```

### ProjectComponent
**Table**: `project_components`
```python
class ProjectComponent(Base):
    __tablename__ = "project_components"

    project_id: int    # FK to projects.id
    component_id: int  # FK to components.id
    quantity: int      # Quantity in project

    __table_args__ = (
        PrimaryKeyConstraint('project_id', 'component_id'),
    )
```

## Database Constraints

### Integrity Constraints
- All foreign keys have `ON DELETE CASCADE`
- `version` column on Component increments on any UPDATE
- Unique constraint on (component_id, tag_id) in ComponentTag
- Unique constraint on (project_id, component_id) in ProjectComponent

### Transaction Isolation
- Bulk operations use `READ COMMITTED` isolation level
- Version check prevents lost updates (optimistic locking)
- Rollback on any operation failure within batch

## Performance Considerations

### Indexing Strategy
```sql
-- Existing indexes
CREATE INDEX idx_components_part_number ON components(part_number);
CREATE INDEX idx_component_tags_component_id ON component_tags(component_id);
CREATE INDEX idx_component_tags_tag_id ON component_tags(tag_id);
CREATE INDEX idx_project_components_project_id ON project_components(project_id);
CREATE INDEX idx_project_components_component_id ON project_components(component_id);

-- New index for version-based queries
CREATE INDEX idx_components_version ON components(version);
```

### Query Optimization
- Use `selectinload` for tag/project relationships in bulk operations
- Batch INSERT/DELETE for junction table operations
- Chunk large bulk operations (>1000 components) into multiple transactions

### Data Volume Estimates
- Components: 1K-100K rows
- Tags: 100-1K rows
- Projects: 10-100 rows
- ComponentTag: 10K-1M rows (avg 10 tags/component)
- ProjectComponent: 1K-10K rows

## Migration Plan

### Alembic Migration: Add Version Column
```python
"""Add version column to components for optimistic locking

Revision ID: 20251004_1200
"""

def upgrade():
    op.add_column('components',
        sa.Column('version', sa.Integer(), nullable=False, server_default='1')
    )
    op.create_index('idx_components_version', 'components', ['version'])

def downgrade():
    op.drop_index('idx_components_version', table_name='components')
    op.drop_column('components', 'version')
```

**Rollout Strategy**:
1. Add column with default value (non-breaking)
2. Deploy backend with version support
3. Monitor for concurrent modification errors
4. No data migration needed (default value sufficient)

## API Contract Alignment

All entities map to request/response schemas:
- `Component` → `ComponentSchema` (existing)
- `Project` → `ProjectSchema` (existing)
- `Tag` → `TagSchema` (existing)
- `BulkOperationRequest` → POST request bodies
- `BulkOperationResponse` → API responses
- `SelectionState` → Frontend store only (not exposed to API)
