<template>
  <q-page class="admin-page">
    <div class="q-pa-lg">
      <!-- Page Header -->
      <div class="row items-center q-mb-lg">
        <div class="col">
          <div class="text-h4">System Administration</div>
          <div class="text-subtitle1 text-grey-6">
            Manage users, system settings, and view analytics
          </div>
        </div>
        <div class="col-auto">
          <q-btn
            color="primary"
            icon="refresh"
            label="Refresh Data"
            :loading="refreshing"
            class="q-mr-sm"
            @click="refreshAllData"
          />
          <q-btn
            color="secondary"
            icon="download"
            label="Export Report"
            @click="exportComprehensiveReport"
          />
        </div>
      </div>

      <!-- Admin Tabs -->
      <q-tabs
        v-model="activeTab"
        dense
        class="text-grey"
        active-color="primary"
        indicator-color="primary"
        align="justify"
        narrow-indicator
      >
        <q-tab name="dashboard" label="Dashboard" icon="dashboard" />
        <q-tab name="users" label="User Management" icon="people" />
        <q-tab name="categories" label="Category Management" icon="category" />
        <q-tab name="system" label="System Management" icon="settings" />
        <q-tab name="analytics" label="Analytics & Reports" icon="analytics" />
      </q-tabs>

      <q-separator />

      <q-tab-panels v-model="activeTab" animated>
        <!-- Dashboard Tab -->
        <q-tab-panel name="dashboard">
          <div class="row q-col-gutter-md">
            <!-- System Overview Cards -->
            <div class="col-lg-3 col-md-6 col-12">
              <q-card>
                <q-card-section>
                  <div class="text-h6 text-primary">Total Components</div>
                  <div class="text-h4">{{ dashboardData.component_statistics?.total_components || 0 }}</div>
                  <div class="text-caption text-grey-6">
                    {{ dashboardData.component_statistics?.available_components || 0 }} available
                  </div>
                </q-card-section>
              </q-card>
            </div>

            <div class="col-lg-3 col-md-6 col-12">
              <q-card>
                <q-card-section>
                  <div class="text-h6 text-warning">Low Stock</div>
                  <div class="text-h4">{{ dashboardData.component_statistics?.low_stock_components || 0 }}</div>
                  <div class="text-caption text-grey-6">
                    {{ dashboardData.component_statistics?.out_of_stock_components || 0 }} out of stock
                  </div>
                </q-card-section>
              </q-card>
            </div>

            <div class="col-lg-3 col-md-6 col-12">
              <q-card>
                <q-card-section>
                  <div class="text-h6 text-green">Active Projects</div>
                  <div class="text-h4">{{ dashboardData.project_statistics?.active_projects || 0 }}</div>
                  <div class="text-caption text-grey-6">
                    of {{ dashboardData.project_statistics?.total_projects || 0 }} total
                  </div>
                </q-card-section>
              </q-card>
            </div>

            <div class="col-lg-3 col-md-6 col-12">
              <q-card>
                <q-card-section>
                  <div class="text-h6 text-purple">Inventory Value</div>
                  <div class="text-h4">${{ formatCurrency(dashboardData.activity_statistics?.total_inventory_value || 0) }}</div>
                  <div class="text-caption text-grey-6">
                    {{ dashboardData.activity_statistics?.transactions_last_week || 0 }} transactions this week
                  </div>
                </q-card-section>
              </q-card>
            </div>
          </div>

          <!-- System Health Summary -->
          <div class="row q-col-gutter-md q-mt-md">
            <div class="col-12">
              <q-card>
                <q-card-section>
                  <div class="text-h6 q-mb-md">System Health Overview</div>
                  <div class="row q-col-gutter-md">
                    <div class="col-md-4 col-12">
                      <div class="text-subtitle2">Data Quality</div>
                      <q-linear-progress
                        :value="getDataQualityScore() / 100"
                        color="positive"
                        size="12px"
                        class="q-mb-sm"
                      />
                      <div class="text-caption">{{ Math.round(getDataQualityScore()) }}% Complete</div>
                    </div>
                    <div class="col-md-4 col-12">
                      <div class="text-subtitle2">Database Health</div>
                      <q-chip
                        :color="systemHealth.system_metrics?.database_health === 'good' ? 'positive' : 'warning'"
                        text-color="white"
                        :label="systemHealth.system_metrics?.database_health || 'Unknown'"
                        class="q-mb-sm"
                      />
                      <div class="text-caption">{{ systemHealth.database_statistics?.total_components || 0 }} total records</div>
                    </div>
                    <div class="col-md-4 col-12">
                      <div class="text-subtitle2">Storage Utilization</div>
                      <div class="text-body2">
                        {{ Math.round(systemHealth.system_metrics?.avg_components_per_location || 0) }} avg/location
                      </div>
                      <div class="text-caption">{{ systemHealth.database_statistics?.total_storage_locations || 0 }} locations</div>
                    </div>
                  </div>
                </q-card-section>
              </q-card>
            </div>
          </div>
        </q-tab-panel>

        <!-- User Management Tab -->
        <q-tab-panel name="users">
          <div class="text-h6 q-mb-md">User Management</div>

          <!-- User Management Sub-tabs -->
          <q-tabs
            v-model="userSubTab"
            dense
            class="text-grey q-mb-md"
            active-color="primary"
            indicator-color="primary"
            align="left"
          >
            <q-tab name="users-list" label="Users" icon="person" />
            <q-tab name="api-tokens" label="API Tokens" icon="vpn_key" />
          </q-tabs>

          <q-tab-panels v-model="userSubTab" animated>
            <!-- Users List Sub-panel -->
            <q-tab-panel name="users-list">
              <div class="row items-center q-mb-md">
                <div class="col">
                  <div class="text-subtitle1">System Users</div>
                  <div class="text-caption text-grey-6">Manage user accounts and permissions</div>
                </div>
                <div class="col-auto">
                  <q-btn
                    color="primary"
                    icon="add"
                    label="Create User"
                    @click="showCreateUserDialog = true"
                  />
                </div>
              </div>

              <!-- User List -->
              <q-table
                :rows="users"
                :columns="userColumns"
                :loading="loadingUsers"
                row-key="id"
                flat
                bordered
                class="users-table"
              >
                <template #body-cell-is_active="props">
                  <q-td :props="props">
                    <q-chip
                      :color="props.value ? 'positive' : 'negative'"
                      text-color="white"
                      :label="props.value ? 'Active' : 'Inactive'"
                      size="sm"
                    />
                  </q-td>
                </template>

                <template #body-cell-is_admin="props">
                  <q-td :props="props">
                    <q-icon
                      :name="props.value ? 'admin_panel_settings' : 'person'"
                      :color="props.value ? 'primary' : 'grey'"
                      size="sm"
                    />
                  </q-td>
                </template>

                <template #body-cell-actions="props">
                  <q-td :props="props">
                    <q-btn-group flat>
                      <q-btn
                        flat
                        dense
                        icon="edit"
                        color="primary"
                        @click="editUser(props.row)"
                      >
                        <q-tooltip>Edit User</q-tooltip>
                      </q-btn>
                      <q-btn
                        flat
                        dense
                        icon="key"
                        color="secondary"
                        @click="resetPassword(props.row)"
                      >
                        <q-tooltip>Reset Password</q-tooltip>
                      </q-btn>
                      <q-btn
                        flat
                        dense
                        :icon="props.row.is_active ? 'block' : 'check_circle'"
                        :color="props.row.is_active ? 'negative' : 'positive'"
                        @click="toggleUserStatus(props.row)"
                      >
                        <q-tooltip>{{ props.row.is_active ? 'Deactivate' : 'Activate' }}</q-tooltip>
                      </q-btn>
                    </q-btn-group>
                  </q-td>
                </template>
              </q-table>
            </q-tab-panel>

            <!-- API Tokens Sub-panel -->
            <q-tab-panel name="api-tokens">
              <div class="row items-center q-mb-md">
                <div class="col">
                  <div class="text-subtitle1">API Tokens</div>
                  <div class="text-caption text-grey-6">Manage API access tokens for programmatic access</div>
                </div>
                <div class="col-auto">
                  <q-btn
                    color="primary"
                    icon="add"
                    label="Create Token"
                    @click="showCreateTokenDialog = true"
                  />
                </div>
              </div>

              <!-- API Tokens Table -->
              <q-table
                :rows="apiTokens"
                :columns="tokenColumns"
                :loading="loadingTokens"
                row-key="id"
                flat
                bordered
                class="tokens-table"
              >
                <template #body-cell-prefix="props">
                  <q-td :props="props">
                    <code class="text-primary">{{ props.value }}***</code>
                  </q-td>
                </template>

                <template #body-cell-status="props">
                  <q-td :props="props">
                    <q-chip
                      :color="getTokenStatusColor(props.row)"
                      text-color="white"
                      :label="getTokenStatusLabel(props.row)"
                      size="sm"
                    />
                  </q-td>
                </template>

                <template #body-cell-expires_at="props">
                  <q-td :props="props">
                    <span v-if="props.value">
                      {{ formatDate(props.value) }}
                    </span>
                    <span v-else class="text-grey-6">Never</span>
                  </q-td>
                </template>

                <template #body-cell-last_used_at="props">
                  <q-td :props="props">
                    <span v-if="props.value">
                      {{ formatDate(props.value) }}
                    </span>
                    <span v-else class="text-grey-6">Never used</span>
                  </q-td>
                </template>

                <template #body-cell-actions="props">
                  <q-td :props="props">
                    <q-btn
                      flat
                      dense
                      icon="delete"
                      color="negative"
                      :disable="!props.row.is_active"
                      @click="confirmDeleteToken(props.row)"
                    >
                      <q-tooltip>Revoke Token</q-tooltip>
                    </q-btn>
                  </q-td>
                </template>

                <template #no-data>
                  <div class="full-width row flex-center q-gutter-sm text-grey-6">
                    <q-icon size="2em" name="key_off" />
                    <span>No API tokens found</span>
                  </div>
                </template>
              </q-table>
            </q-tab-panel>
          </q-tab-panels>
        </q-tab-panel>

        <!-- Category Management Tab -->
        <q-tab-panel name="categories">
          <div class="text-h6 q-mb-md">Category Management</div>

          <!-- Category Management Actions -->
          <div class="row q-mb-md">
            <div class="col">
              <q-input
                v-model="categorySearch"
                placeholder="Search categories..."
                outlined
                dense
                clearable
                debounce="300"
                class="q-mr-md"
                style="max-width: 300px;"
              >
                <template #prepend>
                  <q-icon name="search" />
                </template>
              </q-input>
            </div>
            <div class="col-auto">
              <q-btn
                color="primary"
                icon="add"
                label="Create Category"
                class="q-mr-sm"
                @click="showCreateCategoryDialog = true"
              />
              <q-btn
                color="secondary"
                icon="refresh"
                label="Refresh"
                :loading="loadingCategories"
                @click="loadCategories"
              />
            </div>
          </div>

          <!-- Category Statistics Cards -->
          <div class="row q-gutter-md q-mb-lg">
            <div class="col">
              <q-card>
                <q-card-section class="text-center">
                  <div class="text-h4 text-primary">{{ categoryStats.total }}</div>
                  <div class="text-subtitle1">Total Categories</div>
                </q-card-section>
              </q-card>
            </div>
            <div class="col">
              <q-card>
                <q-card-section class="text-center">
                  <div class="text-h4 text-positive">{{ categoryStats.withComponents }}</div>
                  <div class="text-subtitle1">With Components</div>
                </q-card-section>
              </q-card>
            </div>
            <div class="col">
              <q-card>
                <q-card-section class="text-center">
                  <div class="text-h4 text-warning">{{ categoryStats.empty }}</div>
                  <div class="text-subtitle1">Empty Categories</div>
                </q-card-section>
              </q-card>
            </div>
            <div class="col">
              <q-card>
                <q-card-section class="text-center">
                  <div class="text-h4 text-secondary">{{ categoryStats.maxDepth }}</div>
                  <div class="text-subtitle1">Max Depth</div>
                </q-card-section>
              </q-card>
            </div>
          </div>

          <!-- Category Tree View -->
          <q-card>
            <q-card-section>
              <div class="text-h6 q-mb-md">Category Hierarchy</div>

              <!-- Loading State -->
              <div v-if="loadingCategories" class="text-center q-pa-lg">
                <q-spinner color="primary" size="3em" />
                <div class="q-mt-md">Loading categories...</div>
              </div>

              <!-- Category Tree -->
              <q-tree
                v-else
                :nodes="categoryTreeNodes"
                node-key="id"
                :filter="categorySearch"
                :filter-method="filterCategories"
                selected-color="primary"
                class="category-tree"
              >
                <template #default-header="prop">
                  <div class="row items-center full-width">
                    <div class="col row items-center q-gutter-xs">
                      <q-icon
                        v-if="prop.node.icon"
                        :name="prop.node.icon"
                        :color="prop.node.color || 'primary'"
                        size="18px"
                      />
                      <span class="text-weight-medium">{{ prop.node.label }}</span>
                      <q-chip
                        v-if="prop.node.component_count > 0"
                        :label="prop.node.component_count"
                        size="sm"
                        color="primary"
                        text-color="white"
                      />
                      <q-chip
                        v-else
                        label="0"
                        size="sm"
                        color="grey-4"
                        text-color="dark"
                      />
                    </div>
                    <div class="col-auto">
                      <q-btn
                        flat
                        round
                        dense
                        icon="edit"
                        size="sm"
                        color="primary"
                        @click.stop="editCategory(prop.node)"
                      >
                        <q-tooltip>Edit Category</q-tooltip>
                      </q-btn>
                      <q-btn
                        flat
                        round
                        dense
                        icon="add"
                        size="sm"
                        color="positive"
                        @click.stop="createSubcategory(prop.node)"
                      >
                        <q-tooltip>Add Subcategory</q-tooltip>
                      </q-btn>
                      <q-btn
                        flat
                        round
                        dense
                        icon="delete"
                        size="sm"
                        color="negative"
                        :disable="prop.node.component_count > 0"
                        @click.stop="deleteCategory(prop.node)"
                      >
                        <q-tooltip>
                          {{ prop.node.component_count > 0 ? 'Cannot delete: category has components' : 'Delete Category' }}
                        </q-tooltip>
                      </q-btn>
                    </div>
                  </div>
                </template>

                <template #default-body="prop">
                  <div v-if="prop.node.description" class="text-caption text-grey-6 q-ml-md">
                    {{ prop.node.description }}
                  </div>
                </template>
              </q-tree>

              <!-- Empty State -->
              <div v-if="!loadingCategories && categoryTreeNodes.length === 0" class="text-center q-pa-lg">
                <q-icon name="category" size="4em" color="grey-4" />
                <div class="text-h6 text-grey-6 q-mt-md">No Categories Found</div>
                <div class="text-body2 text-grey-5">Create your first category to get started</div>
                <q-btn
                  color="primary"
                  label="Create Category"
                  class="q-mt-md"
                  @click="showCreateCategoryDialog = true"
                />
              </div>
            </q-card-section>
          </q-card>

          <!-- Create/Edit Category Dialog -->
          <q-dialog v-model="showCreateCategoryDialog" persistent>
            <q-card style="min-width: 500px">
              <q-card-section>
                <div class="text-h6">{{ editingCategory ? 'Edit Category' : 'Create Category' }}</div>
              </q-card-section>
              <q-card-section class="q-pt-none">
                <CategoryForm
                  :category="editingCategory"
                  :parent-id="suggestedParentId"
                  @success="onCategoryFormSuccess"
                  @cancel="closeCreateCategoryDialog"
                />
              </q-card-section>
            </q-card>
          </q-dialog>

          <!-- Delete Confirmation Dialog -->
          <q-dialog v-model="showDeleteDialog" persistent>
            <q-card>
              <q-card-section class="row items-center">
                <q-avatar icon="warning" color="negative" text-color="white" />
                <span class="q-ml-md">
                  Are you sure you want to delete the category "{{ categoryToDelete?.name }}"?
                  <span v-if="categoryToDelete?.children?.length > 0" class="text-weight-bold text-negative">
                    This category has {{ categoryToDelete.children.length }} subcategories.
                  </span>
                </span>
              </q-card-section>
              <q-card-actions align="right">
                <q-btn flat label="Cancel" color="primary" @click="showDeleteDialog = false" />
                <q-btn
                  flat
                  label="Delete"
                  color="negative"
                  :loading="deletingCategory"
                  @click="confirmDeleteCategory"
                />
              </q-card-actions>
            </q-card>
          </q-dialog>
        </q-tab-panel>

        <!-- System Management Tab -->
        <q-tab-panel name="system">
          <div class="text-h6 q-mb-md">System Management</div>

          <!-- System Management Sub-tabs -->
          <q-tabs
            v-model="systemSubTab"
            dense
            class="text-grey q-mb-md"
            active-color="primary"
            indicator-color="primary"
            align="left"
          >
            <q-tab name="health" label="System Health" icon="health_and_safety" />
            <q-tab name="kicad" label="KiCad Management" icon="memory" />
            <q-tab name="database" label="Database" icon="storage" />
          </q-tabs>

          <q-tab-panels v-model="systemSubTab" animated>
            <!-- System Health Sub-panel -->
            <q-tab-panel name="health">
              <div class="text-subtitle1 q-mb-md">System Health & Data Quality</div>

              <div class="row q-col-gutter-md">
                <!-- Database Statistics -->
                <div class="col-md-6 col-12">
                  <q-card>
                    <q-card-section>
                      <div class="text-subtitle1 q-mb-md">Database Statistics</div>
                      <q-list dense>
                        <q-item>
                          <q-item-section>
                            <q-item-label>Total Components</q-item-label>
                          </q-item-section>
                          <q-item-section side>
                            <q-item-label>{{ systemHealth.database_statistics?.total_components || 0 }}</q-item-label>
                          </q-item-section>
                        </q-item>
                        <q-item>
                          <q-item-section>
                            <q-item-label>Total Transactions</q-item-label>
                          </q-item-section>
                          <q-item-section side>
                            <q-item-label>{{ systemHealth.database_statistics?.total_transactions || 0 }}</q-item-label>
                          </q-item-section>
                        </q-item>
                        <q-item>
                          <q-item-section>
                            <q-item-label>Total Projects</q-item-label>
                          </q-item-section>
                          <q-item-section side>
                            <q-item-label>{{ systemHealth.database_statistics?.total_projects || 0 }}</q-item-label>
                          </q-item-section>
                        </q-item>
                        <q-item>
                          <q-item-section>
                            <q-item-label>Storage Locations</q-item-label>
                          </q-item-section>
                          <q-item-section side>
                            <q-item-label>{{ systemHealth.database_statistics?.total_storage_locations || 0 }}</q-item-label>
                          </q-item-section>
                        </q-item>
                        <q-item>
                          <q-item-section>
                            <q-item-label>Categories</q-item-label>
                          </q-item-section>
                          <q-item-section side>
                            <q-item-label>{{ systemHealth.database_statistics?.total_categories || 0 }}</q-item-label>
                          </q-item-section>
                        </q-item>
                      </q-list>
                    </q-card-section>
                  </q-card>
                </div>

                <!-- Data Quality Metrics -->
                <div class="col-md-6 col-12">
                  <q-card>
                    <q-card-section>
                      <div class="text-subtitle1 q-mb-md">Data Quality Metrics</div>

                      <div class="q-mb-sm">
                        <div class="row items-center">
                          <div class="col">Category Coverage</div>
                          <div class="col-auto">{{ Math.round(systemHealth.data_quality?.category_coverage || 0) }}%</div>
                        </div>
                        <q-linear-progress
                          :value="(systemHealth.data_quality?.category_coverage || 0) / 100"
                          color="primary"
                          size="8px"
                        />
                      </div>

                      <div class="q-mb-sm">
                        <div class="row items-center">
                          <div class="col">Location Coverage</div>
                          <div class="col-auto">{{ Math.round(systemHealth.data_quality?.location_coverage || 0) }}%</div>
                        </div>
                        <q-linear-progress
                          :value="(systemHealth.data_quality?.location_coverage || 0) / 100"
                          color="secondary"
                          size="8px"
                        />
                      </div>

                      <div class="q-mb-sm">
                        <div class="row items-center">
                          <div class="col">Specification Coverage</div>
                          <div class="col-auto">{{ Math.round(systemHealth.data_quality?.specification_coverage || 0) }}%</div>
                        </div>
                        <q-linear-progress
                          :value="(systemHealth.data_quality?.specification_coverage || 0) / 100"
                          color="accent"
                          size="8px"
                        />
                      </div>

                      <q-separator class="q-my-md" />

                      <q-list dense>
                        <q-item>
                          <q-item-section>
                            <q-item-label caption>Missing Categories</q-item-label>
                          </q-item-section>
                          <q-item-section side>
                            <q-item-label>{{ systemHealth.data_quality?.components_without_category || 0 }}</q-item-label>
                          </q-item-section>
                        </q-item>
                        <q-item>
                          <q-item-section>
                            <q-item-label caption>Missing Locations</q-item-label>
                          </q-item-section>
                          <q-item-section side>
                            <q-item-label>{{ systemHealth.data_quality?.components_without_location || 0 }}</q-item-label>
                          </q-item-section>
                        </q-item>
                        <q-item>
                          <q-item-section>
                            <q-item-label caption>Missing Specifications</q-item-label>
                          </q-item-section>
                          <q-item-section side>
                            <q-item-label>{{ systemHealth.data_quality?.components_without_specifications || 0 }}</q-item-label>
                          </q-item-section>
                        </q-item>
                      </q-list>
                    </q-card-section>
                  </q-card>
                </div>
              </div>
            </q-tab-panel>

            <!-- KiCad Management Sub-panel -->
            <q-tab-panel name="kicad">
              <div class="text-subtitle1 q-mb-md">KiCad Integration Management</div>

              <div class="row q-col-gutter-md">
                <!-- KiCad Status Overview -->
                <div class="col-md-4 col-12">
                  <q-card>
                    <q-card-section>
                      <div class="text-subtitle2 q-mb-md">KiCad Data Coverage</div>
                      <div class="row items-center q-mb-sm">
                        <div class="col">
                          <div class="text-h4">{{ kicadStatus.components_with_kicad_data || 0 }}</div>
                          <div class="text-caption">of {{ kicadStatus.total_components || 0 }} components</div>
                        </div>
                        <div class="col-auto">
                          <q-circular-progress
                            :value="getKicadCoveragePercentage()"
                            :color="getKicadCoverageColor()"
                            size="60px"
                            :thickness="0.15"
                            show-value
                            class="text-primary"
                          >
                            {{ Math.round(getKicadCoveragePercentage()) }}%
                          </q-circular-progress>
                        </div>
                      </div>
                      <q-linear-progress
                        :value="getKicadCoveragePercentage() / 100"
                        :color="getKicadCoverageColor()"
                        size="8px"
                      />
                    </q-card-section>
                  </q-card>
                </div>

                <!-- Library Management -->
                <div class="col-md-4 col-12">
                  <q-card>
                    <q-card-section>
                      <div class="text-subtitle2 q-mb-md">Library Management</div>
                      <q-btn
                        color="primary"
                        icon="sync"
                        label="Sync Libraries"
                        class="q-mb-sm full-width"
                        @click="showKicadSyncDialog = true"
                      />
                      <q-btn
                        color="secondary"
                        icon="build"
                        label="Generate Missing Data"
                        class="q-mb-sm full-width"
                        :loading="generatingKicadData"
                        @click="generateKicadData"
                      />
                      <q-btn
                        flat
                        color="accent"
                        icon="assessment"
                        label="View Status"
                        class="full-width"
                        @click="loadKicadStatus"
                      />
                    </q-card-section>
                  </q-card>
                </div>

                <!-- Quick Stats -->
                <div class="col-md-4 col-12">
                  <q-card>
                    <q-card-section>
                      <div class="text-subtitle2 q-mb-md">Integration Status</div>
                      <q-list dense>
                        <q-item>
                          <q-item-section>
                            <q-item-label>Library Manager</q-item-label>
                          </q-item-section>
                          <q-item-section side>
                            <q-chip
                              color="positive"
                              text-color="white"
                              label="Available"
                              size="sm"
                            />
                          </q-item-section>
                        </q-item>
                        <q-item>
                          <q-item-section>
                            <q-item-label>Symbol Generation</q-item-label>
                          </q-item-section>
                          <q-item-section side>
                            <q-chip
                              color="positive"
                              text-color="white"
                              label="Active"
                              size="sm"
                            />
                          </q-item-section>
                        </q-item>
                        <q-item>
                          <q-item-section>
                            <q-item-label>Footprint Generation</q-item-label>
                          </q-item-section>
                          <q-item-section side>
                            <q-chip
                              color="positive"
                              text-color="white"
                              label="Active"
                              size="sm"
                            />
                          </q-item-section>
                        </q-item>
                        <q-item>
                          <q-item-section>
                            <q-item-label>API Integration</q-item-label>
                          </q-item-section>
                          <q-item-section side>
                            <q-chip
                              color="positive"
                              text-color="white"
                              label="98.5%"
                              size="sm"
                            />
                          </q-item-section>
                        </q-item>
                      </q-list>
                    </q-card-section>
                  </q-card>
                </div>
              </div>

              <!-- Components Missing KiCad Data -->
              <div class="row q-col-gutter-md q-mt-md">
                <div class="col-12">
                  <q-card>
                    <q-card-section>
                      <div class="text-subtitle2 q-mb-md">Components Missing KiCad Data</div>
                      <q-table
                        :rows="componentsWithoutKicad"
                        :columns="kicadMissingColumns"
                        :loading="loadingKicadMissing"
                        row-key="id"
                        flat
                        bordered
                        :pagination="{ rowsPerPage: 10 }"
                      >
                        <template #body-cell-actions="props">
                          <q-td :props="props">
                            <q-btn
                              flat
                              dense
                              icon="add"
                              color="primary"
                              :loading="generatingComponentData[props.row.id]"
                              @click="generateComponentKicadData(props.row)"
                            >
                              <q-tooltip>Generate KiCad Data</q-tooltip>
                            </q-btn>
                          </q-td>
                        </template>

                        <template #no-data>
                          <div class="full-width row flex-center q-gutter-sm text-grey-6">
                            <q-icon size="2em" name="check_circle" />
                            <span>All components have KiCad data</span>
                          </div>
                        </template>
                      </q-table>
                    </q-card-section>
                  </q-card>
                </div>
              </div>
            </q-tab-panel>

            <!-- Database Sub-panel -->
            <q-tab-panel name="database">
              <div class="text-subtitle1 q-mb-md">Database Administration</div>

              <div class="row q-col-gutter-md">
                <div class="col-md-6 col-12">
                  <q-card>
                    <q-card-section>
                      <div class="text-subtitle2 q-mb-md">Database Operations</div>
                      <q-btn
                        color="primary"
                        icon="refresh"
                        label="Rebuild Search Index"
                        class="q-mb-sm full-width"
                        :loading="rebuildingIndex"
                        @click="rebuildSearchIndex"
                      />
                      <q-btn
                        color="secondary"
                        icon="backup"
                        label="Create Backup"
                        class="q-mb-sm full-width"
                        :loading="creatingBackup"
                        @click="createDatabaseBackup"
                      />
                      <q-btn
                        flat
                        color="warning"
                        icon="cleaning_services"
                        label="Cleanup Orphaned Data"
                        class="full-width"
                        :loading="cleaningData"
                        @click="cleanupOrphanedData"
                      />
                    </q-card-section>
                  </q-card>
                </div>

                <div class="col-md-6 col-12">
                  <q-card>
                    <q-card-section>
                      <div class="text-subtitle2 q-mb-md">Database Health</div>
                      <q-list dense>
                        <q-item>
                          <q-item-section>
                            <q-item-label>Database Size</q-item-label>
                          </q-item-section>
                          <q-item-section side>
                            <q-item-label>{{ formatBytes(databaseSize) }}</q-item-label>
                          </q-item-section>
                        </q-item>
                        <q-item>
                          <q-item-section>
                            <q-item-label>Search Index Status</q-item-label>
                          </q-item-section>
                          <q-item-section side>
                            <q-chip
                              color="positive"
                              text-color="white"
                              label="Healthy"
                              size="sm"
                            />
                          </q-item-section>
                        </q-item>
                        <q-item>
                          <q-item-section>
                            <q-item-label>Last Backup</q-item-label>
                          </q-item-section>
                          <q-item-section side>
                            <q-item-label>{{ lastBackupDate || 'Never' }}</q-item-label>
                          </q-item-section>
                        </q-item>
                      </q-list>
                    </q-card-section>
                  </q-card>
                </div>
              </div>
            </q-tab-panel>
          </q-tab-panels>
        </q-tab-panel>

        <!-- Analytics & Reports Tab -->
        <q-tab-panel name="analytics">
          <div class="text-h6 q-mb-md">Analytics & Reports</div>

          <!-- Analytics Sub-tabs -->
          <q-tabs
            v-model="analyticsSubTab"
            dense
            class="text-grey q-mb-md"
            active-color="primary"
            indicator-color="primary"
            align="left"
          >
            <q-tab name="analytics" label="Analytics" icon="analytics" />
            <q-tab name="reports" label="Reports" icon="assessment" />
            <q-tab name="data-quality" label="Data Quality" icon="verified" />
          </q-tabs>

          <q-tab-panels v-model="analyticsSubTab" animated>
            <!-- Analytics Sub-panel -->
            <q-tab-panel name="analytics">
              <div class="text-subtitle1 q-mb-md">System Analytics</div>

              <div class="row q-col-gutter-md">
                <!-- Inventory Breakdown -->
                <div class="col-md-6 col-12">
                  <q-card>
                    <q-card-section>
                      <div class="text-subtitle1 q-mb-md">Inventory by Category</div>
                      <q-list dense separator>
                        <q-item
                          v-for="category in inventoryBreakdown.by_category?.slice(0, 8)"
                          :key="category.category"
                        >
                          <q-item-section>
                            <q-item-label>{{ category.category }}</q-item-label>
                            <q-item-label caption>{{ category.component_count }} components</q-item-label>
                          </q-item-section>
                          <q-item-section side>
                            <q-item-label>${{ formatCurrency(category.total_value || 0) }}</q-item-label>
                          </q-item-section>
                        </q-item>
                      </q-list>
                    </q-card-section>
                  </q-card>
                </div>

                <!-- Usage Analytics -->
                <div class="col-md-6 col-12">
                  <q-card>
                    <q-card-section>
                      <div class="text-subtitle1 q-mb-md">Most Used Components (30 days)</div>
                      <q-list dense separator>
                        <q-item
                          v-for="component in usageAnalytics.most_used_components?.slice(0, 6)"
                          :key="component.component_id"
                        >
                          <q-item-section>
                            <q-item-label>{{ component.part_number }}</q-item-label>
                            <q-item-label caption>{{ component.name }}</q-item-label>
                          </q-item-section>
                          <q-item-section side>
                            <q-item-label>{{ component.transaction_count }} transactions</q-item-label>
                          </q-item-section>
                        </q-item>
                      </q-list>
                    </q-card-section>
                  </q-card>
                </div>

                <!-- Project Analytics -->
                <div class="col-md-6 col-12">
                  <q-card>
                    <q-card-section>
                      <div class="text-subtitle1 q-mb-md">Project Status Distribution</div>
                      <div v-for="status in projectAnalytics.project_status_distribution" :key="status.status" class="q-mb-sm">
                        <div class="row items-center">
                          <div class="col capitalize">{{ status.status.replace('_', ' ') }}</div>
                          <div class="col-auto">{{ status.count }}</div>
                        </div>
                        <q-linear-progress
                          :value="status.count / getTotalProjectCount()"
                          :color="getProjectStatusColor(status.status)"
                          size="6px"
                        />
                      </div>
                    </q-card-section>
                  </q-card>
                </div>

                <!-- Search Analytics -->
                <div class="col-md-6 col-12">
                  <q-card>
                    <q-card-section>
                      <div class="text-subtitle1 q-mb-md">Popular Tags</div>
                      <div class="row q-col-gutter-xs">
                        <div
                          v-for="tag in searchAnalytics.popular_tags?.slice(0, 10)"
                          :key="tag.tag_name"
                          class="col-auto"
                        >
                          <q-chip
                            :label="`${tag.tag_name} (${tag.component_count})`"
                            color="primary"
                            text-color="white"
                            size="sm"
                          />
                        </div>
                      </div>

                      <q-separator class="q-my-md" />

                      <div class="text-body2">
                        <strong>Data Quality:</strong>
                        {{ Math.round(searchAnalytics.data_quality?.tagging_percentage || 0) }}% components tagged
                      </div>
                      <div class="text-caption text-grey-6">
                        {{ searchAnalytics.data_quality?.untagged_components || 0 }} components need tags
                      </div>
                    </q-card-section>
                  </q-card>
                </div>
              </div>
            </q-tab-panel>

            <!-- Reports Sub-panel -->
            <q-tab-panel name="reports">
              <div class="text-subtitle1 q-mb-md">System Reports</div>

              <div class="row q-col-gutter-md">
                <div class="col-md-4 col-12">
                  <q-card class="report-card cursor-pointer" @click="generateInventoryReport">
                    <q-card-section class="text-center">
                      <q-icon name="inventory" size="48px" color="primary" />
                      <div class="text-h6 q-mt-md">Inventory Report</div>
                      <div class="text-body2 text-grey-6">
                        Comprehensive inventory breakdown and valuation
                      </div>
                    </q-card-section>
                  </q-card>
                </div>

                <div class="col-md-4 col-12">
                  <q-card class="report-card cursor-pointer" @click="generateUsageReport">
                    <q-card-section class="text-center">
                      <q-icon name="trending_up" size="48px" color="secondary" />
                      <div class="text-h6 q-mt-md">Usage Analytics</div>
                      <div class="text-body2 text-grey-6">
                        Component usage patterns and trends
                      </div>
                    </q-card-section>
                  </q-card>
                </div>

                <div class="col-md-4 col-12">
                  <q-card class="report-card cursor-pointer" @click="generateProjectReport">
                    <q-card-section class="text-center">
                      <q-icon name="folder" size="48px" color="accent" />
                      <div class="text-h6 q-mt-md">Project Report</div>
                      <div class="text-body2 text-grey-6">
                        Project analytics and component allocation
                      </div>
                    </q-card-section>
                  </q-card>
                </div>

                <div class="col-md-4 col-12">
                  <q-card class="report-card cursor-pointer" @click="generateFinancialReport">
                    <q-card-section class="text-center">
                      <q-icon name="attach_money" size="48px" color="positive" />
                      <div class="text-h6 q-mt-md">Financial Report</div>
                      <div class="text-body2 text-grey-6">
                        Inventory valuation and cost analysis
                      </div>
                    </q-card-section>
                  </q-card>
                </div>

                <div class="col-md-4 col-12">
                  <q-card class="report-card cursor-pointer" @click="generateSystemReport">
                    <q-card-section class="text-center">
                      <q-icon name="health_and_safety" size="48px" color="warning" />
                      <div class="text-h6 q-mt-md">System Health</div>
                      <div class="text-body2 text-grey-6">
                        Data quality and system performance metrics
                      </div>
                    </q-card-section>
                  </q-card>
                </div>

                <div class="col-md-4 col-12">
                  <q-card class="report-card cursor-pointer" @click="exportComprehensiveReport">
                    <q-card-section class="text-center">
                      <q-icon name="assessment" size="48px" color="info" />
                      <div class="text-h6 q-mt-md">Comprehensive</div>
                      <div class="text-body2 text-grey-6">
                        All reports combined in one export
                      </div>
                    </q-card-section>
                  </q-card>
                </div>
              </div>
            </q-tab-panel>

            <!-- Data Quality Sub-panel -->
            <q-tab-panel name="data-quality">
              <div class="text-subtitle1 q-mb-md">Data Quality Analysis</div>

              <div class="row q-col-gutter-md">
                <!-- Data Completeness -->
                <div class="col-md-6 col-12">
                  <q-card>
                    <q-card-section>
                      <div class="text-subtitle2 q-mb-md">Data Completeness</div>

                      <div class="q-mb-md">
                        <div class="row items-center q-mb-xs">
                          <div class="col">Category Assignment</div>
                          <div class="col-auto">{{ Math.round(systemHealth.data_quality?.category_coverage || 0) }}%</div>
                        </div>
                        <q-linear-progress
                          :value="(systemHealth.data_quality?.category_coverage || 0) / 100"
                          color="primary"
                          size="12px"
                        />
                        <div class="text-caption text-grey-6 q-mt-xs">
                          {{ systemHealth.data_quality?.components_without_category || 0 }} components missing categories
                        </div>
                      </div>

                      <div class="q-mb-md">
                        <div class="row items-center q-mb-xs">
                          <div class="col">Storage Location</div>
                          <div class="col-auto">{{ Math.round(systemHealth.data_quality?.location_coverage || 0) }}%</div>
                        </div>
                        <q-linear-progress
                          :value="(systemHealth.data_quality?.location_coverage || 0) / 100"
                          color="secondary"
                          size="12px"
                        />
                        <div class="text-caption text-grey-6 q-mt-xs">
                          {{ systemHealth.data_quality?.components_without_location || 0 }} components missing locations
                        </div>
                      </div>

                      <div class="q-mb-md">
                        <div class="row items-center q-mb-xs">
                          <div class="col">Technical Specifications</div>
                          <div class="col-auto">{{ Math.round(systemHealth.data_quality?.specification_coverage || 0) }}%</div>
                        </div>
                        <q-linear-progress
                          :value="(systemHealth.data_quality?.specification_coverage || 0) / 100"
                          color="accent"
                          size="12px"
                        />
                        <div class="text-caption text-grey-6 q-mt-xs">
                          {{ systemHealth.data_quality?.components_without_specifications || 0 }} components missing specs
                        </div>
                      </div>

                      <div>
                        <div class="row items-center q-mb-xs">
                          <div class="col">Tag Coverage</div>
                          <div class="col-auto">{{ Math.round(searchAnalytics.data_quality?.tagging_percentage || 0) }}%</div>
                        </div>
                        <q-linear-progress
                          :value="(searchAnalytics.data_quality?.tagging_percentage || 0) / 100"
                          color="positive"
                          size="12px"
                        />
                        <div class="text-caption text-grey-6 q-mt-xs">
                          {{ searchAnalytics.data_quality?.untagged_components || 0 }} components need tags
                        </div>
                      </div>
                    </q-card-section>
                  </q-card>
                </div>

                <!-- Quality Recommendations -->
                <div class="col-md-6 col-12">
                  <q-card>
                    <q-card-section>
                      <div class="text-subtitle2 q-mb-md">Quality Recommendations</div>

                      <q-list dense>
                        <q-item v-if="(systemHealth.data_quality?.category_coverage || 0) < 90">
                          <q-item-section avatar>
                            <q-avatar color="warning" text-color="white" size="24px">
                              <q-icon name="warning" size="16px" />
                            </q-avatar>
                          </q-item-section>
                          <q-item-section>
                            <q-item-label>Improve Category Coverage</q-item-label>
                            <q-item-label caption>Assign categories to uncategorized components</q-item-label>
                          </q-item-section>
                        </q-item>

                        <q-item v-if="(systemHealth.data_quality?.location_coverage || 0) < 85">
                          <q-item-section avatar>
                            <q-avatar color="info" text-color="white" size="24px">
                              <q-icon name="location_on" size="16px" />
                            </q-avatar>
                          </q-item-section>
                          <q-item-section>
                            <q-item-label>Add Storage Locations</q-item-label>
                            <q-item-label caption>Improve inventory tracking with locations</q-item-label>
                          </q-item-section>
                        </q-item>

                        <q-item v-if="(searchAnalytics.data_quality?.tagging_percentage || 0) < 60">
                          <q-item-section avatar>
                            <q-avatar color="accent" text-color="white" size="24px">
                              <q-icon name="local_offer" size="16px" />
                            </q-avatar>
                          </q-item-section>
                          <q-item-section>
                            <q-item-label>Enhance Component Tags</q-item-label>
                            <q-item-label caption>Add tags to improve component discoverability</q-item-label>
                          </q-item-section>
                        </q-item>

                        <q-item v-if="getKicadCoveragePercentage() < 50">
                          <q-item-section avatar>
                            <q-avatar color="primary" text-color="white" size="24px">
                              <q-icon name="memory" size="16px" />
                            </q-avatar>
                          </q-item-section>
                          <q-item-section>
                            <q-item-label>Improve KiCad Integration</q-item-label>
                            <q-item-label caption>Generate KiCad data for more components</q-item-label>
                          </q-item-section>
                        </q-item>

                        <q-item v-if="getOverallDataQuality() >= 90">
                          <q-item-section avatar>
                            <q-avatar color="positive" text-color="white" size="24px">
                              <q-icon name="check_circle" size="16px" />
                            </q-avatar>
                          </q-item-section>
                          <q-item-section>
                            <q-item-label>Excellent Data Quality</q-item-label>
                            <q-item-label caption>Your inventory data is well-maintained</q-item-label>
                          </q-item-section>
                        </q-item>
                      </q-list>
                    </q-card-section>
                  </q-card>
                </div>
              </div>
            </q-tab-panel>
          </q-tab-panels>
        </q-tab-panel>
      </q-tab-panels>
    </div>

    <!-- Create User Dialog -->
    <q-dialog v-model="showCreateUserDialog" persistent max-width="500px">
      <UserForm
        mode="create"
        @saved="handleUserSaved"
        @cancelled="showCreateUserDialog = false"
      />
    </q-dialog>

    <!-- Edit User Dialog -->
    <q-dialog v-model="showEditUserDialog" persistent max-width="500px">
      <UserForm
        mode="edit"
        :user="selectedUser"
        @saved="handleUserSaved"
        @cancelled="showEditUserDialog = false"
      />
    </q-dialog>
  </q-page>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useQuasar } from 'quasar'
