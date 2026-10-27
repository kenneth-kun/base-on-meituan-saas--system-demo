<template>
  <view class="orders">
    <view v-for="o in list" :key="o.id" class="order-item">
      <view class="order-top">
        <text class="order-no">{{ o.order_no }}</text>
        <text class="order-status">{{ o.status_label }}</text>
      </view>
      <view class="order-bottom">
        <text class="order-amount">¥{{ Number(o.total_amount).toFixed(2) }}</text>
        <text class="order-time">{{ o.placed_at.replace("T", " ").slice(5, 16) }}</text>
      </view>
    </view>
    <view v-if="!list.length" class="empty">暂无订单</view>
  </view>
</template>

<script setup lang="ts">
import { onShow } from "@dcloudio/uni-app";
import { ref } from "vue";
import { api } from "@/utils/request";

const list = ref<any[]>([]);

async function load() {
  try {
    const r: any = await api.get("/orders?page=1&page_size=20");
    list.value = r.items;
  } catch (e) {}
}

onShow(load);
</script>

<style>
.orders {
  padding: 24rpx;
}
.order-item {
  background: #fff;
  border-radius: 16rpx;
  padding: 24rpx;
  margin-bottom: 20rpx;
}
.order-top {
  display: flex;
  justify-content: space-between;
}
.order-no {
  font-size: 26rpx;
  color: #898781;
}
.order-status {
  font-size: 24rpx;
  color: #2a78d6;
}
.order-bottom {
  display: flex;
  justify-content: space-between;
  margin-top: 16rpx;
}
.order-amount {
  font-size: 32rpx;
  font-weight: bold;
}
.order-time {
  font-size: 24rpx;
  color: #c3c2b7;
}
.empty {
  text-align: center;
  color: #c3c2b7;
  padding: 100rpx;
}
</style>
