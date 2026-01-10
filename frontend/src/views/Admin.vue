<script setup>
import { ref, onMounted, computed } from 'vue'
import axios from 'axios'

const API_BASE = 'http://localhost:8000'

const adminStatus = ref(null)
const allOrders = ref(null)
const loading = ref(true)
const error = ref(null)
const actionMessage = ref(null)
const actionError = ref(null)

// Resolution log from last resolution
const resolutionLog = ref([])

// Save/Load state
const saves = ref([])
const savesLoading = ref(false)
const showSaveModal = ref(false)
const saveName = ref('')
const saveNotes = ref('')
const saveInProgress = ref(false)

// Config state
const gameConfig = ref(null)
const configLoading = ref(false)
const configExpanded = ref({})  // Track which sections are expanded
const editingConfig = ref(null)  // { key, value } being edited
const editValue = ref('')

// Object Manipulation state
const objManipExpanded = ref(false)
const unitTypes = ref([])
const allFactions = ref([])
const allBases = ref([])
const allCaravans = ref([])

// Spawn Unit form
const spawnUnit = ref({
  unitName: '',
  factionId: null,
  hexId: '',
  hp: '',
  tier: 0
})

// Modify Unit form
const modifyUnitId = ref('')
const modifyUnitData = ref(null)
const modifyUnit = ref({
  hp: '',
  max_hp: '',
  combat: '',
  movement: '',
  light_armor: '',
  heavy_armor: '',
  natural_armor: '',
  location: '',
  faction_id: null,
  tier: '',
  alive: null
})

// Modify Base form
const modifyBaseId = ref('')
const modifyBaseData = ref(null)
const modifyBase = ref({
  faction_id: null,
  tier: '',
  gold: '',
  lumber: '',
  oil: ''
})

// Turn manipulation
const turnState = ref({
  round_number: '',
  round_side: '',
  initiative: '',
  phase: ''
})

const loadAdminStatus = async () => {
  loading.value = true
  error.value = null
  try {
    const [statusRes, ordersRes] = await Promise.all([
      axios.get(`${API_BASE}/admin/status`),
      axios.get(`${API_BASE}/admin/orders`)
    ])
    adminStatus.value = statusRes.data
    allOrders.value = ordersRes.data
  } catch (e) {
    error.value = 'Failed to load admin data: ' + e.message
    console.error(e)
  } finally {
    loading.value = false
  }
}

const formatPhase = (phase) => {
  const phases = {
    'SETUP': 'Setup',
    'PLANNING': 'Planning',
    'RESOLUTION': 'Resolution',
    'COMBAT': 'Combat',
    'ECONOMIC': 'Economic',
    'END_TURN': 'End Turn'
  }
  return phases[phase] || phase
}

const phaseClass = (phase) => {
  const classes = {
    'SETUP': 'phase-setup',
    'PLANNING': 'phase-planning',
    'RESOLUTION': 'phase-resolution',
    'COMBAT': 'phase-combat',
    'ECONOMIC': 'phase-economic',
    'END_TURN': 'phase-end'
  }
  return classes[phase] || ''
}

// Actions
const resolveTurn = async () => {
  try {
    actionMessage.value = null
    actionError.value = null
    const res = await axios.post(`${API_BASE}/admin/resolve-turn`)
    actionMessage.value = res.data.message
    resolutionLog.value = res.data.data?.resolutionLog || []
    await loadAdminStatus()
  } catch (e) {
    actionError.value = e.response?.data?.message || e.message
  }
}

const resetOrders = async () => {
  if (!confirm('Are you sure you want to clear all orders?')) return
  try {
    actionMessage.value = null
    actionError.value = null
    const res = await axios.post(`${API_BASE}/admin/reset-orders`)
    actionMessage.value = res.data.message
    await loadAdminStatus()
  } catch (e) {
    actionError.value = e.response?.data?.message || e.message
  }
}

const advanceTurn = async () => {
  if (!confirm('Skip turn resolution and advance to next initiative?')) return
  try {
    actionMessage.value = null
    actionError.value = null
    const res = await axios.post(`${API_BASE}/admin/advance-initiative`)
    actionMessage.value = res.data.message
    await loadAdminStatus()
  } catch (e) {
    actionError.value = e.response?.data?.message || e.message
  }
}

const startNewGame = async () => {
  if (!confirm('Start a new game? This will reset to Horde Round 1.')) return
  try {
    actionMessage.value = null
    actionError.value = null
    const res = await axios.post(`${API_BASE}/admin/new-game`)
    actionMessage.value = res.data.message
    await loadAdminStatus()
  } catch (e) {
    actionError.value = e.response?.data?.message || e.message
  }
}

// Save/Load methods
const loadSavesList = async () => {
  savesLoading.value = true
  try {
    const res = await axios.get(`${API_BASE}/admin/saves`)
    saves.value = res.data.saves || []
  } catch (e) {
    console.error('Failed to load saves:', e)
    saves.value = []
  } finally {
    savesLoading.value = false
  }
}

const openSaveModal = () => {
  // Pre-fill with a sensible default name
  const status = adminStatus.value
  if (status?.turn) {
    saveName.value = `${status.turn.roundSide}_R${status.turn.roundNumber}_Init${status.turn.currentInitiative}`
  } else {
    saveName.value = ''
  }
  saveNotes.value = ''
  showSaveModal.value = true
}

const closeSaveModal = () => {
  showSaveModal.value = false
  saveName.value = ''
  saveNotes.value = ''
}

const saveGame = async () => {
  if (!saveName.value.trim()) {
    actionError.value = 'Save name is required'
    return
  }
  
  saveInProgress.value = true
  try {
    actionMessage.value = null
    actionError.value = null
    const res = await axios.post(`${API_BASE}/admin/save`, {
      name: saveName.value.trim(),
      notes: saveNotes.value.trim()
    })
    actionMessage.value = res.data.message
    closeSaveModal()
    await loadSavesList()
  } catch (e) {
    actionError.value = e.response?.data?.message || e.message
  } finally {
    saveInProgress.value = false
  }
}

const quicksave = async () => {
  try {
    actionMessage.value = null
    actionError.value = null
    const res = await axios.post(`${API_BASE}/admin/quicksave`)
    actionMessage.value = res.data.message
    await loadSavesList()
  } catch (e) {
    actionError.value = e.response?.data?.message || e.message
  }
}

const loadGame = async (save) => {
  if (!confirm(`Load save "${save.name}"? Current game state will be replaced.`)) return
  
  try {
    actionMessage.value = null
    actionError.value = null
    const res = await axios.post(`${API_BASE}/admin/load`, {
      name: save.name
    })
    actionMessage.value = res.data.message
    await loadAdminStatus()
  } catch (e) {
    actionError.value = e.response?.data?.message || e.message
  }
}

const deleteSave = async (save) => {
  if (!confirm(`Delete save "${save.name}"? This cannot be undone.`)) return
  
  try {
    actionMessage.value = null
    actionError.value = null
    const res = await axios.delete(`${API_BASE}/admin/saves/${encodeURIComponent(save.name)}`)
    actionMessage.value = res.data.message
    await loadSavesList()
  } catch (e) {
    actionError.value = e.response?.data?.message || e.message
  }
}

const formatSaveDate = (isoString) => {
  if (!isoString) return 'Unknown'
  try {
    const date = new Date(isoString)
    return date.toLocaleString()
  } catch {
    return isoString
  }
}

// Config methods
const loadConfig = async () => {
  configLoading.value = true
  try {
    const res = await axios.get(`${API_BASE}/admin/config`)
    gameConfig.value = res.data.config
    // Initialize all sections as collapsed
    Object.keys(res.data.config).forEach(section => {
      if (configExpanded.value[section] === undefined) {
        configExpanded.value[section] = false
      }
    })
  } catch (e) {
    console.error('Failed to load config:', e)
  } finally {
    configLoading.value = false
  }
}

