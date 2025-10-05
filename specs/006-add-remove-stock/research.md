# Stock Management Operations - Technical Research

**Feature**: Add/Remove/Move stock operations from component row expansion menu
**Branch**: 006-add-remove-stock
**Date**: 2025-10-04

## Overview

This document captures technical decisions and implementation patterns for adding inline stock management operations (Add, Remove, Move) to the component row expansion menu in ComponentList.vue.

---

## 1. Inline Form Rendering in Vue 3 + Quasar

### Decision

Use Vue 3's reactive ref-based state management with component-scoped form state, rendering forms directly within the expanded row's content area using Quasar's native form components (QInput, QSelect, QBtn). Forms will be conditionally rendered based on the active tab for each component row.

### Rationale

- **Existing Pattern**: ComponentList.vue already implements inline expansion with tab-based navigation (lines 370-945), providing a proven pattern for displaying different content types (info, images, stock, etc.) within expanded rows
- **Tab-Based UI**: The current implementation uses `activeTab` ref (line 1185) to track which tab is active per component ID, with menu items for "Add Stock", "Remove Stock", and "Move Stock" already in place (lines 414-439)
- **No Modal Overhead**: Inline forms avoid the complexity of modal state management, dialog positioning, and multiple dialog instances
- **Scoped State**: Each expanded row maintains its own form state, preventing interference between multiple open forms
- **Native Quasar Integration**: Leverages existing Quasar form components (QInput, QSelect, QBtn) already used throughout the application

### Alternatives Considered

1. **Modal Dialogs** (TagManagementDialog.vue pattern)
   - Rejected: Spec explicitly requires inline forms within expanded rows, not modal dialogs
   - Overhead: Additional complexity managing dialog visibility, z-index, and backdrop

2. **Separate Route/Page**
   - Rejected: Poor UX for quick stock operations; user loses context of component list
   - Navigation overhead: Requires back/forth navigation and state preservation

3. **Slide-out Panels**
   - Rejected: More complex to implement than inline tabs
   - Accessibility concerns: Harder to manage focus and keyboard navigation

### Implementation Notes

**Key Patterns from Existing Code:**

1. **Component-Scoped State Management** (ComponentList.vue, lines 1185-1399):
```typescript
const activeTab = ref<Record<string, string>>({}) // Tab state per component ID

const setActiveTab = (componentId: string, tab: string) => {
  activeTab.value[componentId] = tab
}

const getActiveTab = (componentId: string) => {
  return activeTab.value[componentId] || 'info'
}
```

2. **Inline Content Rendering** (ComponentList.vue, lines 462-941):
```vue
<div class="col" style="padding: 16px; background: #ffffff;">
  <div v-if="getActiveTab(props.row.id) === 'info'">
    <!-- Part Info Content -->
  </div>
  <div v-else-if="getActiveTab(props.row.id) === 'add-stock'">
    <!-- Add Stock Form (to be implemented) -->
  </div>
</div>
```

3. **Form State Per Component**:
   - Create refs for form data scoped by component ID (e.g., `formState.value[componentId]`)
   - Initialize form state when tab becomes active
   - Clear form state on successful submission or cancellation

4. **Validation**:
   - Use Quasar's built-in form validation with `:rules` prop
   - Validate before submission to prevent invalid API calls
   - Display validation errors inline with form fields

**Critical Gotchas:**

- **Memory Leaks**: Clean up form state when component rows are collapsed or removed from the list
- **Reactivity**: Use Vue 3's ref/reactive properly; avoid direct object mutation
- **Multiple Instances**: Ensure form state is properly isolated between different component rows
- **Tab Switching**: Decide whether to preserve or clear form data when user switches tabs (recommend clearing for safety)

---

## 2. SQLAlchemy Pessimistic Locking

### Decision

Use SQLAlchemy's `with_for_update()` method with `nowait=False` (blocking mode) to acquire row-level pessimistic locks on ComponentLocation records during stock operations.

### Rationale

