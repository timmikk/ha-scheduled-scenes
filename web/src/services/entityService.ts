import type { HAArea, HALightEntity } from '../types'
import { MOCK_AREAS, MOCK_LIGHTS } from '../mock/data'

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

  getAllLights(): HALightEntity[] {
    return [...this.lights]
  }

  getLight(entityId: string): HALightEntity | undefined {
    return this.lights.find((l) => l.entity_id === entityId)
  }

  getAllAreas(): HAArea[] {
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
}

export const entityService = new MockEntityService()
