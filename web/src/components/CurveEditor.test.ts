import { describe, it, expect, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import { reactive } from 'vue'
import CurveEditor from './CurveEditor.vue'
import type { BrightnessCurve } from '../types'

describe('CurveEditor.vue', () => {
  const sampleCurves: Record<string, BrightnessCurve> = {
    cove_accent: {
      name: 'cove_accent',
      lights: ['light.cove_1'],
      points: [
        [0, 0],
        [50, 100],
        [100, 100],
      ],
    },
  }

  it('renders curve selector and SVG canvas with control points', () => {
    const wrapper = mount(CurveEditor, {
      props: {
        brightnessCurves: sampleCurves,
        roomLights: ['light.cove_1', 'light.ceiling_1'],
      },
    })

    expect(wrapper.text()).toContain('Room Brightness Distribution Curves')
    expect(wrapper.text()).toContain('cove_accent')

    // SVG elements: path and 3 control point circles
    const circles = wrapper.findAll('circle')
    expect(circles.length).toBe(3)
  })

  it('emits openGlobalDtw when DTW button is clicked', async () => {
    const wrapper = mount(CurveEditor, {
      props: {
        brightnessCurves: sampleCurves,
        roomLights: ['light.cove_1'],
      },
    })

    const dtwBtn = wrapper.findAll('button').find((b) => b.text().includes('Dim-to-Warm Curves'))
    expect(dtwBtn).toBeDefined()
    await dtwBtn!.trigger('click')

    expect(wrapper.emitted('openGlobalDtw')).toBeTruthy()
  })

  it('renders rename button next to active curve name', () => {
    const wrapper = mount(CurveEditor, {
      props: {
        brightnessCurves: sampleCurves,
        roomLights: ['light.cove_1'],
      },
    })

    const renameBtn = wrapper.findAll('button').find((b) => b.text().includes('Rename'))
    expect(renameBtn).toBeDefined()
    expect(renameBtn!.attributes('title')).toBe('Rename curve')
  })

  it('clicking rename button displays inline editing input pre-filled with curve name', async () => {
    const wrapper = mount(CurveEditor, {
      props: {
        brightnessCurves: sampleCurves,
        roomLights: ['light.cove_1'],
      },
    })

    const renameBtn = wrapper.findAll('button').find((b) => b.text().includes('Rename'))
    await renameBtn!.trigger('click')

    const input = wrapper.find('input[placeholder="Curve name"]')
    expect(input.exists()).toBe(true)
    expect((input.element as HTMLInputElement).value).toBe('cove_accent')
    expect(wrapper.find('button[title="Save new name"]').exists()).toBe(true)
    expect(wrapper.find('button[title="Cancel renaming"]').exists()).toBe(true)
  })

  it('canceling rename reverts view without modifying curve', async () => {
    const curves = reactive({
      cove_accent: {
        name: 'cove_accent',
        lights: ['light.cove_1'],
        points: [[0, 0], [100, 100]] as [number, number][],
      },
    })

    const wrapper = mount(CurveEditor, {
      props: {
        brightnessCurves: curves,
      },
    })

    const renameBtn = wrapper.findAll('button').find((b) => b.text().includes('Rename'))
    await renameBtn!.trigger('click')

    const input = wrapper.find('input[placeholder="Curve name"]')
    await input.setValue('different_name')

    const cancelBtn = wrapper.find('button[title="Cancel renaming"]')
    await cancelBtn.trigger('click')

    expect(wrapper.find('input[placeholder="Curve name"]').exists()).toBe(false)
    expect(wrapper.text()).toContain('cove_accent')
    expect(curves.cove_accent.name).toBe('cove_accent')
  })

  it('submitting a valid new name renames curve, updates dictionary key and selection', async () => {
    const curves = reactive<Record<string, BrightnessCurve>>({
      cove_accent: {
        name: 'cove_accent',
        lights: ['light.cove_1'],
        points: [[0, 0], [50, 75], [100, 100]],
      },
    })

    const wrapper = mount(CurveEditor, {
      props: {
        brightnessCurves: curves,
        roomLights: ['light.cove_1'],
      },
    })

    const renameBtn = wrapper.findAll('button').find((b) => b.text().includes('Rename'))
    await renameBtn!.trigger('click')

    const input = wrapper.find('input[placeholder="Curve name"]')
    await input.setValue('cove_ambient')

    const saveBtn = wrapper.find('button[title="Save new name"]')
    await saveBtn.trigger('click')

    // Inline edit closes
    expect(wrapper.find('input[placeholder="Curve name"]').exists()).toBe(false)

    // Dictionary updated
    expect(curves.cove_accent).toBeUndefined()
    expect(curves.cove_ambient).toBeDefined()
    expect(curves.cove_ambient.name).toBe('cove_ambient')
    expect(curves.cove_ambient.lights).toEqual(['light.cove_1'])
    expect(curves.cove_ambient.points).toEqual([[0, 0], [50, 75], [100, 100]])

    // Dropdown selection updated
    const select = wrapper.find('select')
    expect((select.element as HTMLSelectElement).value).toBe('cove_ambient')
    expect(wrapper.text()).toContain('cove_ambient')
  })

  it('rejects duplicate curve name and displays error message', async () => {
    const curves = reactive<Record<string, BrightnessCurve>>({
      curve_one: {
        name: 'curve_one',
        lights: [],
        points: [[0, 0], [100, 100]],
      },
      curve_two: {
        name: 'curve_two',
        lights: [],
        points: [[0, 0], [100, 100]],
      },
    })

    const wrapper = mount(CurveEditor, {
      props: {
        brightnessCurves: curves,
      },
    })

    const renameBtn = wrapper.findAll('button').find((b) => b.text().includes('Rename'))
    await renameBtn!.trigger('click')

    const input = wrapper.find('input[placeholder="Curve name"]')
    await input.setValue('curve_two')

    const saveBtn = wrapper.find('button[title="Save new name"]')
    await saveBtn.trigger('click')

    // Error displayed
    expect(wrapper.text()).toContain('A curve named "curve_two" already exists.')

    // Dictionary not modified
    expect(curves.curve_one).toBeDefined()
    expect(curves.curve_two).toBeDefined()
    expect(curves.curve_one.name).toBe('curve_one')
  })

  it('rejects empty or whitespace-only name', async () => {
    const curves = reactive<Record<string, BrightnessCurve>>({
      curve_one: {
        name: 'curve_one',
        lights: [],
        points: [[0, 0], [100, 100]],
      },
    })

    const wrapper = mount(CurveEditor, {
      props: {
        brightnessCurves: curves,
      },
    })

    const renameBtn = wrapper.findAll('button').find((b) => b.text().includes('Rename'))
    await renameBtn!.trigger('click')

    const input = wrapper.find('input[placeholder="Curve name"]')
    await input.setValue('   ')

    const saveBtn = wrapper.find('button[title="Save new name"]')
    await saveBtn.trigger('click')

    expect(wrapper.text()).toContain('Curve name cannot be empty.')
    expect(curves.curve_one).toBeDefined()
    expect(curves.curve_one.name).toBe('curve_one')
  })

  it('submitting identical name cleanly exits rename mode without error', async () => {
    const curves = reactive<Record<string, BrightnessCurve>>({
      curve_one: {
        name: 'curve_one',
        lights: [],
        points: [[0, 0], [100, 100]],
      },
    })

    const wrapper = mount(CurveEditor, {
      props: {
        brightnessCurves: curves,
      },
    })

    const renameBtn = wrapper.findAll('button').find((b) => b.text().includes('Rename'))
    await renameBtn!.trigger('click')

    const saveBtn = wrapper.find('button[title="Save new name"]')
    await saveBtn.trigger('click')

    expect(wrapper.find('input[placeholder="Curve name"]').exists()).toBe(false)
    expect(wrapper.find('.text-rose-400').exists()).toBe(false)
  })

  it('pressing Enter saves and pressing Escape cancels', async () => {
    const curves = reactive<Record<string, BrightnessCurve>>({
      curve_one: {
        name: 'curve_one',
        lights: [],
        points: [[0, 0], [100, 100]],
      },
    })

    const wrapper = mount(CurveEditor, {
      props: {
        brightnessCurves: curves,
      },
    })

    // Test Escape cancels
    const renameBtn = wrapper.findAll('button').find((b) => b.text().includes('Rename'))
    await renameBtn!.trigger('click')
    let input = wrapper.find('input[placeholder="Curve name"]')
    await input.setValue('temporary_edit')
    await input.trigger('keydown.esc')

    expect(wrapper.find('input[placeholder="Curve name"]').exists()).toBe(false)
    expect(curves.curve_one.name).toBe('curve_one')

    // Test Enter confirms
    await renameBtn!.trigger('click')
    input = wrapper.find('input[placeholder="Curve name"]')
    await input.setValue('renamed_via_enter')
    await input.trigger('keydown.enter')

    expect(wrapper.find('input[placeholder="Curve name"]').exists()).toBe(false)
    expect(curves.renamed_via_enter).toBeDefined()
    expect(curves.renamed_via_enter.name).toBe('renamed_via_enter')
  })

  it('renders Copy YAML and Import YAML buttons', () => {
    const wrapper = mount(CurveEditor, {
      props: {
        brightnessCurves: sampleCurves,
      },
    })

    const copyBtn = wrapper.findAll('button').find((b) => b.text().includes('Copy YAML'))
    const importBtn = wrapper.findAll('button').find((b) => b.text().includes('Import YAML'))

    expect(copyBtn?.exists()).toBe(true)
    expect(importBtn?.exists()).toBe(true)
  })

  it('copies curve points YAML to clipboard on click', async () => {
    const writeTextMock = vi.fn().mockResolvedValue(undefined)
    Object.defineProperty(navigator, 'clipboard', {
      value: { writeText: writeTextMock },
      writable: true,
      configurable: true,
    })

    const wrapper = mount(CurveEditor, {
      props: {
        brightnessCurves: sampleCurves,
      },
    })

    const copyBtn = wrapper.findAll('button').find((b) => b.text().includes('Copy YAML'))
    await copyBtn!.trigger('click')

    expect(writeTextMock).toHaveBeenCalledTimes(1)
    const written = writeTextMock.mock.calls[0][0]
    expect(written).toContain('points:')
    expect(written).toContain('[0, 0]')
    expect(written).toContain('[50, 100]')
  })

  it('handles curve import modal validation and applying to active curve', async () => {
    const curves = reactive<Record<string, BrightnessCurve>>({
      test_curve: {
        name: 'test_curve',
        lights: [],
        points: [[0, 0], [100, 100]],
      },
    })

    const wrapper = mount(CurveEditor, {
      props: {
        brightnessCurves: curves,
      },
    })

    // Open import modal
    const importBtn = wrapper.findAll('button').find((b) => b.text().includes('Import YAML'))
    await importBtn!.trigger('click')

    const textarea = wrapper.find('textarea')
    expect(textarea.exists()).toBe(true)

    // Test invalid syntax
    await textarea.setValue('points: [ bad')
    await textarea.trigger('input')
    expect(wrapper.text()).toContain('Invalid YAML syntax')

    // Test valid points YAML
    const validYaml = `
points:
  - [0, 0]
  - [40, 20]
  - [80, 90]
  - [100, 100]
`
    await textarea.setValue(validYaml)
    await textarea.trigger('input')

    expect(wrapper.text()).toContain('Ready to import 4 points')

    // Apply to active curve (default radio)
    const applyBtn = wrapper.findAll('button').find((b) => b.text().includes('Apply Curve'))
    await applyBtn!.trigger('click')

    expect(curves.test_curve.points).toEqual([
      [0, 0],
      [40, 20],
      [80, 90],
      [100, 100],
    ])
    // Modal closes
    expect(wrapper.find('textarea').exists()).toBe(false)
  })

  it('handles importing as a new curve', async () => {
    const curves = reactive<Record<string, BrightnessCurve>>({
      test_curve: {
        name: 'test_curve',
        lights: [],
        points: [[0, 0], [100, 100]],
      },
    })

    const wrapper = mount(CurveEditor, {
      props: {
        brightnessCurves: curves,
      },
    })

    const importBtn = wrapper.findAll('button').find((b) => b.text().includes('Import YAML'))
    await importBtn!.trigger('click')

    const textarea = wrapper.find('textarea')
    const validYaml = `
name: imported_accent
points:
  - [0, 0]
  - [30, 60]
  - [100, 100]
`
    await textarea.setValue(validYaml)
    await textarea.trigger('input')

    // Switch destination to "new"
    const radioNew = wrapper.find('input[value="new"]')
    const radioEl = radioNew.element as HTMLInputElement
    radioEl.checked = true
    await radioNew.trigger('change')

    const applyBtn = wrapper.findAll('button').find((b) => b.text().includes('Apply Curve'))
    await applyBtn!.trigger('click')

    expect(curves.imported_accent).toBeDefined()
    expect(curves.imported_accent.name).toBe('imported_accent')
    expect(curves.imported_accent.points).toEqual([
      [0, 0],
      [30, 60],
      [100, 100],
    ])
    expect((wrapper.find('select').element as HTMLSelectElement).value).toBe('imported_accent')
  })
})
