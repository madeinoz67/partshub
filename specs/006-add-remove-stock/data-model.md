# Data Model: Stock Management Operations

**Feature**: Add/Remove/Move stock operations from component row expansion menu
**Branch**: 006-add-remove-stock
**Date**: 2025-10-04

## Overview

This document defines the data model changes and extensions required to support inline stock management operations (Add, Remove, Move). The implementation extends existing models (`StockTransaction`, `ComponentLocation`) rather than creating new tables.

---

## 1. StockTransaction Model Extensions

### Purpose
Immutable audit trail for all stock operations with complete traceability, pricing, and lot information.

### Location
`backend/src/models/stock_transaction.py`

### Schema Extensions Required

The existing `StockTransaction` model requires the following field additions to satisfy spec requirements FR-047, FR-048:

| Field | Type | Constraints | Default | Purpose |
|-------|------|-------------|---------|---------|
| `lot_id` | String | nullable=True, max_length=100 | None | Lot/batch identifier for stock tracking |
| `price_per_unit` | Numeric(10, 4) | nullable=True | None | Unit price at time of transaction |
| `total_price` | Numeric(10, 4) | nullable=True | None | Total price for entire transaction |

### Existing Fields (No Changes)

| Field | Type | Constraints | Default | Purpose |
|-------|------|-------------|---------|---------|
| `id` | String (UUID) | primary_key=True | uuid4() | Unique transaction identifier |
| `component_id` | String (UUID) | ForeignKey("components.id"), nullable=False | - | Component being transacted |
| `transaction_type` | Enum(TransactionType) | nullable=False | - | ADD, REMOVE, MOVE, or ADJUST |
| `quantity_change` | Integer | nullable=False | - | Quantity change (+/- or 0 for moves) |
| `previous_quantity` | Integer | nullable=False | - | Total stock before transaction |
| `new_quantity` | Integer | nullable=False | - | Total stock after transaction |
| `reason` | Text | nullable=False | - | Human-readable reason |
| `reference_id` | String | nullable=True | None | External reference (order ID, etc.) |
| `reference_type` | String(50) | nullable=True | None | Type of reference |
| `from_location_id` | String (UUID) | ForeignKey("storage_locations.id"), nullable=True | None | Source location (for moves) |
| `to_location_id` | String (UUID) | ForeignKey("storage_locations.id"), nullable=True | None | Destination location |
| `user_id` | String | nullable=True | None | User who performed transaction |
| `user_name` | String(100) | nullable=True | None | Cached username for history |
| `batch_id` | String | nullable=True | None | Group related transactions |
| `notes` | Text | nullable=True | None | User comments |
| `created_at` | DateTime(timezone=True) | server_default=func.now() | Now | Immutable timestamp |

### Relationships

```python
component = relationship("Component", back_populates="stock_transactions")
from_location = relationship("StorageLocation", foreign_keys=[from_location_id])
to_location = relationship("StorageLocation", foreign_keys=[to_location_id])
```

### Validation Rules

**Transaction Type Constraints:**

| Transaction Type | quantity_change | from_location_id | to_location_id | Notes |
|-----------------|----------------|------------------|----------------|-------|
| ADD | Positive integer | NULL | Required | Adds stock to location |
| REMOVE | Negative integer | Required | NULL | Removes stock from location |
| MOVE | 0 | Required | Required | Transfers between locations |
| ADJUST | Any integer | NULL | Optional | Manual adjustment |

**Pricing Constraints:**
- If `price_per_unit` is set, `total_price` should equal `price_per_unit * abs(quantity_change)`
- If `total_price` is set, `price_per_unit` should equal `total_price / abs(quantity_change)`
- Both fields can be NULL (no pricing information)
- Backend should validate pricing consistency before insertion

**Immutability:**
- No `updated_at` field - transactions are immutable once created
- Use `created_at` with `server_default=func.now()` for automatic timestamping
- Cannot be modified after insertion (append-only audit log)

### State Transitions

