import { defineStore } from 'pinia'
import { useUserStore } from './user'
import { useNeedStore } from './need'
import { storage, StorageKeys } from '@/utils/storage'

const COMMISSION_RATE = 0.1
const SHARE_COMMISSION_RATE = 0.02

const ORDER_STATUS = {
  PENDING: 'pending',
  ACCEPTED: 'accepted',
  PENDING_CONFIRM: 'pending_confirm',
  COMPLETED: 'completed',
  CANCELLED: 'cancelled'
}

const INITIAL_ORDERS = [
  {
    id: 'ord1',
    needId: 'n5',
    title: '帮忙搬一箱水',
    description: '4楼没电梯，需帮忙搬一箱矿泉水',
    reward: 12,
    location: '阳光花园7栋',
    latitude: 39.912,
    longitude: 116.400,
    publisher: { id: 'u1', nickname: '热心小周', reputation: 100, completedOrders: 12 },
    helper: { id: 'u6', nickname: '大力士', reputation: 88, completedOrders: 15 },
    status: ORDER_STATUS.ACCEPTED,
    createdAt: Date.now() - 5000000,
    acceptedAt: Date.now() - 4000000,
  },
  {
    id: 'ord2',
    needId: 'n6',
    title: '帮忙取快递',
    description: '3个快递在菜鸟驿站，顺路带回来',
    reward: 8,
    location: '阳光花园3栋',
    latitude: 39.909,
    longitude: 116.398,
    publisher: { id: 'u2', nickname: '李阿姨', reputation: 85, completedOrders: 5 },
    helper: { id: 'u1', nickname: '热心小周', reputation: 100, completedOrders: 12 },
    status: ORDER_STATUS.COMPLETED,
    createdAt: Date.now() - 86400000,
    acceptedAt: Date.now() - 80000000,
    completedAt: Date.now() - 70000000,
    rating: 5,
    comment: '服务非常周到，态度很好，准时送达！',
    tags: ['服务周到', '态度友好', '准时到达']
  },
  {
    id: 'ord3',
    needId: 'n7',
    title: '上门喂猫',
    description: '需要喂食、加水，简单清理猫砂',
    reward: 35,
    location: '绿景苑2单元',
    latitude: 39.911,
    longitude: 116.401,
    publisher: { id: 'u3', nickname: '小林', reputation: 92, completedOrders: 8 },
    helper: { id: 'u1', nickname: '热心小周', reputation: 100, completedOrders: 12 },
    status: ORDER_STATUS.COMPLETED,
    createdAt: Date.now() - 172800000,
    acceptedAt: Date.now() - 160000000,
    completedAt: Date.now() - 150000000,
    rating: 0,
    comment: '',
    tags: []
  },
]

