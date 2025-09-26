<template>
  <q-layout view="lHh Lpr lFf">
    <q-header elevated>
      <q-toolbar>
        <q-toolbar-title>
          <div class="cursor-pointer" @click="$router.push('/components')">
            <q-avatar>
              <q-icon name="inventory" />
            </q-avatar>
            PartsHub
          </div>
        </q-toolbar-title>

        <!-- Top Navigation Links -->
        <q-tabs
          v-model="currentTab"
          align="center"
          class="q-mx-lg"
        >
          <q-tab
            v-for="link in visibleLinks"
            :key="link.title"
            :name="link.link"
            :icon="link.icon"
            :label="link.title"
            @click="$router.push(link.link)"
          />
        </q-tabs>

        <q-space />

        <!-- User menu for authenticated users -->
        <div class="q-mr-md" v-if="authStore.isAuthenticated">
          <q-btn-dropdown
            flat
            :label="authStore.user?.username || 'User'"
            icon="person"
            dropdown-icon="arrow_drop_down"
          >
            <q-list>
              <q-item>
                <q-item-section>
                  <q-item-label>{{ authStore.user?.full_name || authStore.user?.username }}</q-item-label>
                  <q-item-label caption>
                    {{ authStore.isAdmin ? 'Administrator' : 'User' }}
                  </q-item-label>
                </q-item-section>
              </q-item>

              <q-separator />

              <q-item
                clickable
                v-close-popup
                @click="showPasswordChangeDialog = true"
              >
                <q-item-section avatar>
                  <q-icon name="lock" />
                </q-item-section>
                <q-item-section>Change Password</q-item-section>
              </q-item>

              <q-item
                v-if="authStore.isAdmin"
                clickable
                v-close-popup
                @click="$router.push('/api-tokens')"
              >
                <q-item-section avatar>
                  <q-icon name="key" />
                </q-item-section>
                <q-item-section>API Tokens</q-item-section>
              </q-item>

              <q-item
                clickable
                v-close-popup
                @click="logout"
              >
                <q-item-section avatar>
                  <q-icon name="logout" />
                </q-item-section>
                <q-item-section>Logout</q-item-section>
              </q-item>
            </q-list>
          </q-btn-dropdown>
        </div>

        <!-- Login button for anonymous users -->
        <div class="q-mr-md" v-else>
          <q-btn
            flat
            icon="login"
            label="Login"
            @click="$router.push('/login')"
          />
        </div>

        <div class="text-caption">v1.0.0</div>
      </q-toolbar>
    </q-header>

    <q-page-container>
      <router-view />
    </q-page-container>

    <!-- Password Change Dialog for required password changes -->
    <PasswordChangeDialog
      v-model="showPasswordChangeDialog"
      @password-changed="onPasswordChanged"
    />
  </q-layout>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import PasswordChangeDialog from '../components/PasswordChangeDialog.vue'

interface EssentialLink {
  title: string
  caption: string
  icon: string
  link: string
  adminOnly?: boolean
}

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()

// Password change dialog state
const showPasswordChangeDialog = ref(false)

const essentialLinks: EssentialLink[] = [
  {
    title: 'Components',
    caption: 'Manage electronic components',
    icon: 'inventory',
    link: '/components'
  },
  {
    title: 'Storage Locations',
    caption: 'Organize workspace',
    icon: 'folder',
    link: '/storage'
  },
  {
    title: 'Dashboard',
    caption: 'Overview and statistics',
    icon: 'dashboard',
    link: '/dashboard'
  },
  {
    title: 'API Tokens',
    caption: 'Manage API access tokens',
    icon: 'key',
    link: '/api-tokens',
    adminOnly: true
  }
]

const visibleLinks = computed(() => {
  return essentialLinks.filter(link => !link.adminOnly || authStore.isAdmin)
})

const currentTab = computed(() => route.path)

async function logout() {
  await authStore.logout()
  router.push('/')
}

const onPasswordChanged = () => {
  showPasswordChangeDialog.value = false
}

// Initialize auth store and check for password change requirement
onMounted(async () => {
  await authStore.initialize()

  // Show password change dialog if required
  if (authStore.requiresPasswordChange) {
    showPasswordChangeDialog.value = true
  }
})

// Watch for auth state changes
watch(() => authStore.requiresPasswordChange, (requiresChange) => {
  if (requiresChange) {
    showPasswordChangeDialog.value = true
  }
})
</script>