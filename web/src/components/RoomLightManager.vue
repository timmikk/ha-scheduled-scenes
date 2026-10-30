<template>
  <div class="flex flex-col gap-2">
    <!-- Header Row -->
    <div class="flex items-center justify-between gap-3 flex-wrap">
      <div class="flex items-center gap-2">
        <label class="text-[11px] font-semibold text-slate-400 uppercase tracking-wider flex items-center gap-1.5">
          <span>💡 Room Fixtures</span>
          <span class="text-[10px] bg-slate-800 text-slate-300 px-1.5 py-0.2 rounded-full font-mono">
            {{ modelValue.length }}
          </span>
        </label>
      </div>

      <!-- Add Light Button Trigger -->
      <div class="relative">
        <button
          ref="triggerBtnRef"
          @click="toggleDropdown"
          class="text-xs px-2.5 py-1 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white font-semibold transition cursor-pointer flex items-center gap-1.5 shadow-sm shadow-indigo-500/20"
        >
          <span>+ Add Light</span>
          <span class="text-[10px] opacity-80">&blacktriangledown;</span>
        </button>

        <!-- Dropdown / Popover -->
        <div
          v-if="isOpen"
          ref="dropdownRef"
          class="absolute right-0 mt-2 w-80 sm:w-96 bg-slate-900 border border-slate-700/80 rounded-xl shadow-2xl z-50 p-3.5 flex flex-col gap-3 backdrop-blur-md"
        >
          <div class="flex items-center justify-between border-b border-slate-800 pb-2">
            <span class="text-xs font-bold text-slate-200">Select Fixtures from Home Assistant</span>
            <button
              @click="isOpen = false"
              class="text-slate-400 hover:text-slate-200 text-sm cursor-pointer"
            >
              &times;
            </button>
          </div>

          <!-- Search Input -->
          <div class="relative">
            <input
              v-model="searchQuery"
              type="text"
              placeholder="Search by name, entity ID, or area..."
              class="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-1.5 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-indigo-500"
              autofocus
            />
          </div>

          <!-- Area Filter Tabs -->
          <div class="flex items-center gap-1 overflow-x-auto pb-1 scrollbar-none text-[11px]">
            <button
              @click="selectedAreaId = null"
              :class="[
                'px-2 py-0.5 rounded-md whitespace-nowrap transition cursor-pointer font-medium',
                selectedAreaId === null
                  ? 'bg-indigo-600 text-white'
                  : 'bg-slate-950 text-slate-400 hover:text-slate-200',
              ]"
            >
              All Areas
            </button>
            <button
              v-for="area in areas"
              :key="area.area_id"
              @click="selectedAreaId = area.area_id"
              :class="[
                'px-2 py-0.5 rounded-md whitespace-nowrap transition cursor-pointer font-medium flex items-center gap-1',
                selectedAreaId === area.area_id
                  ? 'bg-indigo-600 text-white'
                  : 'bg-slate-950 text-slate-400 hover:text-slate-200',
              ]"
            >
              <span>{{ area.name }}</span>
            </button>
          </div>

          <!-- Entity List -->
          <div class="max-h-56 overflow-y-auto flex flex-col gap-1 pr-1">
            <div
              v-if="filteredLights.length === 0"
              class="text-center py-4 text-xs text-slate-500"
            >
              No unassigned fixtures found matching filter.
            </div>

            <button
              v-for="light in filteredLights"
              :key="light.entity_id"
              @click="addLight(light.entity_id)"
              class="w-full text-left bg-slate-950/70 hover:bg-slate-800 border border-slate-800/80 hover:border-indigo-500/50 rounded-lg p-2 transition flex items-center justify-between gap-2 group cursor-pointer"
            >
              <div class="flex flex-col min-w-0">
                <div class="text-xs font-semibold text-slate-200 group-hover:text-indigo-300 truncate">
                  {{ light.name }}
                </div>
                <div class="text-[10px] font-mono text-slate-500 truncate">
                  {{ light.entity_id }}
                </div>
              </div>

              <div class="flex items-center gap-2 shrink-0">
                <span
                  v-if="light.area_name"
                  class="text-[10px] bg-slate-900 border border-slate-800 text-slate-400 px-1.5 py-0.5 rounded"
                >
                  {{ light.area_name }}
                </span>
                <span
                  v-if="light.min_color_temp_kelvin"
                  class="text-[10px] bg-amber-950/60 border border-amber-900/60 text-amber-300 font-mono px-1 py-0.5 rounded"
                  title="Color Temperature Range"
                >
                  {{ light.min_color_temp_kelvin }}-{{ light.max_color_temp_kelvin }}K
                </span>
                <span class="text-indigo-400 font-bold text-xs opacity-0 group-hover:opacity-100 transition-opacity">
                  + Add
                </span>
              </div>
            </button>
          </div>

          <!-- Custom Entity ID Manual Adder -->
          <div class="border-t border-slate-800 pt-2.5 flex flex-col gap-1.5">
            <label class="text-[10px] font-semibold text-slate-400 uppercase tracking-wider">
              Add Custom Entity ID
            </label>
            <div class="flex items-center gap-1.5">
              <input
                v-model="customEntityId"
                @keydown.enter.prevent="addCustomEntity"
                type="text"
                placeholder="light.my_fixture"
                class="flex-1 bg-slate-950 border border-slate-700 rounded-lg px-2.5 py-1 text-xs font-mono text-slate-200 placeholder-slate-600 focus:outline-none focus:border-indigo-500"
              />
              <button
                @click="addCustomEntity"
                :disabled="!isValidCustomEntity"
                class="px-2.5 py-1 rounded-lg bg-slate-800 hover:bg-slate-700 disabled:opacity-40 disabled:hover:bg-slate-800 text-slate-200 text-xs font-medium transition cursor-pointer"
              >
                Add
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Active Fixture Badge Chips -->
    <div class="flex flex-wrap gap-1.5 items-center">
      <div
        v-if="modelValue.length === 0"
        class="text-xs text-slate-500 italic py-1"
      >
        No lights assigned to this room yet. Click "+ Add Light" to assign fixtures.
      </div>

      <div
        v-for="entityId in modelValue"
        :key="entityId"
        class="group text-xs bg-slate-950 border border-slate-800 hover:border-slate-700 text-slate-300 pl-2.5 pr-1.5 py-1 rounded-lg font-mono flex items-center gap-2 transition shadow-sm"
      >
        <span class="w-2 h-2 rounded-full bg-indigo-400"></span>
        <div class="flex flex-col">
          <span class="text-[11px] font-sans font-semibold text-slate-200 leading-tight">
            {{ getLightDisplayName(entityId) }}
          </span>
          <span class="text-[9px] text-slate-500 font-mono leading-none">
            {{ entityId }}
          </span>
        </div>

        <!-- Dim-to-Warm Curve Quick Badge Button -->
        <div class="flex items-center gap-1 ml-1">
          <button
            v-if="getLightCurveName(entityId)"
            type="button"
            @click.stop="$emit('openLightDtw', entityId)"
            class="text-[10px] bg-amber-950/70 border border-amber-800/80 hover:border-amber-500 text-amber-300 px-1.5 py-0.5 rounded cursor-pointer transition flex items-center gap-1 font-mono"
            :title="`Global Dim-to-Warm: ${getLightCurveName(entityId)}. Click to edit.`"
          >
            <span>🌡️</span>
            <span>{{ getLightCurveName(entityId) }}</span>
          </button>
          <button
            v-else
            type="button"
            @click.stop="$emit('openLightDtw', entityId)"
            class="text-[10px] text-slate-500 hover:text-amber-400 border border-transparent hover:border-slate-700 px-1 py-0.5 rounded cursor-pointer transition"
            title="Assign Global Dim-to-Warm Curve"
          >
            + DTW
          </button>

          <!-- Settings Gear Icon -->
          <button
            type="button"
            @click.stop="$emit('openLightDtw', entityId)"
            class="text-slate-500 hover:text-amber-300 p-0.5 rounded hover:bg-slate-800 transition cursor-pointer"
            title="Configure Dim-to-Warm curve for this light"
          >
            <svg class="w-3.5 h-3.5" viewBox="0 0 20 20" fill="currentColor">
              <path
                fill-rule="evenodd"
                d="M11.49 3.17c-.38-1.56-2.6-1.56-2.98 0a1.532 1.532 0 01-2.286.948c-1.372-.836-2.942.734-2.106 2.106.54.886.061 2.042-.947 2.287-1.561.379-1.561 2.6 0 2.978a1.532 1.532 0 01.947 2.287c-.836 1.372.734 2.942 2.106 2.106a1.532 1.532 0 012.287.947c.379 1.561 2.6 1.561 2.978 0a1.533 1.533 0 012.287-.947c1.372.836 2.942-.734 2.106-2.106a1.533 1.533 0 01.947-2.287c1.561-.379 1.561-2.6 0-2.978a1.532 1.532 0 01-.947-2.287c.836-1.372-.734-2.942-2.106-2.106a1.532 1.532 0 01-2.287-.947zM10 13a3 3 0 100-6 3 3 0 000 6z"
                clip-rule="evenodd"
              />
            </svg>
          </button>
        </div>

        <button
          @click="removeLight(entityId)"
          class="ml-1 text-slate-500 hover:text-rose-400 p-0.5 rounded transition cursor-pointer hover:bg-rose-950/40"
          :title="`Remove ${entityId} from room`"
        >
          <svg class="w-3.5 h-3.5" viewBox="0 0 20 20" fill="currentColor">
            <path
              fill-rule="evenodd"
              d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z"
              clip-rule="evenodd"
            />
          </svg>
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import type { DimToWarmCurve } from '../types'
import { entityService } from '../services/entityService'

