<template>
  <view class="login-page">
    <view class="logo">美团商家</view>
    <view class="sub">商家经营工具</view>

    <view class="tabs">
      <view class="tab" :class="{ active: mode === 'account' }" @click="mode = 'account'">账号密码</view>
      <view class="tab" :class="{ active: mode === 'wx' }" @click="mode = 'wx'">微信登录</view>
    </view>

    <!-- 账号密码登录 -->
    <view v-if="mode === 'account'" class="form">
      <input class="input" v-model="username" placeholder="账号" />
      <input class="input" v-model="password" password placeholder="密码" />
      <button class="btn" :loading="loading" @click="accountLogin">登录</button>
    </view>

    <!-- 微信登录 -->
    <view v-else class="form">
      <button class="btn wx" :loading="loading" @click="wxLogin">微信一键登录</button>
      <view v-if="needBind" class="bind">
        <view class="bind-tip">首次登录，请绑定已有账号</view>
        <input class="input" v-model="bindUsername" placeholder="绑定账号" />
        <input class="input" v-model="bindPassword" password placeholder="绑定密码" />
        <button class="btn" @click="wxBind">绑定并登录</button>
      </view>
    </view>

    <view class="hint">测试账号：merchant1 / 123456</view>
  </view>
</template>

<script setup lang="ts">
import { ref } from "vue";
import { api } from "@/utils/request";
import { setAuth } from "@/utils/auth";

const mode = ref<"account" | "wx">("account");
const username = ref("");
const password = ref("");
const loading = ref(false);
const needBind = ref(false);
const openid = ref("");
const bindUsername = ref("");
const bindPassword = ref("");

function goDashboard() {
  uni.switchTab({ url: "/pages/dashboard/dashboard" });
}

async function accountLogin() {
  if (!username.value || !password.value) {
    uni.showToast({ title: "请输入账号密码", icon: "none" });
    return;
  }
  loading.value = true;
  try {
    const r: any = await api.post("/auth/login", {
      username: username.value,
      password: password.value,
      role: "merchant",
    });
    uni.setStorageSync("token", r.token);
    const me: any = await api.get("/auth/me");
    setAuth(r.token, me);
    goDashboard();
  } catch (e: any) {
    uni.showToast({ title: e?.detail || "登录失败", icon: "none" });
  } finally {
    loading.value = false;
  }
}

async function wxLogin() {
  // #ifdef MP-WEIXIN
  loading.value = true;
  uni.login({
    provider: "weixin",
    success: async (loginRes: any) => {
      try {
        const r: any = await api.post("/auth/wx-login", { code: loginRes.code });
        if (r.need_bind) {
          needBind.value = true;
          openid.value = r.openid;
        } else {
          const me: any = await api.get("/auth/me");
          setAuth(r.token, me);
          goDashboard();
        }
      } catch (e: any) {
        uni.showToast({ title: e?.detail || "微信登录失败", icon: "none" });
      } finally {
        loading.value = false;
      }
    },
    fail: () => {
      loading.value = false;
      uni.showToast({ title: "微信登录失败", icon: "none" });
    },
  });
  // #endif
  // #ifndef MP-WEIXIN
  uni.showToast({ title: "请在微信小程序中使用", icon: "none" });
  // #endif
}

async function wxBind() {
  if (!bindUsername.value || !bindPassword.value) {
    uni.showToast({ title: "请输入账号密码", icon: "none" });
    return;
  }
  try {
    const r: any = await api.post("/auth/wx-bind", {
      openid: openid.value,
      username: bindUsername.value,
      password: bindPassword.value,
    });
    const me: any = await api.get("/auth/me");
    setAuth(r.token, me);
    goDashboard();
  } catch (e: any) {
    uni.showToast({ title: e?.detail || "绑定失败", icon: "none" });
  }
}
</script>

<style>
.login-page {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 120rpx 60rpx;
  background: #f9f9f7;
}
.logo {
  font-size: 44rpx;
  font-weight: bold;
  color: #0b0b0b;
}
.sub {
  font-size: 26rpx;
  color: #898781;
  margin-top: 12rpx;
  margin-bottom: 60rpx;
}
.tabs {
  display: flex;
  width: 100%;
  margin-bottom: 40rpx;
}
.tab {
  flex: 1;
  text-align: center;
  padding: 20rpx 0;
  color: #898781;
  border-bottom: 4rpx solid transparent;
}
.tab.active {
  color: #2a78d6;
  border-bottom-color: #2a78d6;
  font-weight: bold;
}
.form {
  width: 100%;
}
.input {
  background: #fff;
  border: 1rpx solid #e1e0d9;
  border-radius: 12rpx;
  padding: 24rpx;
  margin-bottom: 24rpx;
  font-size: 30rpx;
}
.btn {
  background: #2a78d6;
  color: #fff;
  border-radius: 12rpx;
  font-size: 32rpx;
  margin-top: 20rpx;
}
.btn.wx {
  background: #07c160;
}
.bind {
  margin-top: 40rpx;
}
.bind-tip {
  font-size: 26rpx;
  color: #898781;
  margin-bottom: 20rpx;
  text-align: center;
}
.hint {
  margin-top: 60rpx;
  font-size: 24rpx;
  color: #c3c2b7;
}
</style>
