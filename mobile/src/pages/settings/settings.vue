<template>
  <view class="settings">
    <view class="group">
      <view class="cell" @click="go('/pages/settings/store')">
        <text>门店信息</text>
        <text class="arrow">›</text>
      </view>
      <view class="cell" @click="go('/pages/settings/ai')">
        <text>AI 客服</text>
        <text class="arrow">›</text>
      </view>
    </view>
    <view class="group">
      <view class="cell" @click="go('/pages/settings/password')">
        <text>修改密码</text>
        <text class="arrow">›</text>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
function go(url: string) {
  uni.navigateTo({ url });
}
</script>

<style>
.settings {
  padding: 24rpx;
}
.group {
  background: #fff;
  border-radius: 16rpx;
  margin-bottom: 24rpx;
  overflow: hidden;
}
.cell {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 30rpx 24rpx;
  font-size: 30rpx;
  border-bottom: 1rpx solid #f0f0f0;
}
.cell:last-child {
  border-bottom: none;
}
.arrow {
  color: #c3c2b7;
  font-size: 36rpx;
}
</style>
