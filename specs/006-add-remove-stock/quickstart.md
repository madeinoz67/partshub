# Quickstart: Stock Management Operations Testing

**Feature**: Add/Remove/Move stock operations from component row expansion menu
**Branch**: 006-add-remove-stock
**Date**: 2025-10-04

## Overview

This quickstart guide provides step-by-step instructions for testing the stock management feature, including:
- Setting up development environment
- Creating test data
- Testing each user story (Add/Remove/Move stock)
- Validating stock history and audit trail
- Testing concurrent operations and pessimistic locking

---

## 1. Setup

### Prerequisites

- Python 3.11+ installed
- Node.js 18+ installed
- `uv` package manager installed
- Git repository cloned

### Start Development Servers

**Terminal 1: Backend Server**
```bash
# From project root
cd /Users/seaton/Documents/src/partshub
make dev-backend

# Alternatively, run directly:
cd backend
uv run --project .. uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

Backend will be available at: `http://localhost:8000`
API docs (Swagger UI): `http://localhost:8000/docs`

**Terminal 2: Frontend Server**
```bash
# From project root
cd /Users/seaton/Documents/src/partshub
make dev-frontend

# Alternatively, run directly:
cd frontend
npm run dev
```

Frontend will be available at: `http://localhost:9000` (or the port shown in terminal)

**Terminal 3: Documentation Server (Optional)**
```bash
# From project root
cd /Users/seaton/Documents/src/partshub
make docs

# Alternatively:
uv run mkdocs serve
```

Documentation will be available at: `http://localhost:8001`

### Verify Setup

1. Open browser to `http://localhost:9000`
2. Verify you can see the PartsHub UI
3. Check backend health: `curl http://localhost:8000/health`
4. Check API docs: `http://localhost:8000/docs`

---

## 2. Authentication Setup

### Create Admin User

The stock operations require admin authentication (FR-051). Create an admin user for testing:

**Option A: Using Backend CLI (if available)**
```bash
cd backend
uv run --project .. python -m src.cli create-user \
  --username admin \
  --email admin@partshub.local \
  --password admin123 \
  --role admin
```

**Option B: Using SQLite Directly**
```bash
cd backend
sqlite3 partshub.db

-- Create admin user (adjust password hash as needed)
INSERT INTO users (id, username, email, password_hash, role, is_active, created_at)
VALUES (
  '550e8400-e29b-41d4-a716-446655440099',
  'admin',
  'admin@partshub.local',
  -- Use your hashing mechanism here
  'hashed_password_here',
  'admin',
  1,
  datetime('now')
);

.quit
```

**Option C: Using Python Script**
```python
# create_admin.py
import asyncio
from backend.src.database import SessionLocal
from backend.src.models.user import User
from backend.src.auth.password import get_password_hash
import uuid

def create_admin():
    db = SessionLocal()
    try:
        admin_user = User(
            id=str(uuid.uuid4()),
            username="admin",
            email="admin@partshub.local",
            password_hash=get_password_hash("admin123"),
            role="admin",
            is_active=True
        )
        db.add(admin_user)
        db.commit()
        print(f"Admin user created: {admin_user.username} (ID: {admin_user.id})")
    finally:
        db.close()

if __name__ == "__main__":
    create_admin()
```

### Login and Get JWT Token

**Via API (curl)**
```bash
# Login
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin123"}'

# Response will contain:
# {
#   "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
#   "token_type": "bearer",
#   "user": {...}
# }

# Save token for subsequent requests
export TOKEN="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

**Via Frontend UI**
1. Navigate to `http://localhost:9000`
2. Click "Login" in navigation
3. Enter username: `admin`, password: `admin123`
4. Verify you're logged in (admin badge/indicator should appear)
5. Check browser DevTools > Application > Local Storage for token

---

## 3. Create Test Data

### Test Components and Locations

Use the following SQL script or API calls to create test data:

