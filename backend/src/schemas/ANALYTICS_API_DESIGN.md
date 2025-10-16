# Analytics API Design Documentation

## Overview

This document describes the Pydantic schema design for the Advanced Stock Management analytics API. The schemas are designed to support time-series stock data, usage trend analysis, forecasting, and dashboard visualization using Chart.js in the Vue.js frontend.

## Design Principles

1. **Chart.js Integration**: All response schemas are optimized for Chart.js consumption with clear separation of data points and metadata
2. **Consistent Patterns**: Follow existing PartsHub schema conventions (BaseModel, Field descriptions, Config examples)
3. **Type Safety**: Full type hints with Pydantic validation for all fields
4. **Frontend Friendly**: Responses include pre-calculated metrics to minimize frontend computation
5. **Flexibility**: Support aggregation by time period (daily/weekly/monthly) and optional location filtering
6. **Performance**: Metadata fields included for caching and pagination hints

## API Endpoints (Schemas Only - Implementation in Task 4.2)

The following endpoints will consume these schemas:

### 1. Stock Level Time-Series
- **Endpoint**: `GET /api/v1/analytics/stock-levels`
- **Request**: `StockLevelsRequest`
- **Response**: `StockLevelsResponse`
- **Purpose**: Historical stock levels over time for line chart visualization

### 2. Usage Trends Analysis
- **Endpoint**: `GET /api/v1/analytics/usage-trends`
- **Request**: `UsageTrendsRequest`
- **Response**: `UsageTrendsResponse`
- **Purpose**: Consumption patterns and velocity metrics for bar chart visualization

### 3. Stock Forecast
- **Endpoint**: `GET /api/v1/analytics/forecast`
- **Request**: `ForecastRequest`
- **Response**: `ForecastResponse`
- **Purpose**: Moving average predictions with reorder suggestions

### 4. Dashboard Summary
- **Endpoint**: `GET /api/v1/analytics/dashboard`
- **Request**: `DashboardSummaryRequest`
- **Response**: `DashboardSummaryResponse`
- **Purpose**: Aggregated KPIs and top lists for dashboard cards

### 5. Slow-Moving Stock Analysis
- **Endpoint**: `GET /api/v1/analytics/slow-moving-stock`
- **Request**: `SlowMovingStockRequest`
- **Response**: `SlowMovingStockResponse`
- **Purpose**: Identify overstocked/obsolete components

## Schema Categories

### Enums

#### AggregationPeriod
```python
class AggregationPeriod(str, Enum):
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
```

**Usage**: Time period for aggregating stock transactions and metrics

#### ForecastHorizon
```python
class ForecastHorizon(str, Enum):
    WEEK = "7d"
    TWO_WEEKS = "14d"
    MONTH = "30d"
    QUARTER = "90d"
```

**Usage**: How far into the future to predict stock levels

### Base Schemas

#### DateRangeFilter
Common filter for constraining time-series queries. Used across multiple endpoints.

**Fields**:
- `start_date`: ISO 8601 timestamp (inclusive)
- `end_date`: ISO 8601 timestamp (inclusive)

### Stock Time-Series Schemas

#### StockDataPoint
Single point in time-series with stock quantity and transaction count.

**Chart.js Mapping**:
- `timestamp` → x-axis label
- `quantity` → y-axis value
- `transaction_count` → tooltip detail

#### StockLevelsRequest
Query parameters for fetching historical stock levels.

**Key Features**:
- Optional location filtering (null = all locations aggregated)
- Configurable aggregation period
- Date range filtering

#### StockLevelsResponse
Complete time-series response with metadata.

**Metadata Includes**:
- Date range used
- Current stock quantity
- Reorder threshold (for overlay line on chart)

### Usage Trends Schemas

#### VelocityMetrics
Pre-calculated consumption velocity across multiple time windows.

**Use Cases**:
- Display in metric cards
- Calculate days until stockout
- Identify fast/slow movers

#### UsageTrendDataPoint
Single period's consumption data with add/remove breakdown.

**Chart.js Mapping**:
- `timestamp` → x-axis label
- `removed` → positive bar (red)
- `added` → negative bar (green)
- `consumed` → net change tooltip

#### UsageTrendsResponse
Complete usage analysis with velocity metrics.

**Frontend Integration**:
- Bar chart showing adds vs. removes
- Metric cards for daily/weekly/monthly velocity
- Trend arrows based on velocity changes

### Forecast Schemas

#### ForecastDataPoint
Single forecast prediction with confidence level.

