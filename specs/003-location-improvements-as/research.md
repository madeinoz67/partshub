# Research: Storage Location Layout Generator

**Feature**: 003-location-improvements-as
**Date**: 2025-10-02
**Status**: Complete

## Technical Decisions

### 1. Layout Generation Algorithm

**Decision**: Implement iterative Cartesian product generator for multi-dimensional layouts

**Rationale**:
- Memory efficient for large batch operations (500 locations max)
- Supports streaming preview (first 5, last 1, total count)
- Natural fit for Row (1D), Grid (2D), and 3D Grid (3D) layouts
- Python's itertools.product provides battle-tested implementation

**Alternatives Considered**:
- Recursive generation: More complex, harder to limit/preview
- Pre-generate all combinations: Memory inefficient for 500 locations
- Database-driven generation: Adds unnecessary complexity

### 2. Range Specification Design

**Decision**: Use discriminated union pattern with RangeType enum (letters/numbers)

**Rationale**:
- Type-safe handling of letter vs number ranges
- Enables range-specific validation (a-z vs 0-999)
- Supports optional features per type (capitalization for letters, zero-padding for numbers)
- Pydantic validators enforce constraints at schema level

**Alternatives Considered**:
- String-based ranges: Type unsafe, harder to validate
- Separate letter/number range classes: More boilerplate
- Regex-based parsing: Error-prone, poor user feedback

### 3. Preview Generation Strategy

**Decision**: Generate first 5 locations + last location + total count

**Rationale**:
- Provides immediate feedback without full generation cost
- Shows naming pattern consistency (first 5) and end result (last)
- <50ms response time even for 500-location layouts
- PartsBox.io uses similar preview approach (industry standard)

**Alternatives Considered**:
- Full generation with pagination: Slower, unnecessary for preview
- Random sampling: Doesn't show consistent pattern
- First 10 only: Doesn't validate end of range

### 4. Validation Strategy

**Decision**: Multi-layer validation (schema → business logic → database)

**Rationale**:
- Pydantic schemas validate input structure and types
- Service layer validates business rules (max 500, duplicate names, valid ranges)
- Database layer enforces uniqueness constraints
- Fail fast with clear error messages per layer

**Validation Rules**:
1. Schema: Range types, non-negative numbers, single characters for letters
2. Business: Start ≤ End, total ≤ 500, no existing duplicates
3. Database: Unique location names (enforced by DB constraint)

**Alternatives Considered**:
- Single validation layer: Mixes concerns, harder to test
- Client-side only: Security risk, poor UX on failure
- Async validation: Adds latency for minimal benefit

### 5. Database Schema Extension

**Decision**: Add optional `layout_config` JSONB field to storage_locations table

**Rationale**:
- Audit trail for how location was created
- Enables future "regenerate similar" feature
- Minimal schema change (one nullable column)
- No migration needed for existing rows

**Schema**:
```sql
ALTER TABLE storage_locations
ADD COLUMN layout_config JSONB NULL;
```

**Stored Data**:
```json
{
  "layout_type": "grid",
  "prefix": "box1-",
  "ranges": [
    {"type": "letters", "start": "a", "end": "f"},
    {"type": "numbers", "start": 1, "end": 5}
  ],
  "separators": ["-"],
  "created_at": "2025-10-02T10:30:00Z"
}
```

**Alternatives Considered**:
- Separate layout_configs table: Over-engineered for audit-only data
- No persistence: Loses valuable audit information
- Separate fields (prefix, range1, range2): Schema explosion

### 6. API Endpoint Design

**Decision**: Two endpoints - preview (GET-style POST) and create (POST)

**Endpoints**:
1. `POST /api/storage-locations/generate-preview`
   - Input: Layout configuration
   - Output: Preview (first 5 names, last name, total count, validation errors)
   - No side effects (idempotent)

2. `POST /api/storage-locations/bulk-create`
   - Input: Layout configuration + optional parent_id + single_part_only flag
   - Output: Created location IDs, count, success status
   - Authenticated users only
   - Transactional (all-or-nothing)

**Rationale**:
- Separation of concerns: preview is read-only, create mutates
- Preview can be called rapidly during UI configuration
- Bulk create ensures atomicity (rollback on partial failure)

**Alternatives Considered**:
- Single endpoint with dry_run flag: Mixes read/write semantics
- GET for preview: Large payloads problematic, non-standard for complex input
- Separate endpoints per layout type: 8 endpoints instead of 2

### 7. Frontend Component Architecture

**Decision**: Dialog-based workflow with tab navigation and reactive preview

