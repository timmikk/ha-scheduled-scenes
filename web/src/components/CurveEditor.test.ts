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

    // Active curve chip updated
    const activeChip = wrapper.find('[data-testid="curve-chip"][data-curve-name="cove_ambient"]')
    expect(activeChip.exists()).toBe(true)
    expect(activeChip.attributes('data-active')).toBe('true')
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

    const importedChip = wrapper.find('[data-testid="curve-chip"][data-curve-name="imported_accent"]')
    expect(importedChip.exists()).toBe(true)
    expect(importedChip.attributes('data-active')).toBe('true')
    expect(importedChip.attributes('data-visible')).toBe('true')
  })

  it('renders multiple visible curves simultaneously with distinct colors and gradients', () => {
    const curves = reactive<Record<string, BrightnessCurve>>({
      cove_led: {
        name: 'cove_led',
        lights: ['light.cove'],
        points: [[0, 0], [50, 100], [100, 100]],
      },
      ceiling_downlights: {
        name: 'ceiling_downlights',
        lights: ['light.ceiling'],
        points: [[0, 0], [30, 0], [100, 100]],
      },
      kitchen_task: {
        name: 'kitchen_task',
        lights: ['light.kitchen'],
        points: [[0, 0], [100, 100]],
      },
    })

    const wrapper = mount(CurveEditor, {
      props: {
        brightnessCurves: curves,
        roomLights: ['light.cove', 'light.ceiling'],
      },
    })

    // Room-associated curves default to visible; kitchen_task is hidden initially
    expect(wrapper.find('path[data-curve-path="cove_led"]').exists()).toBe(true)
    expect(wrapper.find('path[data-curve-path="ceiling_downlights"]').exists()).toBe(true)
    expect(wrapper.find('path[data-curve-path="kitchen_task"]').exists()).toBe(false)

    const coveStroke = wrapper.find('path[data-curve-path="cove_led"]').attributes('stroke')
    const ceilingStroke = wrapper
      .find('path[data-curve-path="ceiling_downlights"]')
      .attributes('stroke')
    expect(coveStroke).toBeTruthy()
    expect(ceilingStroke).toBeTruthy()
    expect(coveStroke).not.toBe(ceilingStroke)

    // Linear gradients generated for visible curves
    expect(wrapper.findAll('linearGradient').length).toBe(2)
  })

  it('toggles curve visibility on and off via chip toggle button', async () => {
    const curves = reactive<Record<string, BrightnessCurve>>({
      cove_led: {
        name: 'cove_led',
        lights: ['light.cove'],
        points: [[0, 0], [100, 100]],
      },
      ceiling_downlights: {
        name: 'ceiling_downlights',
        lights: ['light.ceiling'],
        points: [[0, 0], [50, 20], [100, 100]],
      },
    })

    const wrapper = mount(CurveEditor, {
      props: {
        brightnessCurves: curves,
        roomLights: ['light.cove', 'light.ceiling'],
      },
    })

    expect(wrapper.find('path[data-curve-path="ceiling_downlights"]').exists()).toBe(true)

    const ceilingChip = wrapper.find('[data-testid="curve-chip"][data-curve-name="ceiling_downlights"]')
    const toggleBtn = ceilingChip.find('[data-testid="curve-visibility-toggle"]')

    // Hide ceiling_downlights
    await toggleBtn.trigger('click')
    expect(wrapper.find('path[data-curve-path="ceiling_downlights"]').exists()).toBe(false)
    expect(ceilingChip.attributes('data-visible')).toBe('false')

    // Show ceiling_downlights again
    await toggleBtn.trigger('click')
    expect(wrapper.find('path[data-curve-path="ceiling_downlights"]').exists()).toBe(true)
    expect(ceilingChip.attributes('data-visible')).toBe('true')
  })

  it('switches active curve when clicking a curve chip or an inactive canvas curve', async () => {
    const curves = reactive<Record<string, BrightnessCurve>>({
      cove_led: {
        name: 'cove_led',
        lights: ['light.cove'],
        points: [[0, 0], [50, 100], [100, 100]],
      },
      ceiling_downlights: {
        name: 'ceiling_downlights',
        lights: ['light.ceiling'],
        points: [[0, 0], [40, 10], [80, 75], [100, 100]],
      },
    })

    const wrapper = mount(CurveEditor, {
      props: {
        brightnessCurves: curves,
        roomLights: ['light.cove', 'light.ceiling'],
      },
    })

    // Initially cove_led is active (3 draggable active points)
    expect(wrapper.findAll('circle[data-active-point="true"]').length).toBe(3)
    expect(
      wrapper
        .find('[data-testid="curve-chip"][data-curve-name="cove_led"]')
        .attributes('data-active')
    ).toBe('true')

    // Click inactive canvas curve path for ceiling_downlights
    const inactivePath = wrapper.find('path[data-curve-path="ceiling_downlights"]')
    await inactivePath.trigger('mousedown')

    expect(
      wrapper
        .find('[data-testid="curve-chip"][data-curve-name="ceiling_downlights"]')
        .attributes('data-active')
    ).toBe('true')
    // Active points now reflect ceiling_downlights (4 points)
    expect(wrapper.findAll('circle[data-active-point="true"]').length).toBe(4)

    // Switch back via curve chip selection button
    const coveSelectBtn = wrapper
      .find('[data-testid="curve-chip"][data-curve-name="cove_led"]')
      .find('[data-testid="curve-select-btn"]')
    await coveSelectBtn.trigger('click')

    expect(
      wrapper
        .find('[data-testid="curve-chip"][data-curve-name="cove_led"]')
        .attributes('data-active')
    ).toBe('true')
    expect(wrapper.findAll('circle[data-active-point="true"]').length).toBe(3)
  })

  it('supports adding and dragging control points on the active curve', async () => {
    const curves = reactive<Record<string, BrightnessCurve>>({
      cove_led: {
        name: 'cove_led',
        lights: [],
        points: [[0, 0], [100, 100]],
      },
    })

    const wrapper = mount(CurveEditor, {
      props: {
        brightnessCurves: curves,
      },
    })

    const svgWrapper = wrapper.find('svg[data-testid="curve-canvas"]')
    const svgEl = svgWrapper.element as SVGSVGElement
    svgEl.setAttribute('viewBox', '0 0 800 256')
    svgEl.getBoundingClientRect = () => ({
      width: 800,
      height: 256,
      top: 0,
      left: 0,
      bottom: 256,
      right: 800,
      x: 0,
      y: 0,
      toJSON: () => {},
    })

    // Click near center of canvas: PAD_X=24, width=800 -> x=400 => roomB=50
    // PAD_Y=18, height=256 -> y=128 => fixB=50
    await svgWrapper.trigger('mousedown', { clientX: 400, clientY: 128 })
    expect(curves.cove_led.points.length).toBe(3)
    expect(curves.cove_led.points[1]).toEqual([50, 50])
    expect(wrapper.emitted('update:previewRoomBrightness')?.[0]).toEqual([50])

    // Drag the new point upward and right (clientX ~ 550, clientY ~ 60)
    window.dispatchEvent(new MouseEvent('mousemove', { clientX: 550, clientY: 60 }))
    window.dispatchEvent(new MouseEvent('mouseup'))

    expect(curves.cove_led.points[1][0]).toBeGreaterThan(50)
    expect(curves.cove_led.points[1][1]).toBeGreaterThan(50)
    expect(wrapper.emitted('update:previewRoomBrightness')?.length).toBeGreaterThan(1)
  })

  it('supports All, None, and Room Fixtures quick toggle controls', async () => {
    const curves = reactive<Record<string, BrightnessCurve>>({
      living_cove: {
        name: 'living_cove',
        lights: ['light.living_cove'],
        points: [[0, 0], [100, 100]],
      },
      living_ceiling: {
        name: 'living_ceiling',
        lights: ['light.living_ceiling'],
        points: [[0, 0], [100, 100]],
      },
      kitchen_task: {
        name: 'kitchen_task',
        lights: ['light.kitchen_strip'],
        points: [[0, 0], [100, 100]],
      },
    })

    const wrapper = mount(CurveEditor, {
      props: {
        brightnessCurves: curves,
        roomLights: ['light.living_cove', 'light.living_ceiling'],
      },
    })

    // Click "All" -> all 3 curves visible
    await wrapper.find('[data-testid="quick-show-all"]').trigger('click')
    expect(wrapper.find('path[data-curve-path="living_cove"]').exists()).toBe(true)
    expect(wrapper.find('path[data-curve-path="living_ceiling"]').exists()).toBe(true)
    expect(wrapper.find('path[data-curve-path="kitchen_task"]').exists()).toBe(true)

    // Click "None" -> only active curve (living_cove) visible
    await wrapper.find('[data-testid="quick-show-none"]').trigger('click')
    expect(wrapper.find('path[data-curve-path="living_cove"]').exists()).toBe(true)
    expect(wrapper.find('path[data-curve-path="living_ceiling"]').exists()).toBe(false)
    expect(wrapper.find('path[data-curve-path="kitchen_task"]').exists()).toBe(false)

    // Click "Room Fixtures" -> living_cove and living_ceiling visible, kitchen_task hidden
    await wrapper.find('[data-testid="quick-show-room"]').trigger('click')
    expect(wrapper.find('path[data-curve-path="living_cove"]').exists()).toBe(true)
    expect(wrapper.find('path[data-curve-path="living_ceiling"]').exists()).toBe(true)
    expect(wrapper.find('path[data-curve-path="kitchen_task"]').exists()).toBe(false)
  })

  it('supports duplicating and deleting curves with confirmation when assigned', async () => {
    const curves = reactive<Record<string, BrightnessCurve>>({
      cove_led: {
        name: 'cove_led',
        lights: ['light.cove'],
        points: [[0, 0], [40, 80], [100, 100]],
      },
    })

    const promptMock = vi.fn().mockReturnValue('cove_led_v2')
    const confirmMock = vi.fn().mockReturnValue(true)
    vi.stubGlobal('prompt', promptMock)
    vi.stubGlobal('confirm', confirmMock)

    try {
      const wrapper = mount(CurveEditor, {
        props: {
          brightnessCurves: curves,
          roomLights: ['light.cove'],
        },
      })

      // Duplicate active curve
      const dupBtn = wrapper.findAll('button').find((b) => b.text().trim() === 'Duplicate')
      await dupBtn!.trigger('click')

      expect(curves.cove_led_v2).toBeDefined()
      expect(curves.cove_led_v2.points).toEqual([[0, 0], [40, 80], [100, 100]])
      expect(
        wrapper
          .find('[data-testid="curve-chip"][data-curve-name="cove_led_v2"]')
          .attributes('data-active')
      ).toBe('true')

      // Switch back to cove_led (which has assigned light) and delete it
      await wrapper
        .find('[data-testid="curve-chip"][data-curve-name="cove_led"] [data-testid="curve-select-btn"]')
        .trigger('click')

      const delBtn = wrapper.findAll('button').find((b) => b.text().trim() === 'Delete')
      await delBtn!.trigger('click')

      expect(confirmMock).toHaveBeenCalledTimes(1)
      expect(curves.cove_led).toBeUndefined()
      expect(
        wrapper
          .find('[data-testid="curve-chip"][data-curve-name="cove_led_v2"]')
          .attributes('data-active')
      ).toBe('true')
    } finally {
      vi.unstubAllGlobals()
    }
  })

  it('renders vertical room brightness cursor and intersection values across visible curves', () => {
    const curves = reactive<Record<string, BrightnessCurve>>({
      cove_led: {
        name: 'cove_led',
        lights: ['light.cove'],
        points: [[0, 0], [50, 100], [100, 100]],
      },
      ceiling_main: {
        name: 'ceiling_main',
        lights: ['light.ceiling'],
        points: [[0, 0], [50, 20], [100, 100]],
      },
    })

    const wrapper = mount(CurveEditor, {
      props: {
        brightnessCurves: curves,
        roomLights: ['light.cove', 'light.ceiling'],
        roomBrightness: 50,
      },
    })

    expect(wrapper.find('[data-testid="room-brightness-cursor"]').exists()).toBe(true)
    const intersectionDots = wrapper.findAll('circle[data-cursor-intersection="true"]')
    expect(intersectionDots.length).toBe(2)

    const readout = wrapper.find('[data-testid="cursor-readout"]').text()
    expect(readout).toContain('Room 50%')
    expect(readout).toContain('cove_led')
    expect(readout).toContain('100%')
    expect(readout).toContain('ceiling_main')
    expect(readout).toContain('20%')
  })

  it('deletes point on double-click while preserving at least 2 control points', async () => {
    const curves = reactive<Record<string, BrightnessCurve>>({
      cove_led: {
        name: 'cove_led',
        lights: [],
        points: [[0, 0], [50, 80], [100, 100]],
      },
    })

    const wrapper = mount(CurveEditor, {
      props: {
        brightnessCurves: curves,
      },
    })

    let circles = wrapper.findAll('circle[data-active-point="true"]')
    expect(circles.length).toBe(3)

    // Double-click middle point -> deleted
    await circles[1].trigger('dblclick')
    expect(curves.cove_led.points).toEqual([[0, 0], [100, 100]])

    // Double-click remaining point -> preserved at minimum 2 points
    circles = wrapper.findAll('circle[data-active-point="true"]')
    await circles[0].trigger('dblclick')
    expect(curves.cove_led.points.length).toBe(2)
  })

  it('attaches and detaches unassigned room fixtures on the active curve', async () => {
    const curves = reactive<Record<string, BrightnessCurve>>({
      cove_led: {
        name: 'cove_led',
        lights: ['light.cove'],
        points: [[0, 0], [100, 100]],
      },
    })

    const wrapper = mount(CurveEditor, {
      props: {
        brightnessCurves: curves,
        roomLights: ['light.cove', 'light.ceiling'],
      },
    })

    // Attach unassigned light.ceiling
    const attachBtn = wrapper.findAll('button').find((b) => b.text().includes('+ Attach Room Light'))
    expect(attachBtn).toBeDefined()
    await attachBtn!.trigger('click')

    const ceilingOption = wrapper.findAll('button').find((b) => b.text().includes('ceiling'))
    expect(ceilingOption).toBeDefined()
    await ceilingOption!.trigger('click')
    expect(curves.cove_led.lights).toEqual(['light.cove', 'light.ceiling'])

    // Detach light.cove
    const removeButtons = wrapper.findAll('button[title="Remove fixture from curve"]')
    expect(removeButtons.length).toBe(2)
    await removeButtons[0].trigger('click')
    expect(curves.cove_led.lights).toEqual(['light.ceiling'])
  })
})
