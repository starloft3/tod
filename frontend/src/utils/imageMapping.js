/**
 * Image Mapping Utilities for Tides of Darkness
 * 
 * Maps factions, units, and bases to their corresponding image assets.
 */

// Base path for images (relative to public folder)
const IMAGE_BASE = '/images'

// ============================================================================
// FACTION IMAGE MAPPINGS
// ============================================================================

/**
 * Maps faction names to their image filename (lowercase, no spaces).
 * Used for backgrounds, banners, etc.
 */
const FACTION_TO_IMAGE = {
  'Amani': 'amani',
  'Bleeding Hollow': 'bleedinghollow',
  'Black Tooth Grin': 'blacktoothgrin',
  'Dragonmaw': 'dragonmaw',
  'Stormreaver': 'stormreavers',  // Note the 's' - matches file
  'Twilight\'s Hammer': 'twilightshammer',
  'Blackrock': 'blackrock',
  'Silvermoon': 'silvermoon',
  'Aerie Peak': 'aeriepeak',
  'Ironforge': 'ironforge',
  'Dalaran': 'dalaran',
  'Kul Tiras': 'kultiras',
  'Stromgarde': 'stromgarde',
  'Azeroth': 'azeroth',
  'Lordaeron': 'lordaeron',
  'Gilneas': 'gilneas',
  'Alterac': 'alterac',
  'Dark Iron': 'darkiron',
  'Burning Blade': 'burningblade',
  'Frostwolf': 'frostwolf',
  'Dalaran Rebel': 'dalaranrebel',
  'Gilnean Rebel': 'gilneasrebel',
  'Firetree': 'firetree',
  'Smolderthorn': 'smolderthorn',
  'Shadowpine': 'shadowpine',
  'Shadowglen': 'shadowglen',
  'Revantusk': 'revantusk',
  'Mossflayer': 'mossflayer',
  'Witherbark': 'witherbark',
  'Vilebranch': 'vilebranch',
  'Dragon': 'dragon',
  'Demon': 'demon',
}

/**
 * Horde factions (by ID) - use Horde building styles
 */
const HORDE_FACTION_IDS = [0, 1, 2, 3, 4, 5, 6, 17, 18, 19, 22, 23, 24, 25, 26, 27, 28, 29]

/**
 * Alliance factions (by ID) - use Alliance building styles
 */
const ALLIANCE_FACTION_IDS = [7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 20, 21]

// ============================================================================
// IMAGE PATH GETTERS
// ============================================================================

/**
 * Get the background image path for a faction.
 * Used as the backdrop when compositing unit icons.
 */
