<template>
  <q-page class="q-pa-md">
    <!-- Page Header -->
    <div class="row items-center q-mb-lg">
      <div class="col">
        <div class="text-h4">Analytics Dashboard</div>
        <div class="text-caption text-grey">Advanced stock management analytics and forecasting</div>
      </div>
      <div class="col-auto">
        <q-btn
          color="primary"
          icon="refresh"
          label="Refresh"
          :loading="loading"
          @click="refreshData"
        />
      </div>
    </div>

    <!-- Filter Controls -->
    <q-card flat bordered class="q-mb-md">
      <q-card-section>
        <div class="text-subtitle1 q-mb-md">Filters</div>
        <div class="row q-col-gutter-md">
          <!-- Component Selector -->
          <div class="col-12 col-md-4">
            <q-select
              v-model="selectedComponent"
              outlined
              dense
              :options="componentOptions"
              option-value="id"
              option-label="name"
              label="Select Component"
              clearable
              use-input
              input-debounce="300"
              @filter="filterComponents"
              @update:model-value="onComponentChange"
            >
              <template #no-option>
                <q-item>
                  <q-item-section class="text-grey">
                    No components found
                  </q-item-section>
                </q-item>
              </template>
              <template #option="scope">
                <q-item v-bind="scope.itemProps">
                  <q-item-section>
                    <q-item-label>{{ scope.opt.name }}</q-item-label>
                    <q-item-label caption>
                      {{ scope.opt.part_number || 'No part number' }}
                    </q-item-label>
                  </q-item-section>
                  <q-item-section side>
                    <q-chip
                      size="sm"
                      :color="getStockStatusColor(scope.opt)"
                      text-color="white"
                    >
                      {{ scope.opt.quantity_on_hand }}
                    </q-chip>
                  </q-item-section>
                </q-item>
              </template>
            </q-select>
          </div>

          <!-- Date Range Picker -->
          <div class="col-12 col-md-4">
            <q-input
              v-model="dateRangeDisplay"
              outlined
              dense
              label="Date Range"
              readonly
            >
              <template #prepend>
                <q-icon name="event" class="cursor-pointer">
                  <q-popup-proxy cover transition-show="scale" transition-hide="scale">
                    <q-date
                      v-model="dateRange"
                      range
                      @update:model-value="onDateRangeChange"
                    >
                      <div class="row items-center justify-end">
                        <q-btn v-close-popup label="Close" color="primary" flat />
                      </div>
                    </q-date>
                  </q-popup-proxy>
                </q-icon>
              </template>
            </q-input>
          </div>

          <!-- Period Selector -->
          <div class="col-12 col-md-4">
            <q-select
              v-model="period"
              outlined
              dense
              :options="periodOptions"
              label="Period"
              emit-value
              map-options
            />
          </div>
        </div>

        <!-- Quick Date Range Buttons -->
        <div class="row q-col-gutter-sm q-mt-sm">
          <div class="col-auto">
            <q-btn
              size="sm"
              outline
              color="primary"
              label="Last 7 Days"
              @click="setQuickDateRange(7)"
            />
          </div>
          <div class="col-auto">
            <q-btn
              size="sm"
              outline
              color="primary"
              label="Last 30 Days"
              @click="setQuickDateRange(30)"
            />
          </div>
          <div class="col-auto">
            <q-btn
              size="sm"
              outline
              color="primary"
              label="Last 90 Days"
              @click="setQuickDateRange(90)"
            />
          </div>
        </div>
      </q-card-section>
    </q-card>

    <!-- Dashboard Summary - Always Visible -->
    <ReorderAlertsSummary class="q-mb-md" />

    <!-- Charts Section - Show when component selected -->
    <div v-if="selectedComponent">
      <div class="text-h6 q-mb-md">
        Analytics for: {{ selectedComponent.name }}
        <span v-if="selectedComponent.part_number" class="text-caption text-grey">
          ({{ selectedComponent.part_number }})
        </span>
      </div>

      <!-- Charts Grid -->
      <div class="row q-col-gutter-md">
        <!-- Stock Level Chart -->
        <div class="col-12 col-md-6">
          <StockLevelChart
            :component-id="selectedComponent.id"
            :location-id="selectedLocation"
            :start-date="startDate"
            :end-date="endDate"
            :period="period"
          />
        </div>

        <!-- Usage Trends Chart -->
        <div class="col-12 col-md-6">
          <UsageTrendsChart
            :component-id="selectedComponent.id"
            :location-id="selectedLocation"
            :start-date="startDate"
            :end-date="endDate"
            :period="period"
          />
        </div>

        <!-- Forecast Chart - Full Width -->
        <div class="col-12">
          <ForecastChart
            :component-id="selectedComponent.id"
            :location-id="selectedLocation"
            :horizon="forecastHorizon"
            :lookback-days="forecastLookbackDays"
          />
        </div>
      </div>
    </div>

    <!-- Empty State -->
    <div v-else class="text-center q-pa-xl">
      <q-icon name="analytics" size="6em" color="grey-4" />
      <div class="text-h5 text-grey q-mt-md">Select a Component</div>
      <div class="text-grey q-mb-lg">
        Choose a component from the dropdown above to view detailed analytics,<br>
        stock trends, usage patterns, and forecasting data.
      </div>
    </div>
  </q-page>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { storeToRefs } from 'pinia'
