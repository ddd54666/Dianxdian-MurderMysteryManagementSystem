/* 二级密码解锁状态检查工具 */

/* 解锁有效期 3 分钟 */
const UNLOCK_DURATION = 3 * 60 * 1000

/* 检查当前是否已解锁 */
export function isUnlocked() {
  const ts = sessionStorage.getItem('pwd_unlocked_at')
  if (!ts) return false
  return Date.now() - parseInt(ts) < UNLOCK_DURATION
}

/* 清除解锁状态 */
export function clearUnlock() {
  sessionStorage.removeItem('pwd_unlocked_at')
}
