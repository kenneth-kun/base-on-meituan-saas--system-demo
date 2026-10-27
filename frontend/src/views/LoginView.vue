<script setup lang="ts">
import { ElMessage } from 'element-plus'
import { ref } from 'vue'
import { useRouter } from 'vue-router'

import { api } from '@/api'
import { setAuth } from '@/auth'

const router = useRouter()
const role = ref<'merchant' | 'admin'>('merchant')
const username = ref('')
const password = ref('')
const loading = ref(false)

async function login() {
  if (!username.value || !password.value) {
    ElMessage.warning('请输入账号密码')
    return
  }
  loading.value = true
  try {
    const r = await api.login(username.value, password.value, role.value)
    localStorage.setItem('token', r.token)  // 先存 token 供 me() 用
    const me = await api.me()
    setAuth(r.token, me)
    ElMessage.success('登录成功')
    router.push(role.value === 'admin' ? '/admin' : '/dashboard')
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || '登录失败')
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="login-page">
    <el-card class="login-card" shadow="never">
      <div class="login-title">美团商家 SaaS</div>
      <div class="login-sub">商家经营工具 · 管理后台</div>

      <el-radio-group v-model="role" class="role-switch">
        <el-radio-button value="merchant">商家登录</el-radio-button>
        <el-radio-button value="admin">管理员登录</el-radio-button>
      </el-radio-group>

      <el-input v-model="username" placeholder="账号" class="field" @keyup.enter="login" />
      <el-input v-model="password" type="password" placeholder="密码" show-password class="field" @keyup.enter="login" />

      <el-button type="primary" class="login-btn" :loading="loading" @click="login">登录</el-button>

      <div class="hint">
        测试账号：<br />
        商家 merchant1 / 123456<br />
        管理员 admin / admin123
      </div>
    </el-card>
  </div>
</template>

<style scoped>
.login-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--page-plane);
}
.login-card {
  width: 360px;
  padding: 8px 12px 20px;
}
.login-title {
  font-size: 22px;
  font-weight: 700;
  text-align: center;
}
.login-sub {
  font-size: 13px;
  color: var(--text-muted);
  text-align: center;
  margin: 6px 0 20px;
}
.role-switch {
  display: flex;
  justify-content: center;
  margin-bottom: 20px;
}
.field {
  margin-bottom: 14px;
}
.login-btn {
  width: 100%;
  margin-top: 4px;
}
.hint {
  margin-top: 18px;
  font-size: 12px;
  color: var(--text-muted);
  line-height: 1.7;
}
</style>
