<template>
  <div class="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-lg flex flex-col gap-4">
    <!-- Header with title & curve actions toolbar -->
    <div class="flex items-center justify-between flex-wrap gap-3 border-b border-slate-800/80 pb-3">
      <div class="flex items-center gap-2">
        <span class="text-xs font-bold text-slate-200 uppercase tracking-wider flex items-center gap-1.5">
          <span>📈 Room Brightness Distribution Curves</span>
        </span>
        <span
          v-if="curveNames.length > 0"
          class="text-[10px] bg-slate-800 text-slate-300 border border-slate-700 px-2 py-0.5 rounded-full font-mono"
        >
          {{ visibleCurvesList.length }}/{{ curveNames.length }} visible
        </span>
      </div>

      <!-- Curve Actions Toolbar -->
      <div class="flex items-center gap-2 flex-wrap">
        <button
          type="button"
          @click="createNewCurve"
          class="text-xs px-2.5 py-1 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 font-medium transition cursor-pointer"
        >
          + New Curve
        </button>

        <button
          type="button"
          @click="duplicateActiveCurve"
          :disabled="!activeCurve"
          :class="[
            'text-xs px-2.5 py-1 rounded-lg font-medium transition border',
            activeCurve
              ? 'bg-slate-800 hover:bg-slate-700 text-slate-200 border-slate-700/60 cursor-pointer'
              : 'bg-slate-900 text-slate-600 border-slate-800 cursor-not-allowed',
          ]"
          title="Duplicate active curve"
        >
          Duplicate
        </button>

        <button
          type="button"
          @click="deleteActiveCurve"
          :disabled="!activeCurve || curveNames.length <= 1"
          :class="[
            'text-xs px-2.5 py-1 rounded-lg font-medium transition border',
            activeCurve && curveNames.length > 1
              ? 'bg-rose-950/50 hover:bg-rose-900/70 text-rose-300 border-rose-800/60 cursor-pointer'
              : 'bg-slate-900 text-slate-600 border-slate-800 cursor-not-allowed',
          ]"
          :title="curveNames.length <= 1 ? 'At least one curve is required' : 'Delete active curve'"
        >
          Delete
        </button>

        <button
          type="button"
          @click="showImportModal = true"
          class="text-xs px-2.5 py-1 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 font-medium transition cursor-pointer flex items-center gap-1 border border-slate-700/60"
          title="Import brightness curve YAML"
        >
          <span>📥 Import YAML</span>
        </button>

        <button
          type="button"
          @click="copyCurveYaml"
          :disabled="!activeCurve"
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
          type="button"
          @click="$emit('openGlobalDtw')"
          class="text-xs px-2.5 py-1 rounded-lg bg-amber-950/70 hover:bg-amber-900/80 border border-amber-800/80 text-amber-300 font-medium transition cursor-pointer flex items-center gap-1"
          title="Open Global Dim-to-Warm Curves manager"
        >
          <span>🌡️ Dim-to-Warm Curves &rarr;</span>
        </button>
      </div>
    </div>

    <!-- Multi-Curve Toggle Selector & Quick Filters -->
    <div
      v-if="curveNames.length > 0"
      class="flex items-center justify-between flex-wrap gap-2 bg-slate-950/60 border border-slate-800/90 rounded-lg p-2"
    >
      <div class="flex items-center gap-1.5 flex-wrap" role="list" aria-label="Brightness curves">
        <div
          v-for="name in curveNames"
          :key="name"
          role="listitem"
          data-testid="curve-chip"
          :data-curve-name="name"
          :data-active="activeCurveName === name ? 'true' : 'false'"
          :data-visible="isCurveVisible(name) ? 'true' : 'false'"
          :class="[
            'inline-flex items-center rounded-lg border text-xs transition overflow-hidden',
            activeCurveName === name
              ? `${getCurveTheme(name).bgClass} ${getCurveTheme(name).borderClass} shadow-sm`
              : isCurveVisible(name)
                ? 'bg-slate-900 border-slate-700/80 hover:border-slate-600'
                : 'bg-slate-950/60 border-slate-800/70 opacity-60 hover:opacity-90',
          ]"
        >
          <!-- Visibility Eye Toggle -->
          <button
            type="button"
            data-testid="curve-visibility-toggle"
            :aria-pressed="isCurveVisible(name)"
            :aria-label="`Toggle ${name} visibility`"
            @click.stop="toggleCurveVisibility(name)"
            class="px-2 py-1.5 hover:bg-white/5 flex items-center gap-1.5 cursor-pointer border-r border-slate-800/70 transition"
            :title="isCurveVisible(name) ? `Hide ${name} on canvas` : `Show ${name} on canvas`"
          >
            <span
              class="w-2.5 h-2.5 rounded-full shrink-0 transition-opacity"
              :style="{
                backgroundColor: getCurveTheme(name).stroke,
                opacity: isCurveVisible(name) ? 1 : 0.3,
              }"
            ></span>
            <span
              class="text-[11px] leading-none font-mono"
              :class="isCurveVisible(name) ? 'text-slate-200' : 'text-slate-500'"
              aria-hidden="true"
            >
              {{ isCurveVisible(name) ? '👁' : '✕' }}
            </span>
          </button>

          <!-- Curve Selection Button -->
          <button
            type="button"
            data-testid="curve-select-btn"
            @click="selectCurve(name)"
            class="px-2.5 py-1.5 flex items-center gap-1.5 cursor-pointer hover:bg-white/5 transition"
          >
            <span
              :class="[
                'font-mono font-semibold',
                activeCurveName === name ? getCurveTheme(name).textClass : 'text-slate-200',
              ]"
            >
              {{ name }}
            </span>

            <span
              class="text-[10px] px-1.5 py-0.2 rounded-full font-mono bg-slate-900/90 text-slate-400 border border-slate-800"
              :title="`${brightnessCurves[name]?.lights.length || 0} assigned fixture(s)`"
            >
              {{ brightnessCurves[name]?.lights.length || 0 }}
            </span>

            <span
              v-if="activeCurveName === name"
              data-testid="active-curve-badge"
              :class="[
                'text-[9px] uppercase tracking-wider font-bold px-1.5 py-0.2 rounded border',
                getCurveTheme(name).badgeClass,
              ]"
            >
              Active
            </span>
          </button>
        </div>
      </div>

      <!-- Quick Visibility Controls -->
      <div class="flex items-center gap-1 shrink-0">
        <span class="text-[10px] text-slate-500 uppercase tracking-wider mr-1">Show:</span>
        <button
          type="button"
          data-testid="quick-show-all"
          @click="showAllCurves"
          class="text-[11px] px-2 py-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-200 font-medium transition cursor-pointer"
        >
          All
        </button>
        <button
          type="button"
          data-testid="quick-show-none"
          @click="showOnlyActiveCurve"
          class="text-[11px] px-2 py-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-200 font-medium transition cursor-pointer"
          title="Hide all curves except the active curve"
        >
          None
        </button>
        <button
          type="button"
          data-testid="quick-show-room"
          @click="showRoomCurves"
          :disabled="roomLights.length === 0"
          :class="[
            'text-[11px] px-2 py-1 rounded font-medium transition',
            roomLights.length > 0
              ? 'bg-slate-800 hover:bg-slate-700 text-slate-200 cursor-pointer'
              : 'bg-slate-900 text-slate-600 cursor-not-allowed',
          ]"
          title="Show only curves assigned to lights in this room"
        >
          Room Fixtures
        </button>
      </div>
    </div>

    <!-- Active Curve Details & Canvas -->
    <div v-if="activeCurve" class="flex flex-col gap-4">
      <!-- Active Curve Summary Inspector Header -->
      <div
        :class="[
          'flex items-center justify-between text-xs text-slate-400 flex-wrap gap-2 rounded-lg border px-3 py-2.5 transition-colors',
          activeCurveColor.bgClass,
          activeCurveColor.borderClass,
        ]"
      >
        <div class="flex items-center gap-2 flex-wrap">
          <span
            class="w-2.5 h-2.5 rounded-full shrink-0"
            :style="{ backgroundColor: activeCurveColor.stroke }"
          ></span>

          <!-- Active curve name or inline rename input -->
          <div v-if="!isRenaming" class="flex items-center gap-1.5">
            <span :class="['font-bold font-mono', activeCurveColor.textClass]">{{ activeCurve.name }}</span>
            <button
              type="button"
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
                type="button"
                @click="confirmRename"
                class="px-2 py-0.5 rounded bg-emerald-600 hover:bg-emerald-500 text-white text-[11px] font-bold cursor-pointer"
                title="Save new name"
              >
                ✓
              </button>
              <button
                type="button"
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
            :class="[
              'inline-flex items-center gap-1 bg-slate-900/90 border px-1.5 py-0.5 rounded text-[11px] font-mono',
              activeCurveColor.textClass,
              activeCurveColor.borderClass,
            ]"
          >
            <span>{{ getLightName(lt) }}</span>
            <button
              type="button"
              @click="detachLight(lt)"
              class="text-slate-500 hover:text-rose-400 cursor-pointer text-xs"
              title="Remove fixture from curve"
            >
              &times;
            </button>
          </span>
          <div class="relative inline-block" v-if="unassignedRoomLights.length > 0">
            <button
              type="button"
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
                type="button"
                @click="attachLight(lt)"
                class="w-full text-left px-3 py-1 text-xs text-slate-200 hover:bg-slate-800 font-mono block cursor-pointer"
              >
                {{ getLightName(lt) }}
              </button>
            </div>
          </div>
        </div>

        <div class="flex items-center gap-2">
          <!-- Panel Active Curve Quick Switcher -->
          <div v-if="curveNames.length > 1" class="inline-flex items-center gap-1">
            <button
              type="button"
              @click="cycleActiveCurve(-1)"
              class="px-1.5 py-0.5 rounded bg-slate-900/90 hover:bg-slate-800 text-slate-300 border border-slate-700 cursor-pointer text-[11px]"
              title="Previous curve"
              aria-label="Previous curve"
            >
              &lsaquo;
            </button>
            <button
              type="button"
              @click="cycleActiveCurve(1)"
              class="px-1.5 py-0.5 rounded bg-slate-900/90 hover:bg-slate-800 text-slate-300 border border-slate-700 cursor-pointer text-[11px]"
              title="Next curve"
              aria-label="Next curve"
            >
              &rsaquo;
            </button>
          </div>

          <span class="text-[11px] text-slate-400">
            Click canvas to add point. Double-click point to delete.
          </span>
        </div>
      </div>

      <!-- 2D Coordinate SVG Graph Canvas -->
      <div class="relative select-none bg-slate-950/70 border border-slate-800/80 rounded-lg p-2">
        <!-- Hover Tooltip for Inactive Curves -->
        <div
          v-if="hoveredCurveName && hoveredCurveName !== activeCurveName"
          class="absolute top-3 right-3 z-20 pointer-events-none bg-slate-900/95 border border-slate-700 text-slate-200 text-[11px] font-mono px-2.5 py-1 rounded-md shadow-lg flex items-center gap-1.5"
        >
          <span
            class="w-2 h-2 rounded-full"
            :style="{ backgroundColor: getCurveTheme(hoveredCurveName).stroke }"
          ></span>
          <span>Click to edit {{ hoveredCurveName }}</span>
        </div>

        <svg
          ref="svgRef"
          data-testid="curve-canvas"
          :viewBox="`0 0 ${svgWidth} ${svgHeight}`"
          class="w-full h-48 sm:h-64 cursor-crosshair overflow-visible block touch-none select-none"
          @mousedown="onCanvasMouseDown"
        >
          <defs>
            <linearGradient
              v-for="curve in visibleCurvesList"
              :key="`grad-${curve.name}`"
              :id="getCurveGradientId(curve.name)"
              x1="0%"
              y1="0%"
              x2="0%"
              y2="100%"
            >
              <stop offset="0%" :stop-color="getCurveTheme(curve.name).fill" stop-opacity="0.35" />
              <stop offset="100%" :stop-color="getCurveTheme(curve.name).fill" stop-opacity="0.0" />
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

          <!-- Inactive Visible Curves (rendered underneath active curve) -->
          <g
            v-for="curve in inactiveVisibleCurves"
            :key="`inactive-${curve.name}`"
            data-curve-layer="inactive"
            :data-curve-name="curve.name"
          >
            <!-- Wider invisible hit target for easy selection -->
            <path
              :d="getCurveLinePath(curve)"
              fill="none"
              stroke="transparent"
              stroke-width="12"
              class="cursor-pointer"
              @mouseenter="hoveredCurveName = curve.name"
              @mouseleave="hoveredCurveName = null"
              @mousedown.stop="selectCurve(curve.name)"
            />

            <!-- Visible inactive curve stroke -->
            <path
              :d="getCurveLinePath(curve)"
              fill="none"
              :stroke="getCurveTheme(curve.name).stroke"
              stroke-width="2"
              :opacity="hoveredCurveName === curve.name ? 0.95 : 0.7"
              :data-curve-path="curve.name"
              class="cursor-pointer transition-opacity"
              @mouseenter="hoveredCurveName = curve.name"
              @mouseleave="hoveredCurveName = null"
              @mousedown.stop="selectCurve(curve.name)"
            >
              <title>{{ curve.name }} — click to edit</title>
            </path>

            <!-- Reference control points for inactive visible curves -->
            <circle
              v-for="(pt, idx) in curve.points"
              :key="`inactive-pt-${curve.name}-${idx}`"
              :cx="scaleX(pt[0])"
              :cy="scaleY(pt[1])"
              :r="hoveredCurveName === curve.name ? 5 : 4"
              :fill="getCurveTheme(curve.name).stroke"
              stroke="#0f172a"
              stroke-width="1.5"
              :opacity="hoveredCurveName === curve.name ? 0.95 : 0.75"
              data-inactive-point="true"
              class="cursor-pointer"
              @mouseenter="hoveredCurveName = curve.name"
              @mouseleave="hoveredCurveName = null"
              @mousedown.stop="selectCurve(curve.name)"
            >
              <title>{{ curve.name }}: Room {{ pt[0] }}% → Fixture {{ pt[1] }}%</title>
            </circle>
          </g>

          <!-- Active Curve Layer (rendered on top when visible) -->
          <g
            v-if="isActiveCurveVisible"
            data-curve-layer="active"
            :data-curve-name="activeCurve.name"
          >
            <!-- Filled Curve Area -->
            <path
              :d="activeAreaPath"
              :fill="`url(#${getCurveGradientId(activeCurve.name)})`"
            />

            <!-- Main Active Curve Line -->
            <path
              :d="activeCurvePath"
              fill="none"
              :stroke="activeCurveColor.stroke"
              stroke-width="3"
              :data-curve-path="activeCurve.name"
            />

            <!-- Draggable Control Points -->
            <g v-for="(pt, idx) in activeCurve.points" :key="`active-pt-${idx}`">
              <circle
                :cx="scaleX(pt[0])"
                :cy="scaleY(pt[1])"
                :r="activePointIdx === idx || hoveredPointIdx === idx ? 8 : 6"
                :fill="activeCurveColor.stroke"
                :stroke="activePointIdx === idx || hoveredPointIdx === idx ? '#ffffff' : '#0f172a'"
                :stroke-width="activePointIdx === idx ? 3 : 2"
                data-active-point="true"
                class="cursor-grab active:cursor-grabbing"
                @mouseenter="hoveredPointIdx = idx"
                @mouseleave="hoveredPointIdx = null"
                @mousedown.stop="onPointMouseDown(idx, $event)"
                @dblclick.stop="removePoint(idx)"
              >
                <title>{{ activeCurve.name }}: Room {{ pt[0] }}% → Fixture {{ pt[1] }}%</title>
              </circle>
            </g>
          </g>

          <!-- Vertical Room Brightness Reference Cursor -->
          <g
            v-if="effectiveRoomBrightness !== null"
            data-testid="room-brightness-cursor"
            class="pointer-events-none"
          >
            <line
              :x1="scaleX(effectiveRoomBrightness)"
              :y1="PAD_Y"
              :x2="scaleX(effectiveRoomBrightness)"
              :y2="svgHeight - PAD_Y"
              stroke="#38bdf8"
              stroke-width="1.5"
              stroke-dasharray="4 3"
            />
            <text
              :x="scaleX(effectiveRoomBrightness)"
              :y="PAD_Y - 5"
              text-anchor="middle"
              fill="#38bdf8"
              font-size="10"
              font-family="monospace"
              font-weight="bold"
            >
              {{ effectiveRoomBrightness }}%
            </text>

            <!-- Intersection dots for all visible curves -->
            <circle
              v-for="item in cursorIntersections"
              :key="`cursor-dot-${item.name}`"
              :cx="scaleX(effectiveRoomBrightness)"
              :cy="scaleY(item.fixtureBrightness)"
              r="4.5"
              :fill="item.color.stroke"
              stroke="#ffffff"
              stroke-width="1.5"
              data-cursor-intersection="true"
              :data-curve-name="item.name"
            >
              <title>{{ item.name }}: {{ item.fixtureBrightness }}% at {{ effectiveRoomBrightness }}% room</title>
            </circle>
          </g>
        </svg>

        <!-- Live Cursor Intersection Readout Strip -->
        <div
          v-if="effectiveRoomBrightness !== null && cursorIntersections.length > 0"
          data-testid="cursor-readout"
          class="flex items-center gap-2 flex-wrap px-3 py-1.5 mt-1 bg-slate-900/80 border border-slate-800/80 rounded text-[11px] font-mono"
        >
          <span class="text-sky-400 font-semibold">Room {{ effectiveRoomBrightness }}%:</span>
          <span
            v-for="item in cursorIntersections"
            :key="`readout-${item.name}`"
            class="inline-flex items-center gap-1 px-1.5 py-0.5 rounded bg-slate-950/90 border border-slate-800"
          >
            <span
              class="w-2 h-2 rounded-full"
              :style="{ backgroundColor: item.color.stroke }"
            ></span>
            <span class="text-slate-300">{{ item.name }}</span>
            <span :class="['font-bold', item.color.textClass]">{{ item.fixtureBrightness }}%</span>
          </span>
        </div>

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
          <span :class="activeCurveColor.textClass">R:</span>
          <input
            type="number"
            min="0"
            max="100"
            step="1"
            v-model.number="pt[0]"
            @change="onPointInputChange"
            class="w-10 bg-slate-900 border border-slate-700 text-center rounded px-0.5 py-0.5 text-xs text-slate-200"
          />
          <span class="text-slate-400">%</span>
          <span :class="[activeCurveColor.textClass, 'ml-1']">F:</span>
          <input
            type="number"
            min="0"
            max="100"
            step="1"
            v-model.number="pt[1]"
            @change="onPointInputChange"
            class="w-10 bg-slate-900 border border-slate-700 text-center rounded px-0.5 py-0.5 text-xs text-slate-200"
          />
          <span class="text-slate-400">%</span>
          <button
            v-if="activeCurve.points.length > 2"
            type="button"
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
            type="button"
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
            type="button"
            @click="closeImportModal"
            class="text-xs px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 transition cursor-pointer"
          >
            Cancel
          </button>
          <button
            type="button"
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
import type { BrightnessCurve, CurvePaletteColor } from '../types'
import {
  getSvgCoordinates,
  getCurveGradientId,
  buildCurveLinePath,
  buildCurveAreaPath,
} from '../utils/svg'
import { getCurveColor, resolveCurveColors } from '../utils/color'
import { evaluateBrightnessCurve } from '../utils/interpolator'
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
    roomBrightness?: number | null
    previewRoomBrightness?: number | null
  }>(),
  {
    roomLights: () => [],
    roomBrightness: null,
    previewRoomBrightness: null,
  }
)

