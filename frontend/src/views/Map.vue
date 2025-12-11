<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { hexes, bases, units as unitsApi } from '../api'

const allHexes = ref([])
const allBases = ref([])
const selectedHex = ref(null)
const hexUnits = ref([])
const loading = ref(true)

// Map image dimensions
const MAP_IMAGE_WIDTH = 4832
const MAP_IMAGE_HEIGHT = 7563

// Map geometry - columns go DOWN
// Even columns (0, 2, 4...): 39 hexes
// Odd columns (1, 3, 5...): 38 hexes (offset down by half hex)
const TOTAL_HEXES = 1117
const NUM_COLUMNS = 29

// Hex geometry - calibrated to align with mainmap.jpg
const HEX_SIZE = 112.0
const OFFSET_X = -50
const OFFSET_Y = -25
const HEX_WIDTH = HEX_SIZE * 2  // flat edge to flat edge
const HEX_HEIGHT = HEX_SIZE * Math.sqrt(3)  // point to point

// Zoom controls
const MIN_ZOOM = 0.25
const MAX_ZOOM = 1.0
const ZOOM_STEP = 0.05
const zoom = ref(0.25)  // Start zoomed out to see the whole map
const mapScrollRef = ref(null)

// Zoom functions
const zoomIn = () => {
  zoom.value = Math.min(MAX_ZOOM, zoom.value + ZOOM_STEP)
}

const zoomOut = () => {
  zoom.value = Math.max(MIN_ZOOM, zoom.value - ZOOM_STEP)
}

const zoomToPoint = (newZoom, mouseX, mouseY) => {
  const container = mapScrollRef.value
  if (!container) return
  
  const oldZoom = zoom.value
  newZoom = Math.max(MIN_ZOOM, Math.min(MAX_ZOOM, newZoom))
  
  if (newZoom === oldZoom) return
  
  // Calculate the point on the actual map that's under the cursor
  const mapX = (container.scrollLeft + mouseX) / oldZoom
  const mapY = (container.scrollTop + mouseY) / oldZoom
  
  // Update zoom
  zoom.value = newZoom
  
  // After Vue updates the DOM, adjust scroll to keep the same point under cursor
  requestAnimationFrame(() => {
    container.scrollLeft = mapX * newZoom - mouseX
    container.scrollTop = mapY * newZoom - mouseY
  })
}

const handleWheel = (e) => {
  // Only zoom if Ctrl is held (standard map behavior)
  if (e.ctrlKey) {
    e.preventDefault()
    
    // Get mouse position relative to the scroll container
    const rect = mapScrollRef.value.getBoundingClientRect()
    const mouseX = e.clientX - rect.left
    const mouseY = e.clientY - rect.top
    
    // Calculate new zoom level
    const delta = e.deltaY < 0 ? ZOOM_STEP : -ZOOM_STEP
    const newZoom = zoom.value + delta
    
    zoomToPoint(newZoom, mouseX, mouseY)
  }
}

const zoomPercent = () => Math.round(zoom.value * 100)

const loadMapData = async () => {
  loading.value = true
  try {
    // Load ALL hexes
    const [hexRes, basesRes] = await Promise.all([
      hexes.list({ limit: 1200 }),
      bases.list({ limit: 200 })
    ])
    allHexes.value = hexRes.data
    allBases.value = basesRes.data
    console.log(`Loaded ${allHexes.value.length} hexes, ${allBases.value.length} bases`)
  } catch (e) {
    console.error('Failed to load map:', e)
  } finally {
    loading.value = false
  }
}

const selectHex = async (hex) => {
  selectedHex.value = hex
  try {
    const response = await unitsApi.atHex(hex.id)
    hexUnits.value = response.data
  } catch (e) {
    console.error('Failed to load units:', e)
    hexUnits.value = []
  }
}

// Convert hex ID to column and row
const getHexPosition = (hexId) => {
  let remaining = hexId
  let col = 0
  
  // Walk through columns to find which one this hex belongs to
  while (remaining >= 0) {
    const colSize = col % 2 === 0 ? 39 : 38
    if (remaining < colSize) {
      break
    }
    remaining -= colSize
    col++
  }
  
  const row = remaining
  
  // Flat-top hex positioning
  // x spacing: 3/4 of hex width between column centers
  // y spacing: full hex height between row centers
  // Odd columns are offset DOWN by half a hex height
  const x = col * HEX_WIDTH * 0.75 + OFFSET_X
  const y = row * HEX_HEIGHT + (col % 2 ? HEX_HEIGHT / 2 : 0) + OFFSET_Y
  
  return { x, y, col, row }
}

