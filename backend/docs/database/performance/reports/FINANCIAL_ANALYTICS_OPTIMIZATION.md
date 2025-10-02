# Financial Analytics Query Optimization

## Current Implementation Analysis

### 1. Financial Summary Query (lines 514-526)

**Current Query**:
```python
current_valuation = (
    self.db.query(
        func.sum(
            ComponentLocation.quantity_on_hand *
            func.coalesce(Component.average_purchase_price, 0)
        )
    )
    .select_from(ComponentLocation)
    .join(Component, ComponentLocation.component_id == Component.id)
    .filter(Component.average_purchase_price.isnot(None))
    .scalar()
)
```

**Performance Issues**:
1. Filter on `average_purchase_price.isnot(None)` comes after JOIN
2. No covering index for (component_id, quantity_on_hand, average_purchase_price)
3. Multiplication performed for every row instead of using aggregated data

**Optimization Strategy**:
```sql
-- Optimized financial valuation query
WITH valued_inventory AS (
    SELECT
        cl.component_id,
        SUM(cl.quantity_on_hand) as total_quantity,
        c.average_purchase_price
    FROM component_locations cl
    INNER JOIN components c ON cl.component_id = c.id
    WHERE c.average_purchase_price IS NOT NULL
      AND c.average_purchase_price > 0
      AND cl.quantity_on_hand > 0
    GROUP BY cl.component_id, c.average_purchase_price
)
SELECT SUM(total_quantity * average_purchase_price) as total_value
FROM valued_inventory;
```

### 2. Top Value Components Query (lines 558-580)

**Current Issues**:
- Multiple JOINs with filtering
- No pre-filtering of zero quantities
- Expensive ordering operation

**Optimized Approach**:
```sql
-- Pre-aggregate and then calculate values
WITH component_values AS (
    SELECT
        c.id,
        c.part_number,
        c.name,
        c.average_purchase_price,
        SUM(cl.quantity_on_hand) as total_quantity
    FROM components c
    INNER JOIN component_locations cl ON c.id = cl.component_id
    WHERE c.average_purchase_price IS NOT NULL
      AND c.average_purchase_price > 0
      AND cl.quantity_on_hand > 0
    GROUP BY c.id, c.part_number, c.name, c.average_purchase_price
)
SELECT
    id,
    part_number,
    name,
    (total_quantity * average_purchase_price) as total_value
FROM component_values
ORDER BY total_value DESC
LIMIT 10;
```

### 3. Purchase Trends Analysis (lines 531-555)

**Current Implementation**:
```python
purchase_trends = (
    self.db.query(
        func.date_trunc("month", Purchase.purchase_date).label("month"),
        func.sum(Purchase.total_amount).label("total_spent"),
        func.count(Purchase.id).label("purchase_count"),
    )
    .filter(Purchase.purchase_date >= start_date)
    .group_by(func.date_trunc("month", Purchase.purchase_date))
    .order_by(func.date_trunc("month", Purchase.purchase_date))
    .all()
)
```

**Optimization Recommendations**:
1. Add index on `(purchase_date, total_amount)` for efficient date filtering and aggregation
2. Consider materialized monthly aggregates for frequently accessed data
3. Pre-filter NULL dates and amounts

## Recommended Financial Analytics Optimizations

### 1. Create Materialized Financial Aggregates

```sql
-- Consider creating a materialized view or table for real-time financial metrics
CREATE TABLE IF NOT EXISTS financial_metrics_cache (
    component_id TEXT PRIMARY KEY,
    total_quantity INTEGER NOT NULL DEFAULT 0,
    average_unit_cost NUMERIC(10,4),
    total_inventory_value NUMERIC(12,2),
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (component_id) REFERENCES components(id)
);

-- Trigger to update cache on ComponentLocation changes
CREATE TRIGGER update_financial_cache
    AFTER INSERT OR UPDATE OR DELETE ON component_locations
    FOR EACH ROW
    EXECUTE FUNCTION refresh_financial_metrics();
```

### 2. Optimized Financial Summary Service Method

