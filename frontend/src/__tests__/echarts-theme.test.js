import { describe, it, expect, vi } from 'vitest'

const styleMap = {
  '--color-text-tertiary': '#888',
  '--font-sans': 'Inter, sans-serif',
  '--color-bg-overlay': '#242429',
  '--color-border-default': '#333',
  '--color-text-secondary': '#ccc',
  '--color-border-light': '#444',
  '--color-border-subtle': 'rgba(255,255,255,0.06)',
}

// Mock getComputedStyle to return a CSSStyleDeclaration-like object
const mockGetComputedStyle = vi.fn(() => ({
  getPropertyValue: vi.fn((name) => styleMap[name] || ''),
}))

Object.defineProperty(globalThis, 'getComputedStyle', { value: mockGetComputedStyle })

describe('darkChartOptions', () => {
  it('returns correct default structure', async () => {
    const { darkChartOptions } = await import('@/utils/echarts-theme')
    const opts = darkChartOptions()
    expect(opts.backgroundColor).toBe('transparent')
    expect(opts.textStyle.color).toBe('#888')
    expect(opts.tooltip.backgroundColor).toBe('#242429')
    expect(opts.grid.containLabel).toBe(true)
  })

  it('merges overrides', async () => {
    const { darkChartOptions } = await import('@/utils/echarts-theme')
    const opts = darkChartOptions({ grid: { left: 50 }, tooltip: { trigger: 'axis' } })
    expect(opts.grid.left).toBe(50)
    expect(opts.tooltip.trigger).toBe('axis')
  })
})
