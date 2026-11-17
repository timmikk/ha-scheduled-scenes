import type { DynamicPointConfig } from '../types'

export function solarPosition(date: Date, _latitude: number, _longitude: number): { declination: number; equationOfTime: number } {
  const n = Math.floor((Date.UTC(date.getFullYear(), date.getMonth(), date.getDate()) - Date.UTC(date.getFullYear(), 0, 0)) / 86400000)
  const g = 2 * Math.PI / 365 * (n - 1)
  const equationOfTime = 229.18 * (0.000075 + 0.001868 * Math.cos(g) - 0.032077 * Math.sin(g) - 0.014615 * Math.cos(2*g) - 0.040849 * Math.sin(2*g))
  const declination = (0.006918 - 0.399912*Math.cos(g) + 0.070257*Math.sin(g) - 0.006758*Math.cos(2*g) + 0.000907*Math.sin(2*g) - 0.002697*Math.cos(3*g) + 0.00148*Math.sin(3*g)) * 180/Math.PI
  return { declination, equationOfTime }
}
export function solarNoon(date: Date, longitude: number): number { return 720 - 4*longitude - solarPosition(date, 0, longitude).equationOfTime }
export function elevationCrossing(date: Date, latitude: number, longitude: number, elevation: number, direction: 'rising'|'setting'|'any' = 'rising'): number | null {
  const { declination } = solarPosition(date, latitude, longitude)
  const rad = Math.PI/180, lat=latitude*rad, dec=declination*rad, alt=elevation*rad
  const c=(Math.sin(alt)-Math.sin(lat)*Math.sin(dec))/(Math.cos(lat)*Math.cos(dec))
  if (c < -1 || c > 1) return null
  const angle=Math.acos(c)*180/Math.PI
  return solarNoon(date, longitude) + (direction === 'setting' ? 1 : -1)*4*angle
}
export function resolveSunPoint(config: DynamicPointConfig, date: Date, latitude: number, longitude: number): number | null {
  const event=config.event ?? 'sunrise'
  let minute: number|null
  if (event==='solar_noon') minute=solarNoon(date,longitude)
  else if (event==='solar_midnight') minute=(solarNoon(date,longitude)+720)%1440
  else if (event==='elevation') minute=elevationCrossing(date,latitude,longitude,config.elevation ?? 0,config.direction ?? 'rising')
  else minute=elevationCrossing(date,latitude,longitude,event==='dawn'||event==='dusk'?-6:-0.833,event==='sunset'||event==='dusk'?'setting':'rising')
  if (minute===null) return null
  if (config.offset_unit==='angle' && ['elevation','sunrise','sunset','dawn','dusk'].includes(event)) {
    const base=event==='elevation' ? config.elevation??0 : event==='dawn'||event==='dusk' ? -6 : -0.833
    const direction=config.direction ?? (event==='sunset'||event==='dusk' ? 'setting' : 'rising')
    minute=elevationCrossing(date,latitude,longitude,base+(config.offset_value??0),direction)
  } else if (config.offset_unit !== 'angle') minute += config.offset_value ?? 0
  return minute===null ? null : ((Math.round(minute)%1440)+1440)%1440
}
export function yearlyVariation(config: DynamicPointConfig, date: Date, latitude: number, longitude: number): [number, number] | null {
  if (config.type !== 'sun') return null
  const values: number[]=[]
  for(let day=0;day<365;day++){const d=new Date(date.getFullYear(),0,1+day);const m=resolveSunPoint(config,d,latitude,longitude);if(m!==null) values.push(((m-d.getTimezoneOffset())%1440+1440)%1440)}
  return values.length ? [Math.min(...values),Math.max(...values)] : null
}
