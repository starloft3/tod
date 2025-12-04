<script setup>
import { ref, onMounted } from 'vue'
import { hexes, bases, units as unitsApi } from '../api'

const mapHexes = ref([])
const mapBases = ref([])
const selectedHex = ref(null)
const hexUnits = ref([])
const loading = ref(true)

// Map dimensions (38 columns x ~29 rows based on 1117 hexes)
const MAP_COLS = 38
const HEX_SIZE = 20

const loadMapData = async () => {
  loading.value = true
  try {
    const [hexRes, basesRes] = await Promise.all([
      hexes.list({ limit: 500 }),
      bases.list({ limit: 200 })
    ])
    mapHexes.value = hexRes.data
    mapBases.value = basesRes.data
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

const getHexPosition = (hexId) => {
  const col = hexId % MAP_COLS
  const row = Math.floor(hexId / MAP_COLS)
  const x = col * HEX_SIZE * 1.5 + (row % 2 ? HEX_SIZE * 0.75 : 0)
  const y = row * HEX_SIZE * 0.866
  return { x, y }
}

const getTerrainColor = (terrain) => {
  const colors = {
    'C': '#3a5a3a', // Clear - green
    'F': '#2a4a2a', // Forest - dark green
    'M': '#6a6a6a', // Mountain - gray
    'O': '#2a4a6a', // Water - blue
    'S': '#5a5a3a', // Swamp - olive
    'X': '#1a1a1a', // Impassable - black
  }
  return colors[terrain] || '#3a3a3a'
}

const getBaseAtHex = (hexId) => {
  return mapBases.value.find(b => b.location === hexId)
}

onMounted(loadMapData)
</script>

<template>
  <div class="map-page fade-in">
    <header class="page-header">
      <div>
        <h2>Strategic Map</h2>
        <p class="text-muted">Eastern Kingdoms Theater of War</p>
      </div>
      <div class="map-legend">
        <div class="legend-item">
          <span class="legend-color" style="background: #3a5a3a"></span>
          <span>Clear</span>
        </div>
        <div class="legend-item">
          <span class="legend-color" style="background: #2a4a2a"></span>
          <span>Forest</span>
        </div>
        <div class="legend-item">
          <span class="legend-color" style="background: #6a6a6a"></span>
          <span>Mountain</span>
        </div>
        <div class="legend-item">
          <span class="legend-color" style="background: #2a4a6a"></span>
          <span>Water</span>
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
          :width="MAP_COLS * HEX_SIZE * 1.5 + 50"
          :height="(1117 / MAP_COLS) * HEX_SIZE * 0.866 + 50"
        >
          <!-- Hexes -->
          <g 
            v-for="hex in mapHexes" 
            :key="hex.id"
            :transform="`translate(${getHexPosition(hex.id).x + 25}, ${getHexPosition(hex.id).y + 25})`"
            @click="selectHex(hex)"
            class="hex-group"
            :class="{ selected: selectedHex?.id === hex.id }"
          >
            <!-- Hex shape -->
            <polygon
              :points="`${HEX_SIZE},0 ${HEX_SIZE*1.5},${HEX_SIZE*0.5} ${HEX_SIZE*1.5},${HEX_SIZE*1.5} ${HEX_SIZE},${HEX_SIZE*2} ${HEX_SIZE*0.5},${HEX_SIZE*1.5} ${HEX_SIZE*0.5},${HEX_SIZE*0.5}`"
              :fill="getTerrainColor(hex.terrain)"
              stroke="#1a1a1a"
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
              :cy="HEX_SIZE * 1.5"
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
        
        <div class="hex-details">
          <div class="detail-row">
            <span class="detail-label">Terrain</span>
            <span class="detail-value capitalize">
              {{ { C: 'Clear', F: 'Forest', M: 'Mountain', O: 'Water', S: 'Swamp', X: 'Impassable' }[selectedHex.terrain] || selectedHex.terrain }}
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
}

.hex-group.selected polygon {
  stroke: var(--color-gold);
  stroke-width: 3;
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

.hex-details {
  display: flex;
  flex-direction: column;
  gap: var(--space-sm);
  margin-bottom: var(--space-md);
}

.detail-row {
  display: flex;
  justify-content: space-between;
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

.capitalize {
  text-transform: capitalize;
}

.hex-units h4 {
  font-size: 0.9rem;
  margin-bottom: var(--space-sm);
  padding-bottom: var(--space-sm);
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
</style>

