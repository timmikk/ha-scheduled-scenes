<template>
  <div class="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-lg flex flex-col gap-4">
    <!-- Header with curve type selection & dropdown -->
    <div class="flex items-center justify-between flex-wrap gap-3 border-b border-slate-800/80 pb-3">
      <div class="flex items-center gap-2">
        <span class="text-xs font-bold text-slate-200 uppercase tracking-wider flex items-center gap-1.5">
          <span>📈 Room Brightness Distribution Curves</span>
        </span>
      </div>

      <!-- Curve Selector Dropdown & Toolbar Actions -->
      <div class="flex items-center gap-2 flex-wrap">
        <select
          v-model="selectedCurveName"
          class="bg-slate-950 border border-slate-700 text-slate-200 rounded-lg px-2.5 py-1 text-xs font-medium focus:border-indigo-500 focus:outline-none"
        >
          <option v-for="name in curveNames" :key="name" :value="name">
            {{ name }}
          </option>
        </select>

        <button
          @click="createNewCurve"
          class="text-xs px-2.5 py-1 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 font-medium transition cursor-pointer"
        >
          + New Curve
        </button>

        <button
          @click="showImportModal = true"
          class="text-xs px-2.5 py-1 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 font-medium transition cursor-pointer flex items-center gap-1 border border-slate-700/60"
          title="Import brightness curve YAML"
        >
          <span>📥 Import YAML</span>
        </button>

        <button
          @click="copyCurveYaml"
          :class="[
            'text-xs px-2.5 py-1 rounded-lg font-medium transition cursor-pointer flex items-center gap-1 border',
            copiedYaml
              ? 'bg-emerald-600 border-emerald-500 text-white'
              : 'bg-slate-800 hover:bg-slate-700 text-slate-200 border-slate-700/60',
          ]"
          title="Copy active curve points as YAML"
        >
          <span>{{ copiedYaml ? '✓ Copied!' : '📋 Copy YAML' }}</span>
        </button>

        <button
          @click="$emit('openGlobalDtw')"
          class="text-xs px-2.5 py-1 rounded-lg bg-amber-950/70 hover:bg-amber-900/80 border border-amber-800/80 text-amber-300 font-medium transition cursor-pointer flex items-center gap-1"
          title="Open Global Dim-to-Warm Curves manager"
        >
          <span>🌡️ Dim-to-Warm Curves &rarr;</span>
        </button>
      </div>
    </div>

    <!-- Active Curve Details -->
    <div v-if="activeCurve" class="flex flex-col gap-4">
      <div class="flex items-center justify-between text-xs text-slate-400 flex-wrap gap-2">
        <div class="flex items-center gap-2 flex-wrap">
          <!-- Active curve name or inline rename input -->
          <div v-if="!isRenaming" class="flex items-center gap-1.5">
            <span class="font-bold text-slate-200 font-mono">{{ activeCurve.name }}</span>
            <button
              @click="startRename"
              class="text-[11px] px-1.5 py-0.5 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white border border-slate-700 hover:border-slate-600 transition cursor-pointer flex items-center gap-1"
              title="Rename curve"
            >
              <span>✎</span>
              <span>Rename</span>
            </button>
          </div>
          <div v-else class="flex items-center gap-1.5 flex-wrap">
            <div class="flex items-center gap-1">
              <input
                ref="renameInputRef"
                v-model="renameInput"
                type="text"
                placeholder="Curve name"
                class="bg-slate-950 border border-indigo-500 text-slate-100 font-mono rounded px-2 py-0.5 text-xs focus:outline-none w-36 sm:w-48"
                @keydown.enter="confirmRename"
                @keydown.esc="cancelRename"
              />
              <button
                @click="confirmRename"
                class="px-2 py-0.5 rounded bg-emerald-600 hover:bg-emerald-500 text-white text-[11px] font-bold cursor-pointer"
                title="Save new name"
              >
                ✓
              </button>
              <button
                @click="cancelRename"
                class="px-2 py-0.5 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 text-[11px] cursor-pointer"
                title="Cancel renaming"
              >
                ✕
              </button>
            </div>
            <span v-if="renameError" class="text-rose-400 text-[11px] font-medium">
              {{ renameError }}
            </span>
          </div>

          <span class="text-slate-400">applied to room fixtures:</span>
          <span
            v-for="lt in activeCurve.lights"
            :key="lt"
            class="inline-flex items-center gap-1 bg-slate-800 text-indigo-300 px-1.5 py-0.5 rounded text-[11px] font-mono"
          >
            <span>{{ getLightName(lt) }}</span>
            <button
              @click="detachLight(lt)"
              class="text-slate-500 hover:text-rose-400 cursor-pointer text-xs"
              title="Remove fixture from curve"
            >
              &times;
            </button>
          </span>
          <div class="relative inline-block" v-if="unassignedRoomLights.length > 0">
            <button
              @click="showAssignLightMenu = !showAssignLightMenu"
              class="text-[11px] bg-slate-800 hover:bg-slate-700 text-slate-300 px-1.5 py-0.5 rounded border border-slate-700 cursor-pointer"
            >
              + Attach Room Light
            </button>
            <div
              v-if="showAssignLightMenu"
              class="absolute left-0 top-full mt-1 bg-slate-950 border border-slate-700 rounded shadow-xl py-1 z-30 min-w-[160px]"
            >
              <button
                v-for="lt in unassignedRoomLights"
                :key="lt"
                @click="attachLight(lt)"
                class="w-full text-left px-3 py-1 text-xs text-slate-200 hover:bg-slate-800 font-mono block cursor-pointer"
              >
                {{ getLightName(lt) }}
              </button>
            </div>
          </div>
        </div>

        <div class="text-[11px] text-slate-500">
          Click canvas to add point. Double-click point to delete.
        </div>
      </div>

      <!-- 2D Coordinate SVG Graph Canvas -->
      <div class="relative select-none bg-slate-950/70 border border-slate-800/80 rounded-lg p-2">
        <svg
          ref="svgRef"
          :viewBox="`0 0 ${svgWidth} ${svgHeight}`"
          class="w-full h-48 sm:h-64 cursor-crosshair overflow-visible block touch-none select-none"
          @mousedown="onCanvasMouseDown"
        >
          <defs>
            <linearGradient id="curveGradient" x1="0%" y1="0%" x2="0%" y2="100%">
              <stop offset="0%" stop-color="#6366f1" stop-opacity="0.35" />
              <stop offset="100%" stop-color="#6366f1" stop-opacity="0.0" />
            </linearGradient>
          </defs>

          <!-- Graph Grid Lines -->
          <g stroke="rgba(255, 255, 255, 0.07)" stroke-dasharray="3 3">
            <line
              v-for="step in [0, 25, 50, 75, 100]"
              :key="`h-${step}`"
              :x1="PAD_X"
              :y1="scaleY(step)"
              :x2="svgWidth - PAD_X"
              :y2="scaleY(step)"
            />
            <line
              v-for="step in [0, 25, 50, 75, 100]"
              :key="`v-${step}`"
              :x1="scaleX(step)"
              :y1="PAD_Y"
              :x2="scaleX(step)"
              :y2="svgHeight - PAD_Y"
            />
          </g>

          <!-- Linear Identity Reference Line (0,0 -> 100,100) -->
          <line
            :x1="scaleX(0)"
            :y1="scaleY(0)"
            :x2="scaleX(100)"
            :y2="scaleY(100)"
            stroke="rgba(255, 255, 255, 0.15)"
            stroke-dasharray="4 4"
            stroke-width="1.5"
          />

          <!-- Filled Curve Area -->
          <path :d="areaPath" fill="url(#curveGradient)" />

          <!-- Main Curve Line -->
          <path :d="curvePath" fill="none" stroke="#6366f1" stroke-width="2.5" />

          <!-- Draggable Control Points -->
          <g v-for="(pt, idx) in activeCurve.points" :key="idx">
            <circle
              :cx="scaleX(pt[0])"
              :cy="scaleY(pt[1])"
              :r="activePointIdx === idx || hoveredPointIdx === idx ? 8 : 6"
              fill="#6366f1"
              :stroke="activePointIdx === idx || hoveredPointIdx === idx ? '#ffffff' : '#0f172a'"
              :stroke-width="activePointIdx === idx ? 3 : 2"
              class="cursor-grab active:cursor-grabbing"
              @mouseenter="hoveredPointIdx = idx"
              @mouseleave="hoveredPointIdx = null"
              @mousedown.stop="onPointMouseDown(idx, $event)"
              @dblclick.stop="removePoint(idx)"
            />
          </g>
        </svg>

        <!-- Coordinate Axis Labels -->
        <div class="flex justify-between text-[10px] text-slate-500 font-mono mt-1 px-4">
          <span>0% Room Brightness</span>
          <span>50%</span>
          <span>100% Room Brightness</span>
        </div>
      </div>

      <!-- Point Fine Tuning Table -->
      <div class="flex items-center gap-2 flex-wrap pt-1">
        <span class="text-xs font-semibold text-slate-400">Control Points:</span>
        <div
          v-for="(pt, idx) in activeCurve.points"
          :key="idx"
          class="flex items-center gap-1 bg-slate-950 border border-slate-800 rounded px-2 py-1 text-xs font-mono"
        >
          <span class="text-slate-500 text-[10px]">#{{ idx + 1 }}</span>
          <span class="text-indigo-400">R:</span>
          <input
            type="number"
            min="0"
            max="100"
            v-model.number="pt[0]"
            class="w-10 bg-slate-900 border border-slate-700 text-center rounded px-0.5 py-0.5 text-xs text-slate-200"
          />
          <span class="text-slate-400">%</span>
          <span class="text-indigo-400 ml-1">F:</span>
          <input
            type="number"
            min="0"
            max="100"
            v-model.number="pt[1]"
            class="w-10 bg-slate-900 border border-slate-700 text-center rounded px-0.5 py-0.5 text-xs text-slate-200"
          />
          <span class="text-slate-400">%</span>
          <button
            v-if="activeCurve.points.length > 2"
            @click="removePoint(idx)"
            class="text-rose-400 hover:text-rose-300 ml-1 cursor-pointer font-bold"
            title="Remove point"
          >
            &times;
          </button>
        </div>
      </div>
    </div>

    <!-- Curve Import Modal -->
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
        aria-labelledby="curve-import-title"
      >
        <div class="flex justify-between items-center border-b border-slate-800 pb-3">
          <h4 id="curve-import-title" class="text-sm font-bold text-white flex items-center gap-2">
            <span>📥 Import Brightness Distribution Curve YAML</span>
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
          Paste YAML containing curve points (e.g. <code>points: [[0, 0], [50, 80], [100, 100]]</code> or a full curve definition):
        </p>

        <textarea
          v-model="importYamlText"
          rows="8"
          placeholder="points:
  - [0, 0]
  - [40, 20]
  - [100, 100]"
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

        <!-- Success Preview Banner & Target Options -->
        <div v-else-if="parsedPoints" class="flex flex-col gap-3">
          <div class="bg-emerald-950/60 border border-emerald-800 text-emerald-300 text-xs px-3 py-2 rounded-lg">
            ✓ Ready to import {{ parsedPoints.length }} points (Room 0%–100%)
          </div>

          <div class="bg-slate-950/60 border border-slate-800 rounded-lg p-3 flex flex-col gap-2.5 text-xs">
            <span class="font-semibold text-slate-300 uppercase tracking-wider text-[11px]">Import Destination</span>

            <label class="flex items-center gap-2 cursor-pointer">
              <input
                type="radio"
                value="active"
                v-model="importDestination"
                class="accent-indigo-500"
              />
              <span class="text-slate-200">
                Apply to active curve: <strong class="text-indigo-400 font-mono">{{ activeCurve?.name }}</strong>
              </span>
            </label>

            <label class="flex items-center gap-2 cursor-pointer">
              <input
                type="radio"
                value="new"
                v-model="importDestination"
                class="accent-indigo-500"
              />
              <span class="text-slate-200">Create as a new curve:</span>
            </label>

            <div v-if="importDestination === 'new'" class="pl-6 pt-1 flex items-center gap-2">
              <input
                v-model="newCurveNameInput"
                type="text"
                placeholder="curve_name"
                class="bg-slate-900 border border-slate-700 text-slate-100 rounded px-2.5 py-1 text-xs font-mono focus:border-indigo-500 focus:outline-none"
              />
              <span v-if="newCurveNameError" class="text-rose-400 text-[11px]">{{ newCurveNameError }}</span>
            </div>
          </div>
        </div>

        <div class="flex justify-end items-center gap-2 pt-2 border-t border-slate-800">
          <button
            @click="closeImportModal"
            class="text-xs px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 transition cursor-pointer"
          >
            Cancel
          </button>
          <button
            @click="applyImportedCurve"
            :disabled="!parsedPoints"
            :class="[
              'text-xs px-4 py-1.5 rounded-lg font-semibold transition',
              parsedPoints
                ? 'bg-indigo-600 hover:bg-indigo-500 text-white cursor-pointer shadow-md shadow-indigo-600/30'
                : 'bg-slate-800 text-slate-500 cursor-not-allowed',
            ]"
          >
            Apply Curve
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted, onUnmounted, nextTick } from 'vue'
import type { BrightnessCurve } from '../types'
import { getSvgCoordinates } from '../utils/svg'
import { entityService } from '../services/entityService'
import {
  serializeCurvePointsYaml,
  parseCurvePointsYaml,
  copyToClipboard,
} from '../utils/curveYaml'

