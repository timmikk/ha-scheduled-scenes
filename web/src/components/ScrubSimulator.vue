<template>
  <div
    :class="[
      'bg-slate-900 border rounded-xl p-5 shadow-lg flex flex-col gap-4 transition-colors',
      liveMode === 'room' ? 'border-rose-500/70 shadow-rose-500/10' : 'border-slate-800',
    ]"
  >
    <!-- Header -->
    <div class="flex items-center justify-between flex-wrap gap-3">
      <div>
        <h3 class="text-base font-bold text-slate-100 flex items-center gap-2">
          <span
            :class="[
              'w-2.5 h-2.5 rounded-full animate-pulse',
              liveMode === 'room' ? 'bg-rose-500' : 'bg-emerald-500',
            ]"
          ></span>
          <span>Real-Time Scrubbing &amp; Room Simulator</span>
          <span
            v-if="liveMode === 'room'"
            class="text-[10px] bg-rose-950/90 text-rose-300 border border-rose-700/70 px-2 py-0.5 rounded-full font-mono uppercase tracking-wider"
          >
            Live Hardware Sync Active
          </span>
        </h3>
        <p class="text-xs text-slate-400 mt-0.5">
          Simulate 24h schedule transitions and room brightness overrides. Enable Live Room Mode to drive physical lights in real time.
        </p>
      </div>

      <div class="flex items-center gap-2 flex-wrap">
        <!-- Play 24h Cycle Button -->
        <button
          @click="togglePlay"
          :class="[
            'text-xs font-semibold px-3 py-1.5 rounded-lg transition cursor-pointer flex items-center gap-1.5',
            isPlaying ? 'bg-amber-600 hover:bg-amber-500 text-white' : 'bg-slate-800 hover:bg-slate-700 text-slate-200',
          ]"
        >
          <span>{{ isPlaying ? '⏸ Pause 24h Cycle' : '▶ Play 24h Cycle' }}</span>
        </button>

        <!-- Timeline / Room Curve Live Mode Toggle -->
        <button
          @click="$emit('toggleLiveRoom')"
          :class="[
            'text-xs font-semibold px-3.5 py-1.5 rounded-lg transition cursor-pointer flex items-center gap-2 border',
            liveMode === 'room'
              ? 'bg-rose-600 hover:bg-rose-500 text-white border-rose-400 shadow-md shadow-rose-600/25'
              : 'bg-slate-950 hover:bg-slate-800 text-slate-200 border-slate-700',
          ]"
        >
          <span
            :class="[
              'w-2 h-2 rounded-full',
              liveMode === 'room' ? 'bg-white animate-ping' : 'bg-rose-500',
            ]"
          ></span>
          <span>
            {{ liveMode === 'room' ? 'Stop Room Live Mode' : 'Live Mode: Timeline & Room Curves' }}
          </span>
        </button>
      </div>
    </div>

    <!-- Live Mode Active Telemetry Banner -->
    <div
      v-if="liveMode === 'room'"
      class="bg-rose-950/30 border border-rose-800/50 rounded-lg px-3.5 py-2 flex items-center justify-between flex-wrap gap-2 text-xs"
    >
      <div class="flex items-center gap-2 text-rose-200">
        <span class="font-semibold">⚡ Room Live Mode Active:</span>
        <span class="text-rose-300/90">
          Physical fixtures in this room mirror the timeline and room brightness curves below.
        </span>
      </div>
      <div v-if="lastCommandLog" class="font-mono text-[11px] text-rose-300 bg-rose-950/70 px-2 py-0.5 rounded border border-rose-800/60">
        [{{ lastCommandLog.time }}] {{ lastCommandLog.summary }}
      </div>
    </div>

    <!-- Notice if Dim-to-Warm Calibration Live Mode is currently active instead -->
    <div
      v-else-if="liveMode === 'dim_to_warm'"
      class="bg-amber-950/30 border border-amber-800/50 rounded-lg px-3.5 py-2 flex items-center justify-between flex-wrap gap-2 text-xs text-amber-200"
    >
      <span>
        🟠 <strong>Dim-to-Warm Calibration Live Mode</strong> is currently driving curve fixtures. Switching to Room Live Mode will pause Dim-to-Warm calibration.
      </span>
      <button
        @click="$emit('toggleLiveRoom')"
        class="text-[11px] font-semibold bg-amber-600/80 hover:bg-amber-500 text-white px-2.5 py-1 rounded cursor-pointer transition"
      >
        Switch to Room Live Mode
      </button>
    </div>

    <!-- Controls Row -->
    <div class="grid grid-cols-1 md:grid-cols-2 gap-4 bg-slate-950/70 border border-slate-800/80 rounded-lg p-3.5">
      <!-- Time Scrubber -->
      <div class="flex flex-col gap-1.5">
        <div class="flex justify-between items-center text-xs">
          <span class="font-semibold text-slate-300">⏰ Scrub Time of Day:</span>
          <span class="font-mono font-bold text-indigo-400 text-sm">{{ formattedTime }}</span>
        </div>
        <input
          type="range"
          min="0"
          max="1439"
          :value="modelValue"
          @input="$emit('update:modelValue', Number(($event.target as HTMLInputElement).value))"
          class="accent-indigo-500 cursor-pointer"
        />
        <div class="flex justify-between text-[10px] text-slate-500 font-mono">
          <span>00:00 (Night)</span>
          <span>06:00 (Dawn)</span>
          <span>12:00 (Noon)</span>
          <span>18:00 (Dusk)</span>
          <span>23:59</span>
        </div>
      </div>

      <!-- Room Brightness Override -->
      <div class="flex flex-col gap-1.5">
        <div class="flex justify-between items-center text-xs">
          <span class="font-semibold text-slate-300">🔆 Room Target Brightness:</span>
          <span class="font-mono font-bold text-amber-400 text-sm">{{ roomBrightness }}%</span>
        </div>
        <input
          type="range"
          min="0"
          max="100"
          :value="roomBrightness"
          @input="$emit('update:roomBrightness', Number(($event.target as HTMLInputElement).value))"
          class="accent-amber-400 cursor-pointer"
        />
        <div class="flex justify-between text-[10px] text-slate-500 font-mono">
          <span>0% (Off)</span>
          <span>25%</span>
          <span>50%</span>
          <span>75%</span>
          <span>100% (Max)</span>
        </div>
      </div>
    </div>

    <!-- Active Fixtures Grid -->
    <div class="flex flex-col gap-2">
      <div class="flex items-center justify-between">
        <span class="text-xs font-semibold text-slate-400">Calculated Physical Light States:</span>
        <span v-if="liveMode === 'room'" class="text-[11px] font-mono text-rose-400">
          Syncing {{ fixturesComputed.length }} fixture(s) to Home Assistant
        </span>
      </div>

      <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
        <div
          v-for="fix in fixturesComputed"
          :key="fix.lightId"
          :class="[
            'bg-slate-950/90 border rounded-lg p-3 flex flex-col gap-2 shadow-sm transition-colors',
            liveMode === 'room' ? 'border-rose-500/40' : 'border-slate-800',
          ]"
        >
          <!-- Fixture Title & Curve Badge -->
          <div class="flex items-start justify-between gap-2">
            <div>
              <div class="text-xs font-bold text-slate-200 flex items-center gap-1.5">
                <span>{{ fix.friendlyName }}</span>
                <span
                  v-if="liveMode === 'room' && fix.liveState"
                  class="text-[9px] bg-rose-950 text-rose-300 border border-rose-700/70 px-1.5 py-0.2 rounded font-mono uppercase"
                  title="Real light is receiving live commands"
                >
                  LIVE
                </span>
              </div>
              <div class="text-[11px] font-mono text-slate-500">{{ fix.lightId }}</div>
            </div>
            <div class="flex flex-col items-end gap-1">
              <span
                v-if="fix.brightnessCurveName"
                class="text-[10px] bg-indigo-950/80 text-indigo-300 border border-indigo-800/60 px-1.5 py-0.5 rounded font-mono"
              >
                {{ fix.brightnessCurveName }}
              </span>
              <!-- Interactive Dim-to-Warm Badge Button -->
              <button
                v-if="fix.dimToWarmCurveName"
                type="button"
                @click="$emit('openLightDtw', fix.lightId)"
                class="text-[10px] bg-amber-950/80 hover:bg-amber-900 border border-amber-800/60 hover:border-amber-400 text-amber-300 px-1.5 py-0.5 rounded font-mono transition cursor-pointer flex items-center gap-1 shadow-sm"
                title="Edit Dim-to-Warm curve for this light"
              >
                <span>🌡️</span>
                <span>{{ fix.dimToWarmCurveName }}</span>
              </button>
              <button
                v-else
                type="button"
                @click="$emit('openLightDtw', fix.lightId)"
                class="text-[10px] text-slate-500 hover:text-amber-400 border border-slate-800 hover:border-slate-700 px-1.5 py-0.5 rounded font-mono transition cursor-pointer"
                title="Assign Dim-to-Warm curve to this light"
              >
                + DTW
              </button>
            </div>
          </div>

          <!-- Color Swatch & Output Level Bar -->
          <div class="flex items-center gap-2 mt-1">
            <div
              class="w-6 h-6 rounded border border-white/20 shadow-sm shrink-0 transition-colors duration-150"
              :style="{ backgroundColor: fix.swatchColor }"
            ></div>
            <div class="flex-1 flex flex-col gap-1">
              <div class="flex justify-between text-[11px] font-mono">
                <span class="text-slate-400">Output:</span>
                <span class="font-bold text-slate-200">{{ fix.brightness }}%</span>
              </div>
              <div class="w-full bg-slate-800 h-1.5 rounded-full overflow-hidden">
                <div
                  class="bg-indigo-500 h-full transition-all duration-150"
                  :style="{ width: `${fix.brightness}%` }"
                ></div>
              </div>
            </div>
          </div>

          <!-- Color Temperature Stat -->
          <div class="flex justify-between text-[11px] text-slate-400 font-mono pt-1 border-t border-slate-800/60">
            <span>Color Temp:</span>
            <span class="font-bold text-amber-300">
              {{ fix.supportsKelvin ? `${fix.temp} K` : 'Fixed / Dimmable Only' }}
            </span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onUnmounted } from 'vue'