const toggleConfigSection = (section) => {
  configExpanded.value[section] = !configExpanded.value[section]
}

const startEditConfig = (section, key, currentValue) => {
  editingConfig.value = { section, key, fullKey: `${section}.${key}` }
  editValue.value = String(currentValue)
}

const cancelEditConfig = () => {
  editingConfig.value = null
  editValue.value = ''
}

const saveConfigValue = async () => {
  if (!editingConfig.value) return
  
  try {
    actionMessage.value = null
    actionError.value = null
    const res = await axios.put(`${API_BASE}/admin/config`, {
      key: editingConfig.value.fullKey,
      value: editValue.value
    })
    
    if (res.data.success) {
      actionMessage.value = res.data.message
      await loadConfig()
    } else {
      actionError.value = res.data.message
    }
    cancelEditConfig()
  } catch (e) {
    actionError.value = e.response?.data?.message || e.message
  }
}

const resetConfigToDefaults = async () => {
  if (!confirm('Reset all config values to defaults?')) return
  
  try {
    actionMessage.value = null
    actionError.value = null
    const res = await axios.post(`${API_BASE}/admin/config/reset`)
    actionMessage.value = res.data.message
    await loadConfig()
  } catch (e) {
    actionError.value = e.response?.data?.message || e.message
  }
}

const persistConfig = async () => {
  try {
    actionMessage.value = null
    actionError.value = null
    const res = await axios.post(`${API_BASE}/admin/config/save`)
    actionMessage.value = res.data.message
  } catch (e) {
    actionError.value = e.response?.data?.message || e.message
  }
}

const formatConfigKey = (key) => {
  // Convert snake_case to Title Case
  return key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())
}

// ==================== Object Manipulation ====================

const loadObjectManipulationData = async () => {
  try {
    const [typesRes, factionsRes, basesRes, caravansRes] = await Promise.all([
      axios.get(`${API_BASE}/admin/debug/unit-types`),
      axios.get(`${API_BASE}/admin/debug/factions`),
      axios.get(`${API_BASE}/bases?limit=200`),
      axios.get(`${API_BASE}/caravans?limit=200`)
    ])
    unitTypes.value = typesRes.data.unit_types || []
    allFactions.value = factionsRes.data.factions || []
    allBases.value = basesRes.data || []
    allCaravans.value = caravansRes.data || []
  } catch (e) {
    console.error('Failed to load object manipulation data:', e)
  }
}

const toggleObjManip = () => {
  objManipExpanded.value = !objManipExpanded.value
  if (objManipExpanded.value && unitTypes.value.length === 0) {
    loadObjectManipulationData()
  }
}

// Spawn Unit
const doSpawnUnit = async () => {
  // Note: factionId can be 0 (Amani), so check for null explicitly
  if (!spawnUnit.value.unitName || spawnUnit.value.factionId === null || !spawnUnit.value.hexId) {
    actionError.value = 'Unit type, faction, and hex are required'
    return
  }
  
  try {
    actionMessage.value = null
    actionError.value = null
    const res = await axios.post(`${API_BASE}/admin/debug/units/spawn`, {
      unit_name: spawnUnit.value.unitName,
      faction_id: spawnUnit.value.factionId,
      hex_id: parseInt(spawnUnit.value.hexId),
      hp: spawnUnit.value.hp ? parseInt(spawnUnit.value.hp) : null,
      tier: parseInt(spawnUnit.value.tier) || 0
    })
    
    if (res.data.success) {
      actionMessage.value = res.data.message
      spawnUnit.value = { unitName: '', factionId: null, hexId: '', hp: '', tier: 0 }
      await loadAdminStatus()
    } else {
      actionError.value = res.data.message
    }
  } catch (e) {
    actionError.value = e.response?.data?.message || e.message
  }
}

// Load unit for modification
const loadUnitForModify = async () => {
  if (modifyUnitId.value === '' || modifyUnitId.value === null || modifyUnitId.value === undefined) return
  
  try {
    const res = await axios.get(`${API_BASE}/admin/debug/unit/${modifyUnitId.value}`)
    modifyUnitData.value = res.data.unit
    modifyUnit.value = {
      hp: res.data.unit.hp,
      max_hp: res.data.unit.maxHp,
      combat: res.data.unit.combat,
      movement: res.data.unit.movementMax,
      light_armor: res.data.unit.lightArmorMax,
      heavy_armor: res.data.unit.heavyArmor,
      natural_armor: res.data.unit.naturalArmor,
      location: res.data.unit.location,
      faction_id: res.data.unit.faction,
      tier: res.data.unit.tier || 0,
      alive: res.data.unit.alive
    }
  } catch (e) {
    actionError.value = `Unit ${modifyUnitId.value} not found`
    modifyUnitData.value = null
  }
}

// Apply unit modifications
const doModifyUnit = async () => {
  if (modifyUnitId.value === '' || modifyUnitId.value === null || modifyUnitId.value === undefined) return
  
  const changes = {}
  
  // Combat stats
  if (modifyUnit.value.combat !== '' && parseInt(modifyUnit.value.combat) !== modifyUnitData.value?.combat) {
    changes.combat = parseInt(modifyUnit.value.combat)
  }
  if (modifyUnit.value.max_hp !== '' && parseInt(modifyUnit.value.max_hp) !== modifyUnitData.value?.maxHp) {
    changes.max_hp = parseInt(modifyUnit.value.max_hp)
  }
  if (modifyUnit.value.hp !== '' && parseInt(modifyUnit.value.hp) !== modifyUnitData.value?.hp) {
    changes.hp = parseInt(modifyUnit.value.hp)
  }
  if (modifyUnit.value.movement !== '' && parseInt(modifyUnit.value.movement) !== modifyUnitData.value?.movementMax) {
    changes.movement = parseInt(modifyUnit.value.movement)
  }
  
  // Armor stats
  if (modifyUnit.value.light_armor !== '' && parseInt(modifyUnit.value.light_armor) !== modifyUnitData.value?.lightArmorMax) {
    changes.light_armor = parseInt(modifyUnit.value.light_armor)
  }
  if (modifyUnit.value.heavy_armor !== '' && parseInt(modifyUnit.value.heavy_armor) !== modifyUnitData.value?.heavyArmor) {
    changes.heavy_armor = parseInt(modifyUnit.value.heavy_armor)
  }
  if (modifyUnit.value.natural_armor !== '' && parseInt(modifyUnit.value.natural_armor) !== modifyUnitData.value?.naturalArmor) {
    changes.natural_armor = parseInt(modifyUnit.value.natural_armor)
  }
  
  // Position and identity
  if (modifyUnit.value.location !== '' && parseInt(modifyUnit.value.location) !== modifyUnitData.value?.location) {
    changes.location = parseInt(modifyUnit.value.location)
  }
  if (modifyUnit.value.faction_id !== null && modifyUnit.value.faction_id !== modifyUnitData.value?.faction) {
    changes.faction_id = modifyUnit.value.faction_id
  }
  if (modifyUnit.value.tier !== '' && parseInt(modifyUnit.value.tier) !== modifyUnitData.value?.tier) {
    changes.tier = parseInt(modifyUnit.value.tier)
  }
  if (modifyUnit.value.alive !== null && modifyUnit.value.alive !== modifyUnitData.value?.alive) {
    changes.alive = modifyUnit.value.alive
  }
  
  if (Object.keys(changes).length === 0) {
    actionError.value = 'No changes to apply'
    return
  }
  
  try {
    actionMessage.value = null
    actionError.value = null
    const res = await axios.put(`${API_BASE}/admin/debug/units/${modifyUnitId.value}`, changes)
    
    if (res.data.success) {
      actionMessage.value = res.data.message
      await loadUnitForModify()
      await loadAdminStatus()
    } else {
      actionError.value = res.data.message
    }
  } catch (e) {
    actionError.value = e.response?.data?.message || e.message
  }
}

