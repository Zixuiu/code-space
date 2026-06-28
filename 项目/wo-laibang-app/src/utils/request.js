import CONFIG from './config'

const BASE_URL = CONFIG.API_BASE_URL

let isRefreshing = false
let refreshSubscribers = []

const subscribeTokenRefresh = (callback) => {
  refreshSubscribers.push(callback)
}

const onTokenRefreshed = (newToken) => {
  refreshSubscribers.forEach(callback => callback(newToken))
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
    balance: 1000.00,
    frozen: 0,
    totalIncome: 5000.00,
    totalExpend: 4000.00
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
        balance: 1000.00,
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

const request = (options) => {
  return new Promise((resolve, reject) => {
    const token = uni.getStorageSync('token')

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

        if (res.statusCode === 200) {
          const data = res.data
          if (data.code === 0 || data.success === true) {
            resolve(data.data)
          } else if (data.code === 401) {
            handleUnauthorized(resolve, reject)
          } else if (data.code === 403) {
            uni.showToast({ title: data.message || '无权限访问', icon: 'none' })
            reject(data)
          } else if (data.code === 500) {
            if (CONFIG.USE_MOCK) {
              const mockData = getMockData(options.url, options.method, options.data)
              resolve(mockData)
            } else {
              uni.showToast({ title: '服务器错误', icon: 'none' })
              reject(data)
            }
          } else {
            if (options.showError !== false) {
              uni.showToast({
                title: data.message || '请求失败',
                icon: 'none'
              })
            }
            reject(data)
          }
        } else if (res.statusCode === 401) {
          handleUnauthorized(resolve, reject)
        } else if (res.statusCode === 500) {
          if (CONFIG.USE_MOCK) {
            if (options.loading !== false) uni.hideLoading()
            const mockData = getMockData(options.url, options.method, options.data)
            resolve(mockData)
          } else {
            uni.showToast({ title: '服务器错误', icon: 'none' })
            reject(res.data)
          }
        } else {
          if (CONFIG.USE_MOCK) {
            if (options.loading !== false) uni.hideLoading()
            const mockData = getMockData(options.url, options.method, options.data)
            resolve(mockData)
          } else {
            uni.showToast({ title: '网络错误', icon: 'none' })
            reject(res.data)
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

const handleUnauthorized = (resolve, reject) => {
  const refreshToken = uni.getStorageSync('refreshToken')

  if (!refreshToken) {
    triggerLogout()
    return
  }

  if (isRefreshing) {
    subscribeTokenRefresh((newToken) => {
      uni.setStorageSync('token', newToken)
    })
    return
  }

  isRefreshing = true

  uni.request({
    url: BASE_URL + '/api/user/refresh-token',
    method: 'POST',
    data: { refreshToken },
    header: { 'Content-Type': 'application/json' }
  }).then(res => {
    isRefreshing = false
    if (res.data.code === 0 && res.data.data) {
      const newToken = res.data.data.token
      uni.setStorageSync('token', newToken)
      if (res.data.data.refreshToken) {
        uni.setStorageSync('refreshToken', res.data.data.refreshToken)
      }
      onTokenRefreshed(newToken)
    } else {
      triggerLogout()
    }
  }).catch(() => {
    isRefreshing = false
    triggerLogout()
  })
}

const triggerLogout = () => {
  uni.removeStorageSync('token')
  uni.removeStorageSync('refreshToken')
  uni.removeStorageSync('isLoggedIn')
  uni.removeStorageSync('userInfo')
  uni.showToast({ title: '登录已过期，请重新登录', icon: 'none' })
  setTimeout(() => {
    uni.reLaunch({ url: '/pages/login/login' })
  }, 1500)
}

const get = (url, data, options = {}) => {
  return request({
    url,
    method: 'GET',
    data,
    ...options
  })
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
    const token = uni.getStorageSync('token')

    if (options.showLoading !== false) {
      uni.showLoading({ title: '上传中...', mask: true })
    }

    uni.uploadFile({
      url: BASE_URL + (options.url || '/api/common/upload'),
      filePath,
      name: options.name || 'file',
      formData,
      header: {
        'Authorization': token ? `Bearer ${token}` : ''
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
            uni.showToast({ title: data.message || '上传失败', icon: 'none' })
            reject(data)
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
  subscribeTokenRefresh
}