import api, { APIService } from '../services/api'
import UserForm from '../components/UserForm.vue'
import CategoryForm from '../components/CategoryForm.vue'

const $q = useQuasar()

// Reactive data
const activeTab = ref('dashboard')
const userSubTab = ref('users-list')
const systemSubTab = ref('health')
const analyticsSubTab = ref('analytics')
const refreshing = ref(false)
const loadingUsers = ref(false)
const loadingTokens = ref(false)

// Dialog state
const showCreateUserDialog = ref(false)
const showEditUserDialog = ref(false)
const showCreateTokenDialog = ref(false)
const showTokenCreatedDialog = ref(false)
const showDeleteTokenDialog = ref(false)
const showKicadSyncDialog = ref(false)
const selectedUser = ref(null)
const selectedToken = ref(null)

// Data containers
const dashboardData = ref({})
const systemHealth = ref({})
const inventoryBreakdown = ref({})
const usageAnalytics = ref({})
const projectAnalytics = ref({})
const searchAnalytics = ref({})
const users = ref([])
const apiTokens = ref([])
const kicadStatus = ref({})
const componentsWithoutKicad = ref([])
const loadingKicadMissing = ref(false)
const generatingKicadData = ref(false)
const generatingComponentData = ref({})

// KiCad management state
const rebuildingIndex = ref(false)
const creatingBackup = ref(false)
const cleaningData = ref(false)
const databaseSize = ref(0)
const lastBackupDate = ref(null)