// Kill/Resurrect unit
const doKillUnit = async () => {
  if (modifyUnitId.value === '' || modifyUnitId.value === null || modifyUnitId.value === undefined) return
  
  try {
    actionMessage.value = null
    actionError.value = null
    const res = await axios.delete(`${API_BASE}/admin/debug/units/${modifyUnitId.value}`)
    
    if (res.data.success) {
      actionMessage.value = res.data.message
      await loadUnitForModify()
      await loadAdminStatus()
    } else {
      actionError.value = res.data.message
    }
  } catch (e) {
    actionError.value = e.response?.data?.message || e.message
  }
}

const doResurrectUnit = async () => {
  if (modifyUnitId.value === '' || modifyUnitId.value === null || modifyUnitId.value === undefined) return
  
  try {
    actionMessage.value = null
    actionError.value = null
    const res = await axios.post(`${API_BASE}/admin/debug/units/${modifyUnitId.value}/resurrect`)
    
    if (res.data.success) {
      actionMessage.value = res.data.message
      await loadUnitForModify()
      await loadAdminStatus()
    } else {
      actionError.value = res.data.message
    }
  } catch (e) {
    actionError.value = e.response?.data?.message || e.message
  }
}

// Load base for modification
const loadBaseForModify = async () => {
  if (!modifyBaseId.value) return
  
  try {
    const res = await axios.get(`${API_BASE}/admin/debug/base/${modifyBaseId.value}`)
    modifyBaseData.value = res.data.base
    modifyBase.value = {
      faction_id: res.data.base.faction,
      tier: res.data.base.tier,
      gold: res.data.base.gold,
      lumber: res.data.base.lumber,
      oil: res.data.base.oil
    }
  } catch (e) {
    actionError.value = `Base ${modifyBaseId.value} not found`
    modifyBaseData.value = null
  }
}

// Apply base modifications
const doModifyBase = async () => {
  if (!modifyBaseId.value) return
  
  const changes = {}
  if (modifyBase.value.faction_id !== null && modifyBase.value.faction_id !== modifyBaseData.value?.faction) {
    changes.faction_id = modifyBase.value.faction_id
  }
  if (modifyBase.value.tier !== '' && parseInt(modifyBase.value.tier) !== modifyBaseData.value?.tier) {
    changes.tier = parseInt(modifyBase.value.tier)
  }
  if (modifyBase.value.gold !== '' && parseInt(modifyBase.value.gold) !== modifyBaseData.value?.gold) {
    changes.gold = parseInt(modifyBase.value.gold)
  }
  if (modifyBase.value.lumber !== '' && parseInt(modifyBase.value.lumber) !== modifyBaseData.value?.lumber) {
    changes.lumber = parseInt(modifyBase.value.lumber)
  }
  if (modifyBase.value.oil !== '' && parseInt(modifyBase.value.oil) !== modifyBaseData.value?.oil) {
    changes.oil = parseInt(modifyBase.value.oil)
  }
  
  if (Object.keys(changes).length === 0) {
    actionError.value = 'No changes to apply'
    return
  }
  
  try {
    actionMessage.value = null
    actionError.value = null
    const res = await axios.put(`${API_BASE}/admin/debug/bases/${modifyBaseId.value}`, changes)
    
    if (res.data.success) {
      actionMessage.value = res.data.message
      await loadBaseForModify()
      await loadAdminStatus()
    } else {
      actionError.value = res.data.message
    }
  } catch (e) {
    actionError.value = e.response?.data?.message || e.message
  }
}

// Set turn state
const doSetTurnState = async () => {
  const changes = {}
  if (turnState.value.round_number) changes.round_number = parseInt(turnState.value.round_number)
  if (turnState.value.round_side) changes.round_side = turnState.value.round_side
  if (turnState.value.initiative) changes.initiative = parseInt(turnState.value.initiative)
  if (turnState.value.phase) changes.phase = turnState.value.phase
  
  if (Object.keys(changes).length === 0) {
    actionError.value = 'No turn state changes specified'
    return
  }
  
  try {
    actionMessage.value = null
    actionError.value = null
    const res = await axios.put(`${API_BASE}/admin/debug/turn`, changes)
    
    if (res.data.success) {
      actionMessage.value = res.data.message
      turnState.value = { round_number: '', round_side: '', initiative: '', phase: '' }
      await loadAdminStatus()
    } else {
      actionError.value = res.data.message
    }
  } catch (e) {
    actionError.value = e.response?.data?.message || e.message
  }
}

// Destroy caravan
const doDestroyCaravan = async (caravanId) => {
  try {
    actionMessage.value = null
    actionError.value = null
    const res = await axios.delete(`${API_BASE}/admin/debug/caravans/${caravanId}`)
    
    if (res.data.success) {
      actionMessage.value = res.data.message
      await loadObjectManipulationData()
    } else {
      actionError.value = res.data.message
    }
  } catch (e) {
    actionError.value = e.response?.data?.message || e.message
  }
}

const getValueType = (value) => {
  if (typeof value === 'boolean') return 'boolean'
  if (typeof value === 'number') {
    if (Number.isInteger(value)) return 'integer'
    return 'float'
  }
  return 'string'
}

// Computed
const totalOrders = computed(() => {
  if (!adminStatus.value?.orders?.factions) return 0
  return Object.values(adminStatus.value.orders.factions)
    .reduce((sum, f) => sum + f.totalOrders, 0)
})

const factionsWithOrders = computed(() => {
  if (!adminStatus.value?.factionStatus) return []
  return Object.entries(adminStatus.value.factionStatus)
    .filter(([_, f]) => !f.isDefeated)
    .map(([id, f]) => ({
      id: parseInt(id),
      ...f,
      orders: adminStatus.value.orders?.factions?.[id] || { totalOrders: 0 }
    }))
    .sort((a, b) => a.initiative - b.initiative)
})

onMounted(() => {
  loadAdminStatus()
  loadSavesList()
  loadConfig()
})
</script>

