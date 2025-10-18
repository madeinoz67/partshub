# Reorder Alerts - User Guide

**New in v0.5.0**: Automatic low-stock monitoring and alerting to ensure you never run out of critical components.

## Overview

PartsHub's Reorder Alerts feature automatically monitors your inventory and notifies you when component stock falls below configured thresholds. This eliminates manual stock checking and ensures timely reordering.

## Key Benefits

- **Never run out of critical parts** - Automatic monitoring prevents stockouts
- **Zero manual intervention** - Database triggers create alerts instantly
- **Per-location control** - Set different thresholds for each storage location
- **Severity-based prioritization** - Focus on critical shortages first
- **Complete audit trail** - Track alert lifecycle from creation to resolution
- **Dashboard visibility** - Real-time reports and statistics

## How It Works

### 1. Configuration Phase

Set reorder thresholds for components at specific storage locations:

```
Component: 10kΩ Resistor 0805
Location: Bin A1
Threshold: 50 units
Enabled: Yes
```

### 2. Automatic Monitoring

Database triggers continuously monitor stock levels. When stock falls below threshold:

```
Current Stock: 45 units  ← Below threshold (50)
Alert Created: Automatically, instantly
Severity: Calculated based on shortage
```

### 3. Alert Lifecycle

Alerts follow a workflow from creation to resolution:

```
ACTIVE → User Action → DISMISSED / ORDERED → Auto-Resolve → RESOLVED
```

### 4. Resolution

When stock is replenished above threshold, alerts automatically resolve:

```
Stock Added: 100 units
New Total: 145 units  ← Above threshold (50)
Alert Resolved: Automatically
```

---

## Getting Started

### Step 1: Enable Reorder Monitoring

**(Admin users only)**

1. Navigate to component details page
2. Expand the storage location row
3. Click "Configure Reorder Alert"
4. Set threshold (e.g., 50 units)
5. Enable monitoring
6. Save

If current stock is below threshold, an alert is created immediately.

### Step 2: View Active Alerts

Access the Reorder Alerts dashboard:

1. Navigate to **Inventory → Reorder Alerts**
2. View list of active alerts sorted by severity
3. Filter by component, location, or minimum shortage
4. See real-time shortage metrics

### Step 3: Process Alerts

For each alert, you can:

- **Mark as Ordered** - After placing supplier order
- **Dismiss** - If reorder is not needed
- **Let Auto-Resolve** - When stock is replenished

---

## Alert Details

### Alert Information

Each alert displays:

| Field | Description |
|-------|-------------|
| **Component** | Name and part number |
| **Location** | Storage location name |
| **Current Stock** | Quantity on hand |
| **Threshold** | Reorder threshold |
| **Shortage** | Units below threshold |
| **Severity** | Critical / High / Medium / Low |
| **Created** | When alert was generated |
| **Status** | Active / Dismissed / Ordered / Resolved |

### Severity Levels

Alerts are prioritized by severity:

| Severity | Shortage | Indicator | Action |
|----------|----------|-----------|--------|
| **Critical** | > 80% | 🔴 Red | Immediate reorder |
| **High** | > 50% | 🟠 Orange | High priority |
| **Medium** | > 20% | 🟡 Yellow | Plan reorder |
| **Low** | ≤ 20% | 🟢 Green | Monitor |

**Example:**
- Threshold: 100 units
- Current: 10 units
- Shortage: 90 units (90%)
- Severity: **Critical** 🔴

---

## Alert Actions

### Mark as Ordered

Use when you've placed a restock order with a supplier.

**Steps:**
1. Open alert details
2. Click "Mark as Ordered"
3. Add notes with order information:
   - Purchase order number
   - Supplier name
   - Expected delivery date
   - Order quantity
4. Confirm

**Example Notes:**
```
PO-2025-042 placed with Mouser
Expected delivery: 2025-11-01
Ordered quantity: 1000 units
```

**Effect:**
- Alert status changes to "Ordered"
- Alert remains visible in history
- Timestamp recorded for tracking

### Dismiss Alert

Use when reorder is not needed.

**Common Reasons:**
- Component being discontinued
- Manual purchase through other channels
- Threshold set too high
- Alert no longer relevant

**Steps:**
1. Open alert details
2. Click "Dismiss"
3. Add notes explaining reason
4. Confirm

**Example Notes:**
```
Component being phased out - switching to alternative part
```

**Effect:**
- Alert status changes to "Dismissed"
- Alert moved to history
- Timestamp recorded

### Auto-Resolution

Alerts automatically resolve when stock rises above threshold.

**Trigger:**
- Stock operation adds inventory
- New quantity ≥ reorder threshold
- Alert status changes to "Resolved"

**No user action required** - the system handles this automatically.

