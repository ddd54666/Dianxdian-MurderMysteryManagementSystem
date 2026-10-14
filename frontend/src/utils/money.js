/* 金额元/分转换工具函数 */

/* 分转元（保留2位小数） */
export function toYuan(fen) {
  if (fen == null) return '0.00'
  return (fen / 100).toFixed(2)
}

/* 元转分（整数） */
export function toFen(yuan) {
  const val = parseFloat(yuan)
  if (isNaN(val)) return 0
  return Math.round(val * 100)
}
