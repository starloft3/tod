<script setup>
import { ref, onMounted, onUnmounted, inject, computed, watch } from 'vue'
import axios from 'axios'
import { hexes, bases, units as unitsApi, factions as factionsApi } from '../api'
import { 
  validateMove, 
  validatePath,
  areHexesAdjacent, 
  hasRoad,
  getHexsideTerrain,
  isRoughTerrain,
  TERRAIN_NAMES,
} from '../utils/movementValidation'

const API_BASE = 'http://localhost:8000'

const allHexes = ref([])               // Full hex data with hexsides and roads
const allBases = ref([])
const selectedHex = ref(null)
const hexUnits = ref([])
const loading = ref(true)
const factionData = ref({})            // Cache of faction data for initiative lookup

// Inject faction view and turn info from App.vue
const selectedFactionId = inject('selectedFactionId')
const factionView = inject('factionView')
const turnInfo = inject('turnInfo')

// ==================== Movement Order State ====================
const movementMode = ref(false)        // Are we in path-building mode?
const selectedUnit = ref(null)         // Unit we're giving orders to
const movementPath = ref([])           // Array of hex IDs forming the path
const orderMessage = ref(null)         // Feedback message
const orderError = ref(null)           // Error message
const submittedOrders = ref({})        // Track submitted orders by faction: { factionId: { movementOrders: [...] } }

// Movement validation state
const pathValidation = ref(null)       // Current path validation result
const movementUsed = ref(0)            // Movement points used so far
const roadMoveUsed = ref(0)            // Road moves used so far
const lastStepWasRough = ref(false)    // Was last step over rough terrain?
const lastStepUsedRoad = ref(false)    // Did last step use a road?

// Build hex lookup for validation
const hexLookup = computed(() => {
  const lookup = {}
  for (const hex of allHexes.value) {
    lookup[hex.id] = hex
  }
  return lookup
})

// Get faction initiative for hexside control checks
const getFactionInitiative = (factionId) => {
  const faction = factionData.value[factionId]
  return faction?.initiative ?? -1
}


// Get the faction ID from a unit (API returns 'factionId')
const getUnitFactionId = (unit) => {
  if (!unit) return null
  // API returns factionId as a number
  return unit.factionId
}

// Check if a unit belongs to the currently selected faction
const isOwnUnit = (unit) => {
  if (selectedFactionId.value === null) return true  // Admin can control all (if it's their turn)
  const unitFaction = getUnitFactionId(unit)
  return unitFaction === selectedFactionId.value
}


// Check if a faction can submit orders (is it their turn?)
const canFactionSubmitOrders = (factionId) => {
  if (!turnInfo.value || !turnInfo.value.activeFactionIds) return false
  return turnInfo.value.activeFactionIds.includes(factionId)
}

// Check if we can give orders to this unit (own unit AND it's their turn)
const canOrderUnit = (unit) => {
  // Must be own unit first
  if (!isOwnUnit(unit)) return false
  
  // Get the unit's faction
  const unitFactionId = getUnitFactionId(unit)
  if (unitFactionId === null) return false
  
  // Check if it's that faction's turn
  return canFactionSubmitOrders(unitFactionId)
}

// Fetch submitted orders for a faction
const fetchFactionOrders = async (factionId) => {
  if (factionId === null) return  // Don't fetch for omniscient mode
  try {
    const response = await axios.get(`${API_BASE}/orders/faction/${factionId}`)
    submittedOrders.value[factionId] = response.data
  } catch (e) {
    console.error('Error fetching orders:', e)
  }
}

// Check if a unit has a submitted movement order
const hasMovementOrder = (unit) => {
  const factionId = getUnitFactionId(unit)
  const factionOrders = submittedOrders.value[factionId]
  if (!factionOrders || !factionOrders.movementOrders) return false
  return factionOrders.movementOrders.some(o => o.unitId === unit.id)
}