// Terrain colors based on the correct terrain codes
const TERRAIN_COLORS = {
  'O': '#1a4a7a',  // Ocean - deep blue
  'C': '#4a7a4a',  // Clear - green plains
  'F': '#2a5a2a',  // Forest - dark green
  'M': '#7a7a7a',  // Mountain - gray
  'S': '#5a6a4a',  // Swamp - murky green-brown
  'I': '#9a9aaa',  // Peaks - light gray/white
  'K': '#3a6a8a',  // Coastal Clear
  'N': '#5a6a7a',  // Coastal Mountain
  'Q': '#3a5a5a',  // Coastal Forest
  'R': '#4a7aaa',  // River
  'W': '#8a6a4a',  // Fortification
  'X': '#1a1a1a',  // Impassable
}

const getTerrainColor = (terrain) => {
  return TERRAIN_COLORS[terrain] || '#3a3a3a'
}

const getTerrainName = (code) => {
  const names = {
    'O': 'Ocean',
    'C': 'Clear',
    'F': 'Forest',
    'M': 'Mountain',
    'S': 'Swamp',
    'I': 'Peaks',
    'K': 'Coastal',
    'N': 'Coastal Mountain',
    'Q': 'Coastal Forest',
    'R': 'River',
    'W': 'Fortification',
    'X': 'Impassable'
  }
  return names[code] || code
}

const getBaseAtHex = (hexId) => {
  return allBases.value.find(b => b.location === hexId)
}

// Generate FLAT-TOP hexagon points (centered at HEX_SIZE, HEX_SIZE)
const hexPoints = (() => {
  const points = []
  for (let i = 0; i < 6; i++) {
    // Start at 0 degrees (pointing right) for flat-top
    const angle = (Math.PI / 3) * i
    const x = HEX_SIZE * Math.cos(angle) + HEX_SIZE
    const y = HEX_SIZE * Math.sin(angle) + HEX_SIZE
    points.push(`${x},${y}`)
  }
  return points.join(' ')
})()

// View dimensions match the image
const svgWidth = MAP_IMAGE_WIDTH
const svgHeight = MAP_IMAGE_HEIGHT

onMounted(loadMapData)
</script>