<template>
  <div class="admin-page fade-in">
    <header class="page-header">
      <div>
        <h2>Admin Panel</h2>
        <p class="text-muted">Game Master Controls</p>
      </div>
      <button class="btn btn-secondary" @click="loadAdminStatus" :disabled="loading">
        Refresh
      </button>
    </header>

    <!-- Loading -->
    <div v-if="loading" class="loading">
      <div class="spinner"></div>
      <p>Loading admin data...</p>
    </div>

    <!-- Error -->
    <div v-else-if="error" class="error-box">
      {{ error }}
    </div>

    <!-- Content -->
    <div v-else class="admin-content">
      <!-- Action Messages -->
      <div v-if="actionMessage" class="action-message success">
        {{ actionMessage }}
      </div>
      <div v-if="actionError" class="action-message error">
        {{ actionError }}
      </div>

      <!-- Game Status Card -->
      <section class="card status-card">
        <h3>Game Status</h3>
        <div class="status-grid">
          <div class="status-item wide">
            <span class="status-label">Round</span>
            <span class="status-value round-display">
              <span :class="adminStatus.turn.roundSide === 'HORDE' ? 'horde-text' : 'alliance-text'">
                {{ adminStatus.turn.roundSide }}
              </span>
              Round {{ adminStatus.turn.roundNumber }}
            </span>
          </div>
          <div class="status-item">
            <span class="status-label">Initiative</span>
            <span class="status-value initiative-number">{{ adminStatus.turn.currentInitiative }}</span>
          </div>
          <div class="status-item">
            <span class="status-label">Phase</span>
            <span class="status-value phase-tag" :class="phaseClass(adminStatus.turn.phase)">
              {{ formatPhase(adminStatus.turn.phase) }}
            </span>
          </div>
          <div class="status-item">
            <span class="status-label">Orders</span>
            <span class="status-value orders-count">{{ totalOrders }}</span>
          </div>
        </div>
        
        <!-- Current Factions -->
        <div class="current-factions" v-if="adminStatus.turn.currentFactions?.length">
          <span class="factions-label">Active Factions:</span>
          <span class="faction-tags">
            <span v-for="name in adminStatus.turn.currentFactions" :key="name" class="faction-tag">
              {{ name }}
            </span>
          </span>
        </div>
        
        <!-- Initiative Progress -->
        <div class="initiative-progress">
          <div class="progress-row">
            <span class="progress-label">Remaining:</span>
            <span class="initiative-badges">
              <span 
                v-for="init in adminStatus.turn.remainingInitiatives" 
                :key="init" 
                class="init-badge remaining"
              >
                {{ init }}
              </span>
              <span v-if="!adminStatus.turn.remainingInitiatives?.length" class="text-muted">
                None (round complete)
              </span>
            </span>
          </div>
          <div class="progress-row">
            <span class="progress-label">Completed:</span>
            <span class="initiative-badges">
              <span 
                v-for="init in adminStatus.turn.completedInitiatives" 
                :key="init" 
                class="init-badge completed"
              >
                {{ init }}
              </span>
              <span v-if="!adminStatus.turn.completedInitiatives?.length" class="text-muted">
                None yet
              </span>
            </span>
          </div>
        </div>
      </section>

      <!-- Turn Control Card -->
      <section class="card actions-card">
        <h3>Turn Control</h3>
        <p class="text-muted">Submit orders via Map, then resolve here</p>
        
        <div class="main-action">
          <button 
            class="btn btn-gold btn-large" 
            @click="resolveTurn"
          >
            Resolve Turn
          </button>
          <span class="action-hint">
            Process all orders and advance to next initiative
          </span>
        </div>
        
        <div class="secondary-actions">
          <button class="btn btn-secondary btn-sm" @click="startNewGame">
            Start New Game
          </button>
          <button class="btn btn-secondary btn-sm" @click="resetOrders">
            Clear Orders
          </button>
          <button class="btn btn-secondary btn-sm" @click="advanceTurn">
            Skip (No Resolution)
          </button>
        </div>
      </section>

      <!-- Save/Load Card -->
      <section class="card saves-card">
        <h3>💾 Save/Load Game</h3>
        <p class="text-muted">Persist game state to file for testing and iteration</p>
        
        <div class="save-actions">
          <button class="btn btn-primary" @click="openSaveModal">
            Save Game
          </button>
          <button class="btn btn-secondary" @click="quicksave">
            Quicksave
          </button>
          <button class="btn btn-secondary btn-sm" @click="loadSavesList" :disabled="savesLoading">
            {{ savesLoading ? 'Loading...' : 'Refresh' }}
          </button>
        </div>
        
        <!-- Saves List -->
        <div class="saves-list" v-if="saves.length > 0">
          <div 
            v-for="save in saves" 
            :key="save.filename" 
            class="save-item"
            :class="{ 'has-error': save.error }"
          >
            <div class="save-info">
              <div class="save-name">{{ save.name || save.filename }}</div>
              <div class="save-meta">
                <span class="save-date">{{ formatSaveDate(save.created_at) }}</span>
                <span v-if="save.round_number" class="save-turn">
                  {{ save.round_side }} R{{ save.round_number }} · Init {{ save.initiative }}
                </span>
                <span v-if="save.unit_count" class="save-units">
                  {{ save.unit_count }} units · {{ save.base_count }} bases
                </span>
              </div>
              <div v-if="save.notes" class="save-notes">{{ save.notes }}</div>
              <div v-if="save.config_modified" class="save-config" :title="save.config_notes">
                ⚙️ Custom config: {{ save.config_notes || 'Modified' }}
              </div>
              <div v-if="save.error" class="save-error">⚠️ {{ save.error }}</div>
            </div>
            <div class="save-buttons">
              <button 
                class="btn btn-primary btn-sm" 
                @click="loadGame(save)"
                :disabled="!!save.error"
              >
                Load
              </button>
              <button class="btn btn-danger btn-sm" @click="deleteSave(save)">
                Delete
              </button>
            </div>
          </div>
        </div>
        
        <div v-else class="no-saves">
          <p class="text-muted">No saves yet. Save your game to create a restore point!</p>
        </div>
      </section>

      <!-- Configuration Card -->
      <section class="card config-card">
        <div class="config-header">
          <h3>⚙️ Game Configuration</h3>
          <div class="config-actions">
            <button class="btn btn-secondary btn-sm" @click="loadConfig" :disabled="configLoading">
              {{ configLoading ? 'Loading...' : 'Refresh' }}
            </button>
            <button class="btn btn-secondary btn-sm" @click="resetConfigToDefaults">
              Reset Defaults
            </button>
            <button class="btn btn-primary btn-sm" @click="persistConfig">
              Save to File
            </button>
          </div>
        </div>
        <p class="text-muted">Tweak game rules and constants at runtime</p>
        
        <div class="config-sections" v-if="gameConfig">
          <div 
            v-for="(values, section) in gameConfig" 
            :key="section" 
            class="config-section"
          >
            <div class="section-header" @click="toggleConfigSection(section)">
              <span class="section-toggle">{{ configExpanded[section] ? '▼' : '▶' }}</span>
              <span class="section-name">{{ formatConfigKey(section) }}</span>
              <span class="section-count">{{ Object.keys(values).length }} values</span>
            </div>
            
            <div v-if="configExpanded[section]" class="section-values">
              <div 
                v-for="(value, key) in values" 
                :key="key" 
                class="config-item"
                :class="{ editing: editingConfig?.fullKey === `${section}.${key}` }"
              >
                <div class="config-key">
                  <span class="key-name">{{ formatConfigKey(key) }}</span>
                  <span class="key-type" :class="getValueType(value)">{{ getValueType(value) }}</span>
                </div>
                
                <div class="config-value" v-if="editingConfig?.fullKey !== `${section}.${key}`">
                  <span 
                    v-if="typeof value === 'boolean'" 
                    class="value-badge"
                    :class="value ? 'true' : 'false'"
                  >
                    {{ value ? 'ON' : 'OFF' }}
                  </span>
                  <span v-else class="value-number">{{ value }}</span>
                  <button class="btn-edit" @click="startEditConfig(section, key, value)">
                    ✏️
                  </button>
                </div>
                
                <div class="config-edit" v-else>
                  <input 
                    v-if="typeof value === 'boolean'"
                    type="checkbox"
                    :checked="editValue === 'true'"
                    @change="editValue = $event.target.checked ? 'true' : 'false'"
                  />
                  <input 
                    v-else
                    type="text"
                    v-model="editValue"
                    class="edit-input"
                    @keyup.enter="saveConfigValue"
                    @keyup.escape="cancelEditConfig"
                  />
                  <button class="btn btn-sm btn-primary" @click="saveConfigValue">✓</button>
                  <button class="btn btn-sm btn-secondary" @click="cancelEditConfig">✕</button>
                </div>
              </div>
            </div>
          </div>
        </div>
        
        <div v-else class="config-loading">
          <p class="text-muted">Loading configuration...</p>
        </div>
      </section>

      <!-- Object Manipulation Card -->
      <section class="card objmanip-card">
        <div class="objmanip-header" @click="toggleObjManip">
          <h3>🛠️ Object Manipulation</h3>
          <span class="toggle-indicator">{{ objManipExpanded ? '▼' : '▶' }}</span>
        </div>
        <p class="text-muted">Debug tools: spawn, modify, and destroy game objects</p>
        
        <div v-if="objManipExpanded" class="objmanip-content">
          <!-- Spawn Unit -->
          <div class="objmanip-section">
            <h4>🗡️ Spawn Unit</h4>
            <div class="form-row">
              <div class="form-group">
                <label>Unit Type</label>
                <select v-model="spawnUnit.unitName" class="form-select">
                  <option value="">-- Select Unit --</option>
                  <option v-for="ut in unitTypes" :key="ut.name" :value="ut.name">
                    {{ ut.name }} (HP: {{ ut.max_hp }}, Combat: {{ ut.combat }})
                  </option>
                </select>
              </div>
              <div class="form-group">
                <label>Faction</label>
                <select v-model="spawnUnit.factionId" class="form-select">
                  <option :value="null">-- Select Faction --</option>
                  <option v-for="f in allFactions" :key="f.id" :value="f.id">
                    {{ f.name }} (Init {{ f.initiative }})
                  </option>
                </select>
              </div>
              <div class="form-group">
                <label>Hex ID</label>
                <input type="number" v-model="spawnUnit.hexId" class="form-input" placeholder="e.g. 765" />
              </div>
            </div>
            <div class="form-row">
              <div class="form-group">
                <label>HP (optional)</label>
                <input type="number" v-model="spawnUnit.hp" class="form-input" placeholder="Max HP" />
              </div>
              <div class="form-group">
                <label>Tier (0-4)</label>
                <input type="number" v-model="spawnUnit.tier" class="form-input" min="0" max="4" />
              </div>
              <div class="form-group">
                <label>&nbsp;</label>
                <button class="btn btn-primary" @click="doSpawnUnit">Spawn Unit</button>
              </div>
            </div>
          </div>
          
          <!-- Modify Unit -->
          <div class="objmanip-section">
            <h4>⚔️ Modify Unit</h4>
            <div class="form-row">
              <div class="form-group">
                <label>Unit ID</label>
                <input type="number" v-model="modifyUnitId" class="form-input" placeholder="e.g. 42" />
              </div>
              <div class="form-group">
                <label>&nbsp;</label>
                <button 
                  class="btn btn-primary" 
                  @click="loadUnitForModify"
                  :disabled="modifyUnitId === '' || modifyUnitId === null || modifyUnitId === undefined"
                >
                  Load Unit
                </button>
              </div>
            </div>
            
            <div v-if="modifyUnitData" class="modify-form">
              <p class="modify-info">
                <strong>{{ modifyUnitData.name }}</strong> ({{ modifyUnitData.factionName }})
                <span :class="modifyUnitData.alive ? 'alive' : 'dead'">
                  {{ modifyUnitData.alive ? '✓ Alive' : '✗ Dead' }}
                </span>
              </p>
              
              <!-- Combat Stats Row -->
              <div class="form-section-label">⚔️ Combat Stats</div>
              <div class="form-row">
                <div class="form-group">
                  <label>Combat <span class="hint">(10-80)</span></label>
                  <input type="number" v-model="modifyUnit.combat" class="form-input" min="10" max="80" />
                </div>
                <div class="form-group">
                  <label>Max HP <span class="hint">(1-30)</span></label>
                  <input type="number" v-model="modifyUnit.max_hp" class="form-input" min="1" max="30" />
                </div>
                <div class="form-group">
                  <label>HP <span class="hint">(1-Max)</span></label>
                  <input type="number" v-model="modifyUnit.hp" class="form-input" min="1" :max="modifyUnit.max_hp" />
                </div>
                <div class="form-group">
                  <label>Movement <span class="hint">(1-5)</span></label>
                  <input type="number" v-model="modifyUnit.movement" class="form-input" min="1" max="5" />
                </div>
              </div>
              
              <!-- Armor Stats Row -->
              <div class="form-section-label">🛡️ Armor</div>
              <div class="form-row">
                <div class="form-group">
                  <label>Light Armor <span class="hint">(0-5)</span></label>
                  <input type="number" v-model="modifyUnit.light_armor" class="form-input" min="0" max="5" />
                </div>
                <div class="form-group">
                  <label>Heavy Armor <span class="hint">(0-5)</span></label>
                  <input type="number" v-model="modifyUnit.heavy_armor" class="form-input" min="0" max="5" />
                </div>
                <div class="form-group">
                  <label>Natural Armor <span class="hint">(0-5)</span></label>
                  <input type="number" v-model="modifyUnit.natural_armor" class="form-input" min="0" max="5" />
                </div>
              </div>
              
              <!-- Position & Identity Row -->
              <div class="form-section-label">📍 Position & Identity</div>
              <div class="form-row">
                <div class="form-group">
                  <label>Location (Hex)</label>
                  <input type="number" v-model="modifyUnit.location" class="form-input" />
                </div>
                <div class="form-group">
                  <label>Tier <span class="hint">(0-4)</span></label>
                  <input type="number" v-model="modifyUnit.tier" class="form-input" min="0" max="4" />
                </div>
                <div class="form-group">
                  <label>Faction</label>
                  <select v-model="modifyUnit.faction_id" class="form-select">
                    <option :value="null">-- No Change --</option>
                    <option v-for="f in allFactions" :key="f.id" :value="f.id">
                      {{ f.name }}
                    </option>
                  </select>
                </div>
              </div>
              
              <!-- Action Buttons -->
              <div class="form-row btn-row">
                <button class="btn btn-primary" @click="doModifyUnit">Apply Changes</button>
                <button class="btn btn-danger" @click="doKillUnit" :disabled="!modifyUnitData.alive">Kill</button>
                <button class="btn btn-success" @click="doResurrectUnit" :disabled="modifyUnitData.alive">Resurrect</button>
              </div>
            </div>
          </div>
          
          <!-- Modify Base -->
          <div class="objmanip-section">
            <h4>🏰 Modify Base</h4>
            <div class="form-row">
              <div class="form-group">
                <label>Base</label>
                <select v-model="modifyBaseId" class="form-select" @change="loadBaseForModify">
                  <option value="">-- Select Base --</option>
                  <option v-for="b in allBases" :key="b.id" :value="b.id">
                    {{ b.name }} (Tier {{ b.tier }}, Hex {{ b.location }})
                  </option>
                </select>
              </div>
            </div>
            
            <div v-if="modifyBaseData" class="modify-form">
              <p class="modify-info">
                <strong>{{ modifyBaseData.name }}</strong> - Tier {{ modifyBaseData.tier }}
                (🪙{{ modifyBaseData.gold }} 🪵{{ modifyBaseData.lumber }} 🛢️{{ modifyBaseData.oil }})
              </p>
              
              <div class="form-row">
                <div class="form-group">
                  <label>Tier (1-3)</label>
                  <input type="number" v-model="modifyBase.tier" class="form-input" min="1" max="3" />
                </div>
                <div class="form-group">
                  <label>Gold</label>
                  <input type="number" v-model="modifyBase.gold" class="form-input" min="0" />
                </div>
                <div class="form-group">
                  <label>Lumber</label>
                  <input type="number" v-model="modifyBase.lumber" class="form-input" min="0" />
                </div>
                <div class="form-group">
                  <label>Oil</label>
                  <input type="number" v-model="modifyBase.oil" class="form-input" min="0" />
                </div>
              </div>
              <div class="form-row">
                <div class="form-group">
                  <label>Faction</label>
                  <select v-model="modifyBase.faction_id" class="form-select">
                    <option :value="null">-- No Change --</option>
                    <option v-for="f in allFactions" :key="f.id" :value="f.id">
                      {{ f.name }}
                    </option>
                  </select>
                </div>
                <div class="form-group">
                  <label>&nbsp;</label>
                  <button class="btn btn-primary" @click="doModifyBase">Apply Changes</button>
                </div>
              </div>
            </div>
          </div>
          
          <!-- Turn/Phase Manipulation -->
          <div class="objmanip-section">
            <h4>⏱️ Turn/Phase Manipulation</h4>
            <div class="form-row">
              <div class="form-group">
                <label>Round</label>
                <input type="number" v-model="turnState.round_number" class="form-input" placeholder="1, 2, 3..." min="1" />
              </div>
              <div class="form-group">
                <label>Side</label>
                <select v-model="turnState.round_side" class="form-select">
                  <option value="">-- No Change --</option>
                  <option value="HORDE">HORDE</option>
                  <option value="ALLIANCE">ALLIANCE</option>
                </select>
              </div>
              <div class="form-group">
                <label>Initiative</label>
                <input type="number" v-model="turnState.initiative" class="form-input" placeholder="1-10" />
              </div>
              <div class="form-group">
                <label>Phase</label>
                <select v-model="turnState.phase" class="form-select">
                  <option value="">-- No Change --</option>
                  <option value="PLANNING">PLANNING</option>
                  <option value="RESOLUTION">RESOLUTION</option>
                </select>
              </div>
              <div class="form-group">
                <label>&nbsp;</label>
                <button class="btn btn-primary" @click="doSetTurnState">Apply</button>
              </div>
            </div>
          </div>
          
          <!-- Caravans -->
          <div class="objmanip-section" v-if="allCaravans.length > 0">
            <h4>🛤️ Caravans ({{ allCaravans.length }})</h4>
            <div class="caravan-list">
              <div v-for="c in allCaravans" :key="c.id" class="caravan-item">
                <span class="caravan-info">
                  #{{ c.id }}: {{ c.origin_base_name || 'Base ' + c.origin_base_id }} ↔ 
                  {{ c.dest_base_name || 'Base ' + c.destination_base_id }}
                  ({{ c.terrain_type }}, {{ c.path?.length || 0 }} hexes)
                </span>
                <button class="btn btn-danger btn-sm" @click="doDestroyCaravan(c.id)">Destroy</button>
              </div>
            </div>
          </div>
        </div>
      </section>

      <!-- Faction Orders Table -->
      <section class="card orders-card">
        <h3>Faction Orders</h3>
        <p class="text-muted">Orders submitted by each faction</p>
        
        <div class="table-container">
          <table class="data-table">
            <thead>
              <tr>
                <th>Faction</th>
                <th>Initiative</th>
                <th>Unit Orders</th>
                <th>Base Orders</th>
                <th>Total</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="faction in factionsWithOrders" :key="faction.id">
                <td class="faction-name">{{ faction.name }}</td>
                <td>
                  <span class="initiative-badge" :class="faction.isHorde ? 'horde' : 'alliance'">
                    {{ faction.initiative }}
                  </span>
                </td>
                <td>{{ faction.orders.unitOrders || 0 }}</td>
                <td>{{ faction.orders.baseOrders || 0 }}</td>
                <td class="order-total">{{ faction.orders.totalOrders || 0 }}</td>
                <td>
                  <span v-if="faction.ordersSubmitted" class="status-badge locked">
                    Locked
                  </span>
                  <span v-else-if="faction.orderCount > 0" class="status-badge pending">
                    Pending
                  </span>
                  <span v-else class="status-badge none">
                    No Orders
                  </span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>

      <!-- Resolution Log -->
      <section v-if="resolutionLog.length > 0" class="card log-card">
        <h3>Resolution Log</h3>
        <p class="text-muted">Last turn resolution events</p>
        
        <div class="log-entries">
          <div v-for="(entry, idx) in resolutionLog" :key="idx" class="log-entry">
            <span class="log-type" :class="entry.type">{{ entry.type }}</span>
            <span class="log-faction">{{ entry.faction }}</span>
            <span class="log-detail">
              <template v-if="entry.type === 'movement'">
                {{ entry.unit }} moving through {{ entry.path?.length || 0 }} hexes
              </template>
              <template v-else-if="entry.type === 'build_unit'">
                Building {{ entry.unitType }} at {{ entry.base }}
              </template>
              <template v-else>
                {{ JSON.stringify(entry) }}
              </template>
            </span>
            <span class="log-status" :class="entry.status">{{ entry.status }}</span>
          </div>
        </div>
      </section>
    </div>
    
    <!-- Save Modal -->
    <div v-if="showSaveModal" class="modal-overlay" @click.self="closeSaveModal">
      <div class="modal save-modal">
        <h3>💾 Save Game</h3>
        
        <div class="form-group">
          <label for="save-name">Save Name</label>
          <input 
            id="save-name"
            type="text" 
            v-model="saveName" 
            placeholder="e.g., Horde_R2_BeforeAttack"
            class="form-input"
            @keyup.enter="saveGame"
          />
        </div>
        
        <div class="form-group">
          <label for="save-notes">Notes (optional)</label>
          <textarea 
            id="save-notes"
            v-model="saveNotes" 
            placeholder="Add any notes about this save point..."
            class="form-textarea"
            rows="3"
          ></textarea>
        </div>
        
        <div class="modal-actions">
          <button class="btn btn-secondary" @click="closeSaveModal">
            Cancel
          </button>
          <button 
            class="btn btn-gold" 
            @click="saveGame"
            :disabled="!saveName.trim() || saveInProgress"
          >
            {{ saveInProgress ? 'Saving...' : 'Save Game' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.admin-page {
  max-width: 1200px;
  margin: 0 auto;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--space-xl);
}

.admin-content {
  display: flex;
  flex-direction: column;
  gap: var(--space-lg);
}

/* Cards */
.card {
  background: var(--color-bg-secondary);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  padding: var(--space-lg);
}

.card h3 {
  color: var(--color-gold);
  margin-bottom: var(--space-xs);
}

/* Status Grid */
.status-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
  gap: var(--space-md);
  margin-top: var(--space-md);
}