**SQL Script (backend/test_data.sql)**
```sql
-- Storage Locations
INSERT INTO storage_locations (id, name, description, type, created_at, updated_at)
VALUES
  ('loc-shelf-a', 'Shelf A', 'Main storage shelf A', 'shelf', datetime('now'), datetime('now')),
  ('loc-shelf-b', 'Shelf B', 'Secondary storage shelf B', 'shelf', datetime('now'), datetime('now')),
  ('loc-bin-1', 'Bin 1', 'Small parts bin 1', 'bin', datetime('now'), datetime('now')),
  ('loc-lab', 'Lab Bench', 'Active project workspace', 'other', datetime('now'), datetime('now'));

-- Test Components
INSERT INTO components (
  id, name, manufacturer_part_number, manufacturer, component_type,
  value, package, quantity_on_hand, quantity_ordered, minimum_stock,
  created_at, updated_at
)
VALUES
  (
    'comp-resistor-1k',
    '1kΩ Resistor 0805',
    'RC0805FR-071KL',
    'Yageo',
    'Resistor',
    '1kΩ',
    '0805',
    0,  -- Will add stock via API
    0,
    50,
    datetime('now'),
    datetime('now')
  ),
  (
    'comp-capacitor-10uf',
    '10µF Capacitor 0603',
    'CL10A106KP8NNNC',
    'Samsung',
    'Capacitor',
    '10µF',
    '0603',
    0,
    0,
    25,
    datetime('now'),
    datetime('now')
  ),
  (
    'comp-led-red',
    'Red LED 5mm',
    'WP7113SRD',
    'Kingbright',
    'LED',
    'Red',
    '5mm',
    0,
    0,
    100,
    datetime('now'),
    datetime('now')
  );

-- Initial component locations (for testing Remove and Move)
INSERT INTO component_locations (
  id, component_id, storage_location_id, quantity_on_hand,
  unit_cost_at_location, created_at, updated_at
)
VALUES
  -- Resistors split between two locations
  (
    'cl-resistor-shelf-a',
    'comp-resistor-1k',
    'loc-shelf-a',
    100,
    0.02,
    datetime('now'),
    datetime('now')
  ),
  (
    'cl-resistor-shelf-b',
    'comp-resistor-1k',
    'loc-shelf-b',
    50,
    0.02,
    datetime('now'),
    datetime('now')
  ),
  -- Capacitors in single location
  (
    'cl-capacitor-bin-1',
    'comp-capacitor-10uf',
    'loc-bin-1',
    75,
    0.15,
    datetime('now'),
    datetime('now')
  );

-- Update component total quantities
UPDATE components SET quantity_on_hand = 150 WHERE id = 'comp-resistor-1k';
UPDATE components SET quantity_on_hand = 75 WHERE id = 'comp-capacitor-10uf';
UPDATE components SET quantity_on_hand = 0 WHERE id = 'comp-led-red';
```

**Load Test Data**
```bash
cd backend
sqlite3 partshub.db < test_data.sql

# Verify data loaded
sqlite3 partshub.db "SELECT name, quantity_on_hand FROM components;"
sqlite3 partshub.db "SELECT c.name, sl.name, cl.quantity_on_hand
  FROM component_locations cl
  JOIN components c ON c.id = cl.component_id
  JOIN storage_locations sl ON sl.id = cl.storage_location_id;"
```

---

## 4. Test Scenario 1: Add Stock

### User Story
Admin adds 200 red LEDs to "Shelf A" with pricing information and lot tracking.

### Prerequisites
- Component exists: "Red LED 5mm" (comp-led-red)
- Location exists: "Shelf A" (loc-shelf-a)
- User is authenticated as admin

### Test Steps

**Step 1: Navigate to Component List**
1. Open `http://localhost:9000/components` in browser
2. Find "Red LED 5mm" in the list
3. Click the expand arrow to open component row details
4. Verify current stock shows 0 units

**Step 2: Open Add Stock Form**
1. In expanded row, click the menu icon (three dots)
2. Select "Add Stock" from dropdown menu
3. Verify inline form appears within the expanded row
4. Verify form has two tabs: "Enter manually" and "Receive against an order"
5. Ensure "Enter manually" tab is active by default

