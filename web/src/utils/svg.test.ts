import { describe, it, expect } from 'vitest'
import { getSvgCoordinates } from './svg'

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
})
