<template>
  <view class="alerts">
    <view v-for="a in list" :key="a.id" class="alert-item">
      <view class="alert-top">
        <text class="alert-rule">{{ a.rule }}</text>
        <text class="alert-status" :class="a.status">{{ a.status === 'open' ? '待处理' : '已处理' }}</text>
      </view>
      <text class="alert-payload">{{ a.payload }}</text>
      <button v-if="a.status === 'open'" size="mini" @click="resolve(a)">标记已处理</button>
    </view>
    <view v-if="!list.length" class="empty">暂无预警</view>
  </view>
</template>

<script setup lang="ts">
import { onShow } from "@dcloudio/uni-app";
import { ref } from "vue";
import { api } from "@/utils/request";

const list = ref<any[]>([]);

async function load() {
  try {
    const r: any = await api.get("/alerts");
    list.value = r.items;
  } catch (e) {}
}

onShow(load);

async function resolve(a: any) {
  await api.post(`/alerts/${a.id}/resolve`);
  uni.showToast({ title: "已处理", icon: "none" });
  await load();
}
</script>

<style>
.alerts {
  padding: 24rpx;
}
.alert-item {
  background: #fff;
  border-radius: 16rpx;
  padding: 24rpx;
  margin-bottom: 20rpx;
}
.alert-top {
  display: flex;
  justify-content: space-between;
}
.alert-rule {
  font-size: 28rpx;
  font-weight: bold;
  color: #d03b3b;
}
.alert-status {
  font-size: 24rpx;
  color: #c3c2b7;
}
.alert-status.open {
  color: #d03b3b;
  font-weight: bold;
}
.alert-payload {
  display: block;
  font-size: 26rpx;
  color: #898781;
  margin: 12rpx 0;
}
.empty {
  text-align: center;
  color: #c3c2b7;
  padding: 100rpx;
}
</style>