**Key Features**:
- `predicted_quantity`: Moving average prediction
- `confidence_level`: 0.0-1.0 (decreases with horizon distance)
- `will_trigger_reorder`: Pre-calculated reorder alert flag

#### ReorderSuggestion
Actionable reorder recommendation based on forecast.

**Includes**:
- `should_reorder`: Boolean recommendation
- `suggested_date`: When to place order
- `suggested_quantity`: How much to order
- `estimated_stockout_date`: When stock will hit zero
- `days_until_stockout`: Urgency metric
- `confidence_level`: Suggestion confidence

#### ForecastResponse
Complete forecast with historical context.

**Chart.js Integration**:
- Historical data as solid line
- Forecast data as dashed line
- Confidence bands as shaded area
- Reorder threshold as horizontal line

### Dashboard Summary Schemas

#### ComponentStockSummary
High-level component statistics for cards/lists.

**Use Cases**:
- Top 10 low stock components
- Top 10 high velocity components
- Search results summaries

#### InventoryHealthMetrics
Aggregate KPIs for entire inventory.

**Dashboard Cards**:
- Total components count
- Low stock alert count (with link to alerts)
- Out of stock count (critical alert)
- Total inventory value
- Active alerts count
- Average consumption velocity

#### DashboardSummaryResponse
Complete dashboard data with top lists.

**Sections**:
1. Health metrics KPIs
2. Top 10 low stock (sorted by urgency)
3. Top 10 high consumers (sorted by velocity)
4. Recent activity count (last 7 days)

### Slow-Moving Stock Schemas

#### SlowMovingItem
Component with low consumption relative to stock level.

**Identification Criteria**:
- `days_of_stock` > threshold (default 180 days)
- `days_since_last_use` > threshold (optional)

**Use Cases**:
- Identify obsolete components
- Find overstocking issues
- Calculate tied-up capital

#### SlowMovingStockResponse
Complete slow-moving analysis.

**Includes**:
- List of slow movers (ordered by days_of_stock DESC)
- Total count
- Total inventory value locked up
- Analysis parameters in metadata

## Validation Rules

### Common Validations
- All quantities: `ge=0` (greater than or equal to zero)
- All date ranges: `start_date <= end_date` (validated in service layer)
- Confidence levels: `ge=0, le=1.0` (0-100%)
- Lookback days: `ge=7, le=365` (reasonable historical window)

### Business Rules
- Component/location IDs: Valid UUIDs (validated by FastAPI)
- Aggregation periods: Must be enum value (validated by Pydantic)
- Forecast horizons: Must be enum value (validated by Pydantic)

## Response Metadata Pattern

All response schemas include a `metadata` dict field for extensibility:

```python
metadata: dict = Field(
    ...,
    description="Additional metadata (varies by endpoint)"
)
```

**Common Metadata Fields**:
- `start_date`: Query start date (ISO 8601)
- `end_date`: Query end date (ISO 8601)
- `last_updated`: When data was last refreshed
- `algorithm`: Algorithm used (e.g., "simple_moving_average")
- `notes`: Additional context for frontend

**Benefits**:
- Backward compatible schema evolution
- Frontend caching hints
- Debug information
- Algorithm transparency

## Frontend Integration Notes

### Chart.js Configuration

#### Stock Levels Line Chart
```javascript
{
  type: 'line',
  data: {
    labels: data.map(d => d.timestamp),
    datasets: [
      {
        label: 'Stock Level',
        data: data.map(d => d.quantity),
        borderColor: 'rgb(75, 192, 192)',
        tension: 0.1
      }
    ]
  }
}
```

#### Usage Trends Bar Chart
```javascript
{
  type: 'bar',
  data: {
    labels: data.map(d => d.timestamp),
    datasets: [
      {
        label: 'Added',
        data: data.map(d => d.added),
        backgroundColor: 'rgba(75, 192, 75, 0.5)'
      },
      {
        label: 'Removed',
        data: data.map(d => d.removed),
        backgroundColor: 'rgba(255, 99, 132, 0.5)'
      }
    ]
  }
}
```

#### Forecast Line Chart with Confidence
```javascript
{
  type: 'line',
  data: {
    labels: data.map(d => d.timestamp),
    datasets: [
      {
        label: 'Predicted Stock',
        data: data.map(d => d.predicted_quantity),
        borderDash: [5, 5], // Dashed line for forecast
        borderColor: 'rgb(153, 102, 255)'
      }
    ]
  }
}
```

### Quasar Component Integration

