# Analytics Chart Components

Vue 3 chart components for the Advanced Stock Management analytics dashboard. Built with Chart.js, TypeScript, and Quasar Framework.

## Components

### 1. StockLevelChart.vue

Line chart showing historical stock levels over time with optional reorder threshold overlay.

**Props:**
- `componentId` (string, required) - Component UUID to analyze
- `locationId` (string | null, optional) - Storage location UUID (null = all locations)
- `startDate` (string, required) - ISO 8601 start date
- `endDate` (string, required) - ISO 8601 end date
- `period` ('daily' | 'weekly' | 'monthly', default: 'daily') - Time aggregation period

**Features:**
- Historical stock level line chart
- Reorder threshold displayed as dashed horizontal line
- Transaction count displayed in tooltip
- Responsive canvas sizing
- Loading and error states

**Example:**
```vue
<script setup lang="ts">
import { StockLevelChart } from 'src/components/analytics'

const componentId = '660e8400-e29b-41d4-a716-446655440001'
const startDate = '2025-09-16T00:00:00Z'
const endDate = '2025-10-16T00:00:00Z'
</script>

<template>
  <StockLevelChart
    :component-id="componentId"
    :start-date="startDate"
    :end-date="endDate"
    period="daily"
  />
</template>
```

---

### 2. UsageTrendsChart.vue

Bar chart showing consumption patterns with velocity metrics displayed in the header.

**Props:**
- `componentId` (string, required) - Component UUID to analyze
- `locationId` (string | null, optional) - Storage location UUID (null = all locations)
- `startDate` (string, required) - ISO 8601 start date
- `endDate` (string, required) - ISO 8601 end date
- `period` ('daily' | 'weekly' | 'monthly', default: 'daily') - Time aggregation period

**Features:**
- Bar chart with separate bars for added (green) and removed (red) quantities
- Velocity metrics displayed as chips in header (daily/monthly averages)
- Net consumption displayed in tooltip
- Loading and error states

**Example:**
```vue
<script setup lang="ts">
import { UsageTrendsChart } from 'src/components/analytics'

const componentId = '660e8400-e29b-41d4-a716-446655440001'
const startDate = '2025-09-16T00:00:00Z'
const endDate = '2025-10-16T00:00:00Z'
</script>

<template>
  <UsageTrendsChart
    :component-id="componentId"
    :start-date="startDate"
    :end-date="endDate"
    period="weekly"
  />
</template>
```

---

### 3. ForecastChart.vue

Line chart with historical data (solid line) and forecast predictions (dashed line), plus reorder suggestion card.

**Props:**
- `componentId` (string, required) - Component UUID to forecast
- `locationId` (string | null, optional) - Storage location UUID (null = all locations)
- `horizon` ('7d' | '14d' | '30d' | '90d', default: '14d') - Forecast time horizon
- `lookbackDays` (number, default: 30) - Historical days for moving average (7-365)

**Features:**
- Historical data shown as solid line
- Forecast shown as dashed line
- Confidence level displayed in tooltip
- Reorder threshold as horizontal line
- Reorder suggestion card (shown if stockout predicted)
- Loading and error states

**Example:**
```vue
<script setup lang="ts">
import { ForecastChart } from 'src/components/analytics'

const componentId = '660e8400-e29b-41d4-a716-446655440001'
</script>

<template>
  <ForecastChart
    :component-id="componentId"
    horizon="14d"
    :lookback-days="30"
  />
</template>
```

---

### 4. ReorderAlertsSummary.vue

Dashboard summary component with inventory health metrics and top 10 lists.

**Props:**
- `categoryId` (string | null, optional) - Filter by category UUID (null = all categories)
- `locationId` (string | null, optional) - Filter by location UUID (null = all locations)

**Features:**
- 4 metric cards (total components, low stock, out of stock, inventory value)
- Top 10 low stock components list (clickable, shows days until stockout)
- Top 10 high consumers list (clickable, shows daily velocity)
- Recent activity count
- Average stock velocity
- Loading and error states
- Click to navigate to component details

**Example:**
```vue
<script setup lang="ts">
import { ReorderAlertsSummary } from 'src/components/analytics'

const categoryId = ref<string | null>(null)
const locationId = ref<string | null>(null)
</script>

<template>
  <ReorderAlertsSummary
    :category-id="categoryId"
    :location-id="locationId"
  />
</template>
```

