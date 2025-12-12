/**
 * Client-side Movement Validation for Tides of Darkness
 * 
 * Mirrors the server-side validation logic but runs in the browser
 * for immediate feedback as players build movement paths.
 * 
 * Note: Client validation is advisory - server makes final decisions,
 * especially for cross-faction hexside conflicts.
 */

// =============================================================================
// CONSTANTS (matching server-side reference_data.py)
// =============================================================================

export const HEXSIDE_LIMITS = {
  'C': 99,  // Clear - unlimited
  'F': 4,   // Forest
  'M': 2,   // Mountain
  'S': 2,   // Swamp
  'I': 0,   // Impassable
  'X': 0,   // Impassable
  'N': 0,   // Coastal Mountain
  'K': 4,   // Coastal
  'O': 99,  // Ocean - unlimited for sea units
  'Q': 2,   // Coastal Forest
  'R': 4,   // River
  'W': 4,   // Fortification
}

export const ROAD_BONUS = 2
export const COASTAL_COMBAT_LIMIT = 2

// =============================================================================
// MOVE RESULT ENUM
// =============================================================================

export const MoveResult = {
  SUCCESS: 'success',
  INVALID_HEX: 'invalid_hex',
  NOT_ADJACENT: 'not_adjacent',
  NO_MOVEMENT_POINTS: 'no_movement_points',
  IMPASSABLE_TERRAIN: 'impassable_terrain',
  IMPASSABLE_HEXSIDE: 'impassable_hexside',
  WRONG_UNIT_TYPE: 'wrong_unit_type',
  ENEMY_HEXSIDE: 'enemy_hexside',
  SIEGE_RESTRICTION: 'siege_restriction',
  CONTINUOUS_MOVE_BLOCKED: 'continuous_move_blocked',
  COMBAT_ENTRY_BLOCKED: 'combat_entry_blocked',
  ROAD_MOVE_INTO_COMBAT: 'road_move_into_combat',
  PATH_CONTINUES_PAST_COMBAT: 'path_continues_past_combat',
  EXCEEDS_HEXSIDE_LIMIT: 'exceeds_hexside_limit',
}

// Human-readable messages for each result
export const MoveResultMessages = {
  [MoveResult.SUCCESS]: 'Move is valid',
  [MoveResult.INVALID_HEX]: 'Invalid hex',
  [MoveResult.NOT_ADJACENT]: 'Hex is not adjacent',
  [MoveResult.NO_MOVEMENT_POINTS]: 'No movement points remaining',
  [MoveResult.IMPASSABLE_TERRAIN]: 'Terrain is impassable',
  [MoveResult.IMPASSABLE_HEXSIDE]: 'Cannot cross this hexside',
  [MoveResult.WRONG_UNIT_TYPE]: 'Unit type cannot enter this terrain',
  [MoveResult.ENEMY_HEXSIDE]: 'Enemy controls this hexside',
  [MoveResult.SIEGE_RESTRICTION]: 'Siege unit cannot cross rough terrain without road',
  [MoveResult.CONTINUOUS_MOVE_BLOCKED]: 'Cannot continue after crossing rough terrain',
  [MoveResult.COMBAT_ENTRY_BLOCKED]: 'Unit in combat cannot enter new combat',
  [MoveResult.ROAD_MOVE_INTO_COMBAT]: 'Cannot enter combat with road bonus move',
  [MoveResult.PATH_CONTINUES_PAST_COMBAT]: 'Path cannot continue past combat',
  [MoveResult.EXCEEDS_HEXSIDE_LIMIT]: 'Too many units crossing this hexside',
}

// =============================================================================
// ADJACENCY HELPERS
// =============================================================================

/**
 * Check if two hexes are adjacent.
 * The map uses offset coordinates where columns alternate between 38 and 39 hexes.
 */
export function areHexesAdjacent(hex1, hex2) {
  const diff = Math.abs(hex1 - hex2)
  return diff === 1 || diff === 38 || diff === 39
}

/**
 * Get hex position (column, row) from hex ID.
 * Matches the server-side and Map.vue calculation.
 */
export function getHexPosition(hexId) {
  let remaining = hexId
  let col = 0
  
  while (remaining >= 0) {
    const colSize = col % 2 === 0 ? 39 : 38
    if (remaining < colSize) {
      break
    }
    remaining -= colSize
    col++
  }
  
  return { col, row: remaining }
}

/**
 * Get the direction from one hex to another.
 */
export function getDirection(fromHex, toHex) {
  const diff = fromHex - toHex
  
  const directionMap = {
    1: 'N',
    [-1]: 'S',
    39: 'NW',
    [-39]: 'SE',
    38: 'NE',
    [-38]: 'SW'
  }
  
  return directionMap[diff] || null
}

// =============================================================================
// TERRAIN PASSABILITY
// =============================================================================

