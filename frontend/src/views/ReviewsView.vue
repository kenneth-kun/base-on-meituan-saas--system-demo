<script setup lang="ts">
import { ElMessage } from 'element-plus'
import { onMounted, ref } from 'vue'

import { api, type ReviewListItem } from '@/api'

const loading = ref(false)
const rows = ref<ReviewListItem[]>([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(20)
const ratingFilter = ref<number | undefined>(undefined)
const replyTab = ref<'all' | 'unreplied' | 'replied'>('unreplied')

const replyDialog = ref(false)
const replyContent = ref('')
const currentReview = ref<ReviewListItem | null>(null)

async function load() {
  loading.value = true
  try {
    const d = await api.listReviews({
      rating: ratingFilter.value,
      replied: replyTab.value === 'all' ? undefined : replyTab.value === 'replied',
      page: page.value,
      page_size: pageSize.value,
    })
    rows.value = d.items
    total.value = d.total
  } finally {
    loading.value = false
  }
}

onMounted(load)

function onFilterChange() {
  page.value = 1
  load()
}
function onTabChange() {
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

function openReply(row: ReviewListItem) {
  currentReview.value = row
  replyContent.value = row.reply || ''
  replyDialog.value = true
}

async function aiDraft(row: ReviewListItem) {
  try {
    const d = await api.aiReviewReply(row.rating, row.content || '')
    currentReview.value = row
    replyContent.value = d.draft
    replyDialog.value = true
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || 'AI 调用失败')
  }
}

async function submitReply() {
  if (!currentReview.value) return
  await api.replyReview(currentReview.value.id, replyContent.value)
  ElMessage.success('已回复')
  replyDialog.value = false
  await load()
}
</script>

<template>
  <div>
    <div class="page-title">评价管理</div>
    <el-card shadow="never">
      <el-tabs v-model="replyTab" @tab-change="onTabChange" class="reply-tabs">
        <el-tab-pane label="未回复" name="unreplied" />
        <el-tab-pane label="已回复" name="replied" />
        <el-tab-pane label="全部" name="all" />
      </el-tabs>
      <div class="toolbar">
        <el-select v-model="ratingFilter" placeholder="全部星级" clearable style="width: 140px" @change="onFilterChange">
          <el-option v-for="n in 5" :key="n" :label="n + ' 星'" :value="n" />
        </el-select>
      </div>

      <el-table :data="rows" v-loading="loading" row-key="id">
        <el-table-column label="星级" width="170">
          <template #default="{ row }">
            <el-rate :model-value="row.rating" disabled />
            <span v-if="row.accurate_star != null" class="star-num">{{ row.accurate_star }} 分</span>
          </template>
        </el-table-column>
        <el-table-column label="消费金额" width="90">
          <template #default="{ row }">
            {{ row.consume_amount ? '¥' + Number(row.consume_amount).toFixed(2) : '—' }}
          </template>
        </el-table-column>
        <el-table-column prop="order_no" label="订单号" width="165" />
        <el-table-column prop="content" label="内容" min-width="220" show-overflow-tooltip />
        <el-table-column prop="tags" label="标签" min-width="120" />
        <el-table-column label="回复" min-width="160" show-overflow-tooltip>
          <template #default="{ row }">
            <span v-if="row.reply">{{ row.reply }}</span>
            <span v-else class="muted">未回复</span>
          </template>
        </el-table-column>
        <el-table-column label="时间" width="150">
          <template #default="{ row }">{{ (row.created_at || '').replace('T', ' ').slice(0, 16) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="150" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" size="small" @click="openReply(row)">回复</el-button>
            <el-button link type="success" size="small" @click="aiDraft(row)">AI 生成</el-button>
          </template>
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

    <el-dialog v-model="replyDialog" title="回复评价" width="460px">
      <el-input v-model="replyContent" type="textarea" :rows="4" placeholder="输入回复内容" />
      <template #footer>
        <el-button @click="replyDialog = false">取消</el-button>
        <el-button type="primary" @click="submitReply">提交</el-button>
      </template>
    </el-dialog>
  </div>
</template>
