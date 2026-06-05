import { post, get } from './request'
import CONFIG from './config'

class PaymentService {
  constructor() {
    this.pendingPayments = new Map()
  }

  async recharge(amount, payMethod) {
    const result = await post('/api/wallet/recharge', {
      amount,
      payMethod
    })

    if (result.payOrder) {
      return this[payMethod + 'Payment'](result.payOrder)
    }

    return result
  }

  async wechatPayment(payOrder) {
    return new Promise((resolve, reject) => {
      uni.requestPayment({
        provider: 'wxpay',
        timeStamp: payOrder.timeStamp,
        nonceStr: payOrder.nonceStr,
        package: payOrder.package,
        signType: payOrder.signType,
        paySign: payOrder.paySign,
        success: (res) => {
          resolve({ success: true, res })
        },
        fail: (err) => {
          reject({ success: false, err })
        }
      })
    })
  }

  async alipayPayment(payOrder) {
    return new Promise((resolve, reject) => {
      uni.requestPayment({
        provider: 'alipay',
        orderInfo: payOrder,
        success: (res) => {
          resolve({ success: true, res })
        },
        fail: (err) => {
          reject({ success: false, err })
        }
      })
    })
  }

  async withdraw(amount, account, accountType) {
    const result = await post('/api/wallet/withdraw', {
      amount,
      account,
      accountType
    })

    return result
  }

  async verifyPayPassword(password) {
    return post('/api/user/verify-pay-password', { password })
  }

  getVerifyLockStatus() {
    const lockData = uni.getStorageSync('payPasswordLock') || {
      attempts: 0,
      lockUntil: 0
    }
    return lockData
  }

  setVerifyLockStatus(attempts, lockUntil = 0) {
    uni.setStorageSync('payPasswordLock', { attempts, lockUntil })
  }

  handleVerifyError() {
    const lockData = this.getVerifyLockStatus()
    lockData.attempts = (lockData.attempts || 0) + 1

    if (lockData.attempts >= 3) {
      lockData.lockUntil = Date.now() + 30 * 60 * 1000
      this.setVerifyLockStatus(lockData.attempts, lockData.lockUntil)
      uni.showToast({
        title: '密码错误次数过多，已锁定30分钟',
        icon: 'none'
      })
      return true
    }

    const remain = 3 - lockData.attempts
    this.setVerifyLockStatus(lockData.attempts)
    uni.showToast({
      title: `密码错误，剩余${remain}次机会`,
      icon: 'none'
    })
    return false
  }

  clearVerifyLock() {
    this.setVerifyLockStatus(0, 0)
  }

  isLocked() {
    const lockData = this.getVerifyLockStatus()
    if (lockData.lockUntil && Date.now() < lockData.lockUntil) {
      return true
    }
    return false
  }

  getRemainingLockTime() {
    const lockData = this.getVerifyLockStatus()
    if (lockData.lockUntil) {
      const remaining = lockData.lockUntil - Date.now()
      return Math.max(0, Math.ceil(remaining / 1000))
    }
    return 0
  }
}

const paymentService = new PaymentService()

export default paymentService
