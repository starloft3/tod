<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute } from 'vue-router'
import { units, factions } from '../api'

const route = useRoute()
const props = defineProps(['id'])

const unit = ref(null)
const faction = ref(null)
const loading = ref(true)

const loadUnit = async () => {
  loading.value = true
  const unitId = props.id || route.params.id
  
  try {
    const unitRes = await units.get(unitId)
    unit.value = unitRes.data
    
    // Load faction info
    const factionRes = await factions.get(unit.value.factionId)
    faction.value = factionRes.data
  } catch (e) {
    console.error('Failed to load unit:', e)
  } finally {
    loading.value = false
  }
}

const hpPercent = computed(() => {
  if (!unit.value) return 0
  return (unit.value.hp / unit.value.maxHp) * 100
})

const hpClass = computed(() => {
  if (hpPercent.value < 25) return 'critical'
  if (hpPercent.value < 50) return 'damaged'
  return ''
})

const abilities = computed(() => {
  if (!unit.value) return []
  const abs = []
  if (unit.value.tier1Ability !== 'none') abs.push({ tier: 1, name: unit.value.tier1Ability })
  if (unit.value.tier2Ability !== 'none') abs.push({ tier: 2, name: unit.value.tier2Ability })
  if (unit.value.tier3Ability !== 'none') abs.push({ tier: 3, name: unit.value.tier3Ability })
  if (unit.value.tier4Ability !== 'none') abs.push({ tier: 4, name: unit.value.tier4Ability })
  return abs
})

onMounted(loadUnit)
watch(() => route.params.id, loadUnit)
</script>

<template>
  <div class="unit-detail fade-in">
    <!-- Loading -->
    <div v-if="loading" class="loading">
      <div class="spinner"></div>
      <p>Loading unit data...</p>
    </div>

    <template v-else-if="unit">
      <!-- Header -->
      <header class="detail-header">
        <RouterLink to="/units" class="back-link">← All Units</RouterLink>
        
        <div class="unit-header">
          <div class="unit-title">
            <h2>{{ unit.name }}</h2>
            <div class="unit-meta">
              <span 
                class="tag"
                :class="faction?.isHorde ? 'tag-horde' : 'tag-alliance'"
              >
                {{ faction?.name || 'Unknown' }}
              </span>
              <span class="tag capitalize">{{ unit.category?.replace('_', ' ') }}</span>
              <span v-if="unit.tier > 0" class="tag tag-gold">Veteran ★{{ unit.tier }}</span>
            </div>
          </div>
          
          <div class="unit-status" :class="{ dead: !unit.alive }">
            {{ unit.alive ? 'Active' : 'Fallen' }}
          </div>
        </div>
      </header>

      <!-- Main Stats -->
      <section class="stats-section grid grid-4 mb-lg">
        <div class="card stat-card hp-card">
          <div class="stat">
            <div class="hp-display">
              <span class="stat-value">{{ unit.hp }}</span>
              <span class="hp-max">/ {{ unit.maxHp }}</span>
            </div>
            <div class="hp-bar large">
              <div 
                class="hp-bar-fill"
                :class="hpClass"
                :style="{ width: `${hpPercent}%` }"
              ></div>
            </div>
            <span class="stat-label">Hit Points</span>
          </div>
        </div>
        
        <div class="card stat-card">
          <div class="stat">
            <span class="stat-value">{{ unit.combat }}</span>
            <span class="stat-label">Combat</span>
          </div>
        </div>
        
        <div class="card stat-card">
          <div class="stat">
            <span class="stat-value">{{ unit.movementRemaining }}/{{ unit.movementMax }}</span>
            <span class="stat-label">Movement</span>
          </div>
        </div>
        
        <div class="card stat-card">
          <div class="stat">
            <span class="stat-value">{{ unit.vision }}</span>
            <span class="stat-label">Vision</span>
          </div>
        </div>
      </section>

      <div class="content-grid grid grid-2">
        <!-- Combat Stats -->
        <div class="card">
          <div class="card-header">
            <h3 class="card-title">⚔ Combat Stats</h3>
          </div>
          <div class="stat-list">
            <div class="stat-row">
              <span class="stat-name">Light Armor</span>
              <span class="stat-val">{{ unit.lightArmorCurrent }}/{{ unit.lightArmorMax }}</span>
            </div>
            <div class="stat-row">
              <span class="stat-name">Heavy Armor</span>
              <span class="stat-val">{{ unit.heavyArmor }}</span>
            </div>
            <div class="stat-row">
              <span class="stat-name">Natural Armor</span>
              <span class="stat-val">{{ unit.naturalArmor }}</span>
            </div>
            <div class="stat-row">
              <span class="stat-name">Stealth</span>
              <span class="stat-val">{{ unit.stealth || 0 }}</span>
            </div>
            <div class="stat-row">
              <span class="stat-name">Armor Broken</span>
              <span class="stat-val" :class="unit.armorBroken ? 'danger' : ''">
                {{ unit.armorBroken ? 'Yes' : 'No' }}
              </span>
            </div>
            <div class="stat-row">
              <span class="stat-name">Has Fired</span>
              <span class="stat-val">{{ unit.fired ? 'Yes' : 'No' }}</span>
            </div>
          </div>
        </div>

        <!-- Position & Movement -->
        <div class="card">
          <div class="card-header">
            <h3 class="card-title">📍 Position</h3>
          </div>
          <div class="stat-list">
            <div class="stat-row">
              <span class="stat-name">Current Location</span>
              <span class="stat-val highlight">Hex {{ unit.location }}</span>
            </div>
            <div class="stat-row">
              <span class="stat-name">Previous Location</span>
              <span class="stat-val">Hex {{ unit.previousLocation }}</span>
            </div>
            <div class="stat-row">
              <span class="stat-name">Road Move Only</span>
              <span class="stat-val">{{ unit.roadMoveOnly ? 'Yes' : 'No' }}</span>
            </div>
            <div class="stat-row">
              <span class="stat-name">Road Movement</span>
              <span class="stat-val">{{ unit.roadMoveRemaining }}/{{ unit.movementMax }}</span>
            </div>
          </div>
        </div>

        <!-- Combat Bonuses -->
        <div class="card">
          <div class="card-header">
            <h3 class="card-title">📊 Combat Modifiers</h3>
          </div>
          <div class="stat-list">
            <div class="stat-row">
              <span class="stat-name">Terrain Bonus</span>
              <span class="stat-val" :class="unit.terrainBonus > 0 ? 'success' : unit.terrainBonus < 0 ? 'danger' : ''">
                {{ unit.terrainBonus > 0 ? '+' : '' }}{{ unit.terrainBonus }}
              </span>
            </div>
            <div class="stat-row">
              <span class="stat-name">Flank Bonus</span>
              <span class="stat-val" :class="unit.flankBonus > 0 ? 'success' : ''">
                {{ unit.flankBonus > 0 ? '+' : '' }}{{ unit.flankBonus }}
              </span>
            </div>
            <div class="stat-row">
              <span class="stat-name">Hold Bonus</span>
              <span class="stat-val" :class="unit.holdBonus > 0 ? 'success' : ''">
                {{ unit.holdBonus > 0 ? '+' : '' }}{{ unit.holdBonus }}
              </span>
            </div>
            <div class="stat-row">
              <span class="stat-name">Combat Start</span>
              <span class="stat-val">{{ unit.combatStart }}</span>
            </div>
          </div>
        </div>

        <!-- Abilities -->
        <div class="card">
          <div class="card-header">
            <h3 class="card-title">✨ Abilities</h3>
          </div>
          <div v-if="abilities.length" class="abilities-list">
            <div 
              v-for="ability in abilities" 
              :key="ability.tier"
              class="ability-item"
            >
              <span class="ability-tier">Tier {{ ability.tier }}</span>
              <span class="ability-name">{{ ability.name }}</span>
            </div>
          </div>
          <p v-else class="text-muted">No special abilities</p>
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
  display: inline-block;
  margin-bottom: var(--space-md);
}