**Add Stock Flow:**
```
1. User submits add stock request
2. Acquire pessimistic lock on ComponentLocation
3. Create StockTransaction record:
   - transaction_type = ADD
   - quantity_change = +N (positive)
   - to_location_id = target location
   - lot_id, price_per_unit, total_price from request
4. Update ComponentLocation.quantity_on_hand += N
5. Commit transaction (releases lock)
```

**Remove Stock Flow:**
```
1. User submits remove stock request
2. Acquire pessimistic lock on ComponentLocation
3. Validate: quantity_on_hand >= requested_quantity
4. Auto-cap if requested_quantity > quantity_on_hand (FR-017)
5. Create StockTransaction record:
   - transaction_type = REMOVE
   - quantity_change = -N (negative)
   - from_location_id = source location
6. Update ComponentLocation.quantity_on_hand -= N
7. If quantity_on_hand = 0, delete ComponentLocation record (FR-021)
8. Commit transaction (releases lock)
```

**Move Stock Flow:**
```
1. User submits move stock request
2. Acquire pessimistic locks on BOTH locations (consistent order: lower ID first)
3. Validate: source.quantity_on_hand >= requested_quantity
4. Auto-cap if requested_quantity > source.quantity_on_hand (FR-029)
5. Create StockTransaction record:
   - transaction_type = MOVE
   - quantity_change = 0 (no net change)
   - from_location_id = source location
   - to_location_id = destination location
   - Copy lot_id, price_per_unit from source (FR-034)
6. Update source.quantity_on_hand -= N
7. If destination exists: destination.quantity_on_hand += N
8. Else: Create new ComponentLocation with quantity = N, inherit pricing (FR-036)
9. If source.quantity_on_hand = 0, delete source ComponentLocation (FR-035)
10. Commit transaction (releases locks)
```

---

## 2. ComponentLocation Table

### Purpose
Junction table tracking component quantities across multiple storage locations with pessimistic locking support.

### Location
`backend/src/models/component_location.py`

### Schema (No Changes Required)

| Field | Type | Constraints | Default | Purpose |
|-------|------|-------------|---------|---------|
| `id` | String (UUID) | primary_key=True | uuid4() | Unique record identifier |
| `component_id` | String (UUID) | ForeignKey("components.id"), nullable=False, index=True | - | Component reference |
| `storage_location_id` | String (UUID) | ForeignKey("storage_locations.id"), nullable=False, index=True | - | Location reference |
| `quantity_on_hand` | Integer | nullable=False | 0 | Current stock quantity |
| `quantity_ordered` | Integer | nullable=False | 0 | Quantity on order |
| `minimum_stock` | Integer | nullable=False | 0 | Low stock threshold |
| `location_notes` | Text | nullable=True | None | Location-specific notes |
| `unit_cost_at_location` | Numeric(10, 4) | nullable=True | None | Location-specific unit cost |
| `created_at` | DateTime(timezone=True) | server_default=func.now() | Now | Creation timestamp |
| `updated_at` | DateTime(timezone=True) | server_default=func.now(), onupdate=func.now() | Now | Last update timestamp |

### Relationships

```python
component = relationship("Component", back_populates="locations")
storage_location = relationship("StorageLocation", back_populates="component_locations")
```

### Table Constraints

```python
__table_args__ = (
    UniqueConstraint("component_id", "storage_location_id", name="uq_component_location"),
)
```

### Pessimistic Locking Strategy

**Lock Acquisition Pattern (FR-041, FR-042):**

```python
from sqlalchemy import select

# Single location lock (Add/Remove operations)
stmt = (
    select(ComponentLocation)
    .where(
        ComponentLocation.component_id == component_id,
        ComponentLocation.storage_location_id == location_id
    )
    .with_for_update(nowait=False)  # Blocking mode
)
location = db.execute(stmt).scalar_one_or_none()

# Dual location lock (Move operations) - ALWAYS lock in consistent order
lock_order = sorted([source_location_id, destination_location_id])

stmt1 = select(ComponentLocation).where(...).with_for_update(nowait=False)
stmt2 = select(ComponentLocation).where(...).with_for_update(nowait=False)

loc1 = db.execute(stmt1).scalar_one_or_none()
loc2 = db.execute(stmt2).scalar_one_or_none()
```