- **Data Integrity**: Prevents race conditions when multiple admins modify the same component/location simultaneously
- **Spec Requirement**: FR-041 explicitly requires pessimistic locking: "System MUST acquire a lock on the affected component/location before executing any stock operation"
- **Blocking Behavior**: `nowait=False` allows the second user to wait for the lock rather than immediately failing, providing better UX
- **Proven Pattern**: SQLite supports row-level locking via `BEGIN IMMEDIATE` transactions, which SQLAlchemy's `with_for_update()` utilizes
- **Existing Infrastructure**: Project already uses SQLAlchemy ORM and in-memory SQLite for testing (backend/tests/conftest.py)

### Alternatives Considered

1. **Optimistic Locking** (existing Component model uses this, line 89-92)
   - Rejected: Optimistic locking detects conflicts after they occur; spec requires preventing conflicts
   - Current implementation uses `version` column for detecting concurrent modifications to Component records
   - Not suitable for stock operations where we need to prevent concurrent access, not just detect it

2. **Application-Level Locking** (Redis/Memcached)
   - Rejected: Adds external dependency for a problem SQLAlchemy already solves
   - Overhead: Requires additional infrastructure, deployment complexity

3. **Database-Level Advisory Locks**
   - Rejected: Not portable across database backends; SQLite has limited support
   - SQLAlchemy's `with_for_update()` provides portable abstraction

### Implementation Notes

**Lock Acquisition Pattern:**

```python
from sqlalchemy import select
from sqlalchemy.orm import Session

def update_stock_with_lock(
    db: Session,
    component_id: str,
    location_id: str,
    quantity_change: int
):
    # Acquire pessimistic lock on ComponentLocation row
    stmt = (
        select(ComponentLocation)
        .where(
            ComponentLocation.component_id == component_id,
            ComponentLocation.storage_location_id == location_id
        )
        .with_for_update(nowait=False)  # Block until lock available
    )

    location_stock = db.execute(stmt).scalar_one_or_none()

    if not location_stock:
        raise HTTPException(status_code=404, detail="Location not found")

    # Perform stock operation under lock
    location_stock.quantity_on_hand += quantity_change

    # Lock automatically released on commit/rollback
    db.commit()
```

**Transaction Scope:**

- Lock held for entire transaction duration
- Use FastAPI's dependency injection to manage transaction lifecycle
- Lock released automatically on commit or rollback

**Error Handling:**

- **Lock Timeout**: Configure reasonable timeout (e.g., 10 seconds) to prevent indefinite waiting
- **User Feedback**: Return HTTP 409 Conflict if lock cannot be acquired within timeout
- **Deadlock Detection**: SQLite handles deadlocks by raising `OperationalError`; catch and return meaningful error

**Testing Considerations:**

- Use in-memory SQLite for tests (backend/tests/conftest.py, line 28)
- Test concurrent access with threading or asyncio tasks
- Verify lock is released on exception/rollback

**Critical Gotchas:**

- **Lock Granularity**: Lock at ComponentLocation level, not Component level (too coarse)
- **Transaction Management**: Ensure locks are released even on exceptions (use try/finally or context managers)
- **Database Compatibility**: `with_for_update()` behavior varies by database; test with actual production database
- **Deadlocks**: Two operations locking different rows in different order can cause deadlock; maintain consistent lock ordering

---

## 3. Stock History Tracking

### Decision

Use the existing `StockTransaction` model (backend/src/models/stock_transaction.py) to create immutable audit trail entries for all stock operations. Extend schema to include location information and ensure quantity_change field uses +/- indicators for Add/Remove operations.

### Rationale

- **Existing Infrastructure**: StockTransaction model already exists with TransactionType enum (ADD, REMOVE, MOVE, ADJUST) and all required fields
- **Immutability**: Records created with `server_default=func.now()` for created_at; no update_at field means entries cannot be modified
- **Complete Audit Trail**: Captures timestamp, user, operation type, quantity changes, locations, and comments (lines 33-67)
- **Spec Alignment**: FR-047, FR-048 require logging all operations with timestamp, user, operation type, quantities with +/- indicators, location(s), lot ID, price, and comments

