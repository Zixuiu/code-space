import { defineStore } from 'pinia'
import { useUserStore } from './user'
import { useOrderStore } from './order'
import { getChatKey } from '@/utils/chat'

const COMMISSION_RATE = 0.1
const SHARE_COMMISSION_RATE = 0.02

export const NEED_STATUS = {
  OPEN: 'open',
  ACCEPTED: 'accepted',
  PENDING_CONFIRM: 'pending_confirm',
  COMPLETED: 'completed',
  CANCELLED: 'cancelled'
}

const INITIAL_NEEDS = [
  {
    id: 'n1',
    title: '帮忙取快递',
    description: '3个快递在菜鸟驿站，顺路带回来',
    reward: 8,
    location: '阳光花园3栋',
    latitude: 39.909,
    longitude: 116.398,
    publisher: { id: 'u2', nickname: '李阿姨', reputation: 85, completedOrders: 5 },
    status: NEED_STATUS.OPEN,
    category: '跑腿',
    isUrgent: false,
    createdAt: Date.now() - 3600000,
    deadline: '今天 18:00',
  },
  {
    id: 'n2',
    title: '上门喂猫',
    description: '需要喂食、加水，简单清理猫砂',
    reward: 35,
    location: '绿景苑2单元',
    latitude: 39.911,
    longitude: 116.401,
    publisher: { id: 'u3', nickname: '小林', reputation: 92, completedOrders: 8 },
    status: NEED_STATUS.OPEN,
    category: '家政',
    isUrgent: true,
    createdAt: Date.now() - 7200000,
    deadline: '明天 12:00',
  },
  {
    id: 'n3',
    title: '陪老人散步',
    description: '小区内散步30分钟，陪聊天',
    reward: 25,
    location: '夕阳红社区',
    latitude: 39.905,
    longitude: 116.395,
    publisher: { id: 'u4', nickname: '王爷爷', reputation: 78, completedOrders: 3 },
    status: NEED_STATUS.OPEN,
    category: '家政',
    isUrgent: false,
    createdAt: Date.now() - 86400000,
  },
  {
    id: 'n4',
    title: '维修电脑小问题',
    description: '系统卡顿清理',
    reward: 40,
    location: '智慧家园5栋',
    latitude: 39.913,
    longitude: 116.403,
    publisher: { id: 'u5', nickname: 'IT张', reputation: 95, completedOrders: 20 },
    status: NEED_STATUS.OPEN,
    category: '技术',
    isUrgent: false,
    createdAt: Date.now() - 43200000,
  },
]

