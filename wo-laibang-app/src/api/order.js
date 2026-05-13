import { post, get, put } from '@/utils/request'

export const orderApi = {
  createOrder(needId) {
    return post('/api/order/create', { needId })
  },

  getOrderList(params) {
    return get('/api/order/list', params)
  },

  getOrderDetail(orderId) {
    return get(`/api/order/detail/${orderId}`)
  },

  acceptOrder(orderId) {
    return put(`/api/order/accept/${orderId}`)
  },

  completeOrder(orderId) {
    return put(`/api/order/complete/${orderId}`)
  },

  confirmComplete(orderId) {
    return put(`/api/order/confirm/${orderId}`)
  },

  cancelOrder(orderId, reason) {
    return put('/api/order/cancel', { orderId, reason })
  },

  rateOrder(orderId, rating, comment) {
    return post('/api/order/rate', { orderId, rating, comment })
  },

  getOrderTimeline(orderId) {
    return get(`/api/order/timeline/${orderId}`)
  },

  applyPlatformIntervention(orderId, reason) {
    return post('/api/order/intervention', { orderId, reason })
  }
}
