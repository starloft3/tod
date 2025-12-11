<script setup>
import { ref, onMounted, provide, computed } from 'vue'
import { RouterLink, RouterView } from 'vue-router'
import { game, factions } from './api'

const gameStatus = ref(null)
const loading = ref(true)
const error = ref(null)

// Faction selector state
const allFactions = ref([])
const selectedFactionId = ref(null) // null = omniscient view
const factionView = ref(null)

// Provide faction view to child components
provide('selectedFactionId', selectedFactionId)
provide('factionView', factionView)

const selectedFactionName = computed(() => {
  if (selectedFactionId.value === null) return 'Omniscient'
  const faction = allFactions.value.find(f => f.id === selectedFactionId.value)
  return faction ? faction.name : 'Unknown'
})

const loadGameStatus = async () => {
  try {
    const response = await game.getStatus()
    gameStatus.value = response.data
    error.value = null
  } catch (e) {
    error.value = 'Failed to connect to game server'
    console.error('API Error:', e)
  } finally {
    loading.value = false
  }
}

const loadFactions = async () => {
  try {
    const response = await factions.list()
    allFactions.value = response.data.filter(f => !f.isDefeated)
  } catch (e) {
    console.error('Failed to load factions:', e)
  }
}

const loadFactionView = async () => {
  try {
    const response = await game.getView(selectedFactionId.value)
    factionView.value = response.data
  } catch (e) {
    console.error('Failed to load faction view:', e)
  }
}

const onFactionChange = () => {
  loadFactionView()
}

onMounted(() => {
  loadGameStatus()
  loadFactions()
  loadFactionView()
  // Refresh every 30 seconds
  setInterval(loadGameStatus, 30000)
})
</script>

<template>
  <div class="app-layout">
    <!-- Header -->
    <header class="app-header">
      <div class="header-brand">
        <h1 class="brand-title">Tides of Darkness</h1>
        <span class="brand-subtitle">Turn-Based Strategy</span>
      </div>
      
      <nav class="header-nav">
        <RouterLink to="/" class="nav-link">Dashboard</RouterLink>
        <RouterLink to="/factions" class="nav-link">Factions</RouterLink>
        <RouterLink to="/units" class="nav-link">Units</RouterLink>
        <RouterLink to="/map" class="nav-link">Map</RouterLink>
        <RouterLink to="/admin" class="nav-link nav-admin">Admin</RouterLink>
      </nav>
      
      <!-- Faction Selector -->
      <div class="faction-selector">
        <label class="selector-label">Viewing as:</label>
        <select 
          v-model="selectedFactionId" 
          @change="onFactionChange"
          class="faction-select"
        >
          <option :value="null">Omniscient (All)</option>
          <optgroup label="Alliance">
            <option 
              v-for="f in allFactions.filter(f => f.isAlliance)" 
              :key="f.id" 
              :value="f.id"
            >
              {{ f.name }}
            </option>
          </optgroup>
          <optgroup label="Horde">
            <option 
              v-for="f in allFactions.filter(f => f.isHorde)" 
              :key="f.id" 
              :value="f.id"
            >
              {{ f.name }}
            </option>
          </optgroup>
        </select>
        <span v-if="factionView" class="vision-count">
          {{ factionView.summary?.visibleHexCount || 0 }} hexes visible
        </span>
      </div>
      
      <div class="header-status">
        <template v-if="gameStatus">
          <div class="status-item">
            <span class="status-label">Turn</span>
            <span class="status-value">{{ gameStatus.turn.turnNumber }}</span>
          </div>
          <div class="status-item">
            <span class="status-label">Phase</span>
            <span class="status-value phase-tag">{{ gameStatus.turn.phase }}</span>
          </div>
        </template>
        <div v-else-if="error" class="status-error">
          ⚠ Offline
        </div>
      </div>
    </header>

    <!-- Main Content -->
    <main class="app-main">
      <RouterView v-slot="{ Component }">
        <transition name="page" mode="out-in">
          <component :is="Component" />
        </transition>
      </RouterView>
    </main>

    <!-- Footer -->
    <footer class="app-footer">
      <div class="footer-content">
        <span>Tides of Darkness © 2015-2025</span>
        <span class="footer-divider">•</span>
        <span v-if="gameStatus" class="text-muted">
          {{ gameStatus.unitCount }} units • {{ gameStatus.baseCount }} bases • {{ gameStatus.factionCount }} factions
        </span>
      </div>
    </footer>
  </div>