---

## Threshold Configuration

### Setting Thresholds

**(Admin only)**

Configure reorder thresholds per component per location:

**Via Component Details:**
1. Navigate to component
2. Expand location row
3. Click "Configure Reorder Alert"
4. Set threshold and enable
5. Save

**Via API:**
```bash
PUT /api/v1/reorder-alerts/thresholds/{component_id}/{location_id}
```

### Determining Threshold Values

Consider these factors:

| Factor | Questions |
|--------|-----------|
| **Usage Rate** | How quickly do you use this component? |
| **Lead Time** | How long does reorder take? |
| **Criticality** | How important is this component? |
| **Batch Size** | Minimum order quantity? |
| **Safety Stock** | Buffer for unexpected demand? |

**Example Calculation:**
```
Weekly usage: 20 units
Lead time: 2 weeks
Safety buffer: 1 week
Threshold = (20 × 2) + (20 × 1) = 60 units
```

### Best Practices

1. **Start conservative** - Set higher thresholds initially
2. **Review regularly** - Adjust based on actual usage
3. **Critical components** - Higher thresholds for critical parts
4. **Bulk orders** - Account for minimum order quantities
5. **Seasonal variation** - Adjust for project cycles

---

## Reports and Monitoring

### Low Stock Report

Real-time report of all components below threshold:

**Access:** **Inventory → Reports → Low Stock**

**Shows:**
- All components with `quantity < threshold`
- Independent of alert status
- Sorted by shortage amount (critical first)
- Exportable to CSV/Excel

**Use Cases:**
- Daily inventory check
- Bulk purchasing planning
- Identifying reorder needs

### Alert Statistics

Dashboard showing aggregate metrics:

**Metrics:**
- Active alerts count
- Dismissed alerts count
- Ordered alerts count
- Resolved alerts count
- Average shortage amount
- Maximum shortage

**Access:** **Inventory → Reports → Alert Statistics**

**Use Cases:**
- Inventory health monitoring
- Alert workflow efficiency
- Purchasing trends analysis

### Alert History

View past alerts to track inventory patterns:

**Access:** **Inventory → Reorder Alerts → History**

**Shows:**
- All dismissed, ordered, and resolved alerts
- Filterable by component
- Ordered by most recent
- Includes user notes

**Use Cases:**
- Audit trail
- Reorder pattern analysis
- Component usage tracking

---

## Common Workflows

### Workflow 1: Daily Alert Review

**Frequency:** Daily (morning)

1. Navigate to **Reorder Alerts**
2. Review active alerts
3. For **Critical** alerts:
   - Place immediate orders
   - Mark as "Ordered" with PO details
4. For **High** alerts:
   - Add to weekly purchase list
5. For **Medium/Low** alerts:
   - Monitor and plan

### Workflow 2: Bulk Purchasing

**Frequency:** Weekly

1. Navigate to **Reports → Low Stock**
2. Export to Excel
3. Group by supplier
4. Batch orders by supplier
5. Place orders
6. Mark alerts as "Ordered" with batch PO

### Workflow 3: Threshold Review

**Frequency:** Monthly

1. Navigate to **Alert History**
2. Identify components with frequent alerts
3. Analyze usage patterns
4. Adjust thresholds:
   - Too frequent → Increase threshold
   - Rarely triggered → Decrease threshold
5. Update configurations

### Workflow 4: New Component Setup

**When:** Adding new component

1. Add component to inventory
2. Assign to storage location
3. Set initial threshold:
   - Research typical usage
   - Account for lead time
   - Add safety buffer
4. Enable reorder monitoring
5. Monitor and adjust over time

---

## Integration with Other Features

### Stock Operations

Alert system integrates with stock operations:

**Add Stock:**
- Automatically resolves alerts when stock exceeds threshold
- Updates shortage metrics in real-time

**Remove Stock:**
- Automatically creates alerts if stock falls below threshold
- Recalculates severity

**Move Stock:**
- Each location monitored independently
- Alerts update per location

### Bulk Operations

Admins can bulk-configure thresholds:

**Via API:**
```bash
POST /api/v1/reorder-alerts/thresholds/bulk
```

**Use Cases:**
- Set standard thresholds across component families
- Update seasonal thresholds
- Initialize new storage area

### Projects and BOMs

Use alerts when planning projects:

1. Check active alerts before starting project
2. Verify component availability
3. Adjust thresholds for project needs
4. Plan purchases for shortages

---

## Troubleshooting

### Alert Not Created

**Problem:** Stock below threshold but no alert generated.

**Solutions:**
1. Verify reorder monitoring is **enabled**
2. Check threshold is correctly set (> 0)
3. Confirm no existing alert for location
4. Review component location exists

### Duplicate Alerts