// Get the submitted movement order for a unit (if any)
const getMovementOrder = (unit) => {
  const factionId = getUnitFactionId(unit)
  const factionOrders = submittedOrders.value[factionId]
  if (!factionOrders || !factionOrders.movementOrders) return null
  return factionOrders.movementOrders.find(o => o.unitId === unit.id)
}

// Cancel a unit's movement order
const cancelUnitMovementOrder = async (unit) => {
  const factionId = getUnitFactionId(unit)
  if (factionId === null) {
    orderError.value = 'Could not determine unit faction'
    return
  }
  
  try {
    await axios.delete(`${API_BASE}/orders/movement/${unit.id}?faction_id=${factionId}`)
    orderMessage.value = `Cancelled movement order for ${unit.name}`
    orderError.value = null
    // Refresh orders
    await fetchFactionOrders(factionId)
    // Clear message after a moment
    setTimeout(() => { orderMessage.value = null }, 2000)
  } catch (e) {
    orderError.value = e.response?.data?.detail || e.message
    orderMessage.value = null
  }
}

// Get units at a hex that belong to the current faction
const getOwnUnitsAtHex = (hexId) => {
  return hexUnits.value.filter(u => isOwnUnit(u))
}

// Start building a movement order for a unit
const startMovementOrder = (unit) => {
  selectedUnit.value = unit
  movementMode.value = true
  movementPath.value = []  // Start fresh
  orderMessage.value = null
  orderError.value = null
  // Reset validation state
  pathValidation.value = null
  movementUsed.value = 0
  roadMoveUsed.value = 0
  lastStepWasRough.value = false
  lastStepUsedRoad.value = false
}

// Cancel the current movement order
const cancelMovementOrder = () => {
  selectedUnit.value = null
  movementMode.value = false
  movementPath.value = []
  orderMessage.value = null
  orderError.value = null
  // Reset validation state
  pathValidation.value = null
  movementUsed.value = 0
  roadMoveUsed.value = 0
  lastStepWasRough.value = false
  lastStepUsedRoad.value = false
}

// Add a hex to the movement path with full validation
const addToPath = (hexId) => {
  if (!selectedUnit.value) return
  
  // Don't add duplicates at the end
  if (movementPath.value.length > 0 && movementPath.value[movementPath.value.length - 1] === hexId) {
    return
  }
  // Don't add the unit's current location
  if (hexId === selectedUnit.value.location) {
    return
  }
  
  // Get current position (either last path hex or unit location)
  const currentHex = movementPath.value.length > 0 
    ? movementPath.value[movementPath.value.length - 1] 
    : selectedUnit.value.location
  
  // Get hex objects for validation
  const fromHexObj = hexLookup.value[currentHex]
  const toHexObj = hexLookup.value[hexId]
  
  // Get faction initiative for hexside control checks
  const unitFactionId = getUnitFactionId(selectedUnit.value)
  const factionInitiative = getFactionInitiative(unitFactionId)
  
  // === FULL CLIENT-SIDE VALIDATION ===
  const validation = validateMove({
    fromHex: currentHex,
    toHex: hexId,
    unit: selectedUnit.value,
    fromHexObj,
    toHexObj,
    factionInitiative,
    movementUsed: movementUsed.value,
    roadMoveUsed: roadMoveUsed.value,
    previousWasRough: lastStepWasRough.value,
    usedRoadOnPrevious: lastStepUsedRoad.value,
  })
  
  if (!validation.valid) {
    orderError.value = validation.message
    pathValidation.value = { valid: false, message: validation.message }
    // Clear error after a moment
    setTimeout(() => { 
      if (orderError.value === validation.message) orderError.value = null 
    }, 3000)
    return
  }
  
  // Valid move - add to path and update state
  movementPath.value.push(hexId)
  orderError.value = null
  
  // Update movement tracking
  if (validation.usesRoadBonus) {
    roadMoveUsed.value += 1
  } else {
    movementUsed.value += 1
  }
  
  // Track rough terrain and road usage for continuous movement rules
  lastStepWasRough.value = validation.isRoughTerrain || false
  lastStepUsedRoad.value = validation.hasRoad || false
  
  // Build helpful message
  let msg = 'Path valid'
  if (validation.hasRoad) {
    msg += ' (road)'
  }
  pathValidation.value = { valid: true, message: msg }
}