.status-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: var(--space-md);
  background: var(--color-bg-tertiary);
  border-radius: var(--radius-sm);
}

.status-label {
  font-size: 0.75rem;
  text-transform: uppercase;
  letter-spacing: 0.1em;
  color: var(--color-text-muted);
}

.status-value {
  font-family: var(--font-display);
  font-size: 1.5rem;
  color: var(--color-gold);
}

.turn-number {
  font-size: 2rem;
}

.orders-count {
  color: var(--color-blood-light);
}

.status-item.wide {
  grid-column: span 2;
}

.round-display {
  font-size: 1.2rem;
}

.horde-text {
  color: var(--color-blood-light);
}

.alliance-text {
  color: steelblue;
}

.initiative-number {
  font-size: 2rem;
}

/* Current Factions */
.current-factions {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  margin-top: var(--space-md);
  padding: var(--space-sm) var(--space-md);
  background: var(--color-bg-tertiary);
  border-radius: var(--radius-sm);
}

.factions-label {
  font-size: 0.8rem;
  color: var(--color-text-muted);
  text-transform: uppercase;
}

.faction-tags {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-xs);
}

.faction-tag {
  padding: 2px 8px;
  background: rgba(201, 162, 39, 0.2);
  border: 1px solid var(--color-gold);
  border-radius: 4px;
  font-size: 0.85rem;
  color: var(--color-gold);
}

