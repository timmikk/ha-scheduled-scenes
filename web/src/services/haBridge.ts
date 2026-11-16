import type { ScheduledScenesConfig } from '../types'

type Hass = {
  states: Record<string, { entity_id: string; attributes: Record<string, unknown>; state: string }>
  callWS<T>(message: Record<string, unknown>): Promise<T>
}

declare global {
  interface Window { hass?: Hass }
}

function findHass(): Hass | undefined {
  try {
    return window.hass ?? window.parent.hass
  } catch {
    return window.hass
  }
}

export const haBridge = {
  connection(): Hass | undefined { return findHass() },
  isConnected(): boolean { return Boolean(findHass()?.callWS) },

  async loadConfig(): Promise<ScheduledScenesConfig> {
    const hass = findHass()
    if (!hass) throw new Error('Home Assistant connection is not available')
    const config = await hass.callWS<ScheduledScenesConfig>({
      type: 'scheduled_scenes/config/get',
    })
    return {
      programs: config.programs ?? [],
      curves: config.curves ?? {},
      brightness_curves: config.brightness_curves ?? {},
    }
  },

  async saveConfig(config: ScheduledScenesConfig): Promise<void> {
    const hass = findHass()
    if (!hass) throw new Error('Home Assistant connection is not available')
    await hass.callWS({
      type: 'scheduled_scenes/config/save',
      ...config,
    })
  },
}
