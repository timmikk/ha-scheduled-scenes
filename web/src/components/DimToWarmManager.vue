<template>
  <div
    :class="[
      'bg-slate-900 border rounded-xl shadow-xl flex flex-col transition-all',
      mode === 'contextual'
        ? 'border-amber-500/60 shadow-amber-500/10 p-5 max-w-4xl w-full'
        : 'border-slate-800 p-6 w-full',
    ]"
  >
    <!-- 1. Contextual Header (when opened from a specific light in room view) -->
    <div
      v-if="mode === 'contextual' && focusedLight"
      class="border-b border-slate-800 pb-4 mb-4 flex flex-col gap-3"
    >
      <div class="flex items-center justify-between flex-wrap gap-2">
        <div class="flex items-center gap-3">
          <div class="w-10 h-10 rounded-xl bg-amber-500/20 border border-amber-500/30 flex items-center justify-center text-amber-300 text-lg">
            💡
          </div>
          <div>
            <div class="flex items-center gap-2">
              <h2 class="text-base font-bold text-slate-100">{{ focusedLight.name }}</h2>
              <span
                v-if="focusedLight.area_name"
                class="text-[10px] bg-slate-800 text-slate-300 px-2 py-0.5 rounded-full border border-slate-700"
              >
                {{ focusedLight.area_name }}
              </span>
            </div>
            <div class="text-[11px] font-mono text-slate-400">
              {{ focusedLight.entity_id }} &bull; Supported: {{ focusedLight.min_color_temp_kelvin }}-{{ focusedLight.max_color_temp_kelvin }}K
            </div>
          </div>
        </div>

        <div class="flex items-center gap-2">
          <button
            @click="$emit('openFullView')"
            class="text-xs px-2.5 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 font-medium transition cursor-pointer flex items-center gap-1"
            title="Open in full-page Global Curves manager"
          >
            <span>↗ Full View</span>
          </button>
          <button
            @click="$emit('close')"
            class="text-slate-400 hover:text-slate-200 text-xl px-2 py-0.5 rounded hover:bg-slate-800 transition cursor-pointer"
            title="Close"
          >
            &times;
          </button>
        </div>
      </div>

      <!-- Quick Curve Switcher & Fork for this light -->
      <div class="bg-slate-950/80 border border-slate-800 rounded-lg p-3 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div class="flex items-center gap-2 flex-wrap flex-1">
          <span class="text-xs font-semibold text-slate-300 whitespace-nowrap">Assigned Hardware Curve:</span>
          <select
            :value="assignedCurveForFocusedLight?.name || '__none__'"
            @change="onFocusedLightCurveChange(($event.target as HTMLSelectElement).value)"
            class="bg-slate-900 border border-slate-700 text-amber-300 font-medium rounded-lg px-2.5 py-1 text-xs focus:border-amber-500 focus:outline-none cursor-pointer"
          >
            <option value="__none__">None (Fixed / Room Schedule Kelvin)</option>
            <option v-for="cName in curveNames" :key="cName" :value="cName">
              {{ cName }} ({{ (curves[cName]?.lights || []).length }} lights)
            </option>
            <option value="__new__">+ Create New Curve for this light...</option>
          </select>
        </div>

        <!-- Fork / Clone Curve Button (if assigned curve is shared across multiple fixtures) -->
        <div v-if="assignedCurveForFocusedLight && (assignedCurveForFocusedLight.lights.length > 1)" class="shrink-0">
          <button
            @click="forkCurveForFocusedLight"
            class="text-xs px-2.5 py-1 rounded-lg bg-amber-950/80 hover:bg-amber-900 border border-amber-700/80 text-amber-300 font-medium transition cursor-pointer flex items-center gap-1"
            title="Create an isolated copy of this curve so edits do not affect other lights"
          >
            <span>🍴 Fork / Clone Curve for this light</span>
          </button>
        </div>
      </div>

      <!-- Shared Curve Impact Warning -->
      <div
        v-if="assignedCurveUsage && assignedCurveUsage.totalLights > 1"
        class="bg-amber-950/30 border border-amber-800/60 rounded-lg px-3 py-2 text-xs flex items-center gap-2 text-amber-200"
      >
        <span class="text-base shrink-0">⚠️</span>
        <div class="flex-1">
          <strong>Shared Hardware Profile:</strong>
          This curve is assigned to <strong>{{ assignedCurveUsage.totalLights }} fixtures</strong> across
          <span class="underline">{{ assignedCurveUsage.rooms.join(', ') || 'multiple rooms' }}</span>.
          Edits below apply <strong>globally</strong> to all of them. Click "Fork / Clone" above if you only want to customize this light.
        </div>
      </div>
    </div>

    <!-- 2. Full Page Header (when opened in standalone page view) -->
    <div
      v-else-if="mode === 'page'"
      class="border-b border-slate-800 pb-4 mb-4 flex items-center justify-between flex-wrap gap-4"
    >
      <div>
        <h2 class="text-base sm:text-lg font-bold text-slate-100 flex items-center gap-2">
          <span>🌡️ Global Dim-to-Warm Curves</span>
          <span class="text-xs bg-amber-950 text-amber-300 border border-amber-800 px-2 py-0.5 rounded-full font-mono font-semibold">
            {{ curveNames.length }} Profile{{ curveNames.length === 1 ? '' : 's' }}
          </span>
        </h2>
        <p class="text-xs text-slate-400 mt-1">
          Global hardware profiles mapping fixture brightness (0–100%) to physical color temperature (Kelvin).
          Shared across all rooms with the same fixture or bulb model.
        </p>
      </div>

      <div class="flex items-center gap-2">
        <button
          @click="createNewCurve"
          class="text-xs px-3 py-1.5 rounded-lg bg-amber-600 hover:bg-amber-500 text-white font-semibold transition cursor-pointer flex items-center gap-1.5 shadow-sm shadow-amber-600/20"
        >
          <span>+ New Global Curve</span>
        </button>
      </div>
    </div>

    <!-- 3. Main Body: Curve Tabs / Selector & Editor -->
    <div class="flex flex-col gap-4">
      <!-- Curve Selection Pills / Tabs (in page mode, or if focused light has a curve) -->
      <div class="flex items-center justify-between flex-wrap gap-2 bg-slate-950/60 border border-slate-800 p-1.5 rounded-xl">
        <div class="flex items-center gap-1.5 overflow-x-auto max-w-full pb-0.5">
          <button
            v-for="name in curveNames"
            :key="name"
            @click="selectedCurveName = name"
            :class="[
              'text-xs font-semibold px-3 py-1.5 rounded-lg transition cursor-pointer flex items-center gap-2 whitespace-nowrap',
              selectedCurveName === name
                ? 'bg-amber-600 text-white shadow-sm'
                : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800',
            ]"
          >
            <span>🌡️ {{ name }}</span>
            <span
              :class="[
                'text-[10px] px-1.5 py-0.2 rounded-full font-mono',
                selectedCurveName === name ? 'bg-amber-800 text-amber-100' : 'bg-slate-900 text-slate-400',
              ]"
            >
              {{ (curves[name]?.lights || []).length }}
            </span>
          </button>
        </div>

        <div v-if="mode === 'page'" class="flex items-center gap-2 shrink-0">
          <button
            v-if="activeCurve"
            @click="cloneActiveCurve"
            class="text-xs text-slate-400 hover:text-slate-200 px-2.5 py-1 rounded-lg hover:bg-slate-800 transition cursor-pointer"
            title="Duplicate this curve"
          >
            Duplicate
          </button>
          <button
            v-if="activeCurve && curveNames.length > 1"
            @click="deleteActiveCurve"
            class="text-xs text-rose-400 hover:text-rose-300 px-2 py-1 rounded-lg hover:bg-rose-950/40 transition cursor-pointer"
            title="Delete this curve"
          >
            Delete
          </button>
        </div>
      </div>

      <!-- Active Curve Details & Assignment -->
      <div v-if="activeCurve" class="flex flex-col gap-4">
        <!-- Curve Overview & Multi-Room Fixture Assignment -->
        <div class="bg-slate-950/70 border border-slate-800 rounded-lg p-3.5 flex flex-col gap-3">
          <div class="flex items-start justify-between flex-wrap gap-2">
            <div>
              <div class="flex items-center gap-2">
                <span class="text-xs font-bold text-slate-200 uppercase tracking-wider">Active Curve:</span>
                <span class="text-sm font-bold text-amber-300 font-mono">{{ activeCurve.name }}</span>
              </div>
              <div class="text-[11px] text-slate-400 mt-0.5">
                Range:
                <span class="font-mono text-slate-300">
                  {{ curveMinKelvin }}K &rarr; {{ curveMaxKelvin }}K
                </span>
                &bull;
                Used in:
                <span class="text-slate-300 font-medium">
                  {{ activeCurveUsage.rooms.length > 0 ? activeCurveUsage.rooms.join(', ') : 'No rooms' }}
                </span>
              </div>
            </div>

            <!-- Add/Assign Light Trigger -->
            <div class="relative">
              <button
                @click="showAssignDropdown = !showAssignDropdown"
                class="text-xs px-2.5 py-1 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 font-medium transition cursor-pointer flex items-center gap-1.5"
              >
                <span>+ Assign Fixtures</span>
                <span class="text-[10px] opacity-70">&blacktriangledown;</span>
              </button>

              <!-- Assign Light Dropdown -->
              <div
                v-if="showAssignDropdown"
                class="absolute right-0 mt-2 w-72 sm:w-80 bg-slate-900 border border-slate-700 rounded-xl shadow-2xl z-30 p-3 flex flex-col gap-2.5"
              >
                <div class="flex items-center justify-between border-b border-slate-800 pb-1.5">
                  <span class="text-xs font-bold text-slate-200">Assign Fixtures to {{ activeCurve.name }}</span>
                  <button @click="showAssignDropdown = false" class="text-slate-400 hover:text-white">&times;</button>
                </div>
                <input
                  v-model="assignSearchQuery"
                  type="text"
                  placeholder="Filter lights by name or area..."
                  class="bg-slate-950 border border-slate-700 rounded-lg px-2.5 py-1 text-xs text-slate-200 focus:outline-none focus:border-amber-500"
                />
                <div class="max-h-48 overflow-y-auto flex flex-col gap-1 pr-1">
                  <button
                    v-for="lt in unassignedAvailableLights"
                    :key="lt.entity_id"
                    @click="assignLightToCurve(lt.entity_id)"
                    class="text-left bg-slate-950/60 hover:bg-slate-800 p-2 rounded-lg border border-slate-800/80 transition flex items-center justify-between text-xs cursor-pointer group"
                  >
                    <div class="truncate">
                      <div class="text-slate-200 font-medium group-hover:text-amber-300 truncate">{{ lt.name }}</div>
                      <div class="text-[10px] text-slate-500 font-mono truncate">{{ lt.entity_id }}</div>
                    </div>
                    <span class="text-amber-400 font-bold text-xs shrink-0 ml-2">+ Add</span>
                  </button>
                  <div v-if="unassignedAvailableLights.length === 0" class="text-center py-3 text-xs text-slate-500">
                    No unassigned lights found.
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- Fixture Chips currently assigned to this curve -->
          <div class="flex flex-wrap items-center gap-1.5 pt-1 border-t border-slate-800/60">
            <span class="text-[11px] font-semibold text-slate-400">Assigned Fixtures ({{ activeCurve.lights.length }}):</span>
            <div v-if="activeCurve.lights.length === 0" class="text-xs text-slate-500 italic">
              No fixtures assigned to this curve yet. Click "+ Assign Fixtures" above.
            </div>
            <div
              v-for="entityId in activeCurve.lights"
              :key="entityId"
              class="group text-xs bg-slate-900 border border-slate-800 hover:border-slate-700 text-slate-200 pl-2 pr-1 py-0.5 rounded-md font-mono flex items-center gap-1.5 shadow-sm"
            >
              <span class="w-1.5 h-1.5 rounded-full bg-amber-400"></span>
              <span class="text-[11px] font-sans font-medium text-slate-200">
                {{ getLightDisplayName(entityId) }}
              </span>
              <span class="text-[9px] text-slate-500">({{ getLightRoomName(entityId) }})</span>
              <button
                @click="unassignLightFromCurve(entityId)"
                class="text-slate-500 hover:text-rose-400 ml-0.5 p-0.5 rounded cursor-pointer transition"
                title="Unassign light from curve"
              >
                &times;
              </button>
            </div>
          </div>
        </div>

        <!-- 4. Interactive 2D Coordinate SVG Graph -->
        <div class="relative select-none bg-slate-950/90 border border-slate-800 rounded-xl p-3 flex flex-col gap-2">
          <div class="flex items-center justify-between text-xs text-slate-400 px-1">
            <span class="font-medium text-slate-300">Curve Graph: Fixture Brightness &rarr; Color Temperature</span>
            <span class="text-[11px] text-slate-500">Click canvas to add point. Drag points to adjust. Double-click to remove.</span>
          </div>

          <svg
            ref="svgRef"
            :viewBox="`0 0 ${svgWidth} ${svgHeight}`"
            class="w-full h-64 cursor-crosshair overflow-visible block touch-none select-none rounded-lg bg-slate-950"
            @mousedown="onCanvasMouseDown"
          >
            <defs>
              <linearGradient id="dtwCurveGradient" x1="0%" y1="0%" x2="0%" y2="100%">
                <stop offset="0%" stop-color="#f59e0b" stop-opacity="0.3" />
                <stop offset="100%" stop-color="#f59e0b" stop-opacity="0.0" />
              </linearGradient>
            </defs>

            <!-- 2D Grid Lines -->
            <g stroke="rgba(255, 255, 255, 0.08)" stroke-dasharray="3 3">
              <line
                v-for="pct in [0, 25, 50, 75, 100]"
                :key="'h' + pct"
                :x1="PAD_X"
                :y1="scaleY(pct)"
                :x2="svgWidth - PAD_X"
                :y2="scaleY(pct)"
              />
              <line
                v-for="pct in [0, 25, 50, 75, 100]"
                :key="'v' + pct"
                :x1="scaleX(pct)"
                :y1="PAD_Y"
                :x2="scaleX(pct)"
                :y2="svgHeight - PAD_Y"
              />
            </g>

            <!-- Y-Axis Kelvin Ticks -->
            <g font-size="11" fill="rgba(255, 255, 255, 0.45)" font-family="monospace">
              <text :x="PAD_X + 6" :y="scaleY(100) + 12">{{ MAX_TEMP }}K</text>
              <text :x="PAD_X + 6" :y="scaleY(50) - 4">{{ Math.round((MIN_TEMP + MAX_TEMP) / 2) }}K</text>
              <text :x="PAD_X + 6" :y="scaleY(0) - 4">{{ MIN_TEMP }}K</text>
            </g>

            <!-- Shaded Area Under Curve -->
            <path :d="areaPath" fill="url(#dtwCurveGradient)" />

            <!-- Curve Line -->
            <path
              :d="linePath"
              fill="none"
              stroke="#f59e0b"
              stroke-width="3"
            />

            <!-- Visual Playhead Indicator for Live Test Brightness -->
            <g v-if="dtwTestBrightness !== null">
              <line
                :x1="scaleX(dtwTestBrightness)"
                :y1="PAD_Y"
                :x2="scaleX(dtwTestBrightness)"
                :y2="svgHeight - PAD_Y"
                stroke="#38bdf8"
                stroke-width="1.5"
                stroke-dasharray="4 2"
              />
              <circle
                :cx="scaleX(dtwTestBrightness)"
                :cy="scaleYKelvin(currentTestKelvin)"
                r="6"
                fill="#38bdf8"
                stroke="#ffffff"
                stroke-width="2"
              />
            </g>

            <!-- Control Points -->
            <g v-for="(pt, idx) in activeCurve.points" :key="idx">
              <circle
                :cx="scaleX(pt[0])"\n                :cy="scaleYKelvin(pt[1])"
                :r="hoveredPointIdx === idx || activePointIdx === idx ? 8 : 6"
                fill="#f59e0b"
                stroke="#ffffff"
                :stroke-width="activePointIdx === idx || hoveredPointIdx === idx ? 3 : 2"
                class="cursor-grab active:cursor-grabbing"
                @mouseenter="hoveredPointIdx = idx"
                @mouseleave="hoveredPointIdx = null"
                @mousedown.stop="onPointMouseDown(idx, $event)"
                @dblclick.stop="removePoint(idx)"
              />
            </g>
          </svg>

          <!-- Axes Labels -->
          <div class="flex justify-between text-[11px] text-slate-400 font-mono px-2">
            <span>0% Fixture Brightness</span>
            <span>Dim-to-Warm Ramp</span>
            <span>100% Brightness</span>
          </div>
        </div>

        <!-- 5. Points List / Fine Tuning Table -->
        <div class="flex flex-wrap items-center gap-2 bg-slate-950/60 border border-slate-800 p-2.5 rounded-lg">
          <span class="text-xs font-semibold text-slate-400">Control Points:</span>
          <div
            v-for="(pt, idx) in activeCurve.points"
            :key="idx"
            class="flex items-center gap-1 bg-slate-900 border border-slate-800 rounded px-2 py-1 text-xs font-mono"
          >
            <span class="text-slate-500">Bri:</span>
            <input
              type="number"
              min="0"
              max="100"
              v-model.number="pt[0]"
              @change="sortPoints"
              class="w-11 bg-slate-950 border border-slate-700 text-center rounded px-0.5 py-0.5 text-xs text-amber-300 font-semibold"
            />
            <span class="text-slate-400">%</span>
            <span class="text-slate-500 ml-1">K:</span>
            <input
              type="number"
              :min="MIN_TEMP"
              :max="MAX_TEMP"
              v-model.number="pt[1]"
              class="w-14 bg-slate-950 border border-slate-700 text-center rounded px-0.5 py-0.5 text-xs text-amber-300 font-semibold"
            />
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

        <!-- 6. Hardware Live Test / Calibration Panel -->
        <div class="bg-slate-950/80 border border-slate-800 rounded-xl p-3.5 flex flex-col gap-3">
          <div class="flex items-center justify-between flex-wrap gap-2">
            <div class="flex items-center gap-2">
              <span class="text-xs font-bold text-slate-200 flex items-center gap-1.5">
                <span>🔦 Live Fixture Calibration</span>
              </span>
              <span class="text-[11px] text-slate-400">
                Drive assigned fixtures with a test brightness slider to physically verify warmth.
              </span>
            </div>

            <!-- Live Hardware Toggle -->
            <button
              @click="$emit('toggleLiveDtw')"
              :class="[
                'text-xs font-semibold px-3 py-1.5 rounded-lg transition cursor-pointer flex items-center gap-1.5 border',
                liveMode === 'dim_to_warm'
                  ? 'bg-amber-600 hover:bg-amber-500 text-white border-amber-400 shadow-md shadow-amber-600/30'
                  : 'bg-slate-900 hover:bg-slate-800 text-slate-300 border-slate-700',
              ]"
            >
              <span
                :class="[
                  'w-2 h-2 rounded-full',
                  liveMode === 'dim_to_warm' ? 'bg-white animate-ping' : 'bg-amber-500',
                ]"
              ></span>
              <span>{{ liveMode === 'dim_to_warm' ? 'Stop Live Test' : 'Start Live Hardware Test' }}</span>
            </button>
          </div>

          <!-- Slider & Readout Row -->
          <div class="grid grid-cols-1 md:grid-cols-3 gap-3 items-center bg-slate-900/60 border border-slate-800/80 rounded-lg p-3">
            <div class="md:col-span-2 flex flex-col gap-1.5">
              <div class="flex justify-between items-center text-xs">
                <span class="font-semibold text-slate-300">Test Brightness:</span>
                <span class="font-mono font-bold text-sky-400">{{ dtwTestBrightness }}%</span>
              </div>
              <input
                type="range"
                min="1"
                max="100"
                v-model.number="dtwTestBrightness"
                class="accent-sky-400 cursor-pointer"
              />
              <div class="flex justify-between text-[10px] text-slate-500 font-mono">
                <span>1% (Deep Warmth)</span>
                <span>50%</span>
                <span>100% (Full Output)</span>
              </div>
            </div>

            <!-- Interpolated Color Swatch & Temp Readout -->
            <div class="flex items-center gap-3 bg-slate-950 border border-slate-800 rounded-lg p-2.5">
              <div
                class="w-10 h-10 rounded-lg border border-white/20 shadow-md shrink-0 transition-colors"
                :style="{ backgroundColor: currentTestSwatchColor }"
              ></div>
              <div class="flex flex-col">
                <span class="text-[10px] text-slate-400 font-mono uppercase">Calculated Kelvin</span>
                <span class="text-sm font-bold text-amber-300 font-mono">{{ currentTestKelvin }} K</span>
                <span class="text-[10px] text-slate-500">at {{ dtwTestBrightness }}% output</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import type { DimToWarmCurve, LiveModeType, ProgramConfig } from '../types'
