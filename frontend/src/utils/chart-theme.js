/* ECharts 统一主题与工具函数，匹配项目类纸白茶棕风格。 */

import * as echarts from 'echarts'

/* 项目色板 */
export const COLORS = {
  primary: '#8B7355',
  primaryLight: '#C4B2A0',
  accent1: '#C4A35A',
  accent2: '#6B8E6B',
  accent3: '#7B8EA3',
  accent4: '#C46B5A',
  accent5: '#A8907A',
  text: '#5C4F3E',
  textDim: '#8C7B6B',
  grid: '#E5DDD0',
  bg: '#FDFBF7'
}

/* 通用图表基础配置 */
export function baseOption(overrides = {}) {
  return {
    animationDuration: 600,
    animationEasing: 'cubicOut',
    textStyle: { fontFamily: '"SimSun","STSong","宋体",serif', color: COLORS.text },
    tooltip: {
      backgroundColor: '#FDFBF7',
      borderColor: COLORS.grid,
      textStyle: { fontFamily: '"SimSun","STSong","宋体",serif', color: COLORS.text, fontSize: 13 },
      ...overrides.tooltip
    },
    grid: { left: '3%', right: '5%', bottom: '10%', top: '15%', containLabel: true },
    ...overrides
  }
}

/* 创建图表实例并自动处理 resize */
export function createChart(domRef) {
  if (!domRef.value) return null
  const instance = echarts.init(domRef.value)
  const resize = () => instance.resize()
  window.addEventListener('resize', resize)
  /* 存储 cleanup 引用 */
  instance._resizeCleanup = () => window.removeEventListener('resize', resize)
  return instance
}

/* 销毁图表实例 */
export function disposeChart(instance) {
  if (!instance) return
  if (instance._resizeCleanup) instance._resizeCleanup()
  instance.dispose()
}

/* 金额格式化（分转元，ECharts tooltip 用） */
export function formatFen(val) {
  return (val / 100).toFixed(2) + ' 元'
}
