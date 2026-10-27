<script setup lang="ts">
import type { EChartsOption } from 'echarts'
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'

import { api } from '@/api'
import EChart from '@/components/EChart.vue'

const router = useRouter()
const trend = ref<{ items: { date: string; revenue: string; order_count: number }[] }>({ items: [] })
const hourly = ref<{ items: { hour: number; order_count: number }[] }>({ items: [] })
const trendMetric = ref<'revenue' | 'order_count' | 'avg'>('revenue')

onMounted(async () => {
  const [t, h] = await Promise.all([api.trend(90), api.hourly(30)])
  trend.value = t
  hourly.value = h
})

const INK = '#898781'
const GRID = '#e1e0d9'
const BASELINE = '#c3c2b7'
const BLUE = '#2a78d6'

const axisX = (data: string[]) => ({
  type: 'category' as const,
  data,
  axisLine: { lineStyle: { color: BASELINE } },
  axisTick: { show: false },
  axisLabel: { color: INK },
})
const axisY = () => ({
  type: 'value' as const,
  axisLabel: { color: INK },
  splitLine: { lineStyle: { color: GRID } },
})

const trendOption = computed<EChartsOption>(() => {
  const items = trend.value.items
  let data: number[] = []
  let name = '营收'
  if (trendMetric.value === 'revenue') {
    data = items.map((i) => Number(i.revenue))
  } else if (trendMetric.value === 'order_count') {
    data = items.map((i) => i.order_count)
    name = '订单量'
  } else {
    data = items.map((i) => (i.order_count ? Number(i.revenue) / i.order_count : 0))
    name = '客单价'
  }
  return {
    grid: { left: 56, right: 16, top: 24, bottom: 32 },
    tooltip: {
      trigger: 'axis',
      valueFormatter: (v) =>
        trendMetric.value === 'avg'
          ? '¥' + Number(v).toFixed(2)
          : trendMetric.value === 'revenue'
            ? '¥' + Number(v).toLocaleString('zh-CN', { minimumFractionDigits: 2 })
            : String(v),
    },
    xAxis: axisX(items.map((i) => i.date.slice(5))),
    yAxis: axisY(),
    series: [{
      name, type: 'line', data, showSymbol: false,
      lineStyle: { width: 2, color: BLUE }, itemStyle: { color: BLUE },
      areaStyle: { color: 'rgba(42,120,214,0.10)' },
    }],
  }
})

const hourlyOption = computed<EChartsOption>(() => ({
  grid: { left: 40, right: 16, top: 16, bottom: 28 },
  tooltip: { trigger: 'axis' },
  xAxis: { ...axisX(hourly.value.items.map((i) => `${i.hour}时`)), axisLabel: { color: INK, interval: 2 } },
  yAxis: axisY(),
  series: [{
    name: '订单量', type: 'bar',
    data: hourly.value.items.map((i) => i.order_count),
    barWidth: 14, itemStyle: { color: BLUE, borderRadius: [4, 4, 0, 0] },
  }],
}))
</script>

<template>
  <div>
    <el-button link @click="router.push('/dashboard')" class="back">← 返回看板</el-button>
    <div class="page-title">趋势分析</div>

    <el-card class="block" shadow="never">
      <div class="block-header">
        <span class="block-title">经营趋势 · 近 90 天</span>
        <el-radio-group v-model="trendMetric" size="small">
          <el-radio-button value="revenue">营收</el-radio-button>
          <el-radio-button value="order_count">订单量</el-radio-button>
          <el-radio-button value="avg">客单价</el-radio-button>
        </el-radio-group>
      </div>
      <EChart class="chart-lg" :option="trendOption" />
    </el-card>

    <el-card class="block" shadow="never">
      <div class="block-header">
        <span class="block-title">时段分布 · 近 30 天</span>
        <span class="block-sub">找午餐 / 晚餐高峰，合理安排备货与人力</span>
      </div>
      <EChart class="chart-md" :option="hourlyOption" />
    </el-card>
  </div>
</template>

<style scoped>
.back {
  margin-bottom: 4px;
}
.block {
  margin-bottom: 16px;
}
.block-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
}
.block-title {
  font-size: 15px;
  font-weight: 600;
}
.block-sub {
  color: var(--text-muted);
  font-size: 12px;
}
.chart-lg {
  height: 320px;
}
.chart-md {
  height: 260px;
}
</style>
