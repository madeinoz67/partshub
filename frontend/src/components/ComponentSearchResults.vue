<template>
  <div class="component-search-results">
    <q-table
      :rows="results"
      :columns="columns"
      row-key="provider_id"
      flat
      bordered
      :pagination="{ rowsPerPage: 10 }"
    >
      <template v-slot:body-cell-part_number="props">
        <q-td :props="props">
          <div class="text-weight-medium">{{ props.value }}</div>
          <div class="text-body2 text-grey-7">{{ props.row.manufacturer }}</div>
        </q-td>
      </template>

      <template v-slot:body-cell-description="props">
        <q-td :props="props">
          <div class="text-body2" style="max-width: 300px; white-space: normal;">
            {{ props.value }}
          </div>
        </q-td>
      </template>

      <template v-slot:body-cell-specifications="props">
        <q-td :props="props">
          <q-btn
            v-if="props.value && Object.keys(props.value).length > 0"
            label="View Specs"
            size="sm"
            flat
            color="blue"
            @click="showSpecifications(props.row)"
          />
          <span v-else class="text-grey-5">No specs</span>
        </q-td>
      </template>

      <template v-slot:body-cell-price="props">
        <q-td :props="props">
          <div v-if="props.row.price_breaks && props.row.price_breaks.length > 0">
            <div v-for="price in props.row.price_breaks.slice(0, 2)" :key="price.quantity">
              <span class="text-body2">{{ price.quantity }}+: {{ price.price }} {{ price.currency || 'USD' }}</span>
            </div>
            <q-btn
              v-if="props.row.price_breaks.length > 2"
              label="More"
              size="sm"
              flat
              color="blue"
              @click="showPricing(props.row)"
            />
          </div>
          <span v-else class="text-grey-5">No pricing</span>
        </q-td>
      </template>

      <template v-slot:body-cell-availability="props">
        <q-td :props="props">
          <q-chip
            v-if="props.value !== null && props.value !== undefined"
            :color="props.value > 0 ? 'positive' : 'negative'"
            text-color="white"
            dense
          >
            {{ props.value }}
          </q-chip>
          <span v-else class="text-grey-5">Unknown</span>
        </q-td>
      </template>

      <template v-slot:body-cell-actions="props">
        <q-td :props="props">
          <div class="q-gutter-xs">
            <q-btn
              label="Import"
              size="sm"
              color="primary"
              @click="$emit('import', props.row)"
            />
            <q-btn
              v-if="props.row.datasheet_url"
              icon="description"
              size="sm"
              flat
              color="blue"
              @click="openUrl(props.row.datasheet_url)"
            >
              <q-tooltip>Datasheet</q-tooltip>
            </q-btn>
            <q-btn
              v-if="props.row.provider_url"
              icon="launch"
              size="sm"
              flat
              color="grey"
              @click="openUrl(props.row.provider_url)"
            >
              <q-tooltip>View on Provider</q-tooltip>
            </q-btn>
          </div>
        </q-td>
      </template>
    </q-table>

    <!-- Specifications Dialog -->
    <q-dialog v-model="showSpecsDialog">
      <q-card style="min-width: 400px">
        <q-card-section>
          <div class="text-h6">Component Specifications</div>
          <div class="text-subtitle2 text-grey-7">{{ selectedComponent?.part_number }}</div>
        </q-card-section>
        <q-card-section>
          <div v-if="selectedComponent?.specifications">
            <div v-for="(value, key) in selectedComponent.specifications" :key="key" class="row q-mb-sm">
              <div class="col-4 text-weight-medium">{{ key }}:</div>
              <div class="col-8">{{ value }}</div>
            </div>
          </div>
        </q-card-section>
        <q-card-actions align="right">
          <q-btn flat label="Close" color="primary" @click="showSpecsDialog = false" />
        </q-card-actions>
      </q-card>
    </q-dialog>

    <!-- Pricing Dialog -->
    <q-dialog v-model="showPricingDialog">
      <q-card style="min-width: 400px">
        <q-card-section>
          <div class="text-h6">Pricing Information</div>
          <div class="text-subtitle2 text-grey-7">{{ selectedComponent?.part_number }}</div>
        </q-card-section>
        <q-card-section>
          <q-table
            v-if="selectedComponent?.price_breaks"
            :rows="selectedComponent.price_breaks"
            :columns="priceColumns"
            flat
            dense
            hide-header
          />
        </q-card-section>
        <q-card-actions align="right">
          <q-btn flat label="Close" color="primary" @click="showPricingDialog = false" />
        </q-card-actions>
      </q-card>
    </q-dialog>
  </div>
</template>

<script>
import { ref } from 'vue'

export default {
  name: 'ComponentSearchResults',
  props: {
    results: {
      type: Array,
      required: true
    }
  },
  emits: ['import', 'viewDetails'],
  setup() {
    const showSpecsDialog = ref(false)
    const showPricingDialog = ref(false)
    const selectedComponent = ref(null)

    const columns = [
      {
        name: 'part_number',
        label: 'Part Number',
        field: 'part_number',
        align: 'left',
        sortable: true
      },
      {
        name: 'description',
        label: 'Description',
        field: 'description',
        align: 'left',
        style: 'max-width: 300px'
      },
      {
        name: 'category',
        label: 'Category',
        field: 'category',
        align: 'left',
        sortable: true
      },
      {
        name: 'specifications',
        label: 'Specifications',
        field: 'specifications',
        align: 'center'
      },
      {
        name: 'price',
        label: 'Pricing',
        field: 'price_breaks',
        align: 'left'
      },
      {
        name: 'availability',
        label: 'Stock',
        field: 'availability',
        align: 'center',
        sortable: true
      },
      {
        name: 'actions',
        label: 'Actions',
        field: 'actions',
        align: 'center'
      }
    ]

    const priceColumns = [
      { name: 'quantity', label: 'Quantity', field: 'quantity', align: 'left' },
      { name: 'price', label: 'Price', field: 'price', align: 'right',
        format: (val, row) => `${val} ${row.currency || 'USD'}` }
    ]

    const showSpecifications = (component) => {
      selectedComponent.value = component
      showSpecsDialog.value = true
    }

    const showPricing = (component) => {
      selectedComponent.value = component
      showPricingDialog.value = true
    }

    const openUrl = (url) => {
      window.open(url, '_blank')
    }

    return {
      columns,
      priceColumns,
      showSpecsDialog,
      showPricingDialog,
      selectedComponent,
      showSpecifications,
      showPricing,
      openUrl
    }
  }
}
</script>

<style scoped>
.component-search-results {
  width: 100%;
}
</style>