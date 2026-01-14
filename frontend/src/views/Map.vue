<script setup>
import { ref, onMounted, onUnmounted, inject, computed, watch } from 'vue'
import axios from 'axios'
import { hexes, bases, units as unitsApi, factions as factionsApi, expansions as expansionsApi } from '../api'
import { 
  validateMove, 
  validatePath,
  areHexesAdjacent, 
  hasRoad,
  getHexsideTerrain,
  getHexsideLimit,
  isRoughTerrain,
  TERRAIN_NAMES,
  HEXSIDE_LIMITS,
} from '../utils/movementValidation'
import {
  getFactionBackground,
  getFactionBanner,
  getUnitImage,
  getBaseImage,
  getRuinsImage,
  getExpansionImage,
  isHordeFaction,
  isAllianceFaction,
  getAlignmentColor,
  calculateUnitPositions,
} from '../utils/imageMapping'

const API_BASE = 'http://localhost:8000'

const allHexes = ref([])               // Full hex data with hexsides and roads
const allBases = ref([])
const allExpansions = ref([])          // All expansions on the map
const allUnits = ref([])               // All units on the map
const activeCombats = ref([])          // Active combat hexes
const selectedHex = ref(null)
const hexUnits = ref([])
const selectedUnitDetail = ref(null)  // Unit being viewed in detail panel
const selectedBaseDetail = ref(null)  // Base being viewed in detail panel
const selectedBaseExpansions = ref([]) // Expansions for the selected base
const baseOrders = ref(null)           // Pending orders for selected base
const harvestPreview = ref(null)       // Preview of harvest yield
const expandMode = ref(false)          // Whether we're in "select expansion target" mode
const expandableTargets = ref([])      // List of valid expansion target hexes
const loading = ref(true)
const factionData = ref({})            // Cache of faction data for initiative lookup
const debugConfig = ref({              // Debug config flags from server
  infinite_resources: false,
  fog_of_war_enabled: true,
  show_all_units: false
})

// Inject faction view and turn info from App.vue (with defaults to prevent undefined)
const selectedFactionId = inject('selectedFactionId', null)
const factionView = inject('factionView', null)
const turnInfo = inject('turnInfo', null)

// ==================== Movement Order State ====================
const movementMode = ref(false)        // Are we in path-building mode?
const selectedUnit = ref(null)         // Unit we're giving orders to
const movementPath = ref([])           // Array of hex IDs forming the path
const orderMessage = ref(null)         // Feedback message
const orderError = ref(null)           // Error message
const submittedOrders = ref({})        // Track submitted orders by faction: { factionId: { movementOrders: [...], rangedfireOrders: [...] } }

// Movement validation state
const pathValidation = ref(null)       // Current path validation result
const movementUsed = ref(0)            // Movement points used so far
const roadMoveUsed = ref(0)            // Road moves used so far
const lastStepWasRough = ref(false)    // Was last step over rough terrain?
const lastStepUsedRoad = ref(false)    // Did last step use a road?
const stillOnRoads = ref(true)         // Has unit been following roads entire time? (for road bonus eligibility)

// ==================== Ranged Fire Order State ====================
const rangedfireMode = ref(false)      // Are we in ranged fire targeting mode?
const rangedfireUnit = ref(null)       // Unit issuing ranged fire order

// ==================== Fast Travel Order State ====================
const fastTravelMode = ref(false)      // Are we in fast travel path-building mode?
const fastTravelUnit = ref(null)       // Unit using fast travel
const fastTravelPath = ref([])         // Path being traced for fast travel
const fastTravelIsNaval = ref(false)   // Is this a naval fast travel (Full Sail)?
const fastTravelError = ref(null)      // Error message for fast travel
const validRangedfireTargets = ref([]) // Valid adjacent combat hexes

// Build hex lookup for validation
const hexLookup = computed(() => {
  const lookup = {}
  for (const hex of allHexes.value) {
    lookup[hex.id] = hex
  }
  return lookup
})

// Group units by hex for rendering
const unitsByHex = computed(() => {
  const byHex = {}
  for (const unit of allUnits.value) {
    const hexId = unit.location
    if (!byHex[hexId]) byHex[hexId] = []
    byHex[hexId].push(unit)
  }
  return byHex
})

// Group bases by hex for rendering
const basesByHex = computed(() => {
  const byHex = {}
  for (const base of allBases.value) {
    byHex[base.hexId] = base
  }
  return byHex
})

// Group expansions by hex for rendering
const expansionsByHex = computed(() => {
  const byHex = {}
  for (const exp of allExpansions.value) {
    byHex[exp.location] = exp
  }
  return byHex
})

// Get expansion at a specific hex
const getExpansionAtHex = (hexId) => {
  return expansionsByHex.value[hexId]
}

// Get faction ID for an expansion (via its base)
const getExpansionFactionId = (hexId) => {
  const exp = getExpansionAtHex(hexId)
  if (!exp) return 0
  // Find the base that owns this expansion
  const base = allBases.value.find(b => b.id === exp.baseId)
  return base?.factionId ?? 0
}

// Combat hexes by ID for quick lookup
const combatHexIds = computed(() => {
  return new Set(activeCombats.value.map(c => c.hexId))
})

// Get faction initiative for hexside control checks
const getFactionInitiative = (factionId) => {
  const faction = factionData.value[factionId]
  return faction?.initiative ?? -1
}

// ==================== Hexside Limit Tracking ====================

/**
 * Get a normalized key for a hexside (smaller hex ID first for consistency)
 */
const getHexsideKey = (hex1, hex2) => {
  return `${Math.min(hex1, hex2)}-${Math.max(hex1, hex2)}`
}

/**
 * Helper to check if a unit is an air unit.
 * Air units ignore hexside limits entirely.
 */
const isAirUnitById = (unitId) => {
  const unit = allUnits.value.find(u => u.id === unitId)
  if (!unit) return false
  const unitType = unit.unitType ?? unit.unit_type ?? 0
  return unitType === 1 || unitType === 'air' || unitType === 'AIR'
}

/**
 * Count how many units are crossing a specific hexside in submitted orders.
 * This includes BOTH movement orders AND fast travel orders from the current faction.
 * NOTE: Air units are excluded - they don't count towards hexside limits.
 */
const countHexsideUsageInOrders = (fromHex, toHex, factionId, excludeUnitId = null) => {
  const key = getHexsideKey(fromHex, toHex)
  const factionOrders = submittedOrders.value[factionId]
  
  if (!factionOrders) {
    return 0
  }
  
  let count = 0
  
  // Count from movement orders
  if (factionOrders.movementOrders) {
    for (const order of factionOrders.movementOrders) {
      // Skip the unit we're currently giving orders to (in case of re-ordering)
      if (excludeUnitId !== null && order.unitId === excludeUnitId) {
        continue
      }
      
      // Air units don't count towards hexside limits
      if (isAirUnitById(order.unitId)) {
        continue
      }
      
      if (!order.path || order.path.length === 0) continue
      
      // Use the startLocation from the order (API now provides this)
      let currentHex = order.startLocation
      if (currentHex === undefined || currentHex < 0) {
        // Fallback: skip if we don't know the starting location
        continue
      }
      
      // Check each step in the path
      for (const nextHex of order.path) {
        const stepKey = getHexsideKey(currentHex, nextHex)
        if (stepKey === key) {
          count++
        }
        currentHex = nextHex
      }
    }
  }
  
  // Count from fast travel orders (March/Full Sail)
  // Note: Air units can't fast travel anyway, but check just in case
  if (factionOrders.fastTravelOrders) {
    for (const order of factionOrders.fastTravelOrders) {
      // Skip the unit we're currently giving orders to
      if (excludeUnitId !== null && order.unitId === excludeUnitId) {
        continue
      }
      
      // Air units don't count towards hexside limits
      if (isAirUnitById(order.unitId)) {
        continue
      }
      
      if (!order.path || order.path.length === 0) continue
      
      // Fast travel orders store startLocation, or we can look up the unit
      let currentHex = order.startLocation
      if (currentHex === undefined || currentHex < 0) {
        // Fallback: try to find unit's current location
        const unit = allUnits.value.find(u => u.id === order.unitId)
        if (unit) {
          currentHex = unit.location
        } else {
          continue
        }
      }
      
      // Check each step in the path
      for (const nextHex of order.path) {
        const stepKey = getHexsideKey(currentHex, nextHex)
        if (stepKey === key) {
          count++
        }
        currentHex = nextHex
      }
    }
  }
  
  return count
}

/**
 * Count hexside usage including both submitted orders AND the current path being built.
 */
const getHexsideUsageForValidation = (fromHex, toHex, factionId, currentPath, unitStartLocation) => {
  const key = getHexsideKey(fromHex, toHex)
  
  // Count from submitted orders (excluding current unit if re-ordering)
  let count = countHexsideUsageInOrders(fromHex, toHex, factionId, selectedUnit.value?.id)
  
  // Count from the current path being built (before this new step)
  if (currentPath.length > 0) {
    let prevHex = unitStartLocation
    for (const pathHex of currentPath) {
      const stepKey = getHexsideKey(prevHex, pathHex)
      if (stepKey === key) {
        count++
      }
      prevHex = pathHex
    }
  }
  
  return count
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

// Computed: Can we issue base orders to the selected base?
const canIssueBaseOrders = computed(() => {
  if (!selectedBaseDetail.value) return false
  const baseFactionId = selectedBaseDetail.value.factionId
  return canFactionSubmitOrders(baseFactionId)
})

// Get the selected base's faction initiative info for display
const selectedBaseFactionInfo = computed(() => {
  if (!selectedBaseDetail.value) return null
  const baseFactionId = selectedBaseDetail.value.factionId
  const faction = factionData.value[baseFactionId]
  return {
    factionId: baseFactionId,
    factionName: faction?.name || `Faction ${baseFactionId}`,
    initiative: faction?.initiative ?? -1,
    currentInitiative: turnInfo.value?.currentInitiative ?? -1
  }
})

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
  stillOnRoads.value = true  // Reset road following flag
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
  stillOnRoads.value = true  // Reset road following flag
}

// ==================== Ranged Fire Order Functions ====================

// Check if a unit can use ranged fire
const canRangedfire = (unit) => {
  if (!unit) return false
  // Check the canRangedfire property from API, or fall back to category check
  // INTERIOR_SIEGE category = 4 or category name = "interior_siege"
  return unit.canRangedfire === true || 
         unit.can_rangedfire === true || 
         unit.category === 4 ||
         unit.category === 'interior_siege'
}

// Check if a unit has a ranged fire order
const hasRangedfireOrder = (unit) => {
  if (!unit) return false
  const factionId = getUnitFactionId(unit)
  const orders = submittedOrders.value[factionId]
  if (!orders?.rangedfireOrders) return false
  return orders.rangedfireOrders.some(o => o.unitId === unit.id)
}

// Get a unit's ranged fire order
const getRangedfireOrder = (unit) => {
  if (!unit) return null
  const factionId = getUnitFactionId(unit)
  const orders = submittedOrders.value[factionId]
  if (!orders?.rangedfireOrders) return null
  return orders.rangedfireOrders.find(o => o.unitId === unit.id)
}

// Get adjacent hexes (for ranged fire targeting)
const getAdjacentHexes = (hexId) => {
  // Map layout: 29 columns, alternating 39/38 hexes per column
  // Column determined by: column = floor(hexId / 39)
  const column = Math.floor(hexId / 39)
  const isEvenColumn = column % 2 === 0
  
  // Adjacent offsets depend on column parity
  const offsets = isEvenColumn 
    ? [-1, 1, -39, -38, 38, 39]   // Even column
    : [-1, 1, -40, -39, 39, 40]   // Odd column
    
  return offsets.map(offset => hexId + offset).filter(id => id >= 0)
}

// Start ranged fire targeting mode
const startRangedfireOrder = (unit) => {
  rangedfireUnit.value = unit
  rangedfireMode.value = true
  orderMessage.value = null
  orderError.value = null
  
  // Calculate valid targets: adjacent combat hexes
  const adjacent = getAdjacentHexes(unit.location)
  const unitFactionId = getUnitFactionId(unit)
  const unitInit = getFactionInitiative(unitFactionId)
  
  validRangedfireTargets.value = adjacent.filter(hexId => {
    // Check if hex is a combat hex (has enemy units)
    const unitsAtHex = allUnits.value.filter(u => u.location === hexId && u.alive)
    if (unitsAtHex.length === 0) return false
    
    // Check if any units are enemies
    const hasEnemy = unitsAtHex.some(u => {
      const theirInit = getFactionInitiative(getUnitFactionId(u))
      return theirInit !== unitInit
    })
    const hasAlly = unitsAtHex.some(u => {
      const theirInit = getFactionInitiative(getUnitFactionId(u))
      return theirInit === unitInit
    })
    
    // Valid if there are enemies (combat hex)
    return hasEnemy && hasAlly  // Needs to be an actual combat (both sides present)
  })
  
  if (validRangedfireTargets.value.length === 0) {
    orderError.value = "No valid targets - ranged fire requires an adjacent combat"
    rangedfireMode.value = false
    rangedfireUnit.value = null
  }
}

// Cancel ranged fire mode
const cancelRangedfireMode = () => {
  rangedfireMode.value = false
  rangedfireUnit.value = null
  validRangedfireTargets.value = []
  orderMessage.value = null
  orderError.value = null
}

// Submit ranged fire order when target hex is clicked
const submitRangedfireOrder = async (targetHex) => {
  if (!rangedfireUnit.value) return
  
  const unit = rangedfireUnit.value
  const factionId = getUnitFactionId(unit)
  
  try {
    const response = await fetch(`${API_BASE}/orders/rangedfire?faction_id=${factionId}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        unitId: unit.id,
        targetHex: targetHex
      })
    })
    
    if (!response.ok) {
      const data = await response.json()
      orderError.value = data.detail || 'Failed to submit ranged fire order'
      return
    }
    
    orderMessage.value = `Ranged fire order: ${unit.name} → Hex ${targetHex}`
    
    // Track in local state
    if (!submittedOrders.value[factionId]) {
      submittedOrders.value[factionId] = { movementOrders: [], rangedfireOrders: [] }
    }
    if (!submittedOrders.value[factionId].rangedfireOrders) {
      submittedOrders.value[factionId].rangedfireOrders = []
    }
    // Remove any existing order for this unit
    submittedOrders.value[factionId].rangedfireOrders = 
      submittedOrders.value[factionId].rangedfireOrders.filter(o => o.unitId !== unit.id)
    // Add new order
    submittedOrders.value[factionId].rangedfireOrders.push({
      unitId: unit.id,
      targetHex: targetHex,
      unitLocation: unit.location
    })
    
    // Exit rangedfire mode
    cancelRangedfireMode()
    
  } catch (err) {
    console.error('Rangedfire order error:', err)
    orderError.value = 'Network error submitting ranged fire order'
  }
}

// Cancel a submitted ranged fire order
const cancelUnitRangedfireOrder = async (unit) => {
  if (!unit) return
  
  const factionId = getUnitFactionId(unit)
  
  try {
    const response = await fetch(`${API_BASE}/orders/rangedfire/${unit.id}?faction_id=${factionId}`, {
      method: 'DELETE'
    })
    
    if (!response.ok) {
      const data = await response.json()
      orderError.value = data.detail || 'Failed to cancel ranged fire order'
      return
    }
    
    orderMessage.value = `Cancelled ranged fire order for ${unit.name}`
    
    // Remove from local tracking
    if (submittedOrders.value[factionId]?.rangedfireOrders) {
      submittedOrders.value[factionId].rangedfireOrders = 
        submittedOrders.value[factionId].rangedfireOrders.filter(o => o.unitId !== unit.id)
    }
    
  } catch (err) {
    console.error('Cancel rangedfire order error:', err)
    orderError.value = 'Network error cancelling ranged fire order'
  }
}

// Check if a hex is a valid ranged fire target
const isValidRangedfireTarget = (hexId) => {
  return rangedfireMode.value && validRangedfireTargets.value.includes(hexId)
}

// ==================== Fast Travel Functions ====================

// Check if unit can use fast travel (March for land, Full Sail for naval)
const canFastTravel = (unit) => {
  if (!unit) return false
  
  const unitType = unit.unitType || unit.unit_type || 0
  
  // Air units cannot fast travel
  if (unitType === 1 || unitType === 'air' || unitType === 'AIR') return false
  
  // Naval units need to be on ocean
  const isNaval = unitType === 2 || unitType === 'sea' || unitType === 'SEA'
  if (isNaval) {
    const hex = hexLookup.value[unit.location]
    return hex && hex.terrain === 'O'
  }
  
  // Land units need to be on a hex with at least one road connection
  const hex = hexLookup.value[unit.location]
  if (!hex) return false
  // Check if any hexside has a road
  return (hex.north?.road || hex.northeast?.road || hex.southeast?.road || 
          hex.south?.road || hex.southwest?.road || hex.northwest?.road)
}

// Get fast travel button label based on unit type
const getFastTravelLabel = (unit) => {
  if (!unit) return 'Fast Travel'
  const unitType = unit.unitType || unit.unit_type || 0
  const isNaval = unitType === 2 || unitType === 'sea' || unitType === 'SEA'
  return isNaval ? '⛵ Full Sail' : '🏃 March'
}

// Start fast travel mode
const startFastTravelMode = (unit) => {
  const unitType = unit.unitType || unit.unit_type || 0
  const isNaval = unitType === 2 || unitType === 'sea' || unitType === 'SEA'
  
  fastTravelUnit.value = unit
  fastTravelMode.value = true
  fastTravelPath.value = []
  fastTravelIsNaval.value = isNaval
  fastTravelError.value = null
  orderMessage.value = null
  orderError.value = null
}

// Cancel fast travel mode
const cancelFastTravelMode = () => {
  fastTravelMode.value = false
  fastTravelUnit.value = null
  fastTravelPath.value = []
  fastTravelError.value = null
}

// Check if a hex is valid for fast travel path
const isValidFastTravelHex = (hexId) => {
  if (!fastTravelMode.value || !fastTravelUnit.value) return false
  
  const unit = fastTravelUnit.value
  const currentHex = fastTravelPath.value.length > 0 
    ? fastTravelPath.value[fastTravelPath.value.length - 1]
    : unit.location
  
  // Check adjacency
  const diff = Math.abs(currentHex - hexId)
  if (![1, 38, 39].includes(diff)) return false
  
  // Check path length limit (get from config, default 10)
  if (fastTravelPath.value.length >= 10) return false
  
  // Check for hostile units
  const unitFactionId = getUnitFactionId(unit)
  const factionInit = getFactionInitiative(unitFactionId)
  const unitsAtHex = allUnits.value.filter(u => u.location === hexId && u.alive)
  for (const u of unitsAtHex) {
    // Use nullish coalescing (??) instead of || to handle faction ID 0 correctly
    const uFactionId = u.factionId ?? u.faction_id ?? u.faction
    const uInit = getFactionInitiative(uFactionId)
    if (uInit !== factionInit) return false  // Hostile unit
  }
  
  if (fastTravelIsNaval.value) {
    // Naval: must be ocean hex
    const hex = hexLookup.value[hexId]
    return hex && hex.terrain === 'O'
  } else {
    // Land: must have road from current to this hex
    return hasRoadBetween(currentHex, hexId)
  }
}

// Check if there's a road between two hexes (using hex data and hasRoad utility)
const hasRoadBetween = (from, to) => {
  const fromHex = hexLookup.value[from]
  if (!fromHex) return false
  
  // Use the imported hasRoad function from movementValidation.js
  return hasRoad(fromHex, from, to)
}

/**
 * Count hexside usage for fast travel validation.
 * Counts submitted orders (both Move and March) plus the current fast travel path being built.
 */
const getHexsideUsageForFastTravelValidation = (fromHex, toHex, factionId, currentFastTravelPath, unitStartLocation) => {
  const key = getHexsideKey(fromHex, toHex)
  
  // Count from submitted orders (excluding current unit if re-ordering)
  let count = countHexsideUsageInOrders(fromHex, toHex, factionId, fastTravelUnit.value?.id)
  
  // Count from the current fast travel path being built (before this new step)
  if (currentFastTravelPath.length > 0) {
    let prevHex = unitStartLocation
    for (const pathHex of currentFastTravelPath) {
      const stepKey = getHexsideKey(prevHex, pathHex)
      if (stepKey === key) {
        count++
      }
      prevHex = pathHex
    }
  }
  
  return count
}

// Add hex to fast travel path
const addToFastTravelPath = (hexId) => {
  if (!isValidFastTravelHex(hexId)) {
    fastTravelError.value = 'Invalid hex for fast travel'
    return
  }
  
  // Don't add duplicates
  if (fastTravelPath.value.includes(hexId)) return
  
  // Get current position (last path hex or unit's starting location)
  const unit = fastTravelUnit.value
  const currentHex = fastTravelPath.value.length > 0 
    ? fastTravelPath.value[fastTravelPath.value.length - 1]
    : unit.location
  
  // === HEXSIDE LIMIT CHECK ===
  const fromHexObj = hexLookup.value[currentHex]
  const hexsideTerrain = getHexsideTerrain(fromHexObj, currentHex, hexId)
  const roadExists = hasRoad(fromHexObj, currentHex, hexId)
  const hexsideLimit = getHexsideLimit(hexsideTerrain, roadExists)
  
  // Count how many units would cross this hexside (from all submitted orders + current path)
  const factionId = getUnitFactionId(unit)
  const currentUsage = getHexsideUsageForFastTravelValidation(
    currentHex,
    hexId,
    factionId,
    fastTravelPath.value,
    unit.location
  )
  
  // Adding this unit would make it currentUsage + 1
  if (currentUsage + 1 > hexsideLimit) {
    const terrainName = TERRAIN_NAMES[hexsideTerrain] || hexsideTerrain
    fastTravelError.value = `Hexside limit reached: ${currentUsage}/${hexsideLimit} units already crossing ${terrainName} hexside`
    return
  }
  
  fastTravelPath.value.push(hexId)
  fastTravelError.value = null
}

// Remove last hex from fast travel path
const undoFastTravelStep = () => {
  if (fastTravelPath.value.length > 0) {
    fastTravelPath.value.pop()
    fastTravelError.value = null
  }
}

// Submit fast travel order
const submitFastTravelOrder = async () => {
  if (!fastTravelUnit.value || fastTravelPath.value.length === 0) return
  
  const unit = fastTravelUnit.value
  const factionId = getUnitFactionId(unit)
  
  try {
    const response = await fetch(`${API_BASE}/orders/fast-travel?faction_id=${factionId}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        unitId: unit.id,
        path: fastTravelPath.value
      })
    })
    
    if (!response.ok) {
      const data = await response.json()
      fastTravelError.value = data.detail || 'Failed to submit fast travel order'
      return
    }
    
    const orderType = fastTravelIsNaval.value ? 'Full Sail' : 'March'
    orderMessage.value = `${orderType} order submitted for ${unit.name}: ${fastTravelPath.value.length} hexes`
    
    // Track the order locally as a fast travel order
    if (!submittedOrders.value[factionId]) {
      submittedOrders.value[factionId] = { movementOrders: [], rangedfireOrders: [], fastTravelOrders: [] }
    }
    if (!submittedOrders.value[factionId].fastTravelOrders) {
      submittedOrders.value[factionId].fastTravelOrders = []
    }
    submittedOrders.value[factionId].fastTravelOrders.push({
      unitId: unit.id,
      path: [...fastTravelPath.value],
      startLocation: unit.location,  // Track starting location for hexside limit counting
      isNaval: fastTravelIsNaval.value
    })
    
    cancelFastTravelMode()
    
  } catch (err) {
    console.error('Fast travel order error:', err)
    fastTravelError.value = 'Network error submitting fast travel order'
  }
}

// Check if unit has a fast travel order
const hasFastTravelOrder = (unit) => {
  if (!unit) return false
  const factionId = getUnitFactionId(unit)
  const factionOrders = submittedOrders.value[factionId]
  if (!factionOrders?.fastTravelOrders) return false
  return factionOrders.fastTravelOrders.some(o => o.unitId === unit.id)
}

// Cancel a fast travel order
const cancelFastTravelOrder = async (unit) => {
  if (!unit) return
  
  const factionId = getUnitFactionId(unit)
  
  try {
    const response = await fetch(`${API_BASE}/orders/fast-travel/${unit.id}?faction_id=${factionId}`, {
      method: 'DELETE'
    })
    
    if (!response.ok) {
      const data = await response.json()
      orderError.value = data.detail || 'Failed to cancel fast travel order'
      return
    }
    
    orderMessage.value = `Cancelled fast travel order for ${unit.name}`
    
    // Remove from local tracking
    if (submittedOrders.value[factionId]?.fastTravelOrders) {
      submittedOrders.value[factionId].fastTravelOrders = 
        submittedOrders.value[factionId].fastTravelOrders.filter(o => o.unitId !== unit.id)
    }
    
  } catch (err) {
    console.error('Cancel fast travel order error:', err)
    orderError.value = 'Network error cancelling fast travel order'
  }
}

// Check if hex is in fast travel path
const isInFastTravelPath = (hexId) => {
  return fastTravelPath.value.includes(hexId)
}

