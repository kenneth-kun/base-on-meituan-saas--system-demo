<script setup lang="ts">
import { ElMessage } from 'element-plus'
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'

import { api, type OrderListItem } from '@/api'

const router = useRouter()

const loading = ref(false)
const rows = ref<OrderListItem[]>([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(20)
const statusFilter = ref<string | undefined>(undefined)
const statuses = ref<{ value: string; label: string }[]>([])
const selection = ref<OrderListItem[]>([])

const detailVisible = ref(false)
const detailData = ref<any>(null)

const STATUS_TYPE: Record<string, 'warning' | 'primary' | 'success' | 'info' | 'danger'> = {
  pending: 'warning',
  confirmed: 'primary',
  delivering: 'primary',
  completed: 'success',
  cancelled: 'info',
  refunding: 'danger',
}

async function load() {
  loading.value = true
  try {
    const d = await api.listOrders({ status: statusFilter.value, page: page.value, page_size: pageSize.value })
    rows.value = d.items
    total.value = d.total
    statuses.value = d.statuses
  } finally {
    loading.value = false
  }
}

onMounted(load)

function onSelectionChange(val: OrderListItem[]) {
  selection.value = val
}
function onStatusChange() {
  page.value = 1
  load()
}
function onPageChange() {
  load()
}
function onSizeChange() {
  page.value = 1
  load()
}

async function confirmOrders() {
  if (!selection.value.length) {
    ElMessage.warning('请先勾选订单')
    return
  }
  const d = await api.confirmOrders(selection.value.map((r) => r.id))
  ElMessage.success(`已接单 ${d.updated} 笔`)
  selection.value = []
  await load()
}

function openDetail(row: OrderListItem) {
  detailData.value = null
  detailVisible.value = true
  api.getOrder(row.id).then((d) => {
    detailData.value = d
  })
}

function ratingBadge(r: number | null) {
  if (r === null || r === undefined) return { text: '—', type: 'info' as const }
  if (r >= 4) return { text: `${r} 星`, type: 'success' as const }
  if (r === 3) return { text: `${r} 星`, type: 'warning' as const }
  return { text: `${r} 星`, type: 'danger' as const }
}

function goReviews() {
  detailVisible.value = false
  router.push('/reviews')
}
</script>

<template>
  <div>
    <div class="page-title">订单管理</div>
    <el-card shadow="never">
      <div class="toolbar">
        <el-select v-model="statusFilter" placeholder="全部状态" clearable style="width: 160px" @change="onStatusChange">
          <el-option v-for="s in statuses" :key="s.value" :label="s.label" :value="s.value" />
        </el-select>
        <div class="spacer" />
        <el-button type="primary" :disabled="!selection.length" @click="confirmOrders">一键接单</el-button>
      </div>

      <el-table :data="rows" v-loading="loading" row-key="id" @selection-change="onSelectionChange">
        <el-table-column type="selection" width="44" />
        <el-table-column label="订单号" min-width="170">
          <template #default="{ row }">
            <el-link type="primary" @click="openDetail(row)">{{ row.order_no }}</el-link>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="90">
          <template #default="{ row }">
            <el-tag :type="STATUS_TYPE[row.status]" size="small">{{ row.status_label }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="金额" width="110">
          <template #default="{ row }">¥{{ Number(row.total_amount).toFixed(2) }}</template>
        </el-table-column>
        <el-table-column prop="item_count" label="商品数" width="80" />
        <el-table-column label="评价" width="80">
          <template #default="{ row }">
            <el-tag v-if="row.review_rating != null" :type="ratingBadge(row.review_rating).type" size="small">
              {{ ratingBadge(row.review_rating).text }}
            </el-tag>
            <span v-else class="muted">—</span>
          </template>
        </el-table-column>
        <el-table-column label="下单时间" min-width="170">
          <template #default="{ row }">{{ row.placed_at.replace('T', ' ').slice(0, 19) }}</template>
        </el-table-column>
      </el-table>

      <div class="pager">
        <el-pagination
          v-model:current-page="page"
          v-model:page-size="pageSize"
          :total="total"
          layout="total, prev, pager, next, sizes"
          :page-sizes="[10, 20, 50]"
          @current-change="onPageChange"
          @size-change="onSizeChange"
        />
      </div>
    </el-card>

    <!-- 订单详情抽屉 -->
    <el-drawer v-model="detailVisible" title="订单详情" size="460px">
      <div v-if="detailData" class="detail" v-loading="!detailData">
        <div class="detail-row"><span class="dl">订单号</span><b>{{ detailData.order_no }}</b></div>
        <div class="detail-row"><span class="dl">美团单号</span>{{ detailData.wm_order_id_view }}</div>
        <div class="detail-row">
          <span class="dl">状态</span>
          <el-tag :type="STATUS_TYPE[detailData.status]" size="small">{{ detailData.status_label }}</el-tag>
        </div>
        <div class="detail-row"><span class="dl">下单时间</span>{{ detailData.placed_at.replace('T', ' ').slice(0, 19) }}</div>

        <div class="divider" />
        <div class="section-title">收货人信息</div>
        <div class="detail-row"><span class="dl">收货人</span>{{ detailData.recipient_name }}</div>
        <div class="detail-row"><span class="dl">电话</span>{{ detailData.recipient_phone }}</div>
        <div class="detail-row"><span class="dl">地址</span>{{ detailData.recipient_address }}</div>

        <div class="divider" />
        <div class="section-title">金额明细</div>
        <div class="detail-row"><span class="dl">原价</span>¥{{ Number(detailData.original_price).toFixed(2) }}</div>
        <div class="detail-row"><span class="dl">订单金额</span><b>¥{{ Number(detailData.total_amount).toFixed(2) }}</b></div>
        <div class="detail-row"><span class="dl">平台佣金</span>-¥{{ Number(detailData.commission).toFixed(2) }}</div>
        <div class="detail-row"><span class="dl">活动补贴</span>-¥{{ Number(detailData.subsidy).toFixed(2) }}</div>
        <div class="detail-row"><span class="dl">配送费</span>¥{{ Number(detailData.delivery_fee).toFixed(2) }}</div>

        <div class="divider" />
        <div class="section-title">商品明细</div>
        <table class="items-table">
          <thead>
            <tr><th>商品</th><th class="c">数量</th><th class="r">小计</th></tr>
          </thead>
          <tbody>
            <tr v-for="(it, i) in detailData.items" :key="i">
              <td>{{ it.product_name }}</td>
              <td class="c">×{{ it.qty }}</td>
              <td class="r">¥{{ Number(it.subtotal).toFixed(2) }}</td>
            </tr>
          </tbody>
        </table>

        <div class="divider" />
        <div class="section-title">关联评价</div>
        <div v-if="detailData.review" class="review-box">
          <el-rate :model-value="detailData.review.rating" disabled />
          <div class="review-content">{{ detailData.review.content }}</div>
          <div class="review-tags" v-if="detailData.review.tags">{{ detailData.review.tags }}</div>
          <div v-if="detailData.review.reply" class="review-reply">商家回复：{{ detailData.review.reply }}</div>
          <div v-else class="muted">未回复</div>
          <el-button link type="primary" size="small" @click="goReviews">在评价管理中查看</el-button>
        </div>
        <el-empty v-else description="该订单暂无评价" :image-size="50" />
      </div>
    </el-drawer>
  </div>
</template>

<style scoped>
.detail {
  padding: 0 4px;
}
.detail-row {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  padding: 5px 0;
}
.dl {
  color: var(--text-muted);
  width: 70px;
  flex-shrink: 0;
}
.divider {
  height: 1px;
  background: var(--gridline);
  margin: 12px 0;
}
.section-title {
  font-size: 14px;
  font-weight: 600;
  margin-bottom: 6px;
}
.items-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
}
.items-table th,
.items-table td {
  text-align: left;
  padding: 6px 4px;
  border-bottom: 1px solid var(--gridline);
}
.items-table th {
  color: var(--text-muted);
  font-weight: 500;
}
.items-table .c {
  text-align: center;
  width: 60px;
}
.items-table .r {
  text-align: right;
  width: 90px;
}
.review-box {
  padding: 8px;
  background: var(--page-plane);
  border-radius: 8px;
}
.review-content {
  margin: 6px 0;
  font-size: 14px;
}
.review-tags {
  color: var(--text-muted);
  font-size: 12px;
  margin-bottom: 6px;
}
.review-reply {
  color: var(--text-secondary);
  font-size: 13px;
  margin-bottom: 6px;
}
</style>
