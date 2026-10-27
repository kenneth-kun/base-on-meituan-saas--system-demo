<template>
  <view class="chart-wrap">
    <canvas :canvas-id="canvasId" :id="canvasId" class="chart-canvas"></canvas>
  </view>
</template>

<script setup lang="ts">
import { getCurrentInstance, onMounted, watch } from "vue";
import uCharts from "@qiun/ucharts";

const props = defineProps<{
  canvasId: string;
  type: string; // "line" | "column"
  categories: string[];
  series: { name: string; data: number[] }[];
  color?: string;
}>();

const proxy = getCurrentInstance()?.proxy;
let chart: any = null;

function render() {
  if (!proxy) return;
  const query = uni.createSelectorQuery().in(proxy);
  query
    .select("#" + props.canvasId)
    .boundingClientRect((rect: any) => {
      if (!rect || !rect.width) return;
      const ctx = uni.createCanvasContext(props.canvasId, proxy);
      chart = new uCharts({
        type: props.type,
        context: ctx,
        width: rect.width,
        height: rect.height,
        categories: props.categories,
        series: props.series,
        animation: true,
        background: "#FFFFFF",
        color: [props.color || "#2a78d6"],
        padding: [15, 15, 0, 5],
        xAxis: {
          disableGrid: true,
          fontColor: "#898781",
          fontSize: 10,
          labelCount: 6,
        },
        yAxis: {
          gridType: "dash",
          gridColor: "#e1e0d9",
          fontColor: "#898781",
          fontSize: 10,
          data: [{ min: 0 }],
        },
        legend: { show: false },
        dataLabel: false,
        extra: {
          line: { type: "curve", width: 2 },
          column: { width: 14 },
        },
      });
    })
    .exec();
}

onMounted(() => {
  setTimeout(render, 200);
});
watch(() => props.categories, () => {
  setTimeout(render, 80);
});
</script>

<style>
.chart-wrap {
  width: 100%;
}
.chart-canvas {
  width: 100%;
  height: 400rpx;
}
</style>
