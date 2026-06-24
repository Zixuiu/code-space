import CONFIG from './config'
import { storage, StorageKeys } from './storage'

const BASE_URL = CONFIG.API_BASE_URL

const cacheMap = new Map()
const CACHE_DEFAULT_TTL = 5 * 60 * 1000

function getCacheKey(url, data) {
  const dataStr = data ? JSON.stringify(data) : ''
  return `${url}_${dataStr}`
}

function getCache(key) {
  const cached = cacheMap.get(key)
  if (!cached) return null
  if (Date.now() > cached.expireTime) {
    cacheMap.delete(key)
    return null
  }
  return cached.data
}

function setCache(key, data, ttl = CACHE_DEFAULT_TTL) {
  cacheMap.set(key, {
    data,
    expireTime: Date.now() + ttl
  })
}

function clearCache() {
  cacheMap.clear()
}

function clearCacheByPrefix(prefix) {
  for (const key of cacheMap.keys()) {
    if (key.startsWith(prefix)) {
      cacheMap.delete(key)
    }
  }
}

export const ErrorCode = {
  SUCCESS: 0,
  BAD_REQUEST: 400,
  UNAUTHORIZED: 401,
  FORBIDDEN: 403,
  NOT_FOUND: 404,
  TOO_MANY_REQUESTS: 429,
  SERVER_ERROR: 500,
  SERVICE_UNAVAILABLE: 503,

  PARAM_ERROR: 1001,
  TOKEN_EXPIRED: 1002,
  TOKEN_INVALID: 1003,
  USER_NOT_EXIST: 2001,
  USER_ALREADY_EXIST: 2002,
  PASSWORD_ERROR: 2003,
  PHONE_FORMAT_ERROR: 2004,
  VERIFY_CODE_ERROR: 2005,
  VERIFY_CODE_EXPIRED: 2006,
  BALANCE_NOT_ENOUGH: 3001,
  ORDER_NOT_EXIST: 4001,
  ORDER_STATUS_ERROR: 4002,
  NEED_NOT_EXIST: 5001,
  NEED_STATUS_ERROR: 5002
}

const ERROR_MESSAGES = {
  [ErrorCode.BAD_REQUEST]: '请求参数错误',
  [ErrorCode.UNAUTHORIZED]: '请先登录',
  [ErrorCode.FORBIDDEN]: '无权限访问',
  [ErrorCode.NOT_FOUND]: '资源不存在',
  [ErrorCode.TOO_MANY_REQUESTS]: '操作过于频繁，请稍后再试',
  [ErrorCode.SERVER_ERROR]: '服务器开小差了',
  [ErrorCode.SERVICE_UNAVAILABLE]: '服务暂不可用',
  [ErrorCode.PARAM_ERROR]: '参数错误',
  [ErrorCode.USER_NOT_EXIST]: '用户不存在',
  [ErrorCode.USER_ALREADY_EXIST]: '用户已存在',
  [ErrorCode.PASSWORD_ERROR]: '密码错误',
  [ErrorCode.PHONE_FORMAT_ERROR]: '手机号格式不正确',
  [ErrorCode.VERIFY_CODE_ERROR]: '验证码错误',
  [ErrorCode.VERIFY_CODE_EXPIRED]: '验证码已过期',
  [ErrorCode.BALANCE_NOT_ENOUGH]: '余额不足',
  [ErrorCode.ORDER_NOT_EXIST]: '订单不存在',
  [ErrorCode.ORDER_STATUS_ERROR]: '订单状态异常',
  [ErrorCode.NEED_NOT_EXIST]: '需求不存在',
  [ErrorCode.NEED_STATUS_ERROR]: '需求状态异常'
}

let isRefreshing = false
let refreshSubscribers = []

const subscribeTokenRefresh = (callback) => {
  refreshSubscribers.push(callback)
}

const onTokenRefreshed = (newToken) => {
  refreshSubscribers.forEach((callback) => callback(newToken))
  refreshSubscribers = []
}

const mockDataMap = {
  '/api/user/info': {
    id: 'u_1001',
    nickname: '演示用户',
    phone: '13800138000',
    avatar: '',
    gender: 'secret',
    region: '北京市朝阳区',
    bio: '我是演示用户',
    reputation: 98,
    completedOrders: 15,
    verified: true,
    createdAt: '2024-01-01'
  },
  '/api/order/list': {
    list: [],
    total: 0,
    page: 1,
    pageSize: 20
  },
  '/api/need/list': {
    list: [],
    total: 0
  },
  '/api/wallet/info': {
    balance: 1000.0,
    frozen: 0,
    totalIncome: 5000.0,
    totalExpend: 4000.0
  }
}

