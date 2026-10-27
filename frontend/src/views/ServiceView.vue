<script setup lang="ts">
import { ElMessage } from 'element-plus'
import { nextTick, onMounted, ref } from 'vue'

import { api, type AiImReplyResp, type MessageItem, type SessionItem } from '@/api'

const sessions = ref<SessionItem[]>([])
const activeSession = ref<number | null>(null)
const messages = ref<MessageItem[]>([])
const customerText = ref('')  // 模拟顾客消息（测试 AI 用）
const replyText = ref('')     // 商家回复
const replyInputRef = ref<any>()  // 商家回复输入框 ref
const aiLoading = ref(false)
const aiResult = ref<AiImReplyResp | null>(null)

const ACTION_LABEL: Record<string, string> = {
  auto: '全自动回复',
  semi: '半自动 · 待确认',
  manual: '转人工',
}
const ACTION_TAG: Record<string, 'success' | 'warning' | 'info'> = {
  auto: 'success',
  semi: 'warning',
  manual: 'info',
}

async function loadSessions() {
  sessions.value = (await api.listSessions()).items
}

async function selectSession(id: number) {
  activeSession.value = id
  aiResult.value = null
  messages.value = (await api.listMessages(id)).items
}

// 某条顾客消息后面没有商家回复，即为「未回复」
function isUnreplied(idx: number): boolean {
  const m = messages.value[idx]
  if (!m || m.direction !== 'inbound') return false
  return !messages.value.slice(idx + 1).some((x) => x.direction === 'outbound')
}
function bubbleClass(m: MessageItem, idx: number): string {
  if (m.is_urgent && !m.is_handled) return 'bubble-urgent'
  if (isUnreplied(idx)) return 'bubble-unreplied'
  return ''
}

async function simulateCustomer() {
  const text = customerText.value.trim()
  if (!text || !activeSession.value) return
  customerText.value = ''
  // 1. 顾客消息入会话
  await api.addMessage(activeSession.value, text, 'inbound')
  messages.value = (await api.listMessages(activeSession.value)).items
  // 2. 触发 AI 回复
  aiLoading.value = true
  aiResult.value = null
  try {
    aiResult.value = await api.aiImReply(text, activeSession.value)
    // 高置信度自动回复：后端已直接落库，刷新消息即可
    if (aiResult.value?.auto_sent) {
      messages.value = (await api.listMessages(activeSession.value)).items
      aiResult.value = null
      ElMessage.success('已自动回复')
    }
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || 'AI 调用失败')
  } finally {
    aiLoading.value = false
  }
  await loadSessions()
}

async function sendReply() {
  const text = replyText.value.trim()
  if (!text || !activeSession.value) return
  // 商家回复入会话（outbound）
  await api.addMessage(activeSession.value, text, 'outbound')
  // 回复即处理：标记该会话的紧急消息已处理（首页提醒随之消失）
  const unhandled = messages.value.filter((m) => m.is_urgent && !m.is_handled)
  for (const m of unhandled) {
    await api.handleMessage(m.id)
  }
  replyText.value = ''
  aiResult.value = null
  messages.value = (await api.listMessages(activeSession.value)).items
  await loadSessions()
  ElMessage.success('已回复')
}

// 采纳 AI 建议回复 → 填入商家回复框，聚焦并定位光标到末尾，可编辑后再发
function adoptDraft() {
  if (aiResult.value) {
    replyText.value = aiResult.value.reply
    aiResult.value = null
    nextTick(() => {
      const el = replyInputRef.value
      if (!el) return
      el.focus()
      const inner = el.$el?.querySelector('input, textarea')
      if (inner) {
        const n = inner.value.length
        inner.setSelectionRange?.(n, n)
      }
    })
  }
}

onMounted(loadSessions)
</script>

<template>
  <div>
    <div class="page-title">客服工作台</div>
    <div class="console">
      <el-card class="session-pane" shadow="never">
        <div class="pane-title">会话列表</div>
        <div
          v-for="s in sessions"
          :key="s.id"
          class="session-item"
          :class="{ active: s.id === activeSession }"
          @click="selectSession(s.id)"
        >
          <div class="session-top">
            <span class="session-id">
              <span v-if="s.unhandled_count" class="session-dot"></span>
              顾客 #{{ s.customer_id }}
            </span>
            <span v-if="s.unhandled_count" class="unhandled-badge">{{ s.unhandled_count }} 未处理</span>
            <span v-else class="session-count">{{ s.message_count }} 条</span>
          </div>
          <div class="session-last">{{ s.last_message }}</div>
        </div>
        <el-empty v-if="!sessions.length" description="暂无会话" :image-size="50" />
      </el-card>

      <el-card class="chat-pane" shadow="never">
        <div class="chat-body">
          <div v-if="!activeSession" class="chat-empty">
            <el-empty description="选择左侧会话开始" :image-size="60" />
          </div>

          <template v-else>
            <div v-for="(m, idx) in messages" :key="m.id" class="msg-row" :class="m.direction">
              <div class="bubble" :class="bubbleClass(m, idx)">
                <span class="bubble-who">{{ m.direction === 'inbound' ? '顾客' : '商家' }}</span>
                <div class="bubble-text">{{ m.content }}</div>
                <div v-if="m.direction === 'inbound'" class="bubble-tags">
                  <span v-if="m.scene_tag" class="tag tag-scene">{{ m.scene_tag }}</span>
                  <span v-if="m.is_urgent" class="tag" :class="m.is_handled ? 'tag-handled' : 'tag-urgent'">
                    {{ m.is_handled ? '已处理' : '待处理' }}
                  </span>
                  <span v-else-if="isUnreplied(idx)" class="tag tag-unreplied">未回复</span>
                </div>
              </div>
            </div>

            <div v-if="aiLoading" class="ai-loading">AI 思考中…</div>

            <div v-if="aiResult" class="ai-card">
              <div class="ai-head">
                <el-tag size="small" :type="aiResult.source === 'faq' ? 'success' : 'primary'">
                  {{ aiResult.source === 'faq' ? 'FAQ命中' : 'AI生成' }}
                </el-tag>
                <el-tag size="small">{{ aiResult.intent }}</el-tag>
                <el-tag :type="ACTION_TAG[aiResult.action]" size="small">{{ ACTION_LABEL[aiResult.action] }}</el-tag>
                <span class="ai-conf">置信度 {{ Math.round(aiResult.confidence * 100) }}%</span>
              </div>
              <div class="ai-reply">{{ aiResult.reply }}</div>
              <div class="ai-actions">
                <el-button type="primary" size="small" @click="adoptDraft">采纳此回复</el-button>
                <el-button size="small" @click="aiResult = null">忽略</el-button>
              </div>
            </div>
          </template>
        </div>

        <!-- 商家回复输入框（主） -->
        <div v-if="activeSession" class="chat-input">
          <el-input ref="replyInputRef" v-model="replyText" placeholder="输入回复内容，回车发送" @keyup.enter="sendReply" />
          <el-button type="primary" :disabled="!replyText.trim()" @click="sendReply">回复</el-button>
        </div>
        <!-- 模拟顾客消息（测试 AI 用） -->
        <div v-if="activeSession" class="chat-input simulate-input">
          <el-input v-model="customerText" placeholder="模拟顾客发消息（测试 AI 用）" @keyup.enter="simulateCustomer" />
          <el-button :disabled="!customerText.trim()" @click="simulateCustomer">模拟顾客</el-button>
        </div>
      </el-card>
    </div>
  </div>
