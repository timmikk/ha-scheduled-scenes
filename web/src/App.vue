<template>
  <div class="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans">
    <!-- Top Navigation Bar -->
    <header class="border-b border-slate-800 bg-slate-900/90 backdrop-blur sticky top-0 z-40 px-6 py-3.5 flex items-center justify-between flex-wrap gap-4">
      <div class="flex items-center gap-3">
        <div class="w-8 h-8 rounded-lg bg-indigo-600 flex items-center justify-center font-bold text-white shadow-md shadow-indigo-500/20">
          🌅
        </div>
        <div>
          <h1 class="text-sm font-bold tracking-tight text-white flex items-center gap-2">
            Scheduled Scenes Studio
            <span class="text-[10px] bg-indigo-950 text-indigo-400 border border-indigo-800 px-1.5 py-0.5 rounded-full font-mono font-semibold">
              v0.3.0
            </span>
          </h1>
          <p class="text-[11px] text-slate-400">
            Graphical Configuration, Circadian Schedules &amp; Global Hardware Curves
          </p>
        </div>
      </div>

      <!-- Center: Navigation Switcher (Rooms vs. Global Dim-to-Warm Module) -->
      <div class="flex items-center gap-2 bg-slate-950/80 border border-slate-800 p-1 rounded-xl">
        <!-- Room Switcher Tabs -->
        <div class="flex items-center gap-1">
          <button
            v-for="(prog, idx) in config.programs"
            :key="prog.name"
            @click="selectRoom(idx)"
            :class="[
              'text-xs font-semibold px-3 py-1.5 rounded-lg transition cursor-pointer flex items-center gap-1.5',
              activeView === 'room' && activeProgramIdx === idx
                ? 'bg-indigo-600 text-white shadow-sm'
                : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900',
            ]"
          >
            <span>🛋️</span>
            <span>{{ prog.name }}</span>
          </button>

          <button
            @click="addNewProgram"
            class="text-xs text-slate-400 hover:text-slate-200 hover:bg-slate-900 px-2.5 py-1.5 rounded-lg transition cursor-pointer"
            title="Add another room"
          >
            + Add Room
          </button>
        </div>

        <div class="h-4 w-px bg-slate-800 mx-1"></div>

        <!-- Global Dim-to-Warm Module Tab -->
        <button
          @click="activeView = 'dim_to_warm'"
          :class="[
            'text-xs font-semibold px-3 py-1.5 rounded-lg transition cursor-pointer flex items-center gap-1.5 border',
            activeView === 'dim_to_warm'
              ? 'bg-amber-600 text-white border-amber-500 shadow-sm shadow-amber-600/30'
              : 'bg-transparent border-transparent text-amber-400 hover:bg-slate-900 hover:text-amber-300',
          ]"
        >
          <span>🌡️</span>
          <span>Global Dim-to-Warm</span>
          <span
            :class="[
              'text-[10px] px-1.5 py-0.2 rounded-full font-mono font-semibold',
              activeView === 'dim_to_warm'
                ? 'bg-amber-800 text-amber-100'
                : 'bg-amber-950 text-amber-300 border border-amber-800',
            ]"
          >
            {{ Object.keys(config.curves).length }}
          </span>
        </button>
      </div>

      <!-- Right: Status & Dev Pills -->
      <div class="flex items-center gap-3">
        <!-- Live Mode Badge -->
        <div
          v-if="liveMode !== 'off'"
          :class="[
            'flex items-center gap-1.5 text-xs px-2.5 py-1 rounded-full font-mono border animate-pulse',
            liveMode === 'room'
              ? 'bg-rose-950/80 border-rose-700 text-rose-300'
              : 'bg-amber-950/80 border-amber-700 text-amber-300',
          ]"
        >
          <span class="w-2 h-2 rounded-full bg-white"></span>
          <span>LIVE: {{ liveMode === 'room' ? 'Room Sync' : 'DTW Calibration' }}</span>
        </div>

        <div class="flex items-center gap-1.5 text-xs bg-emerald-950/60 border border-emerald-800/60 text-emerald-300 px-2.5 py-1 rounded-full font-mono">
          <span class="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
          <span>Mock Data Active</span>
        </div>
        <div class="text-[11px] font-mono text-slate-500 hidden sm:block">
          ahjo:5173
        </div>
      </div>
    </header>

    <!-- Main Workspace Content -->
    <main class="flex-1 max-w-7xl w-full mx-auto p-6 flex flex-col gap-6">
      <!-- VIEW 1: Standalone Global Dim-to-Warm Module -->
      <div v-if="activeView === 'dim_to_warm'" class="flex flex-col gap-6">
        <DimToWarmManager
          mode="page"
          :curves="config.curves"
          :programs="config.programs"
          :live-mode="liveMode"
          @toggle-live-dtw="toggleLiveDtw"
        />

        <!-- Home Assistant Bi-directional YAML Sync -->
        <YamlViewer
          :config="config"
          @update:config="config = $event"
        />
      </div>

      <!-- VIEW 2: Room Configuration -->
      <div v-else-if="currentProgram" class="flex flex-col gap-6">
        <!-- Room Configuration Header Card -->
        <div class="bg-slate-900/80 border border-slate-800 rounded-xl p-4 flex flex-col md:flex-row items-stretch md:items-start justify-between gap-6">
          <!-- Room Timing & General Settings -->
          <div class="flex items-center gap-4 flex-wrap shrink-0">
            <div>
              <label class="text-[11px] font-semibold text-slate-400 block uppercase tracking-wider">Room Name</label>
              <input
                v-model="currentProgram.name"
                class="bg-slate-950 border border-slate-700 text-slate-100 font-bold rounded px-2.5 py-1 text-sm focus:border-indigo-500 focus:outline-none"
              />
            </div>

            <div>
              <label class="text-[11px] font-semibold text-slate-400 block uppercase tracking-wider">Transition Time</label>
              <div class="flex items-center gap-1">
                <input
                  type="number"
                  v-model.number="currentProgram.transition_time"
                  class="w-16 bg-slate-950 border border-slate-700 text-slate-100 rounded px-2 py-1 text-xs font-mono focus:border-indigo-500 focus:outline-none"
                />
                <span class="text-xs text-slate-400">s</span>
              </div>
            </div>

            <div>
              <label class="text-[11px] font-semibold text-slate-400 block uppercase tracking-wider">Check Interval</label>
              <div class="flex items-center gap-1">
                <input
                  type="number"
                  v-model.number="currentProgram.transition_interval"
                  class="w-16 bg-slate-950 border border-slate-700 text-slate-100 rounded px-2 py-1 text-xs font-mono focus:border-indigo-500 focus:outline-none"
                />
                <span class="text-xs text-slate-400">s</span>
              </div>
            </div>
          </div>

          <!-- Room Fixtures Manager -->
          <div class="flex-1 min-w-[280px]">
            <RoomLightManager
              v-model="currentProgram.lights"
              :room-name="currentProgram.name"
              :curves="config.curves"
              @open-light-dtw="openContextualDtw"
            />
          </div>
        </div>

        <!-- 1. Interactive 24-Hour Circadian Timeline -->
        <CircadianTimeline
          :steps="currentProgram.schedule"
          :scrub-minutes="scrubMinutes"
          @update:steps="currentProgram.schedule = $event"
        />

        <!-- 2. Real-Time Scrub Simulator -->
        <ScrubSimulator
          v-model="scrubMinutes"
          v-model:room-brightness="liveRoomBrightness"
          :room-schedule-temp="currentInterpTemp"
          :light-ids="currentProgram.lights"
          :mock-lights="allLights"
          :brightness-curves="config.brightness_curves"
          :dim-to-warm-curves="config.curves"
          :live-mode="liveMode"
          @toggle-live-room="toggleLiveRoom"
          @open-light-dtw="openContextualDtw"
        />

        <!-- 3. Room Brightness Distribution Curves Editor -->
        <CurveEditor
          :brightness-curves="config.brightness_curves"
          :room-lights="currentProgram.lights"
          @open-global-dtw="activeView = 'dim_to_warm'"
          @update:preview-room-brightness="liveRoomBrightness = $event"
        />

        <!-- 4. Home Assistant Bi-directional YAML Sync -->
        <YamlViewer
          :config="config"
          @update:config="config = $event"
        />
      </div>
    </main>

    <!-- Contextual Quick-Edit Modal / Slide-over Drawer for Dim-to-Warm -->
    <div
      v-if="contextualLightId"
      class="fixed inset-0 bg-black/75 backdrop-blur-sm z-50 flex items-center justify-center p-4"
      @click.self="contextualLightId = null"
    >
      <DimToWarmManager
        mode="contextual"
        :focus-light-id="contextualLightId"
        :curves="config.curves"
        :programs="config.programs"
        :live-mode="liveMode"
        @toggle-live-dtw="toggleLiveDtw"
        @close="contextualLightId = null"
        @open-full-view="switchToGlobalDtw"
      />
    </div>

    <!-- Footer -->
    <footer class="border-t border-slate-900 bg-slate-950 p-6 text-center text-xs text-slate-500">
      ha-scheduled-scenes &bull; Standalone Web Studio &bull; Ready for Home Assistant Sidebar Panel integration
    </footer>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import type { LiveModeType, ScheduledScenesConfig } from './types'