const getMockData = (url, method, data) => {
  if (url.startsWith('/api/user/login')) {
    return {
      token: 'mock_token_' + Date.now(),
      refreshToken: 'mock_refresh_' + Date.now(),
      userInfo: {
        id: 'u_1001',
        nickname: '用户' + (data?.phone?.slice(-4) || '0000'),
        phone: data?.phone || '13800138000',
        reputation: 100,
        completedOrders: 0
      },
      wallet: {
        balance: 1000.0,
        frozen: 0
      }
    }
  }

  if (url.startsWith('/api/user/info')) {
    return mockDataMap['/api/user/info']
  }

  if (url.startsWith('/api/order')) {
    return mockDataMap['/api/order/list']
  }

  if (url.startsWith('/api/need')) {
    return mockDataMap['/api/need/list']
  }

  if (url.startsWith('/api/wallet')) {
    return mockDataMap['/api/wallet/info']
  }

  if (url.startsWith('/api/message')) {
    return {
      list: [],
      total: 0
    }
  }

  if (url.startsWith('/api/user/register')) {
    return {
      id: 'u_' + Date.now(),
      nickname: data?.nickname || '新用户',
      phone: data?.phone
    }
  }

  return {}
}

const getErrorMessage = (code, message) => {
  if (message) return message
  return ERROR_MESSAGES[code] || '请求失败'
}

const handleUnauthorized = (resolve, reject) => {
  const refreshToken = storage.get(StorageKeys.REFRESH_TOKEN)

  if (!refreshToken) {
    triggerLogout()
    reject({ code: ErrorCode.UNAUTHORIZED, message: '登录已过期' })
    return
  }

  if (isRefreshing) {
    subscribeTokenRefresh((newToken) => {
      storage.set(StorageKeys.TOKEN, newToken)
    })
    return
  }

  isRefreshing = true

  uni.request({
    url: BASE_URL + '/api/user/refresh-token',
    method: 'POST',
    data: { refreshToken },
    header: { 'Content-Type': 'application/json' }
  })
    .then((res) => {
      isRefreshing = false
      if (res.data.code === 0 && res.data.data) {
        const newToken = res.data.data.token
        storage.set(StorageKeys.TOKEN, newToken)
        if (res.data.data.refreshToken) {
          storage.set(StorageKeys.REFRESH_TOKEN, res.data.data.refreshToken)
        }
        onTokenRefreshed(newToken)
      } else {
        triggerLogout()
        reject({ code: ErrorCode.UNAUTHORIZED, message: '登录已过期' })
      }
    })
    .catch(() => {
      isRefreshing = false
      triggerLogout()
      reject({ code: ErrorCode.UNAUTHORIZED, message: '登录已过期' })
    })
}

const triggerLogout = () => {
  storage.remove(StorageKeys.TOKEN)
  storage.remove(StorageKeys.REFRESH_TOKEN)
  storage.remove(StorageKeys.IS_LOGGED_IN)
  storage.remove(StorageKeys.USER_INFO)
  storage.remove(StorageKeys.CURRENT_USER)
  uni.showToast({ title: '登录已过期，请重新登录', icon: 'none' })
  setTimeout(() => {
    uni.reLaunch({ url: '/pages/login/login' })
  }, 1500)
}

