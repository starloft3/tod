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

onMounted(loadAdminStatus)
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
</style>

