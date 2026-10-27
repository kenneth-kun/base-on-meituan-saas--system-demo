<template>
  <view class="mine">
    <view class="user-card">
      <text class="user-name">{{ user?.username || "未登录" }}</text>
      <text class="user-type">商家账号</text>
    </view>

    <view class="menu">
      <view class="menu-item" @click="go('/pages/settings/settings')">
        <text>设置</text>
        <text class="arrow">›</text>
      </view>
      <view class="menu-item" @click="go('/pages/products/products')">
        <text>商品管理</text>
        <text class="arrow">›</text>
      </view>
      <view class="menu-item" @click="go('/pages/reviews/reviews')">
        <text>评价管理</text>
        <text class="arrow">›</text>
      </view>
      <view class="menu-item" @click="go('/pages/alerts/alerts')">
        <text>预警中心</text>
        <text class="arrow">›</text>
      </view>
    </view>

    <button class="logout" @click="doLogout">退出登录</button>
  </view>
</template>

<script setup lang="ts">
import { ref } from "vue";
import { getUser, logout } from "@/utils/auth";

const user = ref(getUser());

function go(url: string) {
  uni.navigateTo({ url });
}

function doLogout() {
  logout();
  uni.reLaunch({ url: "/pages/login/login" });
}
</script>

<style>
.mine {
  padding: 24rpx;
}
.user-card {
  background: #2a78d6;
  border-radius: 16rpx;
  padding: 40rpx;
  color: #fff;
}
.user-name {
  display: block;
  font-size: 36rpx;
  font-weight: bold;
}
.user-type {
  display: block;
  font-size: 24rpx;
  opacity: 0.8;
  margin-top: 8rpx;
}
.menu {
  background: #fff;
  border-radius: 16rpx;
  margin-top: 24rpx;
}
.menu-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 28rpx;
  font-size: 28rpx;
  border-bottom: 1rpx solid #f0f0f0;
}
.arrow {
  color: #c3c2b7;
  font-size: 32rpx;
}
.logout {
  margin-top: 40rpx;
  background: #fff;
  color: #d03b3b;
  border-radius: 12rpx;
}
</style>
