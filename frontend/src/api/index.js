/**
 * API client for Tides of Darkness backend.
 */
import axios from 'axios'

const API_BASE = 'http://localhost:8000'

const api = axios.create({
  baseURL: API_BASE,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json'
  }
})

// Game endpoints
export const game = {
  getStatus: () => api.get('/game/status'),
  getStatistics: () => api.get('/game/statistics'),
  getTurn: () => api.get('/game/turn'),
  reload: () => api.post('/game/reload'),
  // Faction view - filtered game state
  getView: (factionId = null) => api.get('/game/view', { 
    params: factionId !== null ? { faction: factionId } : {} 
  })
}

// Unit endpoints
export const units = {
  list: (params = {}) => api.get('/units', { params }),
  get: (id) => api.get(`/units/${id}`),
  atHex: (hexId, aliveOnly = true) => api.get(`/units/at/${hexId}`, { params: { aliveOnly } }),
  byFaction: (factionId, aliveOnly = true) => api.get(`/units/faction/${factionId}`, { params: { aliveOnly } }),
  heroes: (params = {}) => api.get('/units/heroes', { params }),
  byCategory: (category, params = {}) => api.get(`/units/category/${category}`, { params })
}

// Hex endpoints
export const hexes = {
  list: (params = {}) => api.get('/hexes', { params }),
  get: (id) => api.get(`/hexes/${id}`),
  adjacent: (id) => api.get(`/hexes/${id}/adjacent`),
  visible: (factionId) => api.get(`/hexes/visible/${factionId}`),
  byTerrain: (terrain) => api.get(`/hexes/terrain/${terrain}`),
  withBases: (params = {}) => api.get('/hexes/with-bases', { params }),
  // Full map data with hexside terrain, control, and roads for movement validation
  getMapData: (params = {}) => api.get('/hexes/map', { params })
}

// Base endpoints
export const bases = {
  list: (params = {}) => api.get('/bases', { params }),
  get: (id) => api.get(`/bases/${id}`),
  atHex: (hexId) => api.get(`/bases/at/${hexId}`),
  byFaction: (factionId) => api.get(`/bases/faction/${factionId}`),
  resources: (factionId) => api.get(`/bases/faction/${factionId}/resources`),
  capitals: (params = {}) => api.get('/bases/capitals', { params }),
  // Base orders
  getOrders: (id) => api.get(`/bases/${id}/orders`),
  getEffectiveResources: (id) => api.get(`/bases/${id}/resources/effective`),
  previewHarvest: (id) => api.get(`/bases/${id}/harvest/preview`),
  queueHarvest: (id) => api.post(`/bases/${id}/orders/harvest`),
  // Expand
  validateExpand: (id, targetHex) => api.get(`/bases/${id}/expand/validate/${targetHex}`),
  getExpandableHexes: (id) => api.get(`/bases/${id}/expand/targets`),
  queueExpand: (id, targetHex) => api.post(`/bases/${id}/orders/expand/${targetHex}`),
  // Commerce
  getCommerceOptions: (id) => api.get(`/bases/${id}/commerce/options`),
  queueCommerce: (id, fromResource, toResource) => api.post(`/bases/${id}/orders/commerce`, null, { params: { from: fromResource, to: toResource } }),
  // Upgrade
  getUpgradeInfo: (id) => api.get(`/bases/${id}/upgrade/info`),
  queueUpgrade: (id) => api.post(`/bases/${id}/orders/upgrade`),
  // Rest Unit
  getRestableUnits: (id) => api.get(`/bases/${id}/rest/units`),
  validateRestUnit: (id, unitId) => api.get(`/bases/${id}/rest/validate/${unitId}`),
  queueRestUnit: (id, unitId) => api.post(`/bases/${id}/orders/rest/${unitId}`),
  // Build Unit
  getBuildableUnits: (id) => api.get(`/bases/${id}/build/units`),
  validateBuildUnit: (id, unitName) => api.get(`/bases/${id}/build/validate/${encodeURIComponent(unitName)}`),
  queueBuildUnit: (id, unitName) => api.post(`/bases/${id}/orders/build/${encodeURIComponent(unitName)}`),
  // Order management
  cancelLastOrder: (id) => api.delete(`/bases/${id}/orders/last`),
  clearOrders: (id) => api.delete(`/bases/${id}/orders`),
  // Caravans
  getCaravanTargets: (id) => api.get(`/bases/${id}/caravan/targets`),
  getCaravanNextHexes: (id, currentPath, isSea, destBaseId = null) => {
    const params = { current_path: currentPath.join(',') }
    // Only include isSea if it's explicitly true or false (null = undecided, get both)
    if (isSea !== null && isSea !== undefined) {
      params.isSea = isSea
    }
    if (destBaseId !== null) params.destBaseId = destBaseId
    return api.get(`/bases/${id}/caravan/next-hexes`, { params })
  },
  validateCaravanPath: (id, destBaseId, path, isSea) => api.post(`/bases/${id}/caravan/validate`, null, {
    params: { destBaseId, path: path.join(','), isSea }
  }),
  queueCaravan: (id, destBaseId, path, isSea) => api.post(`/bases/${id}/orders/caravan`, null, {
    params: { destBaseId, path: path.join(','), isSea }
  }),
  getBaseCaravans: (id) => api.get(`/bases/${id}/caravans`),
  // Send Resources
  getSendDestinations: (id) => api.get(`/bases/${id}/send/destinations`),
  queueSendResources: (id, destBaseId, gold, lumber, oil) => api.post(`/bases/${id}/orders/send`, null, {
    params: { destBaseId, gold, lumber, oil }
  })
}

