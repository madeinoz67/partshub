<template>
  <div class="login-container">
    <q-card class="login-card">
      <q-card-section class="text-center">
        <q-avatar size="64px" class="q-mb-md">
          <q-icon name="inventory" size="48px" color="primary" />
        </q-avatar>
        <div class="text-h4 q-mb-sm">PartsHub</div>
        <div class="text-subtitle2 text-grey-7">Electronic Parts Management</div>
      </q-card-section>

      <q-card-section>
        <q-form
          ref="form"
          class="q-gutter-md"
          @submit="onSubmit"
        >
          <q-input
            v-model="username"
            filled
            label="Username"
            hint="Default username: admin"
            lazy-rules
            :rules="[ val => val && val.length > 0 || 'Username is required']"
            :readonly="isLoading"
          >
            <template #prepend>
              <q-icon name="person" />
            </template>
          </q-input>

          <q-input
            v-model="password"
            filled
            label="Password"
            :type="isPwd ? 'password' : 'text'"
            lazy-rules
            :rules="[ val => val && val.length > 0 || 'Password is required']"
            :readonly="isLoading"
            @keyup.enter="onSubmit"
          >
            <template #prepend>
              <q-icon name="lock" />
            </template>
            <template #append>
              <q-icon
                :name="isPwd ? 'visibility_off' : 'visibility'"
                class="cursor-pointer"
                @click="isPwd = !isPwd"
              />
            </template>
          </q-input>

          <div v-if="authStore.error" class="text-negative q-mt-sm">
            {{ authStore.error }}
          </div>

          <div class="q-pt-md">
            <q-btn
              unelevated
              type="submit"
              color="primary"
              class="full-width"
              label="Sign In"
              :loading="isLoading"
              size="lg"
            />
          </div>
        </q-form>
      </q-card-section>

      <!-- Password Change Dialog -->
      <q-dialog v-model="showPasswordChange" persistent>
        <q-card style="min-width: 400px">
          <q-card-section class="text-center">
            <q-icon name="security" size="48px" color="warning" />
            <div class="text-h6 q-mt-sm">Password Change Required</div>
            <div class="text-subtitle2 text-grey-7 q-mt-sm">
              You must change your password before continuing
            </div>
          </q-card-section>

          <q-card-section>
            <q-form ref="passwordForm" class="q-gutter-md" @submit="onPasswordChange">
              <q-input
                v-model="currentPassword"
                filled
                label="Current Password"
                type="password"
                lazy-rules
                :rules="[ val => val && val.length > 0 || 'Current password is required']"
                :readonly="isLoading"
              >
                <template #prepend>
                  <q-icon name="lock" />
                </template>
              </q-input>

              <q-input
                v-model="newPassword"
                filled
                label="New Password"
                type="password"
                lazy-rules
                :rules="[
                  val => val && val.length >= 8 || 'Password must be at least 8 characters',
                  val => val !== currentPassword || 'New password must be different from current password'
                ]"
                :readonly="isLoading"
              >
                <template #prepend>
                  <q-icon name="lock_reset" />
                </template>
              </q-input>

              <q-input
                v-model="confirmPassword"
                filled
                label="Confirm New Password"
                type="password"
                lazy-rules
                :rules="[
                  val => val && val.length > 0 || 'Please confirm your password',
                  val => val === newPassword || 'Passwords do not match'
                ]"
                :readonly="isLoading"
                @keyup.enter="onPasswordChange"
              >
                <template #prepend>
                  <q-icon name="lock_reset" />
                </template>
              </q-input>

              <div v-if="authStore.error" class="text-negative q-mt-sm">
                {{ authStore.error }}
              </div>

              <div class="q-pt-md">
                <q-btn
                  unelevated
                  type="submit"
                  color="primary"
                  class="full-width"
                  label="Change Password"
                  :loading="isLoading"
                  size="lg"
                />
              </div>
            </q-form>
          </q-card-section>
        </q-card>
      </q-dialog>
    </q-card>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { QForm } from 'quasar'

const router = useRouter()
const authStore = useAuthStore()

// Login form
const form = ref<QForm>()
const username = ref('admin')
const password = ref('')
const isPwd = ref(true)

// Password change form
const passwordForm = ref<QForm>()
const showPasswordChange = ref(false)
const currentPassword = ref('')
const newPassword = ref('')
const confirmPassword = ref('')

const isLoading = computed(() => authStore.isLoading)

async function onSubmit() {
  const valid = await form.value?.validate()
  if (!valid) return

  const success = await authStore.login(username.value, password.value)

  if (success) {
    if (authStore.requiresPasswordChange) {
      // Show password change dialog
      showPasswordChange.value = true
      currentPassword.value = password.value // Pre-fill current password
    } else {
      // Redirect to dashboard
      router.push('/dashboard')
    }
  }
}

async function onPasswordChange() {
  const valid = await passwordForm.value?.validate()
  if (!valid) return

  const success = await authStore.changePassword(currentPassword.value, newPassword.value)

  if (success) {
    showPasswordChange.value = false
    // Redirect to dashboard
    router.push('/dashboard')
  }
}

// Clear any existing errors when component loads
authStore.error = null
</script>

<style scoped>
.login-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
  padding: 20px;
}

.login-card {
  width: 100%;
  max-width: 400px;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.1);
}
</style>