const props = withDefaults(
  defineProps<{
    modelValue: string[]
    roomName?: string
    curves?: Record<string, DimToWarmCurve>
  }>(),
  {
    curves: () => ({}),
  }
)

const emit = defineEmits<{
  (e: 'update:modelValue', value: string[]): void
  (e: 'openLightDtw', entityId: string): void
}>()

const isOpen = ref(false)
const searchQuery = ref('')
const selectedAreaId = ref<string | null>(null)
const customEntityId = ref('')
const dropdownRef = ref<HTMLElement | null>(null)
const triggerBtnRef = ref<HTMLElement | null>(null)

const areas = computed(() => entityService.getAllAreas())

const availableLights = computed(() => {
  return entityService.getAllLights()
})

const filteredLights = computed(() => {
  let list = availableLights.value.filter((l) => !props.modelValue.includes(l.entity_id))

  if (selectedAreaId.value) {
    list = list.filter((l) => l.area_id === selectedAreaId.value)
  }

  if (searchQuery.value.trim()) {
    const q = searchQuery.value.trim().toLowerCase()
    list = list.filter(
      (l) =>
        l.entity_id.toLowerCase().includes(q) ||
        l.name.toLowerCase().includes(q) ||
        (l.area_name && l.area_name.toLowerCase().includes(q)),
    )
  }

  return list
})

