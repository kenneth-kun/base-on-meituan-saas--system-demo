<template>
  <view class="form-page">
    <view class="card">
      <view class="row">
        <text class="row-label">高置信度自动回复</text>
        <switch :checked="settings.ai_auto_send" @change="onAutoSend" />
      </view>
      <text class="row-tip">安全咨询命中高置信度时自动回复，无需人工点击</text>
    </view>

    <view class="card">
      <view class="row">
        <text class="row-label">紧急消息声音提醒</text>
        <switch :checked="settings.sound_enabled" @change="onSound" />
      </view>
    </view>

    <view class="card">
      <view class="row">
        <text class="row-label">自动回复置信度阈值</text>
        <text class="row-value">{{ (settings.ai_threshold * 100).toFixed(0) }}%</text>
      </view>
      <slider :value="settings.ai_threshold * 100" min="50" max="95" step="5" @change="onThreshold" />
      <text class="row-tip">置信度达到该值才自动回复，越低越激进、越高越保守</text>
    </view>

    <button class="save-btn" type="primary" @click="save">保存</button>
  </view>
</template>

<script setup lang="ts">
import { onShow } from "@dcloudio/uni-app";
import { ref } from "vue";
import { api } from "@/utils/request";

const settings = ref<any>({ ai_auto_send: true, ai_threshold: 0.85, sound_enabled: true });

async function load() {
  try {
    const d: any = await api.get("/settings");
    settings.value = d.settings;
  } catch (e) {}
}
onShow(load);

function onAutoSend(e: any) {
  settings.value.ai_auto_send = e.detail.value;
}
function onSound(e: any) {
  settings.value.sound_enabled = e.detail.value;
}
function onThreshold(e: any) {
  settings.value.ai_threshold = e.detail.value / 100;
}

async function save() {
  await api.put("/settings/ai", settings.value);
  uni.showToast({ title: "已保存", icon: "none" });
}
</script>

<style>
.form-page {
  padding: 24rpx;
}
.card {
  background: #fff;
  border-radius: 16rpx;
  padding: 24rpx;
  margin-bottom: 24rpx;
}
.row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 30rpx;
}
.row-label {
  font-size: 30rpx;
}
.row-value {
  font-size: 30rpx;
  color: #2a78d6;
  font-weight: bold;
}
.row-tip {
  display: block;
  font-size: 24rpx;
  color: #c3c2b7;
  margin-top: 12rpx;
}
.save-btn {
  margin-top: 20rpx;
}
</style>
