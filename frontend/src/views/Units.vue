<script setup>
import { ref, computed, onMounted, inject, watch } from 'vue'
import { units, factions } from '../api'

const allUnits = ref([])
const allFactions = ref([])
const foodStatus = ref(null)
const allFoodStatus = ref([])  // For admin view
const loading = ref(true)

// Inject selected faction from App.vue
const selectedFactionId = inject('selectedFactionId', ref(null))

// Filters (only used in admin mode)
const categoryFilter = ref('')
const searchQuery = ref('')

const categories = ['melee', 'ranged', 'expert', 'interior_siege', 'exterior_siege', 'no_fire']

// Is this admin/omniscient mode?
const isAdmin = computed(() => selectedFactionId.value === null)

// Current faction being viewed
const viewingFaction = computed(() => {
  if (isAdmin.value) return null
  return allFactions.value.find(f => f.id === selectedFactionId.value)
})

const loadData = async () => {
  loading.value = true
  try {
    const [unitsRes, factionsRes] = await Promise.all([
      units.list({ limit: 1000 }),
      factions.list()
    ])
    allUnits.value = unitsRes.data
    allFactions.value = factionsRes.data
    
    // Load food status
    await loadFoodStatus()
  } catch (e) {
    console.error('Failed to load units:', e)
  } finally {
    loading.value = false
  }
}

const loadFoodStatus = async () => {
  try {
    if (isAdmin.value) {
      // Admin sees all factions' food
      const res = await factions.allFood({ activeOnly: true })
      allFoodStatus.value = res.data
      foodStatus.value = null
    } else if (selectedFactionId.value !== null) {
      // Single faction view
      const res = await factions.food(selectedFactionId.value)
      foodStatus.value = res.data
      allFoodStatus.value = []
    }
  } catch (e) {
    console.error('Failed to load food status:', e)
  }
}

// Watch for faction changes
watch(selectedFactionId, () => {
  loadFoodStatus()
})

const filteredUnits = computed(() => {
  let result = allUnits.value.filter(u => u.alive !== false)
  
  // Filter by faction unless admin
  if (!isAdmin.value && selectedFactionId.value !== null) {
    result = result.filter(u => u.factionId === selectedFactionId.value)
  }
  
  if (categoryFilter.value) {
    result = result.filter(u => u.category === categoryFilter.value)
  }
  
  if (searchQuery.value) {
    const query = searchQuery.value.toLowerCase()
    result = result.filter(u => u.name.toLowerCase().includes(query))
  }
  
  return result
})

const getFactionName = (id) => {
  const faction = allFactions.value.find(f => f.id === id)
  return faction?.name || `Faction ${id}`
}

const getFactionColor = (id) => {
  const faction = allFactions.value.find(f => f.id === id)
  return faction?.color || '#888888'
}

const getHpClass = (hp, maxHp) => {
  const pct = hp / maxHp
  if (pct < 0.25) return 'critical'
  if (pct < 0.5) return 'damaged'
  return ''
}

const getFoodBarWidth = (food) => {
  if (food.foodLimit === 0) return 0
  return Math.min(100, (food.unitCount / food.foodLimit) * 100)
}

const getFoodBarClass = (food) => {
  if (food.isCapped) return 'capped'
  if (food.foodSurplus <= 2) return 'warning'
  return 'healthy'
}

onMounted(loadData)
</script>