</template>

<style scoped>
.console {
  display: grid;
  grid-template-columns: 280px 1fr;
  gap: 16px;
  height: calc(100vh - 140px);
}
.session-pane,
.chat-pane {
  display: flex;
  flex-direction: column;
  min-height: 0;
}
.pane-title {
  font-size: 14px;
  font-weight: 600;
  margin-bottom: 12px;
}
.session-item {
  padding: 10px 12px;
  border-radius: 8px;
  cursor: pointer;
  margin-bottom: 4px;
}
.session-item:hover {
  background: var(--page-plane);
}
.session-item.active {
  background: var(--page-plane);
  box-shadow: inset 2px 0 0 var(--series-blue);
}
.session-top {
  display: flex;
  justify-content: space-between;
  font-size: 13px;
  margin-bottom: 4px;
}
.session-id {
  display: inline-flex;
  align-items: center;
  gap: 6px;
}
.session-dot {
  width: 8px;
  height: 8px;
  border-color: red;
  border-radius: 50%;
  background: var(--status-critical);
  flex-shrink: 0;
  animation: dot-pulse 1.2s infinite;
}
@keyframes dot-pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.25; }
}
.session-count {
  color: var(--text-muted);
  font-size: 12px;
}
.unhandled-badge {
  background: var(--status-critical);
  color: #fff;
  font-size: 11px;
  padding: 1px 8px;
  border-radius: 10px;
}
.urgent-tag {
  margin-left: 6px;
}
.session-last {
  font-size: 12px;
  color: var(--text-muted);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.chat-body {
  flex: 1;
  overflow-y: auto;
  padding: 8px 4px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.chat-empty {
  margin: auto;
}
.msg-row {
  display: flex;
}
.msg-row.inbound {
  justify-content: flex-start;
}
.msg-row.outbound {
  justify-content: flex-end;
}
.bubble {
  max-width: 70%;
  padding: 8px 12px;
  border-radius: 10px;
  font-size: 14px;
  background: var(--page-plane);
  border: 1px solid var(--gridline);
}
.msg-row.outbound .bubble {
  background: var(--series-blue);
  color: #fff;
  border-color: var(--series-blue);
}
.msg-row.inbound .bubble-urgent {
  background: #fff2f2;
  border: 1.5px solid var(--status-critical);
}
.msg-row.inbound .bubble-unreplied {
  border: 1.5px dashed #e6a23c;
  background: #fffaf0;
}
.bubble-who {
  display: block;
  font-size: 11px;
  opacity: 0.7;
  margin-bottom: 2px;
}
.bubble-text {
  white-space: pre-wrap;
  word-break: break-word;
}
.bubble-tags {
  margin-top: 6px;
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}
.tag {
  display: inline-block;
  font-size: 11px;
  line-height: 18px;
  padding: 0 8px;
  border-radius: 4px;
  border: 1px solid transparent;
}
.tag-scene {
  background: #fff;
  border-color: var(--gridline);
  color: var(--text-secondary);
}
.tag-urgent {
  background: var(--status-critical);
  color: #fff;
}
.tag-handled {
  background: #f0f0f0;
  color: #909399;
}
.tag-unreplied {
  background: #fdf6ec;
  border-color: #f3d19e;
  color: #e6a23c;
}

.ai-loading {
  color: var(--text-muted);
  font-size: 13px;
  padding: 4px;
}
.ai-card {
  border: 1px solid var(--gridline);
  border-left: 3px solid var(--series-blue);
  border-radius: 8px;
  padding: 12px;
  background: var(--surface-1);
}
.ai-head {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}
.ai-conf {
  color: var(--text-muted);
  font-size: 12px;
}
.ai-reply {
  font-size: 14px;
  line-height: 1.5;
  margin-bottom: 8px;
}
.ai-actions {
  display: flex;
  gap: 8px;
}

.chat-input {
  display: flex;
  gap: 8px;
  margin-top: 12px;
}
.simulate-input {
  margin-top: 8px;
  opacity: 0.72;
}
</style>
