import websocketService from './websocket'
import pushService from './push'
import { storage, StorageKeys } from './storage'

class ApiService {
  constructor() {
    this.ws = websocketService
    this.push = pushService
  }

  async init() {
    const isLoggedIn = storage.getBoolean(StorageKeys.IS_LOGGED_IN)
    if (isLoggedIn) {
      await this.initPush()
      this.initWebSocket()
    }
  },

  async initPush() {
    try {
      await this.push.init()
    } catch (e) {
      console.error('ApiService: initPush failed', e)
    }
  }

  initWebSocket() {
    try {
      this.ws.connect()
    } catch (e) {
      console.error('ApiService: initWebSocket failed', e)
    }
  }

  disconnect() {
    this.ws.disconnect()
  }

  onWsMessage(callback) {
    this.ws.on('message', callback)
  }

  onWsNotification(callback) {
    this.ws.on('notification', callback)
  }

  onWsOrderUpdate(callback) {
    this.ws.on('order_update', callback)
  }

  onWsWalletUpdate(callback) {
    this.ws.on('wallet_update', callback)
  }
}

const apiService = new ApiService()

export default apiService