const props = withDefaults(
  defineProps<{
    brightnessCurves: Record<string, BrightnessCurve>
    roomLights?: string[]
  }>(),
  {
    roomLights: () => [],
  }
)

const emit = defineEmits<{
  (e: 'openGlobalDtw'): void
  (e: 'update:previewRoomBrightness', val: number): void
}>()

const curveNames = computed(() => Object.keys(props.brightnessCurves))

const selectedCurveName = ref<string>(curveNames.value[0] || '')

watch(curveNames, (names) => {
  if (!names.includes(selectedCurveName.value)) {
    selectedCurveName.value = names[0] || ''
  }
})

const activeCurve = computed<BrightnessCurve | null>(() => {
  return props.brightnessCurves[selectedCurveName.value] || Object.values(props.brightnessCurves)[0] || null
})

// Rename state and controls
const isRenaming = ref(false)
const renameInput = ref('')
const renameError = ref<string | null>(null)
const renameInputRef = ref<HTMLInputElement | null>(null)

// YAML Copy & Import state
const copiedYaml = ref(false)
const showImportModal = ref(false)
const importYamlText = ref('')
const importError = ref<string | null>(null)
const parsedPoints = ref<[number, number][] | null>(null)
const importDestination = ref<'active' | 'new'>('active')
const newCurveNameInput = ref('')
const newCurveNameError = ref<string | null>(null)

