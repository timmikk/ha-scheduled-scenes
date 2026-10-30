import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import ScrubSimulator from './ScrubSimulator.vue'
import type { MockLight } from '../types'

describe('ScrubSimulator.vue', () => {
  const sampleLights: MockLight[] = [
    {
      entity_id: 'light.test_fixture',
      name: 'Test Light',
      area_id: 'living_room',
      area_name: 'Living Room',
      state: 'on',
      supported_color_modes: ['color_temp'],
      min_color_temp_kelvin: 2000,
      max_color_temp_kelvin: 6500,
    },
  ]

  const defaultProps = {
    modelValue: 480, // 08:00
    roomBrightness: 100,
    roomScheduleTemp: 4000,
    lightIds: ['light.test_fixture'],
    mockLights: sampleLights,
    brightnessCurves: {},
    dimToWarmCurves: {},
    liveMode: 'off' as const,
  }

  it('renders time of day formatted correctly', () => {
    const wrapper = mount(ScrubSimulator, { props: defaultProps })
    expect(wrapper.text()).toContain('08:00')
    expect(wrapper.text()).toContain('Real-Time Scrubbing')
  })

  it('emits update:modelValue when time slider is scrubbed', async () => {
    const wrapper = mount(ScrubSimulator, { props: defaultProps })
    const timeSlider = wrapper.findAll('input[type="range"]')[0]
    await timeSlider.setValue(720) // 12:00

    expect(wrapper.emitted('update:modelValue')).toBeTruthy()
    expect(wrapper.emitted('update:modelValue')![0]).toEqual([720])
  })

  it('emits update:roomBrightness when brightness slider is moved', async () => {
    const wrapper = mount(ScrubSimulator, { props: defaultProps })
    const briSlider = wrapper.findAll('input[type="range"]')[1]
    await briSlider.setValue(50)

    expect(wrapper.emitted('update:roomBrightness')).toBeTruthy()
    expect(wrapper.emitted('update:roomBrightness')![0]).toEqual([50])
  })

  it('emits toggleLiveRoom when Live Room button is clicked', async () => {
    const wrapper = mount(ScrubSimulator, { props: defaultProps })
    const buttons = wrapper.findAll('button')
    const liveBtn = buttons.find((b) => b.text().includes('Live Mode: Timeline'))
    expect(liveBtn).toBeDefined()
    await liveBtn!.trigger('click')

    expect(wrapper.emitted('toggleLiveRoom')).toBeTruthy()
  })
})