import { entityService } from '../services/entityService'
import { evaluateDimToWarm } from '../utils/interpolator'
import { kelvinToCssColor } from '../utils/color'
import { getSvgCoordinates } from '../utils/svg'
import { liveOutputService } from '../services/liveOutputService'

const props = withDefaults(
  defineProps<{
    curves: Record<string, DimToWarmCurve>
    programs: ProgramConfig[]
    focusLightId?: string | null
    mode?: 'page' | 'contextual'
    liveMode?: LiveModeType
  }>(),
  {
    focusLightId: null,
    mode: 'page',
    liveMode: 'off',
  }
)

const emit = defineEmits<{
  (e: 'update:curves', val: Record<string, DimToWarmCurve>): void
  (e: 'close'): void
  (e: 'openFullView'): void
  (e: 'toggleLiveDtw'): void
}>()

const curveNames = computed(() => Object.keys(props.curves))

// Find curve currently assigned to focused light (if any)
const assignedCurveForFocusedLight = computed(() => {
  if (!props.focusLightId) return null
  return Object.values(props.curves).find((c) => c.lights.includes(props.focusLightId!)) || null
})

const focusedLight = computed(() => {
  if (!props.focusLightId) return null
  return entityService.getLight(props.focusLightId)
})

// Active curve being edited in the graph
const selectedCurveName = ref<string>('')