import { useComponentsStore } from '../stores/components'
import {
  ReorderAlertsSummary,
  StockLevelChart,
  UsageTrendsChart,
  ForecastChart
} from '../components/analytics'
import type { Component } from '../services/api'

const componentsStore = useComponentsStore()
const { components } = storeToRefs(componentsStore)

// State
const loading = ref(false)
const selectedComponent = ref<Component | null>(null)
const selectedLocation = ref<string | null>(null)

// Date range state
const dateRange = ref({
  from: formatDateForInput(new Date(Date.now() - 30 * 24 * 60 * 60 * 1000)),
  to: formatDateForInput(new Date())
})

const period = ref<'daily' | 'weekly' | 'monthly'>('daily')
const forecastHorizon = ref<'7d' | '14d' | '30d' | '90d'>('14d')
const forecastLookbackDays = ref(30)

// Component options for dropdown
const componentOptions = ref<Component[]>([])
const allComponents = ref<Component[]>([])

// Options
const periodOptions = [
  { label: 'Daily', value: 'daily' },
  { label: 'Weekly', value: 'weekly' },
  { label: 'Monthly', value: 'monthly' }
]

// Computed
const startDate = computed(() => dateRange.value.from)
const endDate = computed(() => dateRange.value.to)

const dateRangeDisplay = computed(() => {
  if (!dateRange.value.from || !dateRange.value.to) return ''
  return `${formatDateForDisplay(dateRange.value.from)} - ${formatDateForDisplay(dateRange.value.to)}`
})

// Methods
function formatDateForInput(date: Date): string {
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  return `${year}/${month}/${day}`
}

function formatDateForDisplay(dateString: string): string {
  const date = new Date(dateString)
  return date.toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric'
  })
}

function setQuickDateRange(days: number) {
  const today = new Date()
  const pastDate = new Date(today.getTime() - days * 24 * 60 * 60 * 1000)

  dateRange.value = {
    from: formatDateForInput(pastDate),
    to: formatDateForInput(today)
  }
}

function onDateRangeChange() {
  // Date range changed, charts will auto-update via watchers
}

function onComponentChange() {
  // Component changed, charts will auto-update via watchers
}

function getStockStatusColor(component: Component) {
  if (component.quantity_on_hand === 0) return 'negative'
  if (component.quantity_on_hand <= component.minimum_stock && component.minimum_stock > 0) return 'warning'
  return 'positive'
}

function filterComponents(val: string, update: (fn: () => void) => void) {
  update(() => {
    if (val === '') {
      componentOptions.value = allComponents.value
    } else {
      const needle = val.toLowerCase()
      componentOptions.value = allComponents.value.filter(c =>
        c.name.toLowerCase().includes(needle) ||
        (c.part_number && c.part_number.toLowerCase().includes(needle))
      )
    }
  })
}

async function loadComponents() {
  loading.value = true
  try {
    await componentsStore.fetchComponents({ limit: 1000, offset: 0 })
    allComponents.value = [...components.value]
    componentOptions.value = [...components.value]
  } catch (error) {
    console.error('Failed to load components:', error)
  } finally {
    loading.value = false
  }
}

async function refreshData() {
  loading.value = true
  try {
    await loadComponents()
  } finally {
    loading.value = false
  }
}

// Lifecycle
onMounted(async () => {
  await loadComponents()

  // Set default date range to last 30 days
  setQuickDateRange(30)
})
</script>

<style scoped>
/* Add any custom styles here */
</style>
