<template>
  <div
    :class="[
      'bg-slate-900 border rounded-xl p-5 shadow-lg flex flex-col gap-4 transition-colors',
      liveMode === 'room' ? 'border-rose-500/70 shadow-rose-500/10' : 'border-slate-800',
    ]"
  >
    <!-- Header -->
    <div class="flex items-center justify-between flex-wrap gap-2">
      <div>
        <h3 class="text-base font-bold text-slate-100 flex items-center gap-2">
          <span
            :class="[
              'w-2.5 h-2.5 rounded-full',
              liveMode === 'room' ? 'bg-rose-500 animate-pulse' : 'bg-indigo-500',
            ]"
          ></span>
          <span>24-Hour Circadian Schedule Timeline</span>
          <span
            v-if="liveMode === 'room'"
            class="text-[10px] bg-rose-950/90 text-rose-300 border border-rose-700/70 px-2 py-0.5 rounded-full font-mono uppercase tracking-wider"
          >
            Live Timeline Sync
          </span>
        </h3>
        <p class="text-xs text-slate-400 mt-0.5">
          Click anywhere to add a checkpoint. Drag nodes to adjust time and brightness — playhead follows dragged checkpoints for live preview.
        </p>
      </div>

      <div class="flex items-center gap-2 flex-wrap">
        <button
          @click="addCheckpointAtCurrentTime"
          class="text-xs px-3 py-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 font-semibold text-white transition cursor-pointer flex items-center gap-1.5"
        >
          <span>+</span> Add Checkpoint
        </button>

        <button
          @click="showImportModal = true"
          class="text-xs px-2.5 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 font-semibold transition cursor-pointer flex items-center gap-1 border border-slate-700/60"
          title="Import schedule YAML into this room"
        >
          <span>📥 Import YAML</span>
        </button>

        <button
          @click="copyScheduleYaml"
          :class="[
            'text-xs px-2.5 py-1.5 rounded-lg font-semibold transition cursor-pointer flex items-center gap-1 border',
            copiedYaml
              ? 'bg-emerald-600 border-emerald-500 text-white'
              : 'bg-slate-800 hover:bg-slate-700 text-slate-200 border-slate-700/60',
          ]"
          title="Copy room schedule to clipboard as YAML"
        >
          <span>{{ copiedYaml ? '✓ Copied!' : '📋 Copy YAML' }}</span>
        </button>
      </div>
    </div>

    <!-- Interactive SVG Canvas Container -->
    <div class="relative select-none bg-slate-950/70 border border-slate-800/80 rounded-lg p-2">
      <svg
        ref="svgRef"
        :viewBox="`0 0 ${svgWidth} ${svgHeight}`"
        class="w-full h-48 sm:h-56 cursor-crosshair overflow-visible block touch-none select-none"
        @mousedown="onCanvasMouseDown"
      >
        <defs>
          <!-- Kelvin Gradient along the day -->
          <linearGradient id="timelineKelvinGrad" x1="0%" y1="0%" x2="100%" y2="0%">
            <stop
              v-for="(stop, idx) in kelvinGradientStops"
              :key="idx"
              :offset="stop.offset"
              :stop-color="stop.color"
            />
          </linearGradient>

          <!-- Area Glow -->
          <linearGradient id="timelineAreaGlow" x1="0%" y1="0%" x2="0%" y2="100%">
            <stop offset="0%" stop-color="#6366f1" stop-opacity="0.38" />
            <stop offset="100%" stop-color="#6366f1" stop-opacity="0.0" />
          </linearGradient>
        </defs>

        <!-- Horizontal Guide Lines (0%, 25%, 50%, 75%, 100%) -->
        <g stroke="rgba(255, 255, 255, 0.07)" stroke-dasharray="3 3">
          <line :x1="0" :y1="scaleY(100)" :x2="svgWidth" :y2="scaleY(100)" />
          <line :x1="0" :y1="scaleY(75)" :x2="svgWidth" :y2="scaleY(75)" />
          <line :x1="0" :y1="scaleY(50)" :x2="svgWidth" :y2="scaleY(50)" />
          <line :x1="0" :y1="scaleY(25)" :x2="svgWidth" :y2="scaleY(25)" />
          <line :x1="0" :y1="scaleY(0)" :x2="svgWidth" :y2="scaleY(0)" />
        </g>

        <!-- Vertical Hour Guide Lines every 3 hours -->
        <g stroke="rgba(255, 255, 255, 0.05)" stroke-dasharray="2 2">
          <line
            v-for="h in [3, 6, 9, 12, 15, 18, 21]"
            :key="h"
            :x1="scaleX(h * 60)"
            :y1="0"
            :x2="scaleX(h * 60)"
            :y2="canvasBottom"
          />
        </g>

        <!-- Filled Curve Path -->
        <path :d="areaPath" fill="url(#timelineAreaGlow)" />

        <!-- Line Curve Path -->
        <path :d="linePath" fill="none" stroke="#6366f1" stroke-width="2.5" />

        <g v-for="entry in seasonalRanges" :key="entry.id" stroke="#fbbf24" stroke-opacity="0.45" stroke-dasharray="2 3" pointer-events="none">
          <line :x1="scaleX(entry.range[0])" :x2="scaleX(entry.range[1])" :y1="scaleY(entry.brightness)" :y2="scaleY(entry.brightness)">
            <title>{{ entry.tooltip }}</title>
          </line>
        </g>

        <!-- Kelvin Bar at the bottom of the graph -->
        <rect
          :x="0"
          :y="canvasBottom + 6"
          :width="svgWidth"
          :height="10"
          rx="5"
          fill="url(#timelineKelvinGrad)"
        />

        <!-- Current Simulated Playhead indicator -->
        <line
          v-if="scrubMinutes !== null"
          :x1="scaleX(scrubMinutes)"
          :y1="4"
          :x2="scaleX(scrubMinutes)"
          :y2="canvasBottom + 16"
          stroke="#ffffff"
          stroke-width="2"
        />
        <circle
          v-if="scrubMinutes !== null"
          :cx="scaleX(scrubMinutes)"
          :cy="scaleY(interpolatedNow.brightness)"
          r="5"
          fill="#38bdf8"
          stroke="#ffffff"
          stroke-width="2"
        />

        <!-- Draggable Checkpoint Nodes -->
        <g v-for="step in sortedSteps" :key="step.id">
          <circle v-if="collisionIds.has(step.id)" :cx="scaleX(timeToMinutes(step.time))" :cy="scaleY(step.brightness)" r="13" fill="none" stroke="#fb7185" stroke-width="2" />
          <circle
            :cx="scaleX(timeToMinutes(step.time))"
            :cy="scaleY(step.brightness)"
            :r="hoveredStepId === step.id || selectedStepId === step.id ? 8 : 6"
            :fill="step.temp ? kelvinToCssColor(step.temp) : '#6366f1'"
            :stroke="selectedStepId === step.id || hoveredStepId === step.id ? '#ffffff' : '#0f172a'"
            :stroke-width="selectedStepId === step.id ? 3 : 2"
            class="cursor-grab active:cursor-grabbing"
            @mouseenter="hoveredStepId = step.id"
            @mouseleave="hoveredStepId = null"
            @mousedown.stop="onNodeMouseDown(step, $event)"
          />
          <circle v-if="step.dynamic" :cx="scaleX(timeToMinutes(step.time))" :cy="scaleY(step.brightness)" r="10" fill="none" stroke="#fbbf24" stroke-width="1.5" pointer-events="none" />
        </g>
      </svg>

      <!-- Timeline X-Axis Hour Labels -->
      <div class="flex justify-between text-[11px] text-slate-400 font-mono mt-2 px-1">
        <span>00:00</span>
        <span>03:00</span>
        <span>06:00</span>
        <span>09:00</span>
        <span>12:00</span>
        <span>15:00</span>
        <span>18:00</span>
        <span>21:00</span>
        <span>23:59</span>
      </div>

    </div>

    <!-- Selected Checkpoint Inspector / Quick Editor -->
    <div
      v-if="selectedStep"
      class="bg-slate-950/90 border border-slate-800 rounded-lg p-3.5 flex items-center justify-between flex-wrap gap-4"
    >
      <div v-if="selectedStep.dynamic" class="w-full rounded border border-amber-800/60 bg-amber-950/30 px-3 py-2 text-xs text-amber-100">
        <span>Resolved {{ selectedDynamicDetails?.time ?? 'Unavailable' }} for {{ simulationDateLabel }}.</span>
        <span v-if="selectedDynamicDetails?.range"> Yearly range: {{ selectedDynamicDetails.range }}.</span>
        <span v-if="collisionIds.has(selectedStep.id)" class="ml-2 text-rose-300">Collision: this point overlaps another checkpoint within one minute.</span>
      </div>
      <div class="flex items-center gap-3">
        <span
          class="w-5 h-5 rounded-full border border-white/40 shadow-inner"
          :style="{ backgroundColor: selectedStep.temp ? kelvinToCssColor(selectedStep.temp) : '#6366f1' }"
        ></span>
        <div class="text-xs">
          <span class="text-slate-400">Editing Checkpoint:</span>
          <span class="font-bold text-slate-200 ml-1 font-mono">{{ selectedStep.dynamic ? (selectedDynamicDetails?.time ?? 'Unavailable') : selectedStep.time }}</span>
        </div>
      </div>

      <div class="flex items-center gap-4 flex-wrap">
        <label class="flex items-center gap-2 text-xs font-semibold text-slate-400">Point:
          <select :value="selectedStep.dynamic ? 'dynamic' : 'fixed'" @change="setPointType(($event.target as HTMLSelectElement).value)" class="bg-slate-900 border border-slate-700 text-slate-200 rounded px-2 py-1">
            <option value="fixed">Fixed Time</option><option value="dynamic">Dynamic</option>
          </select>
        </label>
        <template v-if="selectedStep.dynamic">
          <label class="text-xs text-slate-400">Dynamic Source
            <select :value="selectedStep.dynamic.type" @change="setDynamicSource(($event.target as HTMLSelectElement).value)" class="bg-slate-900 border border-slate-700 text-slate-200 rounded px-2 py-1">
              <option v-for="provider in dynamicPointProviders" :key="provider.type" :value="provider.type" :disabled="!provider.enabled">{{ provider.label }}</option>
            </select>
          </label>
          <label class="text-xs text-slate-400">Sun event
            <select v-model="selectedStep.dynamic.event" @change="commitSelectedStep" class="bg-slate-900 border border-slate-700 text-slate-200 rounded px-2 py-1">
              <option value="sunrise">Sunrise</option><option value="sunset">Sunset</option><option value="solar_noon">Solar Noon</option><option value="solar_midnight">Solar Midnight</option><option value="dawn">Civil Dawn</option><option value="dusk">Civil Dusk</option><option value="elevation">Elevation Angle</option>
            </select>
          </label>
          <label v-if="selectedStep.dynamic.event === 'elevation'" class="text-xs text-slate-400">Angle ° <input type="number" min="-90" max="90" v-model.number="selectedStep.dynamic.elevation" @change="commitSelectedStep" class="w-16 bg-slate-900 border border-slate-700 rounded px-1 py-1 text-slate-200" /></label>
          <label v-if="selectedStep.dynamic.event === 'elevation'" class="text-xs text-slate-400">Direction
            <select v-model="selectedStep.dynamic.direction" @change="commitSelectedStep" class="bg-slate-900 border border-slate-700 text-slate-200 rounded px-2 py-1"><option value="rising">Rising</option><option value="setting">Setting</option></select>
          </label>
          <label class="text-xs text-slate-400">Offset <input type="number" v-model.number="selectedStep.dynamic.offset_value" @change="commitSelectedStep" class="w-16 bg-slate-900 border border-slate-700 rounded px-1 py-1 text-slate-200" /></label>
          <select v-model="selectedStep.dynamic.offset_unit" @change="commitSelectedStep" class="bg-slate-900 border border-slate-700 text-slate-200 rounded px-2 py-1 text-xs"><option value="time">Minutes</option><option value="angle">Degrees</option></select>
        </template>
        <!-- Time Input -->
        <div v-if="!selectedStep.dynamic" class="flex items-center gap-2">
          <label class="text-xs font-semibold text-slate-400">Time:</label>
          <input
            type="time"
            v-model="selectedStep.time"
            @input="syncScrubToSelectedStep"
            class="bg-slate-900 border border-slate-700 text-slate-200 rounded px-2 py-1 text-xs font-mono focus:border-indigo-500 focus:outline-none"
          />
        </div>

        <!-- Brightness Slider -->
        <div class="flex items-center gap-2">
          <label class="text-xs font-semibold text-slate-400">Brightness:</label>
          <input
            type="range"
            min="0"
            max="100"
            v-model.number="selectedStep.brightness"
            @input="syncScrubToSelectedStep"
            class="w-24 accent-indigo-500"
          />
          <span class="text-xs font-mono font-bold text-indigo-400 w-8">{{ selectedStep.brightness }}%</span>
        </div>

        <!-- Color Temperature Slider -->
        <div class="flex items-center gap-2">
          <label class="text-xs font-semibold text-slate-400">Kelvin:</label>
          <input
            type="range"
            min="2000"
            max="6500"
            step="50"
            v-model.number="selectedStep.temp"
            @input="syncScrubToSelectedStep"
            class="w-24 accent-amber-400"
          />
          <span class="text-xs font-mono font-bold text-amber-300 w-14">{{ selectedStep.temp }} K</span>
        </div>

        <!-- Delete Button -->
        <button
          v-if="steps.length > 2"
          @click="deleteStep(selectedStep.id)"
          class="text-xs text-rose-400 hover:text-rose-300 hover:bg-rose-950/40 px-2.5 py-1 rounded border border-rose-900/50 transition cursor-pointer"
        >
          Delete
        </button>
      </div>
    </div>

    <!-- Timeline Schedule Import Modal -->
    <div
      v-if="showImportModal"
      class="fixed inset-0 bg-black/75 backdrop-blur-sm z-50 flex items-center justify-center p-4"
      @click.self="closeImportModal"
      @keydown.esc="closeImportModal"
    >
      <div
        class="bg-slate-900 border border-slate-700 rounded-xl w-full max-w-xl p-5 shadow-2xl flex flex-col gap-4 text-slate-100"
        role="dialog"
        aria-modal="true"
        aria-labelledby="timeline-import-title"
      >
        <div class="flex justify-between items-center border-b border-slate-800 pb-3">
          <h4 id="timeline-import-title" class="text-sm font-bold text-white flex items-center gap-2">
            <span>📥 Import Circadian Schedule YAML</span>
          </h4>
          <button
            @click="closeImportModal"
            class="text-slate-400 hover:text-white text-lg cursor-pointer px-1 leading-none"
            title="Close modal"
          >
            &times;
          </button>
        </div>

        <p class="text-xs text-slate-400">
          Paste a Home Assistant <code>schedule:</code> YAML block, a list of steps, or JSON to update this room's circadian timeline:
        </p>

        <textarea
          v-model="importYamlText"
          rows="9"
          placeholder="schedule:
  - time: '06:30'
    brightness: 15
    temp: 2200
  - time: '09:00'
    brightness: 100
    temp: 5000"
          class="w-full bg-slate-950 border border-slate-800 text-slate-200 font-mono text-xs rounded-lg p-3 focus:outline-none focus:border-indigo-500"
          @input="validateImportInput"
        ></textarea>

        <!-- Error Banner -->
        <div
          v-if="importError"
          class="bg-rose-950/70 border border-rose-800 text-rose-300 text-xs px-3 py-2 rounded-lg flex items-center gap-2"
        >
          <span class="font-bold">⚠️</span>
          <span>{{ importError }}</span>
        </div>

        <!-- Success Preview Banner -->
        <div
          v-else-if="parsedPreviewSteps"
          class="bg-emerald-950/60 border border-emerald-800 text-emerald-300 text-xs px-3 py-2 rounded-lg flex items-center justify-between"
        >
          <span>✓ Ready to import {{ parsedPreviewSteps.length }} checkpoints ({{ parsedPreviewSteps[0].time }} – {{ parsedPreviewSteps[parsedPreviewSteps.length - 1].time }})</span>
        </div>

        <div class="flex justify-end items-center gap-2 pt-2 border-t border-slate-800">
          <button
            @click="closeImportModal"
            class="text-xs px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 transition cursor-pointer"
          >
            Cancel
          </button>
          <button
            @click="applyImportedSchedule"
            :disabled="!parsedPreviewSteps"
            :class="[
              'text-xs px-4 py-1.5 rounded-lg font-semibold transition',
              parsedPreviewSteps
                ? 'bg-indigo-600 hover:bg-indigo-500 text-white cursor-pointer shadow-md shadow-indigo-600/30'
                : 'bg-slate-800 text-slate-500 cursor-not-allowed',
            ]"
          >
            Apply to Room
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import type { LiveModeType, ScheduleStep } from '../types'
import {
  timeToMinutes,
  minutesToTime,
  interpolateSchedule,
} from '../utils/interpolator'
import { resolveSunPoint, yearlyVariation } from '../utils/solar'
import { kelvinToCssColor } from '../utils/color'
import { getSvgCoordinates } from '../utils/svg'
import {
  serializeScheduleYaml,
  parseScheduleYaml,
  copyToClipboard,
} from '../utils/curveYaml'