**Step 3: Fill Add Stock Form**
1. Enter quantity: `200`
2. Select pricing type: "Per component"
3. Enter unit price: `0.50`
4. Verify total price auto-calculates: `$100.00`
5. Click "Next" to proceed to location selection
6. Select location: "Shelf A"
7. Enter lot ID: `LOT-2025-Q1-LED-RED`
8. Enter comments: `Initial stock - purchased from Digi-Key`

**Step 4: Submit Form**
1. Click "Add Stock" button
2. Verify success notification appears
3. Verify form closes and returns to stock view tab
4. Verify component row shows updated quantity: 200 units
5. Verify "Shelf A" location appears in locations list with 200 units

**Step 5: Verify Stock History**
1. In expanded row, click "History" tab
2. Verify new transaction appears with:
   - Date/time: Current timestamp
   - Quantity: `+200` (positive indicator)
   - Location: "Shelf A"
   - Lot ID: "LOT-2025-Q1-LED-RED"
   - Price: `$0.50/unit ($100.00 total)`
   - Comments: "Initial stock - purchased from Digi-Key"
   - User: "admin"

### API Testing (Alternative)

```bash
# Add stock via API
curl -X POST http://localhost:8000/api/v1/components/comp-led-red/stock/add \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "location_id": "loc-shelf-a",
    "quantity": 200,
    "price_per_unit": 0.50,
    "lot_id": "LOT-2025-Q1-LED-RED",
    "comments": "Initial stock - purchased from Digi-Key"
  }'

# Expected response:
# {
#   "success": true,
#   "message": "Stock added successfully",
#   "transaction_id": "...",
#   "component_id": "comp-led-red",
#   "location_id": "loc-shelf-a",
#   "quantity_added": 200,
#   "previous_quantity": 0,
#   "new_quantity": 200,
#   "total_stock": 200
# }

# Verify in database
sqlite3 backend/partshub.db \
  "SELECT * FROM component_locations WHERE component_id='comp-led-red';"

sqlite3 backend/partshub.db \
  "SELECT transaction_type, quantity_change, lot_id, price_per_unit
   FROM stock_transactions
   WHERE component_id='comp-led-red'
   ORDER BY created_at DESC LIMIT 1;"
```

### Expected Results
- ✅ Stock added successfully with pricing and lot data
- ✅ ComponentLocation created with quantity=200
- ✅ StockTransaction created with transaction_type=ADD
- ✅ Component.quantity_on_hand updated to 200
- ✅ Success notification displayed to user

---

## 5. Test Scenario 2: Remove Stock (with Auto-Capping)

### User Story
Admin removes 30 resistors from "Shelf B", but accidentally requests 100 (more than available). System auto-caps at 50 (available quantity).

### Prerequisites
- Component exists: "1kΩ Resistor 0805" (comp-resistor-1k)
- Location "Shelf B" has 50 units available
- User is authenticated as admin

### Test Steps

**Step 1: Navigate and Open Remove Form**
1. Open `http://localhost:9000/components`
2. Find "1kΩ Resistor 0805" in the list
3. Expand the component row
4. Verify "Stock" tab shows multiple locations (Shelf A: 100, Shelf B: 50)
5. Click menu icon and select "Remove Stock"

**Step 2: Fill Remove Stock Form**
1. Verify inline form appears with location selector
2. Select location: "Shelf B" (available: 50 units)
3. Enter quantity: `100` (exceeding available stock)
4. Verify warning notification appears: "Quantity capped at 50 (maximum available)"
5. Verify quantity field auto-corrects to: `50`
6. Enter comments: `Testing auto-cap behavior`

**Step 3: Submit and Verify**
1. Click "Remove Stock" button
2. Verify success notification: "Stock removed successfully (quantity auto-capped)"
3. Verify component row updates:
   - Total quantity: 150 → 100 (decreased by 50)
   - Location "Shelf B" removed from locations list (quantity reached 0)
   - Location "Shelf A" still shows 100 units
