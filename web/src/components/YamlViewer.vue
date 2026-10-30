<template>
  <div class="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-lg flex flex-col gap-4">
    <!-- Header -->
    <div class="flex items-center justify-between flex-wrap gap-2">
      <div>
        <h3 class="text-base font-bold text-slate-100 flex items-center gap-2">
          <span class="w-2.5 h-2.5 rounded-full bg-cyan-500"></span>
          Home Assistant YAML Configuration
        </h3>
        <p class="text-xs text-slate-400 mt-0.5">
          Bi-directional YAML synchronization for your <code>configuration.yaml</code>.
        </p>
      </div>

      <div class="flex items-center gap-2">
        <button
          @click="showImportModal = true"
          class="text-xs px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 font-semibold transition cursor-pointer"
        >
          📥 Import YAML
        </button>
        <button
          @click="copyYaml"
          :class="[
            'text-xs px-3 py-1.5 rounded-lg font-semibold transition cursor-pointer flex items-center gap-1.5',
            copied ? 'bg-emerald-600 text-white' : 'bg-indigo-600 hover:bg-indigo-500 text-white',
          ]"
        >
          <span>{{ copied ? '✓ Copied!' : '📋 Copy YAML' }}</span>
        </button>
      </div>
    </div>

    <!-- YAML Preview Textarea / Code Box -->
    <div class="relative bg-slate-950 border border-slate-800 rounded-lg p-3 font-mono text-xs text-slate-200 leading-relaxed overflow-x-auto max-h-96">
      <pre><code>{{ yamlOutput }}</code></pre>
    </div>

    <!-- Import Modal -->
    <div
      v-if="showImportModal"
      class="fixed inset-0 bg-black/70 backdrop-blur-sm z-50 flex items-center justify-center p-4"
    >
      <div class="bg-slate-900 border border-slate-700 rounded-xl w-full max-w-2xl p-6 shadow-2xl flex flex-col gap-4">
        <div class="flex justify-between items-center">
          <h4 class="text-base font-bold text-white">Import Existing scheduled_scenes YAML</h4>
          <button @click="showImportModal = false" class="text-slate-400 hover:text-white text-lg">&times;</button>
        </div>

        <p class="text-xs text-slate-400">
          Paste your existing <code>scheduled_scenes:</code> YAML snippet below to populate the visual studio:
        </p>

        <textarea
          v-model="importText"
          rows="12"
          placeholder="scheduled_scenes:
  curves: ...
  programs: ..."
          class="w-full bg-slate-950 border border-slate-800 text-slate-200 font-mono text-xs rounded-lg p-3 focus:outline-none focus:border-indigo-500"
        ></textarea>

        <div v-if="importError" class="text-xs text-rose-400 bg-rose-950/50 border border-rose-900/60 rounded p-2">
          {{ importError }}
        </div>

        <div class="flex justify-end gap-2">
          <button
            @click="showImportModal = false"
            class="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-semibold cursor-pointer"
          >
            Cancel
          </button>
          <button
            @click="handleImport"
            class="px-4 py-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold cursor-pointer"
          >
            Apply to Studio
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { dump, load } from 'js-yaml'
import type { ScheduledScenesConfig } from '../types'

const props = defineProps<{
  config: ScheduledScenesConfig
}>()

const emit = defineEmits<{
  (e: 'update:config', config: ScheduledScenesConfig): void
}>()

const copied = ref(false)
const showImportModal = ref(false)
const importText = ref('')
const importError = ref<string | null>(null)