// Initialize or react to focused light
watch(
  () => props.focusLightId,
  (lightId) => {
    if (lightId) {
      const assigned = Object.values(props.curves).find((c) => c.lights.includes(lightId))
      if (assigned) {
        selectedCurveName.value = assigned.name
        return
      }
    }
    if (!selectedCurveName.value || !props.curves[selectedCurveName.value]) {
      selectedCurveName.value = curveNames.value[0] || ''
    }
  },
  { immediate: true }
)

// Ensure valid selection when curveNames changes
watch(
  curveNames,
  (names) => {
    if (!names.includes(selectedCurveName.value)) {
      selectedCurveName.value = names[0] || ''
    }
  },
  { immediate: true }
)

const activeCurve = computed<DimToWarmCurve | null>(() => {
  if (!selectedCurveName.value) return null
  return props.curves[selectedCurveName.value] || null
})

// Usage analysis for active curve
const activeCurveUsage = computed(() => {
  if (!activeCurve.value) return { totalLights: 0, rooms: [] }
  return analyzeCurveUsage(activeCurve.value)
})

const assignedCurveUsage = computed(() => {
  if (!assignedCurveForFocusedLight.value) return null
  return analyzeCurveUsage(assignedCurveForFocusedLight.value)
})

function analyzeCurveUsage(curve: DimToWarmCurve) {
  const roomsSet = new Set<string>()
  for (const lightId of curve.lights) {
    for (const prog of props.programs) {
      if (prog.lights.includes(lightId)) {
        roomsSet.add(prog.name)
      }
    }
  }
  return {
    totalLights: curve.lights.length,
    rooms: Array.from(roomsSet),
  }
}

