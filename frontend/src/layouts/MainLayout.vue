<template>
  <q-layout view="lHh Lpr lFf">
    <q-header elevated>
      <q-toolbar>
        <q-toolbar-title>
          <q-avatar>
            <q-icon name="inventory" />
          </q-avatar>
          PartsHub
        </q-toolbar-title>

        <!-- Top Navigation Links -->
        <q-tabs
          v-model="currentTab"
          align="center"
          class="q-mx-lg"
        >
          <q-tab
            v-for="link in essentialLinks"
            :key="link.title"
            :name="link.link"
            :icon="link.icon"
            :label="link.title"
            @click="$router.push(link.link)"
          />
        </q-tabs>

        <div>v1.0.0</div>
      </q-toolbar>
    </q-header>

    <q-page-container>
      <router-view />
    </q-page-container>
  </q-layout>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRoute } from 'vue-router'

interface EssentialLink {
  title: string
  caption: string
  icon: string
  link: string
}

const route = useRoute()

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
  }
]

const currentTab = computed(() => route.path)
</script>