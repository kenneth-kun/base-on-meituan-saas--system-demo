<script setup lang="ts">
import { ElMessage, ElMessageBox } from 'element-plus'
import { onMounted, ref } from 'vue'

import { api } from '@/api'

// 门店信息
const storeForm = ref({ name: '', address: '', phone: '', business_hours: '' })

// AI/预警/通知设置
const settingsForm = ref<any>({
  ai_auto_send: true, ai_threshold: 0.85,
  order_drop_ratio: 0.7, bad_review_count: 3, rating_min: 4.2, sound_enabled: true,
})

// FAQ
const faqs = ref<any[]>([])
const faqDialog = ref(false)
const editingFaqId = ref<number | null>(null)
const faqForm = ref({ question: '', answer: '', keywords: '' })

// 密码
const pwdForm = ref({ old_password: '', new_password: '' })

async function load() {
  const d = await api.getSettings()
  storeForm.value = {
    name: d.store.name, address: d.store.address || '',
    phone: d.store.phone || '', business_hours: d.store.business_hours || '',
  }
  settingsForm.value = d.settings
  faqs.value = d.faqs
}
onMounted(load)

async function saveStore() {
  await api.updateStore(storeForm.value)
  ElMessage.success('门店信息已保存')
}
async function saveSettings() {
  await api.updateAiSettings(settingsForm.value)
  ElMessage.success('设置已保存')
}

// FAQ
function openFaqCreate() {
  editingFaqId.value = null
  faqForm.value = { question: '', answer: '', keywords: '' }
  faqDialog.value = true
}
function openFaqEdit(f: any) {
  editingFaqId.value = f.id
  faqForm.value = { question: f.question, answer: f.answer, keywords: f.keywords || '' }
  faqDialog.value = true
}
async function saveFaq() {
  if (editingFaqId.value) {
    await api.updateFaq(editingFaqId.value, faqForm.value)
  } else {
    await api.createFaq(faqForm.value)
  }
  faqDialog.value = false
  ElMessage.success('已保存')
  await load()
}
async function deleteFaq(f: any) {
  await ElMessageBox.confirm(`确定删除「${f.question}」？`, '提示', { type: 'warning' })
  await api.deleteFaq(f.id)
  ElMessage.success('已删除')
  await load()
}

// 密码
async function savePwd() {
  await api.changePassword(pwdForm.value)
  ElMessage.success('密码已修改')
  pwdForm.value = { old_password: '', new_password: '' }
}
</script>

