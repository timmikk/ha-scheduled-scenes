import { describe, it, expect } from 'vitest'
import { kelvinToRgb, kelvinToCssColor } from './color'

describe('color utilities', () => {
  it('converts standard warm white (2700K)', () => {
    const rgb = kelvinToRgb(2700)
    expect(rgb.r).toBe(255)
    expect(rgb.g).toBeGreaterThan(150)
    expect(rgb.b).toBeGreaterThan(50)
    expect(rgb.b).toBeLessThan(150)
  })

  it('converts daylight white (6500K)', () => {
    const rgb = kelvinToRgb(6500)
    expect(rgb.r).toBeGreaterThan(200)
    expect(rgb.g).toBeGreaterThan(200)
    expect(rgb.b).toBeGreaterThanOrEqual(250)
  })

  it('clamps extreme cold and warm values', () => {
    const extremeWarm = kelvinToRgb(500) // below 1000K min
    expect(extremeWarm.r).toBe(255)
    expect(extremeWarm.b).toBe(0)

    const extremeCold = kelvinToRgb(50000) // above 40000K max
    expect(extremeCold.b).toBe(255)
  })

  it('generates valid rgba css color string with opacity', () => {
    const css = kelvinToCssColor(3000, 0.8)
    expect(css).toMatch(/^rgba\(\d+,\s*\d+,\s*\d+,\s*0\.8\)$/)
  })
})
