<template>
  <q-layout view="lHh Lpr lFf">
    <q-header elevated>
      <q-toolbar>
        <!-- Mobile menu button -->
        <q-btn
          v-if="$q.screen.lt.md"
          flat
          dense
          round
          icon="menu"
          aria-label="Menu"
          @click="leftDrawerOpen = !leftDrawerOpen"
        />

        <q-toolbar-title>
          <div class="cursor-pointer" @click="$router.push('/components')">
            <q-avatar>
              <q-icon name="inventory" />
            </q-avatar>
            <span class="q-ml-sm">PartsHub</span>
          </div>
        </q-toolbar-title>

        <!-- Desktop Navigation Links -->
        <q-tabs
          v-if="$q.screen.gt.sm"
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

        <!-- Desktop User menu for authenticated users -->
        <div v-if="authStore.isAuthenticated && $q.screen.gt.sm" class="q-mr-md">
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
                v-close-popup
                clickable
                @click="showPasswordChangeDialog = true"
              >
                <q-item-section avatar>
                  <q-icon name="lock" />
                </q-item-section>
                <q-item-section>Change Password</q-item-section>
              </q-item>

              <q-item
                v-if="authStore.isAdmin"
                v-close-popup
                clickable
                @click="$router.push('/admin')"
              >
                <q-item-section avatar>
                  <q-icon name="admin_panel_settings" />
                </q-item-section>
                <q-item-section>Admin Panel</q-item-section>
              </q-item>

              <q-item
                v-close-popup
                clickable
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

        <!-- Mobile User menu - just icon -->
        <div v-else-if="authStore.isAuthenticated" class="q-mr-sm">
          <q-btn
            flat
            round
            dense
            icon="person"
            @click="rightDrawerOpen = !rightDrawerOpen"
          />
        </div>

        <!-- Desktop Login button for anonymous users -->
        <div v-if="!authStore.isAuthenticated && $q.screen.gt.sm" class="q-mr-md">
          <q-btn
            flat
            icon="login"
            label="Login"
            @click="$router.push('/login')"
          />
        </div>

        <!-- Mobile Login button - just icon -->
        <div v-else-if="!authStore.isAuthenticated" class="q-mr-sm">
          <q-btn
            flat
            round
            dense
            icon="login"
            @click="$router.push('/login')"
          />
        </div>

        <!-- Version - hide on mobile -->
        <div v-if="$q.screen.gt.xs" class="text-caption">v1.0.0</div>
      </q-toolbar>
    </q-header>

    <!-- Mobile Left Drawer for Navigation -->
    <q-drawer
      v-if="$q.screen.lt.md"
      v-model="leftDrawerOpen"
      show-if-above
      bordered
      side="left"
      overlay
      behavior="mobile"
      :width="250"
    >
      <q-list>
        <q-item-label header>Navigation</q-item-label>

        <q-item
          v-for="link in visibleLinks"
          :key="link.title"
          v-ripple
          clickable
          :active="currentTab === link.link"
          @click="navigateAndCloseDrawer(link.link)"
        >
          <q-item-section avatar>
            <q-icon :name="link.icon" />
          </q-item-section>
          <q-item-section>
            <q-item-label>{{ link.title }}</q-item-label>
            <q-item-label caption>{{ link.caption }}</q-item-label>
          </q-item-section>
        </q-item>
      </q-list>
    </q-drawer>

    <!-- Mobile Right Drawer for User Menu -->
    <q-drawer
      v-if="$q.screen.lt.md && authStore.isAuthenticated"
      v-model="rightDrawerOpen"
      side="right"
      overlay
      behavior="mobile"
      :width="250"
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
          v-ripple
          clickable
          @click="showPasswordChangeDialog = true; rightDrawerOpen = false"
        >
          <q-item-section avatar>
            <q-icon name="lock" />
          </q-item-section>
          <q-item-section>Change Password</q-item-section>
        </q-item>

        <q-item
          v-if="authStore.isAdmin"
          v-ripple
          clickable
          @click="navigateAndCloseDrawer('/admin')"
        >
          <q-item-section avatar>
            <q-icon name="admin_panel_settings" />
          </q-item-section>
          <q-item-section>Admin Panel</q-item-section>
        </q-item>

        <q-item
          v-ripple
          clickable
          @click="logout; rightDrawerOpen = false"
        >
          <q-item-section avatar>
            <q-icon name="logout" />
          </q-item-section>
          <q-item-section>Logout</q-item-section>
        </q-item>
      </q-list>
    </q-drawer>

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

// Dialog and drawer state
const showPasswordChangeDialog = ref(false)
const leftDrawerOpen = ref(false)
const rightDrawerOpen = ref(false)

const essentialLinks: EssentialLink[] = [
  {
    title: 'Components',
    caption: 'Manage electronic components',
    icon: 'inventory',
    link: '/components'
  },
  {
    title: 'Projects',
    caption: 'Manage project BOMs',
    icon: 'engineering',
    link: '/projects'
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
    title: 'Admin',
    caption: 'System administration',
    icon: 'admin_panel_settings',
    link: '/admin',
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

const navigateAndCloseDrawer = (path: string) => {
  router.push(path)
  leftDrawerOpen.value = false
  rightDrawerOpen.value = false
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