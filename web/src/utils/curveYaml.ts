import { dump, load } from 'js-yaml'
import type { ScheduleStep } from '../types'
import { timeToMinutes } from './interpolator'

export interface ParsedScheduleResult {
  success: boolean
  data?: ScheduleStep[]
  error?: string
}

export interface ParsedCurvePointsResult {
  success: boolean
  points?: [number, number][]
  name?: string
  error?: string
}

/**
 * Safely copies text to the browser clipboard with fallback for non-secure contexts or mock tests.
 */
export async function copyToClipboard(text: string): Promise<boolean> {
  if (typeof navigator !== 'undefined' && navigator.clipboard && typeof navigator.clipboard.writeText === 'function') {
    try {
      await navigator.clipboard.writeText(text)
      return true
    } catch {
      // Fall through to fallback
    }
  }

  if (typeof document !== 'undefined') {
    try {
      const textarea = document.createElement('textarea')
      textarea.value = text
      textarea.style.position = 'fixed'
      textarea.style.opacity = '0'
      document.body.appendChild(textarea)
      textarea.focus()
      textarea.select()
      const ok = document.execCommand('copy')
      document.body.removeChild(textarea)
      return ok
    } catch {
      return false
    }
  }
  return false
}

/**
 * Serializes an array of ScheduleStep objects into standard Home Assistant schedule YAML.
 */
export function serializeScheduleYaml(steps: ScheduleStep[]): string {
  if (!steps || steps.length === 0) {
    return 'schedule: []\n'
  }

  // Sort steps by time
  const sorted = [...steps].sort((a, b) => timeToMinutes(a.time) - timeToMinutes(b.time))

  const cleanSteps = sorted.map((s) => {
    const item: Record<string, any> = {
      time: String(s.time),
      brightness: Math.round(Number(s.brightness)),
    }
    if (s.temp !== undefined && s.temp !== null) {
      item.temp = Math.round(Number(s.temp))
    }
    if (s.lights && Object.keys(s.lights).length > 0) {
      item.lights = s.lights
    }
    return item
  })

  return dump({ schedule: cleanSteps }, { indent: 2, lineWidth: -1 })
}

/**
 * Normalizes time string to HH:MM format with 24-hour validation.
 */
function normalizeTime(val: any): string | null {
  if (val === undefined || val === null) return null
  const str = String(val).trim()
  const match = str.match(/^(\d{1,2}):(\d{2})$/)
  if (!match) return null

  const hours = parseInt(match[1], 10)
  const minutes = parseInt(match[2], 10)

  if (hours < 0 || hours > 23 || minutes < 0 || minutes > 59) {
    return null
  }

  return `${String(hours).padStart(2, '0')}:${String(minutes).padStart(2, '0')}`
}

/**
 * Parses and validates YAML string containing schedule steps.
 * Supports:
 * - { schedule: [...] }
 * - Bare YAML list of step items
 * - Root object containing a program/room definition with `schedule`
 */
export function parseScheduleYaml(yamlStr: string): ParsedScheduleResult {
  if (!yamlStr || typeof yamlStr !== 'string' || !yamlStr.trim()) {
    return { success: false, error: 'YAML input is empty.' }
  }

  let parsed: any
  try {
    parsed = load(yamlStr)
  } catch (err: any) {
    return { success: false, error: `Invalid YAML syntax: ${err.message || err}` }
  }

  if (!parsed) {
    return { success: false, error: 'Parsed YAML produced no data.' }
  }

  // Extract steps list
  let rawSteps: any[] | null = null

  if (Array.isArray(parsed)) {
    rawSteps = parsed
  } else if (typeof parsed === 'object') {
    if (Array.isArray(parsed.schedule)) {
      rawSteps = parsed.schedule
    } else {
      // Look for a nested program or room object that has a schedule
      const keys = Object.keys(parsed)
      for (const k of keys) {
        if (parsed[k] && typeof parsed[k] === 'object' && Array.isArray(parsed[k].schedule)) {
          rawSteps = parsed[k].schedule
          break
        }
      }
    }
  }

  if (!rawSteps || !Array.isArray(rawSteps)) {
    return {
      success: false,
      error: 'Expected a list of schedule steps or an object with a "schedule" list.',
    }
  }

  if (rawSteps.length < 2) {
    return {
      success: false,
      error: 'A valid schedule requires at least 2 checkpoints across the day.',
    }
  }

  const validatedSteps: ScheduleStep[] = []

  for (let i = 0; i < rawSteps.length; i++) {
    const item = rawSteps[i]
    if (!item || typeof item !== 'object') {
      return {
        success: false,
        error: `Step #${i + 1} is not a valid object.`,
      }
    }

    const normTime = normalizeTime(item.time)
    if (!normTime) {
      return {
        success: false,
        error: `Step #${i + 1} has an invalid time '${item.time}'. Expected 'HH:MM' (00:00 - 23:59).`,
      }
    }

    const b = Number(item.brightness)
    if (isNaN(b) || b < 0 || b > 100) {
      return {
        success: false,
        error: `Step #${i + 1} (${normTime}) brightness '${item.brightness}' must be a number between 0 and 100.`,
      }
    }

    let temp: number | undefined = undefined
    if (item.temp !== undefined && item.temp !== null) {
      const t = Number(item.temp)
      if (isNaN(t) || t < 1000 || t > 10000) {
        return {
          success: false,
          error: `Step #${i + 1} (${normTime}) color temperature '${item.temp}' must be between 1000K and 10000K.`,
        }
      }
      temp = Math.round(t)
    }

    validatedSteps.push({
      id: item.id ? String(item.id) : `step-${Date.now()}-${i}`,
      time: normTime,
      brightness: Math.round(b),
      temp,
      lights: item.lights && typeof item.lights === 'object' ? item.lights : undefined,
    })
  }

  // Sort chronologically
  validatedSteps.sort((a, b) => timeToMinutes(a.time) - timeToMinutes(b.time))

  // Ensure times are distinct
  for (let i = 1; i < validatedSteps.length; i++) {
    if (validatedSteps[i].time === validatedSteps[i - 1].time) {
      return {
        success: false,
        error: `Duplicate checkpoint time '${validatedSteps[i].time}' found. Each checkpoint must have a distinct time.`,
      }
    }
  }

  return { success: true, data: validatedSteps }
}