### Alternatives Considered

1. **Event Sourcing Architecture**
   - Rejected: Too complex for current requirements; StockTransaction already provides event log
   - Future consideration if full state reconstruction becomes necessary

2. **Separate Audit Table**
   - Rejected: StockTransaction already serves this purpose
   - Would duplicate functionality

3. **Component-Level History JSON Field**
   - Rejected: Not queryable, sortable, or filterable
   - Poor performance for reporting and analysis

### Implementation Notes

**Schema Review (StockTransaction model):**

```python
class StockTransaction(Base):
    __tablename__ = "stock_transactions"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    component_id = Column(String, ForeignKey("components.id"), nullable=False)

    # Operation details
    transaction_type = Column(SQLEnum(TransactionType), nullable=False)
    quantity_change = Column(Integer, nullable=False)  # Can be positive or negative
    previous_quantity = Column(Integer, nullable=False)
    new_quantity = Column(Integer, nullable=False)

    # Context
    reason = Column(Text, nullable=False)
    reference_id = Column(String, nullable=True)  # Order ID, etc.
    reference_type = Column(String(50), nullable=True)

    # Location tracking
    from_location_id = Column(String, ForeignKey("storage_locations.id"), nullable=True)
    to_location_id = Column(String, ForeignKey("storage_locations.id"), nullable=True)

    # User tracking
    user_id = Column(String, nullable=True)
    user_name = Column(String(100), nullable=True)

    # Additional metadata
    notes = Column(Text, nullable=True)  # User comments

    # Immutable timestamp
    created_at = Column(DateTime(timezone=True), server_default=func.now())
```

**Quantity Change Indicators:**

- **ADD**: `quantity_change = +N` (positive integer)
- **REMOVE**: `quantity_change = -N` (negative integer)
- **MOVE**: `quantity_change = 0` (no quantity change, only location change)

**Creating History Entries:**

```python
# Add Stock Example
transaction = StockTransaction(
    component_id=component_id,
    transaction_type=TransactionType.ADD,
    quantity_change=quantity,  # +50
    previous_quantity=location.quantity_on_hand,
    new_quantity=location.quantity_on_hand + quantity,
    from_location_id=None,
    to_location_id=location_id,
    reason="Manual stock addition",
    notes=request.comments,
    user_id=current_user.id,
    user_name=current_user.username
)
db.add(transaction)
```

**Frontend Display (Stock History Tab):**

- Query: `GET /api/v1/components/{id}/stock-history?limit=50`
- Table columns: Date, Quantity (+/-), Location, Lot ID, Price, Comments, User
- Sorting: Default to newest first (created_at DESC)
- Filtering: By transaction type, date range, location
- Export: CSV/Excel for audit compliance

**Critical Gotchas:**

- **Atomic Creation**: Create StockTransaction in same database transaction as stock update
- **Rollback Safety**: If stock update fails, transaction record must also roll back
- **User Context**: Capture user information from FastAPI's auth dependency
- **Lot ID and Price**: Currently not in StockTransaction model; may need schema extension if lot tracking is required (see spec FR-048)

**Schema Extensions Needed:**

Based on spec FR-048 requirements for "lot ID" and "price" in history:
- Add `lot_id` field (String, nullable=True)
- Add `unit_price` field (Numeric, nullable=True)
- Add `total_price` field (Numeric, nullable=True)

---

## 4. Multi-Step Form State Management

### Decision

Use local component ref-based state for multi-step forms (Add Stock wizard), with Pinia store only for server communication. Each form step's state is stored in a ref scoped by component ID, with validation rules enforced at each step.

### Rationale

- **Simplicity**: Local ref state is simpler than Pinia for ephemeral form data that doesn't need global access
- **Component Isolation**: Form state isolated per component row prevents cross-contamination
- **Existing Pattern**: GridLayoutForm.vue (storage/forms/) demonstrates local state management for multi-step forms (lines 79-86)
- **No Global Pollution**: Avoids bloating Pinia store with temporary form data
- **Performance**: Ref updates are faster than Pinia mutations for local, high-frequency changes

