import { post, get, put } from '@/utils/request'

export const userApi = {
  login(phone, password) {
    return post('/api/user/login', { phone, password })
  },

  register(userInfo) {
    return post('/api/user/register', userInfo)
  },

  getUserInfo(options = {}) {
    return get('/api/user/info', null, options)
  },

  updateUserInfo(userInfo) {
    return put('/api/user/info', userInfo)
  },

  verifyPhone(phone, code) {
    return post('/api/user/verify-phone', { phone, code })
  },

  resetPassword(phone, password, code) {
    return post('/api/user/reset-password', { phone, password, code })
  },

  getCaptcha(phone) {
    return post('/api/user/captcha', { phone })
  }
}