const props = defineProps<{
  steps: ScheduleStep[]
  scrubMinutes: number | null
  liveMode?: LiveModeType
  latitude?: number
  longitude?: number
  simulationDate?: string
  resolvedSteps?: ScheduleStep[]
}>()

const emit = defineEmits<{
  (e: 'update:steps', steps: ScheduleStep[]): void
  (e: 'update:scrubMinutes', minutes: number): void
  (e: 'selectStep', step: ScheduleStep): void
}>()

const svgWidth = ref(800)
const svgHeight = ref(200)
const CANVAS_TOP = 16
const canvasBottom = computed(() => Math.max(40, svgHeight.value - 26))

const svgRef = ref<SVGSVGElement | null>(null)
const selectedStepId = ref<string | null>(props.steps[0]?.id || null)
const hoveredStepId = ref<string | null>(null)
const draggingStepId = ref<string | null>(null)

// YAML Copy & Import state
const copiedYaml = ref(false)
const showImportModal = ref(false)
const importYamlText = ref('')
const importError = ref<string | null>(null)
const parsedPreviewSteps = ref<ScheduleStep[] | null>(null)

async function copyScheduleYaml() {
  const yaml = serializeScheduleYaml(props.steps)
  const ok = await copyToClipboard(yaml)
  if (ok) {
    copiedYaml.value = true
    setTimeout(() => {
      copiedYaml.value = false
    }, 2000)
  }
}