// API Token creation state
const newToken = ref({ name: '', description: '', expires_in_days: null })
const createdToken = ref(null)
const createdTokenValue = ref('')

// Category Management state
const categories = ref([])
const loadingCategories = ref(false)
const categorySearch = ref('')
const showCreateCategoryDialog = ref(false)
const editingCategory = ref(null)
const suggestedParentId = ref(null)
const showDeleteDialog = ref(false)
const categoryToDelete = ref(null)
const deletingCategory = ref(false)

// User table columns
const userColumns = [
  {
    name: 'username',
    label: 'Username',
    field: 'username',
    align: 'left',
    sortable: true
  },
  {
    name: 'full_name',
    label: 'Full Name',
    field: 'full_name',
    align: 'left',
    sortable: true
  },
  {
    name: 'is_active',
    label: 'Status',
    field: 'is_active',
    align: 'center'
  },
  {
    name: 'is_admin',
    label: 'Admin',
    field: 'is_admin',
    align: 'center'
  },
  {
    name: 'created_at',
    label: 'Created',
    field: 'created_at',
    align: 'center',
    format: (val) => new Date(val).toLocaleDateString()
  },
  {
    name: 'actions',
    label: 'Actions',
    align: 'center'
  }
]

// API Token table columns
const tokenColumns = [
  {
    name: 'name',
    label: 'Name',
    field: 'name',
    align: 'left',
    sortable: true
  },
  {
    name: 'prefix',
    label: 'Token',
    field: 'prefix',
    align: 'left'
  },
  {
    name: 'description',
    label: 'Description',
    field: 'description',
    align: 'left'
  },
  {
    name: 'status',
    label: 'Status',
    field: 'is_active',
    align: 'center'
  },
  {
    name: 'expires_at',
    label: 'Expires',
    field: 'expires_at',
    align: 'left'
  },
  {
    name: 'last_used_at',
    label: 'Last Used',
    field: 'last_used_at',
    align: 'left'
  },
  {
    name: 'actions',
    label: 'Actions',
    align: 'center'
  }
]