/**
 * Check if a ground unit can enter a hex via a hexside.
 */
export function canGroundUnitEnter(hexTerrain, hexsideTerrain) {
  const passableHex = ['C', 'F', 'M', 'S', 'R', 'W'].includes(hexTerrain)
  const passableSide = ['C', 'F', 'M', 'S', 'R', 'W', 'K', 'Q', 'I'].includes(hexsideTerrain)
  return passableHex && passableSide
}

/**
 * Check if a sea unit can move between two hexes.
 */
export function canSeaUnitEnter(fromTerrain, toTerrain, hexsideTerrain) {
  if (fromTerrain === 'O' && toTerrain === 'O') {
    return true
  }
  if ((fromTerrain === 'O' || toTerrain === 'O') && hexsideTerrain === 'K') {
    return true
  }
  return false
}

/**
 * Check if an air unit can enter a hex.
 */
export function canAirUnitEnter(hexTerrain) {
  return hexTerrain !== 'I' && hexTerrain !== 'X'
}

/**
 * Check if a hexside terrain is rough (stops continuous movement).
 */
export function isRoughTerrainHexside(hexsideTerrain) {
  return ['M', 'S', 'R', 'W', 'I', 'Q'].includes(hexsideTerrain)
}

// =============================================================================
// HEXSIDE DATA EXTRACTION
// =============================================================================

/**
 * Get hexside terrain from a hex object.
 * Hex objects have north, south, northeast, northwest, southeast, southwest properties.
 */
export function getHexsideTerrain(hexObj, fromHex, toHex) {
  if (!hexObj) return null
  
  const diff = fromHex - toHex
  
  switch (diff) {
    case 1: return hexObj.north?.terrain
    case -1: return hexObj.south?.terrain
    case 39: return hexObj.northwest?.terrain
    case -39: return hexObj.southeast?.terrain
    case 38: return hexObj.northeast?.terrain
    case -38: return hexObj.southwest?.terrain
    default: return null
  }
}

/**
 * Get hexside control (initiative value) from a hex object.
 */
export function getHexsideControl(hexObj, fromHex, toHex) {
  if (!hexObj) return -1
  
  const diff = fromHex - toHex
  
  switch (diff) {
    case 1: return hexObj.north?.control ?? -1
    case -1: return hexObj.south?.control ?? -1
    case 39: return hexObj.northwest?.control ?? -1
    case -39: return hexObj.southeast?.control ?? -1
    case 38: return hexObj.northeast?.control ?? -1
    case -38: return hexObj.southwest?.control ?? -1
    default: return -1
  }
}

/**
 * Check if there's a road between two hexes.
 */
export function hasRoad(hexObj, fromHex, toHex) {
  if (!hexObj) return false
  
  const diff = fromHex - toHex
  
  switch (diff) {
    case 1: return hexObj.north?.road || false
    case -1: return hexObj.south?.road || false
    case 39: return hexObj.northwest?.road || false
    case -39: return hexObj.southeast?.road || false
    case 38: return hexObj.northeast?.road || false
    case -38: return hexObj.southwest?.road || false
    default: return false
  }
}

// =============================================================================
// HEXSIDE LIMIT CALCULATION
// =============================================================================

/**
 * Get the movement limit for a hexside.
 */
export function getHexsideLimit(hexsideTerrain, hasRoadBonus, isCombatMove) {
  if (!hexsideTerrain) return 0
  
  let limit = HEXSIDE_LIMITS[hexsideTerrain] ?? 0
  
  // Coastal hexsides have reduced limit in combat
  if (hexsideTerrain === 'K' && isCombatMove) {
    limit = COASTAL_COMBAT_LIMIT
  }
  
  // Roads add to limit (but not during combat)
  if (!isCombatMove && hasRoadBonus) {
    limit += ROAD_BONUS
  }
  
  return limit
}

// =============================================================================
// MAIN VALIDATION FUNCTION
// =============================================================================

/**
 * Validate a single move from one hex to an adjacent hex.
 * 
 * @param {Object} params - Validation parameters
 * @param {number} params.fromHex - Source hex ID
 * @param {number} params.toHex - Destination hex ID
 * @param {Object} params.unit - Unit data (movement, movementRemaining, roadMoveRemaining, unitType, category)
 * @param {Object} params.fromHexObj - Full hex object for source hex
 * @param {Object} params.toHexObj - Full hex object for destination hex
 * @param {number} params.factionInitiative - The unit's faction's initiative value
 * @param {boolean} params.hasEnemiesAtDest - Are there enemies at the destination?
 * @param {number} params.movementUsed - Movement points already used this turn
 * @param {number} params.roadMoveUsed - Road moves already used this turn
 * @param {boolean} params.previousWasRough - Did previous step cross rough terrain?
 * @returns {Object} - { valid, result, message, movementCost, usesRoadBonus, entersCombat }
 */
