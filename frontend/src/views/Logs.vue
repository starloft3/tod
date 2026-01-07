<script setup>
/**
 * Logs View - The General's Command Center
 * 
 * A tactical records room where the commanding general reviews
 * dispatches from the front lines - combat reports, movement orders,
 * economic activities, and strategic events.
 */
import { ref, onMounted, computed, watch } from 'vue'
import axios from 'axios'

const API_BASE = 'http://localhost:8000'

// State
const logs = ref([])
const logSummary = ref(null)
const categories = ref({})
const loading = ref(true)
const error = ref(null)

// Filters
const selectedCategory = ref('')
const selectedTurn = ref('')
const selectedFaction = ref('')
const searchQuery = ref('')

// Pagination
const limit = ref(100)
const offset = ref(0)
const totalEntries = ref(0)

// Expansion state for detailed entries
const expandedEntries = ref(new Set())

// Load logs from API
const loadLogs = async () => {
  loading.value = true
  error.value = null
  
  try {
    const params = {
      limit: limit.value,
      offset: offset.value
    }
    
    if (selectedCategory.value) params.category = selectedCategory.value
    if (selectedTurn.value) params.turn = parseInt(selectedTurn.value)
    if (selectedFaction.value) params.faction_id = parseInt(selectedFaction.value)
    
    const response = await axios.get(`${API_BASE}/logs`, { params })
    logs.value = response.data.entries || []
    totalEntries.value = response.data.total || 0
    
  } catch (e) {
    error.value = 'Failed to load logs: ' + e.message
    console.error(e)
  } finally {
    loading.value = false
  }
}

// Load log summary
const loadSummary = async () => {
  try {
    const response = await axios.get(`${API_BASE}/logs/summary`)
    logSummary.value = response.data
  } catch (e) {
    console.error('Failed to load log summary:', e)
  }
}

// Load categories
const loadCategories = async () => {
  try {
    const response = await axios.get(`${API_BASE}/logs/categories`)
    categories.value = response.data.categories || {}
  } catch (e) {
    console.error('Failed to load categories:', e)
  }
}

// Filter handlers
const applyFilters = () => {
  offset.value = 0
  loadLogs()
}

const clearFilters = () => {
  selectedCategory.value = ''
  selectedTurn.value = ''
  selectedFaction.value = ''
  searchQuery.value = ''
  offset.value = 0
  loadLogs()
}

// Toggle entry expansion
const toggleEntry = (entryId) => {
  if (expandedEntries.value.has(entryId)) {
    expandedEntries.value.delete(entryId)
  } else {
    expandedEntries.value.add(entryId)
  }
}

// Format timestamp
const formatTimestamp = (timestamp) => {
  const date = new Date(timestamp)
  return date.toLocaleTimeString('en-US', { 
    hour: '2-digit', 
    minute: '2-digit',
    second: '2-digit'
  })
}

// Get category info
const getCategoryInfo = (categoryKey) => {
  return categories.value[categoryKey] || { 
    name: categoryKey, 
    icon: '📜', 
    color: '#808080' 
  }
}

// Computed: filtered logs (client-side search)
const filteredLogs = computed(() => {
  if (!searchQuery.value) return logs.value
  
  const query = searchQuery.value.toLowerCase()
  return logs.value.filter(entry => 
    entry.summary.toLowerCase().includes(query) ||
    (entry.faction_name && entry.faction_name.toLowerCase().includes(query))
  )
})

// Computed: unique turns in current logs
const availableTurns = computed(() => {
  if (!logSummary.value) return []
  const turns = []
  for (let i = logSummary.value.latest_turn; i >= logSummary.value.earliest_turn; i--) {
    turns.push(i)
  }
  return turns
})

// Refresh data
const refresh = () => {
  loadLogs()
  loadSummary()
}

// Pagination
const nextPage = () => {
  if (offset.value + limit.value < totalEntries.value) {
    offset.value += limit.value
    loadLogs()
  }
}

const prevPage = () => {
  if (offset.value > 0) {
    offset.value = Math.max(0, offset.value - limit.value)
    loadLogs()
  }
}

// Watch for filter changes
watch([selectedCategory], () => applyFilters())

