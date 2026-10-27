import { reactive } from 'vue'

export interface AuthUser {
  type: string
  username: string
  merchant_id?: number
  features: string[]
}

const state = reactive<{ token: string; user: AuthUser | null }>({
  token: localStorage.getItem('token') || '',
  user: JSON.parse(localStorage.getItem('user') || 'null'),
})

export function setAuth(token: string, user: AuthUser) {
  state.token = token
  state.user = user
  localStorage.setItem('token', token)
  localStorage.setItem('user', JSON.stringify(user))
}

export function logout() {
  state.token = ''
  state.user = null
  localStorage.removeItem('token')
  localStorage.removeItem('user')
}

export function hasFeature(code: string) {
  return (state.user?.features || []).includes(code)
}
export function isAdmin() {
  return state.user?.type === 'admin'
}

export default state