export function validateMove({
  fromHex,
  toHex,
  unit,
  fromHexObj,
  toHexObj,
  factionInitiative = -1,
  hasEnemiesAtDest = false,
  movementUsed = 0,
  roadMoveUsed = 0,
  previousWasRough = false,
}) {
  // Check hex validity
  if (!fromHexObj || !toHexObj) {
    return {
      valid: false,
      result: MoveResult.INVALID_HEX,
      message: MoveResultMessages[MoveResult.INVALID_HEX],
    }
  }
  
  // Check adjacency
  if (!areHexesAdjacent(fromHex, toHex)) {
    return {
      valid: false,
      result: MoveResult.NOT_ADJACENT,
      message: MoveResultMessages[MoveResult.NOT_ADJACENT],
    }
  }
  
  // Get terrain info
  const hexTerrain = toHexObj.terrain
  const hexsideTerrain = getHexsideTerrain(fromHexObj, fromHex, toHex) || 'C'
  const roadExists = hasRoad(fromHexObj, fromHex, toHex)
  
  // Check for impassable hexside
  if (hexsideTerrain === 'X' || hexsideTerrain === 'N') {
    return {
      valid: false,
      result: MoveResult.IMPASSABLE_HEXSIDE,
      message: MoveResultMessages[MoveResult.IMPASSABLE_HEXSIDE],
    }
  }
  
  // Check unit type vs terrain
  const unitType = unit.unitType || unit.unit_type || 1  // Default to ground
  
  if (unitType === 1 || unitType === 'ground' || unitType === 'GROUND') {  // Ground units
    if (!canGroundUnitEnter(hexTerrain, hexsideTerrain)) {
      return {
        valid: false,
        result: MoveResult.WRONG_UNIT_TYPE,
        message: `Ground unit cannot enter ${hexTerrain} terrain via ${hexsideTerrain} hexside`,
      }
    }
  } else if (unitType === 2 || unitType === 'sea' || unitType === 'SEA') {  // Sea units
    const fromTerrain = fromHexObj.terrain
    if (!canSeaUnitEnter(fromTerrain, hexTerrain, hexsideTerrain)) {
      return {
        valid: false,
        result: MoveResult.WRONG_UNIT_TYPE,
        message: 'Sea unit cannot make this move',
      }
    }
  } else if (unitType === 3 || unitType === 'air' || unitType === 'AIR') {  // Air units
    if (!canAirUnitEnter(hexTerrain)) {
      return {
        valid: false,
        result: MoveResult.IMPASSABLE_TERRAIN,
        message: 'Air unit cannot enter impassable terrain',
      }
    }
  }
  
  // Calculate available movement
  const baseMovement = unit.movement || unit.movementRemaining || 3
  const movementRemaining = baseMovement - movementUsed
  const roadMoveBase = unit.roadMove || unit.roadMoveRemaining || 0
  const roadMoveRemaining = roadMoveBase - roadMoveUsed
  
  let usesRoadBonus = false
  
  if (movementRemaining <= 0) {
    if (roadExists && roadMoveRemaining > 0) {
      usesRoadBonus = true
    } else {
      return {
        valid: false,
        result: MoveResult.NO_MOVEMENT_POINTS,
        message: MoveResultMessages[MoveResult.NO_MOVEMENT_POINTS],
      }
    }
  }
  
  // Can't enter combat with road move only
  if (hasEnemiesAtDest && usesRoadBonus) {
    return {
      valid: false,
      result: MoveResult.ROAD_MOVE_INTO_COMBAT,
      message: MoveResultMessages[MoveResult.ROAD_MOVE_INTO_COMBAT],
    }
  }
  
  // Check hexside control (enemy-controlled hexsides)
  const hexsideControl = getHexsideControl(fromHexObj, fromHex, toHex)
  if (hexsideControl >= 0 && hexsideControl !== factionInitiative) {
    return {
      valid: false,
      result: MoveResult.ENEMY_HEXSIDE,
      message: MoveResultMessages[MoveResult.ENEMY_HEXSIDE],
    }
  }
  
  // Check siege unit restrictions
  const unitCategory = unit.category || 0
  if (unitCategory === 4 || unitCategory === 'interior_siege' || unitCategory === 'INTERIOR_SIEGE') {
    if (!['C', 'F'].includes(hexsideTerrain) && !roadExists) {
      return {
        valid: false,
        result: MoveResult.SIEGE_RESTRICTION,
        message: MoveResultMessages[MoveResult.SIEGE_RESTRICTION],
      }
    }
  }
  
  // Check continuous movement (rough terrain stops further movement)
  if (previousWasRough && !roadExists) {
    return {
      valid: false,
      result: MoveResult.CONTINUOUS_MOVE_BLOCKED,
      message: MoveResultMessages[MoveResult.CONTINUOUS_MOVE_BLOCKED],
    }
  }
  
  // All checks passed!
  return {
    valid: true,
    result: MoveResult.SUCCESS,
    message: MoveResultMessages[MoveResult.SUCCESS],
    movementCost: 1,
    usesRoadBonus,
    entersCombat: hasEnemiesAtDest,
    isRoughTerrain: isRoughTerrainHexside(hexsideTerrain),
  }
}