const request = (options) => {
  return new Promise((resolve, reject) => {
    const token = storage.get(StorageKeys.TOKEN)

    if (options.loading !== false) {
      uni.showLoading({ title: '加载中...', mask: true })
    }

    const header = {
      'Content-Type': 'application/json',
      ...options.header
    }

    if (token) {
      header['Authorization'] = `Bearer ${token}`
    }

    uni.request({
      url: BASE_URL + options.url,
      method: options.method || 'GET',
      data: options.data || {},
      header,
      timeout: CONFIG.requestTimeout || 30000,
      success: (res) => {
        if (options.loading !== false) {
          uni.hideLoading()
        }

        const { statusCode, data } = res

        if (statusCode === 200) {
          if (data.code === 0 || data.success === true) {
            resolve(data.data)
          } else if (data.code === ErrorCode.UNAUTHORIZED || data.code === ErrorCode.TOKEN_EXPIRED) {
            handleUnauthorized(resolve, reject)
          } else {
            const message = getErrorMessage(data.code, data.message)
            if (options.showError !== false) {
              uni.showToast({ title: message, icon: 'none' })
            }
            reject({ code: data.code, message, data: data.data })
          }
        } else if (statusCode === ErrorCode.UNAUTHORIZED) {
          handleUnauthorized(resolve, reject)
        } else if (statusCode === ErrorCode.TOO_MANY_REQUESTS) {
          if (options.showError !== false) {
            uni.showToast({ title: ERROR_MESSAGES[ErrorCode.TOO_MANY_REQUESTS], icon: 'none' })
          }
          reject({ code: ErrorCode.TOO_MANY_REQUESTS, message: ERROR_MESSAGES[ErrorCode.TOO_MANY_REQUESTS] })
        } else if (statusCode >= 500) {
          if (CONFIG.USE_MOCK) {
            const mockData = getMockData(options.url, options.method, options.data)
            resolve(mockData)
          } else {
            const message = getErrorMessage(statusCode)
            if (options.showError !== false) {
              uni.showToast({ title: message, icon: 'none' })
            }
            reject({ code: statusCode, message })
          }
        } else {
          if (CONFIG.USE_MOCK) {
            const mockData = getMockData(options.url, options.method, options.data)
            resolve(mockData)
          } else {
            if (options.showError !== false) {
              uni.showToast({ title: '网络错误', icon: 'none' })
            }
            reject({ code: statusCode, message: '网络错误' })
          }
        }
      },
      fail: (err) => {
        if (options.loading !== false) {
          uni.hideLoading()
        }

        if (CONFIG.USE_MOCK) {
          console.log('API请求失败，使用Mock数据:', options.url)
          const mockData = getMockData(options.url, options.method, options.data)
          resolve(mockData)
        } else {
          uni.showToast({ title: '网络连接失败', icon: 'none' })
          reject(err)
        }
      }
    })
  })
}

const get = (url, data, options = {}) => {
  if (options.cache) {
    const cacheKey = getCacheKey(url, data)
    const cachedData = getCache(cacheKey)
    if (cachedData !== null) {
      return Promise.resolve(cachedData)
    }
  }

  const promise = request({
    url,
    method: 'GET',
    data,
    ...options
  })

  if (options.cache) {
    const cacheKey = getCacheKey(url, data)
    const ttl = typeof options.cache === 'number' ? options.cache : CACHE_DEFAULT_TTL
    promise.then((res) => {
      setCache(cacheKey, res, ttl)
    }).catch(() => {})
  }

  return promise
}

const post = (url, data, options = {}) => {
  return request({
    url,
    method: 'POST',
    data,
    ...options
  })
}

const put = (url, data, options = {}) => {
  return request({
    url,
    method: 'PUT',
    data,
    ...options
  })
}

const del = (url, data, options = {}) => {
  return request({
    url,
    method: 'DELETE',
    data,
    ...options
  })
}

const upload = (filePath, formData = {}, options = {}) => {
  return new Promise((resolve, reject) => {
    const token = storage.get(StorageKeys.TOKEN)

    if (options.showLoading !== false) {
      uni.showLoading({ title: '上传中...', mask: true })
    }

    uni.uploadFile({
      url: BASE_URL + (options.url || '/api/common/upload'),
      filePath,
      name: options.name || 'file',
      formData,
      header: {
        Authorization: token ? `Bearer ${token}` : ''
      },
      timeout: CONFIG.uploadTimeout || 60000,
      success: (res) => {
        if (options.showLoading !== false) {
          uni.hideLoading()
        }
        const data = JSON.parse(res.data)
        if (data.code === 0) {
          resolve(data.data)
        } else {
          if (CONFIG.USE_MOCK) {
            resolve({
              url: filePath,
              filename: formData?.filename || 'mock_image.jpg'
            })
          } else {
            const message = getErrorMessage(data.code, data.message)
            uni.showToast({ title: message, icon: 'none' })
            reject({ code: data.code, message, data: data.data })
          }
        }
      },
      fail: (err) => {
        if (options.showLoading !== false) {
          uni.hideLoading()
        }
        if (CONFIG.USE_MOCK) {
          resolve({
            url: filePath,
            filename: formData?.filename || 'mock_image.jpg'
          })
        } else {
          uni.showToast({ title: '上传失败', icon: 'none' })
          reject(err)
        }
      }
    })
  })
}

export {
  BASE_URL,
  request,
  get,
  post,
  put,
  del,
  upload,
  subscribeTokenRefresh,
  getErrorMessage,
  clearCache,
  clearCacheByPrefix
}