4. Switch to "History" tab
5. Verify transaction shows:
   - Quantity: `-50` (negative indicator)
   - Location: "Shelf B"
   - Comments: "Testing auto-cap behavior"

### API Testing (Alternative)

```bash
# Attempt to remove more than available (auto-cap test)
curl -X POST http://localhost:8000/api/v1/components/comp-resistor-1k/stock/remove \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "location_id": "loc-shelf-b",
    "quantity": 100,
    "comments": "Testing auto-cap behavior"
  }'

# Expected response (auto-capped):
# {
#   "success": true,
#   "message": "Stock removed successfully (quantity auto-capped at available stock)",
#   "transaction_id": "...",
#   "component_id": "comp-resistor-1k",
#   "location_id": "loc-shelf-b",
#   "quantity_removed": 50,
#   "requested_quantity": 100,
#   "capped": true,
#   "previous_quantity": 50,
#   "new_quantity": 0,
#   "location_deleted": true,
#   "total_stock": 100
# }

# Verify location was deleted
sqlite3 backend/partshub.db \
  "SELECT * FROM component_locations WHERE id='cl-resistor-shelf-b';"
# Should return no rows

# Verify transaction recorded correctly
sqlite3 backend/partshub.db \
  "SELECT transaction_type, quantity_change, previous_quantity, new_quantity
   FROM stock_transactions
   WHERE component_id='comp-resistor-1k'
   AND from_location_id='loc-shelf-b'
   ORDER BY created_at DESC LIMIT 1;"
# Should show: REMOVE | -50 | 50 | 0
```

### Expected Results
- ✅ Auto-capping triggers when quantity exceeds available
- ✅ User sees warning notification
- ✅ Quantity auto-corrects to maximum available (50)
- ✅ Stock removed successfully (50 units)
- ✅ ComponentLocation deleted (quantity reached 0)
- ✅ StockTransaction created with quantity_change=-50

---

## 6. Test Scenario 3: Move Stock (with Atomicity)

### User Story
Admin moves 25 capacitors from "Bin 1" to "Lab Bench" to prepare for active project work. System atomically updates both locations.

### Prerequisites
- Component exists: "10µF Capacitor 0603" (comp-capacitor-10uf)
- Source location "Bin 1" has 75 units
- Destination location "Lab Bench" exists but has 0 units of this component
- User is authenticated as admin

### Test Steps

**Step 1: Navigate and Open Move Form**
1. Open `http://localhost:9000/components`
2. Find "10µF Capacitor 0603" in the list
3. Expand the component row
4. Verify "Stock" tab shows location: "Bin 1" with 75 units
5. Click menu icon and select "Move Stock"

**Step 2: Fill Move Stock Form**
1. Verify inline form appears
2. Source location pre-selected: "Bin 1" (75 units available)
3. View destination options:
   - Section: "Other locations that can accept this part"
   - List should include: "Lab Bench", "Shelf A", "Shelf B"
4. Select destination: "Lab Bench"
5. Enter quantity: `25`
6. Enter comments: `Moving to lab for Project Alpha assembly`