// Caravan endpoints
export const caravans = {
  list: (params = {}) => api.get('/caravans', { params }),
  get: (id) => api.get(`/caravans/${id}`),
  forBase: (baseId) => api.get(`/caravans/base/${baseId}`),
  forInitiative: (initiative) => api.get(`/caravans/initiative/${initiative}`),
  count: (params = {}) => api.get('/caravans/count', { params })
}

// Expansion endpoints
export const expansions = {
  list: (params = {}) => api.get('/expansions', { params }),
  get: (id) => api.get(`/expansions/${id}`),
  atHex: (hexId) => api.get(`/expansions/at/${hexId}`),
  forBase: (baseId) => api.get(`/expansions/base/${baseId}`),
  byFaction: (factionId) => api.get(`/expansions/faction/${factionId}`),
  count: (params = {}) => api.get('/expansions/count', { params })
}

// Faction endpoints
export const factions = {
  list: (params = {}) => api.get('/factions', { params }),
  get: (id) => api.get(`/factions/${id}`),
  summary: (id) => api.get(`/factions/${id}/summary`),
  food: (id) => api.get(`/factions/${id}/food`),
  allFood: (params = {}) => api.get('/factions/food/all', { params }),
  byInitiative: (initiative) => api.get(`/factions/initiative/${initiative}`),
  horde: (params = {}) => api.get('/factions/horde', { params }),
  alliance: (params = {}) => api.get('/factions/alliance', { params })
}

// Order endpoints
export const orders = {
  list: () => api.get('/orders'),
  submitMovement: (order, factionId) => api.post('/orders/movement', order, { params: { faction_id: factionId } }),
  submitFastTravel: (order, factionId) => api.post('/orders/fast-travel', order, { params: { faction_id: factionId } }),
  cancelFastTravel: (unitId, factionId) => api.delete(`/orders/fast-travel/${unitId}`, { params: { faction_id: factionId } }),
  submitSpecial: (order) => api.post('/orders/special', order),
  submitEconomic: (action) => api.post('/orders/economic', action),
  cancelMovement: (unitId) => api.delete(`/orders/movement/${unitId}`),
  clearAll: (factionId = null) => api.delete('/orders/all', { params: { faction_id: factionId } })
}

// Admin endpoints
export const admin = {
  // Status
  getStatus: () => api.get('/admin/status'),
  getOrders: () => api.get('/admin/orders'),
  getCombats: () => api.get('/admin/combats'),
  
  // Turn control
  newGame: () => api.post('/admin/new-game'),
  resolveTurn: () => api.post('/admin/resolve-turn'),
  advanceInitiative: () => api.post('/admin/advance-initiative'),
  resetOrders: () => api.post('/admin/reset-orders'),
  
  // Save/Load
  listSaves: () => api.get('/admin/saves'),
  getSaveInfo: (name) => api.get(`/admin/saves/${encodeURIComponent(name)}`),
  saveGame: (name, notes = '') => api.post('/admin/save', { name, notes }),
  loadGame: (name) => api.post('/admin/load', { name }),
  deleteSave: (name) => api.delete(`/admin/saves/${encodeURIComponent(name)}`),
  quicksave: () => api.post('/admin/quicksave'),
  
  // Config
  getConfig: () => api.get('/admin/config'),
  getConfigSection: (section) => api.get(`/admin/config/${section}`),
  updateConfig: (key, value) => api.put('/admin/config', { key, value: String(value) }),
  resetConfig: () => api.post('/admin/config/reset'),
  saveConfig: () => api.post('/admin/config/save'),
  loadConfig: () => api.post('/admin/config/load'),
  
  // Debug
  getInitiatives: () => api.get('/admin/debug/initiatives'),
  debugUnit: (id) => api.get(`/admin/debug/unit/${id}`),
  debugBase: (id) => api.get(`/admin/debug/base/${id}`),
  
  // Object Manipulation - Units
  getUnitTypes: () => api.get('/admin/debug/unit-types'),
  getFactions: () => api.get('/admin/debug/factions'),
  spawnUnit: (unitName, factionId, hexId, hp = null, tier = 0) => 
    api.post('/admin/debug/units/spawn', { unit_name: unitName, faction_id: factionId, hex_id: hexId, hp, tier }),
  modifyUnit: (unitId, changes) => api.put(`/admin/debug/units/${unitId}`, changes),
  killUnit: (unitId) => api.delete(`/admin/debug/units/${unitId}`),
  resurrectUnit: (unitId, hp = null) => api.post(`/admin/debug/units/${unitId}/resurrect`, null, { params: { hp } }),
  
  // Object Manipulation - Bases
  modifyBase: (baseId, changes) => api.put(`/admin/debug/bases/${baseId}`, changes),
  addBaseResources: (baseId, gold = 0, lumber = 0, oil = 0) => 
    api.post(`/admin/debug/bases/${baseId}/add-resources`, null, { params: { gold, lumber, oil } }),
  
  // Object Manipulation - Caravans
  spawnCaravan: (originBaseId, destBaseId, path, terrainType = 'LAND') =>
    api.post('/admin/debug/caravans/spawn', { origin_base_id: originBaseId, dest_base_id: destBaseId, path, terrain_type: terrainType }),
  destroyCaravan: (caravanId) => api.delete(`/admin/debug/caravans/${caravanId}`),
  
  // Object Manipulation - Turn
  setTurnState: (turnState) => api.put('/admin/debug/turn', turnState)
}

// Health check
export const health = () => api.get('/health')

export default {
  game,
  units,
  hexes,
  bases,
  expansions,
  factions,
  orders,
  caravans,
  admin,
  health
}