#### Metric Cards
```vue
<q-card>
  <q-card-section>
    <div class="text-h6">Daily Velocity</div>
    <div class="text-h3">{{ velocity.daily_average }}</div>
    <div class="text-caption">units/day</div>
  </q-card-section>
</q-card>
```

#### Alert Badges
```vue
<q-badge
  :color="hasActiveAlerts ? 'negative' : 'positive'"
  :label="activeAlertsCount"
/>
```

## Implementation Checklist (Task 4.2)

### Backend Service Layer
- [ ] Create `AnalyticsService` class
- [ ] Implement stock level aggregation (GROUP BY time period)
- [ ] Implement usage trend calculation (SUM transactions)
- [ ] Implement velocity calculation (average per day/week/month)
- [ ] Implement moving average forecast algorithm
- [ ] Implement reorder suggestion logic
- [ ] Implement dashboard metrics aggregation
- [ ] Implement slow-moving stock identification

### Database Queries
- [ ] Stock levels query with time bucketing
- [ ] Transaction aggregation by period
- [ ] Component locations with reorder status
- [ ] Inventory value calculation
- [ ] Last used date calculation

### API Endpoints (Task 4.3)
- [ ] Create `analytics.py` router
- [ ] Implement 5 endpoint handlers
- [ ] Add admin-only authorization
- [ ] Add query parameter validation
- [ ] Add error handling
- [ ] Add OpenAPI documentation

### Testing
- [ ] Unit tests for service methods
- [ ] Unit tests for forecast algorithm
- [ ] Integration tests for API endpoints
- [ ] Test edge cases (no data, single data point, etc.)
- [ ] Performance testing with large datasets

### Frontend Components (Task 4.4-4.6)
- [ ] Create Chart.js composable
- [ ] Create StockLevelChart.vue
- [ ] Create UsageTrendsChart.vue
- [ ] Create ForecastChart.vue
- [ ] Create ReorderAlertsSummary.vue
- [ ] Create AnalyticsDashboard.vue page

## Performance Considerations

### Database Optimization
- Index on `stock_transactions.created_at` for date range queries
- Index on `stock_transactions.component_id` for component filtering
- Consider materialized views for dashboard metrics (if needed)

### Caching Strategy
- Cache dashboard summary for 5-10 minutes
- Cache forecast results for 1 hour (low volatility)
- Invalidate cache on stock transactions

### Query Limits
- Time-series: Max 365 data points (daily for 1 year)
- Dashboard top lists: Max 10 items each
- Slow-moving stock: Consider pagination if >100 items

## Error Handling

### Common Error Cases
- Component not found: 404
- Invalid date range: 400 with message "start_date must be before end_date"
- No historical data: Return empty arrays with metadata note
- Invalid aggregation period: Pydantic validation error
- Unauthorized access: 403 (admin-only endpoints)

### Graceful Degradation
- If no reorder threshold configured: `reorder_threshold: null`
- If velocity is zero: `days_until_stockout: null`
- If no transactions: Return zero velocity, empty data arrays

## Security Considerations

### Authorization
- All analytics endpoints require admin role
- Filter by user's accessible locations (if multi-tenant in future)

### Data Privacy
- No PII in analytics responses
- Audit log for analytics queries (if compliance required)

### Rate Limiting
- Consider rate limits for expensive queries (forecast, dashboard)
- Cache responses to reduce database load

## Future Enhancements (Post-MVP)

### Advanced Analytics
- Seasonal trend detection (ARIMA models)
- Anomaly detection (unusual consumption patterns)
- Correlation analysis (component usage relationships)
- Supplier lead time integration

### Additional Endpoints
- `/api/v1/analytics/export` - CSV/Excel export
- `/api/v1/analytics/scheduled-reports` - Report scheduling
- `/api/v1/analytics/alerts-config` - Custom alert rules

### Frontend Features
- Interactive date range picker
- Drill-down from dashboard to detailed views
- Comparison charts (multiple components)
- Export to PDF/Excel

## References

- PartsHub schema patterns: `/backend/src/schemas/reorder_alerts.py`
- Stock transaction model: `/backend/src/models/stock_transaction.py`
- Component location model: `/backend/src/models/component_location.py`
- Reorder alert model: `/backend/src/models/reorder_alert.py`
- Chart.js documentation: https://www.chartjs.org/
- Pydantic documentation: https://docs.pydantic.dev/

---

**Document Version**: 1.0
**Last Updated**: 2025-10-16
**Status**: Schema Design Complete - Ready for Service Implementation (Task 4.2)
