<script setup lang="ts">
import type { EChartsOption } from 'echarts'
import { ElMessage } from 'element-plus'
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'

import {
  api,
  type AlertsResp,
  type KpiSummary,
  type ProductsResp,
  type RatingItem,
  type TrendResp,
  type WordItem,
  type WordFreqResp,
} from '@/api'
import EChart from '@/components/EChart.vue'
import KpiCard from '@/components/KpiCard.vue'

const router = useRouter()

const loading = ref(true)
const summary = ref<KpiSummary | null>(null)
const trend = ref<TrendResp>({ days: 30, items: [] })
const products = ref<ProductsResp>({ hot: [], slow: [], sold_out: [] })
const alerts = ref<AlertsResp>({ items: [] })
const ratingTrend = ref<{ items: RatingItem[] }>({ items: [] })
const wordFreq = ref<WordFreqResp>({ positive: [], negative: [] })

const trendMetric = ref<'revenue' | 'order_count'>('revenue')

async function loadDashboard() {
  loading.value = true
  try {
    const [s, t, p, a, rt, wf] = await Promise.all([
      api.summary(),
      api.trend(30),
      api.products(),
      api.alerts(),
      api.ratingTrend(30),
      api.wordFrequency(30),
    ])
    summary.value = s
    trend.value = t
    products.value = p
    alerts.value = a
    ratingTrend.value = rt
    wordFreq.value = wf
  } finally {
    loading.value = false
  }
}

// 数据刷新
const lastRefresh = ref<string | null>(null)
const refreshing = ref(false)
const lastRefreshText = computed(() =>
  lastRefresh.value ? lastRefresh.value.replace('T', ' ').slice(0, 16) : '—',
)

async function loadRefreshStatus() {
  try {
    lastRefresh.value = (await api.refreshStatus()).last_refresh_at
  } catch { /* 忽略 */ }
}
async function manualRefresh() {
  refreshing.value = true
  try {
    const r = await api.refreshData()
    lastRefresh.value = r.last_refresh_at
    await loadDashboard()
    ElMessage.success(`已刷新：新增 ${r.orders} 单、${r.reviews} 条评价`)
  } catch {
    ElMessage.error('刷新失败')
  } finally {
    refreshing.value = false
  }
}

onMounted(() => {
  loadDashboard()
  loadRefreshStatus()
})

// 紧急客服消息轮询（首页实时提醒 + 声音提示）
const urgentItems = ref<any[]>([])
let urgentTimer: ReturnType<typeof setInterval> | null = null
let lastUrgentCount = -1
let audioCtx: any = null

function playAlertSound() {
  try {
    const Ctx = window.AudioContext || (window as any).webkitAudioContext
    if (!Ctx) return
    if (!audioCtx) audioCtx = new Ctx()
    if (audioCtx.state === 'suspended') audioCtx.resume()
    const now = audioCtx.currentTime
    const beep = (freq: number, start: number, duration = 0.15) => {
      const osc = audioCtx.createOscillator()
      const gain = audioCtx.createGain()
      osc.type = 'sine'
      osc.frequency.value = freq
      gain.gain.setValueAtTime(0.001, start)
      gain.gain.exponentialRampToValueAtTime(0.3, start + 0.02)
      gain.gain.exponentialRampToValueAtTime(0.001, start + duration)
      osc.connect(gain)
      gain.connect(audioCtx.destination)
      osc.start(start)
      osc.stop(start + duration)
    }
    beep(880, now)          // 两声「叮咚」
    beep(660, now + 0.18)
  } catch {
    /* 忽略（浏览器自动播放限制等） */
  }
}

async function loadUrgent() {
  try {
    const items = (await api.urgentMessages()).items
    urgentItems.value = items
    // 数量增加（出现新紧急消息）→ 播放提示音；首次加载不响
    if (lastUrgentCount >= 0 && items.length > lastUrgentCount) {
      playAlertSound()
    }
    lastUrgentCount = items.length
  } catch {
    /* 忽略轮询错误 */
  }
}
onMounted(() => {
  loadUrgent()
  urgentTimer = setInterval(loadUrgent, 20000)
})
onBeforeUnmount(() => {
  if (urgentTimer) clearInterval(urgentTimer)
})

