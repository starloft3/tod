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
  clearOrders: (id) => api.delete(`/bases/${id}/orders`)
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
  submitMovement: (order) => api.post('/orders/movement', order),
  submitSpecial: (order) => api.post('/orders/special', order),
  submitEconomic: (action) => api.post('/orders/economic', action),
  cancelMovement: (unitId) => api.delete(`/orders/movement/${unitId}`),
  clearAll: (factionId = null) => api.delete('/orders/all', { params: { faction_id: factionId } })
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
  health
}

