import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/Login.vue'),
    meta: { noAuth: true },
  },
  {
    path: '/',
    redirect: '/dashboard',
  },
  {
    path: '/dashboard',
    name: 'Dashboard',
    component: () => import('@/views/Dashboard.vue'),
  },
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
  {
    path: '/shop-floor',
    name: 'ShopFloor',
    component: () => import('@/views/ShopFloor.vue'),
  },
  {
    path: '/permissions',
    name: 'Permissions',
    component: () => import('@/views/PermissionList.vue'),
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

// 路由守卫：未登录跳转登录页
router.beforeEach((to, _from, next) => {
  const token = localStorage.getItem('token')
  if (to.meta.noAuth) {
    // 已登录用户访问登录页 → 跳仪表板
    if (token) return next('/dashboard')
    return next()
  }
  if (!token) return next('/login')
  next()
})

export default router
