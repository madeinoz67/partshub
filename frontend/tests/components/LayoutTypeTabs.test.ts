import { mount, VueWrapper } from '@vue/test-utils'
import { describe, it, expect, beforeEach } from 'vitest'
import LayoutTypeTabs from '../../src/components/storage/LayoutTypeTabs.vue'

describe('LayoutTypeTabs', () => {
  let wrapper: VueWrapper<any>

  beforeEach(() => {
    wrapper = mount(LayoutTypeTabs, {
      props: {
        modelValue: 'single'
      }
    })
  })

  describe('Tab Rendering', () => {
    it('should render all four layout type tabs', () => {
      const tabs = wrapper.findAll('[data-testid^="tab-"]')
      expect(tabs).toHaveLength(4)
    })

    it('should render Single tab', () => {
      const singleTab = wrapper.find('[data-testid="tab-single"]')
      expect(singleTab.exists()).toBe(true)
      expect(singleTab.text()).toContain('Single')
    })

    it('should render Row tab', () => {
      const rowTab = wrapper.find('[data-testid="tab-row"]')
      expect(rowTab.exists()).toBe(true)
      expect(rowTab.text()).toContain('Row')
    })

    it('should render Grid tab', () => {
      const gridTab = wrapper.find('[data-testid="tab-grid"]')
      expect(gridTab.exists()).toBe(true)
      expect(gridTab.text()).toContain('Grid')
    })

    it('should render 3D Grid tab', () => {
      const grid3dTab = wrapper.find('[data-testid="tab-grid_3d"]')
      expect(grid3dTab.exists()).toBe(true)
      expect(grid3dTab.text()).toContain('3D')
    })
  })

  describe('Tab Icons', () => {
    it('should display icon for Single tab', () => {
      const singleTab = wrapper.find('[data-testid="tab-single"]')
      const icon = singleTab.find('i')
      expect(icon.exists()).toBe(true)
    })

    it('should display icon for Row tab', () => {
      const rowTab = wrapper.find('[data-testid="tab-row"]')
      const icon = rowTab.find('i')
      expect(icon.exists()).toBe(true)
    })

    it('should display icon for Grid tab', () => {
      const gridTab = wrapper.find('[data-testid="tab-grid"]')
      const icon = gridTab.find('i')
      expect(icon.exists()).toBe(true)
    })

    it('should display icon for 3D Grid tab', () => {
      const grid3dTab = wrapper.find('[data-testid="tab-grid_3d"]')
      const icon = grid3dTab.find('i')
      expect(icon.exists()).toBe(true)
    })
  })

  describe('Active State', () => {
    it('should mark Single tab as active when modelValue is "single"', async () => {
      await wrapper.setProps({ modelValue: 'single' })

      const singleTab = wrapper.find('[data-testid="tab-single"]')
      expect(singleTab.classes()).toContain('active')
    })

    it('should mark Row tab as active when modelValue is "row"', async () => {
      await wrapper.setProps({ modelValue: 'row' })

      const rowTab = wrapper.find('[data-testid="tab-row"]')
      expect(rowTab.classes()).toContain('active')
    })

    it('should mark Grid tab as active when modelValue is "grid"', async () => {
      await wrapper.setProps({ modelValue: 'grid' })

      const gridTab = wrapper.find('[data-testid="tab-grid"]')
      expect(gridTab.classes()).toContain('active')
    })

    it('should mark 3D Grid tab as active when modelValue is "grid_3d"', async () => {
      await wrapper.setProps({ modelValue: 'grid_3d' })

      const grid3dTab = wrapper.find('[data-testid="tab-grid_3d"]')
      expect(grid3dTab.classes()).toContain('active')
    })

    it('should only have one active tab at a time', async () => {
      await wrapper.setProps({ modelValue: 'row' })

      const activeTabs = wrapper.findAll('.active')
      expect(activeTabs).toHaveLength(1)
      expect(activeTabs[0].attributes('data-testid')).toBe('tab-row')
    })
  })

  describe('Tab Selection', () => {
    it('should emit update:modelValue when Single tab is clicked', async () => {
      await wrapper.setProps({ modelValue: 'row' })

      const singleTab = wrapper.find('[data-testid="tab-single"]')
      await singleTab.trigger('click')

      expect(wrapper.emitted('update:modelValue')).toBeTruthy()
      expect(wrapper.emitted('update:modelValue')![0]).toEqual(['single'])
    })

    it('should emit update:modelValue when Row tab is clicked', async () => {
      const rowTab = wrapper.find('[data-testid="tab-row"]')
      await rowTab.trigger('click')

      expect(wrapper.emitted('update:modelValue')).toBeTruthy()
      expect(wrapper.emitted('update:modelValue')![0]).toEqual(['row'])
    })

    it('should emit update:modelValue when Grid tab is clicked', async () => {
      const gridTab = wrapper.find('[data-testid="tab-grid"]')
      await gridTab.trigger('click')

      expect(wrapper.emitted('update:modelValue')).toBeTruthy()
      expect(wrapper.emitted('update:modelValue')![0]).toEqual(['grid'])
    })

    it('should emit update:modelValue when 3D Grid tab is clicked', async () => {
      const grid3dTab = wrapper.find('[data-testid="tab-grid_3d"]')
      await grid3dTab.trigger('click')

      expect(wrapper.emitted('update:modelValue')).toBeTruthy()
      expect(wrapper.emitted('update:modelValue')![0]).toEqual(['grid_3d'])
    })
  })

  describe('Tab Descriptions', () => {
    it('should show description for Single layout', () => {
      const singleTab = wrapper.find('[data-testid="tab-single"]')
      const description = singleTab.find('.tab-description')
      expect(description.exists()).toBe(true)
      expect(description.text()).toContain('single location')
    })

    it('should show description for Row layout', () => {
      const rowTab = wrapper.find('[data-testid="tab-row"]')
      const description = rowTab.find('.tab-description')
      expect(description.exists()).toBe(true)
      expect(description.text()).toContain('1D')
    })

    it('should show description for Grid layout', () => {
      const gridTab = wrapper.find('[data-testid="tab-grid"]')
      const description = gridTab.find('.tab-description')
      expect(description.exists()).toBe(true)
      expect(description.text()).toContain('2D')
    })

    it('should show description for 3D Grid layout', () => {
      const grid3dTab = wrapper.find('[data-testid="tab-grid_3d"]')
      const description = grid3dTab.find('.tab-description')
      expect(description.exists()).toBe(true)
      expect(description.text()).toContain('3D')
    })
  })

  describe('Accessibility', () => {
    it('should have role="tablist" on container', () => {
      const container = wrapper.find('[data-testid="layout-type-tabs"]')
      expect(container.attributes('role')).toBe('tablist')
    })

    it('should have role="tab" on each tab', () => {
      const tabs = wrapper.findAll('[data-testid^="tab-"]')
      tabs.forEach(tab => {
        expect(tab.attributes('role')).toBe('tab')
      })
    })

    it('should have aria-selected="true" on active tab', async () => {
      await wrapper.setProps({ modelValue: 'row' })

      const rowTab = wrapper.find('[data-testid="tab-row"]')
      expect(rowTab.attributes('aria-selected')).toBe('true')
    })

    it('should have aria-selected="false" on inactive tabs', async () => {
      await wrapper.setProps({ modelValue: 'row' })

      const singleTab = wrapper.find('[data-testid="tab-single"]')
      const gridTab = wrapper.find('[data-testid="tab-grid"]')

      expect(singleTab.attributes('aria-selected')).toBe('false')
      expect(gridTab.attributes('aria-selected')).toBe('false')
    })
  })
})