// -------------------------------------------------------------
// Live Calibration State & Sync
// -------------------------------------------------------------
const dtwTestBrightness = ref(50)

const currentTestKelvin = computed(() => {
  if (!activeCurve.value) return 2700
  return evaluateDimToWarm(activeCurve.value.points, dtwTestBrightness.value)
})

const currentTestSwatchColor = computed(() => {
  return kelvinToCssColor(currentTestKelvin.value, dtwTestBrightness.value > 0 ? 1 : 0.3)
})

// When in live DTW mode, sync changes to live output service
watch([dtwTestBrightness, currentTestKelvin, () => props.liveMode], () => {
  if (props.liveMode === 'dim_to_warm' && activeCurve.value && activeCurve.value.lights.length > 0) {
    const targets = activeCurve.value.lights.map((entityId) => ({
      entityId,
      brightnessPct: dtwTestBrightness.value,
      kelvin: currentTestKelvin.value,
    }))
    liveOutputService.syncFixtures(targets)
  }
})

// -------------------------------------------------------------
// SVG Graph Logic
// -------------------------------------------------------------
const svgWidth = ref(800)
const svgHeight = ref(256)
const PAD_X = 24
const PAD_Y = 18

const MIN_TEMP = 1800
const MAX_TEMP = 5000

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

