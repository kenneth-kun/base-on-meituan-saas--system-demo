import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', redirect: '/dashboard' },
    { path: '/login', component: () => import('@/views/LoginView.vue') },
    { path: '/dashboard', name: 'dashboard', component: () => import('@/views/DashboardView.vue') },
    { path: '/orders', component: () => import('@/views/OrdersView.vue') },
    { path: '/products', component: () => import('@/views/ProductsView.vue') },
    { path: '/reviews', component: () => import('@/views/ReviewsView.vue') },
    { path: '/alerts', component: () => import('@/views/AlertsView.vue') },
    { path: '/service', component: () => import('@/views/ServiceView.vue') },
    { path: '/settings', component: () => import('@/views/SettingsView.vue') },
    { path: '/analytics/trend', component: () => import('@/views/TrendAnalysisView.vue') },
    { path: '/analytics/reputation', component: () => import('@/views/ReputationAnalysisView.vue') },
    { path: '/admin', component: () => import('@/views/AdminView.vue') },
  ],
})

router.beforeEach((to) => {
  const token = localStorage.getItem('token')
  const user = JSON.parse(localStorage.getItem('user') || 'null')

  if (to.path === '/login') {
    return token ? '/dashboard' : true
  }
  if (!token) {
    return '/login'
  }
  if (to.path === '/admin' && user?.type !== 'admin') {
    return '/dashboard'
  }
  return true
})

export default router