function validateImportInput() {
  if (!importYamlText.value.trim()) {
    importError.value = null
    parsedPreviewSteps.value = null
    return
  }

  const res = parseScheduleYaml(importYamlText.value)
  if (res.success && res.data) {
    parsedPreviewSteps.value = res.data
    importError.value = null
  } else {
    parsedPreviewSteps.value = null
    importError.value = res.error || 'Failed to parse YAML.'
  }
}

function applyImportedSchedule() {
  if (!parsedPreviewSteps.value || parsedPreviewSteps.value.length === 0) return
  emit('update:steps', parsedPreviewSteps.value)
  selectedStepId.value = parsedPreviewSteps.value[0]?.id || null
  closeImportModal()
}

function closeImportModal() {
  showImportModal.value = false
  importYamlText.value = ''
  importError.value = null
  parsedPreviewSteps.value = null
}

let resizeObserver: ResizeObserver | null = null

function updateSvgDimensions() {
  if (!svgRef.value) return
  const rect = svgRef.value.getBoundingClientRect()
  if (rect.width > 0 && rect.height > 0) {
    svgWidth.value = Math.round(rect.width)
    svgHeight.value = Math.round(rect.height)
  }
}

onMounted(() => {
  updateSvgDimensions()
  if (typeof ResizeObserver !== 'undefined' && svgRef.value) {
    resizeObserver = new ResizeObserver(() => {
      updateSvgDimensions()
    })
    resizeObserver.observe(svgRef.value)
  }
})