**Lock Behavior:**
- **Duration**: Lock held for entire transaction scope
- **Type**: Row-level exclusive lock (SQLite uses BEGIN IMMEDIATE)
- **Mode**: `nowait=False` - Block and wait for lock (not immediate failure)
- **Timeout**: Backend should configure reasonable timeout (e.g., 10 seconds)
- **Release**: Automatic on commit or rollback (FR-043)
- **Conflict**: Return HTTP 409 Conflict if lock timeout exceeded (FR-044)

**Deadlock Prevention:**
- Always acquire locks in consistent order (sorted by location ID)
- Use shortest possible transaction scope
- Release locks immediately after operation completes

### Validation Rules

**Quantity Constraints:**
- `quantity_on_hand` must always be >= 0 (non-negative)
- Backend validates before decrement operations
- Auto-cap removal/move quantities if exceeding available (FR-017, FR-029)

**Location Lifecycle:**
- Create ComponentLocation when first adding stock to location
- Delete ComponentLocation when quantity_on_hand reaches 0 (FR-021, FR-035)
- Never allow negative `quantity_on_hand`

**Pricing Inheritance (FR-034):**
- When moving stock, copy `unit_cost_at_location` from source to destination
- If destination already exists, preserve existing pricing (don't overwrite)
- New locations inherit source pricing

---

## 3. Stock Operation Atomicity

### Atomicity Requirements (FR-033)

All stock operations must be atomic (all-or-nothing):

**Database Transaction Scope:**
```python
try:
    # 1. Acquire lock(s)
    # 2. Validate quantities
    # 3. Create StockTransaction audit record
    # 4. Update ComponentLocation(s)
    # 5. Handle zero-quantity cleanup
    db.commit()  # All succeed
except Exception:
    db.rollback()  # All fail
    raise
```

**Multi-Location Operations (Move):**
- BOTH source decrement AND destination increment must succeed
- If destination creation fails, source decrement must rollback
- StockTransaction creation must succeed for audit trail
- Lock both locations before ANY modifications

### Validation Order

**Pre-Operation Validation:**
1. Authenticate user (admin only - FR-051)
2. Validate component exists
3. Validate location(s) exist
4. Acquire lock(s) on ComponentLocation(s)
5. Validate sufficient quantity (with auto-capping)
6. Validate source != destination (for moves - FR-031)

**Post-Operation Actions:**
1. Create StockTransaction audit record
2. Update ComponentLocation quantities
3. Clean up zero-quantity locations
4. Commit transaction
5. Release locks automatically

---

## 4. Data Access Patterns

### Query Patterns

**Fetch Component Stock History:**
```python
from sqlalchemy import select, desc

stmt = (
    select(StockTransaction)
    .where(StockTransaction.component_id == component_id)
    .order_by(desc(StockTransaction.created_at))
    .limit(50)
)
transactions = db.execute(stmt).scalars().all()
```

**Fetch Component Locations:**
```python
stmt = (
    select(ComponentLocation)
    .where(ComponentLocation.component_id == component_id)
    .options(joinedload(ComponentLocation.storage_location))
)
locations = db.execute(stmt).scalars().all()
```

**Lock and Update Pattern:**
```python
# Pessimistic lock for update
stmt = (
    select(ComponentLocation)
    .where(
        ComponentLocation.component_id == component_id,
        ComponentLocation.storage_location_id == location_id
    )
    .with_for_update(nowait=False)
)

location = db.execute(stmt).scalar_one_or_none()

if location:
    location.quantity_on_hand += quantity_change
    location.updated_at = func.now()  # Explicit update timestamp
```

### Indexing Considerations

**Existing Indexes:**
- `component_locations.component_id` (indexed)
- `component_locations.storage_location_id` (indexed)
- `uq_component_location` unique constraint (component_id, storage_location_id)

**Recommended Additional Indexes:**
```python
# StockTransaction queries by component
Index('ix_stock_transactions_component_id', StockTransaction.component_id)

# StockTransaction queries by date range
Index('ix_stock_transactions_created_at', StockTransaction.created_at)

# Composite index for component history queries
Index('ix_stock_transactions_component_created',
      StockTransaction.component_id,
      StockTransaction.created_at.desc())
```

---

## 5. Migration Requirements

### Database Migration (Alembic)

**Add Fields to StockTransaction:**
```python
# alembic/versions/XXX_add_lot_pricing_to_stock_transactions.py

def upgrade():
    op.add_column('stock_transactions',
                  sa.Column('lot_id', sa.String(length=100), nullable=True))
    op.add_column('stock_transactions',
                  sa.Column('price_per_unit', sa.Numeric(precision=10, scale=4), nullable=True))
    op.add_column('stock_transactions',
                  sa.Column('total_price', sa.Numeric(precision=10, scale=4), nullable=True))

def downgrade():
    op.drop_column('stock_transactions', 'total_price')
    op.drop_column('stock_transactions', 'price_per_unit')
    op.drop_column('stock_transactions', 'lot_id')
```

**No Changes Required:**
- ComponentLocation schema is already complete
- Pessimistic locking uses existing SQLAlchemy features

---

## 6. Testing Considerations

### Model Testing

**StockTransaction Tests:**
- Test immutability (cannot update after creation)
- Test quantity_change sign conventions (+/- for ADD/REMOVE, 0 for MOVE)
- Test pricing validation (consistency between unit and total price)
- Test relationship loading (component, from_location, to_location)

**ComponentLocation Tests:**
- Test pessimistic locking (with_for_update blocks concurrent access)
- Test unique constraint (component_id, storage_location_id)
- Test quantity validation (non-negative constraint)
- Test zero-quantity cleanup lifecycle

**Transaction Tests:**
- Test atomic rollback on failure
- Test lock release on commit/rollback
- Test deadlock prevention (consistent lock ordering)
- Test concurrent operation blocking

### Test Data Requirements

**Minimal Test Setup:**
```python
# Component
component = Component(id=uuid4(), name="Test Resistor")

# Storage Locations
location_A = StorageLocation(id=uuid4(), name="Shelf A")
location_B = StorageLocation(id=uuid4(), name="Shelf B")

# Component Location (initial stock)
comp_location = ComponentLocation(
    component_id=component.id,
    storage_location_id=location_A.id,
    quantity_on_hand=100,
    unit_cost_at_location=0.50
)

# Admin User
admin = User(id=uuid4(), username="admin", role="admin")
```

---

## Summary

### Key Changes
1. **StockTransaction Extensions**: Add `lot_id`, `price_per_unit`, `total_price` fields
2. **No ComponentLocation Changes**: Existing schema sufficient
3. **Pessimistic Locking**: Use `with_for_update(nowait=False)` on ComponentLocation
4. **Atomic Operations**: All stock changes in single database transaction
5. **Zero Cleanup**: Delete ComponentLocation when quantity_on_hand = 0

### Critical Validation Rules
- Quantity changes must maintain non-negative `quantity_on_hand`
- Auto-cap removal/move quantities exceeding available stock
- Pessimistic locks prevent concurrent modifications
- StockTransaction records are immutable (audit trail)
- Move operations require consistent lock ordering to prevent deadlocks

### State Transition Summary
- **Add**: Lock destination → Create transaction → Increment quantity → Commit
- **Remove**: Lock source → Validate → Create transaction → Decrement → Cleanup if zero → Commit
- **Move**: Lock both (ordered) → Validate → Create transaction → Decrement source → Increment/create destination → Cleanup if zero → Commit

---

**Document Status**: Complete
**Last Updated**: 2025-10-04
