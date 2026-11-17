/**
 * Converts a mouse event's client coordinates into the local coordinate system of an SVG element.
 * Uses getBoundingClientRect() to guarantee exact pixel mapping across all browsers,
 * screen scaling factors (Retina / Windows 125%/150%), page scrolling, and container transforms.
 */
export function getSvgCoordinates(svg: SVGSVGElement, event: MouseEvent): { x: number; y: number } {
  const rect = svg.getBoundingClientRect()
  if (rect.width === 0 || rect.height === 0) {
    return { x: 0, y: 0 }
  }

  // Calculate mouse position relative to the SVG element in CSS pixels, clamped to bounds
  const mouseX = Math.max(0, Math.min(rect.width, event.clientX - rect.left))
  const mouseY = Math.max(0, Math.min(rect.height, event.clientY - rect.top))

  // Normalized fraction across the SVG element (0.0 to 1.0)
  const fractionX = mouseX / rect.width
  const fractionY = mouseY / rect.height

  // Map to SVG viewBox dimensions
  const viewBox = svg.viewBox.baseVal
  const vbWidth = viewBox && viewBox.width > 0 ? viewBox.width : rect.width
  const vbHeight = viewBox && viewBox.height > 0 ? viewBox.height : rect.height

  return {
    x: fractionX * vbWidth,
    y: fractionY * vbHeight,
  }
}

/**
 * Produces a DOM-safe SVG linearGradient id for an arbitrary curve name.
 */
export function getCurveGradientId(curveName: string): string {
  let hash = 2166136261
  for (let i = 0; i < curveName.length; i++) {
    hash ^= curveName.charCodeAt(i)
    hash = Math.imul(hash, 16777619)
  }
  const slug = curveName.replace(/[^a-zA-Z0-9_-]/g, '_').slice(0, 32) || 'curve'
  return `curve-grad-${slug}-${(hash >>> 0).toString(36)}`
}

/**
 * Builds an SVG polyline path string for [x, y] curve control points sorted by X ascending.
 */
export function buildCurveLinePath(
  points: [number, number][],
  scaleX: (val: number) => number,
  scaleY: (val: number) => number
): string {
  if (!points || points.length === 0) return ''
  const sorted = [...points].sort((a, b) => a[0] - b[0])
  let d = `M ${scaleX(sorted[0][0])},${scaleY(sorted[0][1])}`
  for (let i = 1; i < sorted.length; i++) {
    d += ` L ${scaleX(sorted[i][0])},${scaleY(sorted[i][1])}`
  }
  return d
}

/**
 * Builds a closed SVG area path under the curve down to y = 0.
 */
export function buildCurveAreaPath(
  points: [number, number][],
  scaleX: (val: number) => number,
  scaleY: (val: number) => number
): string {
  const line = buildCurveLinePath(points, scaleX, scaleY)
  if (!line || !points.length) return ''
  const sorted = [...points].sort((a, b) => a[0] - b[0])
  const first = sorted[0]
  const last = sorted[sorted.length - 1]
  return `${line} L ${scaleX(last[0])},${scaleY(0)} L ${scaleX(first[0])},${scaleY(0)} Z`
}
