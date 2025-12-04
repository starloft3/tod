<script setup>
import { ref, computed, onMounted } from 'vue'
import { hexes, bases, units as unitsApi } from '../api'

const allHexes = ref([])
const allBases = ref([])
const selectedHex = ref(null)
const hexUnits = ref([])
const loading = ref(true)

// Map geometry - columns go DOWN
// Hex 0 is top-left, hexes 0-38 form first column
// Hex 39 starts second column, etc.
const HEXES_PER_COLUMN = 39
const TOTAL_HEXES = 1117
const NUM_COLUMNS = Math.ceil(TOTAL_HEXES / HEXES_PER_COLUMN) // ~29 columns

// Hex rendering size
const HEX_SIZE = 18
const HEX_WIDTH = HEX_SIZE * 2
const HEX_HEIGHT = HEX_SIZE * Math.sqrt(3)

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

// Convert hex ID to x,y position
// Columns go DOWN: col = id / 39, row = id % 39
const getHexPosition = (hexId) => {
  const col = Math.floor(hexId / HEXES_PER_COLUMN)
  const row = hexId % HEXES_PER_COLUMN
  
  // Hex grid with offset columns
  const x = col * HEX_WIDTH * 0.75
  const y = row * HEX_HEIGHT + (col % 2 ? HEX_HEIGHT / 2 : 0)
  
  return { x, y, col, row }
}

// Terrain colors based on the correct terrain codes
const TERRAIN_COLORS = {
  // Hex terrains
  'O': '#1a4a7a',  // Ocean - deep blue
  'C': '#4a7a4a',  // Clear - green plains
  'F': '#2a5a2a',  // Forest - dark green
  'M': '#7a7a7a',  // Mountain - gray
  'S': '#5a6a4a',  // Swamp - murky green-brown
  'I': '#9a9aaa',  // Peaks - light gray/white
  
  // Hexside-only terrains (shouldn't appear as hex centers, but just in case)
  'K': '#3a6a8a',  // Coastal Clear - lighter blue
  'N': '#5a6a7a',  // Coastal Mountain - blue-gray
  'Q': '#3a5a5a',  // Coastal Forest - teal
  'R': '#4a7aaa',  // River - blue
  'W': '#8a6a4a',  // Fortification - brown
  'X': '#1a1a1a',  // Impassable - black
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

// Generate pointy-top hexagon points
const hexPoints = computed(() => {
  const points = []
  for (let i = 0; i < 6; i++) {
    const angle = (Math.PI / 3) * i - Math.PI / 6
    const x = HEX_SIZE * Math.cos(angle) + HEX_SIZE
    const y = HEX_SIZE * Math.sin(angle) + HEX_SIZE
    points.push(`${x},${y}`)
  }
  return points.join(' ')
})

// SVG dimensions
const svgWidth = computed(() => NUM_COLUMNS * HEX_WIDTH * 0.75 + HEX_WIDTH + 40)
const svgHeight = computed(() => HEXES_PER_COLUMN * HEX_HEIGHT + HEX_HEIGHT + 40)

onMounted(loadMapData)
</script>

<template>
  <div class="map-page fade-in">
    <header class="page-header">
      <div>
        <h2>Strategic Map</h2>
        <p class="text-muted">Eastern Kingdoms • {{ allHexes.length }} hexes loaded</p>
      </div>
      <div class="map-legend">
        <div class="legend-item">
          <span class="legend-color" :style="{ background: TERRAIN_COLORS['C'] }"></span>
          <span>Clear</span>
        </div>
        <div class="legend-item">
          <span class="legend-color" :style="{ background: TERRAIN_COLORS['F'] }"></span>
          <span>Forest</span>
        </div>
        <div class="legend-item">
          <span class="legend-color" :style="{ background: TERRAIN_COLORS['M'] }"></span>
          <span>Mountain</span>
        </div>
        <div class="legend-item">
          <span class="legend-color" :style="{ background: TERRAIN_COLORS['O'] }"></span>
          <span>Ocean</span>
        </div>
        <div class="legend-item">
          <span class="legend-color" :style="{ background: TERRAIN_COLORS['S'] }"></span>
          <span>Swamp</span>
        </div>
        <div class="legend-item">
          <span class="legend-color" :style="{ background: TERRAIN_COLORS['I'] }"></span>
          <span>Peaks</span>
        </div>
      </div>
    </header>

    <div class="map-container">
      <!-- Loading -->
      <div v-if="loading" class="loading">
        <div class="spinner"></div>
        <p>Loading map data...</p>
      </div>

      <!-- Map -->
      <div v-else class="map-scroll">
        <svg 
          class="hex-map"
          :width="svgWidth"
          :height="svgHeight"
          :viewBox="`0 0 ${svgWidth} ${svgHeight}`"
        >
          <!-- All Hexes -->
          <g 
            v-for="hex in allHexes" 
            :key="hex.id"
            :transform="`translate(${getHexPosition(hex.id).x + 20}, ${getHexPosition(hex.id).y + 20})`"
            @click="selectHex(hex)"
            class="hex-group"
            :class="{ selected: selectedHex?.id === hex.id }"
          >
            <!-- Hex shape -->
            <polygon
              :points="hexPoints"
              :fill="getTerrainColor(hex.terrain)"
              stroke="#0a0a0a"
              stroke-width="1"
            />
            
            <!-- Base marker -->
            <circle
              v-if="getBaseAtHex(hex.id)"
              :cx="HEX_SIZE"
              :cy="HEX_SIZE"
              r="5"
              fill="#c9a227"
              stroke="#8a6f1a"
              stroke-width="1"
            />
            
            <!-- Unit indicator -->
            <circle
              v-if="hex.hasUnits"
              :cx="HEX_SIZE"
              :cy="HEX_SIZE + 8"
              r="3"
              fill="#e85050"
            />
          </g>
        </svg>
      </div>

      <!-- Hex Info Panel -->
      <div v-if="selectedHex" class="hex-info card">
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

.map-legend {
  display: flex;
  gap: var(--space-md);
  flex-wrap: wrap;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: var(--space-xs);
  font-size: 0.85rem;
  color: var(--color-text-secondary);
}

.legend-color {
  width: 16px;
  height: 16px;
  border-radius: var(--radius-sm);
  border: 1px solid var(--color-border);
}

.map-container {
  position: relative;
  display: flex;
  gap: var(--space-lg);
}

.map-scroll {
  flex: 1;
  overflow: auto;
  background: var(--color-bg-secondary);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  padding: var(--space-md);
  max-height: 70vh;
}

.hex-map {
  display: block;
}

.hex-group {
  cursor: pointer;
  transition: opacity var(--transition-fast);
}

.hex-group:hover polygon {
  stroke: var(--color-gold);
  stroke-width: 2;
  filter: brightness(1.2);
}

.hex-group.selected polygon {
  stroke: var(--color-gold-light);
  stroke-width: 3;
  filter: brightness(1.3);
}

/* Info Panel */
.hex-info {
  position: sticky;
  top: var(--space-lg);
  width: 280px;
  flex-shrink: 0;
  align-self: flex-start;
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
</style>