import { INITIAL_CONFIG } from './mock/data'
import { entityService } from './services/entityService'
import { interpolateSchedule, calculateFixtureOutput } from './utils/interpolator'
import { liveOutputService } from './services/liveOutputService'
import CircadianTimeline from './components/CircadianTimeline.vue'
import ScrubSimulator from './components/ScrubSimulator.vue'
import CurveEditor from './components/CurveEditor.vue'
import YamlViewer from './components/YamlViewer.vue'
import RoomLightManager from './components/RoomLightManager.vue'
import DimToWarmManager from './components/DimToWarmManager.vue'

const config = ref<ScheduledScenesConfig>(JSON.parse(JSON.stringify(INITIAL_CONFIG)))
const activeView = ref<'room' | 'dim_to_warm'>('room')
const activeProgramIdx = ref(0)
const contextualLightId = ref<string | null>(null)
const liveMode = ref<LiveModeType>('off')

const allLights = computed(() => entityService.getAllLights())

const currentProgram = computed(() => {
  return config.value.programs[activeProgramIdx.value] || config.value.programs[0]
})

function selectRoom(idx: number) {
  activeProgramIdx.value = idx
  activeView.value = 'room'
}

function openContextualDtw(lightId: string) {
  contextualLightId.value = lightId
}

function switchToGlobalDtw() {
  contextualLightId.value = null
  activeView.value = 'dim_to_warm'
}