function scaleY(pct: number): number {
  return svgHeight.value - PAD_Y - (pct / 100) * (svgHeight.value - PAD_Y * 2)
}

function scaleYKelvin(kelvin: number): number {
  const norm = Math.max(0, Math.min(100, ((kelvin - MIN_TEMP) / (MAX_TEMP - MIN_TEMP)) * 100))
  return scaleY(norm)
}

function unscaleX(x: number): number {
  const norm = (x - PAD_X) / (svgWidth.value - PAD_X * 2)
  return Math.max(0, Math.min(100, Math.round(norm * 100)))
}

function unscaleYKelvin(y: number): number {
  const norm = (svgHeight.value - PAD_Y - y) / (svgHeight.value - PAD_Y * 2)
  const pct = Math.max(0, Math.min(100, norm * 100))
  return Math.round(MIN_TEMP + (pct / 100) * (MAX_TEMP - MIN_TEMP))
}

const linePath = computed(() => {
  if (!activeCurve.value || !activeCurve.value.points.length) return ''
  const pts = [...activeCurve.value.points].sort((a, b) => a[0] - b[0])
  return pts.reduce((acc, p, i) => {
    const x = scaleX(p[0])
    const y = scaleYKelvin(p[1])
    return i === 0 ? `M ${x},${y}` : `${acc} L ${x},${y}`
  }, '')
})

