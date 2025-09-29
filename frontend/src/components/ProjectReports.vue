<template>
  <q-card style="min-width: 800px">
    <q-card-section>
      <div class="row items-center">
        <div class="col">
          <div class="text-h6">Project Reports</div>
          <div class="text-body2 text-grey-7">Generate and export project reports</div>
        </div>
        <div class="col-auto">
          <q-btn
            flat
            round
            icon="close"
            aria-label="Close dialog"
            @click="$emit('close')"
          />
        </div>
      </div>
    </q-card-section>

    <q-card-section>
      <div class="row q-gutter-md">
        <!-- Report Type Selection -->
        <div class="col-12 col-md-6">
          <q-card flat bordered>
            <q-card-section>
              <div class="text-subtitle1 q-mb-md">Available Reports</div>

              <q-list>
                <q-item
                  v-for="report in reportTypes"
                  :key="report.type"
                  v-ripple
                  clickable
                  :active="selectedReport === report.type"
                  @click="selectedReport = report.type"
                >
                  <q-item-section avatar>
                    <q-icon :name="report.icon" />
                  </q-item-section>
                  <q-item-section>
                    <q-item-label>{{ report.name }}</q-item-label>
                    <q-item-label caption>{{ report.description }}</q-item-label>
                  </q-item-section>
                </q-item>
              </q-list>
            </q-card-section>
          </q-card>
        </div>

        <!-- Report Options -->
        <div class="col-12 col-md-6">
          <q-card flat bordered>
            <q-card-section>
              <div class="text-subtitle1 q-mb-md">Export Options</div>

              <div class="column q-gutter-md">
                <q-select
                  v-model="exportFormat"
                  label="Export Format"
                  filled
                  :options="formatOptions"
                  emit-value
                  map-options
                />

                <q-checkbox
                  v-model="includeImages"
                  label="Include component images"
                />

                <q-checkbox
                  v-model="includeSpecs"
                  label="Include specifications"
                />

                <q-checkbox
                  v-model="includeStock"
                  label="Include stock information"
                />

                <q-btn
                  color="primary"
                  icon="download"
                  label="Generate Report"
                  :loading="generating"
                  :disable="!selectedReport"
                  @click="generateReport"
                />
              </div>
            </q-card-section>
          </q-card>
        </div>
      </div>

      <!-- Report Preview -->
      <div v-if="reportPreview" class="q-mt-lg">
        <q-card flat bordered>
          <q-card-section>
            <div class="text-subtitle1 q-mb-md">Report Preview</div>
            <div class="report-preview">
              <!-- BOM Table Preview -->
              <q-table
                v-if="selectedReport === 'bom'"
                :rows="bomData"
                :columns="bomColumns"
                flat
                bordered
                dense
                :pagination="{ rowsPerPage: 10 }"
              />

              <!-- Cost Analysis Preview -->
              <div v-else-if="selectedReport === 'cost'" class="cost-analysis">
                <div class="row q-gutter-md">
                  <div class="col">
                    <q-card flat bordered class="text-center q-pa-md">
                      <div class="text-h4 text-primary">{{ totalCost }}</div>
                      <div class="text-subtitle2">Total Cost</div>
                    </q-card>
                  </div>
                  <div class="col">
                    <q-card flat bordered class="text-center q-pa-md">
                      <div class="text-h4 text-orange">{{ componentCount }}</div>
                      <div class="text-subtitle2">Components</div>
                    </q-card>
                  </div>
                </div>
              </div>

              <!-- Stock Status Preview -->
              <div v-else-if="selectedReport === 'stock'" class="stock-status">
                <q-table
                  :rows="stockData"
                  :columns="stockColumns"
                  flat
                  bordered
                  dense
                />
              </div>
            </div>
          </q-card-section>
        </q-card>
      </div>
    </q-card-section>
  </q-card>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useQuasar } from 'quasar'

interface Props {
  projectId?: string
}

const props = defineProps<Props>()
const emit = defineEmits<{
  close: []
}>()
const $q = useQuasar()

const selectedReport = ref('')
const exportFormat = ref('pdf')
const includeImages = ref(true)
const includeSpecs = ref(true)
const includeStock = ref(true)
const generating = ref(false)
const reportPreview = ref(false)

const reportTypes = [
  {
    type: 'bom',
    name: 'Bill of Materials',
    description: 'Complete component list with quantities',
    icon: 'inventory'
  },
  {
    type: 'cost',
    name: 'Cost Analysis',
    description: 'Project cost breakdown and estimates',
    icon: 'attach_money'
  },
  {
    type: 'stock',
    name: 'Stock Status',
    description: 'Component availability and procurement needs',
    icon: 'inventory_2'
  },
  {
    type: 'assembly',
    name: 'Assembly Guide',
    description: 'Step-by-step assembly instructions',
    icon: 'build'
  }
]

const formatOptions = [
  { label: 'PDF', value: 'pdf' },
  { label: 'Excel (XLSX)', value: 'xlsx' },
  { label: 'CSV', value: 'csv' },
  { label: 'JSON', value: 'json' }
]

// Mock data for preview
const bomData = ref([
  { component: 'STM32F407VGT6', quantity: 1, unit_cost: 8.50, total_cost: 8.50 },
  { component: 'LM358P', quantity: 2, unit_cost: 0.75, total_cost: 1.50 },
  { component: '10k Resistor', quantity: 5, unit_cost: 0.05, total_cost: 0.25 }
])

const bomColumns = [
  { name: 'component', label: 'Component', field: 'component', align: 'left' as const },
  { name: 'quantity', label: 'Qty', field: 'quantity', align: 'center' as const },
  { name: 'unit_cost', label: 'Unit Cost', field: 'unit_cost', align: 'right' as const, format: (val: number) => `$${val.toFixed(2)}` },
  { name: 'total_cost', label: 'Total', field: 'total_cost', align: 'right' as const, format: (val: number) => `$${val.toFixed(2)}` }
]

const stockData = ref([
  { component: 'STM32F407VGT6', required: 1, available: 3, status: 'In Stock' },
  { component: 'LM358P', required: 2, available: 0, status: 'Out of Stock' },
  { component: '10k Resistor', required: 5, available: 2, status: 'Partial' }
])

const stockColumns = [
  { name: 'component', label: 'Component', field: 'component', align: 'left' as const },
  { name: 'required', label: 'Required', field: 'required', align: 'center' as const },
  { name: 'available', label: 'Available', field: 'available', align: 'center' as const },
  { name: 'status', label: 'Status', field: 'status', align: 'center' as const }
]

const totalCost = computed(() => {
  const total = bomData.value.reduce((sum, item) => sum + item.total_cost, 0)
  return `$${total.toFixed(2)}`
})

const componentCount = computed(() => bomData.value.length)

async function generateReport() {
  generating.value = true

  try {
    // Simulate report generation
    await new Promise(resolve => setTimeout(resolve, 2000))

    reportPreview.value = true

    $q.notify({
      type: 'positive',
      message: `${reportTypes.find(r => r.type === selectedReport.value)?.name} generated successfully`,
      position: 'top'
    })
  } catch (error) {
    $q.notify({
      type: 'negative',
      message: 'Failed to generate report',
      position: 'top'
    })
  } finally {
    generating.value = false
  }
}
</script>

<style scoped>
.report-preview {
  border: 1px solid #e0e0e0;
  border-radius: 4px;
  padding: 16px;
  background: #fafafa;
}

.cost-analysis .q-card {
  background: white;
}
</style>