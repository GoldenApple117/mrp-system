import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  { path: '/', redirect: '/materials' },
  {
    path: '/materials',
    name: 'Materials',
    component: () => import('@/views/MaterialList.vue'),
  },
  {
    path: '/bom',
    name: 'Bom',
    component: () => import('@/views/BomList.vue'),
  },
  {
    path: '/inventory',
    name: 'Inventory',
    component: () => import('@/views/InventoryList.vue'),
  },
  {
    path: '/mps',
    name: 'Mps',
    component: () => import('@/views/MpsList.vue'),
  },
  {
    path: '/mrp',
    name: 'Mrp',
    component: () => import('@/views/MrpRun.vue'),
  },
  {
    path: '/purchase',
    name: 'Purchase',
    component: () => import('@/views/PurchaseList.vue'),
  },
  {
    path: '/production',
    name: 'Production',
    component: () => import('@/views/ProductionList.vue'),
  },
  {
    path: '/reports',
    name: 'Reports',
    component: () => import('@/views/Reports.vue'),
  },
  {
    path: '/crp',
    name: 'Crp',
    component: () => import('@/views/CrpAnalysis.vue'),
  },
  {
    path: '/inspection',
    name: 'Inspection',
    component: () => import('@/views/InspectionList.vue'),
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

export default router