const emit = defineEmits<{
  (e: 'openGlobalDtw'): void
  (e: 'update:previewRoomBrightness', val: number): void
}>()

const curveNames = computed(() => Object.keys(props.brightnessCurves))

// Deterministic color palette mapping for all curves
const curveColorMap = computed(() => resolveCurveColors(curveNames.value))

function getCurveTheme(name: string): CurvePaletteColor {
  return curveColorMap.value[name] || getCurveColor(name)
}

function getRoomCurveNames(): string[] {
  if (!props.roomLights || props.roomLights.length === 0) return []
  return curveNames.value.filter((name) =>
    props.brightnessCurves[name]?.lights.some((lt) => props.roomLights.includes(lt))
  )
}

function getDefaultVisibleCurves(): string[] {
  const roomCurves = getRoomCurveNames()
  return roomCurves.length > 0 ? roomCurves : [...curveNames.value]
}

// Multi-curve visibility & active editing state
const visibleCurveNames = ref<string[]>(getDefaultVisibleCurves())
const activeCurveName = ref<string>(
  visibleCurveNames.value[0] || curveNames.value[0] || ''
)

let previousCurveNames = [...curveNames.value]

watch(curveNames, (names) => {
  const prevSet = new Set(previousCurveNames)
  const nameSet = new Set(names)

  const filtered = visibleCurveNames.value.filter((n) => nameSet.has(n))
  for (const n of names) {
    if (!prevSet.has(n) && !filtered.includes(n)) {
      filtered.push(n)
    }
  }

  visibleCurveNames.value =
    filtered.length > 0 || names.length === 0 ? filtered : getDefaultVisibleCurves()

  if (!nameSet.has(activeCurveName.value)) {
    activeCurveName.value =
      visibleCurveNames.value.find((n) => nameSet.has(n)) || names[0] || ''
  }

  previousCurveNames = [...names]
})

