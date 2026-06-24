import CONFIG from './config'
import { storage, StorageKeys } from './storage'

class WebSocketService {
  constructor() {
    this.socket = null
    this.isConnected = false
    this.isManualClose = false
    this.reconnectAttempts = 0
    this.maxReconnectAttempts = 5
    this.baseReconnectDelay = 1000
    this.maxReconnectDelay = 30000
    this.heartbeatInterval = null
    this.listeners = new Map()
    this.messageQueue = []
  }

  connect() {
    if (this.isConnected) return
    if (this.isManualClose) return

    if (CONFIG.USE_MOCK) {
      console.log('WebSocket: Skipped in mock mode')
      return
    }

    const token = storage.get(StorageKeys.TOKEN)
    if (!token) {
      console.warn('WebSocket: No token available')
      return
    }

    const wsUrl = CONFIG.WS_BASE_URL || 'wss://api.wolaibang.com'

    this.socket = uni.connectSocket({
      url: `${wsUrl}/ws?token=${token}`,
      success: () => {
        console.log('WebSocket: Connecting...')
      },
      fail: (err) => {
        console.error('WebSocket: Connection failed', err)
        this.scheduleReconnect()
      }
    })

    this.socket.onOpen(() => {
      console.log('WebSocket: Connected')
      this.isConnected = true
      this.reconnectAttempts = 0
      this.startHeartbeat()
      this.flushMessageQueue()
      this.emit('connect', null)
    })

    this.socket.onMessage((res) => {
      try {
        const data = JSON.parse(res.data)
        this.handleMessage(data)
      } catch (e) {
        console.error('WebSocket: Failed to parse message', e)
      }
    })

    this.socket.onClose(() => {
      console.log('WebSocket: Closed')
      this.isConnected = false
      this.stopHeartbeat()
      this.emit('disconnect', null)
      if (!this.isManualClose) {
        this.scheduleReconnect()
      }
    })

    this.socket.onError((err) => {
      console.error('WebSocket: Error', err)
      this.emit('error', err)
    })
  }

  handleMessage(data) {
    const { type, payload } = data

    switch (type) {
      case 'ping':
        this.send({ type: 'pong' })
        break
      case 'message':
        this.emit('message', payload)
        this.emit('chat_message', payload)
        break
      case 'notification':
        this.emit('notification', payload)
        this.emit('system_notification', payload)
        break
      case 'order_update':
        this.emit('order_update', payload)
        break
      case 'wallet_update':
        this.emit('wallet_update', payload)
        break
      default:
        this.emit(type, payload)
    }
  }

  send(data) {
    const message = JSON.stringify(data)
    if (this.isConnected && this.socket) {
      this.socket.send({
        data: message,
        fail: (err) => {
          console.error('WebSocket: Send failed', err)
        }
      })
    } else {
      this.messageQueue.push(message)
    }
  }

  scheduleReconnect() {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.log('WebSocket: Max reconnect attempts reached')
      this.emit('reconnect_failed', null)
      return
    }

    this.reconnectAttempts++
    const delay = Math.min(
      this.baseReconnectDelay * Math.pow(2, this.reconnectAttempts - 1),
      this.maxReconnectDelay
    )
    console.log(`WebSocket: Reconnecting in ${delay}ms (attempt ${this.reconnectAttempts})`)

    setTimeout(() => {
      this.connect()
    }, delay)
  }

  startHeartbeat() {
    this.stopHeartbeat()
    this.heartbeatInterval = setInterval(() => {
      this.send({ type: 'ping' })
    }, 30000)
  }

  stopHeartbeat() {
    if (this.heartbeatInterval) {
      clearInterval(this.heartbeatInterval)
      this.heartbeatInterval = null
    }
  }

  flushMessageQueue() {
    while (this.messageQueue.length > 0) {
      const message = this.messageQueue.shift()
      this.send(JSON.parse(message))
    }
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
        console.error(`WebSocket: Listener error for ${event}`, e)
      }
    })
  }

  sendMessage(toUserId, content, type = 'text') {
    this.send({
      type: 'message',
      payload: {
        toUserId,
        content,
        messageType: type,
        timestamp: Date.now()
      }
    })
  }

  sendImageMessage(toUserId, imageUrl) {
    this.sendMessage(toUserId, imageUrl, 'image')
  }

  markAsRead(messageId) {
    this.send({
      type: 'mark_read',
      payload: { messageId }
    })
  }

  disconnect() {
    this.isManualClose = true
    this.stopHeartbeat()
    this.reconnectAttempts = this.maxReconnectAttempts
    if (this.socket) {
      this.socket.close()
      this.socket = null
    }
    this.isConnected = false
    this.listeners.clear()
    this.messageQueue = []
  }

  reconnect() {
    this.isManualClose = false
    this.reconnectAttempts = 0
    this.connect()
  }
}

const websocketService = new WebSocketService()

export default websocketService