/* Initiative Progress */
.initiative-progress {
  margin-top: var(--space-md);
  padding: var(--space-sm) var(--space-md);
  background: var(--color-bg-tertiary);
  border-radius: var(--radius-sm);
}

.progress-row {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  margin-bottom: var(--space-xs);
}

.progress-row:last-child {
  margin-bottom: 0;
}

.progress-label {
  font-size: 0.75rem;
  color: var(--color-text-muted);
  text-transform: uppercase;
  min-width: 80px;
}

.initiative-badges {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-xs);
}

.init-badge {
  display: inline-block;
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 0.8rem;
  font-weight: bold;
}

.init-badge.remaining {
  background: rgba(201, 162, 39, 0.3);
  color: var(--color-gold);
}

.init-badge.completed {
  background: rgba(74, 122, 74, 0.3);
  color: #8fbc8f;
}

/* Phase Tags */
.phase-tag {
  padding: var(--space-xs) var(--space-sm);
  border-radius: var(--radius-sm);
  font-size: 0.9rem;
}

.phase-planning { background: rgba(74, 122, 74, 0.3); color: #8fbc8f; }
.phase-resolution { background: rgba(201, 162, 39, 0.3); color: var(--color-gold); }
.phase-combat { background: rgba(139, 69, 69, 0.3); color: var(--color-blood-light); }
.phase-setup { background: rgba(100, 100, 100, 0.3); color: #aaa; }

/* Main Action */
.main-action {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--space-sm);
  margin-top: var(--space-lg);
  padding: var(--space-lg);
  background: var(--color-bg-tertiary);
  border-radius: var(--radius-md);
  border: 1px solid var(--color-border);
}

.action-hint {
  font-size: 0.8rem;
  color: var(--color-text-muted);
}

.btn-large {
  padding: var(--space-md) var(--space-xxl);
  font-size: 1.1rem;
}

.secondary-actions {
  display: flex;
  gap: var(--space-sm);
  margin-top: var(--space-lg);
  padding-top: var(--space-md);
  border-top: 1px solid var(--color-border);
  justify-content: center;
}

.btn {
  padding: var(--space-sm) var(--space-lg);
  border-radius: var(--radius-sm);
  font-family: var(--font-display);
  font-size: 0.9rem;
  cursor: pointer;
  transition: all var(--transition-fast);
  border: 1px solid transparent;
}

.btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-primary {
  background: var(--color-bg-tertiary);
  border-color: var(--color-gold);
  color: var(--color-gold);
}

.btn-primary:hover:not(:disabled) {
  background: rgba(201, 162, 39, 0.2);
}

.btn-warning {
  background: rgba(255, 165, 0, 0.2);
  border-color: orange;
  color: orange;
}

.btn-danger {
  background: rgba(139, 69, 69, 0.2);
  border-color: var(--color-blood-light);
  color: var(--color-blood-light);
}

.btn-gold {
  background: var(--color-gold);
  color: var(--color-bg-primary);
  font-weight: bold;
}

.btn-gold:hover:not(:disabled) {
  background: var(--color-gold-light);
}

.btn-secondary {
  background: var(--color-bg-tertiary);
  border-color: var(--color-border);
  color: var(--color-text-secondary);
}

.btn-sm {
  padding: var(--space-xs) var(--space-md);
  font-size: 0.8rem;
}

/* Table */
.table-container {
  margin-top: var(--space-md);
  overflow-x: auto;
}

.data-table {
  width: 100%;
  border-collapse: collapse;
}

.data-table th,
.data-table td {
  padding: var(--space-sm) var(--space-md);
  text-align: left;
  border-bottom: 1px solid var(--color-border);
}

.data-table th {
  font-size: 0.75rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--color-text-muted);
  background: var(--color-bg-tertiary);
}