```python
def get_financial_summary_optimized(self, months: int = 12) -> dict[str, Any]:
    """Optimized financial analytics with single efficient query."""

    try:
        end_date = datetime.now(UTC)
        start_date = end_date - timedelta(days=months * 30)

        # Single CTE for all financial calculations
        financial_cte = text("""
            WITH financial_aggregates AS (
                SELECT
                    c.id as component_id,
                    c.part_number,
                    c.name,
                    c.average_purchase_price,
                    SUM(cl.quantity_on_hand) as total_quantity
                FROM components c
                INNER JOIN component_locations cl ON c.id = cl.component_id
                WHERE c.average_purchase_price IS NOT NULL
                  AND c.average_purchase_price > 0
                  AND cl.quantity_on_hand > 0
                GROUP BY c.id, c.part_number, c.name, c.average_purchase_price
            ),
            inventory_valuation AS (
                SELECT
                    SUM(total_quantity * average_purchase_price) as total_value
                FROM financial_aggregates
            ),
            top_components AS (
                SELECT
                    component_id,
                    part_number,
                    name,
                    (total_quantity * average_purchase_price) as component_value
                FROM financial_aggregates
                ORDER BY component_value DESC
                LIMIT 10
            )
            SELECT
                'total_value' as metric_type,
                NULL as component_id,
                NULL as part_number,
                NULL as name,
                iv.total_value as value
            FROM inventory_valuation iv
            UNION ALL
            SELECT
                'top_component' as metric_type,
                tc.component_id,
                tc.part_number,
                tc.name,
                tc.component_value as value
            FROM top_components tc
            ORDER BY metric_type, value DESC
        """)

        results = self.db.execute(financial_cte).fetchall()

        # Parse results
        total_value = 0.0
        top_components = []

        for row in results:
            if row.metric_type == 'total_value':
                total_value = float(row.value or 0)
            elif row.metric_type == 'top_component':
                top_components.append({
                    "component_id": row.component_id,
                    "part_number": row.part_number or "N/A",
                    "name": row.name or "Unknown",
                    "inventory_value": float(row.value or 0),
                })

        return {
            "current_inventory_value": total_value,
            "top_value_components": top_components,
            "analysis_period_months": months,
            "monthly_spending": []  # Purchase data handled separately if available
        }

    except SQLAlchemyError as e:
        logger.error(f"Database error in get_financial_summary_optimized: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve financial summary due to database error"
        )
```

### 3. Index Requirements for Financial Optimization

```sql
-- Critical indexes for financial calculations
CREATE INDEX IF NOT EXISTS idx_components_financial_calc
ON components(id, average_purchase_price)
WHERE average_purchase_price IS NOT NULL AND average_purchase_price > 0;

-- Covering index for inventory valuation
CREATE INDEX IF NOT EXISTS idx_component_locations_valuation
ON component_locations(component_id, quantity_on_hand)
WHERE quantity_on_hand > 0;

-- Purchase analysis index
CREATE INDEX IF NOT EXISTS idx_purchases_date_amount
ON purchases(purchase_date, total_amount)
WHERE purchase_date IS NOT NULL AND total_amount IS NOT NULL;
```

## Performance Impact Estimates

### Current vs Optimized Performance

**Current Financial Summary**:
- Execution Time: ~200-500ms (depending on data volume)
- Table Scans: Multiple scans of component_locations
- JOIN Operations: Multiple separate JOINs for each metric
- Memory Usage: High due to multiple query result sets

**Optimized Financial Summary**:
- Execution Time: ~50-150ms (estimated 60-70% improvement)
- Table Scans: Single scan of component_locations with efficient filtering
- JOIN Operations: Single JOIN operation with proper indexing
- Memory Usage: Reduced due to single query execution plan

### Cache-Based Approach Benefits

**Real-time Calculation**:
- Pros: Always current data
- Cons: High computational cost on every request

**Materialized Cache Approach**:
- Pros: Sub-millisecond response times, reduced database load
- Cons: Slight data latency (updated on changes)
- Recommended for: High-traffic dashboards, frequent financial reports

## Implementation Priority

### High Priority (Immediate)
1. Deploy critical financial indexes from migration
2. Implement optimized single-query approach for financial summary
3. Add query execution time monitoring for financial endpoints

### Medium Priority (Next Sprint)
1. Implement materialized financial metrics cache
2. Add cache invalidation triggers for real-time accuracy
3. Optimize purchase trend analysis with proper indexing

### Future Optimization
1. Consider read replicas for heavy analytical workloads
2. Implement financial data archiving for historical analysis
3. Add financial metrics pre-computation for instant dashboard loading