export const useNeedStore = defineStore('need', {
  state: () => ({
    needs: INITIAL_NEEDS,
    searchQuery: '',
    sortBy: 'time',
    filteredNeeds: [],
    userLatitude: 39.908823,
    userLongitude: 116.397470,
    NEED_STATUS: NEED_STATUS,
  }),

  getters: {
    allNeeds: (state) => state.needs.filter(n => n.status === NEED_STATUS.OPEN),
    
    openNeeds: (state) => state.needs.filter(n => n.status === NEED_STATUS.OPEN),
    
    filteredNeedsGetter: (state) => {
      if (state.filteredNeeds && state.filteredNeeds.length > 0) {
        return state.filteredNeeds
      }
      let result = state.needs.filter(n => n.status === NEED_STATUS.OPEN)

      if (state.searchQuery.trim()) {
        const query = state.searchQuery.toLowerCase()
        result = result.filter(n =>
          n.title.toLowerCase().includes(query) ||
          n.description.toLowerCase().includes(query) ||
          n.location.toLowerCase().includes(query)
        )
      }

      switch (state.sortBy) {
        case 'time':
          result = [...result].sort((a, b) => b.createdAt - a.createdAt)
          break
        case 'reward':
          result = [...result].sort((a, b) => b.reward - a.reward)
          break
        case 'location':
          result = [...result].sort((a, b) => a.location.localeCompare(b.location))
          break
        case 'distance':
          const userLat = state.userLatitude
          const userLng = state.userLongitude
          const calcDist = (lat, lng) => {
            if (!lat || !lng) return Infinity
            const R = 6371
            const dLat = (lat - userLat) * Math.PI / 180
            const dLng = (lng - userLng) * Math.PI / 180
            const a = Math.sin(dLat/2) * Math.sin(dLat/2) +
                      Math.cos(userLat * Math.PI / 180) * Math.cos(lat * Math.PI / 180) *
                      Math.sin(dLng/2) * Math.sin(dLng/2)
            return R * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a))
          }
          result = [...result].sort((a, b) => calcDist(a.latitude, a.longitude) - calcDist(b.latitude, b.longitude))
          break
      }

      return result
    },
    
    publishedNeeds: (state) => {
      const userStore = useUserStore()
      return state.needs.filter(n => n.publisher.id === userStore.currentUser.id)
    },
    
    allPublishedNeeds: (state) => {
      const userStore = useUserStore()
      return state.needs.filter(n => n.publisher.id === userStore.currentUser.id)
    },
  },

  actions: {
    addNeed(needData) {
      const userStore = useUserStore()
      const newNeed = {
        ...needData,
        id: `n${Date.now()}`,
        createdAt: Date.now(),
        publisher: { ...userStore.currentUser },
        status: NEED_STATUS.OPEN,
        category: needData.category || '其他',
        isUrgent: needData.isUrgent || false,
        latitude: needData.latitude || 39.909 + (Math.random() - 0.5) * 0.01,
        longitude: needData.longitude || 116.398 + (Math.random() - 0.5) * 0.01,
      }
      this.needs.unshift(newNeed)
      return newNeed
    },

    acceptNeed(needId) {
      const userStore = useUserStore()

      if (!userStore.isLoggedIn || !userStore.currentUser?.id) {
        return { success: false, message: '请先登录后再接单' }
      }

      const need = this.needs.find(n => n.id === needId)
      if (!need || need.status !== NEED_STATUS.OPEN) {
        return { success: false, message: '该需求已被接单' }
      }

      if (need.publisher.id === userStore.currentUser.id) {
        return { success: false, message: '不能接自己发布的需求' }
      }
      const alreadyAccepted = need.helper && need.helper.id === userStore.currentUser.id
      if (alreadyAccepted) {
        return { success: false, message: '您已接过此单' }
      }

      const shareSource = uni.getStorageSync('currentShareSource') || null
      const sharedFromThisNeed = shareSource && shareSource.needId === needId
      const shareUserId = shareSource ? shareSource.fromUserId : null

      const newOrder = {
        id: `ord${Date.now()}`,
        needId: need.id,
        title: need.title,
        description: need.description,
        reward: need.reward,
        location: need.location,
        latitude: need.latitude,
        longitude: need.longitude,
        publisher: { ...need.publisher },
        helper: { ...userStore.currentUser },
        status: NEED_STATUS.ACCEPTED,
        createdAt: Date.now(),
        image: need.image || '',
        deadline: need.deadline || '',
        shareUserId: shareUserId,
        sharedFromThisNeed: sharedFromThisNeed,
        commissionRate: COMMISSION_RATE,
        shareCommissionRate: SHARE_COMMISSION_RATE,
      }

      need.status = NEED_STATUS.ACCEPTED
      need.helper = { ...userStore.currentUser }
      need.acceptedAt = Date.now()

      const orderStore = useOrderStore()
      orderStore.addOrder(newOrder)

      uni.setStorageSync('currentShareSource', null)

      const allConvs = uni.getStorageSync('conversations') || []
      const existingIndex = allConvs.findIndex(c => c.userId === need.publisher.id)
      const conv = {
        id: `conv_${need.publisher.id}`,
        userId: need.publisher.id,
        nickname: need.publisher.nickname,
        lastMessage: '已接单，可以开始聊天了~',
        lastTime: Date.now(),
        unread: 0,
        online: true,
        relatedOrder: {
          needId: need.id,
          orderId: newOrder.id,
          title: need.title,
          reward: need.reward,
          status: need.status,
          publisher: { ...need.publisher },
          helper: { ...need.helper }
        }
      }

      if (existingIndex >= 0) {
        allConvs[existingIndex] = conv
      } else {
        allConvs.unshift(conv)
      }
      uni.setStorageSync('conversations', allConvs)

      const allMessages = uni.getStorageSync('chatMessages') || {}
      const chatKey = getChatKey(userStore.currentUser.id, need.publisher.id)
      const systemMsg = {
        id: `msg_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
        type: 'text',
        text: '已接单，可以开始聊天了~',
        time: Date.now(),
        isSelf: false
      }
      if (!allMessages[chatKey]) {
        allMessages[chatKey] = []
      }
      allMessages[chatKey].push(systemMsg)
      uni.setStorageSync('chatMessages', allMessages)

      let commissionInfo = ''
      if (shareUserId) {
        commissionInfo = `（订单通过分享链接完成，分享者将获得 ¥${(need.reward * SHARE_COMMISSION_RATE).toFixed(2)} 佣金）`
      }

      return { success: true, message: '接单成功' + commissionInfo, order: newOrder }
    },

    cancelNeed(needId) {
      const userStore = useUserStore()
      const need = this.needs.find(n => n.id === needId)
      if (!need) {
        return { success: false, message: '需求不存在' }
      }
      if (need.publisher.id !== userStore.currentUser.id) {
        return { success: false, message: '只有发布者才能取消' }
      }
      if (need.status !== NEED_STATUS.OPEN && need.status !== NEED_STATUS.ACCEPTED) {
        return { success: false, message: '当前状态无法取消' }
      }
      const reward = need.reward || 0
      need.status = NEED_STATUS.CANCELLED
      need.cancelledAt = Date.now()
      const orderStore = useOrderStore()
      const order = orderStore.orders.find(o => o.needId === needId)
      if (reward > 0 && !(order && order.settled)) {
        userStore.addBalanceToUser(need.publisher.id, reward)
        const transactions = uni.getStorageSync('walletTransactions') || []
        transactions.unshift({
          id: Date.now(),
          type: 'refund',
          title: '取消需求退款：' + need.title,
          amount: reward,
          time: Date.now()
        })
        uni.setStorageSync('walletTransactions', transactions)
      }
      if (order) {
        order.status = NEED_STATUS.CANCELLED
        order.cancelledAt = Date.now()
      }
      return { success: true, message: '已取消，赏金已退回钱包' }
    },

    markComplete(needId) {
      const userStore = useUserStore()
      const need = this.needs.find(n => n.id === needId)
      if (!need || need.status !== NEED_STATUS.ACCEPTED) {
        return { success: false, message: '当前状态无法标记完成' }
      }
      if (!need.helper || need.helper.id !== userStore.currentUser.id) {
        return { success: false, message: '只有接单者才能标记完成' }
      }
      
      need.status = NEED_STATUS.PENDING_CONFIRM
      need.markedCompleteAt = Date.now()
      need.helperConfirmed = true

      const orderStore = useOrderStore()
      const order = orderStore.orders.find(o => o.needId === needId)
      if (order) {
        order.status = NEED_STATUS.PENDING_CONFIRM
        order.markedCompleteAt = Date.now()
        order.helperConfirmed = true
      }

      const allConvs = uni.getStorageSync('conversations') || []
      const convIndex = allConvs.findIndex(c => c.userId === need.publisher.id)
      if (convIndex >= 0 && allConvs[convIndex].relatedOrder) {
        allConvs[convIndex].relatedOrder.status = NEED_STATUS.PENDING_CONFIRM
        uni.setStorageSync('conversations', allConvs)
      }

      this.sendCompleteNotification(need, 'helper')
      
      return { success: true, message: '已标记完成，等待发布者确认' }
    },

    confirmComplete(needId) {
      const userStore = useUserStore()
      const need = this.needs.find(n => n.id === needId)
      if (!need || need.status !== NEED_STATUS.PENDING_CONFIRM) {
        return { success: false, message: '当前状态无法确认完成' }
      }
      if (need.publisher.id !== userStore.currentUser.id) {
        return { success: false, message: '只有发布者才能确认完成' }
      }

      need.publisherConfirmed = true

      const orderStore = useOrderStore()
      const order = orderStore.orders.find(o => o.needId === needId)
      if (order) {
        order.publisherConfirmed = true
      }

      if (!need.helperConfirmed) {
        this.sendCompleteNotification(need, 'publisher')
        return { success: true, message: '已确认，等待帮手确认后订单完成' }
      }

      const helper = need.helper
      const reward = need.reward

      if (order && order.settled) {
        need.status = NEED_STATUS.COMPLETED
        need.completedAt = Date.now()
        this.sendCompleteNotification(need, 'publisher')
        return { success: true, message: '确认完成，订单已结束' }
      }
      
      need.status = NEED_STATUS.COMPLETED
      need.completedAt = Date.now()

      if (order) {
        order.status = NEED_STATUS.COMPLETED
        order.completedAt = Date.now()
      }

      const platformCommission = reward * COMMISSION_RATE
      let shareCommission = 0
      
      if (order && order.shareUserId) {
        shareCommission = reward * SHARE_COMMISSION_RATE
        userStore.addCommission(shareCommission, order.shareUserId, need.title, reward)
      }
      
      const actualReward = reward - platformCommission - shareCommission
      if (helper && helper.id) {
        userStore.addBalanceToUser(helper.id, actualReward)
      }

      if (order) {
        order.settled = true
      }

      const allConvs = uni.getStorageSync('conversations') || []
      allConvs.forEach((conv, index) => {
        if (conv.relatedOrder && conv.relatedOrder.needId === needId) {
          conv.relatedOrder.status = NEED_STATUS.COMPLETED
        }
      })
      uni.setStorageSync('conversations', allConvs)

      this.sendCompleteNotification(need, 'publisher')
      
      return { success: true, message: '确认完成，订单已结束' }
    },

    sendCompleteNotification(need, fromRole) {
      const isPublisher = fromRole === 'publisher'
      const targetUser = isPublisher ? need.helper : need.publisher

      if (targetUser && targetUser.id) {
        const notifications = uni.getStorageSync('notifications') || []
        const message = isPublisher ? '发布者已确认完成' : '帮手已标记完成，等待您确认'
        notifications.unshift({
          id: Date.now(),
          type: 'order',
          title: isPublisher ? '订单已完成' : '订单待确认',
          content: message,
          orderId: need.id,
          orderTitle: need.title,
          status: isPublisher ? 'completed' : 'pending_confirm',
          read: false,
          createdAt: Date.now()
        })
        uni.setStorageSync('notifications', notifications)

        const unreadCount = notifications.filter(n => !n.read).length
        if (unreadCount > 0) {
          uni.setTabBarBadge({
            index: 3,
            text: unreadCount > 99 ? '99+' : String(unreadCount)
          })
        } else {
          uni.removeTabBarBadge({ index: 3 })
        }
      }
    },

    setSearchQuery(query) {
      this.searchQuery = query
    },

    setSortBy(sortBy) {
      this.sortBy = sortBy
    },

    setUserLocation({ latitude, longitude }) {
      this.userLatitude = latitude
      this.userLongitude = longitude
    },

    setFilteredNeeds(needs) {
      this.filteredNeeds = needs
    },
  },
})
