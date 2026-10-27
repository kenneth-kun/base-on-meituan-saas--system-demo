<template>
  <view class="service">
    <!-- 会话列表 -->
    <view v-for="s in sessions" :key="s.id" class="session" @click="openSession(s)">
      <view class="session-top">
        <view class="session-id">
          <text v-if="s.unhandled_count" class="dot"></text>
          <text>顾客 #{{ s.customer_id }}</text>
        </view>
        <text v-if="s.unhandled_count" class="badge">{{ s.unhandled_count }} 未处理</text>
        <text v-else class="count">{{ s.message_count }} 条</text>
      </view>
      <text class="session-last">{{ s.last_message }}</text>
    </view>
    <view v-if="!sessions.length" class="empty">暂无会话</view>
  </view>
</template>

<script setup lang="ts">
import { onShow } from "@dcloudio/uni-app";
import { ref } from "vue";
import { api } from "@/utils/request";

const sessions = ref<any[]>([]);

async function load() {
  try {
    const r: any = await api.get("/im/sessions");
    sessions.value = r.items;
  } catch (e) {}
}

onShow(load);

function openSession(s: any) {
  uni.navigateTo({ url: `/pages/service/detail?id=${s.id}` });
}
</script>

<style>
.service {
  padding: 24rpx;
}
.session {
  background: #fff;
  border-radius: 16rpx;
  padding: 24rpx;
  margin-bottom: 20rpx;
}
.session-top {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.session-id {
  display: flex;
  align-items: center;
  gap: 12rpx;
  font-size: 28rpx;
  font-weight: bold;
}
.dot {
  width: 14rpx;
  height: 14rpx;
  border-radius: 50%;
  background: #d03b3b;
}
.badge {
  background: #d03b3b;
  color: #fff;
  font-size: 22rpx;
  padding: 4rpx 16rpx;
  border-radius: 20rpx;
}
.count {
  font-size: 24rpx;
  color: #c3c2b7;
}
.session-last {
  display: block;
  font-size: 26rpx;
  color: #898781;
  margin-top: 12rpx;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.empty {
  text-align: center;
  color: #c3c2b7;
  padding: 100rpx;
}
</style>
