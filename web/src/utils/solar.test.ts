import { describe, expect, it } from 'vitest'
import { elevationCrossing, resolveSunPoint, solarNoon, solarPosition } from './solar'
import solarParityCases from '../../../tests/fixtures/solar_parity_cases.json'

describe('solar calculations', () => {
  it('places solar noon around midday at Greenwich', () => {
    expect(solarNoon(new Date(2024, 2, 20), 0)).toBeGreaterThan(710)
    expect(solarNoon(new Date(2024, 2, 20), 0)).toBeLessThan(730)
  })
  it('returns rising and setting crossings around noon', () => {
    const date = new Date(2024, 5, 21)
    const rise = elevationCrossing(date, 51.5, 0, -0.833, 'rising')!
    const set = elevationCrossing(date, 51.5, 0, -0.833, 'setting')!
    expect(rise).toBeLessThan(solarNoon(date, 0))
    expect(set).toBeGreaterThan(solarNoon(date, 0))
  })
  it('returns no sunrise in polar night', () => {
    expect(resolveSunPoint({ type: 'sun', event: 'sunrise' }, new Date(2024, 11, 21), 89, 0)).toBeNull()
  })
  it('matches the shared Python solar golden cases', () => {
    for (const item of solarParityCases) {
      const date = new Date(`${item.date}T12:00:00`)
      const { declination, equationOfTime } = solarPosition(date, item.latitude, item.longitude)
      expect(declination).toBeCloseTo(item.declination, 9)
      expect(equationOfTime).toBeCloseTo(item.equation_of_time, 9)
      expect(solarNoon(date, item.longitude)).toBeCloseTo(item.solar_noon, 9)
      if (item.rise_crossing === null) {
        expect(elevationCrossing(date, item.latitude, item.longitude, -0.833, 'rising')).toBeNull()
        expect(elevationCrossing(date, item.latitude, item.longitude, -0.833, 'setting')).toBeNull()
      } else {
        expect(elevationCrossing(date, item.latitude, item.longitude, -0.833, 'rising')).toBeCloseTo(item.rise_crossing, 9)
        expect(elevationCrossing(date, item.latitude, item.longitude, -0.833, 'setting')).toBeCloseTo(item.set_crossing!, 9)
      }
      expect(resolveSunPoint({ type: 'sun', event: 'sunrise', offset_unit: 'angle', offset_value: 5 }, date, item.latitude, item.longitude)).toBe(item.sunrise_angle_offset)
    }
  })
})
