# Research: Component Bulk Operations

## Research Areas

### 1. SQLAlchemy Transaction Patterns for Atomic Bulk Operations

**Decision**: Use SQLAlchemy session-level transactions with explicit `session.begin()` and rollback on any exception

**Rationale**:
- SQLAlchemy provides ACID transaction guarantees when using explicit transaction blocks
- Context manager pattern (`with session.begin()`) ensures automatic rollback on exceptions
- Supports all-or-nothing semantics required by FR-040 and FR-041
- Compatible with existing FastAPI dependency injection pattern

**Alternatives Considered**:
- **Manual transaction management**: Rejected due to error-prone nature and risk of orphaned transactions
- **SAVEPOINT-based nested transactions**: Rejected as unnecessary complexity for this use case
- **Database-level triggers**: Rejected to keep business logic in application layer

**Implementation Pattern**:
```python
async def bulk_operation(db: Session, component_ids: List[int], operation: Callable):
    try:
        async with db.begin():
            for component_id in component_ids:
                component = await db.get(Component, component_id)
                if not component:
                    raise ComponentNotFoundError(component_id)
                await operation(component)
            await db.commit()
    except Exception as e:
        await db.rollback()
        raise BulkOperationError(failed_components=[...], original_error=e)
```

### 2. Pinia Store Persistence for Selection State

**Decision**: Use Pinia with `pinia-plugin-persistedstate` for automatic localStorage persistence

**Rationale**:
- Pinia's plugin system provides declarative persistence without boilerplate
- localStorage persists across page navigation and browser sessions
- Survives page refreshes and navigation (FR-003 requirement)
- Minimal performance impact for selection state (typically <1KB)
- Integrates seamlessly with Vue 3 Composition API

**Alternatives Considered**:
- **Vuex with manual localStorage**: Rejected in favor of Pinia (Vue 3 recommended)
- **sessionStorage**: Rejected as it doesn't persist across browser sessions
- **IndexedDB**: Rejected as overkill for simple Set<number> storage
- **URL query parameters**: Rejected due to length limits and poor UX

**Implementation Pattern**:
```typescript
import { defineStore } from 'pinia'
import { useLocalStorage } from '@vueuse/core'

export const useSelectionStore = defineStore('selection', {
  state: () => ({
    selectedIds: new Set<number>()
  }),
  persist: {
    storage: localStorage,
    paths: ['selectedIds']
  }
})
```

### 3. FastAPI Dependency Injection for Admin-Only Protection

**Decision**: Create custom `AdminRequired` dependency using FastAPI's `Depends()` with JWT role validation

**Rationale**:
- Follows existing PartsHub authentication pattern (JWT-based)
- Declarative role enforcement at endpoint level
- Centralized admin check logic prevents code duplication
- Compatible with existing JWT middleware
- Returns 403 Forbidden for non-admin users (FR-039)

**Alternatives Considered**:
- **Decorator-based auth**: Rejected as not idiomatic for FastAPI
- **Middleware-based filtering**: Rejected as too coarse-grained (applies globally)
- **Route prefixes with separate router**: Rejected as doesn't enforce at endpoint level

**Implementation Pattern**:
```python
from fastapi import Depends, HTTPException, status
from src.auth import get_current_user

async def require_admin(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required for bulk operations"
        )
    return current_user

@router.post("/api/components/bulk/delete")
async def bulk_delete(
    request: BulkDeleteRequest,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    ...
```

### 4. Vue.js/Quasar Multi-Select Table with Persistent State

**Decision**: Use QTable with `selection="multiple"` and sync to Pinia store via watchers

**Rationale**:
- QTable provides built-in multi-select with checkboxes (FR-001, FR-002)
- Two-way binding between QTable `selected` prop and Pinia store
- Visual indicators (row highlighting) built-in (FR-005)
- Pagination support with persistent selection across pages
- Accessible keyboard navigation included

**Alternatives Considered**:
- **Custom table implementation**: Rejected due to reinventing accessibility and pagination
- **Vue 3 Teleport for selection state**: Rejected as doesn't solve persistence
- **Composition API provide/inject**: Rejected as doesn't persist across routes

