import type { ScheduleStep, BrightnessCurve, DimToWarmCurve } from '../types'

export function timeToMinutes(timeStr: string): number {
  const [h, m] = timeStr.split(':').map((s) => parseInt(s, 10))
  return (h || 0) * 60 + (m || 0)
}

export function minutesToTime(minutes: number): string {
  const normalized = ((Math.round(minutes) % 1440) + 1440) % 1440
  const h = String(Math.floor(normalized / 60)).padStart(2, '0')
  const m = String(normalized % 60).padStart(2, '0')
  return `${h}:${m}`
}

export function interpolateScalar(v1: number, v2: number, fraction: number): number {
  return Math.round(v1 + (v2 - v1) * fraction)
}

/**
 * Evaluates piecewise linear room brightness -> light brightness curve.
 */
export function evaluateBrightnessCurve(points: [number, number][], roomBrightness: number): number {
  if (!points || points.length === 0) {
    return Math.max(0, Math.min(100, Math.round(roomBrightness)))
  }

  const sorted = [...points].sort((a, b) => a[0] - b[0])

  if (roomBrightness <= sorted[0][0]) {
    return Math.max(0, Math.min(100, Math.round(sorted[0][1])))
  }
  if (roomBrightness >= sorted[sorted.length - 1][0]) {
    return Math.max(0, Math.min(100, Math.round(sorted[sorted.length - 1][1])))
  }

  for (let i = 0; i < sorted.length - 1; i++) {
    const [r1, l1] = sorted[i]
    const [r2, l2] = sorted[i + 1]
    if (roomBrightness >= r1 && roomBrightness <= r2) {
      if (r2 === r1) return Math.max(0, Math.min(100, Math.round(l1)))
      const fraction = (roomBrightness - r1) / (r2 - r1)
      const val = interpolateScalar(l1, l2, fraction)
      return Math.max(0, Math.min(100, val))
    }
  }

  return Math.max(0, Math.min(100, Math.round(sorted[sorted.length - 1][1])))
}

/**
 * Evaluates dim-to-warm curve: light brightness (0-100) -> color temperature (Kelvin).
 */
export function evaluateDimToWarm(points: [number, number][], brightness: number): number {
  const DEFAULT_TEMP = 2700
  if (!points || points.length === 0) return DEFAULT_TEMP

  const sorted = [...points].sort((a, b) => a[0] - b[0])

  if (brightness <= sorted[0][0]) return sorted[0][1]
  if (brightness >= sorted[sorted.length - 1][0]) return sorted[sorted.length - 1][1]

  for (let i = 0; i < sorted.length - 1; i++) {
    const [b1, t1] = sorted[i]
    const [b2, t2] = sorted[i + 1]
    if (brightness >= b1 && brightness <= b2) {
      if (b2 === b1) return t1
      const fraction = (brightness - b1) / (b2 - b1)
      return interpolateScalar(t1, t2, fraction)
    }
  }

  return sorted[sorted.length - 1][1]
}

export interface ActiveInterpolation {
  brightness: number
  temp: number
  startStep: ScheduleStep
  endStep: ScheduleStep
  progress: number // 0 to 1
}

/**
 * Interpolates room schedule at a specific minute of the day (0-1439).
 * Correctly wraps around midnight.
 */
export function interpolateSchedule(
  steps: ScheduleStep[],
  minuteOfDay: number
): ActiveInterpolation {
  if (!steps || steps.length === 0) {
    const fallback: ScheduleStep = { id: 'fallback', time: '12:00', brightness: 50, temp: 2700 }
    return { brightness: 50, temp: 2700, startStep: fallback, endStep: fallback, progress: 0 }
  }

  if (steps.length === 1) {
    const s = steps[0]
    return { brightness: s.brightness, temp: s.temp ?? 2700, startStep: s, endStep: s, progress: 1 }
  }

  // Sort steps by minute of day
  const sorted = [...steps].sort((a, b) => timeToMinutes(a.time) - timeToMinutes(b.time))

  let startStep = sorted[sorted.length - 1]
  let endStep = sorted[0]

  for (let i = 0; i < sorted.length; i++) {
    const stepMin = timeToMinutes(sorted[i].time)
    if (minuteOfDay >= stepMin) {
      startStep = sorted[i]
      endStep = sorted[(i + 1) % sorted.length]
    }
  }

  // Calculate elapsed and total duration in minutes
  const startMin = timeToMinutes(startStep.time)
  const endMin = timeToMinutes(endStep.time)

  let totalMinutes = endMin - startMin
  if (totalMinutes <= 0) totalMinutes += 1440

  let elapsedMinutes = minuteOfDay - startMin
  if (elapsedMinutes < 0) elapsedMinutes += 1440

  const fraction = Math.max(0, Math.min(1, elapsedMinutes / totalMinutes))

  const brightness = interpolateScalar(startStep.brightness, endStep.brightness, fraction)

  const startTemp = startStep.temp ?? 2700
  const endTemp = endStep.temp ?? 2700
  const temp = interpolateScalar(startTemp, endTemp, fraction)

  return {
    brightness,
    temp,
    startStep,
    endStep,
    progress: fraction,
  }
}

/**
 * Calculates output for a specific fixture given current room state and curve configurations.
 */
export function calculateFixtureOutput(params: {
  lightId: string
  roomBrightness: number
  scheduleTemp: number
  brightnessCurves: Record<string, BrightnessCurve>
  dimToWarmCurves: Record<string, DimToWarmCurve>
}): { brightness: number; temp: number } {
  const { lightId, roomBrightness, scheduleTemp, brightnessCurves, dimToWarmCurves } = params

  // 1. Check if light has a room brightness curve
  let fixtureBrightness = roomBrightness
  const bCurve = Object.values(brightnessCurves).find((c) => c.lights.includes(lightId))
  if (bCurve) {
    fixtureBrightness = evaluateBrightnessCurve(bCurve.points, roomBrightness)
  }

  // 2. Check if light has a dim-to-warm curve
  let fixtureTemp = scheduleTemp
  const dtwCurve = Object.values(dimToWarmCurves).find((c) => c.lights.includes(lightId))
  if (dtwCurve) {
    fixtureTemp = evaluateDimToWarm(dtwCurve.points, fixtureBrightness)
  }

  return {
    brightness: fixtureBrightness,
    temp: fixtureTemp,
  }
}

/**
 * Calculates fixture-specific target brightness and temp considering per-light schedule step overrides.
 */
export function calculateScheduleLightState(
  active: ActiveInterpolation,
  lightId: string
): { brightness: number; temp: number } {
  const { startStep, endStep, progress } = active

  const startOverride = startStep.lights?.[lightId]
  const endOverride = endStep.lights?.[lightId]

  const bStart = startOverride?.brightness ?? startStep.brightness
  const bEnd = endOverride?.brightness ?? endStep.brightness
  const brightness = interpolateScalar(bStart, bEnd, progress)

  const tStart = startOverride?.temp ?? (startStep.temp ?? 2700)
  const tEnd = endOverride?.temp ?? (endStep.temp ?? 2700)
  const temp = interpolateScalar(tStart, tEnd, progress)

  return { brightness, temp }
}
