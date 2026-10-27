<script setup lang="ts">
import type { EChartsOption } from 'echarts'
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'

import { api, type WordFreqResp, type WordItem } from '@/api'
import EChart from '@/components/EChart.vue'

const router = useRouter()
const dist = ref<{ items: { rating: number; count: number; pct: number }[]; total: number; avg_rating: number }>(
  { items: [], total: 0, avg_rating: 0 },
)
const sentiment = ref<{ items: { date: string; good_rate: number; bad_rate: number }[] }>({ items: [] })
const wordFreq = ref<WordFreqResp>({ positive: [], negative: [] })

onMounted(async () => {
  const [d, s, w] = await Promise.all([
    api.ratingDistribution(30), api.sentimentTrend(30), api.wordFrequency(30),
  ])
  dist.value = d
  sentiment.value = s
  wordFreq.value = w
})

const INK = '#898781'
const GRID = '#e1e0d9'
const BASELINE = '#c3c2b7'
const GREEN = '#0ca30c'
const RED = '#d03b3b'

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

function ratingColor(r: number) {
  if (r >= 4) return GREEN
  if (r === 3) return '#eda100'
  return RED
}

const distOption = computed<EChartsOption>(() => ({
  grid: { left: 40, right: 40, top: 16, bottom: 28 },
  tooltip: { trigger: 'axis' },
  xAxis: axisX(dist.value.items.map((i) => `${i.rating} 星`)),
  yAxis: axisY(),
  series: [{
    type: 'bar',
    data: dist.value.items.map((i) => ({ value: i.count, pct: i.pct, itemStyle: { color: ratingColor(i.rating) } })),
    barWidth: 24,
    label: { show: true, position: 'top', color: INK, formatter: (p: any) => `${p.value} 条 (${p.data.pct}%)` },
  }],
}))

const sentimentOption = computed<EChartsOption>(() => ({
  grid: { left: 40, right: 16, top: 28, bottom: 28 },
  tooltip: { trigger: 'axis', valueFormatter: (v) => v + '%' },
  legend: { top: 0, textStyle: { color: INK } },
  xAxis: axisX(sentiment.value.items.map((i) => i.date.slice(5))),
  yAxis: { ...axisY(), max: 100, axisLabel: { color: INK, formatter: '{value}%' } },
  series: [
    { name: '好评率', type: 'line', data: sentiment.value.items.map((i) => i.good_rate), showSymbol: false, lineStyle: { width: 2, color: GREEN }, itemStyle: { color: GREEN } },
    { name: '差评率', type: 'line', data: sentiment.value.items.map((i) => i.bad_rate), showSymbol: false, lineStyle: { width: 2, color: RED }, itemStyle: { color: RED } },
  ],
}))

function wordBarOption(words: WordItem[], color: string): EChartsOption {
  return {
    grid: { left: 8, right: 44, top: 4, bottom: 4, containLabel: true },
    tooltip: { trigger: 'item' },
    xAxis: { type: 'value', show: false },
    yAxis: {
      type: 'category', inverse: true,
      data: words.map((w) => w.word),
      axisLine: { show: false }, axisTick: { show: false },
      axisLabel: { color: '#52514e', fontSize: 13 },
    },
    series: [{
      type: 'bar', data: words.map((w) => w.count),
      barWidth: 14, itemStyle: { color, borderRadius: [0, 4, 4, 0] },
      label: { show: true, position: 'right', color: INK, fontSize: 12 },
    }],
  }
}
const positiveOption = computed(() => wordBarOption(wordFreq.value.positive, GREEN))
const negativeOption = computed(() => wordBarOption(wordFreq.value.negative, RED))
</script>

<template>
  <div>
    <el-button link @click="router.push('/dashboard')" class="back">← 返回看板</el-button>
    <div class="page-title">口碑分析</div>

    <el-card class="block" shadow="never">
      <div class="block-header">
        <span class="block-title">评分分布 · 近 30 天</span>
        <span class="block-sub">平均 {{ dist.avg_rating }} 分 · 共 {{ dist.total }} 条评价</span>
      </div>
      <EChart class="chart-md" :option="distOption" />
    </el-card>

    <el-card class="block" shadow="never">
      <div class="block-header">
        <span class="block-title">好评率 / 差评率趋势 · 近 30 天</span>
      </div>
      <EChart class="chart-md" :option="sentimentOption" />
    </el-card>

    <el-card class="block" shadow="never">
      <div class="block-header">
        <span class="block-title">好评 / 差评高频词</span>
        <el-button link type="primary" size="small" @click="router.push('/reviews')">查看全部评价 →</el-button>
      </div>
      <div class="word-grid">
        <div>
          <div class="sub-title positive">好评高频词</div>
          <EChart class="chart-sm" :option="positiveOption" />
        </div>
        <div>
          <div class="sub-title negative">差评高频词</div>
          <EChart class="chart-sm" :option="negativeOption" />
        </div>
      </div>
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
.chart-md {
  height: 260px;
}
.chart-sm {
  height: 240px;
}
.word-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 24px;
}
.sub-title {
  font-size: 13px;
  margin-bottom: 8px;
}
.sub-title.positive {
  color: var(--status-good);
}
.sub-title.negative {
  color: var(--status-critical);
}
@media (max-width: 900px) {
  .word-grid {
    grid-template-columns: 1fr;
  }
}
</style>
