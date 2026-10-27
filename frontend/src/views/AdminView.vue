<script setup lang="ts">
import { ElMessage, ElMessageBox } from 'element-plus'
import { onMounted, ref } from 'vue'

import { api } from '@/api'

const FEATURE_LABEL: Record<string, string> = {
  dashboard: '经营看板', orders: '订单管理', products: '商品管理',
  reviews: '评价管理', alerts: '预警中心', service: '客服工作台', settings: '设置',
}

// ---------- 套餐 ----------
const plans = ref<any[]>([])
const features = ref<any[]>([])
const planDialog = ref(false)
const editingPlanId = ref<number | null>(null)
const planForm = ref<any>({ name: '', price: 0, features: [], quotas: { ai_calls_monthly: 0 }, description: '' })

// ---------- 商家 ----------
const merchants = ref<any[]>([])
const merchantDialog = ref(false)
const merchantForm = ref<any>({ name: '', phone: '', username: '', password: '', plan_id: null, expired_at: '' })

// ---------- 订阅 ----------
const subscriptions = ref<any[]>([])
const subDialog = ref(false)
const subForm = ref<any>({ merchant_id: null, plan_id: null, expired_at: '' })

async function loadPlans() {
  plans.value = (await api.listPlans()).items
}
async function loadMerchants() {
  merchants.value = (await api.listMerchants()).items
}
async function loadSubscriptions() {
  subscriptions.value = (await api.listSubscriptions()).items
}

onMounted(async () => {
  features.value = (await api.listFeatures()).items
  await Promise.all([loadPlans(), loadMerchants(), loadSubscriptions()])
})

function featureNames(codes: string[]) {
  return (codes || []).map((c) => FEATURE_LABEL[c] || c).join('、')
}

// 套餐 CRUD
function openPlanCreate() {
  editingPlanId.value = null
  planForm.value = { name: '', price: 0, features: [], quotas: { ai_calls_monthly: 0 }, description: '' }
  planDialog.value = true
}
function openPlanEdit(p: any) {
  editingPlanId.value = p.id
  planForm.value = { name: p.name, price: Number(p.price), features: [...p.features], quotas: { ...p.quotas }, description: p.description }
  planDialog.value = true
}
async function savePlan() {
  if (editingPlanId.value) {
    await api.updatePlan(editingPlanId.value, planForm.value)
  } else {
    await api.createPlan(planForm.value)
  }
  planDialog.value = false
  ElMessage.success('已保存')
  await loadPlans()
}
async function deletePlan(p: any) {
  await ElMessageBox.confirm(`确定删除套餐「${p.name}」？`, '提示', { type: 'warning' })
  await api.deletePlan(p.id)
  ElMessage.success('已删除')
  await loadPlans()
}

// 商家
function openMerchantCreate() {
  merchantForm.value = { name: '', phone: '', username: '', password: '', plan_id: null, expired_at: '' }
  merchantDialog.value = true
}
async function saveMerchant() {
  await api.createMerchant(merchantForm.value)
  merchantDialog.value = false
  ElMessage.success('已创建')
  await loadMerchants()
}
async function toggleMerchant(m: any) {
  const next = m.user_status === 'disabled' ? 'active' : 'disabled'
  await api.setMerchantStatus(m.id, next)
  ElMessage.success(next === 'active' ? '已启用' : '已禁用')
  await loadMerchants()
}

// 订阅
function openSubAssign() {
  subForm.value = { merchant_id: null, plan_id: null, expired_at: '' }
  subDialog.value = true
}
async function saveSub() {
  await api.assignSubscription(subForm.value)
  subDialog.value = false
  ElMessage.success('已分配套餐')
  await Promise.all([loadSubscriptions(), loadMerchants()])
}
</script>

