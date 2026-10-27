import axios from 'axios'

const http = axios.create({ baseURL: '/api/v1', timeout: 15000 })

// 请求拦截：自动带 token
http.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

// 响应拦截：401 跳登录
http.interceptors.response.use(
  (r) => r,
  (err) => {
    if (err.response?.status === 401) {
      localStorage.removeItem('token')
      localStorage.removeItem('user')
      if (window.location.pathname !== '/login') window.location.href = '/login'
    }
    return Promise.reject(err)
  },
)

// ---------- 看板 ----------
export interface KpiSummary {
  date: string
  revenue: string
  order_count: number
  valid_order_count: number
  avg_order_value: string
  valid_rate: string
  revenue_change_pct: string | null
  order_count_change_pct: string | null
  avg_order_value_change_pct: string | null
}

export interface TrendItem {
  date: string
  revenue: string
  order_count: number
}
export interface TrendResp {
  days: number
  items: TrendItem[]
}

export interface ProductItem {
  id: number
  name: string
  category: string | null
  price: string
  sales: number
  stock: number
  status: string
}
export interface ProductsResp {
  hot: ProductItem[]
  slow: ProductItem[]
  sold_out: ProductItem[]
}

export interface AlertItem {
  id: number
  rule: string
  level: string
  payload: string | null
  triggered_at: string | null
}
export interface AlertsResp {
  items: AlertItem[]
}

export interface RatingItem {
  date: string
  avg_rating: number
  count: number
}

export interface WordItem {
  word: string
  count: number
}
export interface WordFreqResp {
  positive: WordItem[]
  negative: WordItem[]
}

// ---------- 订单 ----------
export interface OrderListItem {
  id: number
  order_no: string
  status: string
  status_label: string
  total_amount: string
  placed_at: string
  is_valid: boolean
  item_count: number
  review_id: number | null
  review_rating: number | null
}
export interface OrdersResp {
  total: number
  items: OrderListItem[]
  statuses: { value: string; label: string }[]
}

// ---------- 商品 ----------
export interface CategoryItem {
  id: number
  name: string
}
export interface ProductListItem {
  id: number
  name: string
  category_id: number
  category: string | null
  price: string
  stock: number
  sales: number
  status: string
}

// ---------- 评价 ----------
export interface ReviewListItem {
  id: number
  rating: number
  content: string | null
  tags: string | null
  reply: string | null
  replied_at: string | null
  created_at: string | null
  order_no: string | null
}

// ---------- 预警 ----------
export interface AlertListItem {
  id: number
  rule: string
  level: string
  status: string
  payload: string | null
  triggered_at: string | null
}

// ---------- AI / IM ----------
export interface AiImReplyResp {
  intent: string
  confidence: number
  action: string
  status: string
  reply: string
  source: string  // 'faq' | 'llm'
  auto_sent: boolean
}
export interface SessionItem {
  id: number
  customer_id: number
  last_message: string
  message_count: number
  unhandled_count: number
  updated_at: string | null
}
export interface MessageItem {
  id: number
  content: string
  direction: string
  msg_id: string | null
  scene_tag: string | null
  is_urgent: boolean
  is_handled: boolean
  created_at: string | null
}

