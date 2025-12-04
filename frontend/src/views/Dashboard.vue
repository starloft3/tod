<script setup>
import { ref, computed, onMounted } from 'vue'
import { game, factions } from '../api'

const gameStatus = ref(null)
const statistics = ref(null)
const hordeFactions = ref([])
const allianceFactions = ref([])
const loading = ref(true)
const error = ref(null)

const loadData = async () => {
  loading.value = true
  try {
    const [statusRes, statsRes, hordeRes, allianceRes] = await Promise.all([
      game.getStatus(),
      game.getStatistics(),
      factions.horde({ activeOnly: true }),
      factions.alliance({ activeOnly: true })
    ])
    gameStatus.value = statusRes.data
    statistics.value = statsRes.data
    hordeFactions.value = hordeRes.data
    allianceFactions.value = allianceRes.data
    error.value = null
  } catch (e) {
    error.value = 'Failed to load game data'
    console.error(e)
  } finally {
    loading.value = false
  }
}

const hordeUnits = computed(() => {
  if (!statistics.value) return 0
  return hordeFactions.value.reduce((sum, f) => 
    sum + (statistics.value.unitsByFaction[f.id] || 0), 0)
})

const allianceUnits = computed(() => {
  if (!statistics.value) return 0
  return allianceFactions.value.reduce((sum, f) => 
    sum + (statistics.value.unitsByFaction[f.id] || 0), 0)
})

onMounted(loadData)
</script>

<template>
  <div class="dashboard fade-in">
    <header class="page-header">
      <h2>War Room</h2>
      <p class="text-muted">Strategic Overview of the Eastern Kingdoms</p>
    </header>

    <!-- Loading State -->
    <div v-if="loading" class="loading">
      <div class="spinner"></div>
      <p>Loading war reports...</p>
    </div>

    <!-- Error State -->
    <div v-else-if="error" class="error-message card">
      <h3>⚠ Connection Lost</h3>
      <p>{{ error }}</p>
      <button class="btn" @click="loadData">Retry</button>
    </div>

    <!-- Dashboard Content -->
    <template v-else>
      <!-- Game Status -->
      <section class="status-section grid grid-4 mb-lg">
        <div class="card stat-card">
          <div class="stat">
            <span class="stat-value">{{ gameStatus.turn.turnNumber }}</span>
            <span class="stat-label">Current Turn</span>
          </div>
        </div>
        <div class="card stat-card">
          <div class="stat">
            <span class="stat-value capitalize">{{ gameStatus.turn.phase }}</span>
            <span class="stat-label">Phase</span>
          </div>
        </div>
        <div class="card stat-card">
          <div class="stat">
            <span class="stat-value">{{ gameStatus.aliveUnitCount }}</span>
            <span class="stat-label">Active Units</span>
          </div>
        </div>
        <div class="card stat-card">
          <div class="stat">
            <span class="stat-value">{{ gameStatus.baseCount }}</span>
            <span class="stat-label">Settlements</span>
          </div>
        </div>
      </section>

      <!-- Faction Overview -->
      <section class="factions-section grid grid-2">
        <!-- Horde -->
        <div class="card faction-overview horde-card">
          <div class="card-header">
            <h3 class="card-title">
              <span class="faction-icon">⚔</span>
              The Horde
            </h3>
            <span class="tag tag-horde">{{ hordeFactions.length }} Clans</span>
          </div>
          
          <div class="faction-stats">
            <div class="stat">
              <span class="stat-value">{{ hordeUnits }}</span>
              <span class="stat-label">Warriors</span>
            </div>
          </div>

          <div class="faction-list">
            <div 
              v-for="faction in hordeFactions" 
              :key="faction.id"
              class="faction-item"
            >
              <RouterLink :to="`/factions/${faction.id}`" class="faction-link">
                <span class="faction-name">{{ faction.name }}</span>
                <span class="faction-units">
                  {{ statistics.unitsByFaction[faction.id] || 0 }} units
                </span>
              </RouterLink>
            </div>
          </div>
        </div>

        <!-- Alliance -->
        <div class="card faction-overview alliance-card">
          <div class="card-header">
            <h3 class="card-title">
              <span class="faction-icon">🛡</span>
              The Alliance
            </h3>
            <span class="tag tag-alliance">{{ allianceFactions.length }} Nations</span>
          </div>
          
          <div class="faction-stats">
            <div class="stat">
              <span class="stat-value">{{ allianceUnits }}</span>
              <span class="stat-label">Soldiers</span>
            </div>
          </div>

          <div class="faction-list">
            <div 
              v-for="faction in allianceFactions" 
              :key="faction.id"
              class="faction-item"
            >
              <RouterLink :to="`/factions/${faction.id}`" class="faction-link">
                <span class="faction-name">{{ faction.name }}</span>
                <span class="faction-units">
                  {{ statistics.unitsByFaction[faction.id] || 0 }} units
                </span>
              </RouterLink>
            </div>
          </div>
        </div>
      </section>

      <!-- Quick Actions -->
      <section class="actions-section mt-md">
        <div class="card">
          <div class="card-header">
            <h3 class="card-title">Command Actions</h3>
          </div>
          <div class="action-buttons">
            <RouterLink to="/units" class="btn">
              View All Units
            </RouterLink>
            <RouterLink to="/map" class="btn">
              Strategic Map
            </RouterLink>
            <button class="btn" @click="loadData">
              Refresh Intel
            </button>
          </div>
        </div>
      </section>
    </template>
  </div>
</template>

<style scoped>
.page-header {
  margin-bottom: var(--space-xl);
}

.page-header h2 {
  margin-bottom: var(--space-xs);
}

.stat-card {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: var(--space-xl);
}

.capitalize {
  text-transform: capitalize;
}

/* Faction Cards */
.faction-overview {
  position: relative;
  overflow: hidden;
}

.horde-card {
  border-color: var(--color-horde-red);
}

.horde-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 3px;
  background: linear-gradient(90deg, transparent, var(--color-horde-red), transparent);
}

.alliance-card {
  border-color: var(--color-alliance-blue);
}

.alliance-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 3px;
  background: linear-gradient(90deg, transparent, var(--color-alliance-blue), transparent);
}

.faction-icon {
  margin-right: var(--space-sm);
}

.faction-stats {
  display: flex;
  justify-content: center;
  padding: var(--space-lg) 0;
  border-bottom: 1px solid var(--color-border);
  margin-bottom: var(--space-md);
}

.faction-list {
  display: flex;
  flex-direction: column;
  gap: var(--space-xs);
}

.faction-item {
  border-radius: var(--radius-sm);
  transition: background var(--transition-fast);
}

.faction-item:hover {
  background: var(--color-bg-hover);
}

.faction-link {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--space-sm) var(--space-md);
  color: var(--color-text-primary);
}

.faction-link:hover {
  color: var(--color-gold);
}

.faction-units {
  font-size: 0.85rem;
  color: var(--color-text-muted);
}

/* Actions */
.action-buttons {
  display: flex;
  gap: var(--space-md);
  flex-wrap: wrap;
}

.error-message {
  text-align: center;
  padding: var(--space-2xl);
}

.error-message h3 {
  color: var(--color-blood-light);
  margin-bottom: var(--space-md);
}
</style>