/**
 * Serializes points for a brightness distribution curve into clean YAML with compact point pairs.
 */
export function serializeCurvePointsYaml(points: [number, number][], name?: string): string {
  const sorted = [...points].sort((a, b) => a[0] - b[0])
  const lines: string[] = []

  if (name) {
    lines.push(`name: ${name}`)
  }
  lines.push('points:')
  for (const [x, y] of sorted) {
    lines.push(`  - [${Math.round(x)}, ${Math.round(y)}]`)
  }

  return lines.join('\n') + '\n'
}

/**
 * Parses and validates YAML string containing brightness curve points.
 * Supports:
 * - Bare array of coordinate pairs: [[0, 0], [50, 100]]
 * - { points: [[0, 0], [50, 100]] } with optional `name`
 * - Full curve definition { name: '...', lights: [...], points: [...] }
 * - Container mapping { brightness_curves: { my_curve: { points: [...] } } }
 */
export function parseCurvePointsYaml(yamlStr: string): ParsedCurvePointsResult {
  if (!yamlStr || typeof yamlStr !== 'string' || !yamlStr.trim()) {
    return { success: false, error: 'YAML input is empty.' }
  }

  let parsed: any
  try {
    parsed = load(yamlStr)
  } catch (err: any) {
    return { success: false, error: `Invalid YAML syntax: ${err.message || err}` }
  }

  if (!parsed) {
    return { success: false, error: 'Parsed YAML produced no data.' }
  }

  let rawPoints: any[] | null = null
  let extractedName: string | undefined = undefined

  if (Array.isArray(parsed)) {
    // Check if it's an array of points [[x, y], ...]
    if (parsed.length > 0 && Array.isArray(parsed[0])) {
      rawPoints = parsed
    }
  } else if (typeof parsed === 'object') {
    if (parsed.name && typeof parsed.name === 'string') {
      extractedName = parsed.name
    }

    if (Array.isArray(parsed.points)) {
      rawPoints = parsed.points
    } else {
      // Look for a nested curve object
      const keys = Object.keys(parsed)
      for (const k of keys) {
        const val = parsed[k]
        if (val && typeof val === 'object') {
          if (Array.isArray(val.points)) {
            rawPoints = val.points
            if (!extractedName) extractedName = val.name || k
            break
          } else if (val && typeof val === 'object') {
            // Check one deeper (e.g. brightness_curves: { curve_name: { points: [...] } })
            const subKeys = Object.keys(val)
            for (const sk of subKeys) {
              if (val[sk] && typeof val[sk] === 'object' && Array.isArray(val[sk].points)) {
                rawPoints = val[sk].points
                if (!extractedName) extractedName = val[sk].name || sk
                break
              }
            }
            if (rawPoints) break
          }
        }
      }
    }
  }

  if (!rawPoints || !Array.isArray(rawPoints)) {
    return {
      success: false,
      error: 'Expected a list of [room_brightness, fixture_brightness] points or an object with "points".',
    }
  }

  if (rawPoints.length < 2) {
    return {
      success: false,
      error: 'A curve requires at least 2 control points.',
    }
  }

  const validatedPoints: [number, number][] = []

  for (let i = 0; i < rawPoints.length; i++) {
    const pt = rawPoints[i]
    if (!Array.isArray(pt) || pt.length < 2) {
      return {
        success: false,
        error: `Point #${i + 1} is invalid. Expected [x, y] coordinates.`,
      }
    }

    const x = Number(pt[0])
    const y = Number(pt[1])

    if (isNaN(x) || x < 0 || x > 100) {
      return {
        success: false,
        error: `Point #${i + 1} Room Brightness '${pt[0]}' must be between 0 and 100.`,
      }
    }

    if (isNaN(y) || y < 0 || y > 100) {
      return {
        success: false,
        error: `Point #${i + 1} Fixture Brightness '${pt[1]}' must be between 0 and 100.`,
      }
    }

    validatedPoints.push([Math.round(x), Math.round(y)])
  }

  // Sort by x ascending
  validatedPoints.sort((a, b) => a[0] - b[0])

  return {
    success: true,
    points: validatedPoints,
    name: extractedName,
  }
}
