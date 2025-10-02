<template>
  <q-dialog v-model="isVisible" persistent>
    <q-card style="min-width: 400px">
      <q-card-section class="row items-center">
        <q-icon name="lock" size="24px" class="q-mr-sm" />
        <span class="text-h6">Password Change Required</span>
      </q-card-section>

      <q-card-section>
        <div class="q-mb-md">
          Your password must be changed before you can continue using the application.
        </div>

        <q-form ref="passwordForm" class="q-gutter-md" @submit="changePassword">
          <q-input
            v-model="currentPassword"
            filled
            label="Current Password"
            type="password"
            lazy-rules
            :rules="[val => val && val.length > 0 || 'Current password is required']"
            :readonly="isChanging"
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
            :readonly="isChanging"
          >
            <template #prepend>
              <q-icon name="vpn_key" />
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
            :readonly="isChanging"
          >
            <template #prepend>
              <q-icon name="verified_user" />
            </template>
          </q-input>

          <div v-if="error" class="text-negative q-mt-sm">
            {{ error }}
          </div>
        </q-form>
      </q-card-section>

      <q-card-actions align="right">
        <q-btn
          unelevated
          color="primary"
          label="Change Password"
          :loading="isChanging"
          @click="changePassword"
        />
      </q-card-actions>
    </q-card>
  </q-dialog>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useQuasar, QForm } from 'quasar'
import { useAuthStore } from '../stores/auth'

interface Props {
  modelValue: boolean
}

interface Emits {
  (e: 'update:modelValue', value: boolean): void
  (e: 'password-changed'): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

const $q = useQuasar()
const authStore = useAuthStore()

const isVisible = computed({
  get: () => props.modelValue,
  set: (value: boolean) => emit('update:modelValue', value)
})

const passwordForm = ref<QForm>()
const currentPassword = ref('')
const newPassword = ref('')
const confirmPassword = ref('')
const isChanging = ref(false)
const error = ref<string | null>(null)

const changePassword = async () => {
  const valid = await passwordForm.value?.validate()
  if (!valid) return

  isChanging.value = true
  error.value = null

  try {
    const success = await authStore.changePassword(currentPassword.value, newPassword.value)

    if (success) {
      $q.notify({
        type: 'positive',
        message: 'Password changed successfully',
        position: 'top-right'
      })

      // Reset form
      currentPassword.value = ''
      newPassword.value = ''
      confirmPassword.value = ''

      emit('password-changed')
      isVisible.value = false
    } else {
      error.value = authStore.error || 'Failed to change password'
    }
  } catch (err: unknown) {
    error.value = err instanceof Error ? err.message : 'Failed to change password'
  } finally {
    isChanging.value = false
  }
}
</script>