// ---------- 格式化 ----------
function money(v?: string | number | null): string {
  if (v === null || v === undefined || v === '') return '—'
  const n = Number(v)
  if (Number.isNaN(n)) return '—'
  return '¥' + n.toLocaleString('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}
function pct(v?: string | number | null): string {
  if (v === null || v === undefined || v === '') return '—'
  const n = Number(v)
  return Number.isNaN(n) ? '—' : n.toFixed(2) + '%'
}
function num(v?: string | number | null): number | null {
  if (v === null || v === undefined || v === '') return null
  const n = Number(v)
  return Number.isNaN(n) ? null : n
}

// ---------- 图表配置（遵循 dataviz：单轴、细标记、隐性网格） ----------
const INK = '#898781'
const GRID = '#e1e0d9'
const BASELINE = '#c3c2b7'
const BLUE = '#2a78d6'
const POS_COLOR = '#0ca30c'
const NEG_COLOR = '#d03b3b'

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
  const isRevenue = trendMetric.value === 'revenue'
  const data = trend.value.items.map((i) => (isRevenue ? Number(i.revenue) : i.order_count))
  return {
    grid: { left: 56, right: 16, top: 24, bottom: 32 },
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'cross' },
      valueFormatter: (v) => (isRevenue ? '¥' + Number(v).toLocaleString('zh-CN', { minimumFractionDigits: 2 }) : String(v)),
    },
    xAxis: axisX(trend.value.items.map((i) => i.date.slice(5))),
    yAxis: axisY(),
    series: [
      {
        name: isRevenue ? '营收' : '订单量',
        type: 'line',
        data,
        showSymbol: false,
        lineStyle: { width: 2, color: BLUE },
        itemStyle: { color: BLUE },
        areaStyle: { color: 'rgba(42,120,214,0.10)' },
      },
    ],
  }
})

const ratingOption = computed<EChartsOption>(() => ({
  grid: { left: 40, right: 16, top: 24, bottom: 32 },
  tooltip: { trigger: 'axis' },
  xAxis: axisX(ratingTrend.value.items.map((i) => i.date.slice(5))),
  yAxis: { ...axisY(), min: 0, max: 5 },
  series: [
    {
      name: '综合评分',
      type: 'line',
      data: ratingTrend.value.items.map((i) => i.avg_rating),
      showSymbol: false,
      lineStyle: { width: 2, color: BLUE },
      itemStyle: { color: BLUE },
      areaStyle: { color: 'rgba(42,120,214,0.10)' },
    },
  ],
}))

function wordBarOption(words: WordItem[], color: string): EChartsOption {
  return {
    grid: { left: 8, right: 44, top: 4, bottom: 4, containLabel: true },
    tooltip: { trigger: 'item' },
    xAxis: { type: 'value', show: false },
    yAxis: {
      type: 'category',
      inverse: true,
      data: words.map((w) => w.word),
      axisLine: { show: false },
      axisTick: { show: false },
      axisLabel: { color: '#52514e', fontSize: 13 },
    },
    series: [
      {
        type: 'bar',
        data: words.map((w) => w.count),
        barWidth: 14,
        itemStyle: { color, borderRadius: [0, 4, 4, 0] },
        label: { show: true, position: 'right', color: INK, fontSize: 12 },
      },
    ],
  }
}

const positiveWordsOption = computed(() => wordBarOption(wordFreq.value.positive, POS_COLOR))
const negativeWordsOption = computed(() => wordBarOption(wordFreq.value.negative, NEG_COLOR))

// ---------- 预警 ----------
const LEVEL_TAG: Record<string, 'danger' | 'warning' | 'info'> = {
  critical: 'danger',
  warning: 'warning',
  info: 'info',
}
function levelTag(level: string) {
  return LEVEL_TAG[level] ?? 'info'
}
function alertPath(rule: string): string {
  if (rule.includes('差评') || rule.includes('评分')) return '/reviews'
  if (rule.includes('售罄') || rule.includes('商品')) return '/products'
  return '/orders'
}
function alertIcon(rule: string): string {
  if (rule.includes('差评') || rule.includes('评分')) return '差评'
  if (rule.includes('售罄')) return '售罄'
  return '订单'
}
</script>

