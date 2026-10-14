/* 共享店铺名称，并从后端读取可公开展示的配置。 */

import { ref } from 'vue'
import { get } from './request.js'

const DEFAULT_SHOP_NAME = '剧本杀店铺'
export const shopName = ref(DEFAULT_SHOP_NAME)

/* 加载店铺名称，配置缺失或请求失败时使用通用名称。 */
export async function loadShopInfo() {
  try {
    const res = await get('/api/system/info')
    const name = res.data?.shop_name
    shopName.value = typeof name === 'string' && name.trim() ? name.trim() : DEFAULT_SHOP_NAME
  } catch {
    shopName.value = DEFAULT_SHOP_NAME
  }
}
