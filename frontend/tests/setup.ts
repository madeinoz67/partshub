import { config } from '@vue/test-utils'
import { createPinia } from 'pinia'
import { Quasar } from 'quasar'
import { h } from 'vue'

// Create a global Pinia instance for tests
const pinia = createPinia()

// Global mount options
config.global.plugins = [pinia, [Quasar, {}]]
config.global.stubs = {
  'q-card': { template: '<div class="q-card"><slot /></div>' },
  'q-card-section': { template: '<div class="q-card-section"><slot /></div>' },
  'q-card-actions': { template: '<div class="q-card-actions"><slot /></div>' },
  'q-btn': { template: '<button><slot /></button>' },
  'q-btn-group': { template: '<div><slot /></div>' },
  'q-tabs': { template: '<div class="q-tabs"><slot /></div>', props: ['modelValue'] },
  'q-tab': { template: '<div class="q-tab"><slot /></div>', props: ['name'] },
  'q-tab-panels': { template: '<div class="q-tab-panels"><slot /></div>', props: ['modelValue'] },
  'q-tab-panel': { template: '<div class="q-tab-panel"><slot /></div>', props: ['name'] },
  'q-dialog': { template: '<div class="q-dialog"><slot /></div>', props: ['modelValue'] },
  'q-input': { template: '<input class="q-input" />', props: ['modelValue', 'label'] },
  'q-select': { template: '<select class="q-select"><slot /></select>', props: ['modelValue', 'options'] },
  'q-checkbox': { template: '<input type="checkbox" class="q-checkbox" />', props: ['modelValue', 'label'] },
  'q-separator': { template: '<hr class="q-separator" />' },
  'q-space': { template: '<div class="q-space"></div>' },
  'q-list': { template: '<ul class="q-list"><slot /></ul>' },
  'q-item': { template: '<li class="q-item"><slot /></li>' },
  'q-item-section': { template: '<div class="q-item-section"><slot /></div>' },
  'q-item-label': { template: '<div class="q-item-label"><slot /></div>' },
  'q-inner-loading': { template: '<div></div>' },
  'q-banner': { template: '<div class="q-banner"><slot name="avatar" /><slot /></div>' },
  'q-chip': { template: '<span class="q-chip"><slot /></span>' },
  'q-badge': { template: '<span class="q-badge"><slot /></span>' },
  'q-icon': { template: '<i class="q-icon"><slot /></i>', props: ['name', 'color'] },
  'q-table': {
    props: ['rows', 'columns', 'flat', 'bordered', 'dense', 'hideBottom', 'hidePagination', 'rowsPerPageOptions'],
    setup(props: any, { slots }: any) {
      return () => h('table', {}, [
        h('thead', {}, [
          slots.header?.() || h('tr', {}, props.columns?.map((col: any) =>
            h('th', { key: col.name }, col.label)
          ))
        ]),
        h('tbody', {},
          slots.body ? props.rows?.map((row: any, rowIndex: number) =>
            slots.body({
              row,
              rowIndex,
              cols: props.columns,
              col: props.columns
            })
          ) : props.rows?.map((row: any, i: number) =>
            h('tr', { key: i }, props.columns?.map((col: any) =>
              h('td', { key: col.name }, row[col.field])
            ))
          )
        )
      ])
    }
  },
  'q-tr': { template: '<tr><slot /></tr>', props: ['props'] },
  'q-td': { template: '<td><slot /></td>', props: ['props'] },
  'q-spinner': { template: '<div class="q-spinner"></div>', props: ['color', 'size'] },
  'q-avatar': { template: '<div class="q-avatar"><slot /></div>' }
}