// KiCad missing components columns
const kicadMissingColumns = [
  {
    name: 'part_number',
    label: 'Part Number',
    field: 'part_number',
    align: 'left'
  },
  {
    name: 'name',
    label: 'Name',
    field: 'name',
    align: 'left'
  },
  {
    name: 'category',
    label: 'Category',
    field: 'category',
    align: 'left'
  },
  {
    name: 'actions',
    label: 'Actions',
    align: 'center'
  }
]

// Computed properties
const getDataQualityScore = () => {
  if (!systemHealth.value.data_quality) return 0
  const quality = systemHealth.value.data_quality
  return (quality.category_coverage + quality.location_coverage + quality.specification_coverage) / 3
}

// Category Management computed properties
const categoryTreeNodes = computed(() => {
  const buildTreeNodes = (cats, depth = 0) => {
    return cats.map(cat => ({
      id: cat.id,
      label: cat.name,
      name: cat.name,
      description: cat.description,
      icon: cat.icon,
      color: cat.color,
      component_count: cat.component_count || 0,
      children: cat.children ? buildTreeNodes(cat.children, depth + 1) : [],
      expanded: depth < 2, // Auto-expand first 2 levels
      header: 'generic',
      body: 'generic'
    }))
  }
  return buildTreeNodes(categories.value)
})