// Recalculate movement state from scratch for current path using full validation
const recalculatePathState = () => {
  if (!selectedUnit.value || movementPath.value.length === 0) {
    movementUsed.value = 0
    roadMoveUsed.value = 0
    lastStepWasRough.value = false
    lastStepUsedRoad.value = false
    pathValidation.value = null
    return
  }
  
  const unitFactionId = getUnitFactionId(selectedUnit.value)
  const factionInitiative = getFactionInitiative(unitFactionId)
  
  // Use validatePath to recalculate everything
  const result = validatePath(
    selectedUnit.value,
    movementPath.value,
    hexLookup.value,
    factionInitiative
  )
  
  movementUsed.value = result.totalMovementUsed || 0
  roadMoveUsed.value = result.totalRoadMoveUsed || 0
  
  // Get state from last step
  if (result.steps && result.steps.length > 0) {
    const lastStep = result.steps[result.steps.length - 1]
    lastStepWasRough.value = lastStep.isRoughTerrain || false
    lastStepUsedRoad.value = lastStep.hasRoad || false
  } else {
    lastStepWasRough.value = false
    lastStepUsedRoad.value = false
  }
  
  pathValidation.value = { valid: result.valid, message: result.message }
}

// Remove last hex from path
const undoLastPathStep = () => {
  if (movementPath.value.length > 0) {
    movementPath.value.pop()
    recalculatePathState()
    orderError.value = null
  }
}

// Clear the entire path
const clearPath = () => {
  movementPath.value = []
  movementUsed.value = 0
  roadMoveUsed.value = 0
  lastStepWasRough.value = false
  lastStepUsedRoad.value = false
  pathValidation.value = null
  orderError.value = null
}

// Submit the movement order
const submitMovementOrder = async () => {
  if (!selectedUnit.value || movementPath.value.length === 0) {
    orderError.value = 'No path selected'
    return
  }
  
  // In omniscient mode, use the unit's faction; otherwise use selected faction
  let factionId = selectedFactionId.value
  if (factionId === null) {
    factionId = getUnitFactionId(selectedUnit.value)
    if (factionId === null) {
      orderError.value = 'Could not determine unit faction'
      return
    }
  }
  
  try {
    const response = await axios.post(
      `${API_BASE}/orders/movement?faction_id=${factionId}`,
      {
        unitId: selectedUnit.value.id,
        path: movementPath.value
      }
    )
    orderMessage.value = response.data.message
    orderError.value = null
    
    // Refresh orders to update button state
    await fetchFactionOrders(factionId)
    
    // Keep the path visible for a moment, then clear
    setTimeout(() => {
      cancelMovementOrder()
    }, 1500)
  } catch (e) {
    orderError.value = e.response?.data?.detail || e.message
    orderMessage.value = null
  }
}

// Check if a hex is in the current movement path
const isInPath = (hexId) => {
  return movementPath.value.includes(hexId)
}

// Get the index of a hex in the path (for numbering)
const getPathIndex = (hexId) => {
  return movementPath.value.indexOf(hexId)
}

// Compute visible hex IDs as a Set for fast lookup
const visibleHexIds = computed(() => {
  if (!factionView.value || !factionView.value.visibleHexes) {
    return new Set() // No view data = show nothing (or everything in omniscient)
  }
  return new Set(factionView.value.visibleHexes)
})

// Check if we're in admin mode
const isAdmin = computed(() => selectedFactionId.value === null)

