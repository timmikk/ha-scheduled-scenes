import { describe, it, expect, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import YamlViewer from './YamlViewer.vue'
import type { ScheduledScenesConfig } from '../types'

describe('YamlViewer.vue', () => {
  const sampleConfig: ScheduledScenesConfig = {
    curves: {
      warm_glow: {
        name: 'warm_glow',
        lights: ['light.spot_1'],
        points: [[1, 2200], [100, 4000]],
      },
    },
    brightness_curves: {},
    programs: [
      {
        name: 'living_room',
        lights: ['light.spot_1'],
        transition_time: 120,
        transition_interval: 120,
        schedule: [{ id: '1', time: '08:00', brightness: 100, temp: 4000 }],
      },
    ],
  }

  it('renders YAML output for given configuration', () => {
    const wrapper = mount(YamlViewer, {
      props: { config: sampleConfig },
    })

    const text = wrapper.text()
    expect(text).toContain('Home Assistant YAML Configuration')
    expect(text).toContain('living_room')
    expect(text).toContain('warm_glow')
  })

  it('opens import modal when Import YAML is clicked', async () => {
    const wrapper = mount(YamlViewer, {
      props: { config: sampleConfig },
    })

    expect(wrapper.find('textarea').exists()).toBe(false)
    const importBtn = wrapper.findAll('button').find((b) => b.text().includes('Import YAML'))
    expect(importBtn).toBeDefined()
    await importBtn!.trigger('click')

    expect(wrapper.find('textarea').exists()).toBe(true)
  })

  it('handles clipboard copy button', async () => {
    const writeTextMock = vi.fn().mockResolvedValue(undefined)
    Object.defineProperty(navigator, 'clipboard', {
      value: { writeText: writeTextMock },
      writable: true,
      configurable: true,
    })

    const wrapper = mount(YamlViewer, {
      props: { config: sampleConfig },
    })

    const copyBtn = wrapper.findAll('button').find((b) => b.text().includes('Copy YAML'))
    expect(copyBtn).toBeDefined()
    await copyBtn!.trigger('click')

    expect(writeTextMock).toHaveBeenCalled()
  })
})
