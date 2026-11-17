import { describe, it, expect } from 'vitest'
import {
  getSvgCoordinates,
  getCurveGradientId,
  buildCurveLinePath,
  buildCurveAreaPath,
} from './svg'

describe('svg coordinate mapping', () => {
  it('returns (0,0) when bounding client rect is zero size', () => {
    const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg')
    svg.getBoundingClientRect = () => ({
      width: 0,
      height: 0,
      top: 0,
      left: 0,
      bottom: 0,
      right: 0,
      x: 0,
      y: 0,
      toJSON: () => {},
    })

    const coords = getSvgCoordinates(svg, new MouseEvent('mousemove', { clientX: 50, clientY: 50 }))
    expect(coords).toEqual({ x: 0, y: 0 })
  })

  it('maps mouse event within viewBox dimensions', () => {
    const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg')
    svg.setAttribute('viewBox', '0 0 1000 500')
    svg.getBoundingClientRect = () => ({
      width: 500,
      height: 250,
      top: 100,
      left: 100,
      bottom: 350,
      right: 600,
      x: 100,
      y: 100,
      toJSON: () => {},
    })

    // Click at center: clientX = 350 (left: 100 + 250), clientY = 225 (top: 100 + 125)
    const coords = getSvgCoordinates(svg, new MouseEvent('mousemove', { clientX: 350, clientY: 225 }))
    expect(coords.x).toBeCloseTo(500, 1)
    expect(coords.y).toBeCloseTo(250, 1)
  })

  it('builds sorted curve line and closed area paths', () => {
    const scaleX = (x: number) => x * 2
    const scaleY = (y: number) => 200 - y * 2

    const line = buildCurveLinePath(
      [
        [100, 100],
        [0, 0],
        [50, 80],
      ],
      scaleX,
      scaleY
    )
    expect(line).toBe('M 0,200 L 100,40 L 200,0')

    const area = buildCurveAreaPath(
      [
        [0, 0],
        [50, 80],
        [100, 100],
      ],
      scaleX,
      scaleY
    )
    expect(area).toBe('M 0,200 L 100,40 L 200,0 L 200,200 L 0,200 Z')
  })

  it('generates distinct DOM-safe gradient IDs for different curve names', () => {
    const id1 = getCurveGradientId('living room accent')
    const id2 = getCurveGradientId('living_room_accent')
    expect(id1).toMatch(/^[a-zA-Z0-9_-]+$/)
    expect(id2).toMatch(/^[a-zA-Z0-9_-]+$/)
    expect(id1).not.toBe(id2)
  })
})
