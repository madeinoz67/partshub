<template>
  <div
    data-testid="layout-type-tabs"
    role="tablist"
    class="layout-type-tabs"
  >
    <q-tabs
      v-model="selectedTab"
      dense
      class="text-grey"
      active-color="primary"
      indicator-color="primary"
      align="justify"
      @update:model-value="onTabChange"
    >
      <q-tab
        data-testid="tab-single"
        name="single"
        :class="{ active: selectedTab === 'single' }"
        :aria-selected="selectedTab === 'single' ? 'true' : 'false'"
        role="tab"
      >
        <div class="column items-center">
          <q-icon name="place" size="sm" class="q-mb-xs" />
          <div class="text-caption">Single</div>
          <div class="tab-description text-caption text-grey-6">
            Create a single location
          </div>
        </div>
      </q-tab>

      <q-tab
        data-testid="tab-row"
        name="row"
        :class="{ active: selectedTab === 'row' }"
        :aria-selected="selectedTab === 'row' ? 'true' : 'false'"
        role="tab"
      >
        <div class="column items-center">
          <q-icon name="view_week" size="sm" class="q-mb-xs" />
          <div class="text-caption">Row</div>
          <div class="tab-description text-caption text-grey-6">
            1D sequence
          </div>
        </div>
      </q-tab>

      <q-tab
        data-testid="tab-grid"
        name="grid"
        :class="{ active: selectedTab === 'grid' }"
        :aria-selected="selectedTab === 'grid' ? 'true' : 'false'"
        role="tab"
      >
        <div class="column items-center">
          <q-icon name="grid_on" size="sm" class="q-mb-xs" />
          <div class="text-caption">Grid</div>
          <div class="tab-description text-caption text-grey-6">
            2D grid layout
          </div>
        </div>
      </q-tab>

      <q-tab
        data-testid="tab-grid_3d"
        name="grid_3d"
        :class="{ active: selectedTab === 'grid_3d' }"
        :aria-selected="selectedTab === 'grid_3d' ? 'true' : 'false'"
        role="tab"
      >
        <div class="column items-center">
          <q-icon name="view_in_ar" size="sm" class="q-mb-xs" />
          <div class="text-caption">3D Grid</div>
          <div class="tab-description text-caption text-grey-6">
            3D grid layout
          </div>
        </div>
      </q-tab>
    </q-tabs>
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'

interface Props {
  modelValue: 'single' | 'row' | 'grid' | 'grid_3d'
}

const props = withDefaults(defineProps<Props>(), {
  modelValue: 'single'
})

const emit = defineEmits<{
  'update:modelValue': [value: 'single' | 'row' | 'grid' | 'grid_3d']
}>()

const selectedTab = ref(props.modelValue)

watch(() => props.modelValue, (newValue) => {
  selectedTab.value = newValue
})

const onTabChange = (value: string) => {
  emit('update:modelValue', value as 'single' | 'row' | 'grid' | 'grid_3d')
}
</script>

<style scoped lang="scss">
.layout-type-tabs {
  width: 100%;

  .tab-description {
    font-size: 0.65rem;
    line-height: 1.2;
    margin-top: 2px;
  }

  .active {
    // Additional styling for active tab if needed
  }
}
</style>
