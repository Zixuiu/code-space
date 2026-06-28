import { defineStore } from 'pinia'
import { userApi } from '@/api/user'
import { walletApi } from '@/api/wallet'

const DEFAULT_USER = {
  id: '',
  nickname: '',
  phone: '',
  avatar: '',
  reputation: 0,
  completedOrders: 0,
  walletBalance: 0,
  walletLevel: 1,
  sharedNeeds: [],
  commissionEarned: 0,
  invitedUsers: [],
  skills: [],
  verified: false
}

function getStoredUser() {
  const isLoggedIn = uni.getStorageSync('isLoggedIn')
  if (isLoggedIn) {
    const userInfo = uni.getStorageSync('userInfo')
    if (userInfo) return userInfo
  }
  return { ...DEFAULT_USER }
}

function getWalletKey(userId) {
  return `wallet_${userId}`
}

export const useUserStore = defineStore('user', {
  state: () => ({
    isLoggedIn: uni.getStorageSync('isLoggedIn') || false,
    currentUser: getStoredUser(),
    walletInfo: null,
    token: uni.getStorageSync('token') || '',
    refreshToken: uni.getStorageSync('refreshToken') || ''
  }),

  getters: {
    isAuthenticated: (state) => state.isLoggedIn && !!state.token,

    walletBalance: (state) => {
      const walletKey = getWalletKey(state.currentUser?.id || '')
      const wallet = uni.getStorageSync(walletKey) || {}
      const localStorageBalance = parseFloat(wallet.balance)
      if (!isNaN(localStorageBalance)) {
        return localStorageBalance
      }
      if (state.walletInfo && state.walletInfo.balance !== undefined) {
        return parseFloat(state.walletInfo.balance) || 0
      }
      return state.currentUser?.walletBalance || 0
    },

    commissionEarned: (state) => {
      return state.currentUser?.commissionEarned || 0
    },

    hasPayPassword: () => {
      return !!uni.getStorageSync('payPasswordSet')
    },

    userId: (state) => state.currentUser?.id || ''
  },

  actions: {
    async login(phone, password) {
      try {
        const data = await userApi.login(phone, password)
        this.setAuthData(data)
        return data
      } catch (e) {
        throw e
      }
    },

    async register(userInfo) {
      try {
        const data = await userApi.register(userInfo)
        this.setAuthData(data)
        return data
      } catch (e) {
        throw e
      }
    },

    setAuthData(data) {
      if (data.token) {
        this.token = data.token
        uni.setStorageSync('token', data.token)
      }
      if (data.refreshToken) {
        this.refreshToken = data.refreshToken
        uni.setStorageSync('refreshToken', data.refreshToken)
      }
      if (data.user) {
        this.currentUser = data.user
        uni.setStorageSync('userInfo', data.user)
      }
      this.isLoggedIn = true
      uni.setStorageSync('isLoggedIn', true)
    },

    async fetchUserInfo() {
      try {
        const userInfo = await userApi.getUserInfo()
        this.currentUser = userInfo
        uni.setStorageSync('userInfo', userInfo)
        return userInfo
      } catch (e) {
        console.error('fetchUserInfo failed', e)
        throw e
      }
    },

    async updateUserInfo(userInfo) {
      try {
        const updated = await userApi.updateUserInfo(userInfo)
        this.currentUser = { ...this.currentUser, ...updated }
        uni.setStorageSync('userInfo', this.currentUser)
        return updated
      } catch (e) {
        throw e
      }
    },

    async fetchWalletInfo() {
      try {
        const wallet = await walletApi.getWalletInfo()
        this.walletInfo = wallet
        const walletKey = getWalletKey(this.currentUser.id)
        uni.setStorageSync(walletKey, wallet)
        this.currentUser.walletBalance = parseFloat(wallet.balance) || 0
        return wallet
      } catch (e) {
        console.error('fetchWalletInfo failed', e)
        const walletKey = getWalletKey(this.currentUser.id)
        const wallet = uni.getStorageSync(walletKey) || { balance: 0 }
        this.walletInfo = wallet
        return wallet
      }
    },

    updateWalletBalance(balance) {
      if (this.walletInfo) {
        this.walletInfo.balance = balance
      }
      this.currentUser.walletBalance = balance
      const walletKey = getWalletKey(this.currentUser.id)
      const wallet = uni.getStorageSync(walletKey) || {}
      wallet.balance = balance
      uni.setStorageSync(walletKey, wallet)
    },

    syncWalletBalance() {
      if (this.walletInfo) {
        const balance = parseFloat(this.walletInfo.balance) || 0
        this.currentUser.walletBalance = balance
      }
    },

    logout() {
      this.isLoggedIn = false
      this.currentUser = { ...DEFAULT_USER }
      this.walletInfo = null
      this.token = ''
      this.refreshToken = ''

      uni.removeStorageSync('token')
      uni.removeStorageSync('refreshToken')
      uni.removeStorageSync('isLoggedIn')
      uni.removeStorageSync('userInfo')
    },

    setLoggedIn(status) {
      this.isLoggedIn = status
      uni.setStorageSync('isLoggedIn', status)
    },

    setUserInfo(userInfo) {
      this.currentUser = userInfo
      uni.setStorageSync('userInfo', userInfo)
    },

    setPayPasswordSet() {
      uni.setStorageSync('payPasswordSet', true)
    },

    addSharedNeed(needId, needTitle, reward) {
      if (!this.currentUser.sharedNeeds) {
        this.currentUser.sharedNeeds = []
      }
      this.currentUser.sharedNeeds.push({
        needId,
        needTitle,
        reward,
        sharedAt: Date.now(),
        earned: 0
      })
      uni.setStorageSync('userInfo', this.currentUser)
    },

    addCommission(amount, shareUserId, orderTitle, reward) {
      if (shareUserId) {
        const shareWalletKey = getWalletKey(shareUserId)
        const shareWallet = uni.getStorageSync(shareWalletKey) || { balance: 0 }
        shareWallet.balance = parseFloat(shareWallet.balance || 0) + amount
        uni.setStorageSync(shareWalletKey, shareWallet)
      }
      if (shareUserId === this.currentUser.id) {
        if (!this.currentUser.commissionEarned) {
          this.currentUser.commissionEarned = 0
        }
        this.currentUser.commissionEarned += amount
        if (this.walletInfo) {
          const myWalletKey = getWalletKey(this.currentUser.id)
          const myWallet = uni.getStorageSync(myWalletKey) || { balance: 0 }
          this.walletInfo.balance = parseFloat(myWallet.balance) || 0
        }
        if (this.currentUser.sharedNeeds && this.currentUser.sharedNeeds.length > 0) {
          const sharedNeed = this.currentUser.sharedNeeds.find(sn => sn.needTitle === orderTitle)
          if (sharedNeed) {
            sharedNeed.earned = (sharedNeed.earned || 0) + amount
          }
        }
        uni.setStorageSync('userInfo', this.currentUser)
      }
    },

    deductBalance(amount) {
      const walletKey = getWalletKey(this.currentUser.id)
      const wallet = uni.getStorageSync(walletKey) || { balance: 0 }
      const currentBalance = parseFloat(wallet.balance || 0) || this.currentUser.walletBalance || 0
      const newBalance = Math.max(0, currentBalance - amount)
      wallet.balance = newBalance
      uni.setStorageSync(walletKey, wallet)

      if (this.walletInfo) {
        this.walletInfo.balance = newBalance
      }
      this.currentUser.walletBalance = newBalance
      uni.setStorageSync('userInfo', this.currentUser)
    },

    addBalanceToUser(userId, amount) {
      const walletKey = getWalletKey(userId)
      const wallet = uni.getStorageSync(walletKey) || { balance: 0 }
      const currentBalance = parseFloat(wallet.balance || 0)
      const newBalance = currentBalance + amount
      wallet.balance = newBalance
      uni.setStorageSync(walletKey, wallet)

      const userTransactions = uni.getStorageSync('userTransactions') || {}
      if (!userTransactions[userId]) {
        userTransactions[userId] = {
          balance: 0,
          transactions: []
        }
      }
      userTransactions[userId].balance += amount
      userTransactions[userId].transactions.unshift({
        id: `trans_${Date.now()}`,
        type: 'order_reward',
        amount: amount,
        time: Date.now(),
        status: 'completed'
      })
      uni.setStorageSync('userTransactions', userTransactions)

      if (userId === this.currentUser.id) {
        this.currentUser.walletBalance = newBalance
        uni.setStorageSync('userInfo', this.currentUser)
      }

      if (this.walletInfo) {
        const myWalletKey = getWalletKey(this.currentUser.id)
        const myWallet = uni.getStorageSync(myWalletKey) || {}
        this.walletInfo.balance = parseFloat(myWallet.balance) || 0
      }
    },

    updateBalanceFromWallet() {
      const walletKey = getWalletKey(this.currentUser.id)
      const wallet = uni.getStorageSync(walletKey) || { balance: 0 }
      this.balance = parseFloat(wallet.balance) || 0
    }
  }
})