**Step 3: Submit and Verify Atomicity**
1. Click "Move Stock" button
2. Verify success notification appears
3. Verify component row updates:
   - Total quantity unchanged: 75 units (move doesn't change total)
   - Location "Bin 1" now shows: 50 units
   - Location "Lab Bench" now shows: 25 units (newly created)
4. Switch to "History" tab
5. Verify transaction shows:
   - Type: MOVE
   - Quantity: `0` (no net change, but shows move)
   - From: "Bin 1"
   - To: "Lab Bench"
   - Moved quantity: 25 units
   - Comments: "Moving to lab for Project Alpha assembly"

**Step 4: Verify Pricing Inheritance**
1. Check that "Lab Bench" location inherited unit cost from "Bin 1"
2. Verify in database that `unit_cost_at_location` matches source

### API Testing (Alternative)

```bash
# Move stock between locations
curl -X POST http://localhost:8000/api/v1/components/comp-capacitor-10uf/stock/move \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "source_location_id": "loc-bin-1",
    "destination_location_id": "loc-lab",
    "quantity": 25,
    "comments": "Moving to lab for Project Alpha assembly"
  }'

# Expected response:
# {
#   "success": true,
#   "message": "Stock moved successfully (destination location created)",
#   "transaction_id": "...",
#   "component_id": "comp-capacitor-10uf",
#   "source_location_id": "loc-bin-1",
#   "destination_location_id": "loc-lab",
#   "quantity_moved": 25,
#   "requested_quantity": 25,
#   "capped": false,
#   "source_previous_quantity": 75,
#   "source_new_quantity": 50,
#   "source_location_deleted": false,
#   "destination_previous_quantity": 0,
#   "destination_new_quantity": 25,
#   "destination_location_created": true,
#   "total_stock": 75,
#   "pricing_inherited": true
# }

# Verify both locations updated atomically
sqlite3 backend/partshub.db \
  "SELECT sl.name, cl.quantity_on_hand, cl.unit_cost_at_location
   FROM component_locations cl
   JOIN storage_locations sl ON sl.id = cl.storage_location_id
   WHERE cl.component_id='comp-capacitor-10uf';"
# Should show:
# Bin 1 | 50 | 0.15
# Lab Bench | 25 | 0.15

# Verify move transaction
sqlite3 backend/partshub.db \
  "SELECT transaction_type, quantity_change, from_location_id, to_location_id
   FROM stock_transactions
   WHERE component_id='comp-capacitor-10uf'
   AND transaction_type='move'
   ORDER BY created_at DESC LIMIT 1;"
```

### Expected Results
- ✅ Stock moved atomically (both locations updated or neither)
- ✅ Source location decremented: 75 → 50
- ✅ Destination location created with 25 units
- ✅ Pricing inherited from source to destination
- ✅ Total component quantity unchanged (75)
- ✅ StockTransaction created with transaction_type=MOVE

---

## 7. Test Scenario 4: Concurrent Operations (Pessimistic Locking)

### User Story
Two admins attempt to modify the same component/location simultaneously. Pessimistic locking ensures the second operation blocks until the first completes.

### Prerequisites
- Two browser sessions or API clients
- Both authenticated as admin users
- Component with stock at a location

### Test Steps (Manual)

**Session 1: Start Long-Running Operation**
1. Open first browser window at `http://localhost:9000/components`
2. Expand "1kΩ Resistor 0805" row
3. Click "Remove Stock"
4. Fill form but **DO NOT SUBMIT YET**
5. Keep form open (simulates long user interaction)

**Session 2: Attempt Concurrent Modification**
1. Open second browser window (incognito/private mode)
2. Login as admin
3. Navigate to same component "1kΩ Resistor 0805"
4. Expand row and click "Remove Stock"
5. Fill form quickly and submit

**Expected Behavior**
- Session 2's request should **block** waiting for Session 1's lock
- If Session 1 submits within timeout (10s): Session 2 succeeds after Session 1 completes
- If Session 1 exceeds timeout: Session 2 receives HTTP 409 Conflict error

### API Testing (Simulated Concurrency)

**Terminal 1: Start operation with artificial delay**
```bash
# This requires backend code modification to add delay
# Or use Python script with threading

# Python script: test_concurrent_stock.py
import requests
import threading
import time

TOKEN = "your_jwt_token_here"
BASE_URL = "http://localhost:8000"
COMPONENT_ID = "comp-resistor-1k"
LOCATION_ID = "loc-shelf-a"

def remove_stock_with_delay(delay_seconds, quantity, name):
    """Simulate stock removal with delay"""
    print(f"{name}: Starting operation...")

    response = requests.post(
        f"{BASE_URL}/api/v1/components/{COMPONENT_ID}/stock/remove",
        headers={
            "Authorization": f"Bearer {TOKEN}",
            "Content-Type": "application/json"
        },
        json={
            "location_id": LOCATION_ID,
            "quantity": quantity,
            "comments": f"Concurrent test - {name}"
        }
    )

    print(f"{name}: Status {response.status_code}")
    print(f"{name}: Response: {response.json()}")
    return response

# Test concurrent access
thread1 = threading.Thread(
    target=remove_stock_with_delay,
    args=(0, 10, "Thread-1")
)
thread2 = threading.Thread(
    target=remove_stock_with_delay,
    args=(0.5, 10, "Thread-2")  # Slight delay to ensure Thread-1 acquires lock first
)

thread1.start()
thread2.start()

thread1.join()
thread2.join()

print("Concurrent test completed")
```

**Run Test**
```bash
python test_concurrent_stock.py
```

**Expected Output**
```
Thread-1: Starting operation...
Thread-2: Starting operation...
Thread-1: Status 200
Thread-1: Response: {'success': true, 'quantity_removed': 10, ...}
Thread-2: Status 200  # Blocks until Thread-1 releases lock
Thread-2: Response: {'success': true, 'quantity_removed': 10, ...}
```

OR if lock timeout exceeded:
```
Thread-2: Status 409
Thread-2: Response: {'detail': 'Location is currently locked by another operation. Please try again.'}
```

### Expected Results
- ✅ First operation acquires pessimistic lock
- ✅ Second operation blocks waiting for lock
- ✅ Lock released after first operation commits
- ✅ Second operation proceeds after lock release
- ✅ No race conditions or data corruption

---

## 8. Validation Checks

### Data Integrity Checks

**Check Total Quantities Match**
```sql
-- Verify component.quantity_on_hand equals sum of location quantities
SELECT
  c.id,
  c.name,
  c.quantity_on_hand AS component_total,
  COALESCE(SUM(cl.quantity_on_hand), 0) AS locations_total,
  (c.quantity_on_hand - COALESCE(SUM(cl.quantity_on_hand), 0)) AS difference
FROM components c
LEFT JOIN component_locations cl ON cl.component_id = c.id
GROUP BY c.id
HAVING difference != 0;

-- Should return 0 rows (no discrepancies)
```

**Check Stock History Consistency**
```sql
-- Verify all transactions have corresponding component and location records
SELECT st.id, st.component_id, st.transaction_type
FROM stock_transactions st
LEFT JOIN components c ON c.id = st.component_id
WHERE c.id IS NULL;

-- Should return 0 rows (no orphaned transactions)
```

**Check No Negative Quantities**
```sql
-- Verify no location has negative quantity
SELECT * FROM component_locations WHERE quantity_on_hand < 0;

-- Should return 0 rows
```

### Stock History Display

**Frontend Verification**
1. Expand any component with stock history
2. Click "History" tab
3. Verify table shows columns:
   - Date (formatted timestamp)
   - Quantity (with +/- indicators)
   - Location (from/to for moves)
   - Lot ID
   - Price (unit and total)
   - Comments
   - User
4. Verify sorting works (newest first by default)
5. Verify filtering works (by transaction type, date range)

**API Verification**
```bash
# Fetch stock history
curl -X GET "http://localhost:8000/api/v1/components/comp-led-red/stock-history?limit=10" \
  -H "Authorization: Bearer $TOKEN"

# Expected response:
# {
#   "transactions": [
#     {
#       "id": "...",
#       "transaction_type": "add",
#       "quantity_change": 200,
#       "created_at": "2025-10-04T12:00:00Z",
#       "lot_id": "LOT-2025-Q1-LED-RED",
#       "price_per_unit": 0.50,
#       "total_price": 100.00,
#       "location": "Shelf A",
#       "user": "admin",
#       "comments": "Initial stock - purchased from Digi-Key"
#     }
#   ],
#   "total": 1
# }
```

---

## 9. Error Scenarios

### Test Non-Admin Access

**Setup**: Login as non-admin user

**Test**:
```bash
# Attempt stock operation without admin role
curl -X POST http://localhost:8000/api/v1/components/comp-led-red/stock/add \
  -H "Authorization: Bearer $NON_ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "location_id": "loc-shelf-a",
    "quantity": 10
  }'

# Expected response:
# HTTP 403 Forbidden
# {
#   "detail": "Admin privileges required for stock operations"
# }
```

### Test Invalid Component ID

```bash
curl -X POST http://localhost:8000/api/v1/components/invalid-component-id/stock/add \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "location_id": "loc-shelf-a",
    "quantity": 10
  }'

# Expected response:
# HTTP 404 Not Found
# {
#   "detail": "Component not found"
# }
```

### Test Same Source/Destination (Move)

```bash
curl -X POST http://localhost:8000/api/v1/components/comp-resistor-1k/stock/move \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "source_location_id": "loc-shelf-a",
    "destination_location_id": "loc-shelf-a",
    "quantity": 10
  }'

# Expected response:
# HTTP 400 Bad Request
# {
#   "detail": "Source and destination locations must be different"
# }
```

---

## 10. Cleanup

### Reset Test Data

```bash
# Delete test transactions
sqlite3 backend/partshub.db \
  "DELETE FROM stock_transactions WHERE component_id IN ('comp-led-red', 'comp-resistor-1k', 'comp-capacitor-10uf');"

# Delete test component locations
sqlite3 backend/partshub.db \
  "DELETE FROM component_locations WHERE component_id IN ('comp-led-red', 'comp-resistor-1k', 'comp-capacitor-10uf');"

# Delete test components
sqlite3 backend/partshub.db \
  "DELETE FROM components WHERE id IN ('comp-led-red', 'comp-resistor-1k', 'comp-capacitor-10uf');"

# Delete test locations
sqlite3 backend/partshub.db \
  "DELETE FROM storage_locations WHERE id IN ('loc-shelf-a', 'loc-shelf-b', 'loc-bin-1', 'loc-lab');"
```

### Stop Servers

```bash
# Stop backend (Terminal 1): Ctrl+C
# Stop frontend (Terminal 2): Ctrl+C
# Stop docs (Terminal 3): Ctrl+C
```

---

## 11. Troubleshooting

### Backend Won't Start

**Check Python version**:
```bash
python --version  # Should be 3.11+
```

**Check database**:
```bash
ls -la backend/partshub.db
sqlite3 backend/partshub.db ".tables"
```

**Check dependencies**:
```bash
cd backend
uv run --project .. pip list
```

### Frontend Won't Start

**Check Node version**:
```bash
node --version  # Should be 18+
```

**Reinstall dependencies**:
```bash
cd frontend
rm -rf node_modules package-lock.json
npm install
```

### JWT Token Expired

**Symptom**: API returns 401 Unauthorized

**Solution**: Re-login and get fresh token
```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin123"}'
```

### Database Lock Errors

**Symptom**: "database is locked" error

**Solution**: Ensure only one process is accessing SQLite database
```bash
# Check for stale locks
fuser backend/partshub.db

# Kill stale processes if needed
pkill -f "uvicorn"
```

### Stock Quantities Don't Match

**Symptom**: Component total doesn't match sum of locations

**Solution**: Run integrity check and debug
```sql
-- Find discrepancies
SELECT c.id, c.name, c.quantity_on_hand, SUM(cl.quantity_on_hand)
FROM components c
LEFT JOIN component_locations cl ON cl.component_id = c.id
GROUP BY c.id
HAVING c.quantity_on_hand != COALESCE(SUM(cl.quantity_on_hand), 0);
```

---

## 12. Success Criteria

All tests pass if:

- ✅ Add Stock creates ComponentLocation and StockTransaction with correct data
- ✅ Remove Stock decrements quantity and deletes location when quantity = 0
- ✅ Remove Stock auto-caps at available quantity with visual feedback
- ✅ Move Stock atomically updates both source and destination
- ✅ Move Stock inherits pricing from source to destination
- ✅ Stock history displays all transactions with +/- indicators
- ✅ Pessimistic locking blocks concurrent operations
- ✅ Admin-only access enforced (403 for non-admin)
- ✅ Validation errors return clear messages (400)
- ✅ Component totals match sum of location quantities
- ✅ No negative quantities in database
- ✅ All audit trails immutable (no updates to stock_transactions)

---

**Document Status**: Complete
**Last Updated**: 2025-10-04
