/* Vue Router 配置（Hash 模式） */

import { createRouter, createWebHashHistory } from 'vue-router'

/* 页面路由表 */
const routes = [
  { path: '/', name: 'Home', component: () => import('../views/Home.vue') },
  { path: '/sessions', name: 'Sessions', component: () => import('../views/Sessions.vue') },
  { path: '/carpools', name: 'Carpools', component: () => import('../views/Carpool.vue') },
  { path: '/dms', name: 'DMs', component: () => import('../views/DMs.vue') },
  { path: '/members', name: 'Members', component: () => import('../views/Members.vue') },
  { path: '/scripts', name: 'Scripts', component: () => import('../views/Scripts.vue') },
  { path: '/stats/revenue', name: 'StatsRevenue', component: () => import('../views/StatsRevenue.vue') },
  { path: '/stats/scripts', name: 'StatsScripts', component: () => import('../views/StatsScripts.vue') },
  { path: '/stats/dms', name: 'StatsDMs', component: () => import('../views/StatsDMs.vue') },
  { path: '/messages', name: 'Messages', component: () => import('../views/Messages.vue') }
]

const router = createRouter({
  history: createWebHashHistory(),
  routes
})

export default router