const selectedStep = computed(() => {
  return props.steps.find((s) => s.id === selectedStepId.value)
})

function syncScrubToSelectedStep() {
  if (selectedStep.value) {
    emit('update:scrubMinutes', timeToMinutes(selectedStep.value.time))
  }
}

function setPointType(type: string) {
  if (!selectedStep.value) return
  if (type === 'dynamic') selectedStep.value.dynamic = selectedStep.value.dynamic ?? { type: 'sun', event: 'sunrise', offset_value: 0, offset_unit: 'time' }
  else selectedStep.value.dynamic = undefined
  commitSelectedStep()
}

const dynamicPointProviders = [
  { type: 'sun', label: 'Sun', enabled: true },
  { type: 'sensor', label: 'Ambient Sensor (coming later)', enabled: false },
] as const

function setDynamicSource(source: string) {
  if (!selectedStep.value?.dynamic || source !== 'sun') return
  selectedStep.value.dynamic.type = 'sun'
  commitSelectedStep()
}

function commitSelectedStep() {
  if (!selectedStep.value) return
  emit('update:steps', props.steps.map(step => step.id === selectedStep.value?.id
    ? { ...step, dynamic: step.dynamic ? { ...step.dynamic } : undefined }
    : step))
}

function scaleX(minutes: number): number {
  return (minutes / 1440) * svgWidth.value
}