<template>
  <div>
    <div class="page-title">管理后台</div>
    <el-tabs type="border-card">
      <!-- 套餐 -->
      <el-tab-pane label="套餐管理">
        <div class="toolbar">
          <div class="spacer" />
          <el-button type="primary" @click="openPlanCreate">新建套餐</el-button>
        </div>
        <el-table :data="plans" row-key="id">
          <el-table-column prop="name" label="套餐名" width="120" />
          <el-table-column label="价格" width="90">
            <template #default="{ row }">¥{{ Number(row.price).toFixed(2) }}</template>
          </el-table-column>
          <el-table-column label="功能" min-width="200">
            <template #default="{ row }">{{ featureNames(row.features) }}</template>
          </el-table-column>
          <el-table-column label="AI 配额/月" width="110">
            <template #default="{ row }">{{ row.quotas?.ai_calls_monthly ?? 0 }} 次</template>
          </el-table-column>
          <el-table-column prop="description" label="说明" min-width="140" />
          <el-table-column label="操作" width="130" fixed="right">
            <template #default="{ row }">
              <el-button link type="primary" size="small" @click="openPlanEdit(row)">编辑</el-button>
              <el-button link type="danger" size="small" @click="deletePlan(row)">删除</el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-tab-pane>

      <!-- 商家 -->
      <el-tab-pane label="商家管理">
        <div class="toolbar">
          <div class="spacer" />
          <el-button type="primary" @click="openMerchantCreate">新建商家</el-button>
        </div>
        <el-table :data="merchants" row-key="id">
          <el-table-column prop="name" label="商家名" min-width="120" />
          <el-table-column prop="phone" label="电话" width="130" />
          <el-table-column prop="plan_name" label="套餐" width="100" />
          <el-table-column label="到期" width="110">
            <template #default="{ row }">{{ row.expired_at || '—' }}</template>
          </el-table-column>
          <el-table-column prop="username" label="账号" width="110" />
          <el-table-column label="状态" width="90">
            <template #default="{ row }">
              <el-tag :type="row.user_status === 'active' ? 'success' : 'info'" size="small">
                {{ row.user_status === 'active' ? '正常' : '已禁用' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="90" fixed="right">
            <template #default="{ row }">
              <el-button link :type="row.user_status === 'active' ? 'danger' : 'success'" size="small" @click="toggleMerchant(row)">
                {{ row.user_status === 'active' ? '禁用' : '启用' }}
              </el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-tab-pane>

      <!-- 订阅 -->
      <el-tab-pane label="订阅管理">
        <div class="toolbar">
          <div class="spacer" />
          <el-button type="primary" @click="openSubAssign">分配套餐</el-button>
        </div>
        <el-table :data="subscriptions" row-key="id">
          <el-table-column prop="merchant_name" label="商家" min-width="120" />
          <el-table-column prop="plan_name" label="套餐" width="120" />
          <el-table-column prop="started_at" label="开始" width="110" />
          <el-table-column prop="expired_at" label="到期" width="110" />
          <el-table-column prop="status" label="状态" width="90" />
        </el-table>
      </el-tab-pane>
    </el-tabs>

    <!-- 套餐编辑弹窗 -->
    <el-dialog v-model="planDialog" :title="editingPlanId ? '编辑套餐' : '新建套餐'" width="480px">
      <el-form label-width="90px">
        <el-form-item label="套餐名">
          <el-input v-model="planForm.name" />
        </el-form-item>
        <el-form-item label="价格(元)">
          <el-input-number v-model="planForm.price" :min="0" :precision="2" :step="10" />
        </el-form-item>
        <el-form-item label="功能模块">
          <el-checkbox-group v-model="planForm.features">
            <el-checkbox v-for="f in features" :key="f.code" :value="f.code">{{ f.name }}</el-checkbox>
          </el-checkbox-group>
        </el-form-item>
        <el-form-item label="AI 配额/月">
          <el-input-number v-model="planForm.quotas.ai_calls_monthly" :min="0" :step="100" />
        </el-form-item>
        <el-form-item label="说明">
          <el-input v-model="planForm.description" type="textarea" :rows="2" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="planDialog = false">取消</el-button>
        <el-button type="primary" @click="savePlan">保存</el-button>
      </template>
    </el-dialog>

    <!-- 新建商家弹窗 -->
    <el-dialog v-model="merchantDialog" title="新建商家" width="480px">
      <el-form label-width="90px">
        <el-form-item label="商家名">
          <el-input v-model="merchantForm.name" />
        </el-form-item>
        <el-form-item label="电话">
          <el-input v-model="merchantForm.phone" />
        </el-form-item>
        <el-form-item label="登录账号">
          <el-input v-model="merchantForm.username" />
        </el-form-item>
        <el-form-item label="密码">
          <el-input v-model="merchantForm.password" show-password />
        </el-form-item>
        <el-form-item label="套餐">
          <el-select v-model="merchantForm.plan_id" placeholder="选择套餐" style="width: 100%">
            <el-option v-for="p in plans" :key="p.id" :label="p.name" :value="p.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="到期日">
          <el-date-picker v-model="merchantForm.expired_at" type="date" value-format="YYYY-MM-DD" style="width: 100%" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="merchantDialog = false">取消</el-button>
        <el-button type="primary" @click="saveMerchant">创建</el-button>
      </template>
    </el-dialog>

    <!-- 分配套餐弹窗 -->
    <el-dialog v-model="subDialog" title="分配套餐" width="420px">
      <el-form label-width="80px">
        <el-form-item label="商家">
          <el-select v-model="subForm.merchant_id" placeholder="选择商家" style="width: 100%">
            <el-option v-for="m in merchants" :key="m.id" :label="m.name" :value="m.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="套餐">
          <el-select v-model="subForm.plan_id" placeholder="选择套餐" style="width: 100%">
            <el-option v-for="p in plans" :key="p.id" :label="p.name" :value="p.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="到期日">
          <el-date-picker v-model="subForm.expired_at" type="date" value-format="YYYY-MM-DD" style="width: 100%" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="subDialog = false">取消</el-button>
        <el-button type="primary" @click="saveSub">分配</el-button>
      </template>
    </el-dialog>
  </div>
</template>