<template>
  <div class="dashboard" v-loading="loading">
    <header class="page-header">
      <h1>经营看板</h1>
      <span class="header-meta">早开店扫一眼，看懂今天生意</span>
      <div class="spacer" />
      <span class="header-meta">上次刷新：{{ lastRefreshText }}</span>
      <el-button size="small" :loading="refreshing" @click="manualRefresh">刷新数据</el-button>
    </header>

    <!-- 紧急客服提醒 -->
    <div v-if="urgentItems.length" class="urgent-banner">
      <span class="urgent-dot">●</span>
      <span class="urgent-text">有 {{ urgentItems.length }} 条紧急客服消息待处理（食品安全 / 投诉 / 售后）</span>
      <el-button type="danger" size="small" @click="router.push('/service')">立即处理 →</el-button>
    </div>

    <!-- 1. 今日概况 -->
    <section class="kpi-row">
      <KpiCard label="今日营收" :value="money(summary?.revenue)" :delta="num(summary?.revenue_change_pct)" />
      <KpiCard label="今日订单" :value="summary ? String(summary.order_count) : '—'" :delta="num(summary?.order_count_change_pct)" />
      <KpiCard label="客单价" :value="money(summary?.avg_order_value)" :delta="num(summary?.avg_order_value_change_pct)" />
      <KpiCard label="有效订单率" :value="pct(summary?.valid_rate)" />
    </section>

    <!-- 2. 经营趋势 -->
    <el-card class="block" shadow="never">
      <div class="block-header">
        <span class="block-title">经营趋势 · 近 30 天</span>
        <div class="block-header-right">
          <el-radio-group v-model="trendMetric" size="small">
            <el-radio-button value="revenue">营收</el-radio-button>
            <el-radio-button value="order_count">订单量</el-radio-button>
          </el-radio-group>
          <el-button link type="primary" size="small" @click="router.push('/analytics/trend')">查看详情 →</el-button>
        </div>
      </div>
      <EChart class="chart-lg" :option="trendOption" />
    </el-card>

    <!-- 3 + 4. 商品榜 + 待办预警 -->
    <div class="two-col">
      <el-card class="block" shadow="never">
        <div class="block-header">
          <span class="block-title">商品榜</span>
          <el-button link type="primary" size="small" @click="router.push('/products')">查看全部商品 →</el-button>
        </div>
        <div class="rank-grid">
          <div>
            <div class="sub-title">热销 TOP10</div>
            <ol class="rank-list">
              <li v-for="(p, i) in products.hot" :key="p.id">
                <span class="rank-no">{{ i + 1 }}</span>
                <span class="rank-name">{{ p.name }}</span>
                <span class="rank-meta">{{ p.sales }} 单</span>
              </li>
            </ol>
          </div>
          <div>
            <div class="sub-title">滞销 TOP10</div>
            <ol class="rank-list">
              <li v-for="(p, i) in products.slow" :key="p.id">
                <span class="rank-no muted">{{ i + 1 }}</span>
                <span class="rank-name">{{ p.name }}</span>
                <span class="rank-meta">{{ p.sales }} 单</span>
              </li>
            </ol>
          </div>
        </div>
        <div v-if="products.sold_out.length" class="sold-out">
          <span class="sold-out-label">售罄待补货：</span>
          <el-tag v-for="p in products.sold_out" :key="p.id" type="danger" size="small" effect="plain">
            {{ p.name }}
          </el-tag>
        </div>
      </el-card>

      <el-card class="block" shadow="never">
        <div class="block-header">
          <span class="block-title">待办 / 预警</span>
          <el-button link type="primary" size="small" @click="router.push('/alerts')">查看全部预警 →</el-button>
        </div>
        <ul v-if="alerts.items.length" class="alert-list">
          <li v-for="a in alerts.items" :key="a.id" class="alert-item">
            <el-tag :type="levelTag(a.level)" size="small">{{ a.rule }}</el-tag>
            <span class="alert-payload">{{ a.payload || '—' }}</span>
            <el-button link type="primary" size="small" @click="router.push(alertPath(a.rule))">去处理</el-button>
          </li>
        </ul>
        <el-empty v-else description="暂无预警" :image-size="60" />
      </el-card>
    </div>

    <!-- 5. 口碑洞察 -->
    <el-card class="block" shadow="never">
      <div class="block-header">
        <span class="block-title">口碑洞察 · 近 30 天</span>
        <div class="block-header-right">
          <span class="block-sub">好评要守住 / 差评要改进</span>
          <el-button link type="primary" size="small" @click="router.push('/analytics/reputation')">查看详情 →</el-button>
        </div>
      </div>
      <div class="reputation-grid">
        <div class="rep-panel">
          <div class="sub-title">综合评分趋势</div>
          <EChart class="chart-md" :option="ratingOption" />
        </div>
        <div class="rep-panel">
          <div class="sub-title positive">好评高频词</div>
          <EChart class="chart-md" :option="positiveWordsOption" />
        </div>
        <div class="rep-panel">
          <div class="sub-title negative">差评高频词</div>
          <EChart class="chart-md" :option="negativeWordsOption" />
        </div>
      </div>
    </el-card>
  </div>
