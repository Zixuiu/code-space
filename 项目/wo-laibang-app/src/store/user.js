import { defineStore } from 'pinia'
import { userApi } from '@/api/user'
import { walletApi } from '@/api/wallet'
import { storage, StorageKeys } from '@/utils/storage'

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
  const isLoggedIn = storage.getBoolean(StorageKeys.IS_LOGGED_IN)
  if (isLoggedIn) {
    const userInfo = storage.getObject(StorageKeys.USER_INFO, null)
    if (userInfo && userInfo.id) return userInfo
  }
  return { ...DEFAULT_USER }
}

function getWalletKey(userId) {
  return `wallet_${userId}`
}

export const useUserStore = defineStore('user', {
  state: () => ({
    isLoggedIn: storage.getBoolean(StorageKeys.IS_LOGGED_IN, false),
    currentUser: getStoredUser(),
    walletInfo: null,
    token: storage.get(StorageKeys.TOKEN, ''),
    refreshToken: storage.get(StorageKeys.REFRESH_TOKEN, '')
  }),

  getters: {
    isAuthenticated: (state) => state.isLoggedIn && !!state.token,

    walletBalance: (state) => {
      const walletKey = getWalletKey(state.currentUser?.id || '')
      const wallet = storage.getObject(walletKey, {})
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
      return !!storage.get('payPasswordSet')
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
        storage.set(StorageKeys.TOKEN, data.token)
      }
      if (data.refreshToken) {
        this.refreshToken = data.refreshToken
        storage.set(StorageKeys.REFRESH_TOKEN, data.refreshToken)
      }
      if (data.user) {
        this.currentUser = data.user
        storage.set(StorageKeys.USER_INFO, data.user)
      }
      this.isLoggedIn = true
      storage.set(StorageKeys.IS_LOGGED_IN, true)
    },

    async fetchUserInfo() {
      try {
        const userInfo = await userApi.getUserInfo()
        this.currentUser = userInfo
        storage.set(StorageKeys.USER_INFO, userInfo)
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
        storage.set(StorageKeys.USER_INFO, this.currentUser)
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
        storage.set(walletKey, wallet)
        this.currentUser.walletBalance = parseFloat(wallet.balance) || 0
        return wallet
      } catch (e) {
        console.error('fetchWalletInfo failed', e)
        const walletKey = getWalletKey(this.currentUser.id)
        const wallet = storage.getObject(walletKey, { balance: 0 })
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
      const wallet = storage.getObject(walletKey, {})
      wallet.balance = balance
      storage.set(walletKey, wallet)
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

      storage.remove(StorageKeys.TOKEN)
      storage.remove(StorageKeys.REFRESH_TOKEN)
      storage.remove(StorageKeys.IS_LOGGED_IN)
      storage.remove(StorageKeys.USER_INFO)
    },

    setLoggedIn(status) {
      this.isLoggedIn = status
      storage.set(StorageKeys.IS_LOGGED_IN, status)
    },

    setUserInfo(userInfo) {
      this.currentUser = userInfo
      storage.set(StorageKeys.USER_INFO, userInfo)
    },

    setPayPasswordSet() {
      storage.set('payPasswordSet', true)
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
      storage.set(StorageKeys.USER_INFO, this.currentUser)
    },

    addCommission(amount, shareUserId, orderTitle, reward) {
      if (shareUserId) {
        const shareWalletKey = getWalletKey(shareUserId)
        const shareWallet = storage.getObject(shareWalletKey, { balance: 0 })
        shareWallet.balance = parseFloat(shareWallet.balance || 0) + amount
        storage.set(shareWalletKey, shareWallet)
      }
      if (shareUserId === this.currentUser.id) {
        if (!this.currentUser.commissionEarned) {
          this.currentUser.commissionEarned = 0
        }
        this.currentUser.commissionEarned += amount
        if (this.walletInfo) {
          const myWalletKey = getWalletKey(this.currentUser.id)
          const myWallet = storage.getObject(myWalletKey, { balance: 0 })
          this.walletInfo.balance = parseFloat(myWallet.balance) || 0
        }
        if (this.currentUser.sharedNeeds && this.currentUser.sharedNeeds.length > 0) {
          const sharedNeed = this.currentUser.sharedNeeds.find(sn => sn.needTitle === orderTitle)
          if (sharedNeed) {
            sharedNeed.earned = (sharedNeed.earned || 0) + amount
          }
        }
        storage.set(StorageKeys.USER_INFO, this.currentUser)
      }
    },

    deductBalance(amount) {
      const walletKey = getWalletKey(this.currentUser.id)
      const wallet = storage.getObject(walletKey, { balance: 0 })
      const currentBalance = parseFloat(wallet.balance || 0) || this.currentUser.walletBalance || 0
      const newBalance = Math.max(0, currentBalance - amount)
      wallet.balance = newBalance
      storage.set(walletKey, wallet)

      if (this.walletInfo) {
        this.walletInfo.balance = newBalance
      }
      this.currentUser.walletBalance = newBalance
      storage.set(StorageKeys.USER_INFO, this.currentUser)
    },

    addBalanceToUser(userId, amount) {
      const walletKey = getWalletKey(userId)
      const wallet = storage.getObject(walletKey, { balance: 0 })
      const currentBalance = parseFloat(wallet.balance || 0)
      const newBalance = currentBalance + amount
      wallet.balance = newBalance
      storage.set(walletKey, wallet)

      const userTransactions = storage.getObject('userTransactions', {})
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
      storage.set('userTransactions', userTransactions)

      if (userId === this.currentUser.id) {
        this.currentUser.walletBalance = newBalance
        storage.set(StorageKeys.USER_INFO, this.currentUser)
      }

      if (this.walletInfo) {
        const myWalletKey = getWalletKey(this.currentUser.id)
        const myWallet = storage.getObject(myWalletKey, {})
        this.walletInfo.balance = parseFloat(myWallet.balance) || 0
      }
    },

    updateBalanceFromWallet() {
      const walletKey = getWalletKey(this.currentUser.id)
      const wallet = storage.getObject(walletKey, { balance: 0 })
      this.balance = parseFloat(wallet.balance) || 0
    }
  }
})
