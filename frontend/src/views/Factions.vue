<script setup>
import { ref, computed, onMounted } from 'vue'
import { factions } from '../api'

const allFactions = ref([])
const loading = ref(true)
const filter = ref('all') // 'all', 'horde', 'alliance'

const loadFactions = async () => {
  loading.value = true
  try {
    const response = await factions.list()
    allFactions.value = response.data
  } catch (e) {
    console.error('Failed to load factions:', e)
  } finally {
    loading.value = false
  }
}

const filteredFactions = computed(() => {
  if (filter.value === 'horde') {
    return allFactions.value.filter(f => f.isHorde)
  }
  if (filter.value === 'alliance') {
    return allFactions.value.filter(f => f.isAlliance)
  }
  return allFactions.value
})

const hordeFactions = computed(() => allFactions.value.filter(f => f.isHorde))
const allianceFactions = computed(() => allFactions.value.filter(f => f.isAlliance))

onMounted(loadFactions)
</script>

<template>
  <div class="factions-page fade-in">
    <header class="page-header">
      <div class="header-content">
        <h2>Factions</h2>
        <p class="text-muted">The warring nations of Azeroth</p>
      </div>
      
      <div class="filter-tabs">
        <button 
          class="filter-tab" 
          :class="{ active: filter === 'all' }"
          @click="filter = 'all'"
        >
          All ({{ allFactions.length }})
        </button>
        <button 
          class="filter-tab horde" 
          :class="{ active: filter === 'horde' }"
          @click="filter = 'horde'"
        >
          Horde ({{ hordeFactions.length }})
        </button>
        <button 
          class="filter-tab alliance" 
          :class="{ active: filter === 'alliance' }"
          @click="filter = 'alliance'"
        >
          Alliance ({{ allianceFactions.length }})
        </button>
      </div>
    </header>

    <!-- Loading -->
    <div v-if="loading" class="loading">
      <div class="spinner"></div>
      <p>Loading factions...</p>
    </div>

    <!-- Faction Grid -->
    <div v-else class="faction-grid">
      <RouterLink
        v-for="faction in filteredFactions"
        :key="faction.id"
        :to="`/factions/${faction.id}`"
        class="faction-card card"
        :class="{
          'horde-card': faction.isHorde,
          'alliance-card': faction.isAlliance,
          'defeated': faction.isDefeated
        }"
      >
        <div class="faction-header">
          <h3 class="faction-name">{{ faction.name }}</h3>
          <span 
            class="tag"
            :class="faction.isHorde ? 'tag-horde' : 'tag-alliance'"
          >
            {{ faction.isHorde ? 'Horde' : 'Alliance' }}
          </span>
        </div>
        
        <div class="faction-info">
          <div class="info-row">
            <span class="info-label">Initiative</span>
            <span class="info-value">{{ faction.initiative }}</span>
          </div>
          <div class="info-row">
            <span class="info-label">Status</span>
            <span 
              class="info-value status"
              :class="faction.isDefeated ? 'defeated' : 'active'"
            >
              {{ faction.isDefeated ? 'Defeated' : 'Active' }}
            </span>
          </div>
        </div>

        <div class="faction-footer">
          <span class="view-details">View Details →</span>
        </div>
      </RouterLink>
    </div>
  </div>
</template>

<style scoped>
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: var(--space-xl);
  flex-wrap: wrap;
  gap: var(--space-md);
}

.header-content h2 {
  margin-bottom: var(--space-xs);
}

/* Filter Tabs */
.filter-tabs {
  display: flex;
  gap: var(--space-xs);
  background: var(--color-bg-secondary);
  padding: var(--space-xs);
  border-radius: var(--radius-md);
  border: 1px solid var(--color-border);
}

.filter-tab {
  padding: var(--space-sm) var(--space-md);
  font-family: var(--font-display);
  font-size: 0.8rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--color-text-muted);
  background: transparent;
  border: none;
  border-radius: var(--radius-sm);
  cursor: pointer;
  transition: all var(--transition-fast);
}

.filter-tab:hover {
  color: var(--color-text-primary);
  background: var(--color-bg-tertiary);
}

.filter-tab.active {
  color: var(--color-gold);
  background: var(--color-bg-tertiary);
}

.filter-tab.horde.active {
  color: #e85050;
  background: rgba(139, 26, 26, 0.3);
}

.filter-tab.alliance.active {
  color: #5090e8;
  background: rgba(26, 74, 139, 0.3);
}

/* Faction Grid */
.faction-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: var(--space-lg);
}

/* Faction Cards */
.faction-card {
  display: flex;
  flex-direction: column;
  text-decoration: none;
  color: inherit;
  cursor: pointer;
}

.faction-card.horde-card {
  border-left: 3px solid var(--color-horde-red);
}

.faction-card.alliance-card {
  border-left: 3px solid var(--color-alliance-blue);
}

.faction-card.defeated {
  opacity: 0.6;
}

.faction-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--space-md);
}

.faction-name {
  font-size: 1.1rem;
  margin: 0;
  color: var(--color-text-primary);
  transition: color var(--transition-fast);
}

.faction-card:hover .faction-name {
  color: var(--color-gold);
}

.faction-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: var(--space-sm);
}

.info-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.info-label {
  font-size: 0.85rem;
  color: var(--color-text-muted);
}

.info-value {
  font-family: var(--font-display);
  color: var(--color-text-primary);
}

.info-value.status.active {
  color: var(--color-success);
}

.info-value.status.defeated {
  color: var(--color-danger);
}

.faction-footer {
  margin-top: var(--space-md);
  padding-top: var(--space-md);
  border-top: 1px solid var(--color-border);
}

.view-details {
  font-size: 0.85rem;
  color: var(--color-gold-dark);
  transition: color var(--transition-fast);
}

.faction-card:hover .view-details {
  color: var(--color-gold);
}
</style>

