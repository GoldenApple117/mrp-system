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
    path: '/routings',
    name: 'Routings',
    component: () => import('@/views/RoutingList.vue'),
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
  {
    path: '/sales',
    name: 'Sales',
    component: () => import('@/views/SalesList.vue'),
  },
  {
    path: '/suppliers',
    name: 'Suppliers',
    component: () => import('@/views/SuppliersList.vue'),
  },
  {
    path: '/cost',
    name: 'Cost',
    component: () => import('@/views/CostSummary.vue'),
  },
  {
    path: '/finance',
    name: 'Finance',
    component: () => import('@/views/FinanceList.vue'),
  },
  {
    path: '/exceptions',
    name: 'Exceptions',
    component: () => import('@/views/ExceptionBoard.vue'),
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

export default router