import type { BrightnessCurve, DimToWarmCurve, LiveModeType, MockLight } from '../types'
import {
  minutesToTime,
  calculateFixtureOutput,
} from '../utils/interpolator'
import { kelvinToCssColor } from '../utils/color'
import { liveOutputService } from '../services/liveOutputService'

const props = defineProps<{
  modelValue: number // minutes of day (0-1439)
  roomBrightness: number // 0-100
  roomScheduleTemp: number // current schedule temp
  lightIds: string[]
  mockLights: MockLight[]
  brightnessCurves: Record<string, BrightnessCurve>
  dimToWarmCurves: Record<string, DimToWarmCurve>
  liveMode: LiveModeType
}>()

const emit = defineEmits<{
  (e: 'update:modelValue', value: number): void
  (e: 'update:roomBrightness', value: number): void
  (e: 'toggleLiveRoom'): void
  (e: 'openLightDtw', lightId: string): void
}>()

const formattedTime = computed(() => minutesToTime(props.modelValue))
const lastCommandLog = computed(() => liveOutputService.lastCommandLog.value)

const isPlaying = ref(false)
let playTimer: ReturnType<typeof setInterval> | null = null

function togglePlay() {
  if (isPlaying.value) {
    if (playTimer) clearInterval(playTimer)
    isPlaying.value = false
  } else {
    isPlaying.value = true
    playTimer = setInterval(() => {
      const next = (props.modelValue + 5) % 1440
      emit('update:modelValue', next)
    }, 50)
  }
}

