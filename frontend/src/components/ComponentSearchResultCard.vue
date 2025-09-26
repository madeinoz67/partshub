<template>
  <div class="component-search-result-card">
    <div class="row q-gutter-md">
      <div class="col-md-6 col-xs-12">
        <div class="text-weight-medium">{{ result.part_number }}</div>
        <div class="text-body2 text-grey-7">{{ result.manufacturer }}</div>
        <div class="text-body2 q-mt-sm">{{ result.description }}</div>
      </div>
      <div class="col-md-6 col-xs-12">
        <div v-if="result.category" class="text-body2">
          <strong>Category:</strong> {{ result.category }}
        </div>
        <div v-if="result.availability" class="text-body2">
          <strong>Availability:</strong>
          <q-chip
            :color="result.availability > 0 ? 'positive' : 'negative'"
            text-color="white"
            dense
            class="q-ml-sm"
          >
            {{ result.availability }}
          </q-chip>
        </div>
      </div>
    </div>

    <!-- Specifications -->
    <div v-if="result.specifications && Object.keys(result.specifications).length > 0"
         class="q-mt-md">
      <q-expansion-item
        label="Specifications"
        icon="info"
        dense
      >
        <div class="q-pa-sm">
          <div v-for="(value, key) in result.specifications" :key="key" class="row">
            <div class="col-4 text-weight-medium">{{ key }}:</div>
            <div class="col-8">{{ value }}</div>
          </div>
        </div>
      </q-expansion-item>
    </div>

    <!-- Pricing -->
    <div v-if="result.price_breaks && result.price_breaks.length > 0"
         class="q-mt-md">
      <q-expansion-item
        label="Pricing"
        icon="attach_money"
        dense
      >
        <q-table
          :rows="result.price_breaks"
          :columns="priceColumns"
          flat
          dense
          hide-header
          class="q-mt-sm"
        />
      </q-expansion-item>
    </div>

    <!-- Actions -->
    <div class="row q-gutter-sm q-mt-md">
      <q-btn
        label="Import Component"
        color="primary"
        size="sm"
        @click="$emit('import', result)"
        :loading="importing"
      />
      <q-btn
        v-if="result.datasheet_url"
        label="Datasheet"
        color="blue"
        size="sm"
        flat
        icon="description"
        @click="openUrl(result.datasheet_url)"
      />
      <q-btn
        v-if="result.provider_url"
        :label="`View on ${providerName ? providerName.toUpperCase() : 'Provider'}`"
        color="grey"
        size="sm"
        flat
        icon="launch"
        @click="openUrl(result.provider_url)"
      />
    </div>
  </div>
</template>

<script>
import { ref } from 'vue'

export default {
  name: 'ComponentSearchResultCard',
  props: {
    result: {
      type: Object,
      required: true
    },
    providerName: {
      type: String,
      default: ''
    }
  },
  emits: ['import'],
  setup() {
    const importing = ref(false)

    const priceColumns = [
      { name: 'quantity', label: 'Qty', field: 'quantity', align: 'left' },
      { name: 'price', label: 'Price', field: 'price', align: 'right',
        format: (val, row) => `${val} ${row.currency || 'USD'}` }
    ]

    const openUrl = (url) => {
      window.open(url, '_blank')
    }

    return {
      importing,
      priceColumns,
      openUrl
    }
  }
}
</script>

<style scoped>
.component-search-result-card {
  border-left: 3px solid #1976d2;
  padding-left: 16px;
}
</style>