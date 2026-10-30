/**
 * Tanner Helland algorithm to convert color temperature in Kelvin to RGB.
 * Valid range: 1000K to 40000K.
 */
export function kelvinToRgb(kelvin: number): { r: number; g: number; b: number } {
  const temp = Math.max(1000, Math.min(40000, kelvin)) / 100
  let r: number, g: number, b: number

  // Red
  if (temp <= 66) {
    r = 255
  } else {
    r = 329.698727446 * Math.pow(temp - 60, -0.1332047592)
    r = Math.min(255, Math.max(0, r))
  }

  // Green
  if (temp <= 66) {
    g = 99.4708025861 * Math.log(temp) - 161.1195681661
    g = Math.min(255, Math.max(0, g))
  } else {
    g = 288.1221695283 * Math.pow(temp - 60, -0.0755148492)
    g = Math.min(255, Math.max(0, g))
  }

  // Blue
  if (temp >= 66) {
    b = 255
  } else if (temp <= 19) {
    b = 0
  } else {
    b = 138.5177312231 * Math.log(temp - 10) - 305.0447927307
    b = Math.min(255, Math.max(0, b))
  }

  return {
    r: Math.round(r),
    g: Math.round(g),
    b: Math.round(b),
  }
}

export function kelvinToCssColor(kelvin: number, opacity = 1): string {
  const { r, g, b } = kelvinToRgb(kelvin)
  return `rgba(${r}, ${g}, ${b}, ${opacity})`
}
