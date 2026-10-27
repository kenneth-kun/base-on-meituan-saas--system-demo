<script setup lang="ts">
import * as echarts from 'echarts'
import type { EChartsOption } from 'echarts'
import { onBeforeUnmount, onMounted, ref, watch } from 'vue'

const props = defineProps<{ option: EChartsOption }>()

const el = ref<HTMLDivElement>()
let chart: echarts.ECharts | null = null

function render() {
  if (!chart && el.value) {
    chart = echarts.init(el.value)
  }
  if (chart) {
    chart.setOption(props.option, true)
  }
}

function resize() {
  chart?.resize()
}

onMounted(() => {
  render()
  window.addEventListener('resize', resize)
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', resize)
  chart?.dispose()
})

watch(() => props.option, render, { deep: true })
</script>

<template>
  <div ref="el" class="echart" />
</template>

<style scoped>
.echart {
  width: 100%;
  height: 100%;
}
</style>
