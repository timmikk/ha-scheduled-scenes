import type { CurvePaletteColor } from '../types'

export const CURVE_COLOR_PALETTE: CurvePaletteColor[] = [
  {
    id: 'indigo',
    name: 'Indigo',
    stroke: '#6366f1',
    fill: '#6366f1',
    bgClass: 'bg-indigo-500/15',
    textClass: 'text-indigo-300',
    borderClass: 'border-indigo-500/60',
    badgeClass: 'bg-indigo-950/90 text-indigo-300 border-indigo-700/70',
    dotClass: 'bg-indigo-500',
  },
  {
    id: 'emerald',
    name: 'Emerald',
    stroke: '#10b981',
    fill: '#10b981',
    bgClass: 'bg-emerald-500/15',
    textClass: 'text-emerald-300',
    borderClass: 'border-emerald-500/60',
    badgeClass: 'bg-emerald-950/90 text-emerald-300 border-emerald-700/70',
    dotClass: 'bg-emerald-500',
  },
  {
    id: 'amber',
    name: 'Amber',
    stroke: '#f59e0b',
    fill: '#f59e0b',
    bgClass: 'bg-amber-500/15',
    textClass: 'text-amber-300',
    borderClass: 'border-amber-500/60',
    badgeClass: 'bg-amber-950/90 text-amber-300 border-amber-700/70',
    dotClass: 'bg-amber-500',
  },
  {
    id: 'cyan',
    name: 'Cyan',
    stroke: '#06b6d4',
    fill: '#06b6d4',
    bgClass: 'bg-cyan-500/15',
    textClass: 'text-cyan-300',
    borderClass: 'border-cyan-500/60',
    badgeClass: 'bg-cyan-950/90 text-cyan-300 border-cyan-700/70',
    dotClass: 'bg-cyan-500',
  },
  {
    id: 'rose',
    name: 'Rose',
    stroke: '#f43f5e',
    fill: '#f43f5e',
    bgClass: 'bg-rose-500/15',
    textClass: 'text-rose-300',
    borderClass: 'border-rose-500/60',
    badgeClass: 'bg-rose-950/90 text-rose-300 border-rose-700/70',
    dotClass: 'bg-rose-500',
  },
  {
    id: 'purple',
    name: 'Purple',
    stroke: '#a855f7',
    fill: '#a855f7',
    bgClass: 'bg-purple-500/15',
    textClass: 'text-purple-300',
    borderClass: 'border-purple-500/60',
    badgeClass: 'bg-purple-950/90 text-purple-300 border-purple-700/70',
    dotClass: 'bg-purple-500',
  },
  {
    id: 'orange',
    name: 'Orange',
    stroke: '#f97316',
    fill: '#f97316',
    bgClass: 'bg-orange-500/15',
    textClass: 'text-orange-300',
    borderClass: 'border-orange-500/60',
    badgeClass: 'bg-orange-950/90 text-orange-300 border-orange-700/70',
    dotClass: 'bg-orange-500',
  },
  {
    id: 'teal',
    name: 'Teal',
    stroke: '#14b8a6',
    fill: '#14b8a6',
    bgClass: 'bg-teal-500/15',
    textClass: 'text-teal-300',
    borderClass: 'border-teal-500/60',
    badgeClass: 'bg-teal-950/90 text-teal-300 border-teal-700/70',
    dotClass: 'bg-teal-500',
  },
]

function hashCurveName(name: string): number {
  let hash = 2166136261
  for (let i = 0; i < name.length; i++) {
    hash ^= name.charCodeAt(i)
    hash = Math.imul(hash, 16777619)
  }
  return hash >>> 0
}

/**
 * Deterministically resolves a palette color for a given curve name.
 */
export function getCurveColor(curveName: string): CurvePaletteColor {
  if (!curveName) return CURVE_COLOR_PALETTE[0]
  const idx = hashCurveName(curveName) % CURVE_COLOR_PALETTE.length
  return CURVE_COLOR_PALETTE[idx]
}

/**
 * Deterministically resolves distinct palette colors for a list of curve names,
 * avoiding hash collisions while fewer than palette.length curves are present.
 */
export function resolveCurveColors(curveNames: string[]): Record<string, CurvePaletteColor> {
  const result: Record<string, CurvePaletteColor> = {}
  const usedIndices = new Set<number>()
  const len = CURVE_COLOR_PALETTE.length

  for (const name of curveNames) {
    let idx = hashCurveName(name) % len
    if (usedIndices.size < len) {
      while (usedIndices.has(idx)) {
        idx = (idx + 1) % len
      }
      usedIndices.add(idx)
    }
    result[name] = CURVE_COLOR_PALETTE[idx]
  }

  return result
}

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