async function copyCurveYaml() {
  if (!activeCurve.value) return
  const yaml = serializeCurvePointsYaml(activeCurve.value.points, activeCurve.value.name)
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
    parsedPoints.value = null
    newCurveNameError.value = null
    return
  }

  const res = parseCurvePointsYaml(importYamlText.value)
  if (res.success && res.points) {
    parsedPoints.value = res.points
    importError.value = null
    newCurveNameError.value = null
    if (res.name) {
      newCurveNameInput.value = res.name;
      if (activeCurve.value && res.name !== activeCurve.value.name) { importDestination.value = "new"; }
    } else if (!newCurveNameInput.value) {
      newCurveNameInput.value = 'imported_curve'
    }
  } else {
    parsedPoints.value = null
    importError.value = res.error || 'Failed to parse curve points YAML.'
  }
}

function applyImportedCurve() {
  if (!parsedPoints.value) return

  if (importDestination.value === 'active') {
    if (!activeCurve.value) return
    activeCurve.value.points = parsedPoints.value
    closeImportModal()
  } else {
    const trimmed = newCurveNameInput.value.trim()
    if (!trimmed) {
      newCurveNameError.value = 'Curve name cannot be empty.'
      return
    }
    if (props.brightnessCurves[trimmed]) {
      newCurveNameError.value = `A curve named "${trimmed}" already exists.`
      return
    }

    props.brightnessCurves[trimmed] = {
      name: trimmed,
      lights: [],
      points: parsedPoints.value,
    }
    selectedCurveName.value = trimmed
    closeImportModal()
  }
}

