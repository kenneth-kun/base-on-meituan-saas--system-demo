<script setup lang="ts">
defineProps<{ title: string }>()
</script>

<template>
  <div class="placeholder">
    <h1>{{ title }}</h1>
    <p>该模块开发中</p>
    <el-button @click="$router.push('/dashboard')">返回看板</el-button>
  </div>
</template>

<style scoped>
.placeholder {
  max-width: 1280px;
  margin: 0 auto;
  padding: 80px 20px;
  text-align: center;
  color: var(--text-secondary);
}
.placeholder h1 {
  color: var(--text-primary);
  font-size: 22px;
}
</style>
