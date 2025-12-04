<script setup>
import { ref, computed, onMounted } from 'vue'
import { units, factions } from '../api'

const allUnits = ref([])
const allFactions = ref([])
const loading = ref(true)

// Filters
const factionFilter = ref('')
const categoryFilter = ref('')
const searchQuery = ref('')

const categories = ['melee', 'ranged', 'expert', 'interior_siege', 'exterior_siege', 'no_fire']

const loadData = async () => {
  loading.value = true
  try {
    const [unitsRes, factionsRes] = await Promise.all([
      units.list({ limit: 500 }),
      factions.list()
    ])
    allUnits.value = unitsRes.data
    allFactions.value = factionsRes.data
  } catch (e) {
    console.error('Failed to load units:', e)
  } finally {
    loading.value = false
  }
}

const filteredUnits = computed(() => {
  let result = allUnits.value
  
  if (factionFilter.value) {
    result = result.filter(u => u.factionId === parseInt(factionFilter.value))
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

const getHpClass = (hp, maxHp) => {
  const pct = hp / maxHp
  if (pct < 0.25) return 'critical'
  if (pct < 0.5) return 'damaged'
  return ''
}

onMounted(loadData)
</script>

<template>
  <div class="units-page fade-in">
    <header class="page-header">
      <div>
        <h2>Military Forces</h2>
        <p class="text-muted">All units across the Eastern Kingdoms</p>
      </div>
      <div class="unit-count">
        <span class="count-value">{{ filteredUnits.length }}</span>
        <span class="count-label">Units</span>
      </div>
    </header>

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
          <label>Faction</label>
          <select v-model="factionFilter" class="filter-select">
            <option value="">All Factions</option>
            <option 
              v-for="faction in allFactions" 
              :key="faction.id"
              :value="faction.id"
            >
              {{ faction.name }}
            </option>
          </select>
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
        
        <button class="btn btn-sm" @click="factionFilter = ''; categoryFilter = ''; searchQuery = ''">
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
            <th>Faction</th>
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
            @click="$router.push(`/units/${unit.id}`)"
            class="unit-row"
          >
            <td>
              <RouterLink :to="`/units/${unit.id}`" class="unit-name-link">
                {{ unit.name }}
              </RouterLink>
            </td>
            <td>
              <span 
                class="faction-badge"
                :class="allFactions.find(f => f.id === unit.factionId)?.isHorde ? 'horde' : 'alliance'"
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
  cursor: pointer;
}

.unit-name-link {
  color: var(--color-text-primary);
  font-weight: 500;
}

.unit-name-link:hover {
  color: var(--color-gold);
}

.faction-badge {
  display: inline-block;
  padding: var(--space-xs) var(--space-sm);
  font-size: 0.75rem;
  border-radius: var(--radius-sm);
}

.faction-badge.horde {
  background: rgba(139, 26, 26, 0.3);
  color: #e85050;
}

.faction-badge.alliance {
  background: rgba(26, 74, 139, 0.3);
  color: #5090e8;
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
</style>