const areaPath = computed(() => {
  const base = linePath.value
  if (!base || !activeCurve.value || !activeCurve.value.points.length) return ''
  const pts = [...activeCurve.value.points].sort((a, b) => a[0] - b[0])
  const firstX = scaleX(pts[0][0])
  const lastX = scaleX(pts[pts.length - 1][0])
  return `${base} L ${lastX},${svgHeight.value - PAD_Y} L ${firstX},${svgHeight.value - PAD_Y} Z`
})

const curveMinKelvin = computed(() => {
  if (!activeCurve.value || !activeCurve.value.points.length) return MIN_TEMP
  return Math.min(...activeCurve.value.points.map((p) => p[1]))
})

const curveMaxKelvin = computed(() => {
  if (!activeCurve.value || !activeCurve.value.points.length) return MAX_TEMP
  return Math.max(...activeCurve.value.points.map((p) => p[1]))
})

function sortPoints() {
  if (!activeCurve.value) return
  activeCurve.value.points.sort((a, b) => a[0] - b[0])
}

function onPointMouseDown(idx: number, e: MouseEvent) {
  e.preventDefault()
  activePointIdx.value = idx
  // Auto-snap test brightness to the dragged point's brightness
  if (activeCurve.value && activeCurve.value.points[idx]) {
    dtwTestBrightness.value = activeCurve.value.points[idx][0]
  }

  window.addEventListener('mousemove', onWindowMouseMove)
  window.addEventListener('mouseup', onWindowMouseUp)
}