// Initialize
onMounted(async () => {
  await loadCategories()
  await loadSummary()
  await loadLogs()
})
</script>

<template>
  <div class="logs-page fade-in">
    <!-- Header: The War Room -->
    <header class="logs-header">
      <div class="header-content">
        <h2>📜 War Records</h2>
        <p class="subtitle">Dispatches from the Front</p>
      </div>
      
      <div class="header-stats" v-if="logSummary">
        <div class="stat">
          <span class="stat-value">{{ logSummary.total_entries }}</span>
          <span class="stat-label">Records</span>
        </div>
        <div class="stat">
          <span class="stat-value">{{ logSummary.turns_logged }}</span>
          <span class="stat-label">Turns</span>
        </div>
      </div>
      
      <button class="btn btn-secondary" @click="refresh" :disabled="loading">
        {{ loading ? 'Loading...' : 'Refresh' }}
      </button>
    </header>
    
    <!-- Filters Panel -->
    <div class="filters-panel">
      <div class="filter-group">
        <label>Category</label>
        <div class="category-filters">
          <button 
            class="category-btn" 
            :class="{ active: selectedCategory === '' }"
            @click="selectedCategory = ''"
          >
            All
          </button>
          <button 
            v-for="(info, key) in categories" 
            :key="key"
            class="category-btn"
            :class="{ active: selectedCategory === key }"
            :style="{ '--cat-color': info.color }"
            @click="selectedCategory = key"
          >
            {{ info.icon }} {{ info.name }}
          </button>
        </div>
      </div>
      
      <div class="filter-row">
        <div class="filter-group">
          <label>Turn</label>
          <select v-model="selectedTurn" @change="applyFilters" class="filter-select">
            <option value="">All Turns</option>
            <option v-for="turn in availableTurns" :key="turn" :value="turn">
              Turn {{ turn }}
            </option>
          </select>
        </div>
        
        <div class="filter-group">
          <label>Search</label>
          <input 
            type="text" 
            v-model="searchQuery" 
            placeholder="Search dispatches..."
            class="filter-input"
          />
        </div>
        
        <button v-if="selectedCategory || selectedTurn || searchQuery" 
                class="btn btn-secondary btn-sm" 
                @click="clearFilters">
          Clear Filters
        </button>
      </div>
    </div>
    
    <!-- Error State -->
    <div v-if="error" class="error-banner">
      {{ error }}
    </div>
    
    <!-- Loading State -->
    <div v-if="loading" class="loading-state">
      <div class="quill-loader"></div>
      <p>Consulting the archives...</p>
    </div>
    
    <!-- Empty State -->
    <div v-else-if="filteredLogs.length === 0" class="empty-state">
      <div class="empty-icon">📜</div>
      <h3>No Records Found</h3>
      <p v-if="selectedCategory || selectedTurn || searchQuery">
        No dispatches match your current filters.
      </p>
      <p v-else>
        The war has just begun. Records will appear as events unfold.
      </p>
    </div>
    
    <!-- Log Entries -->
    <div v-else class="logs-container">
      <div 
        v-for="entry in filteredLogs" 
        :key="entry.id"
        class="log-entry"
        :class="[
          entry.category,
          { expanded: expandedEntries.has(entry.id) }
        ]"
        @click="toggleEntry(entry.id)"
      >
        <!-- Entry Header -->
        <div class="entry-header">
          <span class="entry-icon">{{ getCategoryInfo(entry.category).icon }}</span>
          
          <div class="entry-meta">
            <span class="entry-turn">Turn {{ entry.turn_number }}</span>
            <span class="entry-initiative">Init {{ entry.initiative }}</span>
            <span class="entry-time">{{ formatTimestamp(entry.timestamp) }}</span>
          </div>
          
          <span v-if="entry.faction_name" class="entry-faction">
            {{ entry.faction_name }}
          </span>
          
          <span class="expand-indicator">{{ expandedEntries.has(entry.id) ? '▼' : '▶' }}</span>
        </div>
        
        <!-- Entry Summary -->
        <div class="entry-summary">
          {{ entry.summary }}
        </div>
        
        <!-- Entry Details (expanded) -->
        <div v-if="expandedEntries.has(entry.id)" class="entry-details">
          <!-- Combat Attack Details -->
          <template v-if="entry.event_type === 'combat_attack'">
            <div class="detail-grid">
              <div class="detail-item">
                <span class="detail-label">Attacker</span>
                <span class="detail-value">{{ entry.details.attacker?.name }} ({{ entry.details.attacker?.faction_name }})</span>
              </div>
              <div class="detail-item">
                <span class="detail-label">Defender</span>
                <span class="detail-value">{{ entry.details.defender?.name }} ({{ entry.details.defender?.faction_name }})</span>
              </div>
              <div class="detail-item">
                <span class="detail-label">Effective Combat</span>
                <span class="detail-value">{{ entry.details.modifiers?.effective_combat }}%</span>
              </div>
              <div class="detail-item">
                <span class="detail-label">Hits Rolled</span>
                <span class="detail-value">{{ entry.details.modifiers?.hits_rolled }}</span>
              </div>
              <div class="detail-item">
                <span class="detail-label">Damage Dealt</span>
                <span class="detail-value combat-damage">{{ entry.details.damage }}</span>
              </div>
            </div>
            
            <div class="modifier-breakdown" v-if="entry.details.modifiers">
              <span class="breakdown-title">Modifiers:</span>
              <span v-if="entry.details.modifiers.base_combat">Base: {{ entry.details.modifiers.base_combat }}</span>
              <span v-if="entry.details.modifiers.flank_bonus">Flank: +{{ entry.details.modifiers.flank_bonus }}</span>
              <span v-if="entry.details.modifiers.terrain_modifier">Terrain: {{ entry.details.modifiers.terrain_modifier }}</span>
              <span v-if="entry.details.modifiers.base_bonus">Base Bonus: +{{ entry.details.modifiers.base_bonus }}</span>
            </div>
          </template>
          
          <!-- Combat Start Details -->
          <template v-else-if="entry.event_type === 'combat_start'">
            <div class="combatants-list">
              <div class="combatant" v-for="unit in entry.details.combatants" :key="unit.id">
                <span class="combatant-name">{{ unit.name }}</span>
                <span class="combatant-faction">({{ unit.faction_name }})</span>
                <span class="combatant-hp">{{ unit.hp }}/{{ unit.max_hp }} HP</span>
              </div>
            </div>
          </template>
          
          <!-- Movement Details -->
          <template v-else-if="entry.event_type === 'movement'">
            <div class="detail-grid">
              <div class="detail-item">
                <span class="detail-label">Unit</span>
                <span class="detail-value">{{ entry.details.unit?.name }}</span>
              </div>
              <div class="detail-item">
                <span class="detail-label">Path</span>
                <span class="detail-value">{{ entry.details.path?.join(' → ') }}</span>
              </div>
              <div class="detail-item">
                <span class="detail-label">Hexes Traveled</span>
                <span class="detail-value">{{ entry.details.hexes_traveled }}</span>
              </div>
            </div>
          </template>
          
          <!-- Harvest Details -->
          <template v-else-if="entry.event_type === 'harvest'">
            <div class="resource-yields">
              <span v-if="entry.details.yields?.gold" class="yield gold">+{{ entry.details.yields.gold }} 🪙</span>
              <span v-if="entry.details.yields?.lumber" class="yield lumber">+{{ entry.details.yields.lumber }} 🪵</span>
              <span v-if="entry.details.yields?.oil" class="yield oil">+{{ entry.details.yields.oil }} 🛢️</span>
            </div>
          </template>
          
          <!-- Build Unit Details -->
          <template v-else-if="entry.event_type === 'build_unit'">
            <div class="detail-grid">
              <div class="detail-item">
                <span class="detail-label">Unit</span>
                <span class="detail-value">{{ entry.details.unit_name }}</span>
              </div>
              <div class="detail-item">
                <span class="detail-label">Cost</span>
                <span class="detail-value">
                  <span v-if="entry.details.cost?.gold">{{ entry.details.cost.gold }}🪙</span>
                  <span v-if="entry.details.cost?.lumber">{{ entry.details.cost.lumber }}🪵</span>
                  <span v-if="entry.details.cost?.oil">{{ entry.details.cost.oil }}🛢️</span>
                </span>
              </div>
            </div>
          </template>
          
          <!-- Generic Details Fallback -->
          <template v-else>
            <pre class="raw-details">{{ JSON.stringify(entry.details, null, 2) }}</pre>
          </template>
        </div>
      </div>
    </div>
    
    <!-- Pagination -->
    <div v-if="totalEntries > limit" class="pagination">
      <button class="btn btn-secondary" @click="prevPage" :disabled="offset === 0">
        ← Older
      </button>
      <span class="page-info">
        Showing {{ offset + 1 }} - {{ Math.min(offset + limit, totalEntries) }} of {{ totalEntries }}
      </span>
      <button class="btn btn-secondary" @click="nextPage" :disabled="offset + limit >= totalEntries">
        Newer →
      </button>
    </div>
  </div>
