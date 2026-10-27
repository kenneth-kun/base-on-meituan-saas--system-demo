<script setup lang="ts">
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import state, { hasFeature, isAdmin, logout } from '@/auth'

const route = useRoute()
const router = useRouter()

const merchantMenus = [
  { path: '/dashboard', label: '经营看板', icon: 'DataAnalysis', feature: 'dashboard' },
  { path: '/orders', label: '订单管理', icon: 'List', feature: 'orders' },
  { path: '/products', label: '商品管理', icon: 'Goods', feature: 'products' },
  { path: '/reviews', label: '评价管理', icon: 'ChatDotRound', feature: 'reviews' },
  { path: '/service', label: '客服工作台', icon: 'Service', feature: 'service' },
  { path: '/alerts', label: '预警中心', icon: 'Bell', feature: 'alerts' },
  { path: '/settings', label: '设置', icon: 'Setting', feature: 'service' },
]

const menus = computed(() => {
  if (isAdmin()) return [{ path: '/admin', label: '管理后台', icon: 'Setting' }]
  return merchantMenus.filter((m) => hasFeature(m.feature))
})

const username = computed(() => state.user?.username || '')

function onLogout() {
  logout()
  router.push('/login')
}
</script>

<template>
  <div class="shell">
    <aside class="sidebar">
      <div class="logo">美团商家 SaaS</div>
      <el-menu router :default-active="route.path" class="menu">
        <el-menu-item v-for="m in menus" :key="m.path" :index="m.path">
          <el-icon><component :is="m.icon" /></el-icon>
          <span>{{ m.label }}</span>
        </el-menu-item>
      </el-menu>
      <div class="sidebar-footer">
        <div class="user">{{ username }}</div>
        <el-button link size="small" @click="onLogout">退出登录</el-button>
      </div>
    </aside>
    <main class="content">
      <router-view />
    </main>
  </div>
</template>

<style scoped>
.shell {
  display: flex;
  min-height: 100vh;
}
.sidebar {
  width: 220px;
  flex-shrink: 0;
  background: var(--surface-1);
  border-right: 1px solid var(--gridline);
  padding: 16px 0;
  display: flex;
  flex-direction: column;
}
.logo {
  font-size: 16px;
  font-weight: 700;
  padding: 4px 24px 20px;
}
.menu {
  border-right: none;
  flex: 1;
}
.sidebar-footer {
  padding: 12px 24px;
  border-top: 1px solid var(--gridline);
  font-size: 13px;
}
.user {
  margin-bottom: 4px;
  color: var(--text-secondary);
}
.content {
  flex: 1;
  min-width: 0;
  padding: 20px;
}
</style>
