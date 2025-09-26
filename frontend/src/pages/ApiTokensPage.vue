<template>
  <q-page class="q-pa-lg">
    <div class="row items-center q-mb-lg">
      <div class="col">
        <div class="text-h4">API Tokens</div>
        <div class="text-subtitle2 text-grey-6">
          Manage API access tokens for programmatic access to PartsHub
        </div>
      </div>
      <div class="col-auto">
        <q-btn
          color="primary"
          icon="add"
          label="Create Token"
          @click="showCreateDialog = true"
          unelevated
        />
      </div>
    </div>

    <!-- Tokens table -->
    <q-table
      :rows="tokens"
      :columns="columns"
      :loading="isLoading"
      row-key="id"
      :pagination="{ rowsPerPage: 10 }"
      flat
      class="q-mt-md"
    >
      <template v-slot:body-cell-prefix="props">
        <q-td :props="props">
          <code class="text-primary">{{ props.value }}***</code>
        </q-td>
      </template>

      <template v-slot:body-cell-status="props">
        <q-td :props="props">
          <q-badge
            :color="getStatusColor(props.row)"
            :label="getStatusLabel(props.row)"
          />
        </q-td>
      </template>

      <template v-slot:body-cell-expires_at="props">
        <q-td :props="props">
          <span v-if="props.value">
            {{ formatDate(props.value) }}
          </span>
          <span v-else class="text-grey-6">Never</span>
        </q-td>
      </template>

      <template v-slot:body-cell-last_used_at="props">
        <q-td :props="props">
          <span v-if="props.value">
            {{ formatDate(props.value) }}
          </span>
          <span v-else class="text-grey-6">Never used</span>
        </q-td>
      </template>

      <template v-slot:body-cell-actions="props">
        <q-td :props="props">
          <q-btn
            flat
            dense
            round
            icon="delete"
            color="negative"
            @click="confirmDelete(props.row)"
            :disable="!props.row.is_active"
          >
            <q-tooltip>Revoke Token</q-tooltip>
          </q-btn>
        </q-td>
      </template>

      <template v-slot:no-data>
        <div class="full-width row flex-center q-gutter-sm text-grey-6">
          <q-icon size="2em" name="key_off" />
          <span>No API tokens found</span>
        </div>
      </template>
    </q-table>

    <!-- Create Token Dialog -->
    <q-dialog v-model="showCreateDialog" persistent>
      <q-card style="min-width: 400px">
        <q-card-section class="row items-center">
          <q-icon name="key" size="24px" class="q-mr-sm" />
          <span class="text-h6">Create API Token</span>
        </q-card-section>

        <q-card-section>
          <q-form @submit="createToken" class="q-gutter-md" ref="createForm">
            <q-input
              filled
              v-model="newToken.name"
              label="Token Name"
              hint="A descriptive name for this token"
              lazy-rules
              :rules="[ val => val && val.length > 0 || 'Token name is required']"
              :readonly="isCreating"
            >
              <template v-slot:prepend>
                <q-icon name="label" />
              </template>
            </q-input>

            <q-input
              filled
              v-model="newToken.description"
              label="Description (Optional)"
              hint="Additional details about this token's purpose"
              type="textarea"
              rows="3"
              :readonly="isCreating"
            >
              <template v-slot:prepend>
                <q-icon name="description" />
              </template>
            </q-input>

            <q-select
              filled
              v-model="selectedExpiryOption"
              :options="expiryOptions"
              option-label="label"
              option-value="value"
              label="Token Expiry"
              :hint="selectedExpiryOption?.description || 'Choose when this token should expire'"
              :readonly="isCreating"
              clearable
              @update:model-value="updateExpiryDays"
            >
              <template v-slot:prepend>
                <q-icon name="schedule" />
              </template>

              <template v-slot:option="scope">
                <q-item v-bind="scope.itemProps">
                  <q-item-section>
                    <q-item-label>{{ scope.opt.label }}</q-item-label>
                    <q-item-label caption>{{ scope.opt.description }}</q-item-label>
                  </q-item-section>
                  <q-item-section side v-if="scope.opt.value === null">
                    <q-icon name="warning" color="orange" size="xs">
                      <q-tooltip>Not recommended for production</q-tooltip>
                    </q-icon>
                  </q-item-section>
                </q-item>
              </template>
            </q-select>

            <div v-if="error" class="text-negative q-mt-sm">
              {{ error }}
            </div>
          </q-form>
        </q-card-section>

        <q-card-actions align="right">
          <q-btn
            flat
            label="Cancel"
            @click="cancelCreate"
            :disable="isCreating"
          />
          <q-btn
            unelevated
            color="primary"
            label="Create Token"
            @click="createToken"
            :loading="isCreating"
          />
        </q-card-actions>
      </q-card>
    </q-dialog>

    <!-- Token Created Dialog -->
    <q-dialog v-model="showTokenDialog" persistent>
      <q-card style="min-width: 500px">
        <q-card-section class="row items-center">
          <q-icon name="check_circle" color="positive" size="24px" class="q-mr-sm" />
          <span class="text-h6">Token Created Successfully</span>
        </q-card-section>

        <q-card-section>
          <div class="q-mb-md">
            <strong>Important:</strong> This is the only time you'll see the full token.
            Copy it now and store it securely.
          </div>

          <q-input
            filled
            v-model="createdTokenValue"
            label="API Token"
            readonly
            class="q-mb-md"
          >
            <template v-slot:append>
              <q-btn
                flat
                dense
                icon="content_copy"
                @click="copyToken"
                color="primary"
              >
                <q-tooltip>Copy Token</q-tooltip>
              </q-btn>
            </template>
          </q-input>

          <div class="text-body2 text-grey-7">
            Token Details:
            <ul>
              <li><strong>Name:</strong> {{ createdToken?.name }}</li>
              <li><strong>Prefix:</strong> {{ createdToken?.prefix }}</li>
              <li v-if="createdToken?.expires_at">
                <strong>Expires:</strong> {{ formatDate(createdToken.expires_at) }}
              </li>
              <li v-else><strong>Expires:</strong> Never</li>
            </ul>
          </div>
        </q-card-section>

        <q-card-actions align="right">
          <q-btn
            unelevated
            color="primary"
            label="Done"
            @click="closeTokenDialog"
          />
        </q-card-actions>
      </q-card>
    </q-dialog>

    <!-- Delete Confirmation Dialog -->
    <q-dialog v-model="showDeleteDialog" persistent>
      <q-card>
        <q-card-section class="row items-center">
          <q-icon name="warning" color="warning" size="24px" class="q-mr-sm" />
          <span class="text-h6">Revoke API Token</span>
        </q-card-section>

        <q-card-section>
          Are you sure you want to revoke the token "<strong>{{ tokenToDelete?.name }}</strong>"?
          This action cannot be undone and any applications using this token will lose access.
        </q-card-section>

        <q-card-actions align="right">
          <q-btn
            flat
            label="Cancel"
            @click="showDeleteDialog = false"
            :disable="isDeleting"
          />
          <q-btn
            unelevated
            color="negative"
            label="Revoke Token"
            @click="deleteToken"
            :loading="isDeleting"
          />
        </q-card-actions>
      </q-card>
    </q-dialog>
  </q-page>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useQuasar, QTableColumn, QForm } from 'quasar'
