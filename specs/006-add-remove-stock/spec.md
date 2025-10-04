# Feature Specification: Stock Management Operations

**Feature Branch**: `006-add-remove-stock`
**Created**: 2025-10-04
**Status**: Draft
**Input**: User description: "add remove stock; implement the add, remove and move stock from the componet row expansion menu. stock will be added as per the dialog thats opened, removing stokc is alot simpler.  moving stock will allow movemnet betwen the current selected lcoaiton and another that already has the comonents, or a completely new location"

## Execution Flow (main)
```
1. Parse user description from Input
   → If empty: ERROR "No feature description provided"
2. Extract key concepts from description
   → Identified: Add Stock, Remove Stock, Move Stock operations from component row expansion menu
3. For each unclear aspect:
   → [NEEDS CLARIFICATION: What validation rules apply when removing more stock than available?]
   → [NEEDS CLARIFICATION: Should moving stock support partial quantities or only entire stock amounts?]
   → [NEEDS CLARIFICATION: What happens to pricing/lot information when moving stock?]
4. Fill User Scenarios & Testing section
   → User flow clear from screenshots and description
5. Generate Functional Requirements
   → Each requirement must be testable
6. Identify Key Entities
   → Stock entries, locations, components
7. Run Review Checklist
   → WARN "Spec has uncertainties - see clarifications"
8. Return: SUCCESS (spec ready for planning)
```

---

## ⚡ Quick Guidelines
- ✅ Focus on WHAT users need and WHY
- ❌ Avoid HOW to implement (no tech stack, APIs, code structure)
- 👥 Written for business stakeholders, not developers

---

## Clarifications

### Session 2025-10-04
- Q: Should the system log all stock operations (add/remove/move) in a permanent history that users can view? → A: Yes - Track all operations with timestamp, user, operation type, quantities (with +/- indicators), location, lot ID, price, and comments (matching existing stock history implementation)
- Q: Who should be allowed to perform stock operations (add, remove, move)? → A: Admin users only - stock operations are CRUD operations requiring admin privileges
- Q: When a user attempts to remove more stock than available at a location, what should happen? → A: Auto-adjust - Automatically cap removal at available quantity
- Q: When stock is moved between locations, what should happen to pricing and lot information? → A: Preserve all - Copy pricing and lot data to destination location
- Q: How should the system handle concurrent stock modifications when multiple admins modify the same component/location simultaneously? → A: Pessimistic locking - Lock location during operation, block others
- Q: Where should stock operation forms display? → A: Forms must open inline within the expanded component row, not as modal dialogs or separate pages. Multiple rows can have forms open simultaneously, with each operation scoped to its respective component.

### Session 2025-10-05
- Q: When merging stock at a destination location that already has the component (with different pricing/lot information), how should the system handle the pricing conflict? → A: Average the prices weighted by quantities
- Q: When stock history is displayed in the component row expansion, should it show all historical operations or be limited to recent entries? → A: Paginated (10 per page)
- Q: When a pessimistic lock blocks a stock operation, how long should the lock timeout be before automatically releasing? → A: 30 seconds
- Q: Should the stock history export feature support multiple formats or just one? → A: CSV, Excel, and JSON
- Q: When the "Add Stock" form has validation errors (e.g., invalid quantity), should the system behavior be: → A: Highlight fields in red, disable submit until fixed

---

## User Scenarios & Testing

### Primary User Story
Admin users need to manage component stock across different storage locations by adding new stock (with pricing and lot information), removing stock when components are used or discarded, and moving stock between locations to reorganize inventory.

### Acceptance Scenarios

**Add Stock**
1. **Given** a component row is expanded, **When** user selects "Add Stock" from the row expansion menu, **Then** system displays a multi-step form inline within the expanded row with quantity/pricing and storage location options
2. **Given** user is on "Enter manually" tab in the inline form, **When** user enters quantity and pricing (per component or entire lot), **Then** system calculates and displays total lot price
3. **Given** user completes quantity/pricing step, **When** user selects or creates a storage location, **Then** system adds stock entry with all provided information
4. **Given** user is on "Receive against an order" tab, **When** user selects an order, **Then** system pre-fills quantity and pricing from order details
5. **Given** user completes add stock workflow, **When** stock is successfully added, **Then** system updates component's total quantity and displays success confirmation
6. **Given** multiple component rows are expanded with add stock forms open, **When** user submits a form, **Then** system applies the operation only to the component associated with that specific row

**Remove Stock**
1. **Given** a component row is expanded and has stock in one or more locations, **When** user selects "Remove Stock" from the row expansion menu, **Then** system displays a simple form inline within the expanded row showing available locations with quantities
2. **Given** remove stock form is open in the expanded row, **When** user selects a location and enters quantity to remove, **Then** system validates quantity against available stock
3. **Given** user enters valid quantity and optional comments, **When** user confirms removal, **Then** system reduces stock at that location and updates total quantity
4. **Given** user removes all stock from a location, **When** removal is confirmed, **Then** system removes the stock entry entirely
5. **Given** multiple component rows have remove stock forms open, **When** user submits a form, **Then** system applies the removal only to the component associated with that specific row