export function getFactionBackground(factionName) {
  const imageName = FACTION_TO_IMAGE[factionName] || factionName?.toLowerCase().replace(/['\s]/g, '')
  return `${IMAGE_BASE}/Backgrounds/${imageName}Background.png`
}

/**
 * Get the banner image path for a faction.
 * Used behind bases.
 */
export function getFactionBanner(factionName) {
  const imageName = FACTION_TO_IMAGE[factionName] || factionName?.toLowerCase().replace(/['\s]/g, '')
  // Banner filenames don't have "banner" suffix, just the faction name
  // Check the exact naming in the folder
  const bannerName = imageName === 'stormreavers' ? 'stormreaver' : imageName
  return `${IMAGE_BASE}/Banners/${bannerName}.png`
}

/**
 * Get the unit image path.
 * Unit images are named after the unit type, lowercase, no spaces.
 */
export function getUnitImage(unitName) {
  // Convert to lowercase, remove spaces
  const imageName = unitName?.toLowerCase().replace(/[\s']/g, '') || 'footman'
  return `${IMAGE_BASE}/Units/${imageName}.png`
}

/**
 * Get the building image path for a base.
 * 
 * @param {number} factionId - The faction ID
 * @param {number} tier - Base tier (1, 2, or 3)
 * @returns {string} Path to building image
 */
export function getBaseImage(factionId, tier = 1) {
  const isHorde = HORDE_FACTION_IDS.includes(factionId)
  
  if (isHorde) {
    switch(tier) {
      case 3: return `${IMAGE_BASE}/Buildings/fortress.png`
      case 2: return `${IMAGE_BASE}/Buildings/stronghold.png`
      default: return `${IMAGE_BASE}/Buildings/greathall.png`
    }
  } else {
    switch(tier) {
      case 3: return `${IMAGE_BASE}/Buildings/castle.png`
      case 2: return `${IMAGE_BASE}/Buildings/keep.png`
      default: return `${IMAGE_BASE}/Buildings/townhall.png`
    }
  }
}

/**
 * Get the ruins image path.
 */
export function getRuinsImage() {
  return `${IMAGE_BASE}/Buildings/ruins.png`
}

/**
 * Get expansion image (farm, mill, rig).
 * 
 * @param {string} type - 'farm', 'mill', or 'rig'
 * @param {number} factionId - The controlling faction
 */
export function getExpansionImage(type, factionId) {
  const isHorde = HORDE_FACTION_IDS.includes(factionId)
  const prefix = isHorde ? 'horde' : 'alliance'
  return `${IMAGE_BASE}/Buildings/${prefix}${type}.png`
}

/**
 * Get special building image.
 */
export function getSpecialBuildingImage(buildingType) {
  switch(buildingType) {
    case 1: return `${IMAGE_BASE}/Buildings/runestone.png`
    case 2: return `${IMAGE_BASE}/Buildings/darkportal.png`
    case 3: return `${IMAGE_BASE}/Buildings/roost.png`
    default: return null
  }
}

// ============================================================================
// ALIGNMENT HELPERS
// ============================================================================

/**
 * Check if a faction is Horde alignment.
 */
export function isHordeFaction(factionId) {
  return HORDE_FACTION_IDS.includes(factionId)
}

/**
 * Check if a faction is Alliance alignment.
 */
export function isAllianceFaction(factionId) {
  return ALLIANCE_FACTION_IDS.includes(factionId)
}

/**
 * Get alignment color for a faction.
 */
export function getAlignmentColor(factionId) {
  if (isHordeFaction(factionId)) {
    return '#CC0000' // Red for Horde
  } else if (isAllianceFaction(factionId)) {
    return '#0066CC' // Blue for Alliance
  }
  return '#666666' // Gray for neutral/unknown
}

// ============================================================================
// UNIT POSITIONING
// ============================================================================

/**
 * Calculate unit positions within a hex.
 * Alliance units at top, Horde units at bottom.
 * 
 * @param {Array} units - Array of unit objects with factionId
 * @param {number} hexCenterX - Center X of the hex
 * @param {number} hexCenterY - Center Y of the hex
 * @param {number} unitSize - Size of unit icons (default 24)
 * @returns {Array} Array of {unit, x, y} positions
 */
export function calculateUnitPositions(units, hexCenterX, hexCenterY, unitSize = 24) {
  const positions = []
  
  // Separate by alignment
  const allianceUnits = units.filter(u => isAllianceFaction(u.factionId || u.faction))
  const hordeUnits = units.filter(u => isHordeFaction(u.factionId || u.faction))
  
  // Position Alliance units at top of hex
  const allianceY = hexCenterY - 30
  positionUnitRow(allianceUnits, hexCenterX, allianceY, unitSize, positions)
  
  // Position Horde units at bottom of hex
  const hordeY = hexCenterY + 20
  positionUnitRow(hordeUnits, hexCenterX, hordeY, unitSize, positions)
  
  return positions
}

/**
 * Position a row of units horizontally centered.
 */
function positionUnitRow(units, centerX, y, unitSize, positions) {
  if (units.length === 0) return
  
  const spacing = unitSize + 2
  const maxPerRow = 5
  
  // Stack in rows if needed
  let currentY = y
  let remaining = [...units]
  
  while (remaining.length > 0) {
    const rowUnits = remaining.splice(0, maxPerRow)
    const totalWidth = rowUnits.length * spacing - 2
    let startX = centerX - totalWidth / 2
    
    for (let i = 0; i < rowUnits.length; i++) {
      positions.push({
        unit: rowUnits[i],
        x: startX + i * spacing,
        y: currentY
      })
    }
    
    currentY += unitSize + 2
  }
}

// ============================================================================
// EXPORTS
// ============================================================================

export default {
  getFactionBackground,
  getFactionBanner,
  getUnitImage,
  getBaseImage,
  getRuinsImage,
  getExpansionImage,
  getSpecialBuildingImage,
  isHordeFaction,
  isAllianceFaction,
  getAlignmentColor,
  calculateUnitPositions,
  HORDE_FACTION_IDS,
  ALLIANCE_FACTION_IDS,
}