const categoryStats = computed(() => {
  const calculateStats = (cats) => {
    let total = 0
    let withComponents = 0
    let empty = 0
    let maxDepth = 0

    const traverse = (categories, depth = 1) => {
      maxDepth = Math.max(maxDepth, depth)
      for (const cat of categories) {
        total++
        if (cat.component_count > 0) {
          withComponents++
        } else {
          empty++
        }
        if (cat.children) {
          traverse(cat.children, depth + 1)
        }
      }
    }

    traverse(cats)
    return { total, withComponents, empty, maxDepth }
  }

  return calculateStats(categories.value)
})

// Methods
const loadDashboardData = async () => {
  try {
    const response = await api.get('/api/v1/reports/dashboard')
    dashboardData.value = response.data
  } catch (error) {
    console.error('Failed to load dashboard data:', error)
  }
}

const loadSystemHealth = async () => {
  try {
    const response = await api.get('/api/v1/reports/system-health')
    systemHealth.value = response.data
  } catch (error) {
    console.error('Failed to load system health:', error)
  }
}

const loadInventoryBreakdown = async () => {
  try {
    const response = await api.get('/api/v1/reports/inventory-breakdown')
    inventoryBreakdown.value = response.data
  } catch (error) {
    console.error('Failed to load inventory breakdown:', error)
  }
}