function scaleY(brightness: number): number {
  return canvasBottom.value - (brightness / 100) * (canvasBottom.value - CANVAS_TOP)
}

function unscaleX(x: number): number {
  return Math.max(0, Math.min(1439, Math.round((x / svgWidth.value) * 1440)))
}

function unscaleY(y: number): number {
  const normalized = (canvasBottom.value - y) / (canvasBottom.value - CANVAS_TOP)
  return Math.max(0, Math.min(100, Math.round(normalized * 100)))
}

const sortedSteps = computed(() => {
  return [...(props.resolvedSteps ?? props.steps)].sort((a, b) => timeToMinutes(a.time) - timeToMinutes(b.time))
})

const seasonalRanges = computed(() => props.steps.flatMap(step => {
  if (!step.dynamic) return []
  const year = Number(props.simulationDate?.slice(0, 4)) || new Date().getFullYear()
  const range = yearlyVariation(step.dynamic, new Date(year, 0, 1), props.latitude ?? 0, props.longitude ?? 0)
  const event = step.dynamic.event ?? 'sunrise'
  const angle = step.dynamic.elevation === undefined ? '' : ` at ${step.dynamic.elevation}° ${step.dynamic.direction ?? 'rising'}`
  const tooltip = `${event}${angle} · ${props.latitude ?? 0}°, ${props.longitude ?? 0}° · yearly range ${minutesToTime(range?.[0] ?? 0)}–${minutesToTime(range?.[1] ?? 0)}`
  return range ? [{ id: step.id, range, brightness: step.brightness, tooltip }] : []
}))