// Check if a hex is visible
const isHexVisible = (hexId) => {
  if (isAdmin.value) return true
  return visibleHexIds.value.has(hexId)
}

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
    // Load full hex data (with hexsides and roads) for movement validation
    const [hexRes, basesRes, factionsRes] = await Promise.all([
      hexes.getMapData({ limit: 1200 }),
      bases.list({ limit: 200 }),
      factionsApi.list({ limit: 50 })
    ])
    allHexes.value = hexRes.data
    allBases.value = basesRes.data
    
    // Cache faction data for initiative lookups
    for (const faction of factionsRes.data) {
      factionData.value[faction.id] = faction
    }
    
    console.log(`Loaded ${allHexes.value.length} hexes (with hexsides), ${allBases.value.length} bases, ${factionsRes.data.length} factions`)
  } catch (e) {
    console.error('Failed to load map:', e)
  } finally {
    loading.value = false
  }
}

const selectHex = async (hex) => {
  // If in movement mode, add to path instead of selecting
  if (movementMode.value && selectedUnit.value) {
    addToPath(hex.id)
    return
  }
  
  // Normal hex selection
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

// Watch for faction changes to fetch their orders
watch(selectedFactionId, async (newFactionId) => {
  if (newFactionId !== null) {
    await fetchFactionOrders(newFactionId)
  }
}, { immediate: true })

// Also fetch orders for units we're viewing (in omniscient mode)
watch(hexUnits, async (units) => {
  if (selectedFactionId.value === null && units.length > 0) {
    // In omniscient mode, fetch orders for all factions with units at this hex
    const factionIds = [...new Set(units.map(u => u.factionId).filter(Boolean))]
    for (const fid of factionIds) {
      if (!submittedOrders.value[fid]) {
        await fetchFactionOrders(fid)
      }
    }
  }
})

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
            
            <!-- Hex Interaction Overlay -->
            <svg 
              class="hex-overlay"
              :width="svgWidth"
              :height="svgHeight"
              :viewBox="`0 0 ${svgWidth} ${svgHeight}`"
            >
              <!-- Movement Path Lines (drawn first, behind hexes) -->
              <g v-if="movementMode && movementPath.length > 0" class="movement-path-lines">
                <!-- Line from unit location to first path hex -->
                <line
                  v-if="selectedUnit"
                  :x1="getHexPosition(selectedUnit.location).x + HEX_SIZE"
                  :y1="getHexPosition(selectedUnit.location).y + HEX_SIZE"
                  :x2="getHexPosition(movementPath[0]).x + HEX_SIZE"
                  :y2="getHexPosition(movementPath[0]).y + HEX_SIZE"
                  stroke="#00ff88"
                  stroke-width="4"
                  stroke-dasharray="10,5"
                  class="path-line"
                />
                <!-- Lines between path hexes -->
                <line
                  v-for="(hexId, idx) in movementPath.slice(1)"
                  :key="'line-' + idx"
                  :x1="getHexPosition(movementPath[idx]).x + HEX_SIZE"
                  :y1="getHexPosition(movementPath[idx]).y + HEX_SIZE"
                  :x2="getHexPosition(hexId).x + HEX_SIZE"
                  :y2="getHexPosition(hexId).y + HEX_SIZE"
                  stroke="#00ff88"
                  stroke-width="4"
                  stroke-dasharray="10,5"
                  class="path-line"
                />
              </g>
              
              <!-- All Hexes -->
              <g 
                v-for="hex in allHexes" 
                :key="hex.id"
                :transform="`translate(${getHexPosition(hex.id).x}, ${getHexPosition(hex.id).y})`"
                @click="selectHex(hex)"
                class="hex-group"
                :class="{ 
                  selected: selectedHex?.id === hex.id,
                  fogged: !isHexVisible(hex.id),
                  'in-path': isInPath(hex.id),
                  'unit-origin': movementMode && selectedUnit?.location === hex.id
                }"
              >
                <!-- Fog overlay for non-visible hexes -->
                <polygon
                  v-if="!isHexVisible(hex.id)"
                  :points="hexPoints"
                  fill="rgba(0, 0, 0, 0.6)"
                  stroke="rgba(0, 0, 0, 0.8)"
                  stroke-width="1"
                  class="hex-fog"
                />
                
                <!-- Path highlight overlay -->
                <polygon
                  v-if="isInPath(hex.id)"
                  :points="hexPoints"
                  fill="rgba(0, 255, 136, 0.25)"
                  stroke="#00ff88"
                  stroke-width="3"
                  class="path-highlight"
                />
                
                <!-- Unit origin highlight -->
                <polygon
                  v-if="movementMode && selectedUnit?.location === hex.id"
                  :points="hexPoints"
                  fill="rgba(255, 200, 0, 0.3)"
                  stroke="#ffc800"
                  stroke-width="3"
                  class="origin-highlight"
                />
                
                <!-- Hex hitbox (invisible, for interaction) -->
                <polygon
                  :points="hexPoints"
                  fill="transparent"
                  stroke="transparent"
                  stroke-width="1"
                  class="hex-hitbox"
                />
                
                <!-- Path step number -->
                <text
                  v-if="isInPath(hex.id)"
                  :x="HEX_SIZE"
                  :y="HEX_SIZE + 8"
                  text-anchor="middle"
                  fill="#00ff88"
                  font-size="36"
                  font-weight="bold"
                  class="path-number"
                >
                  {{ getPathIndex(hex.id) + 1 }}
                </text>
                
                <!-- Base marker (only show if visible) -->
                <circle
                  v-if="getBaseAtHex(hex.id) && isHexVisible(hex.id)"
                  :cx="HEX_SIZE"
                  :cy="HEX_SIZE"
                  r="8"
                  fill="#c9a227"
                  stroke="#8a6f1a"
                  stroke-width="2"
                  class="base-marker"
                />
                
                <!-- Unit indicator (only show if visible and not in path mode for this hex) -->
                <circle
                  v-if="hex.hasUnits && isHexVisible(hex.id) && !isInPath(hex.id)"
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
              <div
                v-for="unit in hexUnits"
                :key="unit.id"
                class="unit-item"
                :class="{ 
                  'own-unit': isOwnUnit(unit),
                  'selected-unit': selectedUnit?.id === unit.id 
                }"
              >
                <div class="unit-info">
                  <span class="unit-name">{{ unit.name }}</span>
                  <span class="unit-hp">{{ unit.hp }}/{{ unit.maxHp }}</span>
                </div>
                <button 
                  v-if="canOrderUnit(unit) && !movementMode && !hasMovementOrder(unit)"
                  class="btn btn-sm btn-move"
                  @click.stop="startMovementOrder(unit)"
                  title="Give movement order"
                >
                  Move
                </button>
                <button 
                  v-else-if="canOrderUnit(unit) && !movementMode && hasMovementOrder(unit)"
                  class="btn btn-sm btn-cancel"
                  @click.stop="cancelUnitMovementOrder(unit)"
                  title="Cancel movement order"
                >
                  Cancel
                </button>
                <span 
                  v-else-if="isOwnUnit(unit) && !canOrderUnit(unit)"
                  class="not-your-turn"
                  title="Not this faction's turn"
                >
                  (not their turn)
                </span>
              </div>
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
      
      <!-- Movement Order Panel (appears when building a path) -->
      <div v-if="movementMode" class="movement-panel card">
        <div class="card-header">
          <h3 class="card-title">Movement Order</h3>
          <button class="close-btn" @click="cancelMovementOrder">×</button>
        </div>
        
        <div class="movement-info">
          <div class="unit-being-moved">
            <span class="label">Unit:</span>
            <span class="value">{{ selectedUnit?.name }}</span>
          </div>
          <div class="path-length">
            <span class="label">Path:</span>
            <span class="value">{{ movementPath.length }} hex{{ movementPath.length !== 1 ? 'es' : '' }}</span>
          </div>
          <div class="movement-stats">
            <span class="label">Movement:</span>
            <span class="value" :class="{ 'warning': movementUsed >= (selectedUnit?.movement || selectedUnit?.movementRemaining || 3) }">
              {{ movementUsed }} / {{ selectedUnit?.movement || selectedUnit?.movementRemaining || selectedUnit?.movementMax || 3 }}
            </span>
          </div>
          <div v-if="(selectedUnit?.roadMove || selectedUnit?.roadMoveRemaining || 0) > 0" class="movement-stats">
            <span class="label">Road Bonus:</span>
            <span class="value road-bonus" :class="{ 'used': roadMoveUsed > 0 }">
              {{ roadMoveUsed }} / {{ selectedUnit?.roadMove || selectedUnit?.roadMoveRemaining || 0 }}
            </span>
          </div>
          <div v-if="lastStepUsedRoad" class="path-note">
            <span class="road-indicator">🛤️ Using road</span>
          </div>
        </div>
        
        <div class="path-display" v-if="movementPath.length > 0">
          <div class="path-hexes">
            <span 
              v-for="(hexId, idx) in movementPath" 
              :key="hexId"
              class="path-hex"
            >
              {{ hexId }}
              <span v-if="idx < movementPath.length - 1" class="path-arrow">→</span>
            </span>
          </div>
        </div>
        <div v-else class="path-instructions">
          <p class="text-muted">Click hexes on the map to build a path</p>
        </div>
        
        <!-- Messages -->
        <div v-if="orderMessage" class="order-message success">
          {{ orderMessage }}
        </div>
        <div v-if="orderError" class="order-message error">
          {{ orderError }}
        </div>
        
        <div class="movement-actions">
          <button 
            class="btn btn-secondary btn-sm"
            @click="undoLastPathStep"
            :disabled="movementPath.length === 0"
          >
            Undo
          </button>
          <button 
            class="btn btn-secondary btn-sm"
            @click="clearPath"
            :disabled="movementPath.length === 0"
          >
            Clear
          </button>
          <button 
            class="btn btn-gold btn-sm"
            @click="submitMovementOrder"
            :disabled="movementPath.length === 0"
          >
            Submit Order
          </button>
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

