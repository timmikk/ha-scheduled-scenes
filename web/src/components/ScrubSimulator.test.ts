import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import ScrubSimulator from './ScrubSimulator.vue'
import type { MockLight } from '../types'
import { calculateFixtureOutput, interpolateSchedule, resolveDynamicSchedule } from '../utils/interpolator'
import type { ScheduleStep } from '../types'

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

  it('emits seasonal date changes from the date picker and presets', async () => {
    const wrapper = mount(ScrubSimulator, { props: { ...defaultProps, seasonDate: '2024-01-01' } })
    await wrapper.find('#season-date').setValue('2024-06-21')
    expect(wrapper.emitted('update:seasonDate')?.[0]).toEqual(['2024-06-21'])
    const winter = wrapper.findAll('button').find(button => button.text() === 'Winter Solstice')
    await winter?.trigger('click')
    expect(wrapper.emitted('update:seasonDate')?.[1]).toEqual(['2024-12-21'])
  })

  it('recalculates fixture preview output for seasonal dynamic points', () => {
    const steps: ScheduleStep[] = [
      { id: 'night', time: '00:00', brightness: 0 },
      { id: 'sunrise', time: '06:00', brightness: 100, dynamic: { type: 'sun', event: 'sunrise' } },
      { id: 'day', time: '12:00', brightness: 100 },
      { id: 'evening', time: '23:59', brightness: 0 },
    ]
    const previewAt = (date: Date) => {
      const schedule = resolveDynamicSchedule(steps, date, 60, 25)
      const active = interpolateSchedule(schedule, 360)
      return calculateFixtureOutput({ lightId: 'light.test_fixture', roomBrightness: active.brightness, scheduleTemp: active.temp, brightnessCurves: {}, dimToWarmCurves: {} })
    }
    expect(previewAt(new Date(2024, 5, 21, 12)).brightness).toBeGreaterThan(previewAt(new Date(2024, 11, 21, 12)).brightness)
  })
})