<template>
  <div class="map-page fade-in">
    <header class="page-header">
      <div>
        <h2>Strategic Map</h2>
        <p class="text-muted">Eastern Kingdoms • {{ allHexes.length }} hexes loaded</p>
      </div>
      
      <!-- Zoom Controls -->
      <div class="zoom-controls">
        <button class="zoom-btn" @click="zoomOut" :disabled="zoom <= MIN_ZOOM">−</button>
        <span class="zoom-level">{{ zoomPercent() }}%</span>
        <button class="zoom-btn" @click="zoomIn" :disabled="zoom >= MAX_ZOOM">+</button>
        <span class="zoom-hint">Ctrl + Scroll to zoom</span>
      </div>
    </header>

    <div class="map-container">
      <!-- Loading -->
      <div v-if="loading" class="loading">
        <div class="spinner"></div>
        <p>Loading map data...</p>
      </div>

      <!-- Map -->
      <div 
        v-else 
        ref="mapScrollRef"
        class="map-scroll"
        @wheel="handleWheel"
      >
        <div 
          class="map-wrapper" 
          :style="{ 
            width: (svgWidth * zoom) + 'px', 
            height: (svgHeight * zoom) + 'px' 
          }"
        >
          <div 
            class="map-content"
            :style="{ 
              transform: `scale(${zoom})`,
              transformOrigin: 'top left',
              width: svgWidth + 'px',
              height: svgHeight + 'px'
            }"
          >
            <!-- Background Image -->
            <img 
              src="/mainmap.jpg" 
              alt="Map of the Eastern Kingdoms" 
              class="map-background"
              :style="{ width: svgWidth + 'px', height: svgHeight + 'px' }"
              draggable="false"
            />
            
            <!-- Hex Interaction Overlay (invisible but clickable) -->
            <svg 
              class="hex-overlay"
              :width="svgWidth"
              :height="svgHeight"
              :viewBox="`0 0 ${svgWidth} ${svgHeight}`"
            >
              <!-- All Hexes - transparent but interactive -->
              <g 
                v-for="hex in allHexes" 
                :key="hex.id"
                :transform="`translate(${getHexPosition(hex.id).x}, ${getHexPosition(hex.id).y})`"
                @click="selectHex(hex)"
                class="hex-group"
                :class="{ selected: selectedHex?.id === hex.id }"
              >
                <!-- Hex shape - invisible, just for hit detection -->
                <polygon
                  :points="hexPoints"
                  fill="transparent"
                  stroke="transparent"
                  stroke-width="1"
                  class="hex-hitbox"
                />
                
                <!-- Base marker -->
                <circle
                  v-if="getBaseAtHex(hex.id)"
                  :cx="HEX_SIZE"
                  :cy="HEX_SIZE"
                  r="8"
                  fill="#c9a227"
                  stroke="#8a6f1a"
                  stroke-width="2"
                  class="base-marker"
                />
                
                <!-- Unit indicator -->
                <circle
                  v-if="hex.hasUnits"
                  :cx="HEX_SIZE"
                  :cy="HEX_SIZE + 12"
                  r="5"
                  fill="#e85050"
                  stroke="#ffffff"
                  stroke-width="1"
                />
              </g>
            </svg>
          </div>
        </div>
      </div>

      <!-- Hex Info Panel (always visible) -->
      <div class="hex-info card">
        <!-- When a hex is selected -->
        <template v-if="selectedHex">
          <div class="card-header">
            <h3 class="card-title">Hex {{ selectedHex.id }}</h3>
            <button class="close-btn" @click="selectedHex = null">×</button>
          </div>
          
          <div class="hex-position">
            <span class="pos-label">Position:</span>
            <span class="pos-value">
              Col {{ getHexPosition(selectedHex.id).col }}, 
              Row {{ getHexPosition(selectedHex.id).row }}
            </span>
          </div>
          
          <div class="hex-details">
            <div class="detail-row">
              <span class="detail-label">Terrain</span>
              <span class="detail-value terrain-value">
                <span 
                  class="terrain-swatch" 
                  :style="{ background: getTerrainColor(selectedHex.terrain) }"
                ></span>
                {{ getTerrainName(selectedHex.terrain) }}
              </span>
            </div>
            
            <template v-if="getBaseAtHex(selectedHex.id)">
              <div class="detail-row">
                <span class="detail-label">Settlement</span>
                <span class="detail-value highlight">{{ getBaseAtHex(selectedHex.id).name }}</span>
              </div>
              <div class="detail-row">
                <span class="detail-label">Tier</span>
                <span class="detail-value">{{ getBaseAtHex(selectedHex.id).tier }}</span>
              </div>
            </template>
          </div>

          <div v-if="hexUnits.length" class="hex-units">
            <h4>Units ({{ hexUnits.length }})</h4>
            <div class="unit-list">
              <RouterLink
                v-for="unit in hexUnits"
                :key="unit.id"
                :to="`/units/${unit.id}`"
                class="unit-item"
              >
                <span class="unit-name">{{ unit.name }}</span>
                <span class="unit-hp">{{ unit.hp }}/{{ unit.maxHp }}</span>
              </RouterLink>
            </div>
          </div>
          <div v-else class="no-units">
            <span class="text-muted">No units at this hex</span>
          </div>
        </template>
        
        <!-- When no hex is selected -->
        <template v-else>
          <div class="card-header">
            <h3 class="card-title">Hex Info</h3>
          </div>
          <div class="no-selection">
            <p class="text-muted">Click on a hex to view details</p>
          </div>
        </template>
      </div>
    </div>
  </div>
</template>

<style scoped>
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: var(--space-lg);
  flex-wrap: wrap;
  gap: var(--space-md);
}

.page-header h2 {
  margin-bottom: var(--space-xs);
}

/* Zoom Controls */
.zoom-controls {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  padding: var(--space-sm) var(--space-md);
  background: var(--color-bg-secondary);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
}

