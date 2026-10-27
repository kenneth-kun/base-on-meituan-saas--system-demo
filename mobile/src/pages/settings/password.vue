<template>
  <view class="form-page">
    <view class="field">
      <text class="label">原密码</text>
      <input class="input" v-model="pwd.old_password" password placeholder="请输入原密码" />
    </view>
    <view class="field">
      <text class="label">新密码</text>
      <input class="input" v-model="pwd.new_password" password placeholder="至少 6 位" />
    </view>
    <button class="save-btn" type="primary" @click="save">修改密码</button>
  </view>
</template>

<script setup lang="ts">
import { ref } from "vue";
import { api } from "@/utils/request";

const pwd = ref({ old_password: "", new_password: "" });

async function save() {
  if (!pwd.value.old_password || !pwd.value.new_password) {
    uni.showToast({ title: "请填写完整", icon: "none" });
    return;
  }
  try {
    await api.post("/settings/password", pwd.value);
    uni.showToast({ title: "密码已修改", icon: "none" });
    pwd.value = { old_password: "", new_password: "" };
  } catch (e: any) {
    uni.showToast({ title: e?.detail || "修改失败", icon: "none" });
  }
}
</script>

<style>
.form-page {
  padding: 24rpx;
}
.field {
  margin-bottom: 24rpx;
}
.label {
  display: block;
  font-size: 26rpx;
  color: #898781;
  margin-bottom: 12rpx;
}
.input {
  background: #fff;
  border-radius: 12rpx;
  padding: 24rpx;
  font-size: 30rpx;
}
.save-btn {
  margin-top: 40rpx;
}
</style>