export const api = {
  // 鉴权
  login: (username: string, password: string, role: string) =>
    http.post('/auth/login', { username, password, role }).then((r) => r.data),
  me: () => http.get('/auth/me').then((r) => r.data),

  // 看板
  summary: () => http.get<KpiSummary>('/dashboard/summary').then((r) => r.data),
  trend: (days = 30) => http.get<TrendResp>('/dashboard/trend', { params: { days } }).then((r) => r.data),
  products: () => http.get<ProductsResp>('/dashboard/products').then((r) => r.data),
  alerts: () => http.get<AlertsResp>('/dashboard/alerts').then((r) => r.data),
  ratingTrend: (days = 30) =>
    http.get<{ items: RatingItem[] }>('/dashboard/rating-trend', { params: { days } }).then((r) => r.data),
  wordFrequency: (days = 30) =>
    http.get<WordFreqResp>('/dashboard/word-frequency', { params: { days } }).then((r) => r.data),

  // 分析
  hourly: (days = 30) => http.get('/analytics/hourly', { params: { days } }).then((r) => r.data),
  ratingDistribution: (days = 30) =>
    http.get('/analytics/rating-distribution', { params: { days } }).then((r) => r.data),
  sentimentTrend: (days = 30) =>
    http.get('/analytics/sentiment-trend', { params: { days } }).then((r) => r.data),

  // 订单
  listOrders: (params: { status?: string; page?: number; page_size?: number }) =>
    http.get<OrdersResp>('/orders', { params }).then((r) => r.data),
  confirmOrders: (ids: number[]) =>
    http.post<{ updated: number }>('/orders/batch-confirm', { ids }).then((r) => r.data),
  getOrder: (id: number) => http.get(`/orders/${id}`).then((r) => r.data),

  // 商品
  listCategories: () => http.get<{ items: CategoryItem[] }>('/categories').then((r) => r.data),
  listProducts: (params: { category_id?: number; status?: string; q?: string }) =>
    http.get<{ items: ProductListItem[] }>('/products', { params }).then((r) => r.data),
  updateProducts: (payload: { ids: number[]; action: string; price?: number }) =>
    http.post<{ updated: number }>('/products/batch', payload).then((r) => r.data),

  // 评价
  listReviews: (params: { rating?: number; replied?: boolean; page?: number; page_size?: number }) =>
    http.get<{ total: number; items: ReviewListItem[] }>('/reviews', { params }).then((r) => r.data),
  replyReview: (id: number, content: string) =>
    http.post(`/reviews/${id}/reply`, { content }).then((r) => r.data),

  // 预警
  listAlerts: () => http.get<{ items: AlertListItem[] }>('/alerts').then((r) => r.data),
  resolveAlert: (id: number) => http.post(`/alerts/${id}/resolve`).then((r) => r.data),

  // AI
  aiReviewReply: (rating: number, content: string) =>
    http.post<{ draft: string }>('/ai/review-reply', { rating, content }).then((r) => r.data),
  aiImReply: (message: string, session_id?: number) =>
    http.post<AiImReplyResp>('/ai/im-reply', { message, session_id }).then((r) => r.data),

  // IM
  listSessions: () => http.get<{ items: SessionItem[] }>('/im/sessions').then((r) => r.data),
  listMessages: (sessionId: number) =>
    http.get<{ items: MessageItem[] }>(`/im/sessions/${sessionId}/messages`).then((r) => r.data),
  addMessage: (sessionId: number, content: string, direction: string) =>
    http.post(`/im/sessions/${sessionId}/messages`, { content, direction }).then((r) => r.data),
  urgentMessages: () => http.get<{ items: any[] }>('/im/urgent-messages').then((r) => r.data),
  handleMessage: (id: number) => http.post(`/im/messages/${id}/handle`).then((r) => r.data),

  // 管理后台
  listFeatures: () => http.get('/admin/features').then((r) => r.data),
  listPlans: () => http.get('/admin/plans').then((r) => r.data),
  createPlan: (payload: any) => http.post('/admin/plans', payload).then((r) => r.data),
  updatePlan: (id: number, payload: any) => http.put(`/admin/plans/${id}`, payload).then((r) => r.data),
  deletePlan: (id: number) => http.delete(`/admin/plans/${id}`).then((r) => r.data),
  listMerchants: () => http.get('/admin/merchants').then((r) => r.data),
  createMerchant: (payload: any) => http.post('/admin/merchants', payload).then((r) => r.data),
  setMerchantStatus: (id: number, status: string) =>
    http.put(`/admin/merchants/${id}/status`, { status }).then((r) => r.data),
  listSubscriptions: () => http.get('/admin/subscriptions').then((r) => r.data),
  assignSubscription: (payload: any) => http.post('/admin/subscriptions', payload).then((r) => r.data),

  // 商家端设置
  getSettings: () => http.get('/settings').then((r) => r.data),
  updateStore: (payload: any) => http.put('/settings/store', payload).then((r) => r.data),
  updateAiSettings: (payload: any) => http.put('/settings/ai', payload).then((r) => r.data),
  createFaq: (payload: any) => http.post('/settings/faqs', payload).then((r) => r.data),
  updateFaq: (id: number, payload: any) => http.put(`/settings/faqs/${id}`, payload).then((r) => r.data),
  deleteFaq: (id: number) => http.delete(`/settings/faqs/${id}`).then((r) => r.data),
  changePassword: (payload: any) => http.post('/settings/password', payload).then((r) => r.data),

  // 数据刷新
  refreshData: () => http.post('/refresh').then((r) => r.data),
  refreshStatus: () => http.get('/refresh/status').then((r) => r.data),
}
