export interface LightOverride {
  brightness?: number
  temp?: number
}

export interface ScheduleStep {
  id: string
  time: string // "HH:MM"
  brightness: number // 0-100
  temp?: number // Kelvin e.g. 2700
  lights?: Record<string, LightOverride>
}

export interface DimToWarmCurve {
  name: string
  lights: string[]
  points: [number, number][] // [brightness, kelvin]
}

export interface BrightnessCurve {
  name: string
  lights: string[]
  points: [number, number][] // [room_brightness, fixture_brightness]
}

export interface ProgramConfig {
  name: string
  lights: string[]
  transition_time: number
  transition_interval: number
  transition_time_on?: number
  transition_time_on_light_turn_on?: number
  enable_when_light_turn_on?: boolean
  disable_when_lights_off?: boolean
  allow_turn_on_if_any_on?: boolean
  manual_override_timeout?: number
  schedule: ScheduleStep[]
}

export interface ScheduledScenesConfig {
  curves: Record<string, DimToWarmCurve>
  brightness_curves: Record<string, BrightnessCurve>
  programs: ProgramConfig[]
}

export interface HAArea {
  area_id: string
  name: string
}

export interface HALightEntity {
  entity_id: string
  name: string
  area_id?: string
  area_name?: string
  state?: 'on' | 'off'
  supported_color_modes?: string[]
  min_mireds?: number
  max_mireds?: number
  min_color_temp_kelvin: number
  max_color_temp_kelvin: number
}

// Backwards-compatibility alias
export type MockLight = HALightEntity

// Live Mode types
export type LiveModeType = 'off' | 'room' | 'dim_to_warm'

export interface FixtureLiveTarget {
  entityId: string
  brightnessPct: number
  kelvin?: number
}

export interface FixtureLiveState extends FixtureLiveTarget {
  updatedAt: number
  status: 'synced' | 'sending' | 'error'
}

export interface HAConnectionConfig {
  url: string
  token: string
  resumeOnExit: boolean
}