onUnmounted(() => {
  if (playTimer) clearInterval(playTimer)
})

const fixturesComputed = computed(() => {
  return props.lightIds.map((lightId) => {
    const meta = props.mockLights.find((l) => l.entity_id === lightId)
    const friendlyName = meta?.name || lightId.replace('light.', '')
    const supportsKelvin =
      !meta?.supported_color_modes || meta.supported_color_modes.includes('color_temp')

    const out = calculateFixtureOutput({
      lightId,
      roomBrightness: props.roomBrightness,
      scheduleTemp: props.roomScheduleTemp,
      brightnessCurves: props.brightnessCurves,
      dimToWarmCurves: props.dimToWarmCurves,
    })

    const bCurve = Object.values(props.brightnessCurves).find((c) =>
      c.lights.includes(lightId)
    )
    const dtwCurve = Object.values(props.dimToWarmCurves).find((c) =>
      c.lights.includes(lightId)
    )

    return {
      lightId,
      friendlyName,
      brightness: out.brightness,
      temp: out.temp,
      supportsKelvin,
      swatchColor: kelvinToCssColor(out.temp, out.brightness > 0 ? 1 : 0.2),
      brightnessCurveName: bCurve?.name,
      dimToWarmCurveName: dtwCurve?.name,
      liveState: liveOutputService.liveStates[lightId] || null,
    }
  })
})
</script>