**Move Stock**
1. **Given** a component row is expanded and has stock in multiple locations, **When** user selects "Move Stock" from the row expansion menu, **Then** system displays a form inline within the expanded row with source location pre-selected (current row's location)
2. **Given** move stock form is open in the expanded row, **When** user views destination options, **Then** system shows existing locations that already contain this component and option for "Other locations that can accept this part"
3. **Given** user selects an existing location as destination, **When** user enters quantity to move, **Then** system validates quantity against source location's available stock
4. **Given** user selects "Other locations" option, **When** user chooses or creates a new location, **Then** system allows moving stock to a location that doesn't currently have this component
5. **Given** user enters valid move parameters and optional comments, **When** user confirms move, **Then** system transfers stock from source to destination location atomically
6. **Given** user moves all stock from a location, **When** move is confirmed, **Then** system removes the source stock entry and creates/updates destination entry
7. **Given** multiple component rows have move stock forms open, **When** user submits a form, **Then** system applies the move operation only to the component associated with that specific row

**Stock History**
1. **Given** a component row is expanded, **When** user views the expanded row content, **Then** system displays the complete stock history for that component in table format
2. **Given** stock history table is displayed in the expanded row, **When** user views the table, **Then** system shows columns for Date, Quantity (with +/- indicators), Location, Lot ID, Price, Comments, and User
3. **Given** stock history table contains multiple entries, **When** user interacts with column headers, **Then** system allows sorting by any column
4. **Given** stock history is displayed, **When** user performs a stock operation (add/remove/move), **Then** system immediately updates the history table with the new entry

### Edge Cases
- What happens when user tries to move stock but selects the same source and destination location? → System prevents selection via FR-031
- How does system handle validation errors during multi-step add stock workflow? → Highlight invalid fields in red and disable submit button until corrected
- What happens when an admin attempts to modify stock while another admin has the location locked? → Display error message, auto-retry after lock expires (30s timeout)

## Requirements

### Functional Requirements

**Add Stock**
- **FR-001**: System MUST provide an "Add Stock" option in the component row expansion menu
- **FR-002**: System MUST display stock operation forms inline within the expanded component row, not as modal dialogs or separate pages
- **FR-003**: System MUST display a multi-step form for adding stock with tabs for "Enter manually", "Receive against an order", and "Add to order"
- **FR-004**: System MUST allow users to enter quantity for new stock
- **FR-005**: System MUST allow users to specify pricing as "No price", "Per component", or "Entire lot"
- **FR-006**: System MUST calculate and display total lot price based on quantity and per-component price
- **FR-007**: System MUST allow users to select an existing storage location or create a new location
- **FR-008**: System MUST support receiving stock against an existing order with pre-filled quantity and pricing
- **FR-009**: System MUST allow users to enter additional information (comments, lot data) for stock entries
- **FR-010**: System MUST update component's total quantity across all locations after adding stock
- **FR-011**: System MUST provide clear visual feedback when stock is successfully added
- **FR-012**: System MUST support multiple component rows having add stock forms open simultaneously
- **FR-013**: System MUST scope each stock operation to the specific component row where the form is displayed
- **FR-014**: System MUST highlight invalid form fields in red when validation fails
- **FR-015**: System MUST disable form submit button until all validation errors are corrected

**Remove Stock**
- **FR-016**: System MUST provide a "Remove Stock" option in the component row expansion menu
- **FR-017**: System MUST display a simplified inline form within the expanded row showing the source location and current quantity
- **FR-018**: System MUST allow users to enter quantity to remove
- **FR-019**: System MUST automatically cap removal quantity at available stock if user enters a value exceeding current quantity
- **FR-020**: System MUST display visual feedback when removal quantity is auto-adjusted to available maximum
- **FR-021**: System MUST allow users to add optional comments explaining the stock removal
- **FR-022**: System MUST reduce stock quantity at the source location when removal is confirmed
- **FR-023**: System MUST remove stock entry entirely if all stock is removed from a location
- **FR-024**: System MUST update component's total quantity across all locations after removing stock
- **FR-025**: System MUST support multiple component rows having remove stock forms open simultaneously

**Move Stock**
- **FR-026**: System MUST provide a "Move Stock" option in the component row expansion menu
- **FR-027**: System MUST display an inline form within the expanded row showing source location (pre-selected from current row) and destination options
- **FR-028**: System MUST show existing locations that already contain the component as destination options
- **FR-029**: System MUST show an "Other locations that can accept this part" option for moving to new locations
- **FR-030**: System MUST allow users to enter quantity to move
- **FR-031**: System MUST automatically cap move quantity at available stock if user enters a value exceeding source quantity
- **FR-032**: System MUST display visual feedback when move quantity is auto-adjusted to available maximum
- **FR-033**: System MUST prevent users from selecting the same location as both source and destination
- **FR-034**: System MUST allow users to add optional comments describing the stock movement
- **FR-035**: System MUST transfer stock from source to destination location atomically (both operations succeed or both fail)
- **FR-036**: System MUST preserve pricing and lot information when moving stock (copy from source to destination)
- **FR-037**: System MUST remove source stock entry if all stock is moved from that location
- **FR-038**: System MUST create new stock entry at destination if location doesn't currently have the component, inheriting pricing and lot data from source
- **FR-039**: System MUST update existing stock entry at destination if location already has the component, merging quantities and calculating weighted average price based on combined quantities
- **FR-040**: System MUST maintain component's total quantity unchanged after moving stock (only location distribution changes)
- **FR-041**: System MUST support multiple component rows having move stock forms open simultaneously

**Stock History**
- **FR-042**: System MUST display stock history table in the component row expansion area
- **FR-043**: System MUST show stock history table with columns: Date, Quantity (with +/- indicators), Location, Lot ID, Price, Comments, and User
- **FR-044**: System MUST allow users to sort stock history by any column
- **FR-045**: System MUST update the stock history table immediately after any stock operation (add/remove/move) is completed
- **FR-046**: System MUST display the complete history for the specific component being viewed (not mixed with other components)
- **FR-047**: System MUST paginate stock history display showing 10 entries per page
- **FR-048**: System MUST provide navigation controls to move between history pages

**General Requirements**
- **FR-049**: System MUST validate all stock operations before execution to prevent negative quantities
- **FR-050**: System MUST acquire a lock on the affected component/location before executing any stock operation
- **FR-051**: System MUST block concurrent stock operations on the same component/location until the lock is released
- **FR-052**: System MUST release locks immediately after stock operation completes or is cancelled
- **FR-053**: System MUST automatically release locks after 30 seconds if operation has not completed
- **FR-054**: System MUST display clear error message when stock operation cannot proceed due to an active lock by another user
- **FR-055**: System MUST provide clear error messages when stock operations fail validation
- **FR-056**: System MUST allow users to cancel any stock operation before confirmation without making changes
- **FR-057**: System MUST log all stock operations (add, remove, move) in a permanent stock history
- **FR-058**: System MUST record timestamp, user, operation type, quantities (with +/- indicators), location(s), lot ID, price, and comments for each history entry
- **FR-059**: System MUST allow users to export stock history data in CSV, Excel (XLSX), and JSON formats
- **FR-060**: System MUST restrict all stock operations (add, remove, move) to admin users only
- **FR-061**: System MUST hide or disable stock operation menu items for non-admin users
- **FR-062**: System MUST return appropriate error responses if non-admin users attempt to access stock operation endpoints

### Key Entities

- **Stock Entry**: Represents a quantity of a specific component stored at a specific location, including quantity, pricing information, lot data, and comments
- **Storage Location**: A physical or logical location where components can be stored (e.g., "F1-19", "In-Transit")
- **Component**: The electronic part or item being managed, which can have stock across multiple locations
- **Stock History Entry**: A permanent record of a stock operation including timestamp, user, operation type (add/remove/move), quantity change with +/- indicator, affected location(s), lot ID, price, and comments

---

## Review & Acceptance Checklist
*GATE: Automated checks run during main() execution*

### Content Quality
- [x] No implementation details (languages, frameworks, APIs)
- [x] Focused on user value and business needs
- [x] Written for non-technical stakeholders
- [x] All mandatory sections completed

### Requirement Completeness
- [ ] No [NEEDS CLARIFICATION] markers remain
- [x] Requirements are testable and unambiguous
- [x] Success criteria are measurable
- [x] Scope is clearly bounded
- [ ] Dependencies and assumptions identified

### Constitutional Alignment (PartsHub v1.2.0)
- [x] API-first requirements specified (backend before frontend)
- [x] Test scenarios defined for TDD (acceptance criteria testable)
- [ ] Access control requirements clear (Anonymous/Authenticated/Admin) - NEEDS CLARIFICATION
- [x] Test isolation considered (tests can be independently verified)
- [x] Documentation requirements identified (what docs need updates)
- [x] No tool/AI attribution in specification text

---

## Execution Status
*Updated by main() during processing*

- [x] User description parsed
- [x] Key concepts extracted
- [x] Ambiguities marked
- [x] User scenarios defined
- [x] Requirements generated
- [x] Entities identified
- [ ] Review checklist passed (has clarifications pending)

---
