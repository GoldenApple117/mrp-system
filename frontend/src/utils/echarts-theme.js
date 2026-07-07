/**
 * MRP II — ECharts 暗色主题配置
 * 统一管理图表样式，通过 CSS 变量与全局设计 Token 联动
 * 按需导入图表和组件，避免全量引入
 */

// ── 按需导入 ECharts 核心 ──
import * as echarts from 'echarts/core'
import { BarChart, PieChart } from 'echarts/charts'
import {
  TitleComponent,
  TooltipComponent,
  LegendComponent,
  GridComponent,
  DatasetComponent,
} from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'

echarts.use([
  BarChart,
  PieChart,
  TitleComponent,
  TooltipComponent,
  LegendComponent,
  GridComponent,
  DatasetComponent,
  CanvasRenderer,
])

export { echarts }

// ── 从 CSS 变量读取 ──
function cssVar(name) {
  return getComputedStyle(document.documentElement).getPropertyValue(name).trim()
}

export function darkChartOptions(overrides = {}) {
  return {
    backgroundColor: 'transparent',
    textStyle: {
      color: cssVar('--color-text-tertiary') || '#888',
      fontFamily: cssVar('--font-sans') || 'sans-serif',
      fontSize: 12,
    },
    tooltip: {
      backgroundColor: cssVar('--color-bg-overlay') || '#242429',
      borderColor: cssVar('--color-border-default') || '#333',
      borderWidth: 1,
      borderRadius: 8,
      textStyle: { color: cssVar('--color-text-secondary') || '#ccc', fontSize: 12 },
      extraCssText: 'box-shadow: 0 4px 16px rgba(0,0,0,0.5);',
      ...overrides.tooltip,
    },
    legend: {
      textStyle: { color: cssVar('--color-text-tertiary') || '#888', fontSize: 11 },
      itemWidth: 10,
      itemHeight: 10,
      itemGap: 16,
      ...overrides.legend,
    },
    xAxis: {
      axisLine: { lineStyle: { color: cssVar('--color-border-light') || '#333' } },
      axisTick: { show: false },
      axisLabel: { color: cssVar('--color-text-tertiary') || '#888', fontSize: 11 },
      splitLine: { show: false },
      ...overrides.xAxis,
    },
    yAxis: {
      axisLine: { show: false },
      axisTick: { show: false },
      axisLabel: { color: cssVar('--color-text-tertiary') || '#888', fontSize: 11 },
      splitLine: {
        lineStyle: {
          color: cssVar('--color-border-subtle') || 'rgba(255,255,255,0.06)',
          type: 'dashed',
        },
      },
      ...overrides.yAxis,
    },
    grid: { left: 8, right: 16, top: 8, bottom: 24, containLabel: true, ...overrides.grid },
    ...(overrides.series ? { series: overrides.series } : {}),
  }
}

export const chartColors = {
  blue: '#3b82f6',
  green: '#22c55e',
  amber: '#f59e0b',
  red: '#ef4444',
  purple: '#8b5cf6',
  cyan: '#06b6d4',
  gray: '#6b7280',
  pink: '#ec4899',
}

export const woStatusColors = {
  待下达: '#6b7280',
  已下达: '#f59e0b',
  进行中: '#3b82f6',
  已完成: '#22c55e',
  已关闭: '#ef4444',
}

export const materialTypeColors = {
  成品: '#3b82f6',
  半成品: '#8b5cf6',
  零件: '#22c55e',
  原材料: '#f59e0b',
  模块: '#06b6d4',
}