<template>
  <div class="units-page fade-in">
    <header class="page-header">
      <div>
        <h2 v-if="isAdmin">All Military Forces</h2>
        <h2 v-else>{{ viewingFaction?.name || 'Faction' }} Forces</h2>
        <p class="text-muted" v-if="isAdmin">Admin view - all factions</p>
        <p class="text-muted" v-else>Your military units</p>
      </div>
      <div class="unit-count">
        <span class="count-value">{{ filteredUnits.length }}</span>
        <span class="count-label">Units</span>
      </div>
    </header>

    <!-- Food Status Card (Single Faction) -->
    <div v-if="!isAdmin && foodStatus" class="food-status card mb-lg">
      <div class="food-header">
        <h3>🍖 Food Supply</h3>
        <span 
          class="food-badge"
          :class="{ 'capped': foodStatus.isCapped, 'healthy': !foodStatus.isCapped }"
        >
          {{ foodStatus.isCapped ? 'CAPPED' : 'Available' }}
        </span>
      </div>
      
      <div class="food-details">
        <div class="food-stat">
          <span class="food-label">Units</span>
          <span class="food-value">{{ foodStatus.unitCount }}</span>
        </div>
        <div class="food-divider">/</div>
        <div class="food-stat">
          <span class="food-label">Limit</span>
          <span class="food-value highlight">{{ foodStatus.foodLimit }}</span>
        </div>
        <div class="food-breakdown">
          <span class="breakdown-item">🏰 {{ foodStatus.foodFromBases }} from bases</span>
          <span class="breakdown-item">🌾 {{ foodStatus.foodFromFarms }} from farms</span>
        </div>
      </div>
      
      <div class="food-bar-container">
        <div 
          class="food-bar-fill"
          :class="getFoodBarClass(foodStatus)"
          :style="{ width: getFoodBarWidth(foodStatus) + '%' }"
        ></div>
      </div>
      
      <div class="food-surplus" :class="{ 'negative': foodStatus.foodSurplus <= 0 }">
        <span v-if="foodStatus.foodSurplus > 0">
          +{{ foodStatus.foodSurplus }} surplus (can build {{ foodStatus.foodSurplus }} more units)
        </span>
        <span v-else>
          No surplus - cannot build new units
        </span>
      </div>
    </div>

    <!-- Food Status Summary (Admin View) -->
    <div v-if="isAdmin && allFoodStatus.length > 0" class="food-overview card mb-lg">
      <h3>🍖 All Factions Food Status</h3>
      <div class="food-grid">
        <div 
          v-for="food in allFoodStatus" 
          :key="food.factionId"
          class="food-faction-card"
          :style="{ borderLeftColor: food.color }"
        >
          <div class="faction-name">{{ food.factionName }}</div>
          <div class="faction-food">
            <span class="units">{{ food.unitCount }}</span>
            <span class="divider">/</span>
            <span class="limit">{{ food.foodLimit }}</span>
          </div>
          <div 
            class="faction-status"
            :class="{ 'capped': food.isCapped }"
          >
            {{ food.isCapped ? '⚠️ Capped' : `+${food.foodSurplus}` }}
          </div>
        </div>
      </div>
    </div>

    <!-- Filters -->
    <div class="filters card mb-lg">
      <div class="filter-row">
        <div class="filter-group">
          <label>Search</label>
          <input 
            v-model="searchQuery"
            type="text" 
            placeholder="Unit name..."
            class="filter-input"
          />
        </div>
        
        <div class="filter-group">
          <label>Category</label>
          <select v-model="categoryFilter" class="filter-select">
            <option value="">All Categories</option>
            <option v-for="cat in categories" :key="cat" :value="cat">
              {{ cat.replace('_', ' ') }}
            </option>
          </select>
        </div>
        
        <button class="btn btn-sm" @click="categoryFilter = ''; searchQuery = ''">
          Clear
        </button>
      </div>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="loading">
      <div class="spinner"></div>
      <p>Mustering forces...</p>
    </div>

    <!-- Units Table -->
    <div v-else class="table-container">
      <table>
        <thead>
          <tr>
            <th>Name</th>
            <th v-if="isAdmin">Faction</th>
            <th>Category</th>
            <th>HP</th>
            <th>Combat</th>
            <th>Location</th>
            <th>Tier</th>
          </tr>
        </thead>
        <tbody>
          <tr 
            v-for="unit in filteredUnits" 
            :key="unit.id"
            class="unit-row"
          >
            <td>
              <span class="unit-name">{{ unit.name }}</span>
            </td>
            <td v-if="isAdmin">
              <span 
                class="faction-badge"
                :style="{ 
                  borderColor: getFactionColor(unit.factionId),
                  color: getFactionColor(unit.factionId)
                }"
              >
                {{ getFactionName(unit.factionId) }}
              </span>
            </td>
            <td class="capitalize">{{ unit.category?.replace('_', ' ') }}</td>
            <td>
              <div class="hp-cell">
                <span class="hp-text">{{ unit.hp }}/{{ unit.maxHp }}</span>
                <div class="hp-bar">
                  <div 
                    class="hp-bar-fill"
                    :class="getHpClass(unit.hp, unit.maxHp)"
                    :style="{ width: `${(unit.hp / unit.maxHp) * 100}%` }"
                  ></div>
                </div>
              </div>
            </td>
            <td class="combat-value">{{ unit.combat }}</td>
            <td>Hex {{ unit.location }}</td>
            <td>
              <span v-if="unit.tier > 0" class="tier-badge">★{{ unit.tier }}</span>
              <span v-else class="text-muted">-</span>
            </td>
          </tr>
        </tbody>
      </table>
      
      <div v-if="filteredUnits.length === 0" class="no-units">
        <p class="text-muted">No units found</p>
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
}

.page-header h2 {
  margin-bottom: var(--space-xs);
}

.unit-count {
  text-align: right;
}

.count-value {
  font-family: var(--font-display);
  font-size: 2rem;
  color: var(--color-gold);
  display: block;
}

.count-label {
  font-size: 0.8rem;
  text-transform: uppercase;
  letter-spacing: 0.1em;
  color: var(--color-text-muted);
}

/* Food Status Card */
.food-status {
  padding: var(--space-lg);
}

.food-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--space-md);
}

.food-header h3 {
  margin: 0;
  color: var(--color-gold);
}