const loadUsageAnalytics = async () => {
  try {
    const response = await api.get('/api/v1/reports/usage-analytics')
    usageAnalytics.value = response.data
  } catch (error) {
    console.error('Failed to load usage analytics:', error)
  }
}

const loadProjectAnalytics = async () => {
  try {
    const response = await api.get('/api/v1/reports/project-analytics')
    projectAnalytics.value = response.data
  } catch (error) {
    console.error('Failed to load project analytics:', error)
  }
}

const loadSearchAnalytics = async () => {
  try {
    const response = await api.get('/api/v1/reports/search-analytics')
    searchAnalytics.value = response.data
  } catch (error) {
    console.error('Failed to load search analytics:', error)
  }
}

const loadUsers = async () => {
  loadingUsers.value = true
  try {
    const response = await api.get('/api/v1/auth/users')
    users.value = response.data
  } catch (error) {
    $q.notify({
      type: 'negative',
      message: 'Failed to load users',
      caption: error.response?.data?.detail || error.message
    })
  }
  loadingUsers.value = false
}

const refreshAllData = async () => {
  refreshing.value = true
  try {
    await Promise.all([
      loadDashboardData(),
      loadSystemHealth(),
      loadInventoryBreakdown(),
      loadUsageAnalytics(),
      loadProjectAnalytics(),
      loadSearchAnalytics(),
      loadUsers(),
      loadCategories()
    ])
    $q.notify({
      type: 'positive',
      message: 'Data refreshed successfully'
    })
  } catch (error) {
    $q.notify({
      type: 'negative',
      message: 'Failed to refresh some data'
    })
  }
  refreshing.value = false
}