.faction-name {
  font-family: var(--font-display);
  color: var(--color-text-primary);
}

.order-total {
  font-weight: bold;
  color: var(--color-gold);
}

.initiative-badge {
  display: inline-block;
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 0.8rem;
}

.initiative-badge.horde {
  background: rgba(139, 69, 69, 0.3);
  color: var(--color-blood-light);
}

.initiative-badge.alliance {
  background: rgba(70, 130, 180, 0.3);
  color: steelblue;
}

.status-badge {
  display: inline-block;
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 0.75rem;
  text-transform: uppercase;
}

.status-badge.locked {
  background: rgba(201, 162, 39, 0.3);
  color: var(--color-gold);
}

.status-badge.pending {
  background: rgba(74, 122, 74, 0.3);
  color: #8fbc8f;
}

.status-badge.none {
  background: rgba(100, 100, 100, 0.3);
  color: #888;
}

/* Action Messages */
.action-message {
  padding: var(--space-md);
  border-radius: var(--radius-sm);
  margin-bottom: var(--space-md);
}

.action-message.success {
  background: rgba(74, 122, 74, 0.2);
  border: 1px solid #4a7a4a;
  color: #8fbc8f;
}

.action-message.error {
  background: rgba(139, 69, 69, 0.2);
  border: 1px solid var(--color-blood);
  color: var(--color-blood-light);
}

/* Resolution Log */
.log-entries {
  max-height: 300px;
  overflow-y: auto;
  margin-top: var(--space-md);
}

.log-entry {
  display: flex;
  align-items: center;
  gap: var(--space-md);
  padding: var(--space-sm);
  background: var(--color-bg-tertiary);
  border-radius: var(--radius-sm);
  margin-bottom: var(--space-xs);
  font-size: 0.85rem;
}

.log-type {
  padding: 2px 6px;
  border-radius: 3px;
  font-size: 0.7rem;
  text-transform: uppercase;
  min-width: 70px;
  text-align: center;
}

.log-type.movement {
  background: rgba(70, 130, 180, 0.3);
  color: steelblue;
}

.log-type.build_unit {
  background: rgba(201, 162, 39, 0.3);
  color: var(--color-gold);
}

.log-faction {
  color: var(--color-text-muted);
  min-width: 100px;
}

.log-detail {
  flex: 1;
  color: var(--color-text-secondary);
}

.log-status {
  font-size: 0.7rem;
  text-transform: uppercase;
  color: #888;
}

.log-status.pending {
  color: orange;
}

.log-status.complete {
  color: #8fbc8f;
}

/* Loading */
.loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: var(--space-xxl);
}

.spinner {
  width: 40px;
  height: 40px;
  border: 3px solid var(--color-border);
  border-top-color: var(--color-gold);
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.error-box {
  padding: var(--space-lg);
  background: rgba(139, 69, 69, 0.2);
  border: 1px solid var(--color-blood);
  border-radius: var(--radius-md);
  color: var(--color-blood-light);
}

/* Save/Load Styles */
.saves-card h3 {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
}

.save-actions {
  display: flex;
  gap: var(--space-sm);
  margin-top: var(--space-md);
  margin-bottom: var(--space-lg);
}

.saves-list {
  display: flex;
  flex-direction: column;
  gap: var(--space-sm);
  max-height: 400px;
  overflow-y: auto;
}

.save-item {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: var(--space-md);
  padding: var(--space-md);
  background: var(--color-bg-tertiary);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
}

.save-item.has-error {
  border-color: var(--color-blood);
  opacity: 0.7;
}

.save-info {
  flex: 1;
  min-width: 0;
}

.save-name {
  font-family: var(--font-display);
  font-size: 1rem;
  color: var(--color-gold);
  margin-bottom: var(--space-xs);
}

.save-meta {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-sm);
  font-size: 0.8rem;
  color: var(--color-text-muted);
}

.save-meta span:not(:last-child)::after {
  content: '·';
  margin-left: var(--space-sm);
  color: var(--color-text-muted);
}

.save-turn {
  color: var(--color-text-secondary);
}

.save-notes {
  margin-top: var(--space-xs);
  font-size: 0.85rem;
  color: var(--color-text-secondary);
  font-style: italic;
}

.save-error {
  margin-top: var(--space-xs);
  font-size: 0.8rem;
  color: var(--color-blood-light);
}

.save-config {
  margin-top: var(--space-xs);
  font-size: 0.75rem;
  color: cornflowerblue;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 300px;
}

