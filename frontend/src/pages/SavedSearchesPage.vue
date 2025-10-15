<template>
  <q-page class="q-pa-md">
    <div class="saved-searches-page">
      <!-- Page Header -->
      <div class="row items-center q-mb-lg">
        <div class="col">
          <div class="text-h4 q-mb-xs">Saved Searches</div>
          <div class="text-subtitle2 text-grey-7">
            Manage your saved component searches
          </div>
        </div>
        <div class="col-auto">
          <q-btn
            label="Back to Components"
            icon="arrow_back"
            color="primary"
            outline
            @click="$router.push('/components')"
          />
        </div>
      </div>

      <!-- Statistics Cards -->
      <div v-if="stats" class="row q-col-gutter-md q-mb-lg">
        <div class="col-12 col-sm-4">
          <q-card flat bordered>
            <q-card-section class="text-center">
              <q-icon name="bookmark" size="3em" color="primary" />
              <div class="text-h5 q-mt-sm">{{ stats.total_searches }}</div>
              <div class="text-caption text-grey-7">Total Searches</div>
            </q-card-section>
          </q-card>
        </div>
        <div class="col-12 col-sm-4">
          <q-card flat bordered>
            <q-card-section class="text-center">
              <q-icon name="check_circle" size="3em" color="positive" />
              <div class="text-h5 q-mt-sm">{{ stats.total_used }}</div>
              <div class="text-caption text-grey-7">Used Searches</div>
            </q-card-section>
          </q-card>
        </div>
        <div class="col-12 col-sm-4">
          <q-card flat bordered>
            <q-card-section class="text-center">
              <q-icon name="pending" size="3em" color="grey-6" />
              <div class="text-h5 q-mt-sm">{{ stats.total_unused }}</div>
              <div class="text-caption text-grey-7">Unused Searches</div>
            </q-card-section>
          </q-card>
        </div>
      </div>

      <!-- Most Used Searches -->
      <div v-if="stats && stats.most_used && stats.most_used.length > 0" class="q-mb-lg">
        <div class="text-h6 q-mb-md">
          <q-icon name="star" color="amber" class="q-mr-sm" />
          Most Used Searches
        </div>
        <q-list bordered separator>
          <q-item
            v-for="search in stats.most_used"
            :key="search.id"
            clickable
            @click="handleExecute(search.id)"
          >
            <q-item-section>
              <q-item-label class="text-weight-medium">{{ search.name }}</q-item-label>
              <q-item-label caption v-if="search.description">
                {{ search.description }}
              </q-item-label>
            </q-item-section>
            <q-item-section side>
              <q-chip dense color="amber" text-color="black" icon="history">
                Used {{ formatDate(search.last_used_at) }}
              </q-chip>
            </q-item-section>
          </q-item>
        </q-list>
      </div>

      <!-- All Saved Searches -->
      <div class="q-mb-lg">
        <div class="text-h6 q-mb-md">All Saved Searches</div>
        <q-card flat bordered>
          <q-card-section>
            <saved-searches
              :compact="false"
              @execute="handleExecute"
              @updated="loadStats"
            />
          </q-card-section>
        </q-card>
      </div>
    </div>
  </q-page>
</template>

<script>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useQuasar } from 'quasar'
import SavedSearches from '../components/SavedSearches.vue'
import { getSavedSearchesStats, executeSavedSearch } from '../services/savedSearchesService'

export default {
  name: 'SavedSearchesPage',
  components: {
    SavedSearches
  },
  setup() {
    const router = useRouter()
    const $q = useQuasar()
    const stats = ref(null)

    const loadStats = async () => {
      try {
        stats.value = await getSavedSearchesStats()
      } catch (error) {
        console.error('Error loading stats:', error)
        $q.notify({
          type: 'negative',
          message: 'Failed to load statistics',
          timeout: 3000
        })
      }
    }

    const handleExecute = async (searchId) => {
      try {
        await executeSavedSearch(searchId)
        // Navigate to components page with parameters
        router.push({
          path: '/components',
          query: {
            savedSearchId: searchId
          }
        })
      } catch (error) {
        console.error('Error executing search:', error)
        $q.notify({
          type: 'negative',
          message: 'Failed to execute search',
          timeout: 3000
        })
      }
    }

    const formatDate = (dateString) => {
      if (!dateString) return 'Never'
      const date = new Date(dateString)
      const now = new Date()
      const diffMs = now - date
      const diffMins = Math.floor(diffMs / 60000)
      const diffHours = Math.floor(diffMs / 3600000)
      const diffDays = Math.floor(diffMs / 86400000)

      if (diffMins < 1) return 'Just now'
      if (diffMins < 60) return `${diffMins}m ago`
      if (diffHours < 24) return `${diffHours}h ago`
      if (diffDays < 7) return `${diffDays}d ago`
      return date.toLocaleDateString()
    }

    onMounted(() => {
      loadStats()
    })

    return {
      stats,
      loadStats,
      handleExecute,
      formatDate
    }
  }
}
</script>

<style scoped>
.saved-searches-page {
  max-width: 1200px;
  margin: 0 auto;
}
</style>
