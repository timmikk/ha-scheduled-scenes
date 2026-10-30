import { reactive, ref, computed } from 'vue'
import type { FixtureLiveState, FixtureLiveTarget, HAConnectionConfig } from '../types'
import { entityService } from './entityService'

const STORAGE_KEY = 'scheduled_scenes_ha_conn'
const THROTTLE_MS = 120
const LIVE_TRANSITION_SECONDS = 0.15

function loadConnectionConfig(): HAConnectionConfig {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    if (raw) {
      const parsed = JSON.parse(raw)
      return {
        url: typeof parsed.url === 'string' ? parsed.url : '',
        token: typeof parsed.token === 'string' ? parsed.token : '',
        resumeOnExit: typeof parsed.resumeOnExit === 'boolean' ? parsed.resumeOnExit : true,
      }
    }
  } catch {
    // Ignore storage read errors
  }
  return {
    url: '',
    token: '',
    resumeOnExit: true,
  }
}

function getEmbeddedHass(): any | null {
  const w = window as any
  if (w.hass && typeof w.hass.callService === 'function') return w.hass
  try {
    if (w.parent && w.parent !== w && w.parent.hass && typeof w.parent.hass.callService === 'function') {
      return w.parent.hass
    }
  } catch {
    // Cross-origin frame access ignored
  }
  return null
}

class LiveOutputService {
  readonly connectionConfig = reactive<HAConnectionConfig>(loadConnectionConfig())
  readonly liveStates = reactive<Record<string, FixtureLiveState>>({})
  readonly dispatchCount = ref(0)
  readonly lastCommandLog = ref<{ time: string; summary: string } | null>(null)
  readonly lastError = ref<string | null>(null)

  private lastSentCache = new Map<string, { brightnessPct: number; kelvin?: number }>()
  private pendingTargets: FixtureLiveTarget[] | null = null
  private throttleTimer: ReturnType<typeof setTimeout> | null = null
  private lastFlushTime = 0
  private pausedPrograms = new Set<string>()

  readonly transportMode = computed<'ha_embedded' | 'ha_remote' | 'mock'>(() => {
    if (getEmbeddedHass()) return 'ha_embedded'
    if (this.connectionConfig.url.trim() && this.connectionConfig.token.trim()) return 'ha_remote'
    return 'mock'
  })

