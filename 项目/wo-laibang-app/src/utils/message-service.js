import { storage, StorageKeys } from './storage'
import badgeService from './badge-service'
import websocketService from './websocket'

class MessageService {
  constructor() {
    this.listeners = new Map()
    this.wsBound = false
  }

  getConversations() {
    return storage.getArray(StorageKeys.CONVERSATIONS, [])
  }

  saveConversations(conversations) {
    storage.set(StorageKeys.CONVERSATIONS, conversations)
  }

  getConversation(userId) {
    const conversations = this.getConversations()
    return conversations.find(c => c.userId === userId) || null
  }

  incrementUnreadForIncomingMessage(payload) {
    if (!payload || !payload.fromUserId) return

    const conversations = this.getConversations()
    const convIndex = conversations.findIndex(c => c.userId === payload.fromUserId)

    if (convIndex >= 0) {
      conversations[convIndex].unread = (conversations[convIndex].unread || 0) + 1
      conversations[convIndex].lastMessage = payload.content
      conversations[convIndex].lastTime = payload.timestamp || Date.now()
    } else {
      conversations.unshift({
        id: `conv_${payload.fromUserId}`,
        userId: payload.fromUserId,
        nickname: payload.fromNickname || '未知用户',
        lastMessage: payload.content,
        lastTime: payload.timestamp || Date.now(),
        unread: 1,
        online: true
      })
    }

    this.saveConversations(conversations)
    badgeService.updateTabBarBadge()
  }

  markConversationAsRead(userId) {
    const conversations = this.getConversations()
    const convIndex = conversations.findIndex(c => c.userId === userId)
    if (convIndex >= 0) {
      conversations[convIndex].unread = 0
      this.saveConversations(conversations)
      badgeService.updateTabBarBadge()
    }
  }

  updateLastMessage(userId, content, timestamp) {
    const conversations = this.getConversations()
    const convIndex = conversations.findIndex(c => c.userId === userId)
    if (convIndex >= 0) {
      conversations[convIndex].lastMessage = content
      conversations[convIndex].lastTime = timestamp || Date.now()
      this.saveConversations(conversations)
    }
  }

  clearAllUnread() {
    const conversations = this.getConversations()
    conversations.forEach(c => {
      c.unread = 0
    })
    this.saveConversations(conversations)
    badgeService.updateTabBarBadge()
  }

  bindWebSocketListeners() {
    if (this.wsBound) return

    websocketService.on('chat_message', (payload) => {
      this.incrementUnreadForIncomingMessage(payload)
      this.emit('chat_message', payload)
    })

    websocketService.on('notification', (payload) => {
      badgeService.updateTabBarBadge()
      this.emit('notification', payload)
    })

    this.wsBound = true
  }

  on(event, callback) {
    if (!this.listeners.has(event)) {
      this.listeners.set(event, [])
    }
    this.listeners.get(event).push(callback)
  }

  off(event, callback) {
    if (!this.listeners.has(event)) return
    const callbacks = this.listeners.get(event)
    const index = callbacks.indexOf(callback)
    if (index > -1) {
      callbacks.splice(index, 1)
    }
  }

  emit(event, data) {
    if (!this.listeners.has(event)) return
    this.listeners.get(event).forEach(callback => {
      try {
        callback(data)
      } catch (e) {
        console.error(`MessageService: Listener error for ${event}`, e)
      }
    })
  }
}

const messageService = new MessageService()

export default messageService
