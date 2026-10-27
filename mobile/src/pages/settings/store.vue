<template>
  <view class="form-page">
    <view class="field">
      <text class="label">门店名称</text>
      <input class="input" v-model="form.name" placeholder="请输入门店名称" />
    </view>
    <view class="field">
      <text class="label">营业时间</text>
      <input class="input" v-model="form.business_hours" placeholder="如 10:00-22:00" />
    </view>
    <view class="field">
      <text class="label">联系电话</text>
      <input class="input" v-model="form.phone" placeholder="请输入电话" />
    </view>
    <view class="field">
      <text class="label">门店地址</text>
      <input class="input" v-model="form.address" placeholder="请输入地址" />
    </view>
    <button class="save-btn" type="primary" @click="save">保存</button>
  </view>
</template>

<script setup lang="ts">
import { onShow } from "@dcloudio/uni-app";
import { ref } from "vue";
import { api } from "@/utils/request";

const form = ref({ name: "", address: "", phone: "", business_hours: "" });

async function load() {
  try {
    const d: any = await api.get("/settings");
    form.value = {
      name: d.store.name,
      address: d.store.address || "",
      phone: d.store.phone || "",
      business_hours: d.store.business_hours || "",
    };
  } catch (e) {}
}
onShow(load);

async function save() {
  await api.put("/settings/store", form.value);
  uni.showToast({ title: "已保存", icon: "none" });
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
