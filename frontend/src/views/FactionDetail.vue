<script setup>
import { ref, onMounted, watch } from 'vue'
import { useRoute } from 'vue-router'
import { factions, units, bases } from '../api'

const route = useRoute()
const props = defineProps(['id'])

const faction = ref(null)
const factionUnits = ref([])
const factionBases = ref([])
const loading = ref(true)

const loadFaction = async () => {
  loading.value = true
  const factionId = props.id || route.params.id
  
  try {
    const [summaryRes, unitsRes, basesRes] = await Promise.all([
      factions.summary(factionId),
      units.byFaction(factionId),
      bases.byFaction(factionId)
    ])
    faction.value = summaryRes.data
    factionUnits.value = unitsRes.data
    factionBases.value = basesRes.data
  } catch (e) {
    console.error('Failed to load faction:', e)
  } finally {
    loading.value = false
  }
}

onMounted(loadFaction)
watch(() => route.params.id, loadFaction)
</script>

<template>
  <div class="faction-detail fade-in">
    <!-- Loading -->
    <div v-if="loading" class="loading">
      <div class="spinner"></div>
      <p>Loading faction data...</p>
    </div>

    <template v-else-if="faction">
      <!-- Header -->
      <header class="detail-header">
        <div class="header-main">
          <RouterLink to="/factions" class="back-link">← All Factions</RouterLink>
          <h2>{{ faction.faction.name }}</h2>
          <div class="header-tags">
            <span 
              class="tag"
              :class="faction.diplomacy.isHorde ? 'tag-horde' : 'tag-alliance'"
            >
              {{ faction.diplomacy.isHorde ? 'Horde' : 'Alliance' }}
            </span>
            <span class="tag tag-gold">Initiative {{ faction.faction.initiative }}</span>
          </div>
        </div>
      </header>

      <!-- Stats Overview -->
      <section class="stats-section grid grid-4 mb-lg">
        <div class="card stat-card">
          <div class="stat">
            <span class="stat-value">{{ faction.military.aliveUnits }}</span>
            <span class="stat-label">Units</span>
          </div>
        </div>
        <div class="card stat-card">
          <div class="stat">
            <span class="stat-value">{{ faction.military.heroes }}</span>
            <span class="stat-label">Heroes</span>
          </div>
        </div>
        <div class="card stat-card">
          <div class="stat">
            <span class="stat-value">{{ faction.economy.bases }}</span>
            <span class="stat-label">Bases</span>
          </div>
        </div>
        <div class="card stat-card">
          <div class="stat">
            <span class="stat-value">{{ faction.economy.capitals }}</span>
            <span class="stat-label">Capitals</span>
          </div>
        </div>
      </section>

      <div class="content-grid grid grid-2">
        <!-- Economy -->
        <div class="card">
          <div class="card-header">
            <h3 class="card-title">💰 Economy</h3>
          </div>
          <div class="resource-list">
            <div class="resource-item">
              <span class="resource-icon gold">⬤</span>
              <span class="resource-label">Gold</span>
              <span class="resource-value">{{ faction.economy.totalGold }}</span>
            </div>
            <div class="resource-item">
              <span class="resource-icon lumber">⬤</span>
              <span class="resource-label">Lumber</span>
              <span class="resource-value">{{ faction.economy.totalLumber }}</span>
            </div>
            <div class="resource-item">
              <span class="resource-icon oil">⬤</span>
              <span class="resource-label">Oil</span>
              <span class="resource-value">{{ faction.economy.totalOil }}</span>
            </div>
          </div>
        </div>

        <!-- Allies -->
        <div class="card">
          <div class="card-header">
            <h3 class="card-title">🤝 Allied Factions</h3>
          </div>
          <div v-if="faction.diplomacy.allies.length" class="allies-list">
            <RouterLink
              v-for="ally in faction.diplomacy.allies"
              :key="ally.id"
              :to="`/factions/${ally.id}`"
              class="ally-item"
            >
              {{ ally.name }}
            </RouterLink>
          </div>
          <p v-else class="text-muted">No allied factions</p>
        </div>

        <!-- Units -->
        <div class="card">
          <div class="card-header">
            <h3 class="card-title">⚔ Military Forces</h3>
            <span class="text-muted">{{ factionUnits.length }} units</span>
          </div>
          <div class="units-preview">
            <div 
              v-for="unit in factionUnits.slice(0, 8)" 
              :key="unit.id"
              class="unit-preview-item"
            >
              <RouterLink :to="`/units/${unit.id}`">
                <span class="unit-name">{{ unit.name }}</span>
                <span class="unit-hp">{{ unit.hp }}/{{ unit.maxHp }}</span>
              </RouterLink>
            </div>
            <RouterLink 
              v-if="factionUnits.length > 8"
              :to="`/units?faction=${faction.faction.id}`"
              class="view-all"
            >
              View all {{ factionUnits.length }} units →
            </RouterLink>
          </div>
        </div>

        <!-- Bases -->
        <div class="card">
          <div class="card-header">
            <h3 class="card-title">🏰 Settlements</h3>
            <span class="text-muted">{{ factionBases.length }} bases</span>
          </div>
          <div class="bases-list">
            <div 
              v-for="base in factionBases" 
              :key="base.id"
              class="base-item"
            >
              <span class="base-name">{{ base.name }}</span>
              <span class="base-tier">Tier {{ base.tier }}</span>
            </div>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>

<style scoped>
.detail-header {
  margin-bottom: var(--space-xl);
}

.back-link {
  font-size: 0.85rem;
  color: var(--color-text-muted);
  margin-bottom: var(--space-sm);
  display: inline-block;
}

.back-link:hover {
  color: var(--color-gold);
}

.header-main h2 {
  margin-bottom: var(--space-sm);
}

.header-tags {
  display: flex;
  gap: var(--space-sm);
}

.stat-card {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: var(--space-xl);
}

.content-grid {
  gap: var(--space-lg);
}

/* Resources */
.resource-list {
  display: flex;
  flex-direction: column;
  gap: var(--space-md);
}

.resource-item {
  display: flex;
  align-items: center;
  gap: var(--space-md);
}

.resource-icon {
  font-size: 0.5rem;
}

.resource-icon.gold { color: #ffd700; }
.resource-icon.lumber { color: #8b4513; }
.resource-icon.oil { color: #1a1a2e; }

.resource-label {
  flex: 1;
  color: var(--color-text-secondary);
}

.resource-value {
  font-family: var(--font-display);
  font-size: 1.25rem;
  color: var(--color-gold);
}

/* Allies */
.allies-list {
  display: flex;
  flex-direction: column;
  gap: var(--space-sm);
}

.ally-item {
  padding: var(--space-sm) var(--space-md);
  background: var(--color-bg-tertiary);
  border-radius: var(--radius-sm);
  color: var(--color-text-primary);
}

.ally-item:hover {
  background: var(--color-bg-hover);
  color: var(--color-gold);
}

/* Units Preview */
.units-preview {
  display: flex;
  flex-direction: column;
  gap: var(--space-xs);
}

.unit-preview-item a {
  display: flex;
  justify-content: space-between;
  padding: var(--space-sm) var(--space-md);
  color: var(--color-text-primary);
  border-radius: var(--radius-sm);
}

.unit-preview-item:hover a {
  background: var(--color-bg-hover);
  color: var(--color-gold);
}

.unit-hp {
  font-size: 0.85rem;
  color: var(--color-text-muted);
}

.view-all {
  display: block;
  text-align: center;
  padding: var(--space-md);
  color: var(--color-gold-dark);
  border-top: 1px solid var(--color-border);
  margin-top: var(--space-sm);
}

.view-all:hover {
  color: var(--color-gold);
}

/* Bases */
.bases-list {
  display: flex;
  flex-direction: column;
  gap: var(--space-xs);
}

.base-item {
  display: flex;
  justify-content: space-between;
  padding: var(--space-sm) var(--space-md);
  border-radius: var(--radius-sm);
}

.base-item:hover {
  background: var(--color-bg-hover);
}

.base-tier {
  font-size: 0.85rem;
  color: var(--color-text-muted);
}
</style>