</template>

<style scoped>
.logs-page {
  max-width: 1200px;
  margin: 0 auto;
  padding: var(--space-lg);
}

/* Header Styling */
.logs-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--space-xl);
  padding-bottom: var(--space-lg);
  border-bottom: 2px solid var(--color-gold);
}

.header-content h2 {
  font-family: 'Cinzel', serif;
  font-size: 2rem;
  color: var(--color-gold);
  margin: 0;
}

.subtitle {
  font-style: italic;
  color: var(--color-text-secondary);
  margin: var(--space-xs) 0 0 0;
}

.header-stats {
  display: flex;
  gap: var(--space-lg);
}

.stat {
  text-align: center;
}

.stat-value {
  display: block;
  font-size: 1.5rem;
  font-weight: bold;
  color: var(--color-gold);
}

.stat-label {
  font-size: 0.75rem;
  text-transform: uppercase;
  color: var(--color-text-secondary);
}

/* Filters Panel */
.filters-panel {
  background: linear-gradient(135deg, rgba(30, 20, 10, 0.9), rgba(20, 15, 8, 0.95));
  border: 1px solid rgba(139, 90, 43, 0.5);
  border-radius: var(--radius-md);
  padding: var(--space-md);
  margin-bottom: var(--space-lg);
}

.filter-group {
  margin-bottom: var(--space-sm);
}