// Get fast travel order for a unit
const getFastTravelOrder = (unit) => {
  if (!unit) return null
  const factionId = getUnitFactionId(unit)
  const factionOrders = submittedOrders.value[factionId]
  if (!factionOrders?.fastTravelOrders) return null
  return factionOrders.fastTravelOrders.find(o => o.unitId === unit.id)
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
    stillOnRoads: stillOnRoads.value,  // Track if unit has been following roads the entire time
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
  
  // === HEXSIDE LIMIT CHECK ===
  // Air units ignore hexside limits entirely - skip this check for them
  const selectedUnitType = selectedUnit.value.unitType ?? selectedUnit.value.unit_type ?? 0
  const isSelectedUnitAir = selectedUnitType === 1 || selectedUnitType === 'air' || selectedUnitType === 'AIR'
  
  if (!isSelectedUnitAir) {
    // Check if this hexside would exceed the limit considering other submitted orders
    const hexsideTerrain = getHexsideTerrain(fromHexObj, currentHex, hexId)
    const roadExists = hasRoad(fromHexObj, currentHex, hexId)
    const hexsideLimit = getHexsideLimit(hexsideTerrain, roadExists)
    
    // Count how many units (including this one) would cross this hexside
    const currentUsage = getHexsideUsageForValidation(
      currentHex, 
      hexId, 
      unitFactionId, 
      movementPath.value,
      selectedUnit.value.location
    )
    
    // Adding this unit would make it currentUsage + 1
    if (currentUsage + 1 > hexsideLimit) {
      const terrainName = TERRAIN_NAMES[hexsideTerrain] || hexsideTerrain
      const errorMsg = `Hexside limit reached: ${currentUsage}/${hexsideLimit} units already crossing ${terrainName} hexside`
      orderError.value = errorMsg
      pathValidation.value = { valid: false, message: errorMsg }
      setTimeout(() => { 
        if (orderError.value === errorMsg) orderError.value = null 
      }, 4000)
      return
    }
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
  
  // Update stillOnRoads: if this hexside didn't have a road, can no longer use road bonus
  // Air units also can never use road bonus
  // IMPORTANT: Must use ?? not || because unitType=0 (GROUND) is falsy!
  const unitType = selectedUnit.value.unitType ?? selectedUnit.value.unit_type ?? 0
  const isAirUnit = unitType === 1 || unitType === 'air' || unitType === 'AIR'  // AIR = 1
  if (!validation.hasRoad || isAirUnit) {
    stillOnRoads.value = false
  }
  
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
    stillOnRoads.value = true  // Reset to true when path is empty
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
    // stillOnRoads is tracked across all steps - if any step didn't have a road, it's false
    stillOnRoads.value = lastStep.stillOnRoads !== undefined ? lastStep.stillOnRoads : true
  } else {
    lastStepWasRough.value = false
    lastStepUsedRoad.value = false
    stillOnRoads.value = true
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
  stillOnRoads.value = true  // Reset road following flag
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
const MAX_ZOOM = 1.5
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
  e.preventDefault()
  
  const container = mapScrollRef.value
  if (!container) return
  
  const oldZoom = zoom.value
  const delta = e.deltaY < 0 ? ZOOM_STEP : -ZOOM_STEP
  const newZoom = Math.max(MIN_ZOOM, Math.min(MAX_ZOOM, zoom.value + delta))
  
  if (newZoom === oldZoom) return
  
  // Get the center point of the current view on the actual map
  const centerX = (container.scrollLeft + container.clientWidth / 2) / oldZoom
  const centerY = (container.scrollTop + container.clientHeight / 2) / oldZoom
  
  // Update zoom
  zoom.value = newZoom
  
  // After Vue updates the DOM, adjust scroll to keep the same center point
  requestAnimationFrame(() => {
    container.scrollLeft = centerX * newZoom - container.clientWidth / 2
    container.scrollTop = centerY * newZoom - container.clientHeight / 2
  })
}

const zoomPercent = () => Math.round(zoom.value * 100)

// WASD Scrolling
const SCROLL_SPEED = 10  // pixels per keypress
const scrollKeys = { w: false, a: false, s: false, d: false }
let scrollAnimationId = null

const handleKeyDown = (e) => {
  const key = e.key.toLowerCase()
  if (['w', 'a', 's', 'd'].includes(key)) {
    // Don't scroll if typing in an input
    if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') return
    e.preventDefault()
    scrollKeys[key] = true
    startScrollAnimation()
  }
}

const handleKeyUp = (e) => {
  const key = e.key.toLowerCase()
  if (['w', 'a', 's', 'd'].includes(key)) {
    scrollKeys[key] = false
  }
}

const startScrollAnimation = () => {
  if (scrollAnimationId) return  // Already running
  
  const animate = () => {
    const container = mapScrollRef.value
    if (!container) {
      scrollAnimationId = null
      return
    }
    
    let dx = 0, dy = 0
    if (scrollKeys.w) dy -= SCROLL_SPEED
    if (scrollKeys.s) dy += SCROLL_SPEED
    if (scrollKeys.a) dx -= SCROLL_SPEED
    if (scrollKeys.d) dx += SCROLL_SPEED
    
    if (dx !== 0 || dy !== 0) {
      container.scrollLeft += dx
      container.scrollTop += dy
      scrollAnimationId = requestAnimationFrame(animate)
    } else {
      scrollAnimationId = null
    }
  }
  
  scrollAnimationId = requestAnimationFrame(animate)
}

const loadMapData = async () => {
  loading.value = true
  console.log('[Map] Starting map data load...')
  
  // Load hexes
  try {
    console.log('[Map] Loading hexes from /hexes/map...')
    const hexRes = await hexes.getMapData({ limit: 1200 })
    allHexes.value = hexRes.data || []
    console.log(`[Map] Loaded ${allHexes.value.length} hexes`)
  } catch (e) {
    console.error('[Map] Failed to load hexes:', e.message)
    allHexes.value = []
  }
  
  // Load bases
  try {
    console.log('[Map] Loading bases...')
    const basesRes = await bases.list({ limit: 200 })
    allBases.value = basesRes.data || []
    console.log(`[Map] Loaded ${allBases.value.length} bases`)
  } catch (e) {
    console.error('[Map] Failed to load bases:', e.message)
    allBases.value = []
  }
  
  // Load expansions
  try {
    console.log('[Map] Loading expansions...')
    const expansionsRes = await expansionsApi.list({ limit: 500 })
    allExpansions.value = expansionsRes.data || []
    console.log(`[Map] Loaded ${allExpansions.value.length} expansions`)
  } catch (e) {
    console.error('[Map] Failed to load expansions:', e.message)
    allExpansions.value = []
  }
  
  // Load factions
  try {
    console.log('[Map] Loading factions...')
    const factionsRes = await factionsApi.list({ limit: 50 })
    for (const faction of (factionsRes.data || [])) {
      factionData.value[faction.id] = faction
    }
    console.log(`[Map] Loaded ${Object.keys(factionData.value).length} factions`)
  } catch (e) {
    console.error('[Map] Failed to load factions:', e.message)
  }
  
  // Load units
  try {
    console.log('[Map] Loading units...')
    const unitsRes = await axios.get(`${API_BASE}/units?limit=1000`)
    allUnits.value = (unitsRes.data || []).filter(u => u.alive !== false)
    console.log(`[Map] Loaded ${allUnits.value.length} alive units`)
  } catch (e) {
    console.error('[Map] Failed to load units:', e.message)
    allUnits.value = []
  }
  
  // Load combats (optional, may not exist)
  await loadCombats()
  
  // Load caravans for display
  await loadAllCaravans()
  
  // Load debug config
  await loadDebugConfig()
  
  loading.value = false
  console.log(`[Map] Load complete! Hexes: ${allHexes.value.length}, Bases: ${allBases.value.length}, Expansions: ${allExpansions.value.length}, Units: ${allUnits.value.length}, Caravans: ${allCaravans.value.length}`)
}

// Load debug config from server
const loadDebugConfig = async () => {
  try {
    const response = await axios.get(`${API_BASE}/admin/config`)
    if (response.data?.config?.debug) {
      debugConfig.value = response.data.config.debug
      console.log('[Map] Loaded debug config:', debugConfig.value)
    }
  } catch (e) {
    console.warn('[Map] Failed to load debug config:', e.message)
  }
}

// Load active combat data
const loadCombats = async () => {
  try {
    const response = await axios.get(`${API_BASE}/admin/combats`)
    activeCombats.value = response.data.combats || []
  } catch (e) {
    // Combat endpoint might not exist yet, that's okay
    activeCombats.value = []
  }
}

const selectHex = async (hex) => {
  // If in rangedfire mode, handle target selection
  if (rangedfireMode.value && isValidRangedfireTarget(hex.id)) {
    await submitRangedfireOrder(hex.id)
    return
  }
  
  // If in caravan mode, handle path building
  if (caravanMode.value) {
    if (await handleCaravanHexClick(hex.id)) {
      return
    }
  }
  
  // If in expand mode, handle target selection
  if (expandMode.value) {
    if (handleExpandHexClick(hex.id)) {
      return
    }
  }
  
  // If in movement mode, add to path instead of selecting
  if (movementMode.value && selectedUnit.value) {
    addToPath(hex.id)
    return
  }
  
  // If in fast travel mode, add to fast travel path
  if (fastTravelMode.value && fastTravelUnit.value) {
    addToFastTravelPath(hex.id)
    return
  }
  
  // Normal hex selection - clear other detail views first and exit expand mode
  cancelCaravanMode()
  cancelRangedfireMode()
  cancelFastTravelMode()
  exitExpandMode()
  selectedUnitDetail.value = null
  selectedBaseDetail.value = null
  selectedHex.value = hex
  try {
    const response = await unitsApi.atHex(hex.id)
    hexUnits.value = response.data
  } catch (e) {
    console.error('Failed to load units:', e)
    hexUnits.value = []
  }
}

// Check if we're in a hex-targeting input mode
// When true, clicking on objects (bases, units) should select the hex instead
const isHexTargetingMode = computed(() => {
  return (movementMode.value && selectedUnit.value) || 
         (fastTravelMode.value && fastTravelUnit.value) ||
         (caravanMode.value) ||
         (rangedfireMode.value)
})

// Select a unit directly from clicking on the map - opens Unit Info
const selectUnitFromMap = async (unit) => {
  // If in hex targeting mode, redirect click to the hex
  if (isHexTargetingMode.value) {
    const hex = hexLookup.value[unit.location]
    if (hex) {
      selectHex(hex)
      return
    }
  }
  
  // Clear other selections and show unit detail
  selectedHex.value = null
  selectedBaseDetail.value = null
  selectedUnitDetail.value = unit
}

// Select a unit from the hex info list - opens Unit Info
const selectUnitForDetail = (unit) => {
  selectedUnitDetail.value = unit
}

// Close unit detail and return to hex view
const closeUnitDetail = () => {
  selectedUnitDetail.value = null
}

// Select a base directly from clicking on the map - opens Base Info
const selectBaseFromMap = async (base) => {
  if (!base) return
  
  // If in any hex targeting mode, redirect click to the hex
  // This prevents accidentally selecting a base when you're trying to input a movement or caravan path
  if (isHexTargetingMode.value) {
    const hex = hexLookup.value[base.location]
    if (hex) {
      selectHex(hex)
      return
    }
  }
  
  // Clear other selections
  selectedHex.value = null
  selectedUnitDetail.value = null
  selectedBaseExpansions.value = []
  baseOrders.value = null
  harvestPreview.value = null
  expandTargetsPreview.value = null
  upgradeInfo.value = null
  
  // Fetch full base detail (includes resources), expansions, orders, harvest preview, expand targets, upgrade info, restable units, and buildable units
  try {
    const [baseResponse, expansionsResponse, ordersResponse, harvestResponse, expandResponse, upgradeResponse, restResponse, buildResponse] = await Promise.all([
      bases.get(base.id),
      expansionsApi.forBase(base.id),
      bases.getOrders(base.id),
      bases.previewHarvest(base.id),
      bases.getExpandableHexes(base.id),
      bases.getUpgradeInfo(base.id),
      bases.getRestableUnits(base.id),
      bases.getBuildableUnits(base.id)
    ])
    selectedBaseDetail.value = baseResponse.data
    selectedBaseExpansions.value = expansionsResponse.data || []
    baseOrders.value = ordersResponse.data
    harvestPreview.value = harvestResponse.data
    expandTargetsPreview.value = expandResponse.data?.validTargets || []
    upgradeInfo.value = upgradeResponse.data
    restableUnits.value = restResponse.data?.units || []
    buildableUnits.value = buildResponse.data?.units || []
    buildFoodInfo.value = buildResponse.data?.food || null
    buildAlreadyQueued.value = buildResponse.data?.alreadyQueued || false
  } catch (e) {
    console.error('[Map] Failed to load base details:', e.message)
    // Fallback to summary if detail fetch fails
    selectedBaseDetail.value = base
    selectedBaseExpansions.value = []
    baseOrders.value = null
    harvestPreview.value = null
    expandTargetsPreview.value = null
    upgradeInfo.value = null
    restableUnits.value = []
    buildableUnits.value = []
    buildFoodInfo.value = null
    buildAlreadyQueued.value = false
  }
}

// Select a base from the hex info panel
const selectBaseForDetail = async (base) => {
  if (!base) return
  selectedBaseExpansions.value = []
  baseOrders.value = null
  harvestPreview.value = null
  expandTargetsPreview.value = null
  upgradeInfo.value = null
  restableUnits.value = []
  restMode.value = false
  buildableUnits.value = []
  buildFoodInfo.value = null
  buildAlreadyQueued.value = false
  buildModalOpen.value = false
  
  try {
    const [baseResponse, expansionsResponse, ordersResponse, harvestResponse, expandResponse, upgradeResponse, restResponse, buildResponse] = await Promise.all([
      bases.get(base.id),
      expansionsApi.forBase(base.id),
      bases.getOrders(base.id),
      bases.previewHarvest(base.id),
      bases.getExpandableHexes(base.id),
      bases.getUpgradeInfo(base.id),
      bases.getRestableUnits(base.id),
      bases.getBuildableUnits(base.id)
    ])
    selectedBaseDetail.value = baseResponse.data
    selectedBaseExpansions.value = expansionsResponse.data || []
    baseOrders.value = ordersResponse.data
    harvestPreview.value = harvestResponse.data
    expandTargetsPreview.value = expandResponse.data?.validTargets || []
    upgradeInfo.value = upgradeResponse.data
    restableUnits.value = restResponse.data?.units || []
    buildableUnits.value = buildResponse.data?.units || []
    buildFoodInfo.value = buildResponse.data?.food || null
    buildAlreadyQueued.value = buildResponse.data?.alreadyQueued || false
  } catch (e) {
    console.error('[Map] Failed to load base details:', e.message)
    selectedBaseDetail.value = base
    selectedBaseExpansions.value = []
    expandTargetsPreview.value = null
    upgradeInfo.value = null
    restableUnits.value = []
    buildableUnits.value = []
    buildFoodInfo.value = null
    buildAlreadyQueued.value = false
  }
}

// Close base detail
const closeBaseDetail = () => {
  selectedBaseDetail.value = null
  selectedBaseExpansions.value = []
  baseOrders.value = null
  harvestPreview.value = null
  expandTargetsPreview.value = null
  upgradeInfo.value = null
  exitExpandMode()
}

// ==================== BASE ACTIONS ====================

// Queue a Harvest action
const queueHarvest = async () => {
  if (!selectedBaseDetail.value) return
  
  try {
    const response = await bases.queueHarvest(selectedBaseDetail.value.id)
    // Update orders state
    baseOrders.value = {
      ...baseOrders.value,
      actionsUsed: response.data.actionsUsed,
      actionsRemaining: response.data.actionsRemaining,
      orders: response.data.allOrders,
      pendingResources: response.data.pendingResources
    }
    // Update harvest preview (can no longer harvest)
    harvestPreview.value = {
      ...harvestPreview.value,
      canHarvest: false,
      reason: 'Already have a pending harvest action'
    }
    // Refresh expand targets (pending lumber changed, may affect affordability)
    await refreshExpandTargets()
  } catch (e) {
    console.error('[Map] Failed to queue harvest:', e.message)
  }
}

// Cancel the last queued order
const cancelLastOrder = async () => {
  if (!selectedBaseDetail.value) return
  
  try {
    const response = await bases.cancelLastOrder(selectedBaseDetail.value.id)
    // Update orders state
    baseOrders.value = {
      ...baseOrders.value,
      actionsUsed: (baseOrders.value?.actionsUsed || 1) - 1,
      actionsRemaining: response.data.actionsRemaining,
      orders: response.data.remainingOrders,
      pendingResources: response.data.pendingResources
    }
    // If we cancelled a harvest, refresh harvest preview
    if (response.data.cancelledOrder?.type === 'harvest') {
      const harvestResponse = await bases.previewHarvest(selectedBaseDetail.value.id)
      harvestPreview.value = harvestResponse.data
    }
    // If we cancelled an expand, exit expand mode and refresh targets
    if (response.data.cancelledOrder?.type === 'expand') {
      await refreshExpandTargets()
    }
    // If we cancelled a build_unit, refresh buildable units (food cap changed)
    if (response.data.cancelledOrder?.type === 'build_unit') {
      await loadBuildableUnits()
    }
  } catch (e) {
    console.error('[Map] Failed to cancel order:', e.message)
  }
}

// ==================== EXPAND ACTION ====================

// Enter expand mode - load valid targets and highlight them
const enterExpandMode = async () => {
  if (!selectedBaseDetail.value) return
  
  // Use cached targets if available, otherwise fetch
  if (expandTargetsPreview.value && expandTargetsPreview.value.length > 0) {
    expandableTargets.value = expandTargetsPreview.value
    expandMode.value = true
    return
  }
  
  try {
    const response = await bases.getExpandableHexes(selectedBaseDetail.value.id)
    expandableTargets.value = response.data.validTargets || []
    expandTargetsPreview.value = expandableTargets.value
    expandMode.value = true
  } catch (e) {
    console.error('[Map] Failed to load expandable targets:', e.message)
  }
}

// Exit expand mode
const exitExpandMode = () => {
  expandMode.value = false
  expandableTargets.value = []
}

// Refresh expandable targets (after queueing or cancelling)
const refreshExpandTargets = async () => {
  if (!selectedBaseDetail.value) return
  
  try {
    const response = await bases.getExpandableHexes(selectedBaseDetail.value.id)
    expandableTargets.value = response.data.validTargets || []
    expandTargetsPreview.value = expandableTargets.value
  } catch (e) {
    console.error('[Map] Failed to refresh expandable targets:', e.message)
  }
}

// Check if a hex is a valid expansion target
const isExpandableTarget = (hexId) => {
  return expandableTargets.value.some(t => t.hexId === hexId)
}

// Get expansion target info for a hex
const getExpandTarget = (hexId) => {
  return expandableTargets.value.find(t => t.hexId === hexId)
}

// Queue an expand action for a target hex
const queueExpand = async (targetHex) => {
  if (!selectedBaseDetail.value) return
  
  try {
    const response = await bases.queueExpand(selectedBaseDetail.value.id, targetHex)
    
    // Update orders state
    baseOrders.value = {
      ...baseOrders.value,
      actionsUsed: response.data.actionsUsed,
      actionsRemaining: response.data.actionsRemaining,
      orders: response.data.allOrders,
      pendingResources: response.data.pendingResources
    }
    
    // Exit expand mode and refresh targets
    exitExpandMode()
    
    // Refresh to show the expansion is "pending"
    await refreshExpandTargets()
    
  } catch (e) {
    console.error('[Map] Failed to queue expand:', e.message)
  }
}

// Handle clicking on a hex while in expand mode
const handleExpandHexClick = (hexId) => {
  if (!expandMode.value) return false
  
  const target = getExpandTarget(hexId)
  if (target && target.canAfford) {
    queueExpand(hexId)
    return true // Handled
  }
  
  // Click on invalid hex exits expand mode
  exitExpandMode()
  return true // Handled
}

// Pre-loaded expand targets for validation
const expandTargetsPreview = ref(null)

// Validate expand action - returns { canExpand: bool, reasons: string[] }
const expandValidation = computed(() => {
  const reasons = []
  
  if (!baseOrders.value) {
    return { canExpand: false, reasons: ['Loading...'] }
  }
  
  // Check actions remaining
  if (baseOrders.value.actionsRemaining <= 0) {
    reasons.push('No actions remaining')
  }
  
  // Check if already have an expand order queued
  const hasExpandOrder = baseOrders.value.orders?.some(o => o.type === 'expand')
  if (hasExpandOrder) {
    reasons.push('Already have Expand queued')
  }
  
  // Check effective lumber (current + pending from harvest etc) - skip if infinite resources
  if (!debugConfig.value.infinite_resources) {
    const currentLumber = selectedBaseDetail.value?.lumber ?? 0
    const pendingLumber = baseOrders.value.pendingResources?.lumber ?? 0
    const effectiveLumber = currentLumber + pendingLumber
    if (effectiveLumber < 2) {
      reasons.push(`Not enough lumber (need 2, have ${effectiveLumber})`)
    }
  }
  
  // Check if there are valid expansion targets
  if (expandTargetsPreview.value !== null && expandTargetsPreview.value.length === 0) {
    reasons.push('No valid expansion sites')
  }
  
  return {
    canExpand: reasons.length === 0,
    reasons
  }
})

// Computed for whether expand button should be enabled
const canExpand = computed(() => expandValidation.value.canExpand)

// Tooltip for expand button when disabled
const expandTooltip = computed(() => {
  const validation = expandValidation.value
  if (validation.canExpand) {
    return 'Build a new expansion (2 lumber)'
  }
  return validation.reasons.join('; ')
})

// ==================== COMMERCE ACTION ====================

// Commerce options from backend
const commerceOptions = ref(null)

// Commerce mode state
const commerceMode = ref(false)
const selectedCommerceFrom = ref(null)

// Resource display names and icons
const RESOURCE_INFO = {
  gold: { name: 'Gold', icon: '🪙' },
  lumber: { name: 'Lumber', icon: '🪵' },
  oil: { name: 'Oil', icon: '🛢️' }
}

// Load commerce options
const loadCommerceOptions = async () => {
  if (!selectedBaseDetail.value) return
  
  try {
    const response = await bases.getCommerceOptions(selectedBaseDetail.value.id)
    commerceOptions.value = response.data
  } catch (e) {
    console.error('[Map] Failed to load commerce options:', e.message)
    commerceOptions.value = null
  }
}

// Validate commerce action
const commerceValidation = computed(() => {
  const reasons = []
  
  if (!baseOrders.value) {
    return { canCommerce: false, reasons: ['Loading...'] }
  }
  
  // Check actions remaining
  if (baseOrders.value.actionsRemaining <= 0) {
    reasons.push('No actions remaining')
  }
  
  // Check if already have a commerce order queued
  const hasCommerceOrder = baseOrders.value.orders?.some(o => o.type === 'commerce')
  if (hasCommerceOrder) {
    reasons.push('Already have Commerce queued')
  }
  
  // Check if any resource has at least 2 effective (skip if infinite resources enabled)
  const effectiveGold = (selectedBaseDetail.value?.gold ?? 0) + (baseOrders.value.pendingResources?.gold ?? 0)
  const effectiveLumber = (selectedBaseDetail.value?.lumber ?? 0) + (baseOrders.value.pendingResources?.lumber ?? 0)
  const effectiveOil = (selectedBaseDetail.value?.oil ?? 0) + (baseOrders.value.pendingResources?.oil ?? 0)
  
  if (!debugConfig.value.infinite_resources) {
    const hasEnoughResources = effectiveGold >= 2 || effectiveLumber >= 2 || effectiveOil >= 2
    if (!hasEnoughResources) {
      reasons.push('Need at least 2 of any resource')
    }
  }
  
  return {
    canCommerce: reasons.length === 0,
    reasons,
    effectiveGold,
    effectiveLumber,
    effectiveOil
  }
})

// Computed for whether commerce button should be enabled
const canCommerce = computed(() => commerceValidation.value.canCommerce)

// Tooltip for commerce button when disabled
const commerceTooltip = computed(() => {
  const validation = commerceValidation.value
  if (validation.canCommerce) {
    return 'Convert 2 of one resource into 1 of another'
  }
  return validation.reasons.join('; ')
})

// Get available "from" resources (those with >= 2 effective, or all if infinite resources)
const commerceFromOptions = computed(() => {
  const v = commerceValidation.value
  const options = []
  const infiniteResources = debugConfig.value.infinite_resources
  if (infiniteResources || v.effectiveGold >= 2) options.push({ resource: 'gold', amount: v.effectiveGold, ...RESOURCE_INFO.gold })
  if (infiniteResources || v.effectiveLumber >= 2) options.push({ resource: 'lumber', amount: v.effectiveLumber, ...RESOURCE_INFO.lumber })
  if (infiniteResources || v.effectiveOil >= 2) options.push({ resource: 'oil', amount: v.effectiveOil, ...RESOURCE_INFO.oil })
  return options
})

// Get available "to" resources (any except the selected "from")
const commerceToOptions = computed(() => {
  if (!selectedCommerceFrom.value) return []
  return Object.entries(RESOURCE_INFO)
    .filter(([key]) => key !== selectedCommerceFrom.value)
    .map(([key, info]) => ({ resource: key, ...info }))
})

// Enter commerce mode
const enterCommerceMode = () => {
  if (!canCommerce.value) return
  commerceMode.value = true
  selectedCommerceFrom.value = null
}

// Exit commerce mode
const exitCommerceMode = () => {
  commerceMode.value = false
  selectedCommerceFrom.value = null
}

// Queue commerce order
const queueCommerce = async (toResource) => {
  if (!selectedBaseDetail.value || !selectedCommerceFrom.value) return
  
  try {
    const response = await bases.queueCommerce(
      selectedBaseDetail.value.id,
      selectedCommerceFrom.value,
      toResource
    )
    
    // Update orders state
    baseOrders.value = {
      ...baseOrders.value,
      actionsUsed: response.data.actionsUsed,
      actionsRemaining: response.data.actionsRemaining,
      orders: response.data.allOrders,
      pendingResources: response.data.pendingResources
    }
    
    // Exit commerce mode
    exitCommerceMode()
    
    // Refresh expand targets (pending resources changed)
    await refreshExpandTargets()
    
  } catch (e) {
    console.error('[Map] Failed to queue commerce:', e.message)
  }
}

// ==================== UPGRADE BASE ACTION ====================

// Upgrade info from backend
const upgradeInfo = ref(null)

// Load upgrade info
const loadUpgradeInfo = async () => {
  if (!selectedBaseDetail.value) return
  
  try {
    const response = await bases.getUpgradeInfo(selectedBaseDetail.value.id)
    upgradeInfo.value = response.data
  } catch (e) {
    console.error('[Map] Failed to load upgrade info:', e.message)
    upgradeInfo.value = null
  }
}

// Validation for upgrade
const upgradeValidation = computed(() => {
  if (!upgradeInfo.value) {
    return { canUpgrade: false, reasons: ['Loading...'] }
  }
  
  // Check if already at max tier
  if (upgradeInfo.value.targetTier === null) {
    return { canUpgrade: false, reasons: ['Already at maximum tier'] }
  }
  
  // Check actions remaining
  if (!baseOrders.value || baseOrders.value.actionsRemaining <= 0) {
    return { canUpgrade: false, reasons: ['No actions remaining'] }
  }
  
  // Check if already have an upgrade order queued
  const hasUpgradeOrder = baseOrders.value.orders?.some(o => o.type === 'upgrade')
  if (hasUpgradeOrder) {
    return { canUpgrade: false, reasons: ['Already have Upgrade queued'] }
  }
  
  // Use reasons from backend validation
  if (upgradeInfo.value.reasons && upgradeInfo.value.reasons.length > 0) {
    return { canUpgrade: false, reasons: upgradeInfo.value.reasons }
  }
  
  return { canUpgrade: upgradeInfo.value.canUpgrade, reasons: [] }
})

// Computed for whether upgrade button should be enabled
const canUpgrade = computed(() => upgradeValidation.value.canUpgrade)

// Tooltip for upgrade button when disabled
const upgradeTooltip = computed(() => {
  const validation = upgradeValidation.value
  if (validation.canUpgrade && upgradeInfo.value) {
    const cost = upgradeInfo.value.cost
    return `Upgrade to Tier ${upgradeInfo.value.targetTier} (${cost.gold}🪙 ${cost.lumber}🪵 ${cost.oil}🛢️)`
  }
  return validation.reasons.join('; ')
})

// Queue upgrade order
const queueUpgrade = async () => {
  if (!selectedBaseDetail.value || !canUpgrade.value) return
  
  try {
    const response = await bases.queueUpgrade(selectedBaseDetail.value.id)
    
    // Update orders state
    baseOrders.value = {
      ...baseOrders.value,
      actionsUsed: response.data.actionsUsed,
      actionsRemaining: response.data.actionsRemaining,
      orders: response.data.allOrders,
      pendingResources: response.data.pendingResources
    }
    
    // Refresh upgrade info (can't upgrade again)
    await loadUpgradeInfo()
    
    // Refresh expand targets (pending resources changed)
    await refreshExpandTargets()
    
  } catch (e) {
    console.error('[Map] Failed to queue upgrade:', e.message)
  }
}

// ==================== REST UNIT ACTION ====================

// Rest Unit state
const restableUnits = ref([])
const restMode = ref(false)
const selectedRestUnit = ref(null)

// Load restable units at base
const loadRestableUnits = async () => {
  if (!selectedBaseDetail.value) return
  
  try {
    const response = await bases.getRestableUnits(selectedBaseDetail.value.id)
    restableUnits.value = response.data.units || []
  } catch (e) {
    console.error('[Map] Failed to load restable units:', e.message)
    restableUnits.value = []
  }
}

// Computed: can show rest button (has actions, has units that can rest)
const hasRestableUnits = computed(() => {
  return restableUnits.value.some(u => u.can_rest || u.canRest)
})

// Check if rest action already queued
const hasRestQueued = computed(() => {
  return baseOrders.value?.orders?.some(o => o.type === 'rest')
})

// Can rest validation
const canRest = computed(() => {
  // Check actions remaining
  if (!baseOrders.value || baseOrders.value.actionsRemaining <= 0) {
    return { canRest: false, reason: 'No actions remaining' }
  }
  
  // Check if already have a rest order queued
  if (hasRestQueued.value) {
    return { canRest: false, reason: 'Already have Rest Unit queued' }
  }
  
  // Check if we have at least 2 effective gold (skip if infinite resources)
  if (!debugConfig.value.infinite_resources) {
    const effectiveGold = (selectedBaseDetail.value?.gold || 0) + (baseOrders.value?.pendingResources?.gold || 0)
    if (effectiveGold < 2) {
      return { canRest: false, reason: 'Not enough gold (need 2)' }
    }
  }
  
  // Check if any units can be rested
  if (!hasRestableUnits.value) {
    return { canRest: false, reason: 'No units available to rest' }
  }
  
  return { canRest: true, reason: '' }
})

const restTooltip = computed(() => {
  const validation = canRest.value
  if (validation.canRest) {
    return 'Heal a unit for 1/4 max HP (costs 2 gold)'
  }
  return validation.reason
})

// Enter rest mode to select a unit
const enterRestMode = () => {
  restMode.value = true
  selectedRestUnit.value = null
}

// Cancel rest mode
const cancelRestMode = () => {
  restMode.value = false
  selectedRestUnit.value = null
}

// Queue rest unit order
const queueRestUnit = async (unit) => {
  if (!selectedBaseDetail.value) return
  
  try {
    const response = await bases.queueRestUnit(selectedBaseDetail.value.id, unit.unit_id || unit.unitId)
    
    // Update orders state
    baseOrders.value = {
      ...baseOrders.value,
      actionsUsed: response.data.actionsUsed,
      actionsRemaining: response.data.actionsRemaining,
      orders: response.data.allOrders,
      pendingResources: response.data.pendingResources
    }
    
    // Exit rest mode
    restMode.value = false
    selectedRestUnit.value = null
    
    // Refresh restable units
    await loadRestableUnits()
    
    // Refresh expand targets (pending resources changed)
    await refreshExpandTargets()
    
  } catch (e) {
    console.error('[Map] Failed to queue rest unit:', e.message)
  }
}

// Get pending resource amount for a resource type
const getPendingResource = (resourceType) => {
  if (!baseOrders.value?.pendingResources) return 0
  return baseOrders.value.pendingResources[resourceType] || 0
}

// ==================== Build Unit State ====================
const buildableUnits = ref([])
const buildModalOpen = ref(false)
const buildFoodInfo = ref(null)
const buildAlreadyQueued = ref(false)

// Load buildable units for the selected base
const loadBuildableUnits = async () => {
  if (!selectedBaseDetail.value) return
  
  try {
    const response = await bases.getBuildableUnits(selectedBaseDetail.value.id)
    buildableUnits.value = response.data.units || []
    buildFoodInfo.value = response.data.food || null
    buildAlreadyQueued.value = response.data.alreadyQueued || false
  } catch (e) {
    console.error('[Map] Failed to load buildable units:', e.message)
    buildableUnits.value = []
    buildFoodInfo.value = null
    buildAlreadyQueued.value = false
  }
}

// Check if build action already queued
const hasBuildQueued = computed(() => {
  return baseOrders.value?.orders?.some(o => o.type === 'build_unit')
})

// Can show build button
const canShowBuildButton = computed(() => {
  if (!selectedBaseDetail.value) return false
  if (selectedBaseDetail.value.inCombat) return false
  const actionsRemaining = (selectedBaseDetail.value.actions || selectedBaseDetail.value.tier) - (baseOrders.value?.orders?.length || 0)
  return actionsRemaining > 0 && !hasBuildQueued.value
})

// Tooltip for build button when disabled
const buildTooltip = computed(() => {
  if (!selectedBaseDetail.value) return ''
  if (selectedBaseDetail.value.inCombat) return 'Base is in combat'
  if (hasBuildQueued.value) return 'Build Unit already queued'
  const actionsRemaining = (selectedBaseDetail.value.actions || selectedBaseDetail.value.tier) - (baseOrders.value?.orders?.length || 0)
  if (actionsRemaining <= 0) return 'No actions remaining'
  if (!buildFoodInfo.value?.canBuild) return 'Food cap reached'
  return 'Select a unit to build'
})

// Open build modal
const openBuildModal = async () => {
  await loadBuildableUnits()
  buildModalOpen.value = true
}

// Close build modal
const closeBuildModal = () => {
  buildModalOpen.value = false
}

// Queue build unit order
const queueBuildUnit = async (unit) => {
  if (!selectedBaseDetail.value || !unit.can_build) return
  
  try {
    await bases.queueBuildUnit(selectedBaseDetail.value.id, unit.unit_name)
    
    // Close modal
    buildModalOpen.value = false
    
    // Refresh base orders
    const ordersResp = await bases.getOrders(selectedBaseDetail.value.id)
    baseOrders.value = ordersResp.data
    
    // Refresh buildable units (food status changed)
    await loadBuildableUnits()
    
    // Refresh expand targets (pending resources changed)
    await refreshExpandTargets()
    
  } catch (e) {
    console.error('[Map] Failed to queue build unit:', e.message)
  }
}

// ==================== Caravan State ====================
const showCaravans = ref(true)                    // Toggle for displaying caravan routes
const caravanMode = ref(false)                    // Whether we're in caravan establishment mode
const caravanTargets = ref([])                    // Valid destination bases (same initiative)
const caravanPath = ref([])                       // Current path being traced
const caravanValidNextHexes = ref([])             // Valid hexes to extend path (includes destinations)
const caravanIsSea = ref(null)                    // null = undecided, true = sea, false = land
const caravanCost = ref({ lumber: 0, oil: 0 })    // Current cost based on path length
const caravanError = ref(null)                    // Error message to display
const allCaravans = ref([])                       // All caravans for display

// Load all caravans for display
const loadAllCaravans = async () => {
  try {
    const response = await axios.get(`${API_BASE}/caravans`)
    allCaravans.value = response.data?.caravans || []
    console.log(`[Map] Loaded ${allCaravans.value.length} caravans`)
  } catch (e) {
    console.error('[Map] Failed to load caravans:', e.message)
    allCaravans.value = []
  }
}

// Toggle caravan display
const toggleCaravanDisplay = () => {
  showCaravans.value = !showCaravans.value
}

// Get caravan line color based on initiative (uses same logic as hexside control)
const getCaravanColor = (caravan) => {
  return getInitiativeColor(caravan.initiative)
}

// Check if base can establish a caravan
const canEstablishCaravan = computed(() => {
  if (!selectedBaseDetail.value) return false
  if (selectedBaseDetail.value.inCombat) return false
  const actionsRemaining = (selectedBaseDetail.value.actions || selectedBaseDetail.value.tier) - (baseOrders.value?.orders?.length || 0)
  if (actionsRemaining <= 0) return false
  // Check if already queued a caravan
  if (baseOrders.value?.orders?.some(o => o.type === 'establish_caravan')) return false
  return true
})

// Enter caravan establishment mode
const startCaravanMode = async () => {
  if (!selectedBaseDetail.value) return
  
  try {
    // Load valid destination bases (same initiative)
    const response = await bases.getCaravanTargets(selectedBaseDetail.value.id)
    caravanTargets.value = response.data.targets || []
    
    if (caravanTargets.value.length === 0) {
      alert('No valid caravan destinations. Bases must share the same initiative.')
      return
    }
    
    caravanMode.value = true
    caravanPath.value = [selectedBaseDetail.value.location]
    caravanIsSea.value = null  // Undecided until first hex is clicked
    caravanCost.value = { lumber: 2, oil: 0 }
    caravanError.value = null
    
    // Load valid next hexes (both land and sea options from origin)
    await loadCaravanNextHexes()
  } catch (e) {
    console.error('[Map] Failed to start caravan mode:', e.message)
  }
}

// Cancel caravan mode
const cancelCaravanMode = () => {
  caravanMode.value = false
  caravanTargets.value = []
  caravanPath.value = []
  caravanValidNextHexes.value = []
  caravanIsSea.value = null
  caravanError.value = null
}

// Calculate caravan cost based on path length and type
const getCaravanCost = (pathLength, isSea) => {
  // Costs from game config - land caravans cost lumber only, sea caravans cost lumber + oil
  if (pathLength <= 5) {
    return isSea ? { lumber: 2, oil: 2 } : { lumber: 2, oil: 0 }
  } else if (pathLength <= 10) {
    return isSea ? { lumber: 3, oil: 3 } : { lumber: 3, oil: 0 }
  } else {
    return isSea ? { lumber: 4, oil: 4 } : { lumber: 4, oil: 0 }
  }
}

// Load valid next hexes for current path
const loadCaravanNextHexes = async () => {
  if (!selectedBaseDetail.value || caravanPath.value.length === 0) return
  
  try {
    // If caravan type undecided (at origin), load both land and sea options
    // Otherwise, load only the appropriate type
    const response = await bases.getCaravanNextHexes(
      selectedBaseDetail.value.id,
      caravanPath.value,
      caravanIsSea.value,  // null = both, true = sea only, false = land only
      null  // No pre-selected destination
    )
    caravanValidNextHexes.value = response.data.validNextHexes || []
    caravanCost.value = response.data.currentCost || { lumber: 2, oil: 0 }
    caravanError.value = null
  } catch (e) {
    console.error('[Map] Failed to load next caravan hexes:', e.message)
    caravanValidNextHexes.value = []
    caravanError.value = e.response?.data?.detail || 'Failed to load next hexes'
  }
}

// Check if hex is a valid next step for caravan
const isValidCaravanHex = (hexId) => {
  // Check if in backend's valid next hexes
  if (caravanValidNextHexes.value.some(h => h.hex_id === hexId)) {
    return true
  }
  
  // FALLBACK for sea caravans: destination bases reachable via coastal hexside
  if (caravanIsSea.value === true && caravanPath.value.length > 0) {
    const currentPathEnd = caravanPath.value[caravanPath.value.length - 1]
    
    // Check if this hex contains a valid destination base
    const isDestination = caravanTargets.value.some(target => {
      const base = allBases.value.find(b => b.id === target.baseId)
      return base && base.location === hexId && !target.hasExistingCaravan
    })
    
    if (isDestination && areHexesAdjacentForCaravan(currentPathEnd, hexId)) {
      if (isCoastalHexside(currentPathEnd, hexId)) {
        return true
      }
    }
  }
  
  return false
}

// Check if hex contains a valid destination base
const isCaravanDestination = (hexId) => {
  // Check if this hex contains any of our valid destination bases
  return caravanTargets.value.some(target => {
    const base = allBases.value.find(b => b.id === target.baseId)
    return base && base.location === hexId && !target.hasExistingCaravan
  })
}

// Check if hex is in current caravan path
const isInCaravanPath = (hexId) => {
  return caravanPath.value.includes(hexId)
}

// Check if a hex is adjacent to another hex
const areHexesAdjacentForCaravan = (hex1, hex2) => {
  const diff = Math.abs(hex1 - hex2)
  return [1, 38, 39].includes(diff)
}

// Check if hexside between two hexes is coastal (for sea caravan endpoints)
const isCoastalHexside = (fromHexId, toHexId) => {
  const fromHex = hexLookup.value[fromHexId]
  if (!fromHex) return false
  
  const hexsideTerrain = getHexsideTerrain(fromHex, fromHexId, toHexId)
  // Coastal clear (K) and coastal forest (Q) are valid for sea caravan endpoints
  return hexsideTerrain === 'K' || hexsideTerrain === 'Q'
}

// Handle hex click in caravan mode
const handleCaravanHexClick = async (hexId) => {
  if (!caravanMode.value) return false
  
  // Get current path endpoint
  const currentPathEnd = caravanPath.value[caravanPath.value.length - 1]
  
  // Check if this is a valid next hex from the backend
  let nextHex = caravanValidNextHexes.value.find(h => h.hex_id === hexId)
  
  // FALLBACK: For sea caravans, also allow clicking on a destination base
  // if it's adjacent via a coastal hexside (K or Q)
  // This handles the case where the backend might not include the land hex in validNextHexes
  if (!nextHex && caravanIsSea.value === true) {
    // Check if this hex contains a valid destination base
    const isDestination = caravanTargets.value.some(target => {
      const base = allBases.value.find(b => b.id === target.baseId)
      return base && base.location === hexId && !target.hasExistingCaravan
    })
    
    if (isDestination && areHexesAdjacentForCaravan(currentPathEnd, hexId)) {
      // Check if the hexside is coastal (valid for sea caravan endpoint)
      if (isCoastalHexside(currentPathEnd, hexId)) {
        // Allow this as a valid destination
        nextHex = { hex_id: hexId, is_destination: true }
      }
    }
  }
  
  if (!nextHex) {
    caravanError.value = 'Invalid hex - must follow a valid caravan path'
    return false
  }
  
  // If this is the first step (path only has origin), determine land vs sea
  if (caravanPath.value.length === 1 && caravanIsSea.value === null) {
    // Determine type from terrain: if it's ocean or coastal, it's sea; otherwise land
    const hex = hexLookup.value[hexId]
    const isSeaHex = hex && (hex.terrain === 'O' || hex.terrain === 'K')
    caravanIsSea.value = isSeaHex
  }
  
  // Add to path
  caravanPath.value.push(hexId)
  
  // Check if this hex contains a valid destination base
  const destBase = caravanTargets.value.find(t => {
    const base = allBases.value.find(b => b.id === t.baseId)
    return base && base.location === hexId
  })
  
  if (destBase) {
    // Check if we can afford this length
    const pathLen = caravanPath.value.length
    if (pathLen > 15) {
      caravanError.value = 'Caravan path too long (max 15 hexes)'
      caravanPath.value.pop()
      return false
    }
    
    // Check resource requirements
    const isSea = caravanIsSea.value || false
    const cost = getCaravanCost(pathLen, isSea)
    const effective = selectedBaseDetail.value?.effectiveResources || selectedBaseDetail.value
    const availableLumber = effective?.lumber ?? 0
    const availableOil = effective?.oil ?? 0
    
    if (availableLumber < cost.lumber || availableOil < cost.oil) {
      caravanError.value = `Not enough resources. Need ${cost.lumber}🪵${cost.oil > 0 ? ` ${cost.oil}🛢️` : ''}, have ${availableLumber}🪵 ${availableOil}🛢️`
      caravanPath.value.pop()
      return false
    }
    
    // Check if destination already has a caravan (should be caught earlier but double-check)
    if (destBase.hasExistingCaravan) {
      caravanError.value = 'A caravan already exists to this destination'
      caravanPath.value.pop()
      return false
    }
    
    // Finalize the caravan
    await finalizeCaravanTo(destBase.baseId)
    return true
  }
  
  // Check path length limit
  if (caravanPath.value.length > 15) {
    caravanError.value = 'Caravan path too long (max 15 hexes)'
    caravanPath.value.pop()
    return false
  }
  
  // Load next valid hexes (now filtered by determined type)
  await loadCaravanNextHexes()
  return true
}

// Undo last hex in caravan path
const undoCaravanPathStep = async () => {
  if (caravanPath.value.length <= 1) return
  
  caravanPath.value.pop()
  
  // If we're back to just the origin, reset caravan type to undecided
  if (caravanPath.value.length === 1) {
    caravanIsSea.value = null
  }
  
  caravanError.value = null
  await loadCaravanNextHexes()
}

// Finalize and queue caravan to a specific destination
const finalizeCaravanTo = async (destBaseId) => {
  if (!selectedBaseDetail.value || !destBaseId) return
  
  try {
    await bases.queueCaravan(
      selectedBaseDetail.value.id,
      destBaseId,
      caravanPath.value,
      caravanIsSea.value || false
    )
    
    // Exit caravan mode
    cancelCaravanMode()
    
    // Refresh base orders
    const ordersResp = await bases.getOrders(selectedBaseDetail.value.id)
    baseOrders.value = ordersResp.data
    
    // Refresh expand targets (pending resources changed)
    await refreshExpandTargets()
    
  } catch (e) {
    console.error('[Map] Failed to queue caravan:', e.message)
    caravanError.value = e.response?.data?.detail || 'Failed to establish caravan'
    alert('Failed to establish caravan: ' + (e.response?.data?.detail || e.message))
  }
}

// Get cost tier label
const getCaravanCostTier = computed(() => {
  const len = caravanPath.value.length
  if (len <= 5) return '1-5'
  if (len <= 10) return '6-10'
  return '11-15'
})

// Check if path is at a cost threshold
const isAtCostThreshold = computed(() => {
  const len = caravanPath.value.length
  return len === 6 || len === 11
})

// Check if any destination is reachable from valid next hexes
const destinationReachable = computed(() => {
  return caravanValidNextHexes.value.some(h => {
    return caravanTargets.value.some(t => {
      const base = allBases.value.find(b => b.id === t.baseId)
      return base && base.location === h.hex_id && !t.hasExistingCaravan
    })
  })
})

// Get list of valid destinations that are reachable (in valid next hexes)
const validDestinationsReachable = computed(() => {
  return caravanTargets.value.filter(t => {
    if (t.hasExistingCaravan) return false
    const base = allBases.value.find(b => b.id === t.baseId)
    if (!base) return false
    return caravanValidNextHexes.value.some(h => h.hex_id === base.location)
  })
})

// ==================== Send Resources State ====================
const sendMode = ref(false)                       // Whether we're in send resources mode
const sendDestinations = ref([])                  // Valid destinations for sending
const selectedSendDest = ref(null)                // Selected destination
const sendAmounts = ref({ gold: 0, lumber: 0, oil: 0 })  // Amounts to send
const sendAvailableResources = ref({ gold: 0, lumber: 0, oil: 0 })  // Available to send

// Check if base can send resources
const canSendResources = computed(() => {
  if (!selectedBaseDetail.value) return false
  if (selectedBaseDetail.value.inCombat) return false
  const actionsRemaining = (selectedBaseDetail.value.actions || selectedBaseDetail.value.tier) - (baseOrders.value?.orders?.length || 0)
  if (actionsRemaining <= 0) return false
  // Check if already queued
  if (baseOrders.value?.orders?.some(o => o.type === 'send_resources')) return false
  return true
})

// Enter send resources mode
const startSendMode = async () => {
  if (!selectedBaseDetail.value) return
  
  try {
    const response = await bases.getSendDestinations(selectedBaseDetail.value.id)
    
    if (!response.data.canSend) {
      alert('Cannot send resources: ' + response.data.reasons.join(', '))
      return
    }
    
    sendDestinations.value = response.data.destinations || []
    sendAvailableResources.value = response.data.availableResources || { gold: 0, lumber: 0, oil: 0 }
    sendMode.value = true
    selectedSendDest.value = null
    sendAmounts.value = { gold: 0, lumber: 0, oil: 0 }
  } catch (e) {
    console.error('[Map] Failed to start send mode:', e.message)
  }
}

// Cancel send mode
const cancelSendMode = () => {
  sendMode.value = false
  sendDestinations.value = []
  selectedSendDest.value = null
  sendAmounts.value = { gold: 0, lumber: 0, oil: 0 }
}

// Select send destination
const selectSendDestination = (dest) => {
  selectedSendDest.value = dest
  // Default to sending zero - player chooses amounts
  sendAmounts.value = { gold: 0, lumber: 0, oil: 0 }
}

// Update send amount for a resource
const updateSendAmount = (resource, value) => {
  const max = sendAvailableResources.value[resource] || 0
  sendAmounts.value[resource] = Math.max(0, Math.min(max, parseInt(value) || 0))
}

// Total resources being sent
const totalSending = computed(() => {
  return sendAmounts.value.gold + sendAmounts.value.lumber + sendAmounts.value.oil
})

// Confirm send resources
const confirmSendResources = async () => {
  if (!selectedBaseDetail.value || !selectedSendDest.value) return
  if (totalSending.value === 0) {
    alert('Must send at least one resource')
    return
  }
  
  try {
    await bases.queueSendResources(
      selectedBaseDetail.value.id,
      selectedSendDest.value.base_id,
      sendAmounts.value.gold,
      sendAmounts.value.lumber,
      sendAmounts.value.oil
    )
    
    // Exit send mode
    cancelSendMode()
    
    // Refresh base orders
    const ordersResp = await bases.getOrders(selectedBaseDetail.value.id)
    baseOrders.value = ordersResp.data
    
    // Refresh expand targets (pending resources changed)
    await refreshExpandTargets()
    
  } catch (e) {
    console.error('[Map] Failed to queue send resources:', e.message)
    alert('Failed to send resources: ' + (e.response?.data?.detail || e.message))
  }
}

// Get unit type name
const getUnitTypeLabel = (typeNum) => {
  const types = { 0: 'Ground', 1: 'Air', 2: 'Sea' }
  return types[typeNum] || 'Unknown'
}

// Get category name  
const getCategoryLabel = (catNum) => {
  const cats = { 0: 'Exterior Siege', 1: 'Ranged', 2: 'Expert', 3: 'Melee', 4: 'Interior Siege', 5: 'No Fire' }
  return cats[catNum] || 'Unknown'
}

// Get unit image path
const getBuildUnitImage = (unitName) => {
  const cleanedName = unitName.toLowerCase().replace(/ /g, '')
  return `/images/Units/${cleanedName}.png`
}

// Format order type for display (build_unit -> Build Unit)
const formatOrderType = (type) => {
  if (!type) return ''
  return type
    .split('_')
    .map(word => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ')
}

// Check if can issue base actions (admin or owning faction, AND it's their turn)
const canIssueBaseActions = (base) => {
  if (!base) return false
  // Check permission first (admin or owning faction)
  const hasPermission = (selectedFactionId === null || selectedFactionId?.value === null) 
    || (base.factionId === (selectedFactionId?.value ?? selectedFactionId))
  
  if (!hasPermission) return false
  
  // Check if it's this faction's turn (initiative check)
  return canFactionSubmitOrders(base.factionId)
}

// Check if we CAN VIEW base actions (even if we can't issue them)
// This is used to show the actions panel (but with disabled buttons)
const canViewBaseActions = (base) => {
  if (!base) return false
  // Admin/omniscient mode (null = all factions visible)
  if (selectedFactionId === null || selectedFactionId?.value === null) return true
  // Owning faction
  const factionIdValue = selectedFactionId?.value ?? selectedFactionId
  return base.factionId === factionIdValue
}

// Check if base is viewable but orders are blocked due to initiative
const isBaseOrdersBlockedByInitiative = (base) => {
  if (!base) return false
  return canViewBaseActions(base) && !canFactionSubmitOrders(base.factionId)
}

// Check if current viewer can see base resources (admin/omniscient or owning faction)
const canViewBaseResources = (base) => {
  if (!base) return false
  // Admin/omniscient mode (null = all factions visible)
  if (selectedFactionId === null || selectedFactionId?.value === null) return true
  // Owning faction
  const viewingAs = selectedFactionId?.value ?? selectedFactionId
  return base.factionId === viewingAs
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

// Get the center point of a hex (for drawing lines)
const getHexCenter = (hexId) => {
  const pos = getHexPosition(hexId)
  return {
    x: pos.x + HEX_SIZE,
    y: pos.y + HEX_SIZE
  }
}

// Get faction color (hex string)
const getFactionColor = (factionId) => {
  return factionData.value[factionId]?.color || '#888888'
}

// Computed: lines from selected base to its expansions
const selectedBaseExpansionLines = computed(() => {
  if (!selectedBaseDetail.value || selectedBaseExpansions.value.length === 0) {
    return []
  }
  
  const baseCenter = getHexCenter(selectedBaseDetail.value.location)
  const factionColor = getFactionColor(selectedBaseDetail.value.factionId)
  
  return selectedBaseExpansions.value.map(exp => {
    const expCenter = getHexCenter(exp.location)
    return {
      x1: baseCenter.x,
      y1: baseCenter.y,
      x2: expCenter.x,
      y2: expCenter.y,
      color: factionColor
    }
  })
})

// Get SVG polyline points for a caravan route
const getCaravanRoutePoints = (caravan) => {
  if (!caravan.path || caravan.path.length === 0) return ''
  
  return caravan.path.map(hexId => {
    const center = getHexCenter(hexId)
    return `${center.x},${center.y}`
  }).join(' ')
}

// Get SVG polyline points for the caravan path being traced
const getCaravanPathPoints = () => {
  if (caravanPath.value.length === 0) return ''
  
  return caravanPath.value.map(hexId => {
    const center = getHexCenter(hexId)
    return `${center.x},${center.y}`
  }).join(' ')
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

// Get hexside terrain name - empty string means Clear
const getHexsideTerrainName = (code) => {
  if (!code || code === '' || code === 'C') return 'Clear'
  const names = {
    'F': 'Forest',
    'M': 'Mountain',
    'S': 'Swamp',
    'R': 'River',
    'W': 'Fort',
    'O': 'Ocean',
    'K': 'Coastal',
    'I': 'Impass',
    'N': 'C-Moun',    // Coastal Mountain
    'Q': 'C-Forest',  // Coastal Forest
  }
  return names[code] || code
}

// Get all 6 hexside terrains for a hex (including road info)
const getHexsideTerrains = (hex) => {
  if (!hex) return []
  return [
    { dir: 'N', terrain: hex.north?.terrain || '', name: getHexsideTerrainName(hex.north?.terrain), hasRoad: !!hex.north?.road },
    { dir: 'NE', terrain: hex.northeast?.terrain || '', name: getHexsideTerrainName(hex.northeast?.terrain), hasRoad: !!hex.northeast?.road },
    { dir: 'SE', terrain: hex.southeast?.terrain || '', name: getHexsideTerrainName(hex.southeast?.terrain), hasRoad: !!hex.southeast?.road },
    { dir: 'S', terrain: hex.south?.terrain || '', name: getHexsideTerrainName(hex.south?.terrain), hasRoad: !!hex.south?.road },
    { dir: 'SW', terrain: hex.southwest?.terrain || '', name: getHexsideTerrainName(hex.southwest?.terrain), hasRoad: !!hex.southwest?.road },
    { dir: 'NW', terrain: hex.northwest?.terrain || '', name: getHexsideTerrainName(hex.northwest?.terrain), hasRoad: !!hex.northwest?.road },
  ]
}

const getBaseAtHex = (hexId) => {
  return allBases.value.find(b => b.location === hexId || b.hexId === hexId)
}

// Get units at a specific hex from the cached data
const getUnitsAtHex = (hexId) => {
  return unitsByHex.value[hexId] || []
}

// Check if hex has combat
const isCombatHex = (hexId) => {
  return combatHexIds.value.has(hexId)
}

// Get combat data for a hex
const getCombatAtHex = (hexId) => {
  return activeCombats.value.find(c => c.hexId === hexId)
}

// ==================== Hexside Control Visualization ====================

// Get hexagon corner coordinates for hexside lines
// For flat-top hex centered at (HEX_SIZE, HEX_SIZE)
const getHexCorners = () => {
  const corners = []
  for (let i = 0; i < 6; i++) {
    const angle = (Math.PI / 3) * i  // 0, 60, 120, 180, 240, 300 degrees
    corners.push({
      x: HEX_SIZE * Math.cos(angle) + HEX_SIZE,
      y: HEX_SIZE * Math.sin(angle) + HEX_SIZE
    })
  }
  return corners
}

const hexCorners = getHexCorners()

// Map direction names to corner indices for line endpoints
// For flat-top hex: corner 0 = right (3 o'clock), going counter-clockwise
const hexsideCornerMap = {
  'N':  [4, 5],  // top edge: upper-left to upper-right
  'NE': [5, 0],  // upper-right to right
  'SE': [0, 1],  // right to lower-right
  'S':  [1, 2],  // bottom edge: lower-right to lower-left
  'SW': [2, 3],  // lower-left to left
  'NW': [3, 4],  // left to upper-left
}

// Get initiative color for hexside control lines
// Derived from the faction with the HIGHEST faction ID within that initiative
const getInitiativeColor = (initiative) => {
  // Find all factions with this initiative
  const factionsInInit = Object.values(factionData.value).filter(f => f.initiative === initiative)
  
  if (factionsInInit.length === 0) {
    return '#888888' // Fallback gray if no factions found
  }
  
  // Get the faction with the highest ID
  const highestIdFaction = factionsInInit.reduce((highest, current) => {
    return current.id > highest.id ? current : highest
  })
  
  return highestIdFaction.color || '#888888'
}

// Get hexside control for a specific direction
const getHexsideControlForDir = (hexId, direction) => {
  const combat = getCombatAtHex(hexId)
  if (!combat || !combat.hexsideControl) return -1
  return combat.hexsideControl[direction] ?? -1
}

// Get hexside control data for a combat hex
const getHexsideControlLines = (hexId) => {
  const combat = getCombatAtHex(hexId)
  if (!combat || !combat.hexsideControl) return []
  
  const lines = []
  for (const [direction, initiative] of Object.entries(combat.hexsideControl)) {
    const cornerIndices = hexsideCornerMap[direction]
    if (!cornerIndices) continue
    
    const [start, end] = cornerIndices
    lines.push({
      direction,
      initiative,
      color: getInitiativeColor(initiative),
      x1: hexCorners[start].x,
      y1: hexCorners[start].y,
      x2: hexCorners[end].x,
      y2: hexCorners[end].y,
    })
  }
  return lines
}

// Get faction name from ID
const getFactionName = (factionId) => {
  return factionData.value[factionId]?.name || 'Unknown'
}

// Format base name for display (handle long names that need line breaks)
const formatBaseName = (name) => {
  // Hardcoded line breaks for specific bases
  if (name === 'Featherbeard Garrison') {
    return ['Featherbeard', 'Garrison']
  }
  // Default: single line
  return [name]
}

// Convert unit type number to readable string
const getUnitTypeName = (unitType) => {
  const types = { 0: 'Ground', 1: 'Air', 2: 'Sea' }
  return types[unitType] ?? 'Unknown'
}

// Get tier label for bases (alignment-specific)
const getTierLabel = (tier, factionId) => {
  // isHordeFaction expects numeric faction ID, not name
  if (isHordeFaction(factionId)) {
    const labels = { 1: 'Great Hall', 2: 'Stronghold', 3: 'Fortress' }
    return labels[tier] || ''
  } else {
    const labels = { 1: 'Town Hall', 2: 'Keep', 3: 'Castle' }
    return labels[tier] || ''
  }
}

// Calculate HP bar width safely
const getHpBarWidth = (unit, size) => {
  const hp = unit?.hp ?? 1
  const maxHp = unit?.maxHp ?? 1
  if (maxHp <= 0) return size
  const ratio = Math.max(0, Math.min(1, hp / maxHp))
  return Math.round(size * ratio)
}

// Get HP bar color
const getHpBarColor = (unit) => {
  const hp = unit?.hp ?? 0
  const maxHp = unit?.maxHp ?? 1
  const ratio = maxHp > 0 ? hp / maxHp : 1
  if (ratio > 0.5) return '#00cc00'
  if (ratio > 0.25) return '#cccc00'
  return '#cc0000'
}

// Get unit positions within a hex (Alliance at top expanding DOWN, Horde at bottom expanding UP)
const getUnitPositionsAtHex = (hexId) => {
  const units = getUnitsAtHex(hexId)
  if (units.length === 0) return []
  
  const positions = []
  const allianceUnits = units.filter(u => isAllianceFaction(u.factionId))
  const hordeUnits = units.filter(u => isHordeFaction(u.factionId))
  
  // Dynamic sizing based on how crowded the hex is
  const total = units.length
  let UNIT_SIZE, SPACING, MAX_PER_ROW
  
  if (total === 1) {
    UNIT_SIZE = 44; SPACING = 46; MAX_PER_ROW = 1
  } else if (total === 2) {
    UNIT_SIZE = 36; SPACING = 38; MAX_PER_ROW = 2
  } else if (total <= 4) {
    UNIT_SIZE = 30; SPACING = 32; MAX_PER_ROW = 2
  } else if (total <= 6) {
    UNIT_SIZE = 26; SPACING = 28; MAX_PER_ROW = 3
  } else if (total <= 9) {
    UNIT_SIZE = 22; SPACING = 24; MAX_PER_ROW = 3
  } else {
    UNIT_SIZE = 18; SPACING = 20; MAX_PER_ROW = 4
  }
  
  // Alliance units: start at TOP of hex, expand DOWNWARD toward center
  // Position scales with icon size to stay inside hex
  const allianceStartY = 20 + UNIT_SIZE / 2
  let row = 0
  for (let i = 0; i < allianceUnits.length; i++) {
    const col = i % MAX_PER_ROW
    if (i > 0 && col === 0) row++
    const rowCount = Math.min(allianceUnits.length - row * MAX_PER_ROW, MAX_PER_ROW)
    const startX = HEX_SIZE - (rowCount * SPACING) / 2 + SPACING / 2
    
    positions.push({
      unit: allianceUnits[i],
      x: startX + col * SPACING,
      y: allianceStartY + row * SPACING,  // Expand downward
      size: UNIT_SIZE
    })
  }
  
  // Horde units: start at BOTTOM of hex, expand UPWARD toward center
  const hordeStartY = HEX_SIZE * 2 - 20 - UNIT_SIZE / 2
  row = 0
  for (let i = 0; i < hordeUnits.length; i++) {
    const col = i % MAX_PER_ROW
    if (i > 0 && col === 0) row++
    const rowCount = Math.min(hordeUnits.length - row * MAX_PER_ROW, MAX_PER_ROW)
    const startX = HEX_SIZE - (rowCount * SPACING) / 2 + SPACING / 2
    
    positions.push({
      unit: hordeUnits[i],
      x: startX + col * SPACING,
      y: hordeStartY - row * SPACING,  // Expand upward (subtract)
      size: UNIT_SIZE
    })
  }
  
  return positions
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

onMounted(() => {
  loadMapData()
  // Add WASD keyboard listeners
  window.addEventListener('keydown', handleKeyDown)
  window.addEventListener('keyup', handleKeyUp)
})

onUnmounted(() => {
  // Clean up keyboard listeners
  window.removeEventListener('keydown', handleKeyDown)
  window.removeEventListener('keyup', handleKeyUp)
  if (scrollAnimationId) {
    cancelAnimationFrame(scrollAnimationId)
  }
  // Close the build modal if it's open (Teleport cleanup)
  buildModalOpen.value = false
})
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
        <span class="zoom-hint">Scroll to zoom • WASD to pan</span>
      </div>
      
      <!-- Map Display Toggles -->
      <div class="map-toggles">
        <button 
          class="toggle-btn" 
          :class="{ active: showCaravans }"
          @click="toggleCaravanDisplay"
          title="Toggle caravan route display"
        >
          🛤️ {{ showCaravans ? 'Hide' : 'Show' }} Caravans
        </button>
      </div>
      
      <!-- Debug Mode Indicators -->
      <div v-if="debugConfig.infinite_resources" class="debug-indicator" title="Infinite resources enabled - all base actions are free">
        💎 Infinite Resources
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
              <!-- Base to Expansion Connection Lines -->
              <g v-if="selectedBaseDetail && selectedBaseExpansionLines.length > 0" class="expansion-connection-lines">
                <line
                  v-for="(line, idx) in selectedBaseExpansionLines"
                  :key="'exp-line-' + idx"
                  :x1="line.x1"
                  :y1="line.y1"
                  :x2="line.x2"
                  :y2="line.y2"
                  :stroke="line.color"
                  stroke-width="3"
                  stroke-opacity="0.7"
                  stroke-dasharray="8,4"
                  class="expansion-line"
                />
              </g>
              
              <!-- Existing Caravan Routes -->
              <g v-if="showCaravans && allCaravans.length > 0" class="caravan-routes">
                <template v-for="caravan in allCaravans" :key="'caravan-' + caravan.id">
                  <polyline
                    :points="getCaravanRoutePoints(caravan)"
                    fill="none"
                    :stroke="getCaravanColor(caravan)"
                    stroke-width="8"
                    stroke-opacity="0.85"
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    :stroke-dasharray="caravan.terrainType === 'sea' ? '16,8' : ''"
                    class="caravan-route-line"
                  />
                  <!-- Small markers at each hex in the caravan path -->
                  <circle
                    v-for="(hexId, idx) in caravan.path.slice(1, -1)"
                    :key="'caravan-marker-' + caravan.id + '-' + idx"
                    :cx="getHexPosition(hexId).x + HEX_SIZE"
                    :cy="getHexPosition(hexId).y + HEX_SIZE"
                    r="5"
                    :fill="getCaravanColor(caravan)"
                    fill-opacity="0.9"
                    class="caravan-marker"
                  />
                </template>
              </g>
              
              <!-- Caravan Path Being Traced -->
              <g v-if="caravanMode && caravanPath.length > 1" class="caravan-path-trace">
                <polyline
                  :points="getCaravanPathPoints()"
                  fill="none"
                  :stroke="caravanIsSea ? '#66aadd' : '#CD853F'"
                  stroke-width="5"
                  stroke-opacity="0.9"
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  class="caravan-trace-line"
                />
              </g>
              
              <!-- Fast Travel Path Lines -->
              <g v-if="fastTravelMode && fastTravelPath.length > 0" class="fast-travel-path-lines">
                <!-- Line from unit location to first path hex -->
                <line
                  v-if="fastTravelUnit"
                  :x1="getHexPosition(fastTravelUnit.location).x + HEX_SIZE"
                  :y1="getHexPosition(fastTravelUnit.location).y + HEX_SIZE"
                  :x2="getHexPosition(fastTravelPath[0]).x + HEX_SIZE"
                  :y2="getHexPosition(fastTravelPath[0]).y + HEX_SIZE"
                  :stroke="fastTravelIsNaval ? '#66ccff' : '#ffaa00'"
                  stroke-width="5"
                  stroke-dasharray="8,4"
                  class="fast-travel-line"
                />
                <!-- Lines between path hexes -->
                <line
                  v-for="(hexId, i) in fastTravelPath.slice(1)"
                  :key="`ft-line-${i}`"
                  :x1="getHexPosition(fastTravelPath[i]).x + HEX_SIZE"
                  :y1="getHexPosition(fastTravelPath[i]).y + HEX_SIZE"
                  :x2="getHexPosition(hexId).x + HEX_SIZE"
                  :y2="getHexPosition(hexId).y + HEX_SIZE"
                  :stroke="fastTravelIsNaval ? '#66ccff' : '#ffaa00'"
                  stroke-width="5"
                  stroke-dasharray="8,4"
                  class="fast-travel-line"
                />
              </g>
              
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
                  'unit-origin': movementMode && selectedUnit?.location === hex.id,
                  'expand-target': expandMode && isExpandableTarget(hex.id),
                  'caravan-path': caravanMode && isInCaravanPath(hex.id),
                  'caravan-valid': caravanMode && isValidCaravanHex(hex.id),
                  'caravan-dest': caravanMode && isCaravanDestination(hex.id),
                  'rangedfire-target': rangedfireMode && isValidRangedfireTarget(hex.id),
                  'rangedfire-origin': rangedfireMode && rangedfireUnit?.location === hex.id,
                  'fast-travel-path': fastTravelMode && isInFastTravelPath(hex.id),
                  'fast-travel-valid': fastTravelMode && isValidFastTravelHex(hex.id),
                  'fast-travel-origin': fastTravelMode && fastTravelUnit?.location === hex.id
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
                
                <!-- Expand target highlight -->
                <polygon
                  v-if="expandMode && isExpandableTarget(hex.id)"
                  :points="hexPoints"
                  :fill="getExpandTarget(hex.id)?.canAfford ? 'rgba(255, 200, 0, 0.35)' : 'rgba(255, 100, 100, 0.25)'"
                  :stroke="getExpandTarget(hex.id)?.canAfford ? '#ffcc00' : '#ff6666'"
                  stroke-width="4"
                  class="expand-highlight"
                />
                
                <!-- Caravan path highlight (hexes already in path) -->
                <polygon
                  v-if="caravanMode && isInCaravanPath(hex.id)"
                  :points="hexPoints"
                  fill="rgba(139, 69, 19, 0.4)"
                  stroke="#8B4513"
                  stroke-width="3"
                  class="caravan-path-highlight"
                />
                
                <!-- Caravan valid next hex highlight -->
                <polygon
                  v-if="caravanMode && isValidCaravanHex(hex.id) && !isInCaravanPath(hex.id)"
                  :points="hexPoints"
                  :fill="isCaravanDestination(hex.id) ? 'rgba(0, 255, 100, 0.35)' : 'rgba(255, 200, 100, 0.25)'"
                  :stroke="isCaravanDestination(hex.id) ? '#00ff64' : '#ffcc66'"
                  stroke-width="3"
                  class="caravan-valid-highlight"
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
                
                <!-- Ranged fire target highlight -->
                <polygon
                  v-if="rangedfireMode && isValidRangedfireTarget(hex.id)"
                  :points="hexPoints"
                  fill="rgba(255, 100, 50, 0.4)"
                  stroke="#ff4500"
                  stroke-width="4"
                  class="rangedfire-target-highlight"
                />
                
                <!-- Ranged fire origin highlight -->
                <polygon
                  v-if="rangedfireMode && rangedfireUnit?.location === hex.id"
                  :points="hexPoints"
                  fill="rgba(255, 165, 0, 0.35)"
                  stroke="#ffa500"
                  stroke-width="3"
                  class="rangedfire-origin-highlight"
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
                
                <!-- Combat hexside control lines -->
                <g v-if="isCombatHex(hex.id) && isHexVisible(hex.id)" class="combat-hexside-control">
                  <!-- Combat indicator glow BEHIND the hexside lines -->
                  <polygon
                    :points="hexPoints"
                    fill="none"
                    stroke="rgba(255, 68, 68, 0.4)"
                    stroke-width="8"
                    class="combat-glow"
                  />
                  <!-- Draw each hexside with the controlling initiative's color (on top) -->
                  <line
                    v-for="line in getHexsideControlLines(hex.id)"
                    :key="`${hex.id}-${line.direction}`"
                    :x1="line.x1"
                    :y1="line.y1"
                    :x2="line.x2"
                    :y2="line.y2"
                    :stroke="line.color"
                    stroke-width="6"
                    stroke-linecap="round"
                    class="hexside-control-line"
                  />
                </g>
                
                <!-- Expansion (farm/mill/rig - only show if visible and no base in hex) -->
                <g v-if="getExpansionAtHex(hex.id) && isHexVisible(hex.id) && !getBaseAtHex(hex.id)" class="expansion-group">
                  <image
                    :href="getExpansionImage(getExpansionAtHex(hex.id).type, getExpansionFactionId(hex.id))"
                    :x="HEX_SIZE - 60"
                    :y="HEX_SIZE - 50"
                    width="120"
                    height="120"
                    class="expansion-building"
                  />
                </g>
                
                <!-- Base with banner (only show if visible) -->
                <g v-if="getBaseAtHex(hex.id) && isHexVisible(hex.id)" class="base-group clickable-base">
                  <!-- Faction Banner (behind and to the right of base) - hide for ruins -->
                  <image
                    v-if="getBaseAtHex(hex.id).tier > 0"
                    :href="getFactionBanner(getFactionName(getBaseAtHex(hex.id).factionId))"
                    :x="HEX_SIZE * 0.2 + 80"
                    :y="HEX_SIZE * 0.4 - 20"
                    width="56"
                    height="80"
                    class="faction-banner"
                  />
                  <!-- Base Building or Ruins (80% of 144 = 115) - CLICKABLE -->
                  <image
                    :href="getBaseAtHex(hex.id).tier === 0 ? getRuinsImage() : getBaseImage(getBaseAtHex(hex.id).factionId, getBaseAtHex(hex.id).tier || 1)"
                    :x="HEX_SIZE - 58"
                    :y="HEX_SIZE - 48"
                    width="115"
                    height="115"
                    class="base-building clickable"
                    :class="{ 'ruins': getBaseAtHex(hex.id).tier === 0 }"
                    @click.stop="selectBaseFromMap(getBaseAtHex(hex.id))"
                  />
                  <!-- Base Name (below bottom hex border) - ALSO CLICKABLE -->
                  <text
                    :x="HEX_SIZE"
                    :y="HEX_SIZE * 1.85 + 15"
                    text-anchor="middle"
                    :fill="getBaseAtHex(hex.id).tier === 0 ? '#888888' : '#FFD700'"
                    stroke="#000"
                    stroke-width="3"
                    paint-order="stroke"
                    font-size="36"
                    font-weight="bold"
                    class="base-name clickable"
                    @click.stop="selectBaseFromMap(getBaseAtHex(hex.id))"
                  >
                    <tspan 
                      v-for="(line, idx) in formatBaseName(getBaseAtHex(hex.id).tier === 0 ? 'Ruins of ' + getBaseAtHex(hex.id).name : getBaseAtHex(hex.id).name)" 
                      :key="idx"
                      :x="HEX_SIZE"
                      :dy="idx === 0 ? 0 : '1.1em'"
                    >{{ line }}</tspan>
                  </text>
                </g>
                
                <!-- Units at hex (only show if visible) -->
                <g v-if="isHexVisible(hex.id) && getUnitsAtHex(hex.id).length > 0" class="units-group">
                  <g 
                    v-for="pos in getUnitPositionsAtHex(hex.id)" 
                    :key="pos.unit.id"
                    :transform="`translate(${pos.x - pos.size/2}, ${pos.y - pos.size/2})`"
                    class="unit-icon"
                    @click.stop="selectUnitFromMap(pos.unit)"
                  >
                    <!-- Faction background -->
                    <image
                      :href="getFactionBackground(getFactionName(pos.unit.factionId))"
                      x="0"
                      y="0"
                      :width="pos.size"
                      :height="pos.size"
                      class="unit-background"
                    />
                    <!-- Unit sprite -->
                    <image
                      :href="getUnitImage(pos.unit.name)"
                      x="0"
                      y="0"
                      :width="pos.size"
                      :height="pos.size"
                      class="unit-sprite"
                    />
                    <!-- HP bar background -->
                    <rect
                      x="0"
                      :y="pos.size - 3"
                      :width="pos.size"
                      height="3"
                      fill="#333"
                    />
                    <!-- HP bar fill -->
                    <rect
                      x="0"
                      :y="pos.size - 3"
                      :width="getHpBarWidth(pos.unit, pos.size)"
                      height="3"
                      :fill="getHpBarColor(pos.unit)"
                    />
                  </g>
                </g>
              </g>
            </svg>
          </div>
        </div>
      </div>

      <!-- Info Panel - shows Hex Info, Unit Info, or Base Info depending on selection -->
      <div class="info-panel card" v-if="selectedHex || selectedUnitDetail || selectedBaseDetail">
        
        <!-- UNIT INFO PANEL -->
        <template v-if="selectedUnitDetail">
          <div class="card-header">
            <h3 class="card-title">{{ selectedUnitDetail.name }}</h3>
            <span class="unit-id-label">Unit ID: {{ selectedUnitDetail.id }}</span>
            <button class="close-btn" @click="closeUnitDetail">×</button>
          </div>
          
          <!-- Large Unit Portrait -->
          <div class="unit-portrait">
            <div class="portrait-frame">
              <img 
                :src="getFactionBackground(getFactionName(selectedUnitDetail.factionId))" 
                class="portrait-bg"
                alt=""
              />
              <img 
                :src="getUnitImage(selectedUnitDetail.name)" 
                class="portrait-unit"
                alt=""
              />
            </div>
          </div>
          <div class="portrait-faction">{{ getFactionName(selectedUnitDetail.factionId) }}</div>
          
          <!-- Unit Stats -->
          <div class="unit-stats">
            <div class="stat-row">
              <span class="stat-label">HP</span>
              <span class="stat-value">
                <span class="hp-current">{{ selectedUnitDetail.hp }}</span>
                <span class="hp-separator">/</span>
                <span class="hp-max highlight">{{ selectedUnitDetail.maxHp }}</span>
              </span>
              <div class="hp-bar-large">
                <div 
                  class="hp-bar-fill" 
                  :style="{ width: (selectedUnitDetail.hp / selectedUnitDetail.maxHp * 100) + '%' }"
                  :class="{ 
                    'hp-high': selectedUnitDetail.hp > selectedUnitDetail.maxHp * 0.5,
                    'hp-mid': selectedUnitDetail.hp <= selectedUnitDetail.maxHp * 0.5 && selectedUnitDetail.hp > selectedUnitDetail.maxHp * 0.25,
                    'hp-low': selectedUnitDetail.hp <= selectedUnitDetail.maxHp * 0.25
                  }"
                ></div>
              </div>
            </div>
            
            <div class="stat-row">
              <span class="stat-label">Combat</span>
              <span class="stat-value highlight">{{ selectedUnitDetail.combat || '?' }}</span>
            </div>
            
            <div class="stat-row">
              <span class="stat-label">Category</span>
              <span class="stat-value highlight">{{ selectedUnitDetail.category || '?' }}</span>
            </div>
            
            <div class="stat-row">
              <span class="stat-label">Type</span>
              <span class="stat-value highlight">{{ getUnitTypeName(selectedUnitDetail.unitType) }}</span>
            </div>
            
            <div class="stat-row">
              <span class="stat-label">Movement</span>
              <span class="stat-value highlight">
                {{ selectedUnitDetail.movementRemaining ?? selectedUnitDetail.movement ?? '?' }} 
                / {{ selectedUnitDetail.movementMax ?? '?' }}
              </span>
            </div>
            
            <div class="stat-row">
              <span class="stat-label">Tier</span>
              <span class="stat-value highlight">{{ selectedUnitDetail.tier ?? 0 }}</span>
            </div>
            
            <div class="stat-row">
              <span class="stat-label">Light Armor</span>
              <span class="stat-value highlight">{{ selectedUnitDetail.lightArmorCurrent ?? selectedUnitDetail.lightArmor ?? 0 }}</span>
            </div>
            
            <div class="stat-row">
              <span class="stat-label">Heavy Armor</span>
              <span class="stat-value highlight">{{ selectedUnitDetail.heavyArmor ?? 0 }}</span>
            </div>
            
            <div class="stat-row">
              <span class="stat-label">Natural Armor</span>
              <span class="stat-value highlight">{{ selectedUnitDetail.naturalArmor ?? 0 }}</span>
            </div>
          </div>
          
          <!-- Order Messages -->
          <div v-if="orderMessage" class="order-message success">{{ orderMessage }}</div>
          <div v-if="orderError" class="order-message error">{{ orderError }}</div>
          
          <!-- Unit Orders -->
          <div class="unit-orders">
            <h4>Orders</h4>
            <div class="order-buttons">
              <!-- Movement Order Button -->
              <button 
                v-if="canOrderUnit(selectedUnitDetail) && !movementMode && !rangedfireMode && !hasMovementOrder(selectedUnitDetail) && !hasRangedfireOrder(selectedUnitDetail) && !hasFastTravelOrder(selectedUnitDetail)"
                class="btn btn-gold"
                @click="startMovementOrder(selectedUnitDetail)"
              >
                🥾 Move
              </button>
              <button 
                v-else-if="canOrderUnit(selectedUnitDetail) && !movementMode && !rangedfireMode && hasMovementOrder(selectedUnitDetail)"
                class="btn btn-cancel"
                @click="cancelUnitMovementOrder(selectedUnitDetail)"
              >
                ❌ Cancel Move
              </button>
              
              <!-- Fast Travel Button (March for land, Full Sail for naval) -->
              <button 
                v-if="canOrderUnit(selectedUnitDetail) && canFastTravel(selectedUnitDetail) && !movementMode && !rangedfireMode && !fastTravelMode && !hasMovementOrder(selectedUnitDetail) && !hasRangedfireOrder(selectedUnitDetail) && !hasFastTravelOrder(selectedUnitDetail)"
                class="btn btn-fast-travel"
                @click="startFastTravelMode(selectedUnitDetail)"
              >
                {{ getFastTravelLabel(selectedUnitDetail) }}
              </button>
              <button 
                v-else-if="canOrderUnit(selectedUnitDetail) && !movementMode && !rangedfireMode && !fastTravelMode && hasFastTravelOrder(selectedUnitDetail)"
                class="btn btn-cancel"
                @click="cancelFastTravelOrder(selectedUnitDetail)"
              >
                ❌ Cancel {{ getFastTravelLabel(selectedUnitDetail) }}
              </button>
              
              <!-- Ranged Fire Order Button (only for INTERIOR_SIEGE units) -->
              <button 
                v-if="canOrderUnit(selectedUnitDetail) && canRangedfire(selectedUnitDetail) && !movementMode && !rangedfireMode && !fastTravelMode && !hasRangedfireOrder(selectedUnitDetail) && !hasMovementOrder(selectedUnitDetail) && !hasFastTravelOrder(selectedUnitDetail)"
                class="btn btn-siege"
                @click="startRangedfireOrder(selectedUnitDetail)"
              >
                🎯 Ranged Fire
              </button>
              <button 
                v-else-if="canOrderUnit(selectedUnitDetail) && canRangedfire(selectedUnitDetail) && !movementMode && !rangedfireMode && !fastTravelMode && hasRangedfireOrder(selectedUnitDetail)"
                class="btn btn-cancel"
                @click="cancelUnitRangedfireOrder(selectedUnitDetail)"
              >
                ❌ Cancel Fire
              </button>
              
              <div 
                v-else-if="isOwnUnit(selectedUnitDetail) && !canOrderUnit(selectedUnitDetail)"
                class="not-your-turn-notice"
              >
                Not this faction's turn
              </div>
              <div 
                v-else-if="!isOwnUnit(selectedUnitDetail)"
                class="not-own-unit-notice"
              >
                Not your unit
              </div>
            </div>
            
            <!-- Show current movement order if exists -->
            <div v-if="hasMovementOrder(selectedUnitDetail)" class="current-order">
              <span class="order-label">📍 Moving to:</span>
              <span class="order-value">Hex {{ getMovementOrder(selectedUnitDetail)?.path?.slice(-1)[0] }}</span>
            </div>
            
            <!-- Show current rangedfire order if exists -->
            <div v-if="hasRangedfireOrder(selectedUnitDetail)" class="current-order rangedfire-order">
              <span class="order-label">🎯 Firing at:</span>
              <span class="order-value">Hex {{ getRangedfireOrder(selectedUnitDetail)?.targetHex }}</span>
            </div>
            
            <!-- Show current fast travel order if exists -->
            <div v-if="hasFastTravelOrder(selectedUnitDetail)" class="current-order fast-travel-order">
              <span class="order-label">{{ getFastTravelLabel(selectedUnitDetail) }} to:</span>
              <span class="order-value">Hex {{ getFastTravelOrder(selectedUnitDetail)?.path?.slice(-1)[0] }} ({{ getFastTravelOrder(selectedUnitDetail)?.path?.length }} hexes)</span>
            </div>
            
            <!-- Fast Travel Mode UI -->
            <div v-if="fastTravelMode && fastTravelUnit?.id === selectedUnitDetail?.id" class="fast-travel-mode-ui">
              <div class="fast-travel-header">
                <span class="fast-travel-label">{{ fastTravelIsNaval ? '⛵ Full Sail' : '🏃 March' }} Mode</span>
                <button class="cancel-mode-btn" @click="cancelFastTravelMode">✕</button>
              </div>
              
              <div class="fast-travel-info">
                <p class="fast-travel-instructions">Click adjacent {{ fastTravelIsNaval ? 'ocean' : 'road' }} hexes to trace path</p>
                <div class="fast-travel-stats">
                  <span class="stat">Path: {{ fastTravelPath.length }} / 10 hexes</span>
                </div>
              </div>
              
              <div v-if="fastTravelError" class="fast-travel-error">
                {{ fastTravelError }}
              </div>
              
              <div class="fast-travel-controls">
                <button 
                  class="btn btn-small"
                  :disabled="fastTravelPath.length === 0"
                  @click="undoFastTravelStep"
                >↩ Undo</button>
                <button 
                  class="btn btn-gold btn-small"
                  :disabled="fastTravelPath.length === 0"
                  @click="submitFastTravelOrder"
                >✓ Confirm</button>
              </div>
            </div>
          </div>
        </template>
        
        <!-- BASE INFO PANEL -->
        <template v-else-if="selectedBaseDetail">
          <div class="card-header">
            <h3 class="card-title">{{ selectedBaseDetail.tier === 0 ? 'Ruins of ' + selectedBaseDetail.name : selectedBaseDetail.name }}</h3>
            <button class="close-btn" @click="closeBaseDetail">×</button>
          </div>
          
          <!-- Base Visual -->
          <div class="base-portrait" :class="{ 'ruins-portrait': selectedBaseDetail.tier === 0 }">
            <div class="portrait-frame">
              <img 
                v-if="selectedBaseDetail.tier > 0"
                :src="getFactionBanner(getFactionName(selectedBaseDetail.factionId))" 
                class="portrait-banner"
                alt=""
              />
              <img 
                :src="selectedBaseDetail.tier === 0 ? getRuinsImage() : getBaseImage(selectedBaseDetail.factionId, selectedBaseDetail.tier || 1)" 
                class="portrait-base"
                alt=""
              />
            </div>
          </div>
          <div class="portrait-faction" :class="{ 'ruins-faction': selectedBaseDetail.tier === 0 }">
            {{ selectedBaseDetail.tier === 0 ? 'Abandoned' : getFactionName(selectedBaseDetail.factionId) }}
          </div>
          
          <!-- RUINS VIEW (tier 0) - minimal info -->
          <template v-if="selectedBaseDetail.tier === 0">
            <div class="base-stats ruins-stats">
              <div class="stat-row">
                <span class="stat-label">Location</span>
                <span class="stat-value highlight">Hex {{ selectedBaseDetail.location }}</span>
              </div>
              <div class="ruins-description">
                <p class="text-muted">🏚️ These ruins are all that remain of what was once {{ selectedBaseDetail.name }}.</p>
                <p class="text-small">A new settlement could be built here in the future.</p>
              </div>
            </div>
          </template>
          
          <!-- ACTIVE BASE VIEW (tier > 0) -->
          <template v-else>
          <!-- Base Stats -->
          <div class="base-stats">
            <div class="stat-row">
              <span class="stat-label">Tier</span>
              <span class="stat-value">
                <span class="tier-display highlight">{{ selectedBaseDetail.tier || 1 }}</span>
                <span class="tier-label">{{ getTierLabel(selectedBaseDetail.tier, selectedBaseDetail.factionId) }}</span>
              </span>
            </div>
            
            <div class="stat-row">
              <span class="stat-label">Location</span>
              <span class="stat-value highlight">Hex {{ selectedBaseDetail.location }}</span>
            </div>
            
            <!-- Resources - only shown to owning faction or admin -->
            <template v-if="canViewBaseResources(selectedBaseDetail)">
              <div class="resources-header">
                <h4>💰 Resources</h4>
              </div>
              
              <div class="stat-row resource-row">
                <span class="stat-label">🪙 Gold</span>
                <span class="stat-value resource-value gold">
                  {{ selectedBaseDetail.gold ?? 0 }}
                  <span v-if="getPendingResource('gold') !== 0" 
                        class="pending-resource"
                        :class="{ 'positive': getPendingResource('gold') > 0, 'negative': getPendingResource('gold') < 0 }">
                    ({{ getPendingResource('gold') > 0 ? '+' : '' }}{{ getPendingResource('gold') }})
                  </span>
                </span>
              </div>
              
              <div class="stat-row resource-row">
                <span class="stat-label">🪵 Lumber</span>
                <span class="stat-value resource-value lumber">
                  {{ selectedBaseDetail.lumber ?? 0 }}
                  <span v-if="getPendingResource('lumber') !== 0" 
                        class="pending-resource"
                        :class="{ 'positive': getPendingResource('lumber') > 0, 'negative': getPendingResource('lumber') < 0 }">
                    ({{ getPendingResource('lumber') > 0 ? '+' : '' }}{{ getPendingResource('lumber') }})
                  </span>
                </span>
              </div>
              
              <div class="stat-row resource-row">
                <span class="stat-label">🛢️ Oil</span>
                <span class="stat-value resource-value oil">
                  {{ selectedBaseDetail.oil ?? 0 }}
                  <span v-if="getPendingResource('oil') !== 0" 
                        class="pending-resource"
                        :class="{ 'positive': getPendingResource('oil') > 0, 'negative': getPendingResource('oil') < 0 }">
                    ({{ getPendingResource('oil') > 0 ? '+' : '' }}{{ getPendingResource('oil') }})
                  </span>
                </span>
              </div>
            </template>
            
            <!-- Hidden resources notice for non-owning faction -->
            <template v-else>
              <div class="resources-hidden">
                <span class="text-muted">🔒 Resources hidden</span>
                <span class="text-small">Not your faction</span>
              </div>
            </template>
          </div>
          
          <!-- Base Actions -->
          <div class="base-actions" v-if="canViewBaseActions(selectedBaseDetail)">
            <div class="actions-header">
              <h4>⚔️ Actions</h4>
              <span class="action-counter" v-if="baseOrders && !baseOrders.inCombat && canIssueBaseActions(selectedBaseDetail)">
                {{ baseOrders.actionsUsed || 0 }}/{{ selectedBaseDetail.tier || 1 }} used
              </span>
            </div>
            
            <!-- Not this faction's turn - Actions Blocked -->
            <div v-if="isBaseOrdersBlockedByInitiative(selectedBaseDetail)" class="actions-locked-initiative">
              <div class="initiative-lock-icon">⏳</div>
              <div class="initiative-lock-message">Not This Faction's Turn</div>
              <div class="initiative-lock-reason" v-if="selectedBaseFactionInfo">
                {{ selectedBaseFactionInfo.factionName }} (Initiative {{ selectedBaseFactionInfo.initiative }}) 
                — Current: Initiative {{ selectedBaseFactionInfo.currentInitiative }}
              </div>
            </div>
            
            <!-- Base in Combat - Actions Locked -->
            <div v-else-if="baseOrders?.inCombat" class="actions-locked-combat">
              <div class="combat-lock-icon">⚔️</div>
              <div class="combat-lock-message">Actions Locked</div>
              <div class="combat-lock-reason">Base is in combat</div>
            </div>
            
            <!-- Pending Orders (only show if not in combat AND it's their turn) -->
            <div class="pending-orders" v-else-if="baseOrders?.orders?.length > 0 && !isBaseOrdersBlockedByInitiative(selectedBaseDetail)">
              <div class="pending-orders-header">
                <span class="pending-label">Queued Orders</span>
                <button class="cancel-btn" @click="cancelLastOrder" title="Cancel last order">
                  ↩️ Undo
                </button>
              </div>
              <div 
                v-for="(order, idx) in baseOrders.orders" 
                :key="idx"
                class="pending-order-item"
              >
                <span class="order-number">{{ idx + 1 }}.</span>
                <span class="order-type">{{ formatOrderType(order.type) }}</span>
                <!-- Harvest orders are legacy/deprecated - skip display -->
                <span v-if="order.type === 'harvest'" class="order-preview deprecated">
                  (deprecated - harvest is automatic)
                </span>
                <span v-else-if="order.type === 'expand'" class="order-preview">
                  {{ order.expansion_type }} @ Hex {{ order.target_hex }} (-2🪵)
                </span>
                <span v-else-if="order.type === 'commerce'" class="order-preview">
                  -2{{ RESOURCE_INFO[order.from_resource]?.icon }} → +1{{ RESOURCE_INFO[order.to_resource]?.icon }} <span class="next-turn-badge">next turn</span>
                </span>
                <span v-else-if="order.type === 'upgrade'" class="order-preview">
                  T{{ order.from_tier }}→{{ order.to_tier }} (-{{ order.cost_gold }}🪙 -{{ order.cost_lumber }}🪵 -{{ order.cost_oil }}🛢️)
                </span>
                <span v-else-if="order.type === 'rest'" class="order-preview">
                  💤 {{ order.unit_name }} +{{ order.heal_amount }}HP (-2🪙)
                </span>
                <span v-else-if="order.type === 'build_unit'" class="order-preview">
                  🔨 {{ order.unit_name }} (-{{ order.gold_cost }}🪙 -{{ order.lumber_cost }}🪵 -{{ order.oil_cost }}🛢️)
                </span>
                <span v-else-if="order.type === 'establish_caravan'" class="order-preview">
                  🛤️ → {{ order.dest_base_name || 'Unknown' }} (-{{ order.lumber_cost }}🪵<span v-if="order.oil_cost"> -{{ order.oil_cost }}🛢️</span>)
                </span>
                <span v-else-if="order.type === 'send_resources'" class="order-preview">
                  📦 → {{ order.dest_base_name || 'Unknown' }} 
                  (<span v-if="order.gold">-{{ order.gold }}🪙</span>
                   <span v-if="order.lumber">-{{ order.lumber }}🪵</span>
                   <span v-if="order.oil">-{{ order.oil }}🛢️</span>)
                </span>
              </div>
            </div>
            
            <!-- Upcoming Harvest Info (automatic, not an action) - only show on their turn -->
            <div class="harvest-info" v-if="harvestPreview?.expectedYield && !isBaseOrdersBlockedByInitiative(selectedBaseDetail)">
              <div class="harvest-info-header">
                <span class="harvest-icon">🌾</span>
                <span class="harvest-label">Upcoming Harvest</span>
                <span class="harvest-auto-badge">Auto</span>
              </div>
              <div class="harvest-preview">
                <span v-if="harvestPreview.expectedYield.gold > 0" class="harvest-yield gold">+{{ harvestPreview.expectedYield.gold }}🪙</span>
                <span v-if="harvestPreview.expectedYield.lumber > 0" class="harvest-yield lumber">+{{ harvestPreview.expectedYield.lumber }}🪵</span>
                <span v-if="harvestPreview.expectedYield.oil > 0" class="harvest-yield oil">+{{ harvestPreview.expectedYield.oil }}🛢️</span>
                <span v-if="harvestPreview.expectedYield.gold === 0 && harvestPreview.expectedYield.lumber === 0 && harvestPreview.expectedYield.oil === 0" class="no-yield">No resources</span>
              </div>
            </div>
            
            <!-- Available Actions - only show on their turn -->
            <div class="available-actions" v-if="baseOrders?.actionsRemaining > 0 && !baseOrders?.inCombat && !isBaseOrdersBlockedByInitiative(selectedBaseDetail)">
              <!-- Expand Action -->
              <button 
                v-if="!expandMode"
                class="action-btn expand-btn"
                :disabled="!canExpand"
                :title="expandTooltip"
                @click="enterExpandMode"
              >
                <span class="action-icon">🏗️</span>
                <span class="action-name">Expand</span>
                <span class="action-cost">-2🪵</span>
              </button>
              
              <!-- Expand Mode Active -->
              <div v-else class="expand-mode-active">
                <div class="expand-mode-header">
                  <span class="expand-mode-label">🎯 Select expansion target</span>
                  <button class="cancel-expand-btn" @click="exitExpandMode">Cancel</button>
                </div>
                <div class="expand-mode-info text-muted">
                  Click a highlighted hex to build
                </div>
              </div>
              
              <!-- Commerce Action -->
              <button 
                v-if="!commerceMode"
                class="action-btn commerce-btn"
                :disabled="!canCommerce"
                :title="commerceTooltip"
                @click="enterCommerceMode"
              >
                <span class="action-icon">💱</span>
                <span class="action-name">Commerce</span>
                <span class="action-cost">2→1</span>
              </button>
              
              <!-- Commerce Mode Active -->
              <div v-else class="commerce-mode-active">
                <div class="commerce-mode-header">
                  <span class="commerce-mode-label">💱 Commerce</span>
                  <button class="cancel-commerce-btn" @click="exitCommerceMode">Cancel</button>
                </div>
                
                <!-- Step 1: Select resource to spend -->
                <div v-if="!selectedCommerceFrom" class="commerce-step">
                  <div class="commerce-step-label">Spend 2 of:</div>
                  <div class="commerce-options">
                    <button 
                      v-for="opt in commerceFromOptions" 
                      :key="opt.resource"
                      class="commerce-option-btn"
                      @click="selectedCommerceFrom = opt.resource"
                    >
                      <span class="option-icon">{{ opt.icon }}</span>
                      <span class="option-name">{{ opt.name }}</span>
                      <span class="option-amount">({{ opt.amount }})</span>
                    </button>
                  </div>
                </div>
                
                <!-- Step 2: Select resource to gain -->
                <div v-else class="commerce-step">
                  <div class="commerce-step-label">
                    Spending 2 {{ RESOURCE_INFO[selectedCommerceFrom].icon }} → Gain 1:
                  </div>
                  <div class="commerce-options">
                    <button 
                      v-for="opt in commerceToOptions" 
                      :key="opt.resource"
                      class="commerce-option-btn"
                      @click="queueCommerce(opt.resource)"
                    >
                      <span class="option-icon">{{ opt.icon }}</span>
                      <span class="option-name">{{ opt.name }}</span>
                    </button>
                  </div>
                  <button class="commerce-back-btn" @click="selectedCommerceFrom = null">
                    ← Back
                  </button>
                </div>
              </div>
              
              <!-- Upgrade Base Action -->
              <button 
                v-if="upgradeInfo"
                class="action-btn upgrade-btn"
                :disabled="!canUpgrade || !upgradeInfo.targetTier"
                :title="upgradeInfo.targetTier ? upgradeTooltip : 'Base is max tier'"
                @click="upgradeInfo.targetTier && queueUpgrade()"
              >
                <span class="action-icon">⬆️</span>
                <span class="action-name">Upgrade</span>
                <span class="action-cost">
                  {{ upgradeInfo.targetTier ? `T${upgradeInfo.currentTier}→${upgradeInfo.targetTier}` : 'Max Tier' }}
                </span>
              </button>
              
              <!-- Rest Unit Action -->
              <button 
                v-if="!restMode && restableUnits.length > 0"
                class="action-btn rest-btn"
                :disabled="!canRest.canRest"
                :title="restTooltip"
                @click="enterRestMode"
              >
                <span class="action-icon">💤</span>
                <span class="action-name">Rest Unit</span>
                <span class="action-cost">-2🪙</span>
              </button>
              
              <!-- Rest Mode Active: Unit Selection -->
              <div v-else-if="restMode" class="rest-mode-active">
                <div class="rest-mode-header">
                  <span class="rest-mode-label">💤 Select Unit to Rest</span>
                  <button class="cancel-rest-btn" @click="cancelRestMode">Cancel</button>
                </div>
                
                <div class="restable-units-list">
                  <div 
                    v-for="unit in restableUnits" 
                    :key="unit.unit_id || unit.unitId"
                    class="restable-unit-item"
                    :class="{ 
                      'can-rest': unit.can_rest || unit.canRest,
                      'cannot-rest': !(unit.can_rest || unit.canRest)
                    }"
                    @click="(unit.can_rest || unit.canRest) && queueRestUnit(unit)"
                    :title="(unit.can_rest || unit.canRest) ? `Heal ${unit.heal_amount || unit.healAmount} HP` : (unit.reason || 'Cannot rest')"
                  >
                    <span class="unit-name">{{ unit.name }}</span>
                    <span class="unit-hp">{{ unit.hp }}/{{ unit.max_hp || unit.maxHp }}</span>
                    <span v-if="unit.can_rest || unit.canRest" class="heal-preview">+{{ unit.heal_amount || unit.healAmount }}</span>
                    <span v-else class="cannot-reason">{{ unit.reason }}</span>
                  </div>
                </div>
              </div>
              
              <!-- Build Unit Action -->
              <button 
                v-if="canShowBuildButton"
                class="action-btn build-btn"
                :disabled="!buildFoodInfo?.canBuild"
                :title="buildTooltip"
                @click="openBuildModal"
              >
                <span class="action-icon">🔨</span>
                <span class="action-name">Build Unit</span>
              </button>
              
              <!-- Build already queued indicator -->
              <div v-else-if="hasBuildQueued" class="build-queued text-muted">
                <span class="action-icon">🔨</span>
                <span>Build Unit Queued</span>
              </div>
              
              <!-- Establish Caravan Action -->
              <button 
                v-if="canEstablishCaravan && !caravanMode"
                class="action-btn caravan-btn"
                title="Establish a trade route to another base"
                @click="startCaravanMode"
              >
                <span class="action-icon">🛤️</span>
                <span class="action-name">Establish Caravan</span>
              </button>
              
              <!-- Caravan Mode Active -->
              <div v-if="caravanMode" class="caravan-mode-active">
                <div class="caravan-mode-header">
                  <span class="caravan-mode-label">🛤️ Establish Caravan</span>
                  <button class="cancel-mode-btn" @click="cancelCaravanMode">✕</button>
                </div>
                
                <!-- Trace Path - click hexes to build path, click destination base to finish -->
                <div class="caravan-path-tracing">
                  <div class="caravan-instructions">
                    <p>Click hexes to trace your route.</p>
                    <p>Click a destination base to complete.</p>
                    <p class="caravan-type-info" v-if="caravanIsSea !== null">
                      <span class="caravan-type-badge" :class="caravanIsSea ? 'sea' : 'land'">
                        {{ caravanIsSea ? '⛵ Sea Caravan' : '🚶 Land Caravan' }}
                      </span>
                    </p>
                    <p class="caravan-type-info" v-else>
                      <span class="caravan-type-undecided">Type determined by first hex</span>
                    </p>
                  </div>
                  
                  <!-- Error display -->
                  <div v-if="caravanError" class="caravan-error">
                    {{ caravanError }}
                  </div>
                  
                  <div class="caravan-path-info">
                    <div class="path-length">
                      <span class="label">Path:</span>
                      <span class="value">{{ caravanPath.length }} / 15 hexes</span>
                    </div>
                    <div class="path-cost" :class="{ 'threshold': isAtCostThreshold }">
                      <span class="label">Cost:</span>
                      <span class="cost-values">
                        <span class="cost-lumber">🪵 {{ caravanCost.lumber }}</span>
                        <span v-if="caravanIsSea" class="cost-oil">🛢️ {{ caravanCost.oil }}</span>
                      </span>
                      <span class="cost-tier">({{ getCaravanCostTier }})</span>
                    </div>
                  </div>
                  
                  <div class="caravan-path-controls">
                    <button 
                      class="undo-path-btn"
                      :disabled="caravanPath.length <= 1"
                      @click="undoCaravanPathStep"
                    >↩ Undo</button>
                    <div class="path-hint">
                      Click highlighted hexes to trace route
                    </div>
                  </div>
                  
                  <div class="valid-hexes-count">
                    {{ caravanValidNextHexes.length }} valid next hex{{ caravanValidNextHexes.length !== 1 ? 'es' : '' }}
                    <span v-if="destinationReachable" class="dest-reachable">
                      (🎯 destination reachable!)
                    </span>
                  </div>
                  
                  <!-- List valid destinations -->
                  <div class="caravan-destinations" v-if="caravanPath.length >= 2">
                    <span class="dest-list-label">Valid destinations:</span>
                    <div class="dest-list">
                      <span 
                        v-for="target in validDestinationsReachable" 
                        :key="target.baseId"
                        class="dest-chip"
                      >
                        {{ target.baseName }}
                      </span>
                      <span v-if="validDestinationsReachable.length === 0" class="no-dests">
                        None in range yet
                      </span>
                    </div>
                  </div>
                </div>
              </div>
              
              <!-- Send Resources Action -->
              <button 
                v-if="canSendResources && !sendMode && !caravanMode"
                class="action-btn send-btn"
                title="Send resources to a connected base via caravan"
                @click="startSendMode"
              >
                <span class="action-icon">📦</span>
                <span class="action-name">Send Resources</span>
              </button>
              
              <!-- Send Resources Mode Active -->
              <div v-if="sendMode" class="send-mode-active">
                <div class="send-mode-header">
                  <span class="send-mode-label">📦 Send Resources</span>
                  <button class="cancel-mode-btn" @click="cancelSendMode">✕</button>
                </div>
                
                <!-- Step 1: Select Destination -->
                <div v-if="!selectedSendDest" class="send-dest-selection">
                  <div class="send-step-label">Select Destination:</div>
                  <div class="send-targets-list">
                    <div 
                      v-for="dest in sendDestinations" 
                      :key="dest.base_id"
                      class="send-target-item"
                      @click="selectSendDestination(dest)"
                    >
                      <span class="target-name">{{ dest.base_name }}</span>
                      <span class="caravan-length">({{ dest.caravan_path_length }} hexes)</span>
                    </div>
                    <div v-if="sendDestinations.length === 0" class="no-targets">
                      No caravan connections available
                    </div>
                  </div>
                </div>
                
                <!-- Step 2: Select Amounts -->
                <div v-else class="send-amounts-selection">
                  <div class="send-dest-info">
                    <span class="dest-label">To:</span>
                    <span class="dest-name">{{ selectedSendDest.base_name }}</span>
                  </div>
                  
                  <div class="send-amounts-form">
                    <div class="send-amount-row" v-if="sendAvailableResources.gold > 0">
                      <span class="resource-icon">🪙</span>
                      <span class="resource-label">Gold:</span>
                      <div class="amount-control">
                        <button 
                          class="amount-btn minus"
                          :disabled="sendAmounts.gold <= 0"
                          @click="updateSendAmount('gold', sendAmounts.gold - 1)"
                        >−</button>
                        <span class="amount-value">{{ sendAmounts.gold }}</span>
                        <button 
                          class="amount-btn plus"
                          :disabled="sendAmounts.gold >= sendAvailableResources.gold"
                          @click="updateSendAmount('gold', sendAmounts.gold + 1)"
                        >+</button>
                      </div>
                      <span class="max-available">/ {{ sendAvailableResources.gold }}</span>
                    </div>
                    
                    <div class="send-amount-row" v-if="sendAvailableResources.lumber > 0">
                      <span class="resource-icon">🪵</span>
                      <span class="resource-label">Lumber:</span>
                      <div class="amount-control">
                        <button 
                          class="amount-btn minus"
                          :disabled="sendAmounts.lumber <= 0"
                          @click="updateSendAmount('lumber', sendAmounts.lumber - 1)"
                        >−</button>
                        <span class="amount-value">{{ sendAmounts.lumber }}</span>
                        <button 
                          class="amount-btn plus"
                          :disabled="sendAmounts.lumber >= sendAvailableResources.lumber"
                          @click="updateSendAmount('lumber', sendAmounts.lumber + 1)"
                        >+</button>
                      </div>
                      <span class="max-available">/ {{ sendAvailableResources.lumber }}</span>
                    </div>
                    
                    <div class="send-amount-row" v-if="sendAvailableResources.oil > 0">
                      <span class="resource-icon">🛢️</span>
                      <span class="resource-label">Oil:</span>
                      <div class="amount-control">
                        <button 
                          class="amount-btn minus"
                          :disabled="sendAmounts.oil <= 0"
                          @click="updateSendAmount('oil', sendAmounts.oil - 1)"
                        >−</button>
                        <span class="amount-value">{{ sendAmounts.oil }}</span>
                        <button 
                          class="amount-btn plus"
                          :disabled="sendAmounts.oil >= sendAvailableResources.oil"
                          @click="updateSendAmount('oil', sendAmounts.oil + 1)"
                        >+</button>
                      </div>
                      <span class="max-available">/ {{ sendAvailableResources.oil }}</span>
                    </div>
                    
                    <div v-if="sendAvailableResources.gold === 0 && sendAvailableResources.lumber === 0 && sendAvailableResources.oil === 0" 
                         class="no-resources">
                      No resources available to send
                    </div>
                  </div>
                  
                  <div class="send-summary">
                    <span class="summary-label">Sending:</span>
                    <span class="summary-values">
                      <span v-if="sendAmounts.gold > 0">🪙{{ sendAmounts.gold }}</span>
                      <span v-if="sendAmounts.lumber > 0">🪵{{ sendAmounts.lumber }}</span>
                      <span v-if="sendAmounts.oil > 0">🛢️{{ sendAmounts.oil }}</span>
                      <span v-if="totalSending === 0" class="text-muted">Nothing selected</span>
                    </span>
                  </div>
                  
                  <div class="send-actions">
                    <button 
                      class="send-confirm-btn"
                      :disabled="totalSending === 0"
                      @click="confirmSendResources"
                    >
                      ✓ Send Resources
                    </button>
                    <button 
                      class="send-back-btn"
                      @click="selectedSendDest = null"
                    >
                      ← Back
                    </button>
                  </div>
                </div>
              </div>
            </div>
            
            <!-- No actions remaining (only show if not in combat AND it's their turn) -->
            <div v-else-if="!baseOrders?.inCombat && !isBaseOrdersBlockedByInitiative(selectedBaseDetail)" class="no-actions-left text-muted">
              No actions remaining this turn
            </div>
          </div>
          
          <!-- View-only mode for non-owning faction -->
          <div class="base-actions-locked" v-else>
            <div class="actions-header">
              <h4>⚔️ Actions</h4>
            </div>
            <div class="locked-notice text-muted">
              🔒 Not your faction
            </div>
          </div>
          </template><!-- End ACTIVE BASE VIEW -->
        </template>
        
        <!-- HEX INFO PANEL -->
        <template v-else-if="selectedHex">
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
            
            <!-- Hexside Terrains -->
            <div class="hexside-terrains">
              <div class="hexside-header">Hexsides</div>
              <div class="hexside-grid">
                <div 
                  v-for="hs in getHexsideTerrains(selectedHex)" 
                  :key="hs.dir"
                  class="hexside-item"
                >
                  <span class="hexside-dir">{{ hs.dir }}</span>
                  <span class="hexside-terrain">{{ hs.name }}<span v-if="hs.hasRoad" class="road-indicator"> (R)</span></span>
                </div>
              </div>
            </div>
            
            <!-- Base info - clickable to open Base Info panel -->
            <template v-if="getBaseAtHex(selectedHex.id)">
              <div class="detail-row clickable base-link" @click="selectBaseForDetail(getBaseAtHex(selectedHex.id))">
                <span class="detail-label">Settlement</span>
                <span class="detail-value highlight">{{ getBaseAtHex(selectedHex.id).name }}</span>
                <span class="view-arrow">→</span>
              </div>
              <div class="detail-row">
                <span class="detail-label">Tier</span>
                <span class="detail-value">{{ getBaseAtHex(selectedHex.id).tier }}</span>
              </div>
            </template>
          </div>

          <!-- Combat Hex Details (only shown for combat hexes) -->
          <div v-if="isCombatHex(selectedHex.id)" class="combat-hex-details">
            <div class="combat-hex-header">⚔️ Combat Hex</div>
            <div class="hexside-control-grid">
              <div 
                v-for="dir in ['N', 'NE', 'SE', 'S', 'SW', 'NW']" 
                :key="dir"
                class="hexside-control-item"
              >
                <span class="hexside-dir">{{ dir }}</span>
                <span 
                  class="hexside-initiative"
                  :style="{ color: getInitiativeColor(getHexsideControlForDir(selectedHex.id, dir)) }"
                >
                  Init {{ getHexsideControlForDir(selectedHex.id, dir) }}
                </span>
              </div>
            </div>
          </div>

          <!-- Units list - clickable to open Unit Info -->
          <div v-if="hexUnits.length" class="hex-units">
            <h4>Units ({{ hexUnits.length }})</h4>
            <div class="unit-list">
              <div
                v-for="unit in hexUnits"
                :key="unit.id"
                class="unit-item clickable"
                :class="{ 'own-unit': isOwnUnit(unit) }"
                @click="selectUnitForDetail(unit)"
              >
                <div class="unit-info">
                  <span class="unit-name">{{ unit.name }}</span>
                  <span class="unit-hp">{{ unit.hp }}/{{ unit.maxHp }}</span>
                </div>
                <span class="view-arrow">→</span>
              </div>
            </div>
          </div>
          <div v-else class="no-units">
            <span class="text-muted">No units at this hex</span>
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
          <!-- Road bonus only shown for ground units (unitType === 0) -->
          <div v-if="(selectedUnit?.roadMove || selectedUnit?.roadMoveRemaining || 0) > 0 && (selectedUnit?.unitType ?? selectedUnit?.unit_type ?? 0) === 0" class="movement-stats">
            <span class="label">Road Bonus:</span>
            <span class="value road-bonus" :class="{ 'used': roadMoveUsed > 0 }">
              {{ roadMoveUsed }} / {{ selectedUnit?.roadMove || selectedUnit?.roadMoveRemaining || 0 }}
            </span>
          </div>
          <div v-if="lastStepUsedRoad && (selectedUnit?.unitType ?? selectedUnit?.unit_type ?? 0) === 0" class="path-note">
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
      
      <!-- Ranged Fire Order Panel -->
      <div v-if="rangedfireMode" class="rangedfire-panel card">
        <div class="card-header">
          <h3 class="card-title">🎯 Ranged Fire Order</h3>
          <button class="close-btn" @click="cancelRangedfireMode">×</button>
        </div>
        
        <div class="rangedfire-info">
          <div class="unit-being-ordered">
            <span class="label">Unit:</span>
            <span class="value">{{ rangedfireUnit?.name }}</span>
          </div>
          <div class="unit-location">
            <span class="label">Location:</span>
            <span class="value">Hex {{ rangedfireUnit?.location }}</span>
          </div>
          <div class="valid-targets">
            <span class="label">Valid Targets:</span>
            <span class="value">{{ validRangedfireTargets.length }} adjacent combat{{ validRangedfireTargets.length !== 1 ? 's' : '' }}</span>
          </div>
        </div>
        
        <div class="rangedfire-instructions">
          <p>Click on a highlighted hex to fire into that combat.</p>
          <p class="rangedfire-note">⚠️ Ranged fire uses HEX terrain penalties (not hexside).</p>
        </div>
        
        <div v-if="orderMessage" class="order-message success">
          {{ orderMessage }}
        </div>
        <div v-if="orderError" class="order-message error">
          {{ orderError }}
        </div>
        
        <div class="rangedfire-actions">
          <button 
            class="btn btn-secondary btn-sm"
            @click="cancelRangedfireMode"
          >
            Cancel
          </button>
        </div>
      </div>
    </div>
    
    <!-- Build Unit Modal -->
    <div v-if="buildModalOpen" class="build-modal-overlay" @click.self="closeBuildModal">
      <div class="build-modal">
        <div class="build-modal-header">
          <h2>🔨 Build Unit</h2>
          <div class="build-modal-subtitle" v-if="selectedBaseDetail">
            {{ selectedBaseDetail.name }} (Tier {{ selectedBaseDetail.tier }})
          </div>
          <button class="close-modal-btn" @click="closeBuildModal">✕</button>
        </div>
        
        <!-- Food Status Bar -->
        <div class="food-status-bar" v-if="buildFoodInfo">
          <div class="food-info">
            <span class="food-label">🍖 Food:</span>
            <span class="food-value" :class="{ 'food-capped': !buildFoodInfo.canBuild }">
              {{ buildFoodInfo.unitCount }} / {{ buildFoodInfo.limit }}
            </span>
            <span v-if="buildFoodInfo.pendingBuilds > 0" class="pending-builds">
              (+{{ buildFoodInfo.pendingBuilds }} pending)
            </span>
          </div>
          <div class="food-bar">
            <div 
              class="food-bar-fill" 
              :class="{ 'food-capped': !buildFoodInfo.canBuild }"
              :style="{ width: `${Math.min(100, (buildFoodInfo.unitCount / buildFoodInfo.limit) * 100)}%` }"
            ></div>
          </div>
          <div v-if="!buildFoodInfo.canBuild" class="food-warning">
            ⚠️ Food cap reached - cannot build more units
          </div>
        </div>
        
        <!-- Resource Bar -->
        <div class="resource-status-bar" v-if="selectedBaseDetail">
          <div class="resource-item">
            <span class="resource-icon">🪙</span>
            <span class="resource-amount">{{ selectedBaseDetail.gold ?? 0 }}</span>
            <span v-if="getPendingResource('gold') !== 0" 
                  class="pending-resource"
                  :class="{ 'positive': getPendingResource('gold') > 0, 'negative': getPendingResource('gold') < 0 }">
              ({{ getPendingResource('gold') > 0 ? '+' : '' }}{{ getPendingResource('gold') }})
            </span>
          </div>
          <div class="resource-item">
            <span class="resource-icon">🪵</span>
            <span class="resource-amount">{{ selectedBaseDetail.lumber ?? 0 }}</span>
            <span v-if="getPendingResource('lumber') !== 0" 
                  class="pending-resource"
                  :class="{ 'positive': getPendingResource('lumber') > 0, 'negative': getPendingResource('lumber') < 0 }">
              ({{ getPendingResource('lumber') > 0 ? '+' : '' }}{{ getPendingResource('lumber') }})
            </span>
          </div>
          <div class="resource-item">
            <span class="resource-icon">🛢️</span>
            <span class="resource-amount">{{ selectedBaseDetail.oil ?? 0 }}</span>
            <span v-if="getPendingResource('oil') !== 0" 
                  class="pending-resource"
                  :class="{ 'positive': getPendingResource('oil') > 0, 'negative': getPendingResource('oil') < 0 }">
              ({{ getPendingResource('oil') > 0 ? '+' : '' }}{{ getPendingResource('oil') }})
            </span>
          </div>
        </div>
        
        <!-- Unit Cards Grid -->
        <div class="build-units-grid">
          <div 
            v-for="unit in buildableUnits" 
            :key="unit.unit_name"
            class="build-unit-card"
            :class="{ 
              'can-build': unit.can_build, 
              'cannot-build': !unit.can_build,
              'tier-locked': unit.reasons?.some(r => r.includes('Tier'))
            }"
            @click="unit.can_build && queueBuildUnit(unit)"
            :title="unit.can_build ? `Build ${unit.unit_name}` : unit.reasons?.join(', ')"
          >
            <!-- Unit Image -->
            <div class="unit-card-image">
              <img 
                :src="getBuildUnitImage(unit.unit_name)" 
                :alt="unit.unit_name"
                @error="$event.target.src = '/images/Units/footman.png'"
              />
              <div v-if="!unit.can_build" class="unit-card-locked-overlay">
                <span v-if="unit.reasons?.some(r => r.includes('Tier'))">🔒</span>
                <span v-else-if="unit.reasons?.some(r => r.includes('Food'))">🍖</span>
                <span v-else>💰</span>
              </div>
            </div>
            
            <!-- Unit Name -->
            <div class="unit-card-name">{{ unit.unit_name }}</div>
            
            <!-- Cost Row -->
            <div class="unit-card-cost">
              <span v-if="unit.gold_cost > 0" class="cost-item gold">
                <span class="cost-icon">🪙</span>{{ unit.gold_cost }}
              </span>
              <span v-if="unit.lumber_cost > 0" class="cost-item lumber">
                <span class="cost-icon">🪵</span>{{ unit.lumber_cost }}
              </span>
              <span v-if="unit.oil_cost > 0" class="cost-item oil">
                <span class="cost-icon">🛢️</span>{{ unit.oil_cost }}
              </span>
            </div>
            
            <!-- Stats Grid -->
            <div class="unit-card-stats">
              <div class="stat-item">
                <span class="stat-label">HP</span>
                <span class="stat-value">{{ unit.stats?.max_hp || '?' }}</span>
              </div>
              <div class="stat-item">
                <span class="stat-label">Combat</span>
                <span class="stat-value">{{ unit.stats?.combat || '?' }}</span>
              </div>
              <div class="stat-item">
                <span class="stat-label">Move</span>
                <span class="stat-value">{{ unit.stats?.movement || '?' }}</span>
              </div>
              <div class="stat-item">
                <span class="stat-label">Type</span>
                <span class="stat-value type-label">{{ getUnitTypeLabel(unit.stats?.unit_type) }}</span>
              </div>
            </div>
            
            <!-- Category & Armor Row -->
            <div class="unit-card-extras">
              <div class="category-badge">{{ getCategoryLabel(unit.stats?.category) }}</div>
              <div class="armor-info" v-if="unit.stats?.light_armor > 0 || unit.stats?.heavy_armor > 0 || unit.stats?.natural_armor > 0">
                <span v-if="unit.stats?.light_armor > 0" class="armor light" title="Light Armor">🛡️{{ unit.stats.light_armor }}</span>
                <span v-if="unit.stats?.heavy_armor > 0" class="armor heavy" title="Heavy Armor">🔰{{ unit.stats.heavy_armor }}</span>
                <span v-if="unit.stats?.natural_armor > 0" class="armor natural" title="Natural Armor">🐉{{ unit.stats.natural_armor }}</span>
              </div>
            </div>
            
            <!-- Tier requirement and error reasons removed for uniform card sizing -->
            <!-- Info available via hover tooltip -->
          </div>
        </div>
        
        <!-- Empty State -->
        <div v-if="buildableUnits.length === 0" class="no-buildable-units">
          <span class="empty-icon">🏗️</span>
          <span>No units available to build at this base</span>
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

/* Debug Mode Indicators */
.debug-indicator {
  display: flex;
  align-items: center;
  gap: var(--space-xs);
  padding: var(--space-xs) var(--space-sm);
  background: linear-gradient(135deg, #4a1c7a, #6b2fa0);
  border: 1px solid #9b4dca;
  border-radius: var(--radius-md);
  color: #e0c0ff;
  font-size: 0.8rem;
  font-weight: 600;
  text-shadow: 0 1px 2px rgba(0,0,0,0.5);
  animation: pulse-glow 2s infinite;
}

@keyframes pulse-glow {
  0%, 100% { box-shadow: 0 0 5px rgba(155, 77, 202, 0.5); }
  50% { box-shadow: 0 0 15px rgba(155, 77, 202, 0.8); }
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
.info-panel {
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

.unit-id-label {
  display: block;
  font-size: 0.75rem;
  color: var(--color-text-muted);
  margin-top: -0.25rem;
  margin-bottom: 0.25rem;
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

/* Hexside terrain display */
.hexside-terrains {
  margin-top: var(--space-sm);
  padding: var(--space-sm);
  background: var(--color-bg-dark);
  border-radius: 4px;
  border: 1px solid var(--color-border);
}

.hexside-header {
  font-size: 0.75rem;
  color: var(--color-text-muted);
  text-transform: uppercase;
  margin-bottom: var(--space-xs);
  letter-spacing: 0.5px;
}

.hexside-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 4px;
}

.hexside-item {
  display: flex;
  justify-content: space-between;
  padding: 2px 6px;
  background: rgba(200, 150, 50, 0.15);
  border: 1px solid rgba(200, 150, 50, 0.3);
  border-radius: 3px;
  font-size: 0.8rem;
}

.hexside-dir {
  font-weight: 600;
  color: var(--color-text-secondary);
  min-width: 24px;
}

.hexside-terrain {
  color: var(--color-gold);
}

.hexside-terrain .road-indicator {
  color: #8b4513;  /* Saddle brown for roads */
  font-weight: 600;
}

/* Combat Hex Details */
.combat-hex-details {
  margin-top: var(--space-sm);
  padding: var(--space-sm);
  background: rgba(255, 68, 68, 0.1);
  border: 1px solid rgba(255, 68, 68, 0.3);
  border-radius: 4px;
}

.combat-hex-header {
  font-size: 0.85rem;
  font-weight: bold;
  color: #ff6666;
  margin-bottom: var(--space-xs);
}

.hexside-control-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 4px;
}

.hexside-control-item {
  display: flex;
  justify-content: space-between;
  padding: 2px 6px;
  background: var(--color-bg-dark);
  border-radius: 3px;
  font-size: 0.8rem;
}

.hexside-control-item .hexside-dir {
  font-weight: 600;
  color: var(--color-text-secondary);
  min-width: 24px;
}

.hexside-control-item .hexside-initiative {
  font-weight: bold;
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

/* Ranged Fire Panel */
.rangedfire-panel {
  position: absolute;
  top: var(--space-md);
  left: var(--space-md);
  width: 280px;
  z-index: 100;
  background: var(--color-bg-secondary);
  border: 2px solid #ff4500;
  box-shadow: 0 4px 20px rgba(255, 69, 0, 0.3);
}

.rangedfire-info {
  display: flex;
  flex-direction: column;
  gap: var(--space-xs);
  padding: var(--space-sm) 0;
  border-bottom: 1px solid var(--color-border);
}

.rangedfire-info .label {
  color: var(--color-text-muted);
  font-size: 0.85rem;
}

.rangedfire-info .value {
  color: var(--color-text);
  font-weight: 500;
}

.rangedfire-instructions {
  padding: var(--space-sm) 0;
  font-size: 0.85rem;
  color: var(--color-text-muted);
}

.rangedfire-instructions p {
  margin: 0 0 var(--space-xs) 0;
}

.rangedfire-note {
  color: #ff9800;
  font-size: 0.8rem;
}

.rangedfire-actions {
  display: flex;
  gap: var(--space-sm);
  padding-top: var(--space-sm);
  border-top: 1px solid var(--color-border);
}

.rangedfire-actions .btn {
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

/* ==================== Unit and Base Visuals ==================== */

.base-group {
  pointer-events: none;
}

.faction-banner {
  opacity: 0.9;
  filter: drop-shadow(2px 2px 2px rgba(0,0,0,0.5));
}

.base-building {
  filter: drop-shadow(2px 2px 3px rgba(0,0,0,0.6));
}

.base-name {
  font-family: var(--font-display);
  letter-spacing: 0.5px;
}

.units-group {
  pointer-events: auto;
}

.unit-icon {
  cursor: pointer;
  transition: opacity 0.15s ease;
}

.unit-icon:hover {
  opacity: 0.85;
  filter: brightness(1.2) drop-shadow(0 0 4px rgba(255,255,255,0.6));
}

.unit-background {
  filter: drop-shadow(1px 1px 2px rgba(0,0,0,0.5));
}

.unit-sprite {
  filter: drop-shadow(1px 1px 1px rgba(0,0,0,0.4));
}

.hp-bar-bg {
  opacity: 0.8;
}

.hp-bar {
  transition: width 0.3s ease;
}

.combat-border {
  stroke-dasharray: 8, 4;
  animation: combat-pulse 1.5s ease-in-out infinite;
}

@keyframes combat-pulse {
  0%, 100% { stroke-opacity: 0.8; stroke-width: 4; }
  50% { stroke-opacity: 1; stroke-width: 6; }
}

/* ==================== Unit Info Panel ==================== */

.info-panel {
  min-height: 200px;
}

.unit-portrait {
  text-align: center;
  padding: 0;
  background: linear-gradient(135deg, rgba(0,0,0,0.3), rgba(0,0,0,0.1));
  border-radius: var(--radius-md);
  margin-bottom: var(--space-xs);
}

.portrait-frame {
  position: relative;
  width: 100%;
  aspect-ratio: 1;
  border: 3px solid var(--color-gold);
  border-radius: var(--radius-md);
  overflow: hidden;
  box-shadow: 0 4px 12px rgba(0,0,0,0.4);
}

.portrait-bg, .portrait-unit {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.portrait-faction {
  font-size: 0.95rem;
  color: var(--color-gold);
  font-weight: 600;
  text-align: center;
  margin-bottom: var(--space-md);
}

/* Ruins styling */
.ruins-portrait {
  background: linear-gradient(135deg, rgba(50,50,50,0.4), rgba(30,30,30,0.2));
}

.ruins-faction {
  color: #888888;
  font-style: italic;
}

.ruins-stats {
  padding: var(--space-md);
}

.ruins-description {
  margin-top: var(--space-md);
  padding: var(--space-sm);
  border: 1px dashed #555;
  border-radius: var(--radius-sm);
  background: rgba(0,0,0,0.2);
}

.ruins-description p {
  margin: 0;
  line-height: 1.4;
}

.ruins-description .text-small {
  font-size: 0.85rem;
  margin-top: var(--space-xs);
}

.base-building.ruins {
  filter: grayscale(30%) drop-shadow(2px 2px 3px rgba(0,0,0,0.6));
  opacity: 0.85;
}

.unit-stats {
  padding: var(--space-sm) 0;
  border-top: 1px solid var(--color-border);
  border-bottom: 1px solid var(--color-border);
  margin-bottom: var(--space-md);
}

.stat-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--space-xs) 0;
  flex-wrap: wrap;
}

.stat-label {
  color: var(--color-text-muted);
  font-size: 0.85rem;
}

.stat-value {
  color: var(--color-text-primary);
  font-weight: 600;
  font-size: 1.1rem;
}

.stat-value.highlight {
  color: var(--color-gold);
}

.stat-value.road-bonus {
  color: #8bc34a;
}

.hp-current {
  color: #00cc00;
}

.hp-separator {
  color: var(--color-text-muted);
  margin: 0 2px;
}

.hp-max {
  color: var(--color-text-secondary);
}

.hp-bar-large {
  width: 100%;
  height: 6px;
  background: var(--color-bg-tertiary);
  border-radius: 3px;
  margin-top: var(--space-xs);
  overflow: hidden;
}

.hp-bar-fill {
  height: 100%;
  border-radius: 3px;
  transition: width 0.3s ease;
}

.hp-bar-fill.hp-high { background: linear-gradient(90deg, #00cc00, #44dd44); }
.hp-bar-fill.hp-mid { background: linear-gradient(90deg, #cccc00, #dddd44); }
.hp-bar-fill.hp-low { background: linear-gradient(90deg, #cc0000, #dd4444); }

.unit-orders {
  padding-top: var(--space-sm);
}

.unit-orders h4 {
  margin-bottom: var(--space-sm);
  color: var(--color-text-secondary);
  font-size: 0.9rem;
}

.order-buttons {
  display: flex;
  flex-direction: column;
  gap: var(--space-sm);
}

.order-buttons .btn {
  width: 100%;
  padding: var(--space-sm) var(--space-md);
  font-size: 1rem;
}

.not-your-turn-notice,
.not-own-unit-notice {
  padding: var(--space-sm);
  background: rgba(128,128,128,0.2);
  border-radius: var(--radius-sm);
  text-align: center;
  color: var(--color-text-muted);
  font-size: 0.85rem;
}

.current-order {
  margin-top: var(--space-md);
  padding: var(--space-sm);
  background: rgba(0, 255, 136, 0.1);
  border: 1px solid rgba(0, 255, 136, 0.3);
  border-radius: var(--radius-sm);
}

.order-label {
  color: var(--color-text-muted);
  font-size: 0.85rem;
}

.order-value {
  color: #00ff88;
  font-weight: 600;
  margin-left: var(--space-xs);
}

/* Clickable units in hex info */
.unit-item.clickable {
  cursor: pointer;
  transition: background 0.2s ease;
}

.unit-item.clickable:hover {
  background: rgba(201, 162, 39, 0.15);
}

.view-arrow {
  color: var(--color-text-muted);
  font-size: 1.2rem;
}

.unit-item.clickable:hover .view-arrow {
  color: var(--color-gold);
}

/* ==================== Base Info Panel ==================== */

.base-portrait {
  text-align: center;
  padding: 0;
  background: linear-gradient(135deg, rgba(0,0,0,0.3), rgba(0,0,0,0.1));
  border-radius: var(--radius-md);
  margin-bottom: var(--space-xs);
}

.portrait-banner {
  position: absolute;
  top: 5%;
  left: 60%;
  width: 35%;
  height: auto;
  object-fit: contain;
  z-index: 1;
}

.portrait-base {
  position: absolute;
  top: 10%;
  left: 10%;
  width: 80%;
  height: 80%;
  object-fit: contain;
}

.base-stats {
  padding: var(--space-sm) 0;
  border-top: 1px solid var(--color-border);
  border-bottom: 1px solid var(--color-border);
  margin-bottom: var(--space-md);
}

.tier-display {
  font-size: 1.5rem;
  margin-right: var(--space-xs);
}

.tier-label {
  color: var(--color-text-muted);
  font-size: 0.85rem;
}

.resources-header {
  margin-top: var(--space-md);
  margin-bottom: var(--space-sm);
  padding-top: var(--space-sm);
  border-top: 1px solid var(--color-border);
}

.resources-header h4 {
  color: var(--color-gold);
  margin: 0;
  font-size: 0.95rem;
}

.resource-row {
  padding: var(--space-xs) 0;
}

.resource-value {
  font-size: 1.2rem;
  font-weight: 700;
}

.resource-value.gold {
  color: #FFD700;
}

.resource-value.lumber {
  color: #8B4513;
}

.resource-value.oil {
  color: #1a1a2e;
  text-shadow: 0 0 2px #fff;
}

.resources-hidden {
  padding: var(--space-md);
  text-align: center;
  background: rgba(100, 100, 100, 0.1);
  border-radius: var(--radius-sm);
  margin-top: var(--space-md);
}

.resources-hidden .text-small {
  display: block;
  font-size: 0.75rem;
  color: var(--color-text-muted);
  margin-top: var(--space-xs);
}

.base-actions,
.base-actions-locked {
  padding-top: var(--space-sm);
  border-top: 1px solid var(--color-border);
  margin-top: var(--space-sm);
}

.actions-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--space-sm);
}

.actions-header h4 {
  margin: 0;
  color: var(--color-gold);
  font-size: 0.9rem;
}

.action-counter {
  font-size: 0.75rem;
  color: var(--color-text-muted);
  background: rgba(100, 100, 100, 0.2);
  padding: 2px 8px;
  border-radius: var(--radius-sm);
}

/* Pending Orders */
.pending-orders {
  background: rgba(201, 162, 39, 0.1);
  border: 1px solid rgba(201, 162, 39, 0.3);
  border-radius: var(--radius-sm);
  padding: var(--space-sm);
  margin-bottom: var(--space-sm);
}

.pending-orders-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--space-xs);
}

.pending-label {
  font-size: 0.75rem;
  font-weight: 600;
  color: var(--color-gold);
  text-transform: uppercase;
}

.cancel-btn {
  font-size: 0.7rem;
  background: rgba(200, 50, 50, 0.2);
  border: 1px solid rgba(200, 50, 50, 0.5);
  color: #e85050;
  padding: 2px 6px;
  border-radius: var(--radius-sm);
  cursor: pointer;
}

.cancel-btn:hover {
  background: rgba(200, 50, 50, 0.4);
}

.pending-order-item {
  display: flex;
  align-items: center;
  gap: var(--space-xs);
  padding: var(--space-xs) 0;
  font-size: 0.85rem;
  border-bottom: 1px solid rgba(201, 162, 39, 0.2);
}

.pending-order-item:last-child {
  border-bottom: none;
}

.order-number {
  color: var(--color-text-muted);
  min-width: 18px;
}

.order-type {
  color: var(--color-text-primary);
  font-weight: 500;
  text-transform: capitalize;
}

.order-preview {
  color: var(--color-gold);
  font-size: 0.8rem;
  margin-left: auto;
}

.order-preview.deprecated {
  color: var(--color-text-muted);
  font-style: italic;
  font-size: 0.7rem;
}

.next-turn-badge {
  font-size: 0.6rem;
  padding: 1px 4px;
  background: rgba(100, 150, 255, 0.2);
  border: 1px solid rgba(100, 150, 255, 0.4);
  border-radius: 3px;
  color: #88aaff;
  margin-left: 4px;
  text-transform: uppercase;
}

/* Harvest Info (Automatic - not an action) */
.harvest-info {
  background: linear-gradient(135deg, rgba(76, 175, 80, 0.15), rgba(56, 142, 60, 0.1));
  border: 1px solid rgba(76, 175, 80, 0.3);
  border-radius: var(--radius-sm);
  padding: var(--space-sm);
  margin-bottom: var(--space-sm);
}

.harvest-info-header {
  display: flex;
  align-items: center;
  gap: var(--space-xs);
  margin-bottom: var(--space-xs);
}

.harvest-icon {
  font-size: 1rem;
}

.harvest-label {
  font-size: 0.8rem;
  font-weight: 600;
  color: var(--color-text-primary);
}

.harvest-auto-badge {
  font-size: 0.6rem;
  padding: 1px 4px;
  background: rgba(76, 175, 80, 0.3);
  border: 1px solid rgba(76, 175, 80, 0.5);
  border-radius: 3px;
  color: #88cc88;
  text-transform: uppercase;
  margin-left: auto;
}

.harvest-preview {
  display: flex;
  gap: var(--space-sm);
  font-size: 0.85rem;
}

.harvest-yield {
  font-weight: 500;
}

.harvest-yield.gold { color: #ffd700; }
.harvest-yield.lumber { color: #8b6914; }
.harvest-yield.oil { color: #4a90d9; }

.no-yield {
  color: var(--color-text-muted);
  font-style: italic;
  font-size: 0.8rem;
}

/* Action Buttons */
.available-actions {
  display: flex;
  flex-direction: column;
  gap: var(--space-xs);
}

.action-btn {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  padding: var(--space-sm) var(--space-md);
  background: linear-gradient(135deg, rgba(60, 60, 60, 0.9), rgba(40, 40, 40, 0.9));
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  color: var(--color-text-primary);
  cursor: pointer;
  transition: all 0.2s ease;
}

.action-btn:hover:not(:disabled) {
  background: linear-gradient(135deg, rgba(80, 80, 80, 0.9), rgba(60, 60, 60, 0.9));
  border-color: var(--color-gold-dark);
}

.action-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.action-icon {
  font-size: 1.2rem;
}

.action-name {
  font-weight: 600;
}

.action-preview {
  margin-left: auto;
  font-size: 0.8rem;
  color: var(--color-gold);
}

.action-cost {
  margin-left: auto;
  font-size: 0.8rem;
  color: #e85050;
}

/* Expand Mode */
.expand-mode-active {
  background: rgba(255, 200, 0, 0.15);
  border: 1px solid rgba(255, 200, 0, 0.5);
  border-radius: var(--radius-sm);
  padding: var(--space-sm);
}

.expand-mode-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--space-xs);
}

.expand-mode-label {
  font-weight: 600;
  color: var(--color-gold);
  font-size: 0.9rem;
}

.cancel-expand-btn {
  font-size: 0.7rem;
  background: rgba(200, 50, 50, 0.2);
  border: 1px solid rgba(200, 50, 50, 0.5);
  color: #e85050;
  padding: 2px 8px;
  border-radius: var(--radius-sm);
  cursor: pointer;
}

.cancel-expand-btn:hover {
  background: rgba(200, 50, 50, 0.4);
}

.expand-mode-info {
  font-size: 0.75rem;
}

/* Commerce Mode */
.commerce-btn .action-cost {
  font-size: 0.7rem;
  color: var(--color-text-muted);
}

.commerce-mode-active {
  background: rgba(100, 200, 255, 0.15);
  border: 1px solid rgba(100, 200, 255, 0.5);
  border-radius: var(--radius-sm);
  padding: var(--space-sm);
}

.commerce-mode-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--space-sm);
}

.commerce-mode-label {
  font-weight: 600;
  color: var(--color-gold);
  font-size: 0.9rem;
}

.cancel-commerce-btn {
  font-size: 0.7rem;
  background: rgba(200, 50, 50, 0.2);
  border: 1px solid rgba(200, 50, 50, 0.5);
  color: #e85050;
  padding: 2px 8px;
  border-radius: var(--radius-sm);
  cursor: pointer;
}

.cancel-commerce-btn:hover {
  background: rgba(200, 50, 50, 0.4);
}

.commerce-step {
  display: flex;
  flex-direction: column;
  gap: var(--space-xs);
}

.commerce-step-label {
  font-size: 0.8rem;
  color: var(--color-text-secondary);
}

.commerce-options {
  display: flex;
  gap: var(--space-xs);
  flex-wrap: wrap;
}

.commerce-option-btn {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 6px 10px;
  background: rgba(100, 200, 255, 0.2);
  border: 1px solid rgba(100, 200, 255, 0.5);
  border-radius: var(--radius-sm);
  color: var(--color-text-primary);
  font-size: 0.85rem;
  cursor: pointer;
  transition: all 0.2s ease;
}

.commerce-option-btn:hover {
  background: rgba(100, 200, 255, 0.4);
  border-color: rgba(100, 200, 255, 0.8);
}

.commerce-option-btn .option-icon {
  font-size: 1rem;
}

.commerce-option-btn .option-amount {
  font-size: 0.75rem;
  color: var(--color-text-muted);
}

.commerce-back-btn {
  align-self: flex-start;
  margin-top: var(--space-xs);
  font-size: 0.75rem;
  background: transparent;
  border: none;
  color: var(--color-text-muted);
  cursor: pointer;
  padding: 2px 6px;
}

.commerce-back-btn:hover {
  color: var(--color-text-primary);
}

/* Upgrade Base Action */
.upgrade-btn {
  background: linear-gradient(135deg, rgba(255, 215, 0, 0.2), rgba(255, 140, 0, 0.2));
  border-color: rgba(255, 200, 0, 0.5);
}

.upgrade-btn:hover:not(:disabled) {
  background: linear-gradient(135deg, rgba(255, 215, 0, 0.3), rgba(255, 140, 0, 0.3));
  border-color: rgba(255, 200, 0, 0.8);
}

.upgrade-btn .action-cost {
  font-size: 0.7rem;
  color: var(--color-text-muted);
}

.upgrade-maxed {
  display: flex;
  align-items: center;
  gap: var(--space-xs);
  padding: var(--space-xs) var(--space-sm);
  font-size: 0.8rem;
  background: rgba(255, 215, 0, 0.1);
  border-radius: var(--radius-sm);
  border: 1px dashed rgba(255, 200, 0, 0.3);
}

.upgrade-maxed .action-icon {
  font-size: 1rem;
}

/* Rest Unit Action */
.rest-btn {
  background: linear-gradient(135deg, rgba(100, 200, 255, 0.2), rgba(50, 150, 220, 0.2));
  border-color: rgba(100, 200, 255, 0.5);
}

.rest-btn:hover:not(:disabled) {
  background: linear-gradient(135deg, rgba(100, 200, 255, 0.3), rgba(50, 150, 220, 0.3));
  border-color: rgba(100, 200, 255, 0.8);
}

.rest-mode-active {
  background: rgba(100, 200, 255, 0.1);
  border: 1px solid rgba(100, 200, 255, 0.3);
  border-radius: var(--radius-sm);
  padding: var(--space-sm);
}

.rest-mode-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--space-sm);
}

.rest-mode-label {
  font-weight: 600;
  font-size: 0.85rem;
  color: var(--color-text-primary);
}

.cancel-rest-btn {
  background: transparent;
  border: 1px solid rgba(200, 100, 100, 0.5);
  color: rgba(255, 150, 150, 0.8);
  padding: 2px 8px;
  border-radius: var(--radius-sm);
  font-size: 0.75rem;
  cursor: pointer;
  transition: all 0.2s ease;
}

.cancel-rest-btn:hover {
  background: rgba(200, 100, 100, 0.2);
  border-color: rgba(200, 100, 100, 0.8);
}

.restable-units-list {
  display: flex;
  flex-direction: column;
  gap: var(--space-xs);
  max-height: 150px;
  overflow-y: auto;
}

.restable-unit-item {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  padding: var(--space-xs) var(--space-sm);
  border-radius: var(--radius-sm);
  font-size: 0.8rem;
  transition: all 0.2s ease;
}

.restable-unit-item.can-rest {
  background: rgba(100, 200, 100, 0.1);
  border: 1px solid rgba(100, 200, 100, 0.3);
  cursor: pointer;
}

.restable-unit-item.can-rest:hover {
  background: rgba(100, 200, 100, 0.2);
  border-color: rgba(100, 200, 100, 0.6);
}

.restable-unit-item.cannot-rest {
  background: rgba(150, 150, 150, 0.1);
  border: 1px solid rgba(150, 150, 150, 0.2);
  opacity: 0.6;
  cursor: not-allowed;
}

.restable-unit-item .unit-name {
  flex: 1;
  font-weight: 500;
}

.restable-unit-item .unit-hp {
  color: var(--color-text-muted);
  font-size: 0.75rem;
}

.restable-unit-item .heal-preview {
  color: #00cc66;
  font-weight: 600;
}

.restable-unit-item .cannot-reason {
  color: rgba(200, 150, 150, 0.8);
  font-size: 0.7rem;
  font-style: italic;
}

/* Expand target hex highlighting */
.hex-group.expand-target {
  cursor: pointer;
}

.expand-highlight {
  pointer-events: none;
  animation: expand-pulse 1.5s ease-in-out infinite;
}

@keyframes expand-pulse {
  0%, 100% { opacity: 0.8; }
  50% { opacity: 1; }
}

/* Pending resource display */
.pending-resource {
  font-weight: 600;
  margin-left: var(--space-xs);
}

.pending-resource.positive {
  color: #00cc66;
}

.pending-resource.negative {
  color: #ff6b6b;
}

.coming-soon {
  font-size: 0.75rem;
  text-align: center;
  padding: var(--space-xs);
}

/* Combat Lock */
.actions-locked-combat {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: var(--space-md);
  background: rgba(200, 50, 50, 0.15);
  border: 1px solid rgba(200, 50, 50, 0.4);
  border-radius: var(--radius-sm);
  margin-bottom: var(--space-sm);
}

.combat-lock-icon {
  font-size: 2rem;
  margin-bottom: var(--space-xs);
}

.combat-lock-message {
  font-weight: 700;
  font-size: 1rem;
  color: #ff6b6b;
}

.combat-lock-reason {
  font-size: 0.8rem;
  color: var(--color-text-muted);
  margin-top: var(--space-xs);
}

/* Initiative Lock (not this faction's turn) */
.actions-locked-initiative {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: var(--space-md);
  background: rgba(100, 100, 150, 0.15);
  border: 1px solid rgba(100, 100, 150, 0.4);
  border-radius: var(--radius-sm);
  margin-bottom: var(--space-sm);
}

.initiative-lock-icon {
  font-size: 2rem;
  margin-bottom: var(--space-xs);
}

.initiative-lock-message {
  font-weight: 700;
  font-size: 1rem;
  color: #8888bb;
}

.initiative-lock-reason {
  font-size: 0.75rem;
  color: var(--color-text-muted);
  margin-top: var(--space-xs);
  text-align: center;
}

.no-actions-left {
  text-align: center;
  padding: var(--space-sm);
  font-size: 0.85rem;
}

.locked-notice {
  text-align: center;
  padding: var(--space-sm);
  font-size: 0.85rem;
}

/* Expansion markers on map */
.expansion-group {
  pointer-events: none;
}

.expansion-building {
  filter: drop-shadow(2px 2px 3px rgba(0,0,0,0.5));
}

/* Expansion connection lines from base */
.expansion-connection-lines {
  pointer-events: none;
}

.expansion-line {
  filter: drop-shadow(0 0 2px rgba(0,0,0,0.5));
}

/* Clickable base link in hex info */
.base-link {
  cursor: pointer;
  transition: background 0.2s ease;
  padding: var(--space-xs) var(--space-sm);
  margin: 0 calc(-1 * var(--space-sm));
  border-radius: var(--radius-sm);
}

.base-link:hover {
  background: rgba(201, 162, 39, 0.15);
}

.base-link .view-arrow {
  margin-left: auto;
}

/* Clickable base on map */
.clickable-base .base-building.clickable,
.clickable-base .base-name.clickable {
  cursor: pointer;
  pointer-events: all;
}

.clickable-base .base-building.clickable:hover {
  filter: brightness(1.2) drop-shadow(0 0 8px rgba(255, 215, 0, 0.5));
}

.clickable-base .base-name.clickable:hover {
  fill: #FFF8DC;
}

/* ==================== Build Unit Modal ==================== */
.build-modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.85);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 9999;
  animation: fadeIn 0.2s ease;
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

.build-modal {
  background: linear-gradient(180deg, #1a1a2e 0%, #16213e 100%);
  border: 2px solid var(--color-gold-dark);
  border-radius: var(--radius-lg);
  box-shadow: 0 0 60px rgba(0, 0, 0, 0.8), 0 0 30px rgba(201, 162, 39, 0.2);
  max-width: 900px;
  width: 95%;
  max-height: 85vh;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  animation: slideUp 0.3s ease;
}

@keyframes slideUp {
  from { 
    opacity: 0;
    transform: translateY(30px);
  }
  to { 
    opacity: 1;
    transform: translateY(0);
  }
}

.build-modal-header {
  display: flex;
  align-items: center;
  gap: var(--space-md);
  padding: var(--space-md) var(--space-lg);
  background: linear-gradient(90deg, rgba(201, 162, 39, 0.15) 0%, transparent 100%);
  border-bottom: 1px solid rgba(201, 162, 39, 0.3);
  position: relative;
}

.build-modal-header h2 {
  margin: 0;
  font-family: var(--font-display);
  font-size: 1.4rem;
  color: var(--color-gold);
}

.build-modal-subtitle {
  font-size: 0.9rem;
  color: var(--color-text-muted);
}

.close-modal-btn {
  position: absolute;
  right: var(--space-md);
  top: 50%;
  transform: translateY(-50%);
  background: transparent;
  border: 1px solid rgba(200, 100, 100, 0.4);
  color: rgba(255, 150, 150, 0.8);
  width: 32px;
  height: 32px;
  border-radius: 50%;
  cursor: pointer;
  font-size: 1rem;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s ease;
}

.close-modal-btn:hover {
  background: rgba(200, 100, 100, 0.2);
  border-color: rgba(200, 100, 100, 0.6);
  color: #ff8888;
}

/* Food Status Bar */
.food-status-bar {
  padding: var(--space-sm) var(--space-lg);
  background: rgba(0, 0, 0, 0.3);
  border-bottom: 1px solid rgba(255, 255, 255, 0.05);
}

.food-info {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  margin-bottom: var(--space-xs);
}

.food-label {
  font-size: 0.85rem;
  color: var(--color-text-muted);
}

.food-value {
  font-weight: 600;
  color: var(--color-text-primary);
}

.food-value.food-capped {
  color: #ff6b6b;
}

.pending-builds {
  font-size: 0.8rem;
  color: var(--color-gold);
}

.food-bar {
  height: 6px;
  background: rgba(0, 0, 0, 0.4);
  border-radius: 3px;
  overflow: hidden;
}

.food-bar-fill {
  height: 100%;
  background: linear-gradient(90deg, #4ade80, #22c55e);
  transition: width 0.3s ease;
}

.food-bar-fill.food-capped {
  background: linear-gradient(90deg, #f87171, #ef4444);
}

.food-warning {
  margin-top: var(--space-xs);
  font-size: 0.8rem;
  color: #ff6b6b;
}

/* Resource Status Bar */
.resource-status-bar {
  display: flex;
  gap: var(--space-lg);
  padding: var(--space-sm) var(--space-lg);
  background: rgba(0, 0, 0, 0.2);
  border-bottom: 1px solid rgba(255, 255, 255, 0.05);
}

.resource-status-bar .resource-item {
  display: flex;
  align-items: center;
  gap: var(--space-xs);
}

.resource-status-bar .resource-icon {
  font-size: 1rem;
}

.resource-status-bar .resource-amount {
  font-weight: 600;
  color: var(--color-text-primary);
}

.resource-status-bar .pending-resource {
  font-size: 0.85rem;
}

.resource-status-bar .pending-resource.positive {
  color: #4ade80;
}

.resource-status-bar .pending-resource.negative {
  color: #f87171;
}

/* Unit Cards Grid */
.build-units-grid {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: var(--space-md);
  padding: var(--space-lg);
  overflow-y: auto;
  max-height: 60vh;
}

.build-unit-card {
  background: linear-gradient(180deg, rgba(30, 40, 60, 0.9) 0%, rgba(20, 30, 50, 0.95) 100%);
  border: 1px solid rgba(100, 120, 150, 0.3);
  border-radius: var(--radius-md);
  padding: var(--space-sm);
  cursor: pointer;
  transition: all 0.2s ease;
  display: flex;
  flex-direction: column;
  gap: var(--space-xs);
  position: relative;
  overflow: hidden;
}

.build-unit-card.can-build {
  border-color: rgba(201, 162, 39, 0.4);
}

.build-unit-card.can-build:hover {
  border-color: var(--color-gold);
  transform: translateY(-4px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.4), 0 0 20px rgba(201, 162, 39, 0.15);
}

.build-unit-card.cannot-build {
  opacity: 0.6;
  cursor: not-allowed;
  filter: grayscale(0.4);
}

.build-unit-card.tier-locked {
  opacity: 0.5;
  filter: grayscale(0.6);
}

/* Unit Card Image */
.unit-card-image {
  position: relative;
  width: 100%;
  aspect-ratio: 1;
  background: linear-gradient(135deg, rgba(0, 0, 0, 0.4) 0%, rgba(0, 0, 0, 0.6) 100%);
  border-radius: var(--radius-sm);
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: center;
}

.unit-card-image img {
  max-width: 90%;
  max-height: 90%;
  object-fit: contain;
  filter: drop-shadow(0 2px 4px rgba(0, 0, 0, 0.5));
}

.unit-card-locked-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 2rem;
}

/* Unit Card Name */
.unit-card-name {
  font-family: var(--font-display);
  font-size: 0.95rem;
  color: var(--color-text-primary);
  text-align: center;
  padding: var(--space-xs) 0;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.can-build .unit-card-name {
  color: var(--color-gold);
}

/* Unit Card Cost */
.unit-card-cost {
  display: flex;
  justify-content: center;
  gap: var(--space-sm);
  padding: var(--space-xs) 0;
}

.cost-item {
  display: flex;
  align-items: center;
  gap: 2px;
  font-size: 0.85rem;
  font-weight: 600;
}

.cost-item.gold { color: #ffd700; }
.cost-item.lumber { color: #8b4513; }
.cost-item.oil { color: #4a90d9; }

.cost-icon {
  font-size: 0.9rem;
}

/* Unit Card Stats */
.unit-card-stats {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 2px;
  background: rgba(0, 0, 0, 0.2);
  border-radius: var(--radius-sm);
  padding: var(--space-xs);
}

.unit-card-stats .stat-item {
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
  padding: 2px var(--space-xs);
  font-size: 0.7rem;
}

.unit-card-stats .stat-label {
  color: var(--color-text-muted);
  font-size: 0.7rem;
}

.unit-card-stats .stat-value {
  color: var(--color-text-primary);
  font-weight: 500;
  font-size: 0.7rem;
}

/* Category & Armor Row */
.unit-card-extras {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: var(--space-xs);
  padding: var(--space-xs) 0;
}

.category-badge {
  font-size: 0.65rem;
  padding: 2px 6px;
  background: rgba(100, 120, 150, 0.3);
  border-radius: 3px;
  color: var(--color-text-muted);
  text-transform: uppercase;
  letter-spacing: 0.03em;
}

.armor-info {
  display: flex;
  gap: 4px;
  font-size: 0.75rem;
}

.armor {
  display: flex;
  align-items: center;
  gap: 1px;
}

.armor.light { color: #87ceeb; }
.armor.heavy { color: #a0a0a0; }
.armor.natural { color: #90ee90; }

/* Tier Requirement */
.tier-requirement {
  text-align: center;
  font-size: 0.7rem;
  padding: 2px var(--space-xs);
  background: rgba(200, 100, 100, 0.2);
  border-radius: 3px;
  color: #ff8888;
}

.tier-requirement.met {
  background: rgba(100, 200, 100, 0.2);
  color: #88ff88;
}

/* Cannot Build Reasons */
.cannot-build-reasons {
  background: rgba(0, 0, 0, 0.3);
  border-radius: var(--radius-sm);
  padding: var(--space-xs);
  margin-top: auto;
}

.cannot-build-reasons .reason {
  font-size: 0.7rem;
  color: #ff8888;
  padding: 1px 0;
}

.cannot-build-reasons .more-reasons {
  font-size: 0.65rem;
  color: var(--color-text-muted);
  font-style: italic;
}

/* No Buildable Units */
.no-buildable-units {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: var(--space-md);
  padding: var(--space-2xl);
  color: var(--color-text-muted);
}

.no-buildable-units .empty-icon {
  font-size: 3rem;
  opacity: 0.5;
}

/* Build Button & Queued Indicator */
.build-btn {
  background: linear-gradient(135deg, rgba(139, 69, 19, 0.3), rgba(101, 67, 33, 0.3));
  border-color: rgba(139, 90, 43, 0.5);
}

.build-btn:hover:not(:disabled) {
  background: linear-gradient(135deg, rgba(139, 69, 19, 0.4), rgba(101, 67, 33, 0.4));
  border-color: rgba(160, 100, 50, 0.8);
}

.build-queued {
  display: flex;
  align-items: center;
  gap: var(--space-xs);
  padding: var(--space-xs) var(--space-sm);
  font-size: 0.8rem;
  background: rgba(139, 69, 19, 0.1);
  border-radius: var(--radius-sm);
  border: 1px dashed rgba(139, 90, 43, 0.3);
}

/* Map Display Toggles */
.map-toggles {
  display: flex;
  gap: var(--space-sm);
  margin-left: var(--space-md);
}

.toggle-btn {
  padding: var(--space-xs) var(--space-sm);
  background: rgba(139, 69, 19, 0.2);
  border: 1px solid rgba(139, 69, 19, 0.4);
  border-radius: var(--radius-sm);
  color: var(--color-text-secondary);
  cursor: pointer;
  font-size: 0.8rem;
  transition: all 0.2s ease;
}

.toggle-btn:hover {
  background: rgba(139, 69, 19, 0.3);
  border-color: rgba(139, 69, 19, 0.6);
}

.toggle-btn.active {
  background: rgba(139, 69, 19, 0.4);
  border-color: #8B4513;
  color: var(--color-text);
}

/* Caravan Button */
.caravan-btn {
  background: linear-gradient(135deg, rgba(139, 69, 19, 0.3), rgba(160, 82, 45, 0.2));
  border: 1px solid rgba(139, 69, 19, 0.5);
}

.caravan-btn:hover:not(:disabled) {
  background: linear-gradient(135deg, rgba(139, 69, 19, 0.4), rgba(160, 82, 45, 0.3));
  border-color: #8B4513;
}

/* Caravan Mode Active */
.caravan-mode-active {
  background: rgba(139, 69, 19, 0.15);
  border: 1px solid rgba(139, 69, 19, 0.4);
  border-radius: var(--radius-md);
  padding: var(--space-sm);
}

.caravan-mode-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--space-sm);
  padding-bottom: var(--space-xs);
  border-bottom: 1px solid rgba(139, 69, 19, 0.3);
}

.caravan-mode-label {
  font-weight: 600;
  color: #CD853F;
}

.cancel-mode-btn {
  background: rgba(180, 80, 80, 0.3);
  border: 1px solid rgba(180, 80, 80, 0.5);
  color: #ff8888;
  padding: 2px 8px;
  border-radius: var(--radius-sm);
  cursor: pointer;
  font-size: 0.9rem;
}

.cancel-mode-btn:hover {
  background: rgba(180, 80, 80, 0.5);
}

/* Caravan Destination Selection */
.caravan-dest-selection {
  margin-top: var(--space-sm);
}

.caravan-step-label {
  font-size: 0.85rem;
  color: var(--color-text-secondary);
  margin-bottom: var(--space-xs);
}

.caravan-targets-list {
  display: flex;
  flex-direction: column;
  gap: var(--space-xs);
  max-height: 200px;
  overflow-y: auto;
}

.caravan-target-item {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  padding: var(--space-xs) var(--space-sm);
  background: rgba(0, 0, 0, 0.2);
  border-radius: var(--radius-sm);
}

.caravan-target-item.has-existing {
  opacity: 0.5;
}

.target-name {
  flex: 1;
  font-size: 0.85rem;
}

.target-buttons {
  display: flex;
  gap: var(--space-xs);
}

.target-select-btn {
  padding: 2px 8px;
  font-size: 0.75rem;
  border-radius: var(--radius-sm);
  cursor: pointer;
  transition: all 0.2s ease;
}

.target-select-btn.land {
  background: rgba(139, 69, 19, 0.3);
  border: 1px solid rgba(139, 69, 19, 0.5);
  color: #CD853F;
}

.target-select-btn.land:hover:not(:disabled) {
  background: rgba(139, 69, 19, 0.5);
}

.target-select-btn.sea {
  background: rgba(68, 136, 204, 0.3);
  border: 1px solid rgba(68, 136, 204, 0.5);
  color: #6699cc;
}

.target-select-btn.sea:hover:not(:disabled) {
  background: rgba(68, 136, 204, 0.5);
}

.target-select-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.existing-badge {
  font-size: 0.7rem;
  color: #888;
  padding: 1px 4px;
  background: rgba(128, 128, 128, 0.2);
  border-radius: 3px;
}

.no-targets {
  font-size: 0.8rem;
  color: var(--color-text-muted);
  text-align: center;
  padding: var(--space-sm);
}

/* Caravan Path Tracing */
.caravan-path-tracing {
  margin-top: var(--space-sm);
}

.caravan-instructions {
  font-size: 0.8rem;
  color: var(--color-text-muted);
  margin-bottom: var(--space-sm);
}

.caravan-instructions p {
  margin: 2px 0;
}

.caravan-type-info {
  margin-top: var(--space-xs);
}

.caravan-type-undecided {
  font-style: italic;
  color: var(--color-text-muted);
}

.caravan-error {
  background: rgba(220, 53, 69, 0.15);
  border: 1px solid rgba(220, 53, 69, 0.4);
  border-radius: 4px;
  padding: var(--space-xs) var(--space-sm);
  margin-bottom: var(--space-sm);
  font-size: 0.8rem;
  color: #ff6b6b;
}

.caravan-dest-info {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  margin-bottom: var(--space-sm);
}

.dest-label {
  font-size: 0.8rem;
  color: var(--color-text-muted);
}

.dest-name {
  font-weight: 600;
  flex: 1;
}

.caravan-type-badge {
  font-size: 0.7rem;
  padding: 2px 6px;
  border-radius: 3px;
}

.caravan-type-badge.land {
  background: rgba(139, 69, 19, 0.3);
  color: #CD853F;
}

.caravan-type-badge.sea {
  background: rgba(68, 136, 204, 0.3);
  color: #6699cc;
}

.caravan-path-info {
  display: flex;
  flex-direction: column;
  gap: var(--space-xs);
  padding: var(--space-xs) var(--space-sm);
  background: rgba(0, 0, 0, 0.2);
  border-radius: var(--radius-sm);
  margin-bottom: var(--space-sm);
}

.path-length, .path-cost {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  font-size: 0.85rem;
}

.path-length .label, .path-cost .label {
  color: var(--color-text-muted);
  min-width: 40px;
}

.path-cost.threshold {
  animation: cost-pulse 0.5s ease;
}

@keyframes cost-pulse {
  0%, 100% { background: rgba(0, 0, 0, 0.2); }
  50% { background: rgba(255, 200, 0, 0.3); }
}

.cost-values {
  display: flex;
  gap: var(--space-sm);
}

.cost-lumber {
  color: #8B4513;
}

.cost-oil {
  color: #4a4a4a;
}

.cost-tier {
  font-size: 0.7rem;
  color: var(--color-text-muted);
}

.caravan-path-controls {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  margin-bottom: var(--space-xs);
}

.undo-path-btn {
  padding: 3px 8px;
  font-size: 0.75rem;
  background: rgba(100, 100, 100, 0.3);
  border: 1px solid rgba(100, 100, 100, 0.5);
  color: var(--color-text-secondary);
  border-radius: var(--radius-sm);
  cursor: pointer;
}

.undo-path-btn:hover:not(:disabled) {
  background: rgba(100, 100, 100, 0.5);
}

.undo-path-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.path-hint {
  font-size: 0.75rem;
  color: var(--color-text-muted);
  font-style: italic;
}

.valid-hexes-count {
  font-size: 0.8rem;
  color: var(--color-text-secondary);
}

.dest-reachable {
  color: #00ff64;
  font-weight: 600;
}

.caravan-destinations {
  margin-top: var(--space-xs);
  font-size: 0.75rem;
}

.dest-list-label {
  color: var(--color-text-muted);
}

.dest-list {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  margin-top: 4px;
}

.dest-chip {
  background: rgba(0, 255, 100, 0.15);
  border: 1px solid rgba(0, 255, 100, 0.4);
  border-radius: 3px;
  padding: 2px 6px;
  color: #00ff64;
  font-size: 0.7rem;
}

.no-dests {
  color: var(--color-text-muted);
  font-style: italic;
}

/* Caravan Routes on Map */
.caravan-routes {
  pointer-events: none;
}

.caravan-route-line {
  filter: drop-shadow(0 0 3px rgba(0, 0, 0, 0.5));
}

.caravan-marker {
  filter: drop-shadow(0 0 2px rgba(0, 0, 0, 0.5));
}

.caravan-path-trace .caravan-trace-line {
  filter: drop-shadow(0 0 4px rgba(255, 200, 100, 0.5));
}

/* Hex highlights for caravan mode */
.hex-group.caravan-path .hex-fill {
  filter: brightness(1.2);
}

.hex-group.caravan-valid:not(.caravan-path) {
  cursor: pointer;
}

.hex-group.caravan-dest {
  cursor: pointer;
}

.caravan-path-highlight {
  pointer-events: none;
}

.caravan-valid-highlight {
  pointer-events: none;
  animation: caravan-valid-pulse 1.5s ease-in-out infinite;
}

@keyframes caravan-valid-pulse {
  0%, 100% { opacity: 0.7; }
  50% { opacity: 1; }
}

/* ==================== Ranged Fire Styles ==================== */

.btn-siege {
  background: linear-gradient(135deg, rgba(255, 100, 50, 0.3), rgba(200, 50, 0, 0.2));
  border: 1px solid rgba(255, 100, 50, 0.5);
}

.btn-siege:hover:not(:disabled) {
  background: linear-gradient(135deg, rgba(255, 100, 50, 0.5), rgba(200, 50, 0, 0.4));
  border-color: rgba(255, 100, 50, 0.8);
}

.rangedfire-target-highlight {
  pointer-events: none;
  animation: rangedfire-pulse 0.8s ease-in-out infinite;
}

.rangedfire-origin-highlight {
  pointer-events: none;
}

@keyframes rangedfire-pulse {
  0%, 100% { opacity: 0.6; stroke-width: 3px; }
  50% { opacity: 1; stroke-width: 5px; }
}

.hex-group.rangedfire-target {
  cursor: crosshair;
}

.current-order.rangedfire-order {
  border-left: 3px solid #ff4500;
  padding-left: 8px;
}

.current-order.fast-travel-order {
  border-left: 3px solid #ffaa00;
  padding-left: 8px;
  background: rgba(255, 170, 0, 0.1);
  border-color: rgba(255, 170, 0, 0.3);
}

/* Fast Travel Button */
.btn-fast-travel {
  background: linear-gradient(135deg, rgba(255, 170, 0, 0.3), rgba(255, 140, 0, 0.2));
  border: 1px solid rgba(255, 170, 0, 0.5);
}

.btn-fast-travel:hover:not(:disabled) {
  background: linear-gradient(135deg, rgba(255, 170, 0, 0.4), rgba(255, 140, 0, 0.3));
  border-color: #ffaa00;
}

/* Fast Travel Mode UI */
.fast-travel-mode-ui {
  margin-top: var(--space-md);
  padding: var(--space-sm);
  background: rgba(255, 170, 0, 0.1);
  border: 1px solid rgba(255, 170, 0, 0.4);
  border-radius: var(--radius-sm);
}

.fast-travel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--space-sm);
}

.fast-travel-label {
  font-weight: 600;
  color: #ffaa00;
}

.fast-travel-info {
  font-size: 0.85rem;
}

.fast-travel-instructions {
  color: var(--color-text-muted);
  margin: 0 0 var(--space-xs) 0;
}

.fast-travel-stats {
  color: #ffcc00;
  font-weight: 500;
}

.fast-travel-error {
  background: rgba(220, 53, 69, 0.15);
  border: 1px solid rgba(220, 53, 69, 0.4);
  border-radius: 4px;
  padding: var(--space-xs) var(--space-sm);
  margin: var(--space-sm) 0;
  font-size: 0.8rem;
  color: #ff6b6b;
}

.fast-travel-controls {
  display: flex;
  gap: var(--space-sm);
  margin-top: var(--space-sm);
}

.fast-travel-controls .btn {
  flex: 1;
  min-width: 0;  /* Allow buttons to shrink below content size */
  padding: var(--space-xs) var(--space-sm);
}

.fast-travel-path-lines {
  pointer-events: none;
}

.fast-travel-line {
  filter: drop-shadow(0 0 3px rgba(255, 170, 0, 0.5));
}

/* Fast Travel Hex Highlighting */
.hex-group.fast-travel-origin polygon.hex-background {
  stroke: #ffaa00 !important;
  stroke-width: 4px !important;
}

.hex-group.fast-travel-path polygon.hex-background {
  stroke: #ffcc00 !important;
  stroke-width: 3px !important;
}

.hex-group.fast-travel-valid:not(.fast-travel-path) polygon.hex-background {
  stroke: rgba(255, 170, 0, 0.6) !important;
  stroke-width: 2px !important;
  stroke-dasharray: 5,3 !important;
}

/* Send Resources Button */
.send-btn {
  background: linear-gradient(135deg, rgba(70, 130, 180, 0.3), rgba(65, 105, 225, 0.2));
  border: 1px solid rgba(70, 130, 180, 0.5);
}

.send-btn:hover:not(:disabled) {
  background: linear-gradient(135deg, rgba(70, 130, 180, 0.4), rgba(65, 105, 225, 0.3));
  border-color: #4682B4;
}

/* Send Resources Mode Active */
.send-mode-active {
  background: rgba(70, 130, 180, 0.15);
  border: 1px solid rgba(70, 130, 180, 0.4);
  border-radius: var(--radius-md);
  padding: var(--space-sm);
}

.send-mode-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--space-sm);
  padding-bottom: var(--space-xs);
  border-bottom: 1px solid rgba(70, 130, 180, 0.3);
}

.send-mode-label {
  font-weight: 600;
  color: #87CEEB;
}

/* Send Destination Selection */
.send-dest-selection {
  margin-top: var(--space-sm);
}

.send-step-label {
  font-size: 0.85rem;
  color: var(--color-text-secondary);
  margin-bottom: var(--space-xs);
}

.send-targets-list {
  display: flex;
  flex-direction: column;
  gap: var(--space-xs);
  max-height: 150px;
  overflow-y: auto;
}

.send-target-item {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  padding: var(--space-xs) var(--space-sm);
  background: rgba(0, 0, 0, 0.2);
  border-radius: var(--radius-sm);
  cursor: pointer;
  transition: all 0.2s ease;
}

.send-target-item:hover {
  background: rgba(70, 130, 180, 0.3);
}

.caravan-length {
  font-size: 0.75rem;
  color: var(--color-text-muted);
}

/* Send Amounts Selection */
.send-amounts-selection {
  margin-top: var(--space-sm);
}

.send-dest-info {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  margin-bottom: var(--space-sm);
}

.send-amounts-form {
  display: flex;
  flex-direction: column;
  gap: var(--space-sm);
  padding: var(--space-sm);
  background: rgba(0, 0, 0, 0.2);
  border-radius: var(--radius-sm);
  margin-bottom: var(--space-sm);
}

.send-amount-row {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
}

.resource-icon {
  font-size: 1rem;
  width: 20px;
}

.resource-label {
  font-size: 0.8rem;
  color: var(--color-text-secondary);
  min-width: 50px;
}

.amount-control {
  display: flex;
  align-items: center;
  gap: var(--space-xs);
}

.amount-btn {
  width: 24px;
  height: 24px;
  border-radius: 4px;
  border: 1px solid rgba(70, 130, 180, 0.5);
  background: rgba(70, 130, 180, 0.2);
  color: var(--color-text);
  font-size: 1rem;
  font-weight: bold;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.15s ease;
}

.amount-btn:hover:not(:disabled) {
  background: rgba(70, 130, 180, 0.4);
  border-color: #4682B4;
}

.amount-btn:disabled {
  opacity: 0.3;
  cursor: not-allowed;
}

.amount-btn.minus {
  color: #ff8888;
}

.amount-btn.plus {
  color: #88ff88;
}

.amount-value {
  font-size: 1rem;
  font-weight: 600;
  min-width: 30px;
  text-align: center;
  font-variant-numeric: tabular-nums;
}

.max-available {
  font-size: 0.75rem;
  color: var(--color-text-muted);
  margin-left: var(--space-xs);
}

.no-resources {
  font-size: 0.8rem;
  color: var(--color-text-muted);
  text-align: center;
  padding: var(--space-sm);
}

.send-summary {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  margin-bottom: var(--space-sm);
  padding: var(--space-xs) var(--space-sm);
  background: rgba(0, 0, 0, 0.15);
  border-radius: var(--radius-sm);
}

.summary-label {
  font-size: 0.8rem;
  color: var(--color-text-secondary);
}

.summary-values {
  display: flex;
  gap: var(--space-sm);
  font-size: 0.9rem;
}

.send-actions {
  display: flex;
  gap: var(--space-sm);
}

.send-confirm-btn {
  flex: 1;
  padding: var(--space-xs) var(--space-sm);
  background: rgba(70, 180, 130, 0.3);
  border: 1px solid rgba(70, 180, 130, 0.5);
  color: #90EE90;
  border-radius: var(--radius-sm);
  cursor: pointer;
  font-size: 0.85rem;
}

.send-confirm-btn:hover:not(:disabled) {
  background: rgba(70, 180, 130, 0.5);
}

.send-confirm-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.send-back-btn {
  padding: var(--space-xs) var(--space-sm);
  background: rgba(100, 100, 100, 0.3);
  border: 1px solid rgba(100, 100, 100, 0.5);
  color: var(--color-text-secondary);
  border-radius: var(--radius-sm);
  cursor: pointer;
  font-size: 0.85rem;
}

.send-back-btn:hover {
  background: rgba(100, 100, 100, 0.5);
}
</style>
