<template>
  <q-page class="q-pa-md">
    <!-- Breadcrumb Navigation -->
    <q-breadcrumbs class="q-mb-md">
      <q-breadcrumbs-el label="Components" :to="{ name: 'components' }" />
      <q-breadcrumbs-el
        :label="component?.name || 'Loading...'"
        :to="{ name: 'component-detail', params: { id: componentId } }"
      />
    </q-breadcrumbs>

    <!-- Component Detail -->
    <ComponentDetail
      :component-id="componentId"
      @edit-component="editComponent"
      @update-stock="updateStock"
    />

    <!-- Component Form Dialog -->
    <ComponentForm
      v-model="showEditDialog"
      :component="component"
      :is-edit="true"
      @saved="onComponentSaved"
    />

    <!-- Stock Update Dialog -->
    <StockUpdateDialog
      v-model="showStockDialog"
      :component="component"
      @updated="onStockUpdated"
    />
  </q-page>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRoute } from 'vue-router'
import { useQuasar } from 'quasar'
import { storeToRefs } from 'pinia'
import ComponentDetail from '../components/ComponentDetail.vue'
import ComponentForm from '../components/ComponentForm.vue'
import StockUpdateDialog from '../components/StockUpdateDialog.vue'
import { useComponentsStore } from '../stores/components'
import type { Component } from '../services/api'

const route = useRoute()
const $q = useQuasar()
const componentsStore = useComponentsStore()

const { currentComponent: component } = storeToRefs(componentsStore)

const componentId = computed(() => route.params.id as string)
const showEditDialog = ref(false)
const showStockDialog = ref(false)

const editComponent = (component: Component) => {
  showEditDialog.value = true
}

const updateStock = (component: Component) => {
  showStockDialog.value = true
}

const onComponentSaved = (component: Component) => {
  $q.notify({
    type: 'positive',
    message: 'Component updated successfully',
    position: 'top-right'
  })

  showEditDialog.value = false
}

const onStockUpdated = () => {
  $q.notify({
    type: 'positive',
    message: 'Stock updated successfully',
    position: 'top-right'
  })

  showStockDialog.value = false
}
</script>