.filter-group label {
  display: block;
  font-size: 0.75rem;
  text-transform: uppercase;
  color: var(--color-text-secondary);
  margin-bottom: var(--space-xs);
}

.category-filters {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-xs);
}

.category-btn {
  padding: var(--space-xs) var(--space-sm);
  background: rgba(0, 0, 0, 0.3);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  color: var(--color-text-secondary);
  cursor: pointer;
  transition: all 0.2s;
  font-size: 0.85rem;
}

.category-btn:hover {
  background: rgba(0, 0, 0, 0.5);
  color: var(--color-text-primary);
}

.category-btn.active {
  background: var(--cat-color, var(--color-gold));
  border-color: var(--cat-color, var(--color-gold));
  color: white;
}

.filter-row {
  display: flex;
  gap: var(--space-md);
  align-items: flex-end;
  flex-wrap: wrap;
}

.filter-select,
.filter-input {
  padding: var(--space-xs) var(--space-sm);
  background: rgba(0, 0, 0, 0.4);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  color: var(--color-text-primary);
  min-width: 150px;
}

.filter-input {
  min-width: 200px;
}

/* Loading State */
.loading-state {
  text-align: center;
  padding: var(--space-xxl);
  color: var(--color-text-secondary);
}

.quill-loader {
  width: 40px;
  height: 40px;
  border: 3px solid rgba(139, 90, 43, 0.3);
  border-top-color: var(--color-gold);
  border-radius: 50%;
  margin: 0 auto var(--space-md);
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* Empty State */
.empty-state {
  text-align: center;
  padding: var(--space-xxl);
  color: var(--color-text-secondary);
}

.empty-icon {
  font-size: 4rem;
  margin-bottom: var(--space-md);
}

/* Error Banner */
.error-banner {
  background: rgba(139, 32, 32, 0.3);
  border: 1px solid #b83030;
  color: #fcc;
  padding: var(--space-md);
  border-radius: var(--radius-md);
  margin-bottom: var(--space-lg);
}

/* Logs Container */
.logs-container {
  display: flex;
  flex-direction: column;
  gap: var(--space-xs);
}

/* Log Entry */
.log-entry {
  background: linear-gradient(135deg, rgba(40, 30, 20, 0.8), rgba(30, 25, 15, 0.9));
  border: 1px solid rgba(100, 70, 40, 0.4);
  border-left: 4px solid var(--color-border);
  border-radius: var(--radius-sm);
  padding: var(--space-sm) var(--space-md);
  cursor: pointer;
  transition: all 0.2s;
}

.log-entry:hover {
  background: linear-gradient(135deg, rgba(50, 40, 25, 0.9), rgba(40, 30, 20, 0.95));
}

.log-entry.expanded {
  border-left-width: 4px;
}

/* Category Colors */
.log-entry.combat { border-left-color: #b83030; }
.log-entry.movement { border-left-color: #3080b8; }
.log-entry.economic { border-left-color: #b8a030; }
.log-entry.entity { border-left-color: #808080; }
.log-entry.turn { border-left-color: #30b880; }
.log-entry.debug { border-left-color: #9b4dca; }

/* Entry Header */
.entry-header {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  font-size: 0.8rem;
  color: var(--color-text-secondary);
}

.entry-icon {
  font-size: 1rem;
}

.entry-meta {
  display: flex;
  gap: var(--space-sm);
}

.entry-turn {
  color: var(--color-gold);
  font-weight: 600;
}

.entry-initiative {
  color: var(--color-text-secondary);
}

.entry-time {
  color: var(--color-text-muted);
}

.entry-faction {
  margin-left: auto;
  padding: 2px 8px;
  background: rgba(0, 0, 0, 0.3);
  border-radius: 4px;
  font-size: 0.75rem;
}

.expand-indicator {
  margin-left: var(--space-sm);
  color: var(--color-text-muted);
}

/* Entry Summary */
.entry-summary {
  margin-top: var(--space-xs);
  color: var(--color-text-primary);
  font-size: 0.95rem;
}

/* Entry Details */
.entry-details {
  margin-top: var(--space-md);
  padding-top: var(--space-md);
  border-top: 1px solid rgba(100, 70, 40, 0.3);
}

.detail-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: var(--space-sm);
}

.detail-item {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.detail-label {
  font-size: 0.7rem;
  text-transform: uppercase;
  color: var(--color-text-secondary);
}

.detail-value {
  font-size: 0.9rem;
  color: var(--color-text-primary);
}

.combat-damage {
  color: #ff6666;
  font-weight: bold;
}

.modifier-breakdown {
  margin-top: var(--space-sm);
  font-size: 0.8rem;
  color: var(--color-text-secondary);
  display: flex;
  gap: var(--space-sm);
  flex-wrap: wrap;
}

.breakdown-title {
  color: var(--color-gold);
}

/* Combatants List */
.combatants-list {
  display: flex;
  flex-direction: column;
  gap: var(--space-xs);
}

.combatant {
  display: flex;
  gap: var(--space-sm);
  font-size: 0.85rem;
}

.combatant-name {
  font-weight: 600;
  color: var(--color-text-primary);
}

.combatant-faction {
  color: var(--color-text-secondary);
}

.combatant-hp {
  margin-left: auto;
  color: var(--color-gold);
}

/* Resource Yields */
.resource-yields {
  display: flex;
  gap: var(--space-md);
}

.yield {
  padding: var(--space-xs) var(--space-sm);
  border-radius: var(--radius-sm);
  font-weight: bold;
}

.yield.gold { background: rgba(212, 175, 55, 0.2); color: #d4af37; }
.yield.lumber { background: rgba(139, 90, 43, 0.2); color: #8b5a2b; }
.yield.oil { background: rgba(60, 60, 80, 0.2); color: #8888aa; }

/* Raw Details */
.raw-details {
  background: rgba(0, 0, 0, 0.3);
  padding: var(--space-sm);
  border-radius: var(--radius-sm);
  font-size: 0.75rem;
  overflow-x: auto;
  color: var(--color-text-secondary);
}

/* Pagination */
.pagination {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: var(--space-md);
  margin-top: var(--space-xl);
  padding-top: var(--space-lg);
  border-top: 1px solid var(--color-border);
}

.page-info {
  color: var(--color-text-secondary);
  font-size: 0.9rem;
}
</style>

