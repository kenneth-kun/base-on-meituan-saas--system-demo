<script setup lang="ts">
import { ElMessage } from 'element-plus'
import { onMounted, ref } from 'vue'

import { api, type CategoryItem, type ProductListItem } from '@/api'

const loading = ref(false)
const rows = ref<ProductListItem[]>([])
const categories = ref<CategoryItem[]>([])
const categoryFilter = ref<number | undefined>(undefined)
const statusFilter = ref<string | undefined>(undefined)
const keyword = ref('')
const selection = ref<ProductListItem[]>([])

const priceDialog = ref(false)
const newPrice = ref(10)

async function load() {
  loading.value = true
  try {
    const d = await api.listProducts({
      category_id: categoryFilter.value,
      status: statusFilter.value,
      q: keyword.value || undefined,
    })
    rows.value = d.items
  } finally {
    loading.value = false
  }
}

onMounted(async () => {
  categories.value = (await api.listCategories()).items
  await load()
})

function onSelectionChange(val: ProductListItem[]) {
  selection.value = val
}
function onSearch() {
  load()
}

async function batch(action: string) {
  if (!selection.value.length) {
    ElMessage.warning('请先勾选商品')
    return
  }
  if (action === 'price') {
    priceDialog.value = true
    return
  }
  const d = await api.updateProducts({ ids: selection.value.map((r) => r.id), action })
  ElMessage.success(`已${action === 'on' ? '上架' : '下架'} ${d.updated} 件`)
  selection.value = []
  await load()
}

async function submitPrice() {
  const d = await api.updateProducts({
    ids: selection.value.map((r) => r.id),
    action: 'price',
    price: newPrice.value,
  })
  ElMessage.success(`已改价 ${d.updated} 件`)
  priceDialog.value = false
  selection.value = []
  await load()
}
</script>

<template>
  <div>
    <div class="page-title">商品管理</div>
    <el-card shadow="never">
      <div class="toolbar">
        <el-select v-model="categoryFilter" placeholder="全部分类" clearable style="width: 140px" @change="load">
          <el-option v-for="c in categories" :key="c.id" :label="c.name" :value="c.id" />
        </el-select>
        <el-select v-model="statusFilter" placeholder="全部状态" clearable style="width: 120px" @change="load">
          <el-option label="上架中" value="on" />
          <el-option label="已下架" value="off" />
        </el-select>
        <el-input
          v-model="keyword"
          placeholder="搜索商品名"
          clearable
          style="width: 180px"
          @keyup.enter="onSearch"
          @clear="onSearch"
        />
        <el-button @click="onSearch">搜索</el-button>
        <div class="spacer" />
        <el-button :disabled="!selection.length" @click="batch('on')">批量上架</el-button>
        <el-button :disabled="!selection.length" @click="batch('off')">批量下架</el-button>
        <el-button type="primary" :disabled="!selection.length" @click="batch('price')">批量改价</el-button>
      </div>

      <el-table :data="rows" v-loading="loading" row-key="id" @selection-change="onSelectionChange">
        <el-table-column type="selection" width="44" />
        <el-table-column prop="name" label="商品名" min-width="140" />
        <el-table-column prop="app_food_code" label="编码" width="90" />
        <el-table-column prop="category" label="分类" width="100" />
        <el-table-column label="价格" width="90">
          <template #default="{ row }">¥{{ Number(row.price).toFixed(2) }}</template>
        </el-table-column>
        <el-table-column label="库存" width="90">
          <template #default="{ row }">
            <span :class="{ 'sold-out': row.stock === 0 }">{{ row.stock }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="sales" label="销量" width="90" />
        <el-table-column label="状态" width="90">
          <template #default="{ row }">
            <el-tag :type="row.status === 'on' ? 'success' : 'info'" size="small">
              {{ row.status === 'on' ? '上架中' : '已下架' }}
            </el-tag>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-dialog v-model="priceDialog" title="批量改价" width="360px">
      <div class="price-row">
        <span>新价格（元）</span>
        <el-input-number v-model="newPrice" :min="0.1" :step="0.5" :precision="1" />
      </div>
      <template #footer>
        <el-button @click="priceDialog = false">取消</el-button>
        <el-button type="primary" @click="submitPrice">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.sold-out {
  color: var(--status-critical);
  font-weight: 600;
}
.price-row {
  display: flex;
  align-items: center;
  gap: 16px;
}
</style>