// Live Mode Toggles
async function toggleLiveRoom() {
  if (liveMode.value === 'room') {
    liveMode.value = 'off'
    await liveOutputService.stopLiveSession()
  } else {
    liveMode.value = 'room'
    await liveOutputService.startLiveSession(currentProgram.value?.name)
    dispatchRoomLiveOutputs()
  }
}

async function toggleLiveDtw() {
  if (liveMode.value === 'dim_to_warm') {
    liveMode.value = 'off'
    await liveOutputService.stopLiveSession()
  } else {
    liveMode.value = 'dim_to_warm'
    await liveOutputService.startLiveSession()
  }
}

// Scrub Simulator State
const scrubMinutes = ref(840) // 14:00 by default
const liveRoomBrightness = ref(70)

const currentInterp = computed(() => {
  if (!currentProgram.value) return { brightness: 50, temp: 2700 }
  return interpolateSchedule(currentProgram.value.schedule, scrubMinutes.value)
})

const currentInterpTemp = computed(() => currentInterp.value.temp)

// When scrubbing time, track schedule brightness automatically unless manually adjusted
watch(scrubMinutes, () => {
  liveRoomBrightness.value = currentInterp.value.brightness
})

// Dispatch room outputs when in 'room' live mode
function dispatchRoomLiveOutputs() {
  if (liveMode.value !== 'room' || !currentProgram.value) return

  const targets = currentProgram.value.lights.map((lightId) => {
    const out = calculateFixtureOutput({
      lightId,
      roomBrightness: liveRoomBrightness.value,
      scheduleTemp: currentInterpTemp.value,
      brightnessCurves: config.value.brightness_curves,
      dimToWarmCurves: config.value.curves,
    })
    return {
      entityId: lightId,
      brightnessPct: out.brightness,
      kelvin: out.temp,
    }
  })

  liveOutputService.syncFixtures(targets)
}

watch(
  [scrubMinutes, liveRoomBrightness, () => currentProgram.value?.lights, () => config.value.brightness_curves, () => config.value.curves],
  () => {
    if (liveMode.value === 'room') {
      dispatchRoomLiveOutputs()
    }
  },
  { deep: true }
)

function addNewProgram() {
  const name = prompt('Enter a name for the new room/program:', 'bedroom')
  if (!name) return

  const normalized = name.toLowerCase().replace(/[^a-z0-9]/g, '_')
  const matched = entityService.getLightsByArea(normalized)
  const defaultLights = matched.length > 0 ? matched.map((l) => l.entity_id) : []

  config.value.programs.push({
    name,
    lights: defaultLights,
    transition_time: 120,
    transition_interval: 60,
    schedule: [
      { id: 's1', time: '07:00', brightness: 30, temp: 2200 },
      { id: 's2', time: '09:00', brightness: 100, temp: 4000 },
      { id: 's3', time: '21:00', brightness: 40, temp: 2400 },
      { id: 's4', time: '23:00', brightness: 10, temp: 2000 },
    ],
  })

  activeProgramIdx.value = config.value.programs.length - 1
  activeView.value = 'room'
}
</script>
