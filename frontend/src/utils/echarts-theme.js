/**
 * MRP II — ECharts 暗色主题配置
 * 统一管理图表样式，通过 CSS 变量与全局设计 Token 联动
 */

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

    // ── 通用工具提示 ──
    tooltip: {
      backgroundColor: cssVar('--color-bg-overlay') || '#242429',
      borderColor: cssVar('--color-border-default') || '#333',
      borderWidth: 1,
      borderRadius: 8,
      textStyle: {
        color: cssVar('--color-text-secondary') || '#ccc',
        fontSize: 12,
      },
      extraCssText: 'box-shadow: 0 4px 16px rgba(0,0,0,0.5);',
      ...overrides.tooltip,
    },

    // ── 图例 ──
    legend: {
      textStyle: {
        color: cssVar('--color-text-tertiary') || '#888',
        fontSize: 11,
      },
      itemWidth: 10,
      itemHeight: 10,
      itemGap: 16,
      ...overrides.legend,
    },

    // ── X 轴 ──
    xAxis: {
      axisLine: { lineStyle: { color: cssVar('--color-border-light') || '#333' } },
      axisTick: { show: false },
      axisLabel: {
        color: cssVar('--color-text-tertiary') || '#888',
        fontSize: 11,
      },
      splitLine: { show: false },
      ...overrides.xAxis,
    },

    // ── Y 轴 ──
    yAxis: {
      axisLine: { show: false },
      axisTick: { show: false },
      axisLabel: {
        color: cssVar('--color-text-tertiary') || '#888',
        fontSize: 11,
      },
      splitLine: {
        lineStyle: {
          color: cssVar('--color-border-subtle') || 'rgba(255,255,255,0.06)',
          type: 'dashed',
        },
      },
      ...overrides.yAxis,
    },

    // ── 网格 ──
    grid: {
      left: 8,
      right: 16,
      top: 8,
      bottom: 24,
      containLabel: true,
      ...overrides.grid,
    },

    // ── 饼图通用 ──
    ...(overrides.series ? { series: overrides.series } : {}),
  }
}

/** 语义色色板 */
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

/** 工单状态 → 颜色映射 */
export const woStatusColors = {
  '待下达': chartColors.gray,
  '已下达': chartColors.amber,
  '进行中': chartColors.blue,
  '已完成': chartColors.green,
  '已关闭': chartColors.red,
}

/** 物料类型 → 颜色映射 */
export const materialTypeColors = {
  '成品': chartColors.blue,
  '半成品': chartColors.purple,
  '零件': chartColors.green,
  '原材料': chartColors.amber,
  '模块': chartColors.cyan,
}