### Alternatives Considered

1. **Pinia Store for All Form State**
   - Rejected: Overkill for ephemeral data; adds unnecessary complexity
   - Store should manage server state, not UI state

2. **Composition API Composable**
   - Rejected: Adds layer of indirection for simple forms
   - Better suited for reusable logic across multiple components

3. **Vuex (Legacy)**
   - Rejected: Project uses Pinia, not Vuex
   - Vuex is deprecated in favor of Pinia

### Implementation Notes

**Multi-Step Form Pattern (Add Stock):**

```typescript
// Form state structure per component
interface AddStockFormState {
  step: number // 1: Quantity/Pricing, 2: Location
  mode: 'manual' | 'order' | 'add_to_order'
  quantity: number
  pricingType: 'none' | 'per_component' | 'entire_lot'
  unitPrice: number | null
  totalPrice: number | null
  selectedLocation: string | null
  createNewLocation: boolean
  newLocationName: string
  comments: string
  orderId: string | null // For "Receive against order" mode
}

// Scoped state by component ID
const addStockForms = ref<Record<string, AddStockFormState>>({})

// Initialize form when tab becomes active
const initAddStockForm = (componentId: string) => {
  addStockForms.value[componentId] = {
    step: 1,
    mode: 'manual',
    quantity: 0,
    pricingType: 'none',
    unitPrice: null,
    totalPrice: null,
    selectedLocation: null,
    createNewLocation: false,
    newLocationName: '',
    comments: '',
    orderId: null
  }
}
```

**Step Navigation:**

```typescript
const nextStep = (componentId: string) => {
  const form = addStockForms.value[componentId]
  if (validateCurrentStep(form)) {
    form.step += 1
  }
}

const previousStep = (componentId: string) => {
  addStockForms.value[componentId].step -= 1
}
```

**Price Calculation (Auto-computed):**

```typescript
const updatePricing = (componentId: string) => {
  const form = addStockForms.value[componentId]

  if (form.pricingType === 'per_component' && form.unitPrice) {
    form.totalPrice = form.unitPrice * form.quantity
  } else if (form.pricingType === 'entire_lot' && form.totalPrice) {
    form.unitPrice = form.totalPrice / form.quantity
  }
}
```

**Validation Per Step:**

```typescript
const validateCurrentStep = (form: AddStockFormState): boolean => {
  if (form.step === 1) {
    // Validate quantity and pricing
    if (form.quantity <= 0) return false
    if (form.pricingType === 'per_component' && !form.unitPrice) return false
    if (form.pricingType === 'entire_lot' && !form.totalPrice) return false
  } else if (form.step === 2) {
    // Validate location selection
    if (!form.selectedLocation && !form.createNewLocation) return false
    if (form.createNewLocation && !form.newLocationName) return false
  }
  return true
}
```

**Submission (Pinia Store Integration):**

```typescript
const submitAddStock = async (componentId: string) => {
  const form = addStockForms.value[componentId]

  // Use existing componentsStore for API call
  await componentsStore.addStock(componentId, {
    quantity: form.quantity,
    locationId: form.selectedLocation,
    unitPrice: form.unitPrice,
    comments: form.comments
  })

  // Clear form state on success
  delete addStockForms.value[componentId]

  // Reset tab to 'stock' view
  setActiveTab(componentId, 'stock')
}
```

**Critical Gotchas:**

- **State Cleanup**: Delete form state when component row collapses or is removed
- **Tab Switching**: Clear form state if user switches away from stock operation tab
- **Reactive Updates**: Use `ref` for primitives, `reactive` for nested objects
- **Form Reset**: Provide explicit "Cancel" button to clear form state
- **Computed Properties**: Use `computed()` for derived values (total price, validation status)

---

## 5. Atomic Stock Transfers

### Decision

Use database transactions with pessimistic locking on both source and destination ComponentLocation records, ensuring both decrement and increment operations succeed or both fail. Lock acquisition order: always lock lower ID first to prevent deadlocks.

