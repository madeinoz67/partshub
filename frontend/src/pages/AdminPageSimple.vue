<template>
  <q-page class="admin-page">
    <div class="q-pa-lg">
      <div class="text-h4">System Administration</div>
      <div class="text-subtitle1 text-grey-6 q-mb-lg">
        Manage users, system settings, and view analytics
      </div>

      <!-- Simple test content -->
      <q-card>
        <q-card-section>
          <div class="text-h6">Admin Panel Test</div>
          <p>This is a simplified admin page to test navigation.</p>

          <!-- Main tabs -->
          <q-tabs v-model="activeTab" class="q-mb-md">
            <q-tab name="dashboard" label="Dashboard" icon="dashboard" />
            <q-tab name="users" label="User Management" icon="people" />
            <q-tab name="system" label="System" icon="settings" />
          </q-tabs>

          <q-tab-panels v-model="activeTab">
            <q-tab-panel name="dashboard">
              <div class="text-h6">Dashboard</div>
              <p>System overview and statistics</p>
            </q-tab-panel>

            <q-tab-panel name="users">
              <div class="text-h6">User Management</div>

              <!-- Sub-tabs -->
              <q-tabs v-model="userSubTab" dense class="q-mb-md">
                <q-tab name="users-list" label="Users" />
                <q-tab name="api-tokens" label="API Tokens" />
              </q-tabs>

              <q-tab-panels v-model="userSubTab">
                <q-tab-panel name="users-list">
                  <p>User management interface</p>
                </q-tab-panel>
                <q-tab-panel name="api-tokens">
                  <p>API token management interface</p>
                </q-tab-panel>
              </q-tab-panels>
            </q-tab-panel>

            <q-tab-panel name="system">
              <div class="text-h6">System Management</div>

              <!-- Sub-tabs -->
              <q-tabs v-model="systemSubTab" dense class="q-mb-md">
                <q-tab name="health" label="Health" />
                <q-tab name="kicad" label="KiCad" />
                <q-tab name="database" label="Database" />
              </q-tabs>

              <q-tab-panels v-model="systemSubTab">
                <q-tab-panel name="health">
                  <p>System health monitoring</p>
                </q-tab-panel>
                <q-tab-panel name="kicad">
                  <p>KiCad integration management</p>
                </q-tab-panel>
                <q-tab-panel name="database">
                  <p>Database administration</p>
                </q-tab-panel>
              </q-tab-panels>
            </q-tab-panel>
          </q-tab-panels>
        </q-card-section>
      </q-card>
    </div>
  </q-page>
</template>

<script setup>
import { ref } from 'vue'

const activeTab = ref('dashboard')
const userSubTab = ref('users-list')
const systemSubTab = ref('health')
</script>