const collisionIds = computed(() => {
  const date = new Date(`${props.simulationDate ?? new Date().toISOString().slice(0, 10)}T12:00:00`)
  const candidates = props.steps.map(step => {
    const raw = step.dynamic?.type === 'sun' ? resolveSunPoint(step.dynamic, date, props.latitude ?? 0, props.longitude ?? 0) : null
    const minute = raw === null ? timeToMinutes(step.time) : ((raw - date.getTimezoneOffset()) % 1440 + 1440) % 1440
    return { id: step.id, minute }
  })
  const ids = new Set<string>()
  for (let i = 0; i < candidates.length; i++) for (let j = i + 1; j < candidates.length; j++) {
    const delta = Math.abs(candidates[i].minute - candidates[j].minute)
    if (Math.min(delta, 1440 - delta) <= 1) { ids.add(candidates[i].id); ids.add(candidates[j].id) }
  }
  return ids
})

const simulationDateLabel = computed(() => props.simulationDate ?? new Date().toISOString().slice(0, 10))
const selectedDynamicDetails = computed(() => {
  const step = selectedStep.value
  if (!step?.dynamic) return null
  const date = new Date(`${simulationDateLabel.value}T12:00:00`)
  const resolved = resolveSunPoint(step.dynamic, date, props.latitude ?? 0, props.longitude ?? 0)
  const local = resolved === null ? null : ((resolved - date.getTimezoneOffset()) % 1440 + 1440) % 1440
  const range = yearlyVariation(step.dynamic, date, props.latitude ?? 0, props.longitude ?? 0)
  return { time: local === null ? null : minutesToTime(local), range: range ? `${minutesToTime(range[0])}–${minutesToTime(range[1])}` : null }
})

const interpolatedNow = computed(() => {
  return interpolateSchedule(sortedSteps.value, props.scrubMinutes ?? 720)
})