---

## API Endpoints Used

All components use the analytics API endpoints:

- `/api/v1/analytics/stock-levels` - Stock level time-series
- `/api/v1/analytics/usage-trends` - Usage trend analysis
- `/api/v1/analytics/forecast` - Stock forecast
- `/api/v1/analytics/dashboard` - Dashboard summary

Authentication is handled automatically via the axios interceptor (Bearer token from localStorage).

## Common Patterns

### Date Range Props

All time-series components accept `startDate` and `endDate` props in ISO 8601 format:

```typescript
const startDate = new Date('2025-09-16').toISOString()
const endDate = new Date('2025-10-16').toISOString()
```

### Loading States

All components show a centered `q-spinner` while data is loading.

### Error Handling

All components display errors in a `q-banner` with a red background and error icon.

### Chart Responsiveness

All charts use `maintainAspectRatio: false` and a fixed container height of 300px for consistent sizing across different screen sizes.

## TypeScript Types

Each component defines its own TypeScript interfaces matching the backend Pydantic schemas. Key types include:

- `StockDataPoint` - Single stock level data point
- `UsageTrendDataPoint` - Single usage trend data point
- `ForecastDataPoint` - Single forecast prediction
- `ReorderSuggestion` - Reorder recommendation
- `ComponentStockSummary` - Component summary for lists
- `InventoryHealthMetrics` - Aggregate health KPIs

## Dependencies

- Vue 3 Composition API (`ref`, `onMounted`, `watch`)
- Quasar Framework components (`q-card`, `q-spinner`, `q-banner`, etc.)
- Chart.js (via `useChart` composable)
- Axios (via `api` from `src/boot/axios`)
- Vue Router (for navigation in ReorderAlertsSummary)

## Chart.js Integration

All components use the `useChart` composable from `src/composables/useChart.ts`:

```typescript
import { useChart, chartHelpers } from 'src/composables/useChart'

const chartCanvas = ref<HTMLCanvasElement>()
const { createChart } = useChart(chartCanvas)

// Transform data and create chart
const chartData = chartHelpers.transformStockLevels(data, threshold)
createChart({ type: 'line', data: chartData, options: {...} })
```

## Styling

All components use scoped styles with:
- `.chart-container` - Fixed height (300px), relative positioning for canvas
- Responsive design using Quasar grid classes (`col-12`, `col-md-6`, etc.)
- Consistent spacing with Quasar utility classes (`q-mb-md`, `q-pa-xl`, etc.)

## Testing

Component testing should cover:
1. Props validation and defaults
2. API call parameters (check query strings)
3. Loading state rendering
4. Error state rendering
5. Chart rendering with mock data
6. Reactive prop updates (watch triggers)
7. User interactions (clicks, navigation)

Example test setup:
```typescript
import { mount } from '@vue/test-utils'
import { Quasar } from 'quasar'
import StockLevelChart from './StockLevelChart.vue'

const wrapper = mount(StockLevelChart, {
  global: {
    plugins: [Quasar]
  },
  props: {
    componentId: '123',
    startDate: '2025-09-16T00:00:00Z',
    endDate: '2025-10-16T00:00:00Z'
  }
})
```

## Performance Considerations

- Charts are only created/updated when data changes (watch on props)
- Chart instances are properly destroyed on component unmount (handled by useChart)
- API calls are debounced via watch (no manual debouncing needed)
- Large datasets are handled efficiently by Chart.js

## Accessibility

- All charts have proper ARIA labels (handled by Chart.js)
- Loading states use semantic `q-spinner` with accessible markup
- Error messages use `q-banner` with icon for visual + screen reader support
- Clickable items in ReorderAlertsSummary use semantic `q-item` with proper roles

## Future Enhancements

Potential improvements for future iterations:
- Date range picker integration
- Export to CSV/Excel functionality
- Drill-down interactions (click chart to filter)
- Comparison mode (multiple components on one chart)
- Customizable chart colors via props
- Print/PDF export
- Real-time updates via WebSocket

---

**Created:** 2025-10-17
**Version:** 1.0
**Status:** Task 4.5 Complete - Ready for Integration