function onCanvasMouseDown(e: MouseEvent) {
  if (activePointIdx.value !== null || !svgRef.value || !activeCurve.value) return

  const coords = getSvgCoordinates(svgRef.value, e)
  if (
    coords.x >= PAD_X - 10 &&
    coords.x <= svgWidth.value - PAD_X + 10 &&
    coords.y >= PAD_Y - 10 &&
    coords.y <= svgHeight.value - PAD_Y + 10
  ) {
    const xVal = unscaleX(coords.x)
    const yVal = unscaleYKelvin(coords.y)

    activeCurve.value.points.push([xVal, yVal])
    activeCurve.value.points.sort((a, b) => a[0] - b[0])
    dtwTestBrightness.value = xVal
    const newIdx = activeCurve.value.points.findIndex((p) => p[0] === xVal && p[1] === yVal)
    activePointIdx.value = newIdx >= 0 ? newIdx : null

    window.addEventListener('mousemove', onWindowMouseMove)
    window.addEventListener('mouseup', onWindowMouseUp)
  }
}

function onWindowMouseMove(e: MouseEvent) {
  if (activePointIdx.value === null || !svgRef.value || !activeCurve.value) return

  const coords = getSvgCoordinates(svgRef.value, e)
  const xVal = unscaleX(coords.x)
  const yVal = unscaleYKelvin(coords.y)

  activeCurve.value.points[activePointIdx.value] = [xVal, yVal]
  dtwTestBrightness.value = xVal
}

function onWindowMouseUp() {
  sortPoints()
  activePointIdx.value = null
  window.removeEventListener('mousemove', onWindowMouseMove)
  window.removeEventListener('mouseup', onWindowMouseUp)
}

function removePoint(idx: number) {
  if (!activeCurve.value || activeCurve.value.points.length <= 2) return
  activeCurve.value.points.splice(idx, 1)
  activePointIdx.value = null
}

// -------------------------------------------------------------
// Fixture Assignment Dropdown
// -------------------------------------------------------------
const showAssignDropdown = ref(false)
const assignSearchQuery = ref('')

const unassignedAvailableLights = computed(() => {
  if (!activeCurve.value) return []
  const assigned = new Set(activeCurve.value.lights)
  let all = entityService.getAllLights().filter((l) => !assigned.has(l.entity_id))
  if (assignSearchQuery.value.trim()) {
    const q = assignSearchQuery.value.trim().toLowerCase()
    all = all.filter(
      (l) =>
        l.name.toLowerCase().includes(q) ||
        l.entity_id.toLowerCase().includes(q) ||
        (l.area_name && l.area_name.toLowerCase().includes(q))
    )
  }
  return all
})

