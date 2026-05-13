import { post, get, put } from '@/utils/request'

export const messageApi = {
  sendMessage(toUserId, content, type = 'text') {
    return post('/api/message/send', { toUserId, content, type })
  },

  getConversationList() {
    return get('/api/message/conversations')
  },

  getMessageHistory(userId, params) {
    return get(`/api/message/history/${userId}`, params)
  },

  markAsRead(userId) {
    return put('/api/message/mark-read', { userId })
  },

  getUnreadCount() {
    return get('/api/message/unread-count')
  },

  deleteConversation(userId) {
    return del(`/api/message/conversation/${userId}`)
  }
}
