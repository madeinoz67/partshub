<template>
  <q-page padding>
    <div class="analytics-dashboard">
      <div class="text-h4 q-mb-lg">Stock Analytics Dashboard</div>

      <div class="row q-col-gutter-md q-mb-md">
        <div class="col-12 col-md-6">
          <q-select
            v-model="selectedComponent"
            :options="componentOptions"
            option-value="id"
            option-label="name"
            label="Select Component"
            outlined
            emit-value
            map-options
            clearable
          />
        </div>
        <div class="col-12 col-md-3">
          <q-input
            v-model="startDate"
            type="date"
            label="Start Date"
            outlined
          />
        </div>
        <div class="col-12 col-md-3">
          <q-input
            v-model="endDate"
            type="date"
            label="End Date"
            outlined
          />
        </div>
      </div>

      <ReorderAlertsSummary class="q-mb-lg" />

      <div v-if="selectedComponent" class="component-analytics">
        <div class="text-h5 q-mb-md">Component Details</div>

        <div class="row q-col-gutter-md">
          <div class="col-12 col-md-6">
            <StockLevelChart
              :component-id="selectedComponent"
              :start-date="startDateISO"
              :end-date="endDateISO"
              period="daily"
            />
          </div>

          <div class="col-12 col-md-6">
            <UsageTrendsChart
              :component-id="selectedComponent"
              :start-date="startDateISO"
              :end-date="endDateISO"
              period="daily"
            />
          </div>

          <div class="col-12">
            <ForecastChart
              :component-id="selectedComponent"
              horizon="14d"
              :lookback-days="30"
            />
          </div>
        </div>
      </div>

      <div v-else class="text-center text-grey q-pa-xl">
        <q-icon name="analytics" size="4em" />
        <div class="text-h6 q-mt-md">Select a component to view detailed analytics</div>
      </div>
    </div>
  </q-page>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import {
  StockLevelChart,
  UsageTrendsChart,
  ForecastChart,
  ReorderAlertsSummary
} from './index'

interface ComponentOption {
  id: string
  name: string
}

const selectedComponent = ref<string | null>(null)

const startDate = ref(
  new Date(Date.now() - 30 * 24 * 60 * 60 * 1000)
    .toISOString()
    .split('T')[0]
)

const endDate = ref(
  new Date()
    .toISOString()
    .split('T')[0]
)

const componentOptions = ref<ComponentOption[]>([
  { id: '660e8400-e29b-41d4-a716-446655440001', name: 'Ceramic Capacitor 100nF 0805' },
  { id: '660e8400-e29b-41d4-a716-446655440002', name: 'Resistor 10kΩ 0603' },
  { id: '660e8400-e29b-41d4-a716-446655440003', name: 'LED Red 0805' }
])

const startDateISO = computed(() => {
  return new Date(startDate.value).toISOString()
})

const endDateISO = computed(() => {
  return new Date(endDate.value).toISOString()
})
</script>

<style scoped>
.analytics-dashboard {
  max-width: 1400px;
  margin: 0 auto;
}

.component-analytics {
  margin-top: 24px;
}
</style>
