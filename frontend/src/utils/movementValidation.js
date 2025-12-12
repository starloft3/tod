/**
 * Client-side Movement Validation for Tides of Darkness
 * 
 * Comprehensive validation using full hex data including hexsides and roads.
 * Validates: adjacency, terrain passability, hexside limits (own faction), 
 * movement points, and road bonuses.
 * 
 * Server still handles: cross-faction hexside conflicts, hidden enemies, combat.
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
  'N': 0,   // Coastal Mountain (impassable for ground)
  'K': 4,   // Coastal
  'O': 99,  // Ocean - unlimited for sea units
  'Q': 2,   // Coastal Forest
  'R': 4,   // River
  'W': 4,   // Fortification
}

export const ROAD_BONUS = 2

// Passable hex terrain for ground units
const GROUND_PASSABLE_HEX = ['C', 'F', 'M', 'S', 'R', 'W']
const GROUND_PASSABLE_HEXSIDE = ['C', 'F', 'M', 'S', 'R', 'W', 'K', 'Q']

// Rough terrain hexsides (stop continuous movement unless using road)
const ROUGH_HEXSIDES = ['M', 'S', 'R', 'W', 'Q']

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
  [MoveResult.CONTINUOUS_MOVE_BLOCKED]: 'Cannot continue after rough terrain (no road)',
  [MoveResult.EXCEEDS_HEXSIDE_LIMIT]: 'Too many of your units crossing this hexside',
}

// Terrain display names
export const TERRAIN_NAMES = {
  'C': 'Clear',
  'F': 'Forest',
  'M': 'Mountain',
  'S': 'Swamp',
  'O': 'Ocean',
  'I': 'Peaks (Impassable)',
  'X': 'Impassable',
  'K': 'Coastal',
  'N': 'Coastal Mountain',
  'Q': 'Coastal Forest',
  'R': 'River',
  'W': 'Fortification',
}

// =============================================================================
// ADJACENCY HELPERS
// =============================================================================

/**
 * Check if two hexes are adjacent.
 */
export function areHexesAdjacent(hex1, hex2) {
  const diff = Math.abs(hex1 - hex2)
  return diff === 1 || diff === 38 || diff === 39
}

/**
 * Get the direction from one hex to another.
 * Returns the hexside key for looking up data.
 * Uses (from - to) to match server.py HasRoad() convention.
 */
export function getDirectionKey(fromHex, toHex) {
  const diff = fromHex - toHex
  
  // Direction map matches server.py HasRoad():
  // result==1 -> north, result==39 -> northwest, result==38 -> southwest
  // result==-1 -> south, result==-39 -> southeast, result==-38 -> northeast
  const directionMap = {
    1: 'north',
    [-1]: 'south',
    39: 'northwest',
    [-39]: 'southeast',
    38: 'southwest',
    [-38]: 'northeast'
  }
  
  return directionMap[diff] || null
}

// =============================================================================
// HEXSIDE DATA EXTRACTION
// =============================================================================

/**
 * Get hexside data from a hex object.
 * The hex object should have north, south, etc. properties with { terrain, control, road }
 */
export function getHexside(hexObj, fromHex, toHex) {
  if (!hexObj) return null
  
  const direction = getDirectionKey(fromHex, toHex)
  if (!direction) return null
  
  return hexObj[direction] || null
}

/**
 * Check if there's a road on a hexside.
 */
export function hasRoad(hexObj, fromHex, toHex) {
  const hexside = getHexside(hexObj, fromHex, toHex)
  return hexside?.road || false
}

/**
 * Get hexside terrain.
 */
export function getHexsideTerrain(hexObj, fromHex, toHex) {
  const hexside = getHexside(hexObj, fromHex, toHex)
  return hexside?.terrain || 'C'
}

/**
 * Get hexside control (initiative value).
 */
export function getHexsideControl(hexObj, fromHex, toHex) {
  const hexside = getHexside(hexObj, fromHex, toHex)
  return hexside?.control ?? -1
}

/**
 * Check if hexside is rough terrain.
 */
export function isRoughTerrain(hexsideTerrain) {
  return ROUGH_HEXSIDES.includes(hexsideTerrain)
}

// =============================================================================
// TERRAIN PASSABILITY
// =============================================================================

/**
 * Check if a ground unit can enter a hex via a hexside.
 */
export function canGroundUnitEnter(hexTerrain, hexsideTerrain) {
  const passableHex = GROUND_PASSABLE_HEX.includes(hexTerrain)
  const passableSide = GROUND_PASSABLE_HEXSIDE.includes(hexsideTerrain)
  return passableHex && passableSide
}

/**
 * Check if a sea unit can move between two hexes.
 */