.zoom-btn {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--color-bg-tertiary);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  color: var(--color-text-primary);
  font-size: 1.25rem;
  font-weight: bold;
  cursor: pointer;
  transition: all var(--transition-fast);
}

.zoom-btn:hover:not(:disabled) {
  background: var(--color-gold);
  color: var(--color-bg-primary);
  border-color: var(--color-gold);
}

.zoom-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.zoom-level {
  min-width: 50px;
  text-align: center;
  font-size: 0.9rem;
  color: var(--color-text-secondary);
  font-variant-numeric: tabular-nums;
}

.zoom-hint {
  font-size: 0.75rem;
  color: var(--color-text-muted);
  margin-left: var(--space-sm);
}

.map-container {
  position: relative;
  display: flex;
  gap: var(--space-lg);
}

.map-scroll {
  /* Fixed width to fit map exactly at 25% zoom (4832 * 0.25 = 1208px) */
  width: 1208px;
  flex-shrink: 0;
  overflow: auto;
  background: var(--color-bg-secondary);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  max-height: 80vh;
}

.map-wrapper {
  position: relative;
}

.map-content {
  position: relative;
}

.map-background {
  display: block;
  user-select: none;
}

.hex-overlay {
  position: absolute;
  top: 0;
  left: 0;
  pointer-events: auto;
}

.hex-group {
  cursor: pointer;
}

/* Hex hitbox - invisible but shows on hover */
.hex-hitbox {
  transition: all 0.15s ease;
}

.hex-group:hover .hex-hitbox {
  fill: rgba(201, 162, 39, 0.25);
  stroke: var(--color-gold);
  stroke-width: 3;
}

.hex-group.selected .hex-hitbox {
  fill: rgba(201, 162, 39, 0.35);
  stroke: var(--color-gold-light);
  stroke-width: 4;
}

/* Base markers */
.base-marker {
  filter: drop-shadow(0 0 3px rgba(0, 0, 0, 0.5));
}

/* Info Panel */
.hex-info {
  position: sticky;
  top: var(--space-lg);
  width: 238px;  /* 85% of 280px */
  flex-shrink: 0;
  align-self: flex-start;
  margin-left: -10px;
}

.close-btn {
  background: none;
  border: none;
  color: var(--color-text-muted);
  font-size: 1.5rem;
  cursor: pointer;
  padding: 0;
  line-height: 1;
}

.close-btn:hover {
  color: var(--color-text-primary);
}

.hex-position {
  display: flex;
  justify-content: space-between;
  padding: var(--space-sm) 0;
  margin-bottom: var(--space-sm);
  border-bottom: 1px solid var(--color-border);
  font-size: 0.85rem;
}

.pos-label {
  color: var(--color-text-muted);
}

.pos-value {
  color: var(--color-text-secondary);
}

.hex-details {
  display: flex;
  flex-direction: column;
  gap: var(--space-sm);
  margin-bottom: var(--space-md);
}

.detail-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.detail-label {
  color: var(--color-text-muted);
}

.detail-value {
  color: var(--color-text-primary);
}

.detail-value.highlight {
  color: var(--color-gold);
}

.terrain-value {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
}

.terrain-swatch {
  width: 14px;
  height: 14px;
  border-radius: 2px;
  border: 1px solid var(--color-border);
}

.hex-units h4 {
  font-size: 0.9rem;
  margin-bottom: var(--space-sm);
  padding-top: var(--space-sm);
  padding-bottom: var(--space-sm);
  border-top: 1px solid var(--color-border);
  border-bottom: 1px solid var(--color-border);
}

.unit-list {
  display: flex;
  flex-direction: column;
  gap: var(--space-xs);
}

.unit-item {
  display: flex;
  justify-content: space-between;
  padding: var(--space-sm);
  background: var(--color-bg-tertiary);
  border-radius: var(--radius-sm);
  color: var(--color-text-primary);
  font-size: 0.9rem;
}

.unit-item:hover {
  background: var(--color-bg-hover);
  color: var(--color-gold);
}

.unit-hp {
  color: var(--color-text-muted);
}

.no-units {
  padding: var(--space-md) 0;
  text-align: center;
}

.no-selection {
  padding: var(--space-xl) var(--space-md);
  text-align: center;
}
</style>