watch(
  () => props.roomLights.join('|'),
  (newVal, oldVal) => {
    if (newVal === oldVal) return
    const defaults = getDefaultVisibleCurves()
    visibleCurveNames.value = defaults
    if (!defaults.includes(activeCurveName.value)) {
      activeCurveName.value = defaults[0] || curveNames.value[0] || ''
    }
  }
)

const activeCurve = computed<BrightnessCurve | null>(() => {
  return (
    props.brightnessCurves[activeCurveName.value] ||
    Object.values(props.brightnessCurves)[0] ||
    null
  )
})

const activeCurveColor = computed<CurvePaletteColor>(() => {
  return getCurveTheme(activeCurve.value?.name || activeCurveName.value)
})

function isCurveVisible(name: string): boolean {
  return visibleCurveNames.value.includes(name)
}

const isActiveCurveVisible = computed(() => {
  return !!activeCurve.value && isCurveVisible(activeCurve.value.name)
})

const visibleCurvesList = computed<BrightnessCurve[]>(() => {
  return curveNames.value
    .filter((name) => isCurveVisible(name))
    .map((name) => props.brightnessCurves[name])
    .filter((c): c is BrightnessCurve => Boolean(c))
})

const inactiveVisibleCurves = computed<BrightnessCurve[]>(() => {
  return visibleCurvesList.value.filter((c) => c.name !== activeCurve.value?.name)
})