const isValidCustomEntity = computed(() => {
  const val = customEntityId.value.trim().toLowerCase()
  return val.startsWith('light.') && val.length > 6 && !props.modelValue.includes(val)
})

function getLightCurveName(entityId: string): string | null {
  for (const [name, curve] of Object.entries(props.curves)) {
    if (curve.lights.includes(entityId)) return name
  }
  return null
}

function toggleDropdown() {
  isOpen.value = !isOpen.value
  if (isOpen.value) {
    searchQuery.value = ''
    if (props.roomName) {
      const normalizedRoom = props.roomName.toLowerCase().replace(/[^a-z0-9]/g, '_')
      const matchedArea = areas.value.find(
        (a) => a.area_id === normalizedRoom || a.name.toLowerCase() === props.roomName?.toLowerCase(),
      )
      if (matchedArea) {
        selectedAreaId.value = matchedArea.area_id
      }
    }
  }
}

function addLight(entityId: string) {
  if (props.modelValue.includes(entityId)) return
  emit('update:modelValue', [...props.modelValue, entityId])
}

function removeLight(entityId: string) {
  emit(
    'update:modelValue',
    props.modelValue.filter((id) => id !== entityId),
  )
}

function addCustomEntity() {
  const val = customEntityId.value.trim().toLowerCase()
  if (!isValidCustomEntity.value) return
  addLight(val)
  customEntityId.value = ''
}

function getLightDisplayName(entityId: string): string {
  return entityService.getFriendlyName(entityId)
}

function handleClickOutside(event: MouseEvent) {
  if (
    isOpen.value &&
    dropdownRef.value &&
    !dropdownRef.value.contains(event.target as Node) &&
    triggerBtnRef.value &&
    !triggerBtnRef.value.contains(event.target as Node)
  ) {
    isOpen.value = false
  }
}

onMounted(() => {
  window.addEventListener('click', handleClickOutside)
})

onUnmounted(() => {
  window.removeEventListener('click', handleClickOutside)
})
</script>