/* Fog of War */
.hex-fog {
  pointer-events: none;
}

.hex-group.fogged {
  cursor: default;
}

.hex-group.fogged:hover .hex-hitbox {
  fill: rgba(50, 50, 50, 0.3);
  stroke: rgba(100, 100, 100, 0.5);
  stroke-width: 1;
}

.hex-group.fogged.selected .hex-hitbox {
  fill: rgba(50, 50, 50, 0.4);
  stroke: rgba(150, 150, 150, 0.6);
  stroke-width: 2;
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

/* ==================== Movement Order Styles ==================== */

/* Unit item with move button */
.unit-item {
  flex-wrap: wrap;
  gap: var(--space-xs);
}

.unit-info {
  display: flex;
  justify-content: space-between;
  flex: 1;
  min-width: 0;
}

.unit-item.own-unit {
  border-left: 3px solid var(--color-gold);
}

.unit-item.selected-unit {
  background: rgba(0, 255, 136, 0.2);
  border-left: 3px solid #00ff88;
}

.btn-move {
  padding: 2px 8px;
  font-size: 0.75rem;
  background: var(--color-bg-secondary);
  border: 1px solid var(--color-gold);
  color: var(--color-gold);
  border-radius: 3px;
  cursor: pointer;
  transition: all var(--transition-fast);
}

.btn-move:hover {
  background: rgba(201, 162, 39, 0.2);
}

.btn-cancel {
  padding: 2px 8px;
  font-size: 0.75rem;
  background: var(--color-bg-secondary);
  border: 1px solid #e74c3c;
  color: #e74c3c;
  border-radius: 3px;
  cursor: pointer;
  transition: all var(--transition-fast);
}

.btn-cancel:hover {
  background: rgba(231, 76, 60, 0.2);
}

.not-your-turn {
  font-size: 0.7rem;
  color: var(--color-text-muted);
  font-style: italic;
}

/* Movement Panel */
.movement-panel {
  position: absolute;
  top: var(--space-md);
  left: var(--space-md);
  width: 280px;
  z-index: 100;
  background: var(--color-bg-secondary);
  border: 2px solid #00ff88;
  box-shadow: 0 4px 20px rgba(0, 255, 136, 0.3);
}

.movement-info {
  display: flex;
  flex-direction: column;
  gap: var(--space-xs);
  padding: var(--space-sm) 0;
  border-bottom: 1px solid var(--color-border);
}

.movement-info .label {
  color: var(--color-text-muted);
  font-size: 0.8rem;
  margin-right: var(--space-sm);
}

.movement-info .value {
  color: var(--color-gold);
  font-weight: bold;
}

.movement-info .value.warning {
  color: #ff9800;
}

.movement-stats {
  display: flex;
  align-items: center;
  gap: var(--space-xs);
}

.road-bonus {
  color: #4fc3f7;  /* Light blue for road bonus */
}

.road-bonus.used {
  color: #29b6f6;
  font-weight: bold;
}

.path-note {
  margin-top: var(--space-xs);
  font-size: 0.8rem;
}

.road-indicator {
  color: #4fc3f7;
}

.path-display {
  padding: var(--space-sm) 0;
}

.path-hexes {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-xs);
  font-size: 0.85rem;
}

