<template>
  <view class="dash">
    <!-- KPI 卡 -->
    <view class="kpi-row">
      <view class="kpi">
        <text class="kpi-label">今日营收</text>
        <text class="kpi-value">¥{{ s.revenue }}</text>
      </view>
      <view class="kpi">
        <text class="kpi-label">今日订单</text>
        <text class="kpi-value">{{ s.order_count }}</text>
      </view>
      <view class="kpi">
        <text class="kpi-label">客单价</text>
        <text class="kpi-value">¥{{ s.avg_order_value }}</text>
      </view>
    </view>

    <!-- 待办预警 -->
    <view v-if="urgentCount" class="urgent" @click="goService">
      <text class="urgent-dot">●</text>
      <text class="urgent-text">{{ urgentCount }} 条紧急客服消息待处理</text>
    </view>

    <!-- 营收趋势 -->
    <view class="card">
      <view class="card-title">近 30 天营收</view>
      <u-chart canvas-id="trendChart" type="line" :categories="trendCats" :series="trendSeries" />
    </view>

    <!-- 时段分布 -->
    <view class="card">
      <view class="card-title">时段分布（近 30 天订单）</view>
      <u-chart canvas-id="hourlyChart" type="column" :categories="hourlyCats" :series="hourlySeries" color="#1baf7a" />
    </view>

    <!-- 快捷入口 -->
    <view class="grid">
      <view class="grid-item" @click="go('/pages/orders/orders')">
        <text class="grid-icon">📋</text>
        <text class="grid-label">订单管理</text>
      </view>
      <view class="grid-item" @click="go('/pages/service/service')">
        <text class="grid-icon">💬</text>
        <text class="grid-label">客服工作台</text>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { onShow } from "@dcloudio/uni-app";
import { ref } from "vue";
import { api } from "@/utils/request";
import UChart from "@/components/u-chart/u-chart.vue";

const s = ref({ revenue: "0", order_count: 0, avg_order_value: "0" });
const urgentCount = ref(0);
const trendCats = ref<string[]>([]);
const trendSeries = ref<any[]>([]);
const hourlyCats = ref<string[]>([]);
const hourlySeries = ref<any[]>([]);

async function load() {
  try {
    const summary: any = await api.get("/dashboard/summary");
    s.value = {
      revenue: Number(summary.revenue).toFixed(2),
      order_count: summary.order_count,
      avg_order_value: Number(summary.avg_order_value).toFixed(2),
    };
  } catch (e) {}
  try {
    const u: any = await api.get("/im/urgent-messages");
    urgentCount.value = u.items.length;
  } catch (e) {}
  try {
    const t: any = await api.get("/dashboard/trend?days=30");
    trendCats.value = t.items.map((i: any) => i.date.slice(5));
    trendSeries.value = [{ name: "营收", data: t.items.map((i: any) => Number(i.revenue)) }];
  } catch (e) {}
  try {
    const h: any = await api.get("/analytics/hourly?days=30");
    hourlyCats.value = h.items.map((i: any) => i.hour + "时");
    hourlySeries.value = [{ name: "订单量", data: h.items.map((i: any) => i.order_count) }];
  } catch (e) {}
}

onShow(load);

function go(url: string) {
  uni.switchTab({ url });
}
function goService() {
  uni.switchTab({ url: "/pages/service/service" });
}
</script>

<style>
.dash {
  padding: 24rpx;
}
.kpi-row {
  display: flex;
  gap: 20rpx;
}
.kpi {
  flex: 1;
  background: #fff;
  border-radius: 16rpx;
  padding: 28rpx;
}
.kpi-label {
  display: block;
  font-size: 24rpx;
  color: #898781;
}
.kpi-value {
  display: block;
  font-size: 36rpx;
  font-weight: bold;
  margin-top: 12rpx;
  color: #0b0b0b;
}
.urgent {
  display: flex;
  align-items: center;
  gap: 12rpx;
  background: #fdecec;
  border: 1rpx solid #d03b3b;
  border-radius: 12rpx;
  padding: 20rpx;
  margin-top: 24rpx;
}
.urgent-dot {
  color: #d03b3b;
  font-size: 32rpx;
}
.urgent-text {
  color: #b32424;
  font-size: 28rpx;
  font-weight: bold;
}
.card {
  background: #fff;
  border-radius: 16rpx;
  padding: 24rpx;
  margin-top: 24rpx;
}
.card-title {
  font-size: 28rpx;
  font-weight: bold;
  margin-bottom: 16rpx;
}
.grid {
  display: flex;
  gap: 20rpx;
  margin-top: 24rpx;
}
.grid-item {
  flex: 1;
  background: #fff;
  border-radius: 16rpx;
  padding: 40rpx 20rpx;
  text-align: center;
}
.grid-icon {
  display: block;
  font-size: 56rpx;
}
.grid-label {
  display: block;
  font-size: 28rpx;
  color: #52514e;
  margin-top: 12rpx;
}
</style>