// Build SVG paths with seamless 24h midnight continuity
const linePath = computed(() => {
  const list = sortedSteps.value
  if (!list.length) return ''
  if (list.length === 1) {
    const y = scaleY(list[0].brightness)
    return `M 0,${y} L ${svgWidth.value},${y}`
  }

  const pStart = interpolateSchedule(sortedSteps.value, 0)
  const pEnd = interpolateSchedule(sortedSteps.value, 1440)

  let d = `M 0,${scaleY(pStart.brightness)}`
  for (const step of list) {
    d += ` L ${scaleX(timeToMinutes(step.time))},${scaleY(step.brightness)}`
  }
  d += ` L ${svgWidth.value},${scaleY(pEnd.brightness)}`
  return d
})

const areaPath = computed(() => {
  const line = linePath.value
  if (!line) return ''
  return `${line} L ${svgWidth.value},${canvasBottom.value} L 0,${canvasBottom.value} Z`
})

const kelvinGradientStops = computed(() => {
  const stops: { offset: string; color: string }[] = []
  const samples = 12
  for (let i = 0; i <= samples; i++) {
    const m = (i / samples) * 1440
    const interp = interpolateSchedule(sortedSteps.value, m)
    stops.push({
      offset: `${((i / samples) * 100).toFixed(1)}%`,
      color: kelvinToCssColor(interp.temp),
    })
  }
  return stops
})

function onNodeMouseDown(step: ScheduleStep, e: MouseEvent) {
  e.preventDefault()
  selectedStepId.value = step.id
  draggingStepId.value = step.id
  emit('selectStep', step)
  emit('update:scrubMinutes', timeToMinutes(step.time))

  if (step.dynamic) {
    draggingStepId.value = null
    return
  }

  window.addEventListener('mousemove', onWindowMouseMove)
  window.addEventListener('mouseup', onWindowMouseUp)
}

function onCanvasMouseDown(e: MouseEvent) {
  if (!svgRef.value) return
  const coords = getSvgCoordinates(svgRef.value, e)
  const min = unscaleX(coords.x)
  const bri = unscaleY(coords.y)

  const toleranceMin = 20
  const existing = props.steps.find((s) => Math.abs(timeToMinutes(s.time) - min) < toleranceMin)

  if (existing) {
    selectedStepId.value = existing.id
    emit('update:scrubMinutes', timeToMinutes(existing.time))
  } else {
    const newStep: ScheduleStep = {
      id: `step-${Date.now()}`,
      time: minutesToTime(min),
      brightness: bri,
      temp: interpolateSchedule(props.steps, min).temp,
    }
    const updated = [...props.steps, newStep]
    emit('update:steps', updated)
    selectedStepId.value = newStep.id
    draggingStepId.value = newStep.id
    emit('update:scrubMinutes', min)

    window.addEventListener('mousemove', onWindowMouseMove)
    window.addEventListener('mouseup', onWindowMouseUp)
  }
}

function onWindowMouseMove(e: MouseEvent) {
  if (!draggingStepId.value || !svgRef.value) return

  const coords = getSvgCoordinates(svgRef.value, e)
  const newMin = unscaleX(coords.x)
  const newBri = unscaleY(coords.y)

  const step = props.steps.find((s) => s.id === draggingStepId.value)
  if (step) {
    step.time = minutesToTime(newMin)
    step.brightness = newBri
    emit('update:scrubMinutes', newMin)
  }
}

function onWindowMouseUp() {
  draggingStepId.value = null
  window.removeEventListener('mousemove', onWindowMouseMove)
  window.removeEventListener('mouseup', onWindowMouseUp)
}

onUnmounted(() => {
  if (resizeObserver) {
    resizeObserver.disconnect()
  }
  window.removeEventListener('mousemove', onWindowMouseMove)
  window.removeEventListener('mouseup', onWindowMouseUp)
})

function addCheckpointAtCurrentTime() {
  const min = props.scrubMinutes ?? 720
  const interp = interpolateSchedule(props.steps, min)
  const newStep: ScheduleStep = {
    id: `step-${Date.now()}`,
    time: minutesToTime(min),
    brightness: interp.brightness,
    temp: interp.temp,
  }
  emit('update:steps', [...props.steps, newStep])
  selectedStepId.value = newStep.id
}

function deleteStep(id: string) {
  if (props.steps.length <= 2) return
  const filtered = props.steps.filter((s) => s.id !== id)
  emit('update:steps', filtered)
  selectedStepId.value = filtered[0]?.id || null
}
</script>