.path-hex {
  color: #00ff88;
}

.path-arrow {
  color: var(--color-text-muted);
  margin: 0 2px;
}

.path-instructions {
  padding: var(--space-md) 0;
  text-align: center;
}

.order-message {
  padding: var(--space-sm);
  margin: var(--space-sm) 0;
  border-radius: var(--radius-sm);
  font-size: 0.85rem;
}

.order-message.success {
  background: rgba(0, 255, 136, 0.2);
  border: 1px solid #00ff88;
  color: #00ff88;
}

.order-message.error {
  background: rgba(255, 80, 80, 0.2);
  border: 1px solid #ff5050;
  color: #ff5050;
}

.movement-actions {
  display: flex;
  gap: var(--space-sm);
  padding-top: var(--space-sm);
  border-top: 1px solid var(--color-border);
}

.movement-actions .btn {
  flex: 1;
}

.btn-gold {
  background: var(--color-gold);
  color: var(--color-bg-primary);
  border: none;
  font-weight: bold;
}

.btn-gold:hover:not(:disabled) {
  background: var(--color-gold-light);
}

.btn-gold:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-secondary {
  background: var(--color-bg-tertiary);
  border: 1px solid var(--color-border);
  color: var(--color-text-secondary);
}

.btn-secondary:hover:not(:disabled) {
  background: var(--color-bg-hover);
}

.btn-secondary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-sm {
  padding: var(--space-xs) var(--space-sm);
  font-size: 0.8rem;
}

/* Path visualization on map */
.path-line {
  pointer-events: none;
}

.path-highlight {
  pointer-events: none;
}

.origin-highlight {
  pointer-events: none;
}

.path-number {
  pointer-events: none;
  font-family: var(--font-display);
  text-shadow: 
    -2px -2px 0 var(--color-bg-primary),
    2px -2px 0 var(--color-bg-primary),
    -2px 2px 0 var(--color-bg-primary),
    2px 2px 0 var(--color-bg-primary);
}

.hex-group.in-path {
  cursor: pointer;
}

.hex-group.unit-origin .hex-hitbox {
  cursor: default;
}
</style>
