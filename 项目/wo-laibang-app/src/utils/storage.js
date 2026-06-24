export const StorageKeys = {
  TOKEN: 'token',
  REFRESH_TOKEN: 'refreshToken',
  IS_LOGGED_IN: 'isLoggedIn',
  CURRENT_USER: 'currentUser',
  USER_INFO: 'userInfo',
  HAS_SEEN_GUIDE: 'hasSeenGuide',
  REDIRECT_AFTER_LOGIN: 'redirectAfterLogin',
  CONVERSATIONS: 'conversations',
  CHAT_MESSAGES: 'chatMessages',
  NOTIFICATIONS: 'notifications',
  TOTAL_UNREAD_COUNT: 'totalUnreadCount',
  NEEDS: 'needs',
  ORDERS: 'orders',
  ORDER_RATINGS: 'orderRatings',
  WALLET_TRANSACTIONS: 'walletTransactions',
  CURRENT_SHARE_SOURCE: 'currentShareSource',
  REGISTERED_USERS: 'registeredUsers',
  VERIFY_DATA: 'verifyData',
  PUBLISH_DRAFT: 'publishDraft',
  REPUBLISH_DATA: 'republishData',
  LAST_PUBLISHED_NEED_ID: 'lastPublishedNeedId',
  PAY_PASSWORD: 'payPassword',
  PAY_PASSWORD_SET_TIME: 'payPasswordSetTime',
  HAS_DISMISSED_GPS: 'hasDismissedGps',
  GPS_ENABLED: 'gpsEnabled',
  USER_LOCATION: 'userLocation'
}

function safeGet(key, defaultValue = null) {
  try {
    const value = uni.getStorageSync(key)
    if (value === '' || value === undefined) return defaultValue
    return value
  } catch (e) {
    return defaultValue
  }
}

function safeSet(key, value) {
  try {
    uni.setStorageSync(key, value)
    return true
  } catch (e) {
    return false
  }
}

function safeRemove(key) {
  try {
    uni.removeStorageSync(key)
    return true
  } catch (e) {
    return false
  }
}

export const storage = {
  get(key, defaultValue = null) {
    return safeGet(key, defaultValue)
  },

  set(key, value) {
    return safeSet(key, value)
  },

  remove(key) {
    return safeRemove(key)
  },

  getJSON(key, defaultValue = null) {
    const raw = safeGet(key, null)
    if (raw === null || raw === undefined) return defaultValue
    if (typeof raw === 'object') return raw
    try {
      return JSON.parse(raw)
    } catch (e) {
      return defaultValue
    }
  },

  setJSON(key, value) {
    return safeSet(key, value)
  },

  getArray(key, defaultValue = []) {
    const val = safeGet(key, defaultValue)
    return Array.isArray(val) ? val : defaultValue
  },

  getObject(key, defaultValue = {}) {
    const val = safeGet(key, defaultValue)
    return val && typeof val === 'object' ? val : defaultValue
  },

  getNumber(key, defaultValue = 0) {
    const val = safeGet(key, defaultValue)
    const num = Number(val)
    return isNaN(num) ? defaultValue : num
  },

  getBoolean(key, defaultValue = false) {
    const val = safeGet(key, defaultValue)
    if (typeof val === 'boolean') return val
    if (val === 'true') return true
    if (val === 'false') return false
    return defaultValue
  },

  clearAll() {
    try {
      uni.clearStorageSync()
      return true
    } catch (e) {
      return false
    }
  }
}

export default storage