/**
 * Validate an entire path for a unit.
 * 
 * @param {Object} unit - Unit data
 * @param {number[]} path - Array of hex IDs (not including starting hex)
 * @param {Object} hexLookup - Map of hexId -> hex object
 * @param {number} factionInitiative - The unit's faction's initiative
 * @param {Function} getEnemiesAtHex - Function to check for enemies at a hex
 * @returns {Object} - { valid, validSteps, invalidStepIndex, message, totalMovementUsed, totalRoadMoveUsed }
 */
export function validatePath(unit, path, hexLookup, factionInitiative, getEnemiesAtHex = () => []) {
  if (!path || path.length === 0) {
    return {
      valid: false,
      validSteps: 0,
      invalidStepIndex: -1,
      message: 'Empty path',
    }
  }
  
  let currentHex = unit.location
  let movementUsed = 0
  let roadMoveUsed = 0
  let previousWasRough = false
  
  for (let i = 0; i < path.length; i++) {
    const nextHex = path[i]
    const fromHexObj = hexLookup[currentHex]
    const toHexObj = hexLookup[nextHex]
    const enemies = getEnemiesAtHex(nextHex)
    const hasEnemies = enemies.length > 0
    
    const result = validateMove({
      fromHex: currentHex,
      toHex: nextHex,
      unit,
      fromHexObj,
      toHexObj,
      factionInitiative,
      hasEnemiesAtDest: hasEnemies,
      movementUsed,
      roadMoveUsed,
      previousWasRough,
    })
    
    if (!result.valid) {
      return {
        valid: false,
        validSteps: i,
        invalidStepIndex: i,
        message: `Step ${i + 1}: ${result.message}`,
        result: result.result,
      }
    }
    
    // Update state for next step
    if (result.usesRoadBonus) {
      roadMoveUsed += 1
    } else {
      movementUsed += result.movementCost
    }
    previousWasRough = result.isRoughTerrain || false
    
    // If entering combat, path must end here
    if (result.entersCombat && i < path.length - 1) {
      return {
        valid: false,
        validSteps: i + 1,
        invalidStepIndex: i + 1,
        message: `Step ${i + 1}: Path cannot continue past combat`,
        result: MoveResult.PATH_CONTINUES_PAST_COMBAT,
      }
    }
    
    currentHex = nextHex
  }
  
  return {
    valid: true,
    validSteps: path.length,
    invalidStepIndex: -1,
    message: 'Path is valid',
    totalMovementUsed: movementUsed,
    totalRoadMoveUsed: roadMoveUsed,
  }
}

/**
 * Check hexside usage for the player's own faction.
 * Counts how many of the player's units are crossing each hexside.
 * 
 * @param {Object[]} movementOrders - Array of { unitId, path, unit } objects
 * @param {Object} hexLookup - Map of hexId -> hex object
 * @param {Object} unitLookup - Map of unitId -> unit object
 * @returns {Map} - Map of "fromHex-toHex" -> { count, limit }
 */
export function checkHexsideUsage(movementOrders, hexLookup, unitLookup) {
  const usage = new Map()
  
  for (const order of movementOrders) {
    const unit = unitLookup[order.unitId] || order.unit
    if (!unit) continue
    
    let currentHex = unit.location
    
    for (const nextHex of order.path) {
      // Normalize key (smaller hex first)
      const key = `${Math.min(currentHex, nextHex)}-${Math.max(currentHex, nextHex)}`
      
      if (!usage.has(key)) {
        const fromHexObj = hexLookup[currentHex]
        const hexsideTerrain = getHexsideTerrain(fromHexObj, currentHex, nextHex) || 'C'
        const roadExists = hasRoad(fromHexObj, currentHex, nextHex)
        const limit = getHexsideLimit(hexsideTerrain, roadExists, false)
        
        usage.set(key, { count: 0, limit })
      }
      
      usage.get(key).count += 1
      currentHex = nextHex
    }
  }
  
  return usage
}

export default {
  MoveResult,
  MoveResultMessages,
  areHexesAdjacent,
  getHexPosition,
  getDirection,
  validateMove,
  validatePath,
  checkHexsideUsage,
  getHexsideTerrain,
  getHexsideLimit,
  hasRoad,
  isRoughTerrainHexside,
}