import { useAuthStore, type APIToken, type APITokenCreated, type CreateAPITokenRequest } from '../stores/auth'

const $q = useQuasar()
const authStore = useAuthStore()

// State
const tokens = ref<APIToken[]>([])
const isLoading = ref(false)
const error = ref<string | null>(null)

// Create dialog state
const showCreateDialog = ref(false)
const isCreating = ref(false)
const createForm = ref<QForm>()
const newToken = ref<CreateAPITokenRequest>({
  name: '',
  description: undefined,
  expires_in_days: undefined
})

// Expiry options with industry standard timeframes
const selectedExpiryOption = ref<ExpiryOption | null>(null)

interface ExpiryOption {
  label: string
  value: number | null
  description: string
}

const expiryOptions: ExpiryOption[] = [
  { label: 'Never expires', value: null, description: 'Token will never expire (not recommended for production)' },
  { label: '24 hours', value: 1, description: 'Good for temporary testing' },
  { label: '1 week', value: 7, description: 'Short-term access' },
  { label: '1 month', value: 30, description: 'Medium-term access' },
  { label: '3 months', value: 90, description: 'Quarterly rotation' },
  { label: '6 months', value: 180, description: 'Semi-annual rotation' },
  { label: '1 year', value: 365, description: 'Annual rotation (maximum)' }
]

// Token created dialog state
const showTokenDialog = ref(false)
const createdToken = ref<APITokenCreated | null>(null)
const createdTokenValue = ref('')