**Implementation Pattern**:
```vue
<template>
  <q-table
    :rows="components"
    :columns="columns"
    selection="multiple"
    v-model:selected="localSelection"
    @update:selected="syncToStore"
    row-key="id"
  >
    <template v-slot:top>
      <q-btn
        label="Selected..."
        :disable="!hasSelection"
        @click="showBulkMenu = true"
      />
    </template>
  </q-table>
</template>

<script setup>
import { useSelectionStore } from '@/stores/selection'
const selectionStore = useSelectionStore()
const localSelection = computed({
  get: () => Array.from(selectionStore.selectedIds).map(id => components.value.find(c => c.id === id)),
  set: (selected) => selectionStore.setSelection(selected.map(c => c.id))
})
</script>
```

### 5. Optimistic Concurrency Control for Concurrent Modifications

**Decision**: Use row-level version counter with SQLAlchemy's `version_id_col` and compare-and-swap semantics

**Rationale**:
- Detects concurrent modifications at database level (FR-044)
- SQLAlchemy's `version_id_col` provides automatic version increment
- ConcurrentModificationError raised on version mismatch
- No additional database columns needed (reuse existing `updated_at` or add `version`)
- Minimal performance overhead (single integer comparison)

**Alternatives Considered**:
- **Timestamp-based locking**: Rejected due to clock skew issues
- **Pessimistic locking (SELECT FOR UPDATE)**: Rejected due to deadlock risk in bulk ops
- **Read-before-write check**: Rejected as race condition still possible
- **No concurrency control**: Rejected as violates FR-044 requirement

**Implementation Pattern**:
```python
class Component(Base):
    __tablename__ = "components"
    id = Column(Integer, primary_key=True)
    version = Column(Integer, nullable=False, default=1)
    __mapper_args__ = {"version_id_col": version}

# In bulk operation:
try:
    component.tags.append(new_tag)  # SQLAlchemy auto-increments version
    await db.flush()  # Raises StaleDataError if version mismatch
except StaleDataError:
    raise ConcurrentModificationError(
        component_id=component.id,
        message="Component modified by another user"
    )
```

## Performance Considerations

### Bulk Operation Batch Size
**Decision**: Process up to 1000 components per transaction with chunked commit strategy

**Rationale**:
- Keeps transaction size manageable for SQLite
- Meets performance goal: <200ms for <100 components, <500ms for 100-1000
- Prevents memory exhaustion on large bulk operations
- Allows progress feedback for operations >1000 components

### Tag Preview Optimization
**Decision**: Use SQLAlchemy `selectinload` for tag relationships to prevent N+1 queries

**Rationale**:
- Preview endpoint (FR-023) needs all tags for selected components
- Single query with JOIN more efficient than per-component queries
- Critical for responsive preview UI (<100ms target)

## Security Considerations

### Admin-Only Enforcement
- All bulk endpoints protected via `Depends(require_admin)`
- Non-admin users get 403 Forbidden (not 401 Unauthorized)
- Frontend hides UI controls for non-admin (FR-008) but backend enforces

### SQL Injection Prevention
- All component IDs validated as integers before query construction
- SQLAlchemy parameterized queries used throughout
- No string concatenation in SQL generation

### CSRF Protection
- JWT tokens in Authorization header (not cookies)
- Double-submit cookie pattern not required
- All state-changing operations use POST (not GET)

## Documentation Requirements

### API Documentation Updates
- Add bulk operations section to OpenAPI spec
- Document admin-only requirement for all bulk endpoints
- Include error response schemas (BulkOperationError)
- Add examples for each bulk operation type

### User Documentation Updates
- Add "Bulk Operations Guide" to user docs
- Document admin role requirement
- Include screenshots of bulk operation dialogs
- Add troubleshooting section for common errors

## Summary

All technical decisions support the constitutional requirements:
- ✅ API-First: Backend endpoints defined with OpenAPI contracts
- ✅ TDD: Contract tests written before implementation
- ✅ Access Control: Admin-only enforcement at API level
- ✅ Quality: Ruff-compliant code, full test coverage
- ✅ Test Isolation: In-memory SQLite, no shared state
- ✅ Documentation: OpenAPI specs and user guides planned

**Next Phase**: Generate data model, API contracts, and failing tests
