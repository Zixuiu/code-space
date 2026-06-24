import { storage, StorageKeys } from './storage'

export const NEED_LOGIN_PAGES = [
  '/pages/orders/orders',
  '/pages/wallet/wallet',
  '/pages/messages/messages',
  '/pages/recharge/recharge',
  '/pages/withdraw/withdraw',
  '/pages/transfer/transfer',
  '/pages/profile/profile',
  '/pages/edit-profile/edit-profile',
  '/pages/settings/settings',
  '/pages/verify/verify',
  '/pages/order-detail/order-detail',
  '/pages/accept-order/accept-order',
  '/pages/rate/rate',
  '/pages/skills/skills',
  '/pages/blacklist/blacklist',
  '/pages/received-help/received-help',
  '/pages/rating-history/rating-history',
  '/pages/notification-settings/notification-settings',
  '/pages/feedback/feedback',
  '/pages/transaction/transaction',
  '/pages/bind-alipay/bind-alipay',
  '/pages/bind-bank/bind-bank',
  '/pages/complaint/complaint',
  '/pages/complaint-list/complaint-list',
  '/pages/complaint-detail/complaint-detail'
]

const LOGIN_PAGE = '/pages/login/login'

export function extractPath(url) {
  if (url.startsWith('/')) {
    return url.split('?')[0]
  }
  return '/' + url.split('?')[0]
}

export function shouldCheckLogin(url) {
  const path = extractPath(url)
  const isNeedLogin = NEED_LOGIN_PAGES.some(page => path.startsWith(page))
  if (!isNeedLogin) return false

  const isLoggedIn = storage.getBoolean(StorageKeys.IS_LOGGED_IN, false)
  const token = storage.get(StorageKeys.TOKEN, '')
  return !isLoggedIn || !token
}

function redirectToLogin(targetUrl) {
  storage.set(StorageKeys.REDIRECT_AFTER_LOGIN, extractPath(targetUrl))
  uni.showToast({ title: '请先登录', icon: 'none' })
}

export function setupRouterGuard() {
  const originalNavigateTo = uni.navigateTo
  const originalSwitchTab = uni.switchTab
  const originalRedirectTo = uni.redirectTo
  const originalReLaunch = uni.reLaunch

  uni.navigateTo = (options) => {
    options.animationType = 'none'
    if (shouldCheckLogin(options.url)) {
      redirectToLogin(options.url)
      setTimeout(() => {
        originalNavigateTo.call(uni, { url: LOGIN_PAGE, animationType: 'none' })
      }, 500)
      return
    }
    return originalNavigateTo.call(uni, options)
  }

  uni.switchTab = (options) => {
    options.animationType = 'none'
    if (shouldCheckLogin(options.url)) {
      redirectToLogin(options.url)
      setTimeout(() => {
        originalReLaunch.call(uni, { url: LOGIN_PAGE, animationType: 'none' })
      }, 500)
      return
    }
    return originalSwitchTab.call(uni, options)
  }

  uni.redirectTo = (options) => {
    options.animationType = 'none'
    if (shouldCheckLogin(options.url)) {
      redirectToLogin(options.url)
      setTimeout(() => {
        originalRedirectTo.call(uni, { url: LOGIN_PAGE, animationType: 'none' })
      }, 500)
      return
    }
    return originalRedirectTo.call(uni, options)
  }

  uni.reLaunch = (options) => {
    options.animationType = 'none'
    if (shouldCheckLogin(options.url)) {
      redirectToLogin(options.url)
      setTimeout(() => {
        originalReLaunch.call(uni, { url: LOGIN_PAGE, animationType: 'none' })
      }, 500)
      return
    }
    return originalReLaunch.call(uni, options)
  }
}

export default {
  NEED_LOGIN_PAGES,
  extractPath,
  shouldCheckLogin,
  setupRouterGuard
}