.save-buttons {
  display: flex;
  gap: var(--space-xs);
  flex-shrink: 0;
}

.no-saves {
  padding: var(--space-lg);
  text-align: center;
  background: var(--color-bg-tertiary);
  border-radius: var(--radius-sm);
}

/* Save Modal */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.7);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal {
  background: var(--color-bg-secondary);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  padding: var(--space-xl);
  min-width: 400px;
  max-width: 500px;
}

.modal h3 {
  margin-bottom: var(--space-lg);
  color: var(--color-gold);
}

.form-group {
  margin-bottom: var(--space-md);
}

.form-group label {
  display: block;
  margin-bottom: var(--space-xs);
  font-size: 0.85rem;
  color: var(--color-text-secondary);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.form-input,
.form-textarea {
  width: 100%;
  padding: var(--space-sm) var(--space-md);
  background: var(--color-bg-tertiary);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  color: var(--color-text-primary);
  font-family: inherit;
  font-size: 0.95rem;
}

.form-input:focus,
.form-textarea:focus {
  outline: none;
  border-color: var(--color-gold);
}

.form-textarea {
  resize: vertical;
  min-height: 80px;
}

.modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: var(--space-sm);
  margin-top: var(--space-lg);
  padding-top: var(--space-md);
  border-top: 1px solid var(--color-border);
}

.btn-danger {
  background: rgba(139, 69, 69, 0.2);
  border-color: var(--color-blood);
  color: var(--color-blood-light);
}

.btn-danger:hover:not(:disabled) {
  background: rgba(139, 69, 69, 0.4);
}

/* Config Styles */
.config-card h3 {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
}

.config-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: var(--space-sm);
}

.config-actions {
  display: flex;
  gap: var(--space-xs);
}

.config-sections {
  margin-top: var(--space-lg);
}

.config-section {
  background: var(--color-bg-tertiary);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  margin-bottom: var(--space-sm);
  overflow: hidden;
}

.section-header {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  padding: var(--space-sm) var(--space-md);
  cursor: pointer;
  transition: background 0.2s;
}

.section-header:hover {
  background: rgba(201, 162, 39, 0.1);
}

.section-toggle {
  width: 16px;
  color: var(--color-text-muted);
  font-size: 0.8rem;
}

.section-name {
  font-family: var(--font-display);
  color: var(--color-gold);
  flex: 1;
}

.section-count {
  font-size: 0.75rem;
  color: var(--color-text-muted);
}

.section-values {
  border-top: 1px solid var(--color-border);
}

.config-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--space-xs) var(--space-md);
  border-bottom: 1px solid var(--color-border);
}

.config-item:last-child {
  border-bottom: none;
}

.config-item.editing {
  background: rgba(201, 162, 39, 0.1);
}

.config-key {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
}

.key-name {
  font-size: 0.85rem;
  color: var(--color-text-secondary);
}

.key-type {
  font-size: 0.65rem;
  padding: 1px 4px;
  border-radius: 3px;
  text-transform: uppercase;
}

.key-type.boolean {
  background: rgba(100, 149, 237, 0.3);
  color: cornflowerblue;
}

.key-type.integer {
  background: rgba(60, 179, 113, 0.3);
  color: mediumseagreen;
}

.key-type.float {
  background: rgba(255, 165, 0, 0.3);
  color: orange;
}

.config-value {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
}

.value-number {
  font-family: monospace;
  color: var(--color-text-primary);
  font-size: 0.9rem;
}

.value-badge {
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 0.75rem;
  font-weight: bold;
}

.value-badge.true {
  background: rgba(60, 179, 113, 0.3);
  color: mediumseagreen;
}

.value-badge.false {
  background: rgba(139, 69, 69, 0.3);
  color: #b88;
}

.btn-edit {
  background: transparent;
  border: none;
  cursor: pointer;
  padding: 2px 4px;
  opacity: 0.5;
  transition: opacity 0.2s;
}

.btn-edit:hover {
  opacity: 1;
}

.config-edit {
  display: flex;
  align-items: center;
  gap: var(--space-xs);
}

.edit-input {
  width: 100px;
  padding: 2px 6px;
  background: var(--color-bg-primary);
  border: 1px solid var(--color-gold);
  border-radius: 3px;
  color: var(--color-text-primary);
  font-family: monospace;
}

.edit-input:focus {
  outline: none;
}

.config-loading {
  padding: var(--space-lg);
  text-align: center;
}

/* Object Manipulation Styles */
.objmanip-card {
  grid-column: 1 / -1;
}

.objmanip-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  cursor: pointer;
  padding: var(--space-sm) 0;
}

.objmanip-header:hover {
  opacity: 0.8;
}

.toggle-indicator {
  font-size: 0.9rem;
  color: var(--color-text-secondary);
}

.objmanip-content {
  margin-top: var(--space-md);
  display: flex;
  flex-direction: column;
  gap: var(--space-lg);
}

.objmanip-section {
  padding: var(--space-md);
  background: rgba(0, 0, 0, 0.2);
  border-radius: var(--radius-md);
  border: 1px solid var(--color-border);
}

.objmanip-section h4 {
  margin: 0 0 var(--space-md) 0;
  color: var(--color-gold);
  font-size: 1rem;
}

.form-row {
  display: flex;
  gap: var(--space-md);
  flex-wrap: wrap;
  margin-bottom: var(--space-sm);
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: var(--space-xs);
  min-width: 120px;
  flex: 1;
}

.form-group label {
  font-size: 0.75rem;
  color: var(--color-text-secondary);
  text-transform: uppercase;
}

.form-input,
.form-select {
  padding: var(--space-xs) var(--space-sm);
  background: var(--color-bg-primary);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  color: var(--color-text-primary);
  font-size: 0.9rem;
}

.form-input:focus,
.form-select:focus {
  outline: none;
  border-color: var(--color-gold);
}

.form-select {
  cursor: pointer;
}

.modify-form {
  margin-top: var(--space-md);
  padding-top: var(--space-md);
  border-top: 1px solid var(--color-border);
}

.form-section-label {
  font-size: 0.85rem;
  color: var(--color-gold);
  margin: var(--space-md) 0 var(--space-sm) 0;
  font-weight: bold;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.form-section-label:first-of-type {
  margin-top: var(--space-sm);
}

.form-group label .hint {
  color: var(--color-text-muted);
  font-size: 0.8em;
  font-weight: normal;
}

.btn-row {
  margin-top: var(--space-md);
  padding-top: var(--space-md);
  border-top: 1px solid var(--color-border);
  justify-content: flex-start;
  gap: var(--space-sm);
}

.modify-info {
  margin-bottom: var(--space-md);
  font-size: 0.9rem;
}

.modify-info .alive {
  color: mediumseagreen;
}

.modify-info .dead {
  color: #b88;
}

.btn-group-modify {
  display: flex;
  gap: var(--space-sm);
  align-items: flex-end;
}

.btn-danger {
  background: linear-gradient(135deg, #8b2020, #5a1515);
  border: 1px solid #b83030;
  color: #fcc;
}

.btn-danger:hover:not(:disabled) {
  background: linear-gradient(135deg, #a02525, #6a1a1a);
}

.btn-success {
  background: linear-gradient(135deg, #206b20, #154515);
  border: 1px solid #30b830;
  color: #cfc;
}

.btn-success:hover:not(:disabled) {
  background: linear-gradient(135deg, #258025, #1a5a1a);
}

.caravan-list {
  display: flex;
  flex-direction: column;
  gap: var(--space-xs);
}

.caravan-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--space-xs) var(--space-sm);
  background: rgba(0, 0, 0, 0.2);
  border-radius: var(--radius-sm);
}

.caravan-info {
  font-size: 0.85rem;
}
</style>