<template>
  <div>
    <div class="page-title">设置</div>
    <el-tabs type="border-card">
      <!-- 门店信息 -->
      <el-tab-pane label="门店信息">
        <el-form label-width="90px" style="max-width: 520px">
          <el-form-item label="门店名称">
            <el-input v-model="storeForm.name" />
          </el-form-item>
          <el-form-item label="营业时间">
            <el-input v-model="storeForm.business_hours" placeholder="如 10:00-22:00" />
          </el-form-item>
          <el-form-item label="联系电话">
            <el-input v-model="storeForm.phone" />
          </el-form-item>
          <el-form-item label="门店地址">
            <el-input v-model="storeForm.address" type="textarea" :rows="2" />
          </el-form-item>
          <el-form-item>
            <el-button type="primary" @click="saveStore">保存</el-button>
          </el-form-item>
        </el-form>
        <div class="tip">这些信息会用于 AI 客服回答「几点关门」「地址」「电话」等问题。</div>
      </el-tab-pane>

      <!-- 知识库 FAQ -->
      <el-tab-pane label="知识库 FAQ">
        <div class="toolbar">
          <span class="tip">AI 客服会优先匹配这里的问答，命中率高、回答稳定、零成本。</span>
          <div class="spacer" />
          <el-button type="primary" @click="openFaqCreate">新建 FAQ</el-button>
        </div>
        <el-table :data="faqs" row-key="id">
          <el-table-column prop="question" label="问题" min-width="200" />
          <el-table-column prop="answer" label="答案" min-width="240" show-overflow-tooltip />
          <el-table-column prop="keywords" label="触发关键词" min-width="160" />
          <el-table-column label="操作" width="130" fixed="right">
            <template #default="{ row }">
              <el-button link type="primary" size="small" @click="openFaqEdit(row)">编辑</el-button>
              <el-button link type="danger" size="small" @click="deleteFaq(row)">删除</el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-tab-pane>

      <!-- AI 客服 -->
      <el-tab-pane label="AI 客服">
        <el-form label-width="160px" style="max-width: 560px">
          <el-form-item label="高置信度自动回复">
            <el-switch v-model="settingsForm.ai_auto_send" />
            <span class="tip-inline">开启后，安全咨询命中高置信度时自动回复，无需人工点击</span>
          </el-form-item>
          <el-form-item label="自动回复置信度阈值">
            <el-slider v-model="settingsForm.ai_threshold" :min="0.5" :max="0.95" :step="0.05" show-input style="width: 100%" />
            <div class="tip">置信度达到该值才自动回复，越低越激进、越高越保守（默认 0.85）。</div>
          </el-form-item>
          <el-form-item label="紧急消息声音提醒">
            <el-switch v-model="settingsForm.sound_enabled" />
          </el-form-item>
          <el-form-item>
            <el-button type="primary" @click="saveSettings">保存</el-button>
          </el-form-item>
        </el-form>
      </el-tab-pane>

      <!-- 预警阈值 -->
      <el-tab-pane label="预警阈值">
        <el-form label-width="180px" style="max-width: 560px">
          <el-form-item label="订单骤降阈值">
            <el-slider v-model="settingsForm.order_drop_ratio" :min="0.3" :max="0.9" :step="0.05" show-input :format-tooltip="(v: number) => Math.round(v * 100) + '%'" style="width: 100%" />
            <div class="tip">当日订单量低于近 7 天同时段均值的该比例时告警。</div>
          </el-form-item>
          <el-form-item label="差评激增阈值">
            <el-input-number v-model="settingsForm.bad_review_count" :min="1" :max="20" />
            <span class="tip-inline">24 小时内新增差评达到该数量时告警</span>
          </el-form-item>
          <el-form-item label="评分跌破阈值">
            <el-input-number v-model="settingsForm.rating_min" :min="3" :max="5" :step="0.1" :precision="1" />
            <span class="tip-inline">近 30 天综合评分低于该值时告警</span>
          </el-form-item>
          <el-form-item>
            <el-button type="primary" @click="saveSettings">保存</el-button>
          </el-form-item>
        </el-form>
      </el-tab-pane>

      <!-- 账号安全 -->
      <el-tab-pane label="账号安全">
        <el-form label-width="90px" style="max-width: 420px">
          <el-form-item label="原密码">
            <el-input v-model="pwdForm.old_password" type="password" show-password />
          </el-form-item>
          <el-form-item label="新密码">
            <el-input v-model="pwdForm.new_password" type="password" show-password />
          </el-form-item>
          <el-form-item>
            <el-button type="primary" @click="savePwd">修改密码</el-button>
          </el-form-item>
        </el-form>
      </el-tab-pane>
    </el-tabs>

    <!-- FAQ 编辑弹窗 -->
    <el-dialog v-model="faqDialog" :title="editingFaqId ? '编辑 FAQ' : '新建 FAQ'" width="480px">
      <el-form label-width="90px">
        <el-form-item label="问题">
          <el-input v-model="faqForm.question" placeholder="如：你们几点关门？" />
        </el-form-item>
        <el-form-item label="答案">
          <el-input v-model="faqForm.answer" type="textarea" :rows="3" placeholder="如：本店 10:00-22:00 营业" />
        </el-form-item>
        <el-form-item label="触发关键词">
          <el-input v-model="faqForm.keywords" placeholder="逗号分隔，如：营业时间,几点,关门" />
          <div class="tip">顾客消息包含这些关键词时命中此 FAQ。</div>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="faqDialog = false">取消</el-button>
        <el-button type="primary" @click="saveFaq">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.tip {
  font-size: 12px;
  color: var(--text-muted);
  margin-top: 4px;
}
.tip-inline {
  font-size: 12px;
  color: var(--text-muted);
  margin-left: 10px;
}
</style>
