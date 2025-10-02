<template>
  <q-page class="q-pa-md">
    <!-- Breadcrumb Navigation -->
    <q-breadcrumbs class="q-mb-md">
      <q-breadcrumbs-el label="Storage Locations" :to="{ name: 'storage' }" />
      <q-breadcrumbs-el
        :label="location?.name || 'Loading...'"
        :to="{ name: 'storage-location-detail', params: { id: locationId } }"
      />
    </q-breadcrumbs>

    <!-- Loading State -->
    <div v-if="loading" class="row justify-center q-mt-xl">
      <q-spinner-dots size="50px" color="primary" />
    </div>

    <!-- Error State -->
    <div v-else-if="error" class="row justify-center q-mt-xl">
      <q-card class="q-pa-lg">
        <q-card-section class="text-center">
          <q-icon name="error" size="48px" color="negative" class="q-mb-md" />
          <div class="text-h6">Error Loading Storage Location</div>
          <div class="text-body2 text-grey q-mt-sm">{{ error }}</div>
        </q-card-section>
      </q-card>
    </div>

    <!-- Location Details -->
    <div v-else-if="location">
      <!-- Location Information Card -->
      <q-card class="q-mb-lg">
        <q-card-section>
          <div class="row items-center">
            <div class="col">
              <div class="text-h4">{{ location.name }}</div>
              <div class="text-subtitle1 text-grey">{{ location.location_hierarchy }}</div>
              <div v-if="location.description" class="text-body2 q-mt-sm">{{ location.description }}</div>
            </div>
            <div class="col-auto">
              <q-chip
                :color="getTypeColor(location.type)"
                text-color="white"
                :label="location.type"
                size="md"
              />
            </div>
          </div>
        </q-card-section>
      </q-card>

      <!-- Components in this Location -->
      <q-card>
        <q-card-section>
          <div class="text-h6 q-mb-md">Components Stored Here</div>

          <!-- Loading Components -->
          <div v-if="componentsLoading" class="text-center q-pa-md">
            <q-spinner-dots size="24px" color="primary" />
            <div class="text-body2 text-grey q-mt-sm">Loading components...</div>
          </div>

          <!-- No Components -->
          <div v-else-if="components.length === 0" class="text-center q-pa-md">
            <q-icon name="inventory_2" size="48px" color="grey-5" class="q-mb-md" />
            <div class="text-body1 text-grey">No components stored in this location</div>
          </div>

          <!-- Components List -->
          <div v-else>
            <q-list separator>
              <q-item
v-for="component in components" :key="component.id" clickable
                      :to="{ name: 'component-detail', params: { id: component.id } }"
                      :class="{
                        'depleted-item': component.quantity_on_hand === 0,
                        'low-stock-item': component.quantity_on_hand > 0 && component.quantity_on_hand <= component.minimum_stock
                      }">
                <q-item-section>
                  <q-item-label>{{ component.name }}</q-item-label>
                  <q-item-label caption>
                    {{ component.part_number }} • {{ component.manufacturer }}
                  </q-item-label>
                </q-item-section>
                <q-item-section side>
                  <div class="text-right">
                    <div
class="text-body2 stock-quantity"
                         :class="{
                           'depleted-text': component.quantity_on_hand === 0,
                           'low-stock-text': component.quantity_on_hand > 0 && component.quantity_on_hand <= component.minimum_stock
                         }">
                      <q-icon
                        v-if="component.quantity_on_hand === 0"
                        name="warning"
                        color="negative"
                        size="18px"
                        class="q-mr-xs"
                        :title="'Out of stock'"
                      />
                      <q-icon
                        v-else-if="component.quantity_on_hand <= component.minimum_stock"
                        name="error_outline"
                        color="orange"
                        size="18px"
                        class="q-mr-xs"
                        :title="'Low stock'"
                      />
                      {{ component.quantity_on_hand }}
                    </div>
                    <div class="text-caption text-grey">
                      on hand
                      <span v-if="component.minimum_stock > 0" class="text-grey">
                        (min: {{ component.minimum_stock }})
                      </span>
                    </div>
                  </div>
                </q-item-section>
              </q-item>
            </q-list>
          </div>
        </q-card-section>
      </q-card>
    </div>
  </q-page>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRoute } from 'vue-router'
import { api } from '../services/api'

const route = useRoute()
const locationId = computed(() => route.params.id as string)

const location = ref(null)
const components = ref([])
const loading = ref(true)
const componentsLoading = ref(true)
const error = ref('')

const getTypeColor = (type: string) => {
  const colors = {
    building: 'brown',
    room: 'blue',
    cabinet: 'purple',
    shelf: 'green',
    drawer: 'orange',
    bin: 'teal',
    container: 'grey'
  }
  return colors[type] || 'grey'
}

const fetchLocation = async () => {
  try {
    loading.value = true
    error.value = ''

    const response = await api.get(`/api/v1/storage-locations/${locationId.value}`, {
      params: {
        include_children: true,
        include_component_count: true,
        include_full_hierarchy: true
      }
    })

    location.value = response.data
  } catch (err) {
    console.error('Error fetching storage location:', err)
    error.value = 'Failed to load storage location details'
  } finally {
    loading.value = false
  }
}

const fetchComponents = async () => {
  try {
    componentsLoading.value = true

    const response = await api.get(`/api/v1/storage-locations/${locationId.value}/components`, {
      params: {
        include_children: false,
        limit: 100
      }
    })

    components.value = response.data
  } catch (err) {
    console.error('Error fetching location components:', err)
  } finally {
    componentsLoading.value = false
  }
}

onMounted(async () => {
  await Promise.all([fetchLocation(), fetchComponents()])
})
</script>

<style scoped>
/* Stock level highlighting */
.depleted-item {
  background-color: rgba(244, 67, 54, 0.05);
  border-left: 3px solid #f44336;
}

.low-stock-item {
  background-color: rgba(255, 152, 0, 0.05);
  border-left: 3px solid #ff9800;
}

.depleted-text {
  color: #f44336;
  font-weight: 600;
}

.low-stock-text {
  color: #ff9800;
  font-weight: 600;
}

.stock-quantity {
  display: flex;
  align-items: center;
  justify-content: flex-end;
}
</style>