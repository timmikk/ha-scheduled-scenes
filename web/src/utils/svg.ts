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
