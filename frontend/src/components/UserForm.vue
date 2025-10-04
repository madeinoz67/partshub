<template>
  <q-dialog
    v-model="dialogVisible"
    persistent
    maximized
    transition-show="slide-up"
    transition-hide="slide-down"
  >
    <q-card class="column">
      <q-card-section class="row items-center q-pb-none">
        <div class="text-h6">{{ isEditing ? 'Edit User' : 'Create New User' }}</div>
        <q-space />
        <q-btn v-close-popup icon="close" flat round dense />
      </q-card-section>

      <q-card-section class="col">
        <q-form class="q-gutter-md" @submit="handleSubmit">
          <div class="row q-col-gutter-md">
            <div class="col-md-6 col-12">
              <q-input
                v-model="formData.username"
                label="Username *"
                :rules="[val => !!val || 'Username is required']"
                outlined
                dense
              />
            </div>
            <div class="col-md-6 col-12">
              <q-input
                v-model="formData.email"
                label="Email *"
                type="email"
                :rules="[
                  val => !!val || 'Email is required',
                  val => /.+@.+\..+/.test(val) || 'Please enter a valid email'
                ]"
                outlined
                dense
              />
            </div>
          </div>

          <div class="row q-col-gutter-md">
            <div class="col-md-6 col-12">
              <q-input
                v-model="formData.full_name"
                label="Full Name"
                outlined
                dense
              />
            </div>
            <div class="col-md-6 col-12">
              <q-select
                v-model="formData.role"
                :options="roleOptions"
                label="Role *"
                outlined
                dense
                :rules="[val => !!val || 'Role is required']"
              />
            </div>
          </div>

          <div v-if="!isEditing" class="row q-col-gutter-md">
            <div class="col-md-6 col-12">
              <q-input
                v-model="formData.password"
                label="Password *"
                :type="showPassword ? 'text' : 'password'"
                :rules="[
                  val => !!val || 'Password is required',
                  val => val.length >= 6 || 'Password must be at least 6 characters'
                ]"
                outlined
                dense
              >
                <template #append>
                  <q-icon
                    :name="showPassword ? 'visibility_off' : 'visibility'"
                    class="cursor-pointer"
                    @click="showPassword = !showPassword"
                  />
                </template>
              </q-input>
            </div>
            <div class="col-md-6 col-12">
              <q-input
                v-model="formData.confirmPassword"
                label="Confirm Password *"
                :type="showConfirmPassword ? 'text' : 'password'"
                :rules="[
                  val => !!val || 'Please confirm password',
                  val => val === formData.password || 'Passwords do not match'
                ]"
                outlined
                dense
              >
                <template #append>
                  <q-icon
                    :name="showConfirmPassword ? 'visibility_off' : 'visibility'"
                    class="cursor-pointer"
                    @click="showConfirmPassword = !showConfirmPassword"
                  />
                </template>
              </q-input>
            </div>
          </div>

          <div class="row">
            <div class="col-12">
              <q-checkbox
                v-model="formData.is_active"
                label="Active User"
                color="primary"
              />
            </div>
          </div>

          <div class="row">
            <div class="col-12">
              <q-checkbox
                v-model="formData.require_password_change"
                label="Require password change on next login"
                color="warning"
              />
            </div>
          </div>
        </q-form>
      </q-card-section>

      <q-card-actions align="right">
        <q-btn v-close-popup flat label="Cancel" />
        <q-btn
          color="primary"
          label="Save"
          :loading="saving"
          @click="handleSubmit"
        />
      </q-card-actions>
    </q-card>
  </q-dialog>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'

interface UserFormData {
  username: string
  email: string
  full_name: string
  role: string
  password: string
  confirmPassword: string
  is_active: boolean
  require_password_change: boolean
}

interface User {
  id?: string
  username: string
  email?: string
  full_name?: string
  is_admin: boolean
  is_active: boolean
  must_change_password: boolean
}

interface Props {
  modelValue: boolean
  user?: User | null
}

interface Emits {
  (e: 'update:modelValue', value: boolean): void
  (e: 'user-saved', user: User): void
}

const props = withDefaults(defineProps<Props>(), {
  user: null
})

const emit = defineEmits<Emits>()

const dialogVisible = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value)
})

const saving = ref(false)
const showPassword = ref(false)
const showConfirmPassword = ref(false)

const roleOptions = [
  { label: 'User', value: 'user' },
  { label: 'Admin', value: 'admin' }
]

const defaultFormData: UserFormData = {
  username: '',
  email: '',
  full_name: '',
  role: 'user',
  password: '',
  confirmPassword: '',
  is_active: true,
  require_password_change: false
}

const formData = ref<UserFormData>({ ...defaultFormData })

const isEditing = computed(() => !!props.user?.id)

// Watch for user prop changes to populate form
watch(() => props.user, (newUser) => {
  if (newUser) {
    formData.value = {
      username: newUser.username,
      email: newUser.email || '',
      full_name: newUser.full_name || '',
      role: newUser.is_admin ? 'admin' : 'user', // Convert is_admin boolean to role string
      password: '',
      confirmPassword: '',
      is_active: newUser.is_active,
      require_password_change: newUser.must_change_password || false
    }
  } else {
    formData.value = { ...defaultFormData }
  }
}, { immediate: true })

// Reset form when dialog closes
watch(() => props.modelValue, (isVisible) => {
  if (!isVisible) {
    formData.value = { ...defaultFormData }
    saving.value = false
  }
})

async function handleSubmit() {
  saving.value = true

  try {
    const userData: Partial<User> & { password?: string } = {
      username: formData.value.username,
      full_name: formData.value.full_name,
      is_admin: formData.value.role === 'admin', // Convert role string to is_admin boolean
      is_active: formData.value.is_active,
      must_change_password: formData.value.require_password_change
    }

    if (!isEditing.value) {
      userData.password = formData.value.password
    }

    if (isEditing.value) {
      userData.id = props.user?.id
    }

    emit('user-saved', userData)
    dialogVisible.value = false
  } catch (error) {
    console.error('Error saving user:', error)
  } finally {
    saving.value = false
  }
}
</script>