</template>

<style scoped>
.app-layout {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
}

/* Header */
.app-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--space-md) var(--space-xl);
  background: linear-gradient(180deg, var(--color-bg-secondary) 0%, var(--color-bg-primary) 100%);
  border-bottom: 1px solid var(--color-border-gold);
  box-shadow: 0 2px 20px rgba(0, 0, 0, 0.5);
  position: sticky;
  top: 0;
  z-index: 100;
}

.header-brand {
  display: flex;
  flex-direction: column;
}

.brand-title {
  font-size: 1.5rem;
  margin: 0;
  background: linear-gradient(180deg, var(--color-gold-light) 0%, var(--color-gold) 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  text-shadow: 0 0 30px var(--color-glow);
}

.brand-subtitle {
  font-size: 0.7rem;
  text-transform: uppercase;
  letter-spacing: 0.2em;
  color: var(--color-text-muted);
}

/* Navigation */
.header-nav {
  display: flex;
  gap: var(--space-xs);
}

.nav-link {
  font-family: var(--font-display);
  font-size: 0.85rem;
  font-weight: 600;
  letter-spacing: 0.05em;
  text-transform: uppercase;
  padding: var(--space-sm) var(--space-md);
  color: var(--color-text-secondary);
  border-radius: var(--radius-sm);
  transition: all var(--transition-fast);
}

.nav-link:hover {
  color: var(--color-gold);
  background: var(--color-bg-hover);
}

.nav-link.router-link-active {
  color: var(--color-gold);
  background: var(--color-bg-tertiary);
  border-bottom: 2px solid var(--color-gold);
}

.nav-admin {
  margin-left: var(--space-md);
  border: 1px solid var(--color-border);
}

.nav-admin:hover {
  border-color: var(--color-gold);
}

/* Faction Selector */
.faction-selector {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  padding: var(--space-xs) var(--space-md);
  background: var(--color-bg-tertiary);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
}

.selector-label {
  font-size: 0.75rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--color-text-muted);
}

.faction-select {
  background: var(--color-bg-primary);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  color: var(--color-gold);
  font-family: var(--font-display);
  font-size: 0.9rem;
  padding: var(--space-xs) var(--space-sm);
  cursor: pointer;
  min-width: 150px;
}

.faction-select:hover {
  border-color: var(--color-gold);
}

.faction-select:focus {
  outline: none;
  border-color: var(--color-gold);
  box-shadow: 0 0 0 2px rgba(201, 162, 39, 0.2);
}

.faction-select option {
  background: var(--color-bg-primary);
  color: var(--color-text-primary);
}

.faction-select optgroup {
  font-weight: bold;
  color: var(--color-text-secondary);
}

.vision-count {
  font-size: 0.75rem;
  color: var(--color-text-muted);
}

/* Status */
.header-status {
  display: flex;
  gap: var(--space-lg);
}

.status-item {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.status-label {
  font-size: 0.65rem;
  text-transform: uppercase;
  letter-spacing: 0.1em;
  color: var(--color-text-muted);
}

.status-value {
  font-family: var(--font-display);
  font-size: 1rem;
  color: var(--color-gold);
}

.phase-tag {
  text-transform: capitalize;
}

.status-error {
  color: var(--color-blood-light);
  font-size: 0.85rem;
}

/* Main Content */
.app-main {
  flex: 1;
  padding: var(--space-xl);
  max-width: 1400px;
  margin: 0 auto;
  width: 100%;
}

/* Footer */
.app-footer {
  padding: var(--space-md) var(--space-xl);
  background: var(--color-bg-secondary);
  border-top: 1px solid var(--color-border);
}

.footer-content {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-sm);
  font-size: 0.8rem;
  color: var(--color-text-muted);
}

.footer-divider {
  color: var(--color-border);
}

/* Page transitions */
.page-enter-active,
.page-leave-active {
  transition: opacity 0.2s ease, transform 0.2s ease;
}

.page-enter-from {
  opacity: 0;
  transform: translateY(10px);
}

.page-leave-to {
  opacity: 0;
  transform: translateY(-10px);
}
</style>
