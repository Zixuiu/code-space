import CONFIG from './config'

class PushService {
  constructor() {
    this.clientId = ''
    this.isInit = false
  }

  async init() {
    if (this.isInit) return

    const platform = uni.getSystemInfoSync().platform

    if (platform === 'ios') {
      await this.initIosPush()
    } else if (platform === 'android') {
      await this.initAndroidPush()
    }

    this.isInit = true
  }

  async initIosPush() {
    const info = await this.getPushInfo()
    this.clientId = info.clientId

    uni.setStorageSync('pushClientId', this.clientId)

    return this.clientId
  }

  async initAndroidPush() {
    const jpushModule = uni.requireNativePlugin('JG-JPush')

    if (jpushModule) {
      jpushModule.init()

      jpushModule.addPushReceiver((result) => {
        this.handlePushMessage(result)
      })

      const registrationId = jpushModule.getRegistrationID()
      if (registrationId) {
        this.clientId = registrationId
        uni.setStorageSync('pushClientId', this.clientId)
        this.reportClientId(registrationId)
      }
    }

    return this.clientId
  }

  handlePushMessage(result) {
    const { title, content, extras } = result

    const notification = {
      id: Date.now(),
      title: title || '我来帮',
      content: content || '',
      type: extras?.type || 'system',
      data: extras || {},
      read: false,
      createdAt: Date.now()
    }

    this.saveNotification(notification)

    this.handleNotificationAction(notification)
  }

  handleNotificationAction(notification) {
    const { type, data } = notification

    switch (type) {
      case 'order':
        if (data.orderId) {
          uni.navigateTo({
            url: `/pages/order-detail/order-detail?orderId=${data.orderId}`
          })
        }
        break
      case 'message':
        if (data.chatId) {
          uni.navigateTo({
            url: `/pages/chat/chat?chatId=${data.chatId}`
          })
        }
        break
      case 'wallet':
        uni.switchTab({ url: '/pages/wallet/wallet' })
        break
      default:
        uni.navigateTo({ url: '/pages/notifications/notifications' })
    }
  }

  saveNotification(notification) {
    const notifications = uni.getStorageSync('notifications') || []
    notifications.unshift(notification)
    if (notifications.length > 100) {
      notifications.splice(100)
    }
    uni.setStorageSync('notifications', notifications)

    this.updateTabBarBadge()
  }

  updateTabBarBadge() {
    const notifications = uni.getStorageSync('notifications') || []
    const unreadCount = notifications.filter(n => !n.read).length

    if (unreadCount > 0) {
      uni.setTabBarBadge({
        index: 3,
        text: unreadCount > 99 ? '99+' : unreadCount.toString()
      })
    } else {
      uni.removeTabBarBadge({ index: 3 })
    }
  }

  async reportClientId(clientId) {
    if (!clientId) return

    try {
      const token = uni.getStorageSync('token')
      if (!token) return

      await uni.request({
        url: CONFIG.API_BASE_URL + '/api/user/bind-push',
        method: 'POST',
        data: {
          clientId,
          platform: uni.getSystemInfoSync().platform
        },
        header: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      })
    } catch (e) {
      console.error('PushService: reportClientId failed', e)
    }
  }

  async getPushInfo() {
    return new Promise((resolve) => {
      const info = uni.getPushClientId({
        success: (res) => {
          resolve({ clientId: res.clientId })
        },
        fail: () => {
          resolve({ clientId: '' })
        }
      })
      if (!info) {
        resolve({ clientId: '' })
      }
    })
  }

  setBadge(count) {
    uni.setTabBarBadge({
      index: 3,
      text: count > 99 ? '99+' : count.toString()
    })
  }

  clearBadge() {
    uni.removeTabBarBadge({ index: 3 })
  }

  async requestNotificationPermission() {
    if (uni.getSystemInfoSync().platform === 'ios') {
      const result = await new Promise((resolve) => {
        uni.requestNotificationPermission({
          success: (res) => {
            resolve(res)
          },
          fail: () => {
            resolve({ permission: 0 })
          }
        })
      })
      return result.permission === 1
    }
    return true
  }

  getSettings() {
    const settings = uni.getStorageSync('notificationSettings') || {
      orderEnabled: true,
      messageEnabled: true,
      systemEnabled: true,
      soundEnabled: true,
      vibrationEnabled: true
    }
    return settings
  }

  setSettings(settings) {
    uni.setStorageSync('notificationSettings', settings)
  }
}

const pushService = new PushService()

export function createOrderNotification(orderId, orderTitle, status, targetUserId) {
  const statusMessages = {
    'accepted': { title: '订单已被接单', content: '有新的帮手接单了，赶快去沟通吧' },
    'pending_confirm': { title: '订单待确认', content: '帮手已申请完成，等待您确认' },
    'completed': { title: '订单已完成', content: '双方已确认完成，订单已结束' },
    'cancelled': { title: '订单已取消', content: '订单已被取消' },
    'helper_confirmed': { title: '帮手已确认完成', content: '帮手已确认完成，等待您确认' },
    'publisher_confirmed': { title: '发布者已确认', content: '发布者已确认完成，订单即将结束' }
  }

  const messageInfo = statusMessages[status] || { title: '订单状态更新', content: '订单状态发生了变化' }

  const notification = {
    id: Date.now(),
    type: 'order',
    title: messageInfo.title,
    content: messageInfo.content,
    orderId: orderId,
    orderTitle: orderTitle,
    status: status,
    targetUserId: targetUserId,
    read: false,
    createdAt: Date.now()
  }

  const notifications = uni.getStorageSync('notifications') || []
  notifications.unshift(notification)
  if (notifications.length > 100) {
    notifications.splice(100)
  }
  uni.setStorageSync('notifications', notifications)

  pushService.updateTabBarBadge()

  return notification
}

export default pushService
