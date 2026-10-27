<script setup lang="ts">
import { ElMessage } from 'element-plus'
import { onMounted, ref } from 'vue'

import { api, type AlertListItem } from '@/api'

const loading = ref(false)
const rows = ref<AlertListItem[]>([])

const LEVEL_TAG: Record<string, 'danger' | 'warning' | 'info'> = {
  critical: 'danger',
  warning: 'warning',
  info: 'info',
}

async function load() {
  loading.value = true
  try {
    rows.value = (await api.listAlerts()).items
  } finally {
    loading.value = false
  }
}

onMounted(load)

async function resolve(a: AlertListItem) {
  await api.resolveAlert(a.id)
  ElMessage.success('已标记处理')
  await load()
}
</script>

<template>
  <div>
    <div class="page-title">预警中心</div>
    <el-card shadow="never">
      <el-table :data="rows" v-loading="loading" row-key="id">
        <el-table-column label="规则" width="140">
          <template #default="{ row }">
            <el-tag :type="LEVEL_TAG[row.level]" size="small">{{ row.rule }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="payload" label="详情" min-width="260" />
        <el-table-column label="触发时间" width="180">
          <template #default="{ row }">{{ (row.triggered_at || '').replace('T', ' ').slice(0, 19) }}</template>
        </el-table-column>
        <el-table-column label="状态" width="90">
          <template #default="{ row }">
            <el-tag :type="row.status === 'open' ? 'danger' : 'info'" size="small" effect="plain">
              {{ row.status === 'open' ? '待处理' : '已处理' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="110" fixed="right">
          <template #default="{ row }">
            <el-button v-if="row.status === 'open'" link type="primary" size="small" @click="resolve(row)">
              标记已处理
            </el-button>
          </template>
        </el-table-column>
      </el-table>
      <el-empty v-if="!rows.length && !loading" description="暂无预警" :image-size="60" />
    </el-card>
  </div>
</template>
