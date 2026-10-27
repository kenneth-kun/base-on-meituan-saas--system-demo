<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{
  label: string
  value: string
  delta?: number | null
  deltaLabel?: string
}>()

const color = computed(() => {
  if (props.delta === null || props.delta === undefined) return 'var(--text-muted)'
  // 这些指标都是「涨是好」——涨绿跌红
  return props.delta >= 0 ? 'var(--delta-up)' : 'var(--status-critical)'
})

const deltaText = computed(() => {
  if (props.delta === null || props.delta === undefined) return '—'
  const sign = props.delta >= 0 ? '+' : ''
  return `${sign}${props.delta.toFixed(2)}%`
})

const arrow = computed(() => {
  if (props.delta === null || props.delta === undefined) return ''
  return props.delta >= 0 ? '↑' : '↓'
})
</script>

<template>
  <div class="kpi-card">
    <div class="kpi-label">{{ label }}</div>
    <div class="kpi-value">{{ value }}</div>
    <div class="kpi-delta" :style="{ color }">
      <span v-if="arrow">{{ arrow }} {{ deltaText }}</span>
      <span v-else class="kpi-none">—</span>
      <span class="kpi-delta-label">{{ deltaLabel || '较 7 天前' }}</span>
    </div>
  </div>
</template>

<style scoped>
.kpi-card {
  background: var(--surface-1);
  border: 1px solid var(--gridline);
  border-radius: 10px;
  padding: 16px 20px;
}
.kpi-label {
  font-size: 13px;
  color: var(--text-muted);
  margin-bottom: 8px;
}
.kpi-value {
  font-size: 30px;
  font-weight: 600;
  letter-spacing: -0.5px;
}
.kpi-delta {
  font-size: 13px;
  margin-top: 6px;
}
.kpi-delta-label {
  color: var(--text-muted);
  margin-left: 6px;
}
.kpi-none {
  color: var(--text-muted);
}
</style>