### Rationale

- **ACID Compliance**: Database transactions guarantee atomicity (all-or-nothing)
- **Spec Requirement**: FR-033 requires atomic transfers: "System MUST transfer stock from source to destination location atomically (both operations succeed or both fail)"
- **Data Consistency**: Prevents partial transfers where source is decremented but destination fails to increment
- **Existing Infrastructure**: SQLAlchemy's session management provides transaction boundaries
- **Pessimistic Locking**: Prevents concurrent modifications during transfer

### Alternatives Considered

1. **Saga Pattern**
   - Rejected: Overly complex for simple database operations within single database
   - Better suited for distributed transactions across microservices

2. **Two-Phase Commit**
   - Rejected: SQLite doesn't support distributed transactions
   - Unnecessary complexity for single-database operations

3. **Optimistic Locking Only**
   - Rejected: Can fail on concurrent access, requiring retry logic
   - Spec requires blocking concurrent operations, not retrying

### Implementation Notes

**Move Stock Transaction Pattern:**

```python
from sqlalchemy import select
from sqlalchemy.orm import Session

def move_stock(
    db: Session,
    component_id: str,
    source_location_id: str,
    destination_location_id: str,
    quantity: int,
    current_user: User
):
    # Validate inputs
    if quantity <= 0:
        raise HTTPException(status_code=400, detail="Quantity must be positive")

    if source_location_id == destination_location_id:
        raise HTTPException(status_code=400, detail="Source and destination must be different")

    # Lock order: always lock lower ID first to prevent deadlocks
    lock_order = sorted([source_location_id, destination_location_id])

    # Acquire locks in consistent order
    stmt1 = (
        select(ComponentLocation)
        .where(
            ComponentLocation.component_id == component_id,
            ComponentLocation.storage_location_id == lock_order[0]
        )
        .with_for_update(nowait=False)
    )

    stmt2 = (
        select(ComponentLocation)
        .where(
            ComponentLocation.component_id == component_id,
            ComponentLocation.storage_location_id == lock_order[1]
        )
        .with_for_update(nowait=False)
    )

    loc1 = db.execute(stmt1).scalar_one_or_none()
    loc2 = db.execute(stmt2).scalar_one_or_none()

    # Determine which is source and which is destination
    if lock_order[0] == source_location_id:
        source_loc = loc1
        dest_loc = loc2
    else:
        source_loc = loc2
        dest_loc = loc1

    if not source_loc:
        raise HTTPException(status_code=404, detail="Source location not found")

    # Validate sufficient quantity
    if source_loc.quantity_on_hand < quantity:
        raise HTTPException(
            status_code=400,
            detail=f"Insufficient quantity at source location (available: {source_loc.quantity_on_hand})"
        )

    # Perform atomic transfer
    source_loc.quantity_on_hand -= quantity

    if dest_loc:
        # Destination already exists - increment quantity
        dest_loc.quantity_on_hand += quantity
    else:
        # Create new destination location entry
        dest_loc = ComponentLocation(
            component_id=component_id,
            storage_location_id=destination_location_id,
            quantity_on_hand=quantity,
            unit_cost_at_location=source_loc.unit_cost_at_location,  # Inherit pricing
            location_notes=source_loc.location_notes  # Copy notes
        )
        db.add(dest_loc)

    # Create audit trail
    transaction = StockTransaction(
        component_id=component_id,
        transaction_type=TransactionType.MOVE,
        quantity_change=0,  # No net change to total quantity
        previous_quantity=source_loc.quantity_on_hand + quantity,  # Before move
        new_quantity=source_loc.quantity_on_hand + quantity,  # After move (same)
        from_location_id=source_location_id,
        to_location_id=destination_location_id,
        reason=f"Moved {quantity} units between locations",
        user_id=current_user.id,
        user_name=current_user.username
    )
    db.add(transaction)

    # Remove source location if depleted (FR-035)
    if source_loc.quantity_on_hand == 0:
        db.delete(source_loc)

    # Commit atomically
    db.commit()
```

