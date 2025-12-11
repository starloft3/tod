import { createRouter, createWebHistory } from 'vue-router'

import Dashboard from '../views/Dashboard.vue'
import Factions from '../views/Factions.vue'
import FactionDetail from '../views/FactionDetail.vue'
import Units from '../views/Units.vue'
import UnitDetail from '../views/UnitDetail.vue'
import Map from '../views/Map.vue'
import Admin from '../views/Admin.vue'

const routes = [
  {
    path: '/',
    name: 'Dashboard',
    component: Dashboard
  },
  {
    path: '/factions',
    name: 'Factions',
    component: Factions
  },
  {
    path: '/factions/:id',
    name: 'FactionDetail',
    component: FactionDetail,
    props: true
  },
  {
    path: '/units',
    name: 'Units',
    component: Units
  },
  {
    path: '/units/:id',
    name: 'UnitDetail',
    component: UnitDetail,
    props: true
  },
  {
    path: '/map',
    name: 'Map',
    component: Map
  },
  {
    path: '/admin',
    name: 'Admin',
    component: Admin
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router