**Problem:** Multiple alerts for same component/location.

**Cause:** System prevents duplicates - only one active alert per location.

**Check:**
- Alert status (may be dismissed/ordered, not active)
- Different locations (each has separate alert)

### Alert Won't Dismiss

**Problem:** Cannot dismiss or mark as ordered.

**Solutions:**
1. Verify you have **admin** privileges
2. Check alert status is "active"
3. Ensure alert exists (check alert ID)
4. Try refreshing page

### Threshold Not Saving

**Problem:** Threshold changes don't persist.

**Solutions:**
1. Verify **admin** authentication
2. Check component location exists
3. Ensure threshold value ≥ 0
4. Look for concurrent modification error
5. Try again after short delay

---

## Tips and Best Practices

### Setting Up New System

1. **Start small** - Configure thresholds for critical components first
2. **Use conservative values** - Start with higher thresholds
3. **Monitor for 1 month** - Observe actual usage patterns
4. **Adjust gradually** - Refine thresholds based on data
5. **Document decisions** - Record why thresholds were chosen

### Ongoing Maintenance

1. **Daily review** - Check active alerts each morning
2. **Weekly batch orders** - Combine orders by supplier
3. **Monthly analysis** - Review alert patterns
4. **Quarterly adjustments** - Update thresholds based on trends
5. **Annual audit** - Verify all critical components have monitoring

### Component Categorization

**Critical Components** (High threshold):
- Unique parts (long lead time)
- Project-specific components
- High-cost items (minimize rush orders)

**Standard Components** (Medium threshold):
- Common resistors/capacitors
- Standard ICs
- Connectors

**Bulk Components** (Low threshold):
- High-volume consumables
- Wire, solder, tape
- Generic hardware

### Performance Optimization

- **Limit active alerts** - Process alerts promptly
- **Use bulk operations** - Configure thresholds in batches
- **Regular cleanup** - Review and dismiss outdated alerts
- **Optimize thresholds** - Avoid over-alerting

---

## Admin-Only Features

All reorder alert operations require **admin authentication**.

**Admin Capabilities:**
- View all alerts
- Configure thresholds
- Dismiss alerts
- Mark alerts as ordered
- Bulk threshold updates
- Access reports and statistics

**Non-admin users:**
- Cannot access reorder alert features
- Can view component stock levels
- Cannot configure monitoring

---

## API Access

For automation and integration, use the REST API:

**Base URL:**
```
http://localhost:8000/api/v1/reorder-alerts
```

**Key Endpoints:**
- `GET /` - List active alerts
- `GET /history` - View alert history
- `POST /{alert_id}/mark-ordered` - Mark as ordered
- `POST /{alert_id}/dismiss` - Dismiss alert
- `PUT /thresholds/{component_id}/{location_id}` - Update threshold
- `POST /thresholds/bulk` - Bulk threshold updates
- `GET /reports/low-stock` - Low stock report
- `GET /reports/statistics` - Alert statistics

**Complete API documentation:** [Reorder Alerts API Guide](../api/reorder-alerts.md)

---

## FAQ

### Q: Can I set different thresholds for the same component in different locations?

**A:** Yes! Each component-location pair has independent threshold configuration.

### Q: What happens if I disable reorder monitoring?

**A:** Existing active alerts remain but new alerts won't be created. No automatic resolution occurs.

### Q: Can I edit an alert's shortage amount?

**A:** No. Shortage is automatically calculated as `threshold - current_quantity`. Update stock or threshold to change it.

### Q: How fast are alerts created?

**A:** Instant (< 1ms). Database triggers fire immediately when stock changes.

### Q: Can I export alert data?

**A:** Yes. Use the low stock report export feature (CSV/Excel) or access via API.

### Q: What if I delete a component with active alerts?

**A:** Alerts are cascade-deleted automatically (database foreign key constraint).

### Q: Can I restore a dismissed alert?

**A:** No. Dismissed alerts are historical. If needed, adjust threshold or manually add note to create awareness.

### Q: Is there a limit on number of alerts?

**A:** No hard limit, but performance degrades with 1000+ active alerts. Process alerts regularly.

### Q: Can non-admin users view alerts?

**A:** No. Reorder alerts are admin-only for inventory management control.

---

## Next Steps

- **[API Documentation](../api/reorder-alerts.md)** - Complete API reference
- **[Stock Operations](stock-operations.md)** - Manage inventory
- **[Bulk Operations](bulk-operations.md)** - Batch component management
- **[Features Overview](features.md)** - All PartsHub features

---

**Need Help?**

- Check the [API Documentation](../api/reorder-alerts.md) for technical details
- Review [Stock Operations Guide](stock-operations.md) for related features
- Submit issues via GitHub issue tracker