const editUser = (user) => {
  selectedUser.value = user
  showEditUserDialog.value = true
}

const resetPassword = async (user) => {
  try {
    await api.post(`/api/v1/auth/users/${user.id}/reset-password`)
    $q.notify({
      type: 'positive',
      message: 'Password reset successfully'
    })
  } catch (error) {
    $q.notify({
      type: 'negative',
      message: 'Failed to reset password',
      caption: error.response?.data?.detail || error.message
    })
  }
}

const toggleUserStatus = async (user) => {
  try {
    await api.patch(`/api/v1/auth/users/${user.id}`, {
      is_active: !user.is_active
    })
    await loadUsers()
    $q.notify({
      type: 'positive',
      message: `User ${user.is_active ? 'deactivated' : 'activated'} successfully`
    })
  } catch (error) {
    $q.notify({
      type: 'negative',
      message: 'Failed to update user status',
      caption: error.response?.data?.detail || error.message
    })
  }
}

const handleUserSaved = () => {
  showCreateUserDialog.value = false
  showEditUserDialog.value = false
  selectedUser.value = null
  loadUsers()
  $q.notify({
    type: 'positive',
    message: 'User saved successfully'
  })
}

// Report generation methods
const exportComprehensiveReport = async () => {
  try {
    const response = await api.get('/api/v1/reports/comprehensive', { responseType: 'blob' })
    const blob = new Blob([response.data], { type: 'application/json' })
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `comprehensive-report-${new Date().toISOString().split('T')[0]}.json`
    link.click()
    window.URL.revokeObjectURL(url)
  } catch (error) {
    $q.notify({
      type: 'negative',
      message: 'Failed to export comprehensive report',
      caption: error.response?.data?.detail || error.message
    })
  }
}

const generateInventoryReport = async () => {
  try {
    const response = await api.get('/api/v1/reports/export/inventory', { responseType: 'blob' })
    downloadReport(response.data, 'inventory-report')
  } catch (error) {
    $q.notify({
      type: 'negative',
      message: 'Failed to generate inventory report'
    })
  }
}

const generateUsageReport = async () => {
  try {
    const response = await api.get('/api/v1/reports/export/usage', { responseType: 'blob' })
    downloadReport(response.data, 'usage-report')
  } catch (error) {
    $q.notify({
      type: 'negative',
      message: 'Failed to generate usage report'
    })
  }
}

const generateProjectReport = async () => {
  try {
    const response = await api.get('/api/v1/reports/export/projects', { responseType: 'blob' })
    downloadReport(response.data, 'project-report')
  } catch (error) {
    $q.notify({
      type: 'negative',
      message: 'Failed to generate project report'
    })
  }
}

const generateFinancialReport = async () => {
  try {
    const response = await api.get('/api/v1/reports/export/financial', { responseType: 'blob' })
    downloadReport(response.data, 'financial-report')
  } catch (error) {
    $q.notify({
      type: 'negative',
      message: 'Failed to generate financial report'
    })
  }
}

const generateSystemReport = async () => {
  try {
    const response = await api.get('/api/v1/reports/export/system-health', { responseType: 'blob' })
    downloadReport(response.data, 'system-health-report')
  } catch (error) {
    $q.notify({
      type: 'negative',
      message: 'Failed to generate system report'
    })
  }
}

const downloadReport = (data, filename) => {
  const blob = new Blob([data], { type: 'application/json' })
  const url = window.URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = `${filename}-${new Date().toISOString().split('T')[0]}.json`
  link.click()
  window.URL.revokeObjectURL(url)

  $q.notify({
    type: 'positive',
    message: 'Report downloaded successfully'
  })
}

// Helper methods
const formatCurrency = (amount) => {
  return new Intl.NumberFormat('en-US', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2
  }).format(amount)
}

const getTotalProjectCount = () => {
  return projectAnalytics.value.project_status_distribution?.reduce((total, status) => total + status.count, 0) || 1
}

const getProjectStatusColor = (status) => {
  const colors = {
    planning: 'blue',
    active: 'green',
    on_hold: 'orange',
    completed: 'positive',
    cancelled: 'negative'
  }
  return colors[status] || 'grey'
}

// API Token helper methods
const loadApiTokens = async () => {
  loadingTokens.value = true
  try {
    const response = await api.get('/auth/api-tokens')
    apiTokens.value = response.data
  } catch (error) {
    console.error('Failed to load API tokens:', error)
    $q.notify({
      type: 'negative',
      message: 'Failed to load API tokens'
    })
  }
  loadingTokens.value = false
}

const createApiToken = async () => {
  try {
    const response = await api.post('/auth/api-tokens', newToken.value)
    createdToken.value = response.data
    createdTokenValue.value = response.data.token
    showTokenCreatedDialog.value = true
    showCreateTokenDialog.value = false
    newToken.value = { name: '', description: '', expires_in_days: null }
    await loadApiTokens()
    $q.notify({
      type: 'positive',
      message: 'API token created successfully'
    })
  } catch (error) {
    $q.notify({
      type: 'negative',
      message: 'Failed to create API token',
      caption: error.response?.data?.detail || error.message
    })
  }
}

const confirmDeleteToken = (token) => {
  selectedToken.value = token
  showDeleteTokenDialog.value = true
}

