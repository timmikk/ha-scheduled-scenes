import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import CircadianTimeline from './CircadianTimeline.vue'
import type { ScheduleStep } from '../types'

describe('CircadianTimeline.vue', () => {
  const initialSteps: ScheduleStep[] = [
    { id: 's1', time: '06:00', brightness: 20, temp: 2400 },
    { id: 's2', time: '12:00', brightness: 100, temp: 4500 },
    { id: 's3', time: '22:00', brightness: 10, temp: 2000 },
  ]

  beforeEach(() => {
    vi.restoreAllMocks()
  })

  it('renders Copy YAML and Import YAML buttons', () => {
    const wrapper = mount(CircadianTimeline, {
      props: {
        steps: initialSteps,
        scrubMinutes: 720,
      },
    })

    const buttons = wrapper.findAll('button')
    const copyBtn = buttons.find((b) => b.text().includes('Copy YAML'))
    const importBtn = buttons.find((b) => b.text().includes('Import YAML'))

    expect(copyBtn?.exists()).toBe(true)
    expect(importBtn?.exists()).toBe(true)
  })

  it('copies schedule YAML to clipboard on copy click', async () => {
    const writeTextMock = vi.fn().mockResolvedValue(undefined)
    Object.defineProperty(navigator, 'clipboard', {
      value: { writeText: writeTextMock },
      writable: true,
      configurable: true,
    })

    const wrapper = mount(CircadianTimeline, {
      props: {
        steps: initialSteps,
        scrubMinutes: 720,
      },
    })

    const copyBtn = wrapper.findAll('button').find((b) => b.text().includes('Copy YAML'))
    expect(copyBtn).toBeDefined()
    await copyBtn!.trigger('click')

    expect(writeTextMock).toHaveBeenCalledTimes(1)
    const written = writeTextMock.mock.calls[0][0]
    expect(written).toContain('schedule:')
    expect(written).toContain('06:00')
    expect(written).toContain('brightness: 20')
  })

  it('opens import modal and handles validation & applying schedule', async () => {
    const wrapper = mount(CircadianTimeline, {
      props: {
        steps: initialSteps,
        scrubMinutes: 720,
      },
    })

    // Initially modal not open
    expect(wrapper.find('textarea').exists()).toBe(false)

    // Open modal
    const importBtn = wrapper.findAll('button').find((b) => b.text().includes('Import YAML'))
    await importBtn!.trigger('click')
    expect(wrapper.find('textarea').exists()).toBe(true)

    // Paste invalid YAML
    const textarea = wrapper.find('textarea')
    await textarea.setValue('schedule: - invalid: [')
    await textarea.trigger('input')

    // Expect error banner
    expect(wrapper.text()).toContain('Invalid YAML syntax')

    // Paste valid schedule YAML
    const validYaml = `
schedule:
  - time: "07:00"
    brightness: 30
    temp: 2700
  - time: "19:00"
    brightness: 70
    temp: 3200
`
    await textarea.setValue(validYaml)
    await textarea.trigger('input')

    // Error gone, preview shown
    expect(wrapper.text()).toContain('Ready to import 2 checkpoints')

    // Click Apply to Room
    const applyBtn = wrapper.findAll('button').find((b) => b.text().includes('Apply to Room'))
    expect(applyBtn?.attributes('disabled')).toBeUndefined()
    await applyBtn!.trigger('click')

    // update:steps emitted
    const emitted = wrapper.emitted('update:steps')
    expect(emitted).toBeDefined()
    expect(emitted![0][0]).toHaveLength(2)
    expect((emitted![0][0] as ScheduleStep[])[0].time).toBe('07:00')
    expect((emitted![0][0] as ScheduleStep[])[1].brightness).toBe(70)

    // Modal closed
    expect(wrapper.find('textarea').exists()).toBe(false)
  })
})