function assignLightToCurve(entityId: string) {
  if (!activeCurve.value) return
  // If light was on another curve, remove it from that curve first
  for (const c of Object.values(props.curves)) {
    c.lights = c.lights.filter((id) => id !== entityId)
  }
  activeCurve.value.lights.push(entityId)
  showAssignDropdown.value = false
}

function unassignLightFromCurve(entityId: string) {
  if (!activeCurve.value) return
  activeCurve.value.lights = activeCurve.value.lights.filter((id) => id !== entityId)
}

function getLightDisplayName(entityId: string): string {
  return entityService.getFriendlyName(entityId)
}

function getLightRoomName(entityId: string): string {
  for (const prog of props.programs) {
    if (prog.lights.includes(entityId)) return prog.name
  }
  return 'Unassigned'
}

// -------------------------------------------------------------
// Contextual Light Assignment & Forking
// -------------------------------------------------------------
function onFocusedLightCurveChange(selectedVal: string) {
  const lightId = props.focusLightId
  if (!lightId) return

  if (selectedVal === '__none__') {
    // Unassign from any curve
    for (const c of Object.values(props.curves)) {
      c.lights = c.lights.filter((id) => id !== lightId)
    }
    return
  }

  if (selectedVal === '__new__') {
    const name = prompt('Enter a name for the new Dim-to-Warm curve:', `${lightId.replace('light.', '')}_dtw`)
    if (!name) return
    // Remove from existing
    for (const c of Object.values(props.curves)) {
      c.lights = c.lights.filter((id) => id !== lightId)
    }
    props.curves[name] = {
      name,
      lights: [lightId],
      points: [
        [1, 2000],
        [40, 2700],
        [100, 4000],
      ],
    }
    selectedCurveName.value = name
    return
  }

  // Assign to selected existing curve
  for (const c of Object.values(props.curves)) {
    c.lights = c.lights.filter((id) => id !== lightId)
  }
  if (props.curves[selectedVal]) {
    props.curves[selectedVal].lights.push(lightId)
    selectedCurveName.value = selectedVal
  }
}

function forkCurveForFocusedLight() {
  const lightId = props.focusLightId
  if (!lightId || !assignedCurveForFocusedLight.value) return

  const original = assignedCurveForFocusedLight.value
  const baseName = `${original.name}_${lightId.replace('light.', '')}`
  const newName = prompt('Enter name for the forked curve:', baseName)
  if (!newName) return

  // Remove light from original curve
  original.lights = original.lights.filter((id) => id !== lightId)

  // Create deep copy of points for the new curve
  props.curves[newName] = {
    name: newName,
    lights: [lightId],
    points: JSON.parse(JSON.stringify(original.points)),
  }

  selectedCurveName.value = newName
}

// -------------------------------------------------------------
// Global Curve Management Actions
// -------------------------------------------------------------
function createNewCurve() {
  const name = prompt('Enter a unique name for the new global Dim-to-Warm curve:', 'warm_glow')
  if (!name) return

  if (props.curves[name]) {
    alert(`A curve named "${name}" already exists.`)
    return
  }

  props.curves[name] = {
    name,
    lights: [],
    points: [
      [1, 2000],
      [40, 2700],
      [100, 4000],
    ],
  }
  selectedCurveName.value = name
}

function cloneActiveCurve() {
  if (!activeCurve.value) return
  const newName = prompt('Enter a name for the cloned curve:', `${activeCurve.value.name}_copy`)
  if (!newName) return

  props.curves[newName] = {
    name: newName,
    lights: [],
    points: JSON.parse(JSON.stringify(activeCurve.value.points)),
  }
  selectedCurveName.value = newName
}

function deleteActiveCurve() {
  if (!activeCurve.value) return
  if (curveNames.value.length <= 1) {
    alert('You must keep at least one Dim-to-Warm curve.')
    return
  }

  const name = activeCurve.value.name
  if (activeCurve.value.lights.length > 0) {
    const confirm = window.confirm(
      `"${name}" is currently assigned to ${activeCurve.value.lights.length} lights. Are you sure you want to delete it?`
    )
    if (!confirm) return
  }

  delete props.curves[name]
  selectedCurveName.value = curveNames.value[0] || ''
}
</script>