function toggleCurveVisibility(name: string) {
  if (isCurveVisible(name)) {
    visibleCurveNames.value = visibleCurveNames.value.filter((n) => n !== name)
  } else {
    visibleCurveNames.value = [...visibleCurveNames.value, name]
  }
}

function selectCurve(name: string) {
  if (!props.brightnessCurves[name]) return
  activeCurveName.value = name
  if (!isCurveVisible(name)) {
    visibleCurveNames.value = [...visibleCurveNames.value, name]
  }
}

function cycleActiveCurve(delta: number) {
  const names = curveNames.value
  if (names.length <= 1) return
  const currentIdx = names.indexOf(activeCurveName.value)
  const nextIdx = ((currentIdx === -1 ? 0 : currentIdx) + delta + names.length) % names.length
  selectCurve(names[nextIdx])
}

function showAllCurves() {
  visibleCurveNames.value = [...curveNames.value]
}

function showOnlyActiveCurve() {
  if (activeCurve.value && props.brightnessCurves[activeCurve.value.name]) {
    visibleCurveNames.value = [activeCurve.value.name]
  } else {
    visibleCurveNames.value = []
  }
}

function showRoomCurves() {
  const roomCurves = getRoomCurveNames()
  visibleCurveNames.value = roomCurves
  if (roomCurves.length > 0 && !roomCurves.includes(activeCurveName.value)) {
    activeCurveName.value = roomCurves[0]
  }
}

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
      newCurveNameInput.value = res.name
      if (activeCurve.value && res.name !== activeCurve.value.name) {
        importDestination.value = 'new'
      }
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
    if (!isCurveVisible(trimmed)) {
      visibleCurveNames.value = [...visibleCurveNames.value, trimmed]
    }
    activeCurveName.value = trimmed
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

