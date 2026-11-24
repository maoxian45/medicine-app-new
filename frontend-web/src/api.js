export async function api(path, options = {}) {
  const key = path.startsWith('/admin/') ? 'admin_token' : 'family_token'
  const token = sessionStorage.getItem(key)
  const response = await fetch(`/api${path}`, {
    ...options, headers: { 'Content-Type': 'application/json', ...(token ? { Authorization: `Bearer ${token}` } : {}), ...options.headers },
  })
  if (!response.ok) {
    if(response.status === 401 && !path.startsWith('/auth/')) {
      sessionStorage.removeItem(key)
      window.dispatchEvent(new CustomEvent('auth-expired', {detail:key}))
    }
    const body = await response.json().catch(() => ({}))
    const details = Array.isArray(body.detail)
      ? body.detail.map(({loc, msg}) => `${loc.slice(1).join('.')}: ${msg}`).join('；')
      : body.detail
    const error = new Error(typeof details === 'string' ? details : '请求失败，请检查输入或后端连接')
    error.status = response.status
    throw error
  }
  return response.status === 204 ? null : response.json()
}
export const post = (path, body) => api(path, { method: 'POST', body: JSON.stringify(body) })
