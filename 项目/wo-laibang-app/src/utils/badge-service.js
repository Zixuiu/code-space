import { storage, StorageKeys } from './storage'

const MESSAGE_TAB_INDEX = 3

class BadgeService {
  constructor() {
    this.tabIndex = MESSAGE_TAB_INDEX
  }

  getUnreadCount() {
    const notifications = storage.getArray(StorageKeys.NOTIFICATIONS, [])
    const unreadNotifications = notifications.filter(n => !n.read).length

    const conversations = storage.getArray(StorageKeys.CONVERSATIONS, [])
    const unreadMessages = conversations.reduce((sum, c) => sum + (c.unread || 0), 0)

    return unreadNotifications + unreadMessages
  }

  updateTabBarBadge() {
    const totalUnread = this.getUnreadCount()

    if (totalUnread > 0) {
      uni.setTabBarBadge({
        index: this.tabIndex,
        text: totalUnread > 99 ? '99+' : String(totalUnread),
        fail: (err) => {
          console.warn('BadgeService: setTabBarBadge failed', err)
        }
      })
    } else {
      uni.removeTabBarBadge({
        index: this.tabIndex,
        fail: (err) => {
          console.warn('BadgeService: removeTabBarBadge failed', err)
        }
      })
    }

    storage.set(StorageKeys.TOTAL_UNREAD_COUNT, totalUnread)
    uni.$emit('updateBadge')
  }

  setupListeners() {
    uni.$on('updateMessageBadge', () => {
      this.updateTabBarBadge()
    })
    uni.$on('clearMessageBadge', () => {
      this.updateTabBarBadge()
    })
  }
}

const badgeService = new BadgeService()

export default badgeService