  saveConnectionConfig(config: Partial<HAConnectionConfig>) {
    if (config.url !== undefined) this.connectionConfig.url = config.url.trim().replace(/\/+$/, '')
    if (config.token !== undefined) this.connectionConfig.token = config.token.trim()
    if (config.resumeOnExit !== undefined) this.connectionConfig.resumeOnExit = config.resumeOnExit
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(this.connectionConfig))
    } catch {
      // Ignore storage write errors
    }
  }

  /**
   * Starts a live session and pauses the active room schedule in Home Assistant
   * so background periodic transitions do not overwrite live studio adjustments.
   */
  async startLiveSession(programName?: string) {
    this.lastSentCache.clear()
    this.lastError.value = null

    if (programName) {
      this.pausedPrograms.add(programName)
      await this.callService('scheduled_scenes', 'disable', {
        entity_id: `switch.schedule_${programName}`,
      })
      this.recordLog(`Paused schedule_${programName} for live preview`)
    }
  }

  /**
   * Stops the active live session and optionally resumes any paused room schedules.
   */
  async stopLiveSession() {
    if (this.throttleTimer) {
      clearTimeout(this.throttleTimer)
      this.throttleTimer = null
    }
    this.pendingTargets = null
    this.lastSentCache.clear()

    if (this.connectionConfig.resumeOnExit && this.pausedPrograms.size > 0) {
      const programsToResume = Array.from(this.pausedPrograms)
      this.pausedPrograms.clear()
      for (const progName of programsToResume) {
        await this.callService('scheduled_scenes', 'enable', {
          entity_id: `switch.schedule_${progName}`,
        })
        await this.callService('scheduled_scenes', 'resume_schedule', {
          entity_id: `switch.schedule_${progName}`,
        })
        this.recordLog(`Resumed schedule_${progName}`)
      }
    } else {
      this.pausedPrograms.clear()
    }
  }

  /**
   * Queues target fixture outputs with trailing-edge throttling (120ms)
   * so 60fps scrubbing/dragging stays smooth without flooding Zigbee/Thread bridges.
   */
  syncFixtures(targets: FixtureLiveTarget[]) {
    this.pendingTargets = targets
    const now = Date.now()
    const elapsed = now - this.lastFlushTime

    if (elapsed >= THROTTLE_MS && !this.throttleTimer) {
      this.flushTargets()
    } else if (!this.throttleTimer) {
      const remaining = Math.max(16, THROTTLE_MS - elapsed)
      this.throttleTimer = setTimeout(() => {
        this.throttleTimer = null
        this.flushTargets()
      }, remaining)
    }
  }

  private async flushTargets() {
    const targets = this.pendingTargets
    if (!targets) return
    this.pendingTargets = null
    this.lastFlushTime = Date.now()

    for (const rawTarget of targets) {
      const { entityId } = rawTarget
      const brightnessPct = Math.max(0, Math.min(100, Math.round(rawTarget.brightnessPct)))
      const meta = entityService.getLight(entityId)

      const supportsKelvin =
        !meta?.supported_color_modes || meta.supported_color_modes.includes('color_temp')

      let effectiveKelvin: number | undefined = undefined
      if (brightnessPct > 0 && rawTarget.kelvin !== undefined && supportsKelvin) {
        const minK = meta?.min_color_temp_kelvin ?? 1500
        const maxK = meta?.max_color_temp_kelvin ?? 6500
        effectiveKelvin = Math.max(minK, Math.min(maxK, Math.round(rawTarget.kelvin)))
      }

      const prev = this.lastSentCache.get(entityId)
      if (prev && prev.brightnessPct === brightnessPct && prev.kelvin === effectiveKelvin) {
        continue
      }

      this.lastSentCache.set(entityId, { brightnessPct, kelvin: effectiveKelvin })
      this.liveStates[entityId] = {
        entityId,
        brightnessPct,
        kelvin: effectiveKelvin,
        updatedAt: Date.now(),
        status: 'sending',
      }

      try {
        if (brightnessPct <= 0) {
          await this.callService('light', 'turn_off', {
            entity_id: entityId,
            transition: LIVE_TRANSITION_SECONDS,
          })
          this.recordLog(`${entityId} → OFF`)
        } else {
          const payload: Record<string, any> = {
            entity_id: entityId,
            brightness_pct: brightnessPct,
            transition: LIVE_TRANSITION_SECONDS,
          }
          if (effectiveKelvin !== undefined) {
            payload.color_temp_kelvin = effectiveKelvin
          }
          await this.callService('light', 'turn_on', payload)
          this.recordLog(
            `${entityId} → ${brightnessPct}%${effectiveKelvin ? ` @ ${effectiveKelvin}K` : ''}`,
          )
        }

        if (meta) {
          meta.state = brightnessPct > 0 ? 'on' : 'off'
        }

        this.dispatchCount.value += 1
        this.liveStates[entityId] = {
          entityId,
          brightnessPct,
          kelvin: effectiveKelvin,
          updatedAt: Date.now(),
          status: 'synced',
        }
      } catch (err: any) {
        this.lastError.value = err?.message || 'Failed to dispatch light command'
        this.liveStates[entityId] = {
          entityId,
          brightnessPct,
          kelvin: effectiveKelvin,
          updatedAt: Date.now(),
          status: 'error',
        }
      }
    }
  }

  private async callService(domain: string, service: string, serviceData: Record<string, any>) {
    const mode = this.transportMode.value

    if (mode === 'ha_embedded') {
      const hass = getEmbeddedHass()
      if (hass) {
        await hass.callService(domain, service, serviceData)
        return
      }
    }

    if (mode === 'ha_remote') {
      const url = `${this.connectionConfig.url}/api/services/${domain}/${service}`
      const res = await fetch(url, {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${this.connectionConfig.token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(serviceData),
      })
      if (!res.ok) {
        throw new Error(`HA HTTP ${res.status}: ${res.statusText}`)
      }
      return
    }

    // In 'mock' mode, no network request is required
  }

  private recordLog(summary: string) {
    const now = new Date()
    const time = now.toTimeString().slice(0, 8)
    this.lastCommandLog.value = { time, summary }
  }
}

export const liveOutputService = new LiveOutputService()