const yamlOutput = computed(() => {
  const exportData: Record<string, any> = {}

  // 1. Export curves (global dim-to-warm)
  if (Object.keys(props.config.curves).length > 0) {
    exportData.curves = {}
    for (const [key, curve] of Object.entries(props.config.curves)) {
      exportData.curves[key] = {
        lights: curve.lights,
        curve: curve.points,
      }
    }
  }

  // 2. Export brightness_curves
  if (Object.keys(props.config.brightness_curves).length > 0) {
    exportData.brightness_curves = {}
    for (const [key, bCurve] of Object.entries(props.config.brightness_curves)) {
      exportData.brightness_curves[key] = {
        lights: bCurve.lights,
        points: bCurve.points,
      }
    }
  }

  // 3. Export programs
  exportData.programs = props.config.programs.map((p) => {
    return {
      name: p.name,
      lights: p.lights,
      transition_time: p.transition_time,
      transition_interval: p.transition_interval,
      enable_when_light_turn_on: p.enable_when_light_turn_on,
      disable_when_lights_off: p.disable_when_lights_off,
      allow_turn_on_if_any_on: p.allow_turn_on_if_any_on,
      schedule: p.schedule.map((s) => {
        const stepOut: any = {
          time: s.time,
          brightness: s.brightness,
        }
        if (s.temp !== undefined) stepOut.temp = s.temp
        if (s.lights && Object.keys(s.lights).length > 0) stepOut.lights = s.lights
        return stepOut
      }),
    }
  })

  return dump({ scheduled_scenes: exportData }, { indent: 2, lineWidth: -1 })
})

function copyYaml() {
  navigator.clipboard.writeText(yamlOutput.value)
  copied.value = true
  setTimeout(() => {
    copied.value = false
  }, 2000)
}

function handleImport() {
  importError.value = null
  try {
    const parsed = load(importText.value) as any
    if (!parsed) throw new Error('Empty YAML input')

    const root = parsed.scheduled_scenes || parsed
    const newConfig: ScheduledScenesConfig = {
      curves: {},
      brightness_curves: {},
      programs: [],
    }

    // Parse global curves
    if (root.curves) {
      for (const [k, v] of Object.entries<any>(root.curves)) {
        newConfig.curves[k] = {
          name: k,
          lights: Array.isArray(v.lights) ? v.lights : v.lights ? [v.lights] : [],
          points: v.curve || v.points || [],
        }
      }
    }

    // Parse brightness_curves
    if (root.brightness_curves) {
      for (const [k, v] of Object.entries<any>(root.brightness_curves)) {
        newConfig.brightness_curves[k] = {
          name: k,
          lights: Array.isArray(v.lights) ? v.lights : v.lights ? [v.lights] : [],
          points: v.points || [],
        }
      }
    }

    // Parse programs
    const progs = root.programs || root.rooms || (Array.isArray(root) ? root : [])
    newConfig.programs = progs.map((p: any, idx: number) => ({
      name: p.name || `program_${idx + 1}`,
      lights: p.lights || [],
      transition_time: p.transition_time ?? 120,
      transition_interval: p.transition_interval ?? 60,
      enable_when_light_turn_on: p.enable_when_light_turn_on ?? true,
      disable_when_lights_off: p.disable_when_lights_off ?? false,
      allow_turn_on_if_any_on: p.allow_turn_on_if_any_on ?? true,
      schedule: (p.schedule || []).map((s: any, sIdx: number) => ({
        id: `imported-${Date.now()}-${sIdx}`,
        time: s.time,
        brightness: s.brightness,
        temp: s.temp,
        lights: s.lights,
      })),
    }))

    // Hoist any legacy per-program curves into top-level global curves
    for (const p of progs) {
      if (p.curves && typeof p.curves === 'object') {
        for (const [k, v] of Object.entries<any>(p.curves)) {
          if (!newConfig.curves[k]) {
            newConfig.curves[k] = {
              name: k,
              lights: Array.isArray(v.lights) ? v.lights : v.lights ? [v.lights] : [],
              points: v.curve || v.points || [],
            }
          }
        }
      }
    }

    if (!newConfig.programs.length) {
      throw new Error('No programs found in imported YAML')
    }

    emit('update:config', newConfig)
    showImportModal.value = false
    importText.value = ''
  } catch (err: any) {
    importError.value = `Failed to parse YAML: ${err.message}`
  }
}
</script>
