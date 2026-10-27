<template>
  <view class="chat-page">
    <scroll-view class="msg-list" scroll-y :scroll-into-view="scrollId">
      <view v-for="(m, idx) in messages" :key="m.id" :id="'msg-' + m.id" class="msg-row" :class="m.direction">
        <view class="bubble" :class="bubbleClass(m, idx)">
          <text class="who">{{ m.direction === 'inbound' ? '顾客' : '商家' }}</text>
          <text class="content">{{ m.content }}</text>
          <view v-if="m.direction === 'inbound'" class="tags">
            <text v-if="m.scene_tag" class="tag">{{ m.scene_tag }}</text>
            <text v-if="m.is_urgent" class="tag" :class="m.is_handled ? 'handled' : 'urgent'">
              {{ m.is_handled ? '已处理' : '待处理' }}
            </text>
            <text v-else-if="isUnreplied(idx)" class="tag unreplied">未回复</text>
          </view>
        </view>
      </view>

      <view v-if="aiLoading" class="ai-loading">AI 思考中…</view>

      <view v-if="aiResult" class="ai-card">
        <text class="ai-head">{{ aiResult.source === 'faq' ? 'FAQ命中' : 'AI生成' }} · {{ aiResult.intent }}</text>
        <text class="ai-reply">{{ aiResult.reply }}</text>
        <view class="ai-actions">
          <button size="mini" type="primary" @click="adoptDraft">采纳此回复</button>
          <button size="mini" @click="aiResult = null">忽略</button>
        </view>
      </view>
    </scroll-view>

    <view class="input-area">
      <input class="reply-input" v-model="replyText" placeholder="输入回复" confirm-type="send" @confirm="sendReply" />
      <button class="reply-btn" size="mini" type="primary" @click="sendReply">回复</button>
    </view>
    <view class="simulate-area">
      <input class="reply-input" v-model="customerText" placeholder="模拟顾客消息（测试）" @confirm="simulateCustomer" />
      <button class="reply-btn" size="mini" @click="simulateCustomer">模拟</button>
    </view>
  </view>
</template>

<script setup lang="ts">
import { onLoad } from "@dcloudio/uni-app";
import { ref } from "vue";
import { api } from "@/utils/request";

const sessionId = ref(0);
const messages = ref<any[]>([]);
const replyText = ref("");
const customerText = ref("");
const aiResult = ref<any>(null);
const aiLoading = ref(false);
const scrollId = ref("");

function isUnreplied(idx: number): boolean {
  const m = messages.value[idx];
  if (!m || m.direction !== "inbound") return false;
  return !messages.value.slice(idx + 1).some((x) => x.direction === "outbound");
}
function bubbleClass(m: any, idx: number): string {
  if (m.is_urgent && !m.is_handled) return "bubble-urgent";
  if (isUnreplied(idx)) return "bubble-unreplied";
  return "";
}

async function loadMessages() {
  if (!sessionId.value) return;
  const r: any = await api.get(`/im/sessions/${sessionId.value}/messages`);
  messages.value = r.items;
  scrollId.value = "msg-" + (r.items.length ? r.items[r.items.length - 1].id : "");
}

onLoad((options: any) => {
  sessionId.value = Number(options.id);
  loadMessages();
});

async function sendReply() {
  const text = replyText.value.trim();
  if (!text || !sessionId.value) return;
  await api.post(`/im/sessions/${sessionId.value}/messages`, { content: text, direction: "outbound" });
  const unhandled = messages.value.filter((m) => m.is_urgent && !m.is_handled);
  for (const m of unhandled) {
    await api.post(`/im/messages/${m.id}/handle`);
  }
  replyText.value = "";
  aiResult.value = null;
  await loadMessages();
}

async function simulateCustomer() {
  const text = customerText.value.trim();
  if (!text || !sessionId.value) return;
  await api.post(`/im/sessions/${sessionId.value}/messages`, { content: text, direction: "inbound" });
  await loadMessages();
  customerText.value = "";
  aiLoading.value = true;
  aiResult.value = null;
  try {
    const r: any = await api.post("/ai/im-reply", { message: text, session_id: sessionId.value });
    if (r.auto_sent) {
      await loadMessages();
      uni.showToast({ title: "已自动回复", icon: "none" });
    } else {
      aiResult.value = r;
    }
  } catch (e: any) {
    uni.showToast({ title: e?.detail || "AI 调用失败", icon: "none" });
  } finally {
    aiLoading.value = false;
  }
}

function adoptDraft() {
  if (aiResult.value) {
    replyText.value = aiResult.value.reply;
    aiResult.value = null;
  }
}
</script>

<style>
.chat-page {
  display: flex;
  flex-direction: column;
  height: 100vh;
}
.msg-list {
  flex: 1;
  padding: 24rpx;
  box-sizing: border-box;
}
.msg-row {
  display: flex;
  margin-bottom: 20rpx;
}
.msg-row.inbound {
  justify-content: flex-start;
}
.msg-row.outbound {
  justify-content: flex-end;
}
.bubble {
  max-width: 70%;
  background: #fff;
  border: 1rpx solid #e1e0d9;
  border-radius: 16rpx;
  padding: 20rpx;
}
.msg-row.outbound .bubble {
  background: #2a78d6;
  border-color: #2a78d6;
}
.bubble-urgent {
  border: 2rpx solid #d03b3b;
  background: #fff2f2;
}
.bubble-unreplied {
  border: 2rpx dashed #e6a23c;
  background: #fffaf0;
}
.who {
  display: block;
  font-size: 22rpx;
  opacity: 0.6;
  margin-bottom: 8rpx;
}
.msg-row.outbound .who {
  color: #fff;
}
.content {
  font-size: 28rpx;
  color: #0b0b0b;
}
.msg-row.outbound .content {
  color: #fff;
}
.tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8rpx;
  margin-top: 8rpx;
}
.tag {
  font-size: 20rpx;
  background: #f0f0f0;
  color: #898781;
  padding: 2rpx 12rpx;
  border-radius: 8rpx;
}
.tag.urgent {
  background: #d03b3b;
  color: #fff;
}
.tag.handled {
  background: #f0f0f0;
  color: #909399;
}
.tag.unreplied {
  background: #fdf6ec;
  color: #e6a23c;
  border: 1rpx solid #f3d19e;
}
.ai-loading {
  text-align: center;
  color: #c3c2b7;
  font-size: 24rpx;
  padding: 20rpx;
}
.ai-card {
  background: #fff;
  border-left: 6rpx solid #2a78d6;
  border-radius: 12rpx;
  padding: 20rpx;
  margin-bottom: 20rpx;
}
.ai-head {
  font-size: 22rpx;
  color: #898781;
}
.ai-reply {
  display: block;
  font-size: 28rpx;
  margin: 12rpx 0;
}
.ai-actions {
  display: flex;
  gap: 16rpx;
}
.input-area {
  display: flex;
  gap: 12rpx;
  padding: 16rpx 24rpx;
  border-top: 1rpx solid #e1e0d9;
}
.simulate-area {
  display: flex;
  gap: 12rpx;
  padding: 0 24rpx 20rpx;
}
.reply-input {
  flex: 1;
  background: #fff;
  border: 1rpx solid #e1e0d9;
  border-radius: 12rpx;
  padding: 16rpx;
  font-size: 28rpx;
}
.reply-btn {
  margin: 0;
}
</style>