</template>

<style scoped>
.dashboard {
  padding-bottom: 24px;
}
.urgent-banner {
  display: flex;
  align-items: center;
  gap: 10px;
  background: #fdecec;
  border: 1px solid var(--status-critical);
  border-radius: 8px;
  padding: 10px 16px;
  margin-bottom: 16px;
}
.urgent-dot {
  color: var(--status-critical);
  font-size: 16px;
  animation: urgent-pulse 1.2s infinite;
}
.urgent-text {
  flex: 1;
  color: #b32424;
  font-weight: 600;
  font-size: 14px;
}
@keyframes urgent-pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.25; }
}
.page-header {
  display: flex;
  align-items: baseline;
  gap: 12px;
  margin-bottom: 20px;
}
.page-header h1 {
  font-size: 22px;
  margin: 0;
}
.header-meta {
  color: var(--text-muted);
  font-size: 13px;
}

.kpi-row {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  margin-bottom: 16px;
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
.block-header-right {
  display: flex;
  align-items: center;
  gap: 12px;
}

.chart-lg {
  height: 320px;
}
.chart-md {
  height: 240px;
}

.two-col {
  display: grid;
  grid-template-columns: 1.4fr 1fr;
  gap: 16px;
}

.rank-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 24px;
}
.sub-title {
  font-size: 13px;
  color: var(--text-secondary);
  margin-bottom: 8px;
}
.sub-title.positive { color: var(--status-good); }
.sub-title.negative { color: var(--status-critical); }

.rank-list {
  list-style: none;
  margin: 0;
  padding: 0;
}
.rank-list li {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 5px 0;
  font-size: 13px;
  border-bottom: 1px solid var(--gridline);
}
.rank-list li:last-child { border-bottom: none; }
.rank-no {
  width: 18px;
  color: var(--series-orange);
  font-weight: 600;
}
.rank-no.muted { color: var(--text-muted); }
.rank-name { flex: 1; }
.rank-meta { color: var(--text-muted); }

.sold-out {
  margin-top: 12px;
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 6px;
}
.sold-out-label {
  font-size: 13px;
  color: var(--status-critical);
  font-weight: 600;
}

.alert-list {
  list-style: none;
  margin: 0;
  padding: 0;
}
.alert-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 0;
  border-bottom: 1px solid var(--gridline);
}
.alert-item:last-child { border-bottom: none; }
.alert-payload {
  flex: 1;
  font-size: 13px;
  color: var(--text-secondary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.reputation-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 24px;
}

@media (max-width: 900px) {
  .kpi-row { grid-template-columns: repeat(2, 1fr); }
  .two-col { grid-template-columns: 1fr; }
  .reputation-grid { grid-template-columns: 1fr; }
}
</style>