// Delete dialog state
const showDeleteDialog = ref(false)
const isDeleting = ref(false)
const tokenToDelete = ref<APIToken | null>(null)

// Table columns
const columns: QTableColumn[] = [
  {
    name: 'name',
    label: 'Name',
    align: 'left',
    field: 'name',
    sortable: true
  },
  {
    name: 'prefix',
    label: 'Token',
    align: 'left',
    field: 'prefix',
    sortable: false
  },
  {
    name: 'description',
    label: 'Description',
    align: 'left',
    field: 'description',
    sortable: false
  },
  {
    name: 'status',
    label: 'Status',
    align: 'center',
    field: 'is_active',
    sortable: true
  },
  {
    name: 'expires_at',
    label: 'Expires',
    align: 'left',
    field: 'expires_at',
    sortable: true
  },
  {
    name: 'last_used_at',
    label: 'Last Used',
    align: 'left',
    field: 'last_used_at',
    sortable: true
  },
  {
    name: 'actions',
    label: 'Actions',
    align: 'center',
    field: '',
    sortable: false
  }
]

// Load tokens on mount
onMounted(() => {
  loadTokens()
})

async function loadTokens() {
  isLoading.value = true
  error.value = null

  try {
    tokens.value = await authStore.getAPITokens()
  } catch (err: any) {
    console.error('Failed to load tokens:', err)
    error.value = err.response?.data?.detail || 'Failed to load tokens'
    $q.notify({
      type: 'negative',
      message: 'Failed to load API tokens'
    })
  } finally {
    isLoading.value = false
  }
}

function updateExpiryDays(option: ExpiryOption | null) {
  newToken.value.expires_in_days = option?.value || undefined
}

async function createToken() {
  const valid = await createForm.value?.validate()
  if (!valid) return

  isCreating.value = true
  error.value = null

  try {
    const token = await authStore.createAPIToken({
      name: newToken.value.name,
      description: newToken.value.description || undefined,
      expires_in_days: newToken.value.expires_in_days || undefined
    })

    createdToken.value = token
    createdTokenValue.value = token.token
    showTokenDialog.value = true
    showCreateDialog.value = false

    // Reload tokens
    await loadTokens()

    $q.notify({
      type: 'positive',
      message: 'API token created successfully'
    })
  } catch (err: any) {
    console.error('Failed to create token:', err)
    error.value = err.response?.data?.detail || 'Failed to create token'
  } finally {
    isCreating.value = false
  }
}

function cancelCreate() {
  showCreateDialog.value = false
  resetCreateForm()
}

function resetCreateForm() {
  newToken.value = {
    name: '',
    description: undefined,
    expires_in_days: undefined
  }
  selectedExpiryOption.value = null
  error.value = null
}

function closeTokenDialog() {
  showTokenDialog.value = false
  createdToken.value = null
  createdTokenValue.value = ''
  resetCreateForm()
}

async function copyToken() {
  try {
    await navigator.clipboard.writeText(createdTokenValue.value)
    $q.notify({
      type: 'positive',
      message: 'Token copied to clipboard',
      position: 'bottom'
    })
  } catch (err) {
    console.error('Failed to copy token:', err)
    $q.notify({
      type: 'negative',
      message: 'Failed to copy token'
    })
  }
}

function confirmDelete(token: APIToken) {
  tokenToDelete.value = token
  showDeleteDialog.value = true
}

async function deleteToken() {
  if (!tokenToDelete.value) return

  isDeleting.value = true

  try {
    await authStore.revokeAPIToken(tokenToDelete.value.id)

    showDeleteDialog.value = false
    tokenToDelete.value = null

    // Reload tokens
    await loadTokens()

    $q.notify({
      type: 'positive',
      message: 'API token revoked successfully'
    })
  } catch (err: any) {
    console.error('Failed to revoke token:', err)
    $q.notify({
      type: 'negative',
      message: 'Failed to revoke token'
    })
  } finally {
    isDeleting.value = false
  }
}

function getStatusColor(token: APIToken): string {
  if (!token.is_active) return 'negative'
  if (token.expires_at && new Date(token.expires_at) < new Date()) return 'warning'
  return 'positive'
}

function getStatusLabel(token: APIToken): string {
  if (!token.is_active) return 'Revoked'
  if (token.expires_at && new Date(token.expires_at) < new Date()) return 'Expired'
  return 'Active'
}

function formatDate(dateString: string): string {
  return new Date(dateString).toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
}
</script>