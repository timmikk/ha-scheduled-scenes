import { describe, it, expect } from 'vitest'
import {
  timeToMinutes,
  minutesToTime,
  interpolateScalar,
  evaluateBrightnessCurve,
  evaluateDimToWarm,
  interpolateSchedule,
  calculateFixtureOutput,
} from './interpolator'
import type { ScheduleStep } from '../types'

describe('interpolator utilities', () => {
  describe('time conversions', () => {
    it('converts HH:MM strings to minutes from midnight', () => {
      expect(timeToMinutes('00:00')).toBe(0)
      expect(timeToMinutes('06:30')).toBe(390)
      expect(timeToMinutes('12:00')).toBe(720)
      expect(timeToMinutes('23:59')).toBe(1439)
    })

    it('converts minutes from midnight to normalized HH:MM', () => {
      expect(minutesToTime(0)).toBe('00:00')
      expect(minutesToTime(390)).toBe('06:30')
      expect(minutesToTime(1440)).toBe('00:00') // wrap
      expect(minutesToTime(-60)).toBe('23:00') // negative wrap
    })
  })

  describe('scalar interpolation', () => {
    it('interpolates midpoint linearly', () => {
      expect(interpolateScalar(0, 100, 0.5)).toBe(50)
      expect(interpolateScalar(2000, 4000, 0.25)).toBe(2500)
    })
  })

  describe('piecewise brightness curves', () => {
    const curve: [number, number][] = [
      [0, 0],
      [30, 0],
      [50, 40],
      [100, 100],
    ]

    it('clamps outside boundaries', () => {
      expect(evaluateBrightnessCurve(curve, -10)).toBe(0)
      expect(evaluateBrightnessCurve(curve, 120)).toBe(100)
    })

    it('evaluates dead zones and linear segments', () => {
      expect(evaluateBrightnessCurve(curve, 20)).toBe(0)
      expect(evaluateBrightnessCurve(curve, 30)).toBe(0)
      expect(evaluateBrightnessCurve(curve, 40)).toBe(20) // halfway between 30 (0) and 50 (40)
      expect(evaluateBrightnessCurve(curve, 50)).toBe(40)
      expect(evaluateBrightnessCurve(curve, 75)).toBe(70) // halfway between 50 (40) and 100 (100)
    })
  })

  describe('dim-to-warm curves', () => {
    const dtw: [number, number][] = [
      [1, 2000],
      [50, 2600],
      [100, 3500],
    ]

    it('evaluates color temperature across brightness', () => {
      expect(evaluateDimToWarm(dtw, 1)).toBe(2000)
      expect(evaluateDimToWarm(dtw, 50)).toBe(2600)
      expect(evaluateDimToWarm(dtw, 100)).toBe(3500)
      expect(evaluateDimToWarm(dtw, 0)).toBe(2000) // clamped
      expect(evaluateDimToWarm(dtw, 75)).toBe(3050) // halfway between 2600 and 3500
    })
  })

  describe('schedule interpolation and wrap-around', () => {
    const steps: ScheduleStep[] = [
      { id: '1', time: '06:00', brightness: 20, temp: 2000 },
      { id: '2', time: '12:00', brightness: 100, temp: 5000 },
      { id: '3', time: '22:00', brightness: 40, temp: 2400 },
    ]

    it('interpolates within daytime steps', () => {
      const active = interpolateSchedule(steps, 540) // 09:00 (halfway 06:00 to 12:00)
      expect(active.brightness).toBe(60)
      expect(active.temp).toBe(3500)
      expect(active.progress).toBeCloseTo(0.5, 2)
    })

    it('interpolates wrapping around midnight', () => {
      // Transition from 22:00 (min 1320) to 06:00 (min 360) = total 480 mins
      // Midpoint is 02:00 (min 120, elapsed 240 mins)
      const active = interpolateSchedule(steps, 120)
      expect(active.progress).toBeCloseTo(0.5, 2)
      expect(active.brightness).toBe(30) // halfway between 40 and 20
      expect(active.temp).toBe(2200) // halfway between 2400 and 2000
    })
  })

  describe('fixture output calculation', () => {
    it('applies brightness curves and dim-to-warm curves in sequence', () => {
      const output = calculateFixtureOutput({
        lightId: 'light.accent',
        roomBrightness: 50,
        scheduleTemp: 4000,
        brightnessCurves: {
          accent_curve: {
            name: 'accent_curve',
            lights: ['light.accent'],
            points: [
              [0, 0],
              [50, 80],
              [100, 100],
            ],
          },
        },
        dimToWarmCurves: {
          dtw: {
            name: 'dtw',
            lights: ['light.accent'],
            points: [
              [0, 2000],
              [80, 2800],
              [100, 3200],
            ],
          },
        },
      })

      // Room bri 50 -> fixture bri 80
      expect(output.brightness).toBe(80)
      // Fixture bri 80 -> DTW temp 2800
      expect(output.temp).toBe(2800)
    })
  })
})