**Rollback on Error:**

```python
try:
    move_stock(db, component_id, source_id, dest_id, quantity, user)
except Exception as e:
    db.rollback()  # All changes rolled back atomically
    raise HTTPException(status_code=500, detail=f"Stock move failed: {str(e)}")
```

**Testing Strategy:**

```python
def test_atomic_stock_transfer_rollback(db_session):
    """Test that partial failures roll back completely."""
    # Setup: Create source location with stock
    source = ComponentLocation(component_id=comp_id, storage_location_id=loc1, quantity_on_hand=50)
    db_session.add(source)
    db_session.commit()

    # Mock destination creation to fail
    with patch('sqlalchemy.orm.session.Session.add', side_effect=Exception("DB error")):
        with pytest.raises(HTTPException):
            move_stock(db_session, comp_id, loc1, loc2, 30, admin_user)

    # Verify source quantity unchanged (rollback successful)
    db_session.refresh(source)
    assert source.quantity_on_hand == 50
```

**Critical Gotchas:**

- **Lock Ordering**: Always lock in consistent order (by ID) to prevent deadlocks
- **Phantom Reads**: Use `with_for_update()` to prevent concurrent inserts of destination location
- **Zero Stock Cleanup**: Remove source ComponentLocation if quantity becomes 0 (FR-035)
- **Pricing Inheritance**: Copy unit_cost_at_location from source to destination (FR-034)
- **Transaction Scope**: Ensure all operations within single database transaction
- **Error Handling**: Catch database errors and return meaningful HTTP responses

---

## 6. Auto-Capping Validation

### Decision

Implement client-side auto-capping with immediate visual feedback, combined with server-side validation. When user enters quantity exceeding available stock, automatically cap the value and display a warning notification.

### Rationale

- **Spec Requirement**: FR-017 and FR-029 require auto-capping: "System MUST automatically cap removal/move quantity at available stock if user enters a value exceeding current quantity"
- **UX Best Practice**: Immediate feedback prevents user from submitting invalid form
- **Double Validation**: Client-side for UX, server-side for security
- **Quasar Integration**: Use Quasar's input validation and notification system

### Alternatives Considered

1. **Server-Side Only Validation**
   - Rejected: Poor UX; user discovers error only after submission
   - Round-trip delay frustrating for users

2. **Hard Block (Prevent Input)**
   - Rejected: Confusing UX; user doesn't understand why they can't type
   - Auto-capping is more explicit and educational

3. **Soft Warning (Allow Submission)**
   - Rejected: Spec requires auto-capping, not just warnings
   - Would violate business rule preventing negative stock

### Implementation Notes

**Client-Side Auto-Capping (Vue 3 + Quasar):**

```vue
<template>
  <div class="remove-stock-form">
    <q-input
      v-model.number="removeQuantity"
      type="number"
      label="Quantity to Remove"
      outlined
      dense
      :hint="`Available: ${availableQuantity}`"
      :rules="[
        val => val > 0 || 'Quantity must be positive',
        val => val <= availableQuantity || 'Exceeds available stock'
      ]"
      @update:model-value="handleQuantityChange"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import { useQuasar } from 'quasar'

const $q = useQuasar()
const removeQuantity = ref(0)
const availableQuantity = ref(100) // From props or store

const handleQuantityChange = (newValue: number) => {
  if (newValue > availableQuantity.value) {
    // Auto-cap to available quantity
    removeQuantity.value = availableQuantity.value

    // Show warning notification (FR-018)
    $q.notify({
      type: 'warning',
      message: `Quantity capped at ${availableQuantity.value} (maximum available)`,
      position: 'top-right',
      timeout: 3000,
      icon: 'warning'
    })
  }
}

// Watch for external changes to available quantity
watch(availableQuantity, (newAvailable) => {
  if (removeQuantity.value > newAvailable) {
    removeQuantity.value = newAvailable
  }
})
</script>
```

**Server-Side Validation:**

