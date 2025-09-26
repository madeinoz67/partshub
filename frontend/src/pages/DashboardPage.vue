<template>
  <q-page class="q-pa-md">
    <!-- Page Title -->
    <div class="row items-center q-mb-lg">
      <div class="col">
        <div class="text-h4">Dashboard</div>
        <div class="text-caption text-grey">Welcome to PartsHub - Your Electronic Parts Inventory</div>
      </div>
    </div>

    <!-- Quick Stats Cards -->
    <div class="row q-gutter-md q-mb-lg">
      <div class="col-md-3 col-sm-6 col-xs-12">
        <q-card>
          <q-card-section>
            <div class="row items-center">
              <div class="col">
                <div class="text-h6">{{ totalComponents }}</div>
                <div class="text-caption text-grey">Total Components</div>
              </div>
              <div class="col-auto">
                <q-icon name="inventory" size="2em" color="primary" />
              </div>
            </div>
          </q-card-section>
        </q-card>
      </div>

      <div class="col-md-3 col-sm-6 col-xs-12">
        <q-card>
          <q-card-section>
            <div class="row items-center">
              <div class="col">
                <div class="text-h6 text-orange">{{ lowStockCount }}</div>
                <div class="text-caption text-grey">Low Stock</div>
              </div>
              <div class="col-auto">
                <q-icon name="warning" size="2em" color="orange" />
              </div>
            </div>
          </q-card-section>
        </q-card>
      </div>

      <div class="col-md-3 col-sm-6 col-xs-12">
        <q-card>
          <q-card-section>
            <div class="row items-center">
              <div class="col">
                <div class="text-h6 text-red">{{ outOfStockCount }}</div>
                <div class="text-caption text-grey">Out of Stock</div>
              </div>
              <div class="col-auto">
                <q-icon name="error" size="2em" color="red" />
              </div>
            </div>
          </q-card-section>
        </q-card>
      </div>

      <div class="col-md-3 col-sm-6 col-xs-12">
        <q-card>
          <q-card-section>
            <div class="row items-center">
              <div class="col">
                <div class="text-h6">{{ totalLocations }}</div>
                <div class="text-caption text-grey">Storage Locations</div>
              </div>
              <div class="col-auto">
                <q-icon name="folder" size="2em" color="secondary" />
              </div>
            </div>
          </q-card-section>
        </q-card>
      </div>
    </div>

    <!-- Quick Actions -->
    <div class="row q-gutter-md q-mb-lg">
      <div class="col-md-6 col-xs-12">
        <q-card>
          <q-card-section>
            <div class="text-h6 q-mb-md">Quick Actions</div>
            <div class="q-gutter-sm">
              <q-btn
                color="primary"
                icon="add"
                label="Add Component"
                @click="$router.push('/components')"
                class="full-width q-mb-sm"
              />
              <q-btn
                color="secondary"
                icon="folder_open"
                label="Manage Locations"
                @click="$router.push('/storage')"
                class="full-width q-mb-sm"
              />
              <q-btn
                color="accent"
                icon="inventory"
                label="Update Stock"
                @click="$router.push('/components')"
                class="full-width"
              />
            </div>
          </q-card-section>
        </q-card>
      </div>

      <div class="col-md-6 col-xs-12">
        <q-card>
          <q-card-section>
            <div class="text-h6 q-mb-md">Recent Activity</div>
            <div v-if="loading" class="text-center q-pa-md">
              <q-spinner size="2em" />
            </div>
            <div v-else-if="!components.length" class="text-center q-pa-md text-grey">
              No components yet. Add your first component to get started!
            </div>
            <q-list v-else>
              <q-item
                v-for="component in recentComponents"
                :key="component.id"
                clickable
                @click="$router.push(`/components/${component.id}`)"
              >
                <q-item-section>
                  <q-item-label>{{ component.name }}</q-item-label>
                  <q-item-label caption>
                    {{ component.part_number || 'No part number' }}
                  </q-item-label>
                </q-item-section>
                <q-item-section side>
                  <q-chip
                    :color="getStockStatusColor(component)"
                    text-color="white"
                    :label="component.quantity_on_hand"
                    size="sm"
                  />
                </q-item-section>
              </q-item>
            </q-list>
          </q-card-section>
        </q-card>
      </div>
    </div>

    <!-- Welcome Message for Empty State -->
    <div v-if="!loading && !components.length" class="text-center q-pa-xl">
      <q-icon name="inventory" size="6em" color="grey-4" />
      <div class="text-h5 text-grey q-mt-md">Welcome to PartsHub!</div>
      <div class="text-grey q-mb-lg">
        Start by adding your first electronic components and organizing your workspace.
      </div>
      <q-btn
        color="primary"
        size="lg"
        label="Add First Component"
        icon="add"
        @click="$router.push('/components')"
      />
    </div>
  </q-page>
</template>

<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { storeToRefs } from 'pinia'
import { useComponentsStore } from '../stores/components'
import { useStorageStore } from '../stores/storage'
import type { Component } from '../services/api'

const componentsStore = useComponentsStore()
const storageStore = useStorageStore()

const {
  components,
  loading,
  lowStockComponents,
  outOfStockComponents,
  totalComponents
} = storeToRefs(componentsStore)

const { locations } = storeToRefs(storageStore)

const lowStockCount = computed(() => lowStockComponents.value.length)
const outOfStockCount = computed(() => outOfStockComponents.value.length)
const totalLocations = computed(() => locations.value.length)

const recentComponents = computed(() => {
  return components.value
    .slice()
    .sort((a, b) => new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime())
    .slice(0, 5)
})

const getStockStatusColor = (component: Component) => {
  if (component.quantity_on_hand === 0) return 'negative'
  if (component.quantity_on_hand <= component.minimum_stock && component.minimum_stock > 0) return 'warning'
  return 'positive'
}

onMounted(() => {
  // Load initial data
  componentsStore.fetchComponents()
  storageStore.fetchLocations()
})
</script>