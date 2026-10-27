<template>
  <view class="products">
    <view v-for="p in list" :key="p.id" class="product-item">
      <view class="product-info">
        <text class="product-name">{{ p.name }}</text>
        <text class="product-meta">{{ p.category }} · 编码 {{ p.app_food_code }}</text>
      </view>
      <view class="product-right">
        <text class="product-price">¥{{ Number(p.price).toFixed(2) }}</text>
        <text class="product-stock" :class="{ zero: p.stock === 0 }">库存 {{ p.stock }}</text>
        <text class="product-sales">销量 {{ p.sales }}</text>
      </view>
    </view>
    <view v-if="!list.length" class="empty">暂无商品</view>
  </view>
</template>

<script setup lang="ts">
import { onShow } from "@dcloudio/uni-app";
import { ref } from "vue";
import { api } from "@/utils/request";

const list = ref<any[]>([]);

async function load() {
  try {
    const r: any = await api.get("/products");
    list.value = r.items;
  } catch (e) {}
}

onShow(load);
</script>

<style>
.products {
  padding: 24rpx;
}
.product-item {
  background: #fff;
  border-radius: 16rpx;
  padding: 24rpx;
  margin-bottom: 20rpx;
  display: flex;
  justify-content: space-between;
}
.product-name {
  display: block;
  font-size: 30rpx;
  font-weight: bold;
}
.product-meta {
  display: block;
  font-size: 24rpx;
  color: #c3c2b7;
  margin-top: 8rpx;
}
.product-right {
  text-align: right;
}
.product-price {
  display: block;
  font-size: 30rpx;
  color: #d03b3b;
  font-weight: bold;
}
.product-stock {
  display: block;
  font-size: 24rpx;
  color: #898781;
  margin-top: 6rpx;
}
.product-stock.zero {
  color: #d03b3b;
  font-weight: bold;
}
.product-sales {
  display: block;
  font-size: 24rpx;
  color: #c3c2b7;
  margin-top: 6rpx;
}
.empty {
  text-align: center;
  color: #c3c2b7;
  padding: 100rpx;
}
</style>