export function canSeaUnitEnter(fromTerrain, toTerrain, hexsideTerrain) {
  // Sea units need ocean on both sides, or coastal hexside
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

// =============================================================================
// HEXSIDE LIMITS
// =============================================================================

/**
 * Get the base hexside limit for terrain.
 */
export function getHexsideLimit(hexsideTerrain, hasRoadBonus = false) {
  let limit = HEXSIDE_LIMITS[hexsideTerrain] ?? 0
  
  // Roads add to limit
  if (hasRoadBonus) {
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
 * @param {Object} params.unit - Unit data (movement, movementRemaining, roadMove/roadMoveRemaining, unitType, category)
 * @param {Object} params.fromHexObj - Full hex object for source hex (with hexside data)
 * @param {Object} params.toHexObj - Full hex object for destination hex
 * @param {number} params.factionInitiative - The unit's faction's initiative value (for hexside control)
 * @param {number} params.movementUsed - Movement points already used this turn
 * @param {number} params.roadMoveUsed - Road moves already used this turn
 * @param {boolean} params.previousWasRough - Did previous step cross rough terrain?
 * @param {boolean} params.usedRoadOnPrevious - Did we use a road on the previous step?
 * @returns {Object} - { valid, result, message, usesRoadBonus, isRoughTerrain }
 */
export function validateMove({
  fromHex,
  toHex,
  unit,
  fromHexObj,
  toHexObj,
  factionInitiative = -1,
  movementUsed = 0,
  roadMoveUsed = 0,
  previousWasRough = false,
  usedRoadOnPrevious = false,
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
  const hexsideTerrain = getHexsideTerrain(fromHexObj, fromHex, toHex)
  const roadExists = hasRoad(fromHexObj, fromHex, toHex)
  
  // Check for impassable hexside
  if (hexsideTerrain === 'X' || hexsideTerrain === 'N' || hexsideTerrain === 'I') {
    return {
      valid: false,
      result: MoveResult.IMPASSABLE_HEXSIDE,
      message: `Cannot cross ${TERRAIN_NAMES[hexsideTerrain] || hexsideTerrain} hexside`,
    }
  }
  
  // Check unit type vs terrain
  const unitType = unit.unitType || unit.unit_type || 1  // Default to ground
  
  if (unitType === 1 || unitType === 'ground' || unitType === 'GROUND') {
    if (!canGroundUnitEnter(hexTerrain, hexsideTerrain)) {
      return {
        valid: false,
        result: MoveResult.WRONG_UNIT_TYPE,
        message: `Ground unit cannot enter ${TERRAIN_NAMES[hexTerrain] || hexTerrain} via ${TERRAIN_NAMES[hexsideTerrain] || hexsideTerrain}`,
      }
    }
  } else if (unitType === 2 || unitType === 'sea' || unitType === 'SEA') {
    const fromTerrain = fromHexObj.terrain
    if (!canSeaUnitEnter(fromTerrain, hexTerrain, hexsideTerrain)) {
      return {
        valid: false,
        result: MoveResult.WRONG_UNIT_TYPE,
        message: 'Sea unit cannot make this move',
      }
    }
  } else if (unitType === 3 || unitType === 'air' || unitType === 'AIR') {
    if (!canAirUnitEnter(hexTerrain)) {
      return {
        valid: false,
        result: MoveResult.IMPASSABLE_TERRAIN,
        message: 'Air unit cannot enter impassable terrain',
      }
    }
  }
  
  // Calculate available movement
  const baseMovement = unit.movement || unit.movementRemaining || unit.movementMax || 3
  const baseRoadMove = unit.roadMove || unit.roadMoveRemaining || 0
  const movementRemaining = baseMovement - movementUsed
  const roadMoveRemaining = baseRoadMove - roadMoveUsed
  
  let usesRoadBonus = false
  
  if (movementRemaining <= 0) {
    // Must use road bonus
    if (roadExists && roadMoveRemaining > 0) {
      usesRoadBonus = true
    } else {
      return {
        valid: false,
        result: MoveResult.NO_MOVEMENT_POINTS,
        message: roadMoveRemaining > 0 
          ? 'No regular movement - need a road to use bonus move'
          : 'No movement points remaining',
      }
    }
  }
  
  // NOTE: Hexside control check DISABLED for now
  // Hexside control only applies during active combat situations, not as a 
  // permanent property of hexsides. Will be re-enabled when combat is implemented.
  // TODO: Re-enable after combat implementation
  // const hexsideControl = getHexsideControl(fromHexObj, fromHex, toHex)
  // if (hexsideControl >= 0 && factionInitiative >= 0 && hexsideControl !== factionInitiative) {
  //   return {
  //     valid: false,
  //     result: MoveResult.ENEMY_HEXSIDE,
  //     message: MoveResultMessages[MoveResult.ENEMY_HEXSIDE],
  //   }
  // }
  
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
  
  // Check continuous movement (rough terrain stops further movement unless using road)
  const currentIsRough = isRoughTerrain(hexsideTerrain)
  if (previousWasRough && !usedRoadOnPrevious && !roadExists) {
    return {
      valid: false,
      result: MoveResult.CONTINUOUS_MOVE_BLOCKED,
      message: `Cannot continue movement after crossing rough terrain (${TERRAIN_NAMES[hexsideTerrain] || hexsideTerrain}) without a road`,
    }
  }
  
  // All checks passed!
  return {
    valid: true,
    result: MoveResult.SUCCESS,
    message: roadExists ? 'Move valid (road)' : 'Move valid',
    usesRoadBonus,
    isRoughTerrain: currentIsRough,
    hasRoad: roadExists,
  }
}

/**
 * Validate an entire path for a unit, tracking movement and road bonus usage.
 * 
 * @param {Object} unit - Unit data
 * @param {number[]} path - Array of hex IDs (not including starting hex)
 * @param {Object} hexLookup - Map of hexId -> hex object (with hexside data)
 * @param {number} factionInitiative - The unit's faction's initiative
 * @returns {Object} - { valid, steps[], totalMovementUsed, totalRoadMoveUsed, message }
 */
export function validatePath(unit, path, hexLookup, factionInitiative = -1) {
  if (!path || path.length === 0) {
    return {
      valid: false,
      steps: [],
      message: 'Empty path',
    }
  }
  
  let currentHex = unit.location
  let movementUsed = 0
  let roadMoveUsed = 0
  let previousWasRough = false
  let usedRoadOnPrevious = false
  
  const steps = []
  
  for (let i = 0; i < path.length; i++) {
    const nextHex = path[i]
    const fromHexObj = hexLookup[currentHex]
    const toHexObj = hexLookup[nextHex]
    
    const result = validateMove({
      fromHex: currentHex,
      toHex: nextHex,
      unit,
      fromHexObj,
      toHexObj,
      factionInitiative,
      movementUsed,
      roadMoveUsed,
      previousWasRough,
      usedRoadOnPrevious,
    })
    
    steps.push({
      hexId: nextHex,
      ...result,
      movementUsedAfter: movementUsed + (result.usesRoadBonus ? 0 : 1),
      roadMoveUsedAfter: roadMoveUsed + (result.usesRoadBonus ? 1 : 0),
    })
    
    if (!result.valid) {
      return {
        valid: false,
        steps,
        totalMovementUsed: movementUsed,
        totalRoadMoveUsed: roadMoveUsed,
        message: `Step ${i + 1}: ${result.message}`,
      }
    }
    
    // Update state for next step
    if (result.usesRoadBonus) {
      roadMoveUsed += 1
    } else {
      movementUsed += 1
    }
    previousWasRough = result.isRoughTerrain
    usedRoadOnPrevious = result.hasRoad
    currentHex = nextHex
  }
  
  return {
    valid: true,
    steps,
    totalMovementUsed: movementUsed,
    totalRoadMoveUsed: roadMoveUsed,
    message: 'Path is valid',
  }
}

/**
 * Check hexside usage for the player's own faction.
 * Useful for checking if too many units are trying to cross the same hexside.
 * 
 * @param {Object[]} movementOrders - Array of { unitId, path, unit } objects
 * @param {Object} hexLookup - Map of hexId -> hex object
 * @param {Object} unitLookup - Map of unitId -> unit object
 * @returns {Map} - Map of "minHex-maxHex" -> { count, limit, terrain, hasRoad }
 */
export function checkHexsideUsage(movementOrders, hexLookup, unitLookup) {
  const usage = new Map()
  
  for (const order of movementOrders) {
    const unit = unitLookup[order.unitId] || order.unit
    if (!unit) continue
    
    let currentHex = unit.location
    
    for (const nextHex of order.path) {
      // Normalize key (smaller hex first for consistent lookup)
      const key = `${Math.min(currentHex, nextHex)}-${Math.max(currentHex, nextHex)}`
      
      if (!usage.has(key)) {
        const fromHexObj = hexLookup[currentHex]
        const hexsideTerrain = getHexsideTerrain(fromHexObj, currentHex, nextHex)
        const roadExists = hasRoad(fromHexObj, currentHex, nextHex)
        const limit = getHexsideLimit(hexsideTerrain, roadExists)
        
        usage.set(key, { 
          count: 0, 
          limit,
          terrain: hexsideTerrain,
          hasRoad: roadExists,
        })
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
  TERRAIN_NAMES,
  areHexesAdjacent,
  getDirectionKey,
  getHexside,
  hasRoad,
  getHexsideTerrain,
  getHexsideControl,
  isRoughTerrain,
  canGroundUnitEnter,
  canSeaUnitEnter,
  canAirUnitEnter,
  getHexsideLimit,
  validateMove,
  validatePath,
  checkHexsideUsage,
}