```python
from fastapi import APIRouter, HTTPException

@router.post("/components/{component_id}/stock/remove")
def remove_stock(
    component_id: str,
    request: RemoveStockRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_auth)
):
    # Fetch current stock with lock
    stmt = (
        select(ComponentLocation)
        .where(
            ComponentLocation.component_id == component_id,
            ComponentLocation.storage_location_id == request.location_id
        )
        .with_for_update(nowait=False)
    )

    location = db.execute(stmt).scalar_one_or_none()

    if not location:
        raise HTTPException(status_code=404, detail="Location not found")

    # Server-side auto-capping (defense in depth)
    quantity_to_remove = min(request.quantity, location.quantity_on_hand)

    if quantity_to_remove != request.quantity:
        # Log discrepancy (client-side capping should have caught this)
        logger.warning(
            f"Server-side capping: requested {request.quantity}, "
            f"capped to {quantity_to_remove} for component {component_id}"
        )

    # Perform removal
    location.quantity_on_hand -= quantity_to_remove

    # Create audit trail
    transaction = StockTransaction(
        component_id=component_id,
        transaction_type=TransactionType.REMOVE,
        quantity_change=-quantity_to_remove,
        previous_quantity=location.quantity_on_hand + quantity_to_remove,
        new_quantity=location.quantity_on_hand,
        to_location_id=request.location_id,
        reason="Stock removal",
        notes=request.comments,
        user_id=current_user.id,
        user_name=current_user.username
    )
    db.add(transaction)

    # Remove location if depleted (FR-021)
    if location.quantity_on_hand == 0:
        db.delete(location)

    db.commit()

    return {
        "success": True,
        "quantity_removed": quantity_to_remove,
        "new_quantity": location.quantity_on_hand if location.quantity_on_hand > 0 else 0
    }
```

**Real-Time Stock Updates:**

```typescript
// Fetch available quantity when form loads
const loadAvailableQuantity = async (componentId: string, locationId: string) => {
  const response = await api.get(
    `/api/v1/components/${componentId}/locations/${locationId}`
  )
  availableQuantity.value = response.data.quantity_on_hand
}

// Refresh after concurrent changes (optional WebSocket integration)
const refreshQuantity = () => {
  loadAvailableQuantity(componentId, locationId)
}
```

**Critical Gotchas:**

- **Race Conditions**: Available quantity can change between page load and submission; server validation is essential
- **Decimal/Float Inputs**: Use `v-model.number` and `type="number"` to prevent non-numeric input
- **Negative Values**: Add validation rule to prevent negative quantities
- **Zero Handling**: Allow user to remove all stock (quantity = available quantity)
- **Visual Feedback**: Use Quasar's `:hint` prop to show available quantity
- **Notification Spam**: Debounce notifications if user types quickly exceeding max value

**Accessibility Considerations:**

- Ensure screen readers announce auto-capping notifications
- Use `aria-live="polite"` for quantity validation messages
- Provide clear error messages in validation rules

---

## Summary of Key Decisions

1. **Inline Forms**: Render forms within expanded rows using tab-based navigation (existing ComponentList.vue pattern)
2. **Pessimistic Locking**: Use SQLAlchemy's `with_for_update()` for row-level locks during stock operations
3. **Stock History**: Leverage existing StockTransaction model with quantity +/- indicators; extend schema for lot ID and pricing
4. **Form State**: Use local ref-based state for multi-step forms; Pinia only for server communication
5. **Atomic Transfers**: Database transactions with consistent lock ordering to prevent deadlocks
6. **Auto-Capping**: Client-side auto-capping with visual feedback + server-side validation for defense in depth

---

## Next Steps

1. **Phase 1 (Planning)**: Create detailed implementation plan based on these decisions
2. **Phase 2 (Tasks)**: Break down plan into actionable tasks with dependency ordering
3. **Phase 3 (Implementation)**: TDD approach - write tests first, then implement features

---

**Document Status**: Research Complete ✓
**Author**: Claude (Sonnet 4.5)
**Last Updated**: 2025-10-04
