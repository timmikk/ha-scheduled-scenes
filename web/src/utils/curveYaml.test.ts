import { describe, it, expect } from 'vitest'
import {
  serializeScheduleYaml,
  parseScheduleYaml,
  serializeCurvePointsYaml,
  parseCurvePointsYaml,
} from './curveYaml'
import type { ScheduleStep } from '../types'

describe('curveYaml utils', () => {
  describe('serializeScheduleYaml', () => {
    it('serializes schedule steps to clean Home Assistant YAML format', () => {
      const steps: ScheduleStep[] = [
        { id: '1', time: '09:00', brightness: 100, temp: 4000 },
        { id: '2', time: '06:30', brightness: 20, temp: 2400 },
      ]

      const yaml = serializeScheduleYaml(steps)
      expect(yaml).toContain('schedule:')
      // Verify sorted order (06:30 before 09:00)
      const idx1 = yaml.indexOf('06:30')
      const idx2 = yaml.indexOf('09:00')
      expect(idx1).toBeGreaterThan(-1)
      expect(idx2).toBeGreaterThan(idx1)
      expect(yaml).toContain('brightness: 20')
      expect(yaml).toContain('temp: 2400')
      expect(yaml).not.toContain('id:')
    })

    it('handles empty step array gracefully', () => {
      expect(serializeScheduleYaml([])).toBe('schedule: []\n')
    })
  })

  describe('parseScheduleYaml', () => {
    it('parses valid schedule YAML with schedule: root key', () => {
      const yaml = `
schedule:
  - time: "06:30"
    brightness: 20
    temp: 2400
  - time: "18:00"
    brightness: 80
    temp: 3500
`
      const res = parseScheduleYaml(yaml)
      expect(res.success).toBe(true)
      expect(res.data).toHaveLength(2)
      expect(res.data![0].time).toBe('06:30')
      expect(res.data![0].brightness).toBe(20)
      expect(res.data![0].temp).toBe(2400)
      expect(res.data![1].time).toBe('18:00')
      expect(res.data![1].brightness).toBe(80)
    })

    it('parses bare YAML list of steps', () => {
      const yaml = `
- time: "07:15"
  brightness: 35
- time: "22:00"
  brightness: 5
`
      const res = parseScheduleYaml(yaml)
      expect(res.success).toBe(true)
      expect(res.data).toHaveLength(2)
      expect(res.data![0].time).toBe('07:15')
      expect(res.data![0].brightness).toBe(35)
      expect(res.data![0].temp).toBeUndefined()
    })

    it('normalizes single digit hours to HH:MM', () => {
      const yaml = `
- time: "7:05"
  brightness: 50
- time: "19:30"
  brightness: 10
`
      const res = parseScheduleYaml(yaml)
      expect(res.success).toBe(true)
      expect(res.data![0].time).toBe('07:05')
    })

    it('sorts unsorted checkpoints chronologically', () => {
      const yaml = `
- time: "23:00"
  brightness: 10
- time: "05:00"
  brightness: 15
- time: "12:00"
  brightness: 100
`
      const res = parseScheduleYaml(yaml)
      expect(res.success).toBe(true)
      expect(res.data!.map((s) => s.time)).toEqual(['05:00', '12:00', '23:00'])
    })

    it('rejects duplicate checkpoint times', () => {
      const yaml = `
- time: "12:00"
  brightness: 50
- time: "12:00"
  brightness: 80
`
      const res = parseScheduleYaml(yaml)
      expect(res.success).toBe(false)
      expect(res.error).toContain('Duplicate checkpoint time')
    })

    it('rejects empty input or malformed YAML', () => {
      expect(parseScheduleYaml('').success).toBe(false)
      expect(parseScheduleYaml('   ').success).toBe(false)
      expect(parseScheduleYaml(': bad yaml :').success).toBe(false)
    })

    it('rejects invalid time or brightness ranges', () => {
      const badTime = `
- time: "25:00"
  brightness: 50
- time: "12:00"
  brightness: 50
`
      expect(parseScheduleYaml(badTime).success).toBe(false)

      const badBrightness = `
- time: "06:00"
  brightness: 150
- time: "12:00"
  brightness: 50
`
      expect(parseScheduleYaml(badBrightness).success).toBe(false)
    })

    it('rejects schedules with fewer than 2 points', () => {
      const single = `
- time: "12:00"
  brightness: 50
`
      expect(parseScheduleYaml(single).success).toBe(false)
      expect(parseScheduleYaml(single).error).toContain('at least 2 checkpoints')
    })
  })

  describe('serializeCurvePointsYaml', () => {
    it('serializes points cleanly', () => {
      const points: [number, number][] = [
        [0, 0],
        [50, 80],
        [100, 100],
      ]
      const yaml = serializeCurvePointsYaml(points, 'accent_curve')
      expect(yaml).toContain('name: accent_curve')
      expect(yaml).toContain('points:')
      expect(yaml).toContain('[0, 0]')
      expect(yaml).toContain('[50, 80]')
    })
  })

  describe('parseCurvePointsYaml', () => {
    it('parses bare array of points', () => {
      const yaml = `
- [0, 0]
- [40, 20]
- [100, 100]
`
      const res = parseCurvePointsYaml(yaml)
      expect(res.success).toBe(true)
      expect(res.points).toEqual([
        [0, 0],
        [40, 20],
        [100, 100],
      ])
    })

    it('parses object with points and name', () => {
      const yaml = `
name: reading_light
points:
  - [0, 0]
  - [30, 50]
  - [100, 100]
`
      const res = parseCurvePointsYaml(yaml)
      expect(res.success).toBe(true)
      expect(res.name).toBe('reading_light')
      expect(res.points).toHaveLength(3)
    })

    it('parses nested curve dictionary', () => {
      const yaml = `
brightness_curves:
  cove_lighting:
    points:
      - [0, 0]
      - [60, 90]
      - [100, 100]
`
      const res = parseCurvePointsYaml(yaml)
      expect(res.success).toBe(true)
      expect(res.name).toBe('cove_lighting')
      expect(res.points).toEqual([
        [0, 0],
        [60, 90],
        [100, 100],
      ])
    })

    it('sorts points by X coordinate', () => {
      const yaml = `
- [100, 100]
- [0, 0]
- [50, 75]
`
      const res = parseCurvePointsYaml(yaml)
      expect(res.success).toBe(true)
      expect(res.points).toEqual([
        [0, 0],
        [50, 75],
        [100, 100],
      ])
    })

    it('rejects points out of range 0-100', () => {
      const badX = `
- [-5, 0]
- [100, 100]
`
      expect(parseCurvePointsYaml(badX).success).toBe(false)

      const badY = `
- [0, 0]
- [50, 120]
`
      expect(parseCurvePointsYaml(badY).success).toBe(false)
    })

    it('rejects empty input or less than 2 points', () => {
      expect(parseCurvePointsYaml('').success).toBe(false)
      expect(parseCurvePointsYaml('- [0, 0]').success).toBe(false)
    })
  })
})