export const useOrderStore = defineStore('order', {
  state: () => ({
    orders: INITIAL_ORDERS,
    currentOrderTab: 'accepted',
    ORDER_STATUS: ORDER_STATUS,
  }),

  getters: {
    pendingOrders: (state) => {
      const userStore = useUserStore()
      return state.orders.filter(o => o.status === ORDER_STATUS.PENDING)
    },

    acceptedOrders: (state) => {
      const userStore = useUserStore()
      return state.orders.filter(o =>
        o.helper && o.helper.id === userStore.currentUser.id &&
        (o.status === ORDER_STATUS.ACCEPTED || o.status === ORDER_STATUS.PENDING_CONFIRM)
      )
    },

    completedOrders: (state) => {
      const userStore = useUserStore()
      return state.orders.filter(o =>
        (o.helper && o.helper.id === userStore.currentUser.id || o.publisher.id === userStore.currentUser.id) &&
        o.status === ORDER_STATUS.COMPLETED
      )
    },

    cancelledOrders: (state) => {
      return state.orders.filter(o => o.status === ORDER_STATUS.CANCELLED)
    },

    pendingConfirmOrders: (state) => {
      const userStore = useUserStore()
      return state.orders.filter(o =>
        (o.helper && o.helper.id === userStore.currentUser.id || o.publisher.id === userStore.currentUser.id) &&
        o.status === ORDER_STATUS.PENDING_CONFIRM
      )
    },
  },

  actions: {
    createOrder(orderData) {
      const order = {
        id: 'ord_' + Date.now(),
        status: ORDER_STATUS.PENDING,
        createdAt: Date.now(),
        helperConfirmed: false,
        publisherConfirmed: false,
        ...orderData
      }
      this.orders.push(order)
      return order
    },

    acceptOrder(orderId, helperInfo) {
      const order = this.orders.find(o => o.id === orderId)
      if (order && order.status === ORDER_STATUS.PENDING) {
        order.status = ORDER_STATUS.ACCEPTED
        order.helper = helperInfo
        order.acceptedAt = Date.now()
        return { success: true }
      }
      return { success: false, message: '订单状态不允许接单' }
    },

    applyComplete(orderId) {
      const order = this.orders.find(o => o.id === orderId)
      if (!order) return { success: false, message: '订单不存在' }

      const userStore = useUserStore()
      const isHelper = order.helper?.id === userStore.currentUser.id

      if (!isHelper) {
        return { success: false, message: '只有帮手才能申请完成' }
      }

      if (order.status !== ORDER_STATUS.ACCEPTED && order.status !== ORDER_STATUS.PENDING_CONFIRM) {
        return { success: false, message: '订单状态不允许此操作' }
      }

      order.helperConfirmed = true
      order.status = ORDER_STATUS.PENDING_CONFIRM
      order.pendingConfirmAt = Date.now()

      const allConvs = storage.getArray(StorageKeys.CONVERSATIONS)
      allConvs.forEach((conv) => {
        if (conv.relatedOrder && conv.relatedOrder.needId === order.needId) {
          conv.relatedOrder.status = ORDER_STATUS.PENDING_CONFIRM
        }
      })
      storage.set(StorageKeys.CONVERSATIONS, allConvs)

      return { success: true }
    },

    confirmComplete(orderId) {
      const order = this.orders.find(o => o.id === orderId)
      if (!order) return { success: false, message: '订单不存在' }

      const userStore = useUserStore()
      const isPublisher = order.publisher?.id === userStore.currentUser.id
      const isHelper = order.helper?.id === userStore.currentUser.id

      if (!isPublisher && !isHelper) {
        return { success: false, message: '无权操作此订单' }
      }

      if (isPublisher) {
        order.publisherConfirmed = true
      } else {
        order.helperConfirmed = true
      }

      if (order.helperConfirmed && order.publisherConfirmed) {
        if (order.settled) {
          order.status = ORDER_STATUS.COMPLETED
          order.completedAt = Date.now()
          return { success: true }
        }
        order.status = ORDER_STATUS.COMPLETED
        order.completedAt = Date.now()

        const platformCommission = order.reward * COMMISSION_RATE
        let shareCommission = 0

        if (order.shareUserId) {
          shareCommission = order.reward * SHARE_COMMISSION_RATE
          userStore.addCommission(shareCommission, order.shareUserId, order.title, order.reward)
        }

        const actualReward = order.reward - platformCommission - shareCommission
        if (order.helper && order.helper.id) {
          userStore.addBalanceToUser(order.helper.id, actualReward)
        }
        order.settled = true

        const allConvs = storage.getArray(StorageKeys.CONVERSATIONS)
        allConvs.forEach((conv) => {
          if (conv.relatedOrder && (conv.relatedOrder.needId === order.needId || conv.relatedOrder.orderId === order.id)) {
            conv.relatedOrder.status = ORDER_STATUS.COMPLETED
          }
        })
        storage.set(StorageKeys.CONVERSATIONS, allConvs)
      }

      return { success: true }
    },

    cancelOrder(orderId) {
      const order = this.orders.find(o => o.id === orderId || o.needId === orderId)
      if (!order) {
        return { success: false, message: '订单不存在' }
      }

      const userStore = useUserStore()
      const isPublisher = order.publisher?.id === userStore.currentUser.id
      const isHelper = order.helper?.id === userStore.currentUser.id

      if (!isPublisher && !isHelper) {
        return { success: false, message: '无权取消此订单' }
      }

      if (order.status !== ORDER_STATUS.PENDING && order.status !== ORDER_STATUS.ACCEPTED) {
        return { success: false, message: '当前状态不允许取消' }
      }

      order.status = ORDER_STATUS.CANCELLED
      order.cancelledAt = Date.now()

      const reward = order.reward || 0
      if (reward > 0 && !order.settled && order.publisher && order.publisher.id) {
        userStore.addBalanceToUser(order.publisher.id, reward)
        const transactions = storage.getArray(StorageKeys.WALLET_TRANSACTIONS)
        transactions.unshift({
          id: Date.now(),
          type: 'refund',
          title: '取消订单退款：' + order.title,
          amount: reward,
          time: Date.now()
        })
        storage.set(StorageKeys.WALLET_TRANSACTIONS, transactions)
      }

      const needStore = useNeedStore()
      const need = needStore.needs.find(n => n.id === order.needId)
      if (need) {
        if (isHelper) {
          need.status = 'open'
          need.helper = null
          need.acceptedAt = null
        } else {
          need.status = ORDER_STATUS.CANCELLED
          need.cancelledAt = Date.now()
        }
      }

      const allConvs = storage.getArray(StorageKeys.CONVERSATIONS)
      if (isPublisher && order.publisher?.id) {
        const convIndex = allConvs.findIndex(c => c.userId === order.publisher.id)
        if (convIndex >= 0 && allConvs[convIndex].relatedOrder) {
          allConvs[convIndex].relatedOrder.status = ORDER_STATUS.CANCELLED
        }
      }
      if (isHelper && order.helper?.id) {
        const convIndex = allConvs.findIndex(c => c.userId === order.helper.id)
        if (convIndex >= 0 && allConvs[convIndex].relatedOrder) {
          allConvs[convIndex].relatedOrder.status = ORDER_STATUS.CANCELLED
        }
      }
      storage.set(StorageKeys.CONVERSATIONS, allConvs)

      return { success: true }
    },

    completeOrder(orderId) {
      const order = this.orders.find(o => o.id === orderId)
      if (!order) return { success: false, message: '订单不存在' }
      if (order.status !== ORDER_STATUS.PENDING_CONFIRM) {
        return { success: false, message: '请先申请完成并等待对方确认' }
      }
      if (order.settled) {
        order.status = ORDER_STATUS.COMPLETED
        order.completedAt = Date.now()
        return order
      }

      if (!order.helperConfirmed || !order.publisherConfirmed) {
        return { success: false, message: '需要双方确认后才能完成订单' }
      }

      const userStore = useUserStore()

      order.status = ORDER_STATUS.COMPLETED
      order.completedAt = Date.now()

      const platformCommission = order.reward * COMMISSION_RATE
      let shareCommission = 0
      if (order.shareUserId) {
        shareCommission = order.reward * SHARE_COMMISSION_RATE
        userStore.addCommission(shareCommission, order.shareUserId, order.title, order.reward)
      }
      const actualReward = order.reward - platformCommission - shareCommission
      if (order.helper && order.helper.id) {
        userStore.addBalanceToUser(order.helper.id, actualReward)
      }
      order.settled = true

      const allConvs = storage.getArray(StorageKeys.CONVERSATIONS)
      if (order.publisher?.id) {
        const convIndex = allConvs.findIndex(c => c.userId === order.publisher.id)
        if (convIndex >= 0 && allConvs[convIndex].relatedOrder) {
          allConvs[convIndex].relatedOrder.status = ORDER_STATUS.COMPLETED
        }
      }
      if (order.helper?.id) {
        const convIndex = allConvs.findIndex(c => c.userId === order.helper.id)
        if (convIndex >= 0 && allConvs[convIndex].relatedOrder) {
          allConvs[convIndex].relatedOrder.status = ORDER_STATUS.COMPLETED
        }
      }
      storage.set(StorageKeys.CONVERSATIONS, allConvs)
      return order
    },

    rateOrder(orderId, rating, comment, tags) {
      const order = this.orders.find(o => o.id === orderId)
      if (order) {
        order.rating = rating
        order.comment = comment
        order.tags = tags || []
        order.isRated = true
        return { success: true }
      }
      return { success: false, message: '订单不存在' }
    },

    setCurrentOrderTab(tab) {
      this.currentOrderTab = tab
    },

    formatTime(timestamp) {
      const date = new Date(timestamp)
      const month = String(date.getMonth() + 1).padStart(2, '0')
      const day = String(date.getDate()).padStart(2, '0')
      const hours = String(date.getHours()).padStart(2, '0')
      const minutes = String(date.getMinutes()).padStart(2, '0')
      return `${month}/${day} ${hours}:${minutes}`
    },

    addOrder(order) {
      this.orders.push(order)
    },

    getStatusText(status) {
      const statusMap = {
        'pending': '待接单',
        'accepted': '进行中',
        'pending_confirm': '待确认',
        'completed': '已完成',
        'cancelled': '已取消'
      }
      return statusMap[status] || status
    },
  },
})