.back-link:hover {
  color: var(--color-gold);
}

.unit-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
}

.unit-title h2 {
  margin-bottom: var(--space-sm);
}

.unit-meta {
  display: flex;
  gap: var(--space-sm);
  flex-wrap: wrap;
}

.capitalize {
  text-transform: capitalize;
}

.unit-status {
  font-family: var(--font-display);
  font-size: 0.9rem;
  text-transform: uppercase;
  letter-spacing: 0.1em;
  color: var(--color-success);
  padding: var(--space-sm) var(--space-md);
  background: rgba(45, 122, 58, 0.2);
  border: 1px solid var(--color-success);
  border-radius: var(--radius-sm);
}

.unit-status.dead {
  color: var(--color-danger);
  background: rgba(139, 42, 42, 0.2);
  border-color: var(--color-danger);
}

.stat-card {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: var(--space-xl);
}

.hp-card .stat {
  width: 100%;
}

.hp-display {
  display: flex;
  align-items: baseline;
  justify-content: center;
  gap: var(--space-xs);
}

.hp-max {
  font-size: 1rem;
  color: var(--color-text-muted);
}

.hp-bar.large {
  height: 10px;
  margin: var(--space-sm) 0;
}

.content-grid {
  gap: var(--space-lg);
}

.stat-list {
  display: flex;
  flex-direction: column;
}

.stat-row {
  display: flex;
  justify-content: space-between;
  padding: var(--space-sm) 0;
  border-bottom: 1px solid var(--color-border);
}

.stat-row:last-child {
  border-bottom: none;
}

.stat-name {
  color: var(--color-text-secondary);
}

.stat-val {
  font-family: var(--font-display);
  color: var(--color-text-primary);
}

.stat-val.highlight {
  color: var(--color-gold);
}

.stat-val.success {
  color: var(--color-success);
}

.stat-val.danger {
  color: var(--color-danger);
}

.abilities-list {
  display: flex;
  flex-direction: column;
  gap: var(--space-sm);
}

.ability-item {
  display: flex;
  gap: var(--space-md);
  padding: var(--space-sm) var(--space-md);
  background: var(--color-bg-tertiary);
  border-radius: var(--radius-sm);
  border-left: 3px solid var(--color-gold);
}

.ability-tier {
  font-size: 0.75rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--color-gold);
  min-width: 50px;
}

.ability-name {
  color: var(--color-text-primary);
}
</style>

