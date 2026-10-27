<template>
  <view class="reviews">
    <view class="tabs">
      <view class="tab" :class="{ active: tab === 'unreplied' }" @click="switchTab('unreplied')">未回复</view>
      <view class="tab" :class="{ active: tab === 'replied' }" @click="switchTab('replied')">已回复</view>
      <view class="tab" :class="{ active: tab === 'all' }" @click="switchTab('all')">全部</view>
    </view>

    <view v-for="r in list" :key="r.id" class="review-item">
      <view class="review-top">
        <text class="review-star">{{ starText(r.rating) }} {{ r.accurate_star ?? r.rating }}分</text>
        <text class="review-order">{{ r.order_no }}</text>
      </view>
      <text class="review-content">{{ r.content }}</text>
      <text v-if="r.tags" class="review-tags">{{ r.tags }}</text>
      <view v-if="r.reply" class="review-reply">商家回复：{{ r.reply }}</view>
      <view v-else-if="replyingId === r.id" class="reply-edit">
        <input v-model="replyText" placeholder="输入回复" />
        <button size="mini" type="primary" @click="submitReply(r)">提交</button>
      </view>
      <button v-else size="mini" @click="openReply(r)">回复</button>
    </view>
    <view v-if="!list.length" class="empty">暂无评价</view>
  </view>
</template>

<script setup lang="ts">
import { onShow } from "@dcloudio/uni-app";
import { ref } from "vue";
import { api } from "@/utils/request";

const tab = ref<"all" | "unreplied" | "replied">("unreplied");
const list = ref<any[]>([]);
const replyingId = ref<number | null>(null);
const replyText = ref("");

function starText(rating: number): string {
  return "★".repeat(rating) + "☆".repeat(5 - rating);
}

async function load() {
  try {
    const replied = tab.value === "all" ? "" : tab.value === "replied" ? "&replied=true" : "&replied=false";
    const r: any = await api.get(`/reviews?page=1&page_size=50${replied}`);
    list.value = r.items;
  } catch (e) {}
}

onShow(load);

function switchTab(t: "all" | "unreplied" | "replied") {
  tab.value = t;
  load();
}

function openReply(r: any) {
  replyingId.value = r.id;
  replyText.value = "";
}
async function submitReply(r: any) {
  if (!replyText.value.trim()) return;
  await api.post(`/reviews/${r.id}/reply`, { content: replyText.value.trim() });
  replyingId.value = null;
  uni.showToast({ title: "已回复", icon: "none" });
  await load();
}
</script>

<style>
.reviews {
  padding: 24rpx;
}
.tabs {
  display: flex;
  background: #fff;
  border-radius: 16rpx;
  margin-bottom: 24rpx;
  overflow: hidden;
}
.tab {
  flex: 1;
  text-align: center;
  padding: 24rpx 0;
  font-size: 28rpx;
  color: #898781;
  border-bottom: 4rpx solid transparent;
}
.tab.active {
  color: #2a78d6;
  border-bottom-color: #2a78d6;
  font-weight: bold;
}
.review-item {
  background: #fff;
  border-radius: 16rpx;
  padding: 24rpx;
  margin-bottom: 20rpx;
}
.review-top {
  display: flex;
  justify-content: space-between;
}
.review-star {
  font-size: 26rpx;
  color: #e6a23c;
}
.review-order {
  font-size: 22rpx;
  color: #c3c2b7;
}
.review-content {
  display: block;
  font-size: 28rpx;
  margin: 12rpx 0;
}
.review-tags {
  display: block;
  font-size: 22rpx;
  color: #898781;
}
.review-reply {
  background: #f9f9f7;
  border-radius: 8rpx;
  padding: 16rpx;
  font-size: 24rpx;
  color: #52514e;
  margin-top: 12rpx;
}
.reply-edit {
  display: flex;
  gap: 12rpx;
  margin-top: 12rpx;
}
.reply-edit input {
  flex: 1;
  background: #f9f9f7;
  border-radius: 8rpx;
  padding: 12rpx;
  font-size: 26rpx;
}
.empty {
  text-align: center;
  color: #c3c2b7;
  padding: 100rpx;
}
</style>