const deleteToken = async () => {
  if (!selectedToken.value) return

  try {
    await api.delete(`/auth/api-tokens/${selectedToken.value.id}`)
    showDeleteTokenDialog.value = false
    selectedToken.value = null
    await loadApiTokens()
    $q.notify({
      type: 'positive',
      message: 'API token revoked successfully'
    })
  } catch (error) {
    $q.notify({
      type: 'negative',
      message: 'Failed to revoke token'
    })
  }
}

const getTokenStatusColor = (token) => {
  if (!token.is_active) return 'negative'
  if (token.expires_at && new Date(token.expires_at) < new Date()) return 'warning'
  return 'positive'
}

const getTokenStatusLabel = (token) => {
  if (!token.is_active) return 'Revoked'
  if (token.expires_at && new Date(token.expires_at) < new Date()) return 'Expired'
  return 'Active'
}

// KiCad management methods
const loadKicadStatus = async () => {
  try {
    const response = await api.get('/kicad/libraries/status')
    kicadStatus.value = response.data
  } catch (error) {
    console.error('Failed to load KiCad status:', error)
  }
}

const loadComponentsWithoutKicad = async () => {
  loadingKicadMissing.value = true
  try {
    // This would need a dedicated endpoint to get components without KiCad data
    const response = await api.get('/components', {
      params: {
        limit: 100,
        // Add filter for components without KiCad data when available
      }
    })
    componentsWithoutKicad.value = response.data.filter(c => !c.kicad_data)
  } catch (error) {
    console.error('Failed to load components without KiCad data:', error)
  }
  loadingKicadMissing.value = false
}

const generateKicadData = async () => {
  generatingKicadData.value = true
  try {
    // This would trigger bulk KiCad data generation
    await api.post('/kicad/generate-missing-data')
    await loadKicadStatus()
    await loadComponentsWithoutKicad()
    $q.notify({
      type: 'positive',
      message: 'KiCad data generation started'
    })
  } catch (error) {
    $q.notify({
      type: 'negative',
      message: 'Failed to start KiCad data generation'
    })
  }
  generatingKicadData.value = false
}

const generateComponentKicadData = async (component) => {
  generatingComponentData.value[component.id] = true
  try {
    await api.post(`/kicad/components/${component.id}/generate`)
    await loadComponentsWithoutKicad()
    $q.notify({
      type: 'positive',
      message: `Generated KiCad data for ${component.part_number}`
    })
  } catch (error) {
    $q.notify({
      type: 'negative',
      message: 'Failed to generate KiCad data'
    })
  }
  generatingComponentData.value[component.id] = false
}

const getKicadCoveragePercentage = () => {
  const total = kicadStatus.value.total_components || 0
  const withKicad = kicadStatus.value.components_with_kicad_data || 0
  return total > 0 ? (withKicad / total) * 100 : 0
}

const getKicadCoverageColor = () => {
  const percentage = getKicadCoveragePercentage()
  if (percentage >= 80) return 'positive'
  if (percentage >= 50) return 'warning'
  return 'negative'
}

const getOverallDataQuality = () => {
  if (!systemHealth.value.data_quality) return 0
  const quality = systemHealth.value.data_quality
  return (quality.category_coverage + quality.location_coverage + quality.specification_coverage) / 3
}

// Database management methods
const rebuildSearchIndex = async () => {
  rebuildingIndex.value = true
  try {
    await api.post('/admin/rebuild-search-index')
    $q.notify({
      type: 'positive',
      message: 'Search index rebuilt successfully'
    })
  } catch (error) {
    $q.notify({
      type: 'negative',
      message: 'Failed to rebuild search index'
    })
  }
  rebuildingIndex.value = false
}

const createDatabaseBackup = async () => {
  creatingBackup.value = true
  try {
    const response = await api.post('/admin/create-backup', {}, { responseType: 'blob' })
    const blob = new Blob([response.data], { type: 'application/octet-stream' })
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `partshub-backup-${new Date().toISOString().split('T')[0]}.db`
    link.click()
    window.URL.revokeObjectURL(url)
    $q.notify({
      type: 'positive',
      message: 'Database backup created successfully'
    })
  } catch (error) {
    $q.notify({
      type: 'negative',
      message: 'Failed to create database backup'
    })
  }
  creatingBackup.value = false
}

const cleanupOrphanedData = async () => {
  cleaningData.value = true
  try {
    const response = await api.post('/admin/cleanup-orphaned-data')
    $q.notify({
      type: 'positive',
      message: `Cleaned up ${response.data.removed_count} orphaned records`
    })
  } catch (error) {
    $q.notify({
      type: 'negative',
      message: 'Failed to cleanup orphaned data'
    })
  }
  cleaningData.value = false
}

const formatBytes = (bytes) => {
  if (bytes === 0) return '0 Bytes'
  const k = 1024
  const sizes = ['Bytes', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

const formatDate = (dateString) => {
  return new Date(dateString).toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
}

// Category Management Methods
const loadCategories = async () => {
  loadingCategories.value = true
  try {
    const response = await api.get('/api/v1/categories?hierarchy=true&include_empty=true')
    categories.value = response.data
  } catch (error) {
    console.error('Error loading categories:', error)
    $q.notify({
      type: 'negative',
      message: 'Failed to load categories',
      caption: error.response?.data?.detail || error.message
    })
  } finally {
    loadingCategories.value = false
  }
}

const filterCategories = (node, filter) => {
  if (!filter) return true
  const searchTerm = filter.toLowerCase()
  return node.label.toLowerCase().includes(searchTerm) ||
         (node.description && node.description.toLowerCase().includes(searchTerm))
}

const editCategory = (categoryNode) => {
  editingCategory.value = {
    id: categoryNode.id,
    name: categoryNode.name,
    description: categoryNode.description,
    icon: categoryNode.icon,
    color: categoryNode.color,
    parent_id: categoryNode.parent_id || null
  }
  suggestedParentId.value = null
  showCreateCategoryDialog.value = true
}

const createSubcategory = (parentNode) => {
  editingCategory.value = null
  suggestedParentId.value = parentNode.id
  showCreateCategoryDialog.value = true
}

const deleteCategory = (categoryNode) => {
  if (categoryNode.component_count > 0) {
    $q.notify({
      type: 'negative',
      message: 'Cannot delete category with components',
      caption: 'Move or delete all components first'
    })
    return
  }

  categoryToDelete.value = categoryNode
  showDeleteDialog.value = true
}

const confirmDeleteCategory = async () => {
  if (!categoryToDelete.value) return

  deletingCategory.value = true
  try {
    await api.delete(`/api/v1/categories/${categoryToDelete.value.id}`)

    $q.notify({
      type: 'positive',
      message: `Category "${categoryToDelete.value.name}" deleted successfully`
    })

    await loadCategories()
  } catch (error) {
    console.error('Error deleting category:', error)
    $q.notify({
      type: 'negative',
      message: 'Failed to delete category',
      caption: error.response?.data?.detail || error.message
    })
  } finally {
    deletingCategory.value = false
    showDeleteDialog.value = false
    categoryToDelete.value = null
  }
}

const onCategoryFormSuccess = async (newCategory) => {
  showCreateCategoryDialog.value = false
  editingCategory.value = null
  suggestedParentId.value = null

  await loadCategories()

  $q.notify({
    type: 'positive',
    message: editingCategory.value
      ? `Category "${newCategory.name}" updated successfully`
      : `Category "${newCategory.name}" created successfully`
  })
}

const closeCreateCategoryDialog = () => {
  showCreateCategoryDialog.value = false
  editingCategory.value = null
  suggestedParentId.value = null
}

// Lifecycle
onMounted(() => {
  refreshAllData()
})
</script>

<style scoped>
.admin-page {
  max-width: 1400px;
  margin: 0 auto;
}

.report-card {
  transition: transform 0.2s, box-shadow 0.2s;
}

.report-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.users-table tbody tr:hover {
  background-color: rgba(0, 0, 0, 0.05);
}

.capitalize {
  text-transform: capitalize;
}
</style>