function closeImportModal() {
  showImportModal.value = false
  importYamlText.value = ''
  importError.value = null
  parsedPoints.value = null
  newCurveNameError.value = null
  importDestination.value = 'active'
}

watch(selectedCurveName, () => {
  if (isRenaming.value) {
    cancelRename()
  }
})

function startRename() {
  if (!activeCurve.value) return
  renameInput.value = activeCurve.value.name
  renameError.value = null
  isRenaming.value = true
  nextTick(() => {
    if (renameInputRef.value) {
      renameInputRef.value.focus()
      renameInputRef.value.select()
    }
  })
}

function cancelRename() {
  isRenaming.value = false
  renameError.value = null
  renameInput.value = ''
}

function confirmRename() {
  if (!activeCurve.value) return
  const oldName = activeCurve.value.name
  const trimmedName = renameInput.value.trim()

  if (!trimmedName) {
    renameError.value = 'Curve name cannot be empty.'
    return
  }

  if (trimmedName === oldName) {
    cancelRename()
    return
  }

  if (props.brightnessCurves[trimmedName]) {
    renameError.value = `A curve named "${trimmedName}" already exists.`
    return
  }

  const curveToUpdate = props.brightnessCurves[oldName]
  if (curveToUpdate) {
    curveToUpdate.name = trimmedName
    delete props.brightnessCurves[oldName]
    props.brightnessCurves[trimmedName] = curveToUpdate
  }

  selectedCurveName.value = trimmedName
  isRenaming.value = false
  renameError.value = null
}

const showAssignLightMenu = ref(false)

const unassignedRoomLights = computed(() => {
  if (!activeCurve.value) return []
  return props.roomLights.filter((lt) => !activeCurve.value!.lights.includes(lt))
})

function getLightName(entityId: string): string {
  return entityService.getFriendlyName(entityId)
}

function attachLight(entityId: string) {
  if (!activeCurve.value) return
  if (!activeCurve.value.lights.includes(entityId)) {
    activeCurve.value.lights.push(entityId)
  }
  showAssignLightMenu.value = false
}

function detachLight(entityId: string) {
  if (!activeCurve.value) return
  activeCurve.value.lights = activeCurve.value.lights.filter((id) => id !== entityId)
}

const svgWidth = ref(800)
const svgHeight = ref(256)
const PAD_X = 24
const PAD_Y = 18

const svgRef = ref<SVGSVGElement | null>(null)
const activePointIdx = ref<number | null>(null)
const hoveredPointIdx = ref<number | null>(null)

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
  if (typeof ResizeObserver !== 'undefined') {
    resizeObserver = new ResizeObserver(() => updateSvgDimensions())
    if (svgRef.value) resizeObserver.observe(svgRef.value)
  }
})

onUnmounted(() => {
  if (resizeObserver) resizeObserver.disconnect()
  window.removeEventListener('mousemove', onWindowMouseMove)
  window.removeEventListener('mouseup', onWindowMouseUp)
})

function scaleX(val: number): number {
  return PAD_X + (val / 100) * (svgWidth.value - PAD_X * 2)
}

function scaleY(val: number): number {
  return svgHeight.value - PAD_Y - (val / 100) * (svgHeight.value - PAD_Y * 2)
}

function unscaleX(x: number): number {
  const norm = (x - PAD_X) / (svgWidth.value - PAD_X * 2)
  return Math.max(0, Math.min(100, Math.round(norm * 100)))
}

function unscaleY(y: number): number {
  const norm = (svgHeight.value - PAD_Y - y) / (svgHeight.value - PAD_Y * 2)
  return Math.max(0, Math.min(100, Math.round(norm * 100)))
}

const curvePath = computed(() => {
  if (!activeCurve.value || !activeCurve.value.points.length) return ''
  const sorted = [...activeCurve.value.points].sort((a, b) => a[0] - b[0])
  let d = `M ${scaleX(sorted[0][0])},${scaleY(sorted[0][1])}`
  for (let i = 1; i < sorted.length; i++) {
    d += ` L ${scaleX(sorted[i][0])},${scaleY(sorted[i][1])}`
  }
  return d
})

const areaPath = computed(() => {
  const line = curvePath.value
  if (!line || !activeCurve.value || !activeCurve.value.points.length) return ''
  const sorted = [...activeCurve.value.points].sort((a, b) => a[0] - b[0])
  const first = sorted[0]
  const last = sorted[sorted.length - 1]
  return `${line} L ${scaleX(last[0])},${scaleY(0)} L ${scaleX(first[0])},${scaleY(0)} Z`
})

function onPointMouseDown(idx: number, e: MouseEvent) {
  e.preventDefault()
  activePointIdx.value = idx
  window.addEventListener('mousemove', onWindowMouseMove)
  window.addEventListener('mouseup', onWindowMouseUp)
}

function onCanvasMouseDown(e: MouseEvent) {
  if (!svgRef.value || !activeCurve.value) return
  const coords = getSvgCoordinates(svgRef.value, e)
  const roomB = unscaleX(coords.x)
  const fixB = unscaleY(coords.y)

  const existingIdx = activeCurve.value.points.findIndex(
    (pt) => Math.abs(pt[0] - roomB) < 5 && Math.abs(pt[1] - fixB) < 5
  )

  if (existingIdx !== -1) {
    activePointIdx.value = existingIdx
  } else {
    activeCurve.value.points.push([roomB, fixB])
    activeCurve.value.points.sort((a, b) => a[0] - b[0])
    activePointIdx.value = activeCurve.value.points.findIndex((pt) => pt[0] === roomB && pt[1] === fixB)
    emit('update:previewRoomBrightness', roomB)
  }

  window.addEventListener('mousemove', onWindowMouseMove)
  window.addEventListener('mouseup', onWindowMouseUp)
}

function onWindowMouseMove(e: MouseEvent) {
  if (activePointIdx.value === null || !svgRef.value || !activeCurve.value) return

  const coords = getSvgCoordinates(svgRef.value, e)
  const roomB = unscaleX(coords.x)
  const fixB = unscaleY(coords.y)

  activeCurve.value.points[activePointIdx.value] = [roomB, fixB]
  activeCurve.value.points.sort((a, b) => a[0] - b[0])
  activePointIdx.value = activeCurve.value.points.findIndex((pt) => pt[0] === roomB && pt[1] === fixB)

  emit('update:previewRoomBrightness', roomB)
}

function onWindowMouseUp() {
  activePointIdx.value = null
  window.removeEventListener('mousemove', onWindowMouseMove)
  window.removeEventListener('mouseup', onWindowMouseUp)
}

function removePoint(idx: number) {
  if (!activeCurve.value || activeCurve.value.points.length <= 2) return
  activeCurve.value.points.splice(idx, 1)
  activePointIdx.value = null
}

function createNewCurve() {
  const name = prompt('Enter a unique name for the new room brightness curve:')
  if (!name) return

  const trimmed = name.trim()
  if (!trimmed) return

  if (props.brightnessCurves[trimmed]) {
    alert(`A curve named "${trimmed}" already exists.`)
    return
  }

  props.brightnessCurves[trimmed] = {
    name: trimmed,
    lights: [],
    points: [
      [0, 0],
      [50, 50],
      [100, 100],
    ],
  }
  selectedCurveName.value = trimmed
}
</script>
