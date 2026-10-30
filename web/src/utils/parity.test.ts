import { describe, it, expect } from 'vitest'
import parityFixture from '../../../tests/fixtures/parity_cases.json'
import { interpolateSchedule, calculateScheduleLightState } from './interpolator'
import type { ScheduleStep } from '../types'

describe('cross-engine schedule parity tests', () => {
  for (const [roomName, roomData] of Object.entries(parityFixture.rooms)) {
    describe(`room: ${roomName}`, () => {
      const steps: ScheduleStep[] = roomData.schedule.map((s, idx) => ({
        id: `step_${idx}`,
        time: s.time,
        brightness: s.brightness,
        temp: s.temp,
        lights: (s as any).lights || {},
      }))

      for (const evalCase of roomData.evaluations) {
        it(`matches evaluation at ${evalCase.time} for ${evalCase.light}`, () => {
          const active = interpolateSchedule(steps, evalCase.minute_of_day)
          const fixtureState = calculateScheduleLightState(active, evalCase.light)

          if (evalCase.expected.brightness !== undefined) {
            expect(fixtureState.brightness).toBe(evalCase.expected.brightness)
          }
          if (evalCase.expected.temp !== undefined) {
            expect(fixtureState.temp).toBe(evalCase.expected.temp)
          }
        })
      }
    })
  }
})