watch(activeCurveName, () => {
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

  const wasVisible = isCurveVisible(oldName)
  const curveToUpdate = props.brightnessCurves[oldName]
  if (curveToUpdate) {
    curveToUpdate.name = trimmedName
    delete props.brightnessCurves[oldName]
    props.brightnessCurves[trimmedName] = curveToUpdate
  }

  if (wasVisible) {
    visibleCurveNames.value = visibleCurveNames.value.map((n) =>
      n === oldName ? trimmedName : n
    )
  }
  activeCurveName.value = trimmedName
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
const hoveredCurveName = ref<string | null>(null)
const localPreviewBrightness = ref<number | null>(null)

const effectiveRoomBrightness = computed<number | null>(() => {
  if (props.roomBrightness !== null && props.roomBrightness !== undefined) {
    return Math.max(0, Math.min(100, Math.round(props.roomBrightness)))
  }
  if (props.previewRoomBrightness !== null && props.previewRoomBrightness !== undefined) {
    return Math.max(0, Math.min(100, Math.round(props.previewRoomBrightness)))
  }
  return localPreviewBrightness.value
})

const cursorIntersections = computed(() => {
  if (effectiveRoomBrightness.value === null) return []
  const roomVal = effectiveRoomBrightness.value
  return visibleCurvesList.value.map((curve) => ({
    name: curve.name,
    color: getCurveTheme(curve.name),
    fixtureBrightness: evaluateBrightnessCurve(curve.points, roomVal),
  }))
})

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

function getCurveLinePath(curve: BrightnessCurve): string {
  return buildCurveLinePath(curve.points, scaleX, scaleY)
}

const activeCurvePath = computed(() => {
  if (!activeCurve.value) return ''
  return buildCurveLinePath(activeCurve.value.points, scaleX, scaleY)
})

const activeAreaPath = computed(() => {
  if (!activeCurve.value) return ''
  return buildCurveAreaPath(activeCurve.value.points, scaleX, scaleY)
})

function onPointInputChange() {
  if (!activeCurve.value) return
  for (const pt of activeCurve.value.points) {
    pt[0] = Math.max(0, Math.min(100, Math.round(Number(pt[0]) || 0)))
    pt[1] = Math.max(0, Math.min(100, Math.round(Number(pt[1]) || 0)))
  }
  activeCurve.value.points.sort((a, b) => a[0] - b[0])
}

function onPointMouseDown(idx: number, e: MouseEvent) {
  e.preventDefault()
  activePointIdx.value = idx
  if (activeCurve.value && activeCurve.value.points[idx]) {
    const roomB = activeCurve.value.points[idx][0]
    localPreviewBrightness.value = roomB
    emit('update:previewRoomBrightness', roomB)
  }
  window.addEventListener('mousemove', onWindowMouseMove)
  window.addEventListener('mouseup', onWindowMouseUp)
}

function onCanvasMouseDown(e: MouseEvent) {
  if (!svgRef.value || !activeCurve.value || !isActiveCurveVisible.value) return
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
    activePointIdx.value = activeCurve.value.points.findIndex(
      (pt) => pt[0] === roomB && pt[1] === fixB
    )
    localPreviewBrightness.value = roomB
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
  activePointIdx.value = activeCurve.value.points.findIndex(
    (pt) => pt[0] === roomB && pt[1] === fixB
  )

  localPreviewBrightness.value = roomB
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
  if (!isCurveVisible(trimmed)) {
    visibleCurveNames.value = [...visibleCurveNames.value, trimmed]
  }
  activeCurveName.value = trimmed
}

function duplicateActiveCurve() {
  if (!activeCurve.value) return
  const suggested = `${activeCurve.value.name}_copy`
  const name = prompt('Enter a unique name for the duplicated curve:', suggested)
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
    points: JSON.parse(JSON.stringify(activeCurve.value.points)),
  }
  if (!isCurveVisible(trimmed)) {
    visibleCurveNames.value = [...visibleCurveNames.value, trimmed]
  }
  activeCurveName.value = trimmed
}

function deleteActiveCurve() {
  if (!activeCurve.value) return
  if (curveNames.value.length <= 1) {
    alert('You must keep at least one brightness curve.')
    return
  }

  const name = activeCurve.value.name
  const assignedCount = activeCurve.value.lights.length
  if (assignedCount > 0) {
    const confirmed = window.confirm(
      `"${name}" is currently assigned to ${assignedCount} fixture(s). Are you sure you want to delete it?`
    )
    if (!confirmed) return
  }

  delete props.brightnessCurves[name]
  visibleCurveNames.value = visibleCurveNames.value.filter((n) => n !== name)
  const remaining = Object.keys(props.brightnessCurves)
  activeCurveName.value =
    visibleCurveNames.value.find((n) => remaining.includes(n)) || remaining[0] || ''
}
</script>
