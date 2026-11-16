import type { HAArea, HALightEntity } from '../types'
import { ref } from 'vue'
import { MOCK_AREAS, MOCK_LIGHTS } from '../mock/data'
import { haBridge } from './haBridge'

export interface EntityProvider {
  getAllLights(): HALightEntity[]
  getLight(entityId: string): HALightEntity | undefined
  getAllAreas(): HAArea[]
  getLightsByArea(areaId: string): HALightEntity[]
  searchLights(query: string): HALightEntity[]
}

class MockEntityService implements EntityProvider {
  private lights: HALightEntity[] = MOCK_LIGHTS
  private areas: HAArea[] = MOCK_AREAS
  private revision = ref(0)

  getAllLights(): HALightEntity[] {
    this.revision.value
    return [...this.lights]
  }

  getLight(entityId: string): HALightEntity | undefined {
    return this.lights.find((l) => l.entity_id === entityId)
  }

  getAllAreas(): HAArea[] {
    this.revision.value
    return [...this.areas]
  }

  getLightsByArea(areaId: string): HALightEntity[] {
    return this.lights.filter((l) => l.area_id === areaId)
  }

  searchLights(query: string): HALightEntity[] {
    const q = query.trim().toLowerCase()
    if (!q) return this.getAllLights()
    return this.lights.filter(
      (l) =>
        l.entity_id.toLowerCase().includes(q) ||
        l.name.toLowerCase().includes(q) ||
        (l.area_name && l.area_name.toLowerCase().includes(q)),
    )
  }

  /**
   * Helper to format light for display: returns friendly name if known, else entityId.
   */
  getFriendlyName(entityId: string): string {
    const light = this.getLight(entityId)
    return light?.name || entityId.replace(/^light\./, '').replace(/_/g, ' ')
  }

  refreshFromHomeAssistant(): void {
    const hass = haBridge.connection()
    if (!hass) return
    const areaByEntity = new Map<string, { id: string; name: string }>()
    // Home Assistant exposes area assignments in entity registry; states remain
    // useful even when an entity has not been assigned to an area.
    void hass.callWS<Array<{ entity_id: string; area_id?: string }>>({
      type: 'config/entity_registry/list',
    }).then(async (entities) => {
      const areas = await hass.callWS<Array<{ area_id: string; name: string }>>({
        type: 'config/area_registry/list',
      })
      const areaNames = new Map(areas.map((area) => [area.area_id, area.name]))
      for (const entity of entities) {
        if (entity.area_id) areaByEntity.set(entity.entity_id, { id: entity.area_id, name: areaNames.get(entity.area_id) ?? entity.area_id })
      }
      this.areas = areas
        .map((area) => ({ area_id: area.area_id, name: area.name }))
        .sort((a, b) => a.name.localeCompare(b.name))
      this.lights = Object.values(hass.states)
        .filter((state) => state.entity_id.startsWith('light.'))
        .map((state) => {
          const area = areaByEntity.get(state.entity_id)
          const attrs = state.attributes
          return {
            entity_id: state.entity_id,
            name: String(attrs.friendly_name ?? state.entity_id),
            area_id: area?.id,
            area_name: area?.name,
            state: state.state === 'on' ? 'on' as const : 'off' as const,
            supported_color_modes: attrs.supported_color_modes as string[] | undefined,
            min_mireds: attrs.min_mireds as number | undefined,
            max_mireds: attrs.max_mireds as number | undefined,
            min_color_temp_kelvin: Number(attrs.min_color_temp_kelvin ?? 2000),
            max_color_temp_kelvin: Number(attrs.max_color_temp_kelvin ?? 6500),
          }
        })
      this.revision.value += 1
    }).catch((error: unknown) => console.warn('Unable to load Home Assistant entity registry', error))
  }
}

export const entityService = new MockEntityService()
