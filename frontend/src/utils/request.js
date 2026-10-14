/* fetch 请求封装：统一 baseURL、JSON 解析、错误处理。 */

const BASE_URL = ''

/* 内部请求函数 */
async function request(url, options = {}) {
  const config = {
    headers: { 'Content-Type': 'application/json' },
    ...options
  }

  if (config.body && typeof config.body === 'object') {
    config.body = JSON.stringify(config.body)
  }

  const response = await fetch(BASE_URL + url, config)

  if (response.headers.get('Content-Type')?.includes('text/csv')) {
    return response
  }

  const data = await response.json()

  if (!response.ok) {
    const { ElMessage } = await import('element-plus')
    ElMessage.error(data.error || '请求失败')
    throw new Error(data.error || `HTTP ${response.status}`)
  }

  return data
}

/* 便捷方法 */
export function get(url, params = {}) {
  const query = new URLSearchParams()
  Object.entries(params).forEach(([k, v]) => {
    if (v !== undefined && v !== null && v !== '') {
      query.append(k, v)
    }
  })
  const qs = query.toString()
  return request(qs ? `${url}?${qs}` : url)
}

export function post(url, body = {}) {
  return request(url, { method: 'POST', body })
}

export function put(url, body = {}) {
  return request(url, { method: 'PUT', body })
}

export function del(url) {
  return request(url, { method: 'DELETE' })
}

export default { get, post, put, del }