.food-badge {
  padding: var(--space-xs) var(--space-sm);
  border-radius: var(--radius-sm);
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
}

.food-badge.healthy {
  background: rgba(0, 200, 100, 0.2);
  color: #00c864;
}

.food-badge.capped {
  background: rgba(200, 50, 50, 0.2);
  color: #e85050;
}

.food-details {
  display: flex;
  align-items: center;
  gap: var(--space-md);
  margin-bottom: var(--space-md);
  flex-wrap: wrap;
}

.food-stat {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.food-label {
  font-size: 0.75rem;
  color: var(--color-text-muted);
  text-transform: uppercase;
}

.food-value {
  font-family: var(--font-display);
  font-size: 2rem;
  color: var(--color-text-primary);
}

.food-value.highlight {
  color: var(--color-gold);
}

.food-divider {
  font-size: 2rem;
  color: var(--color-text-muted);
}

.food-breakdown {
  display: flex;
  gap: var(--space-md);
  margin-left: auto;
}

.breakdown-item {
  font-size: 0.85rem;
  color: var(--color-text-secondary);
}

.food-bar-container {
  height: 8px;
  background: var(--color-bg-tertiary);
  border-radius: 4px;
  overflow: hidden;
  margin-bottom: var(--space-sm);
}

.food-bar-fill {
  height: 100%;
  transition: width 0.3s ease;
  border-radius: 4px;
}

.food-bar-fill.healthy {
  background: linear-gradient(90deg, #00c864, #44dd44);
}

.food-bar-fill.warning {
  background: linear-gradient(90deg, #cccc00, #dddd44);
}

.food-bar-fill.capped {
  background: linear-gradient(90deg, #cc0000, #dd4444);
}

.food-surplus {
  font-size: 0.9rem;
  color: #00c864;
}

.food-surplus.negative {
  color: #e85050;
}

/* Admin Food Overview */
.food-overview {
  padding: var(--space-lg);
}

.food-overview h3 {
  margin: 0 0 var(--space-md) 0;
  color: var(--color-gold);
}

.food-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
  gap: var(--space-md);
}

.food-faction-card {
  padding: var(--space-sm) var(--space-md);
  background: var(--color-bg-secondary);
  border-radius: var(--radius-sm);
  border-left: 3px solid;
}

.food-faction-card .faction-name {
  font-weight: 600;
  font-size: 0.85rem;
  margin-bottom: var(--space-xs);
}

.food-faction-card .faction-food {
  font-family: var(--font-display);
  font-size: 1.2rem;
}

.food-faction-card .units {
  color: var(--color-text-primary);
}

.food-faction-card .divider {
  color: var(--color-text-muted);
  margin: 0 2px;
}

.food-faction-card .limit {
  color: var(--color-gold);
}

.food-faction-card .faction-status {
  font-size: 0.8rem;
  color: #00c864;
  margin-top: var(--space-xs);
}

.food-faction-card .faction-status.capped {
  color: #e85050;
}

/* Filters */
.filters {
  padding: var(--space-md);
}

.filter-row {
  display: flex;
  gap: var(--space-md);
  align-items: flex-end;
  flex-wrap: wrap;
}

.filter-group {
  display: flex;
  flex-direction: column;
  gap: var(--space-xs);
}

.filter-group label {
  font-size: 0.75rem;
  text-transform: uppercase;
  letter-spacing: 0.1em;
  color: var(--color-text-muted);
}

.filter-input,
.filter-select {
  padding: var(--space-sm) var(--space-md);
  font-family: var(--font-body);
  font-size: 0.9rem;
  color: var(--color-text-primary);
  background: var(--color-bg-secondary);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  min-width: 150px;
}

.filter-input:focus,
.filter-select:focus {
  outline: none;
  border-color: var(--color-gold-dark);
}

/* Table */
.unit-row {
  cursor: default;
}

.unit-name {
  color: var(--color-text-primary);
  font-weight: 500;
}

.faction-badge {
  display: inline-block;
  padding: var(--space-xs) var(--space-sm);
  font-size: 0.75rem;
  border-radius: var(--radius-sm);
  border: 1px solid;
  background: transparent;
}

.capitalize {
  text-transform: capitalize;
}

.hp-cell {
  display: flex;
  flex-direction: column;
  gap: var(--space-xs);
  min-width: 80px;
}

.hp-text {
  font-size: 0.85rem;
}

.combat-value {
  font-family: var(--font-display);
  color: var(--color-gold);
}

.tier-badge {
  display: inline-flex;
  align-items: center;
  gap: 2px;
  padding: var(--space-xs) var(--space-sm);
  background: rgba(201, 162, 39, 0.2);
  border: 1px solid var(--color-gold-dark);
  border-radius: var(--radius-sm);
  font-size: 0.8rem;
  color: var(--color-gold);
}

.no-units {
  text-align: center;
  padding: var(--space-xl);
}
</style>