**Component Hierarchy**:
```
LocationLayoutDialog (parent)
├── LayoutTypeTabs (Single/Row/Grid/3D Grid)
├── RangeConfigurator (dynamic based on layout type)
├── LocationPreview (real-time feedback)
└── Action buttons (Cancel/Create)
```

**Rationale**:
- Single dialog keeps UI focused (modal interaction)
- Tabs provide clear layout type selection
- Reactive preview updates on every config change (debounced 300ms)
- Follows Quasar dialog patterns (consistent with app UX)

**Alternatives Considered**:
- Multi-step wizard: More clicks, slower workflow
- Separate page: Disrupts context, requires navigation
- Inline form: Clutters storage locations page

### 8. Error Handling Strategy

**Decision**: Progressive error disclosure with inline validation

**Error Levels**:
1. **Input validation** (immediate): Range format, start ≤ end
2. **Business rules** (on preview): Total count > 500, duplicate detection
3. **Creation errors** (on submit): Database conflicts, server errors

**User Feedback**:
- Inline field errors (red border, helper text)
- Preview area warnings (yellow banner for 100-500 locations)
- Creation errors (error dialog with actionable message)

**Rationale**:
- Early feedback prevents wasted effort
- Clear error hierarchy (client → business → server)
- Actionable messages ("Reduce range" vs "An error occurred")

**Alternatives Considered**:
- Error summary at top: Requires scrolling, disconnected from input
- Toast notifications only: Disappear, not persistent enough
- Validation on blur only: Delayed feedback, poor UX

### 9. Performance Optimization

**Decision**: Debounced preview requests + client-side count estimation

**Strategy**:
- Debounce preview API calls (300ms after last input change)
- Calculate total count client-side for instant feedback
- Full preview generation server-side (validate duplicates)
- Limit preview rendering (5 + 1 items, not full list)

**Performance Targets**:
- Preview API: <200ms for 500-location config
- Bulk create API: <2s for 500 locations
- UI responsiveness: <16ms frame time (60fps)

**Alternatives Considered**:
- No debounce: API spam, server load
- Server-side only counting: Slower feedback loop
- Pagination preview: Adds complexity for minimal value

### 10. Testing Strategy

**Decision**: Three-layer test pyramid (contract → integration → unit)

**Test Breakdown**:
1. **Contract tests** (API layer):
   - Request/response schema validation
   - Error response formats
   - Authentication requirements

2. **Integration tests** (user scenarios):
   - All 8 acceptance scenarios from spec
   - 5 edge cases from spec
   - End-to-end workflows (preview → create → verify)

3. **Unit tests** (business logic):
   - Range generation algorithms (letters, numbers, combinations)
   - Validation rules (max 500, duplicates, range validity)
   - Preview generation logic

**Test Data Strategy**:
- In-memory SQLite database per test (test isolation)
- Factory functions for test locations
- Parameterized tests for all layout types

**Alternatives Considered**:
- E2E tests only: Slow, brittle, poor debugging
- Unit tests only: Misses integration issues
- Shared test database: Violates test isolation principle

## Implementation Dependencies

### External Libraries (already available)
- **itertools** (stdlib): Cartesian product generation
- **pydantic**: Schema validation with custom validators
- **pytest**: Test framework with fixtures
- **Quasar**: Dialog, tabs, form components

### Database Migration
- **Alembic migration**: Add layout_config JSONB column
- **Backward compatible**: Nullable column, existing data unaffected

### API Authentication
- **Existing JWT middleware**: Reuse for bulk-create endpoint
- **No new auth logic needed**: FR-024 uses existing access control

## Risk Assessment

| Risk | Impact | Mitigation |
|------|--------|------------|
| Duplicate location names created | High | Pre-creation validation, database unique constraint, transactional create |
| Preview performance for complex layouts | Medium | Limit to 500 locations max, optimize query for duplicate check |
| UI state management for multi-step input | Medium | Pinia store for layout config, reactive computed preview |
| Migration breaks existing locations | Low | Nullable column, no data migration needed, test on SQLite first |

## Open Questions (All Resolved)

1. ~~How to handle location type assignment?~~ → FR-021: User selects type in dialog (default: "bin")
2. ~~Parent location hierarchy?~~ → FR-014: Optional parent selection in dialog
3. ~~Single-part only designation?~~ → FR-015: Checkbox option in dialog
4. ~~Zero-padding preference?~~ → FR-011: Per-range option (e.g., "01" vs "1")
5. ~~Capitalization preference?~~ → FR-010: Per-range option (e.g., "A" vs "a")

All questions resolved via functional requirements in spec.md.

---

**Research Status**: ✅ Complete
**Outcome**: All technical decisions documented, no blockers identified, ready for Phase 1 design
