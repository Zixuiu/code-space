import { defineStore } from 'pinia'
import { useNeedStore } from './need'
import { useOrderStore } from './order'
import { useUserStore } from './user'

const SIMULATION_USERS = [
  { id: 'sim1', nickname: '热心张叔', reputation: 88, completedOrders: 15, avatar: '', skills: ['跑腿', '家政'], active: true },
  { id: 'sim2', nickname: '小李子', reputation: 92, completedOrders: 23, avatar: '', skills: ['技术', '跑腿'], active: true },
  { id: 'sim3', nickname: '王姐家政', reputation: 85, completedOrders: 31, avatar: '', skills: ['家政', '其他'], active: true },
  { id: 'sim4', nickname: 'IT达人', reputation: 96, completedOrders: 18, avatar: '', skills: ['技术'], active: true },
  { id: 'sim5', nickname: '阳光邻居', reputation: 78, completedOrders: 8, avatar: '', skills: ['跑腿', '其他'], active: true },
]

const NEED_TEMPLATES = [
  { category: '跑腿', titles: ['帮忙取快递', '顺路带个东西', '帮忙买个菜', '取个包裹'], descriptions: ['在菜鸟驿站，顺路带回来', '小区门口便利店买一下', '快递到了取一下', '帮忙捎一下'], rewards: [5, 8, 10, 12, 15] },
  { category: '家政', titles: ['上门喂猫', '帮忙遛狗', '打扫卫生', '陪老人聊天'], descriptions: ['需要喂食、加水', '小区内遛半小时', '简单打扫一下', '陪老人散散步聊聊天'], rewards: [25, 30, 35, 40, 50] },
  { category: '技术', titles: ['修个电脑', '帮忙调下网络', '手机设置一下', '教下怎么用'], descriptions: ['系统卡顿清理一下', '网络有点问题帮忙看看', '老人手机不会用教一下', '软件设置一下'], rewards: [30, 40, 50, 60, 80] },
  { category: '其他', titles: ['帮个小忙', '咨询个事情', '搭把手', '帮下忙'], descriptions: ['临时有事搭把手', '有点小事请教一下', '帮个小忙', '邻里互助一下'], rewards: [10, 15, 20, 25, 30] },
]

const LOCATIONS = ['阳光花园', '绿景苑', '夕阳红社区', '智慧家园', '和谐小区', '幸福里', '金色家园', '湖畔小区']

const MESSAGE_TEMPLATES = {
  greeting: ['你好！', '您好~', '嗨！', '哈喽~', '你好呀！'],
  accepted: ['好的，我接了这个单！', '收到，我马上过去~', '没问题，这个我可以帮忙！', '好的，这个我来！', 'OK，我接了！'],
  confirm: ['太好了，谢谢！', '太感谢了！', '好的，辛苦你了！', '太好了，麻烦你了！', '非常感谢！'],
  question: ['请问什么时候方便？', '大概多久能到？', '需要我准备什么吗？', '请问地址是这里吗？', '请问需要带什么工具吗？'],
  update: ['我现在出发了~', '我快到了！', '已经在路上了~', '还有5分钟到！', '已经到楼下了！'],
  complete: ['已经完成了~', '好的，我弄完了！', '已经搞定了！', '好了，检查一下！', '完成了，您看看！'],
  thanks: ['辛苦了！', '非常感谢！', '谢谢，太感谢了！', '太谢谢你了！', '谢谢你的帮助！'],
  small_talk: ['今天天气不错~', '最近忙不忙？', '吃饭了吗？', '周末怎么安排的？', '最近小区挺热闹的！'],
  emoji: ['😊', '👍', '🙏', '✨', '🎉', '☕', '🌸', '☀️', '🌟', '💪', '🎯', '🏃', '🚀', '💯', '❤️']
}

export const useSimulationStore = defineStore('simulation', {
  state: () => ({
    isRunning: false,
    simulationUsers: [...SIMULATION_USERS],
    activityLog: [],
    publishInterval: 5000,
    acceptInterval: 3000,
    completeInterval: 5000,
    confirmInterval: 3000,
    maxActiveNeeds: 10,
    simulationTimers: [],
  }),

  getters: {
    activeUsers: (state) => state.simulationUsers.filter(u => u.active),
    randomUser: (state) => state.activeUsers[Math.floor(Math.random() * state.activeUsers.length)],
  },

  actions: {
    logActivity(type, message, user = null) {
      const entry = {
        id: Date.now(),
        type,
        message,
        user,
        timestamp: new Date().toLocaleTimeString(),
      }
      this.activityLog.unshift(entry)
      if (this.activityLog.length > 100) {
        this.activityLog = this.activityLog.slice(0, 100)
      }
    },

    generateRandomNeed() {
      const template = NEED_TEMPLATES[Math.floor(Math.random() * NEED_TEMPLATES.length)]
      const title = template.titles[Math.floor(Math.random() * template.titles.length)]
      const description = template.descriptions[Math.floor(Math.random() * template.descriptions.length)]
      const reward = template.rewards[Math.floor(Math.random() * template.rewards.length)]
      const location = LOCATIONS[Math.floor(Math.random() * LOCATIONS.length)]
      const unit = `${1 + Math.floor(Math.random() * 10)}栋${1 + Math.floor(Math.random() * 5)}单元`
      
      const user = this.randomUser
      if (!user) return null

      return {
        title,
        description,
        reward,
        location: `${location}${unit}`,
        category: template.category,
        latitude: 39.908 + (Math.random() - 0.5) * 0.02,
        longitude: 116.397 + (Math.random() - 0.5) * 0.02,
        publisher: user,
      }
    },

    publishRandomNeed() {
      const needStore = useNeedStore()
      const openNeeds = needStore.openNeeds.length
      
      if (openNeeds >= this.maxActiveNeeds) {
        return { published: false, reason: '活跃需求已达上限' }
      }

      const needData = this.generateRandomNeed()
      if (!needData) {
        return { published: false, reason: '没有活跃的模拟用户' }
      }

      const originalUser = useUserStore().currentUser
      const originalIsLoggedIn = useUserStore().isLoggedIn
      
      useUserStore().currentUser = needData.publisher
      useUserStore().isLoggedIn = true

      const newNeed = needStore.addNeed({
        title: needData.title,
        description: needData.description,
        reward: needData.reward,
        location: needData.location,
        category: needData.category,
        latitude: needData.latitude,
        longitude: needData.longitude,
      })

      useUserStore().currentUser = originalUser
      useUserStore().isLoggedIn = originalIsLoggedIn

      this.logActivity('publish', `${needData.publisher.nickname} 发布了「${needData.title}」`, needData.publisher)
      
      return { published: true, need: newNeed }
    },

    acceptRandomNeed() {
      const needStore = useNeedStore()
      const userStore = useUserStore()
      const openNeeds = needStore.openNeeds
      
      if (openNeeds.length === 0) {
        return { accepted: false, reason: '没有可接的需求' }
      }

      const need = openNeeds[Math.floor(Math.random() * openNeeds.length)]
      const user = this.activeUsers.find(u => u.id !== need.publisher.id)
      
      if (!user) {
        return { accepted: false, reason: '没有合适的接单用户' }
      }

      const originalUserId = userStore.currentUser?.id || ''
      const originalUser = { ...userStore.currentUser }
      const originalIsLoggedIn = userStore.isLoggedIn
      
      userStore.currentUser = user
      userStore.isLoggedIn = true

      const result = needStore.acceptNeed(need.id)

      userStore.currentUser = originalUser
      userStore.isLoggedIn = originalIsLoggedIn

      if (result.success) {
        const isCurrentUserPublisher = need.publisher.id === originalUserId
        
        console.log('=== DEBUG - acceptRandomNeed ===')
        console.log('originalUserId:', originalUserId)
        console.log('need.publisher.id:', need.publisher.id)
        console.log('isCurrentUserPublisher:', isCurrentUserPublisher)
        
        if (isCurrentUserPublisher) {
          const chatKey = this.getChatKey(need.publisher.id, user.id)
          console.log('chatKey:', chatKey)
          
          const allMessages = uni.getStorageSync('chatMessages') || {}
          console.log('allMessages before:', allMessages)
          
          if (!allMessages[chatKey]) {
            allMessages[chatKey] = []
          }
          
          const systemMsg = {
            id: `msg_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
            type: 'text',
            text: `已接单，可以开始聊天了~`,
            time: Date.now(),
            isSelf: false
          }
          
          const welcomeMsg = {
            id: `msg_${Date.now() + 1}_${Math.random().toString(36).substr(2, 9)}`,
            type: 'text',
            text: `您好！我是${user.nickname}，很高兴接单！请问什么时候方便呢？`,
            time: Date.now() + 1000,
            isSelf: false
          }
          
          allMessages[chatKey].push(systemMsg)
          allMessages[chatKey].push(welcomeMsg)
          uni.setStorageSync('chatMessages', allMessages)
          
          console.log('allMessages after:', allMessages)
          
          const allConvs = uni.getStorageSync('conversations') || []
          
          const convUserId = originalUserId === need.publisher.id ? user.id : need.publisher.id
          const convNickname = originalUserId === need.publisher.id ? user.nickname : need.publisher.nickname
          
          const existingIndex = allConvs.findIndex(c => c.userId === convUserId)

          if (existingIndex >= 0) {
            const existing = allConvs[existingIndex]
            existing.lastMessage = `您好！我是${user.nickname}，很高兴接单！`
            existing.lastTime = Date.now() + 1000
            existing.unread = (existing.unread || 0) + 2
            existing.online = true
            existing.relatedOrder = {
              needId: need.id,
              orderId: result.order.id,
              title: need.title,
              reward: need.reward,
              status: 'accepted',
              publisher: { ...need.publisher },
              helper: { ...user }
            }
          } else {
            allConvs.unshift({
              id: `conv_${convUserId}`,
              userId: convUserId,
              nickname: convNickname,
              lastMessage: `您好！我是${user.nickname}，很高兴接单！`,
              lastTime: Date.now() + 1000,
              unread: 2,
              online: true,
              relatedOrder: {
                needId: need.id,
                orderId: result.order.id,
                title: need.title,
                reward: need.reward,
                status: 'accepted',
                publisher: { ...need.publisher },
                helper: { ...user }
              }
            })
          }
          uni.setStorageSync('conversations', allConvs)
        }
        
        this.logActivity('accept', `${user.nickname} 接了 ${need.publisher.nickname} 的「${need.title}」`, user)
        return { accepted: true, need, user }
      } else {
        return { accepted: false, reason: result.message }
      }
    },

    cancelRandomNeed() {
      const needStore = useNeedStore()
      const publishedNeeds = needStore.needs.filter(n => n.status === 'open' && this.activeUsers.some(u => u.id === n.publisher.id))
      
      if (publishedNeeds.length === 0) {
        return { cancelled: false, reason: '没有可取消的需求' }
      }

      const need = publishedNeeds[Math.floor(Math.random() * publishedNeeds.length)]
      const user = need.publisher

      const originalUser = useUserStore().currentUser
      const originalIsLoggedIn = useUserStore().isLoggedIn
      
      useUserStore().currentUser = user
      useUserStore().isLoggedIn = true

      const result = needStore.cancelNeed(need.id)

      useUserStore().currentUser = originalUser
      useUserStore().isLoggedIn = originalIsLoggedIn

      if (result.success) {
        this.logActivity('cancel', `${user.nickname} 取消了「${need.title}」`, user)
        return { cancelled: true, need }
      } else {
        return { cancelled: false, reason: result.message }
      }
    },

    markCompleteRandomNeed() {
      const needStore = useNeedStore()
      const userStore = useUserStore()
      const acceptedNeeds = needStore.needs.filter(n => n.status === 'accepted' && n.helper && this.activeUsers.some(u => u.id === n.helper.id))
      
      if (acceptedNeeds.length === 0) {
        return { marked: false, reason: '没有可标记完成的需求' }
      }

      const need = acceptedNeeds[Math.floor(Math.random() * acceptedNeeds.length)]
      const user = need.helper

      const originalUserId = userStore.currentUser?.id || ''
      const originalUser = { ...userStore.currentUser }
      const originalIsLoggedIn = userStore.isLoggedIn
      
      userStore.currentUser = user
      userStore.isLoggedIn = true

      const result = needStore.markComplete(need.id)

      userStore.currentUser = originalUser
      userStore.isLoggedIn = originalIsLoggedIn

      if (result.success) {
        const isCurrentUserPublisher = need.publisher.id === originalUserId
        
        if (isCurrentUserPublisher) {
          const chatKey = this.getChatKey(need.publisher.id, user.id)
          const allMessages = uni.getStorageSync('chatMessages') || {}
          if (!allMessages[chatKey]) {
            allMessages[chatKey] = []
          }
          
          const completeMsg = {
            id: `msg_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
            type: 'text',
            text: `您好！我已经完成了「${need.title}」，麻烦您确认一下！`,
            time: Date.now(),
            isSelf: false
          }
          
          allMessages[chatKey].push(completeMsg)
          uni.setStorageSync('chatMessages', allMessages)
          
          const allConvs = uni.getStorageSync('conversations') || []
          const existingIndex = allConvs.findIndex(c => c.userId === user.id)
          
          if (existingIndex >= 0) {
            allConvs[existingIndex].lastMessage = `您好！我已经完成了「${need.title}」，麻烦您确认一下！`
            allConvs[existingIndex].lastTime = Date.now()
            allConvs[existingIndex].unread = (allConvs[existingIndex].unread || 0) + 1
            if (allConvs[existingIndex].relatedOrder) {
              allConvs[existingIndex].relatedOrder.status = 'pending_confirm'
            }
          }
          uni.setStorageSync('conversations', allConvs)
        }
        
        this.logActivity('complete', `${user.nickname} 完成了 ${need.publisher.nickname} 的「${need.title}」`, user)
        return { marked: true, need }
      } else {
        return { marked: false, reason: result.message }
      }
    },

    confirmCompleteRandomNeed() {
      const needStore = useNeedStore()
      const userStore = useUserStore()
      const originalUserId = userStore.currentUser?.id || ''

      const pendingNeeds = needStore.needs.filter(n =>
        n.status === 'pending_confirm' &&
        (this.activeUsers.some(u => u.id === n.publisher.id) ||
         this.activeUsers.some(u => u.id === n.helper?.id) ||
         (n.helper?.id === originalUserId && n.publisher?.id !== originalUserId))
      )

      if (pendingNeeds.length === 0) {
        return { confirmed: false, reason: '没有待确认的需求' }
      }

      const need = pendingNeeds[Math.floor(Math.random() * pendingNeeds.length)]

      const isCurrentUserPublisher = need.publisher?.id === originalUserId

      if (isCurrentUserPublisher) {
        return { confirmed: false, reason: '不代替真实用户确认订单' }
      }

      const isPublisherSimUser = this.activeUsers.some(u => u.id === need.publisher.id)
      const isHelperSimUser = this.activeUsers.some(u => u.id === need.helper?.id)
      const user = isPublisherSimUser ? need.publisher :
                   (isHelperSimUser ? need.helper : need.publisher)

      if (!user) {
        return { confirmed: false, reason: '没有合适的确认用户' }
      }

      const originalUser = { ...userStore.currentUser }
      const originalIsLoggedIn = userStore.isLoggedIn

      userStore.currentUser = user
      userStore.isLoggedIn = true

      const result = needStore.confirmComplete(need.id)

      userStore.currentUser = originalUser
      userStore.isLoggedIn = originalIsLoggedIn

      if (result.success) {
        const isCurrentUserHelper = need.helper?.id === originalUserId

        if (isCurrentUserHelper && need.helper) {
          const chatKey = this.getChatKey(need.helper.id, need.publisher.id)
          const allMessages = uni.getStorageSync('chatMessages') || {}
          if (!allMessages[chatKey]) {
            allMessages[chatKey] = []
          }

          const confirmMsg = {
            id: `msg_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
            type: 'text',
            text: `太好了！谢谢您的确认！「${need.title}」圆满完成！`,
            time: Date.now(),
            isSelf: false
          }

          allMessages[chatKey].push(confirmMsg)
          uni.setStorageSync('chatMessages', allMessages)

          const allConvs = uni.getStorageSync('conversations') || []
          const existingIndex = allConvs.findIndex(c => c.userId === need.helper.id)

          if (existingIndex >= 0) {
            allConvs[existingIndex].lastMessage = `太好了！谢谢您的确认！「${need.title}」圆满完成！`
            allConvs[existingIndex].lastTime = Date.now()
            allConvs[existingIndex].unread = (allConvs[existingIndex].unread || 0) + 1
            if (allConvs[existingIndex].relatedOrder) {
              allConvs[existingIndex].relatedOrder.status = 'completed'
            }
          }
          uni.setStorageSync('conversations', allConvs)
        }

        this.logActivity('confirm', `${user.nickname} 确认了 ${need.helper.nickname} 的「${need.title}」完成`, user)
        return { confirmed: true, need }
      } else {
        return { confirmed: false, reason: result.message }
      }
    },

    randomAction() {
      const actions = [
        { action: 'publish', weight: 4 },
        { action: 'accept', weight: 5 },
        { action: 'cancel', weight: 1 },
        { action: 'complete', weight: 2 },
        { action: 'confirm', weight: 2 },
      ]

      const totalWeight = actions.reduce((sum, a) => sum + a.weight, 0)
      let random = Math.random() * totalWeight
      
      let selectedAction = 'publish'
      for (const a of actions) {
        random -= a.weight
        if (random <= 0) {
          selectedAction = a.action
          break
        }
      }

      switch (selectedAction) {
        case 'publish':
          this.publishRandomNeed()
          break
        case 'accept':
          this.acceptRandomNeed()
          break
        case 'cancel':
          this.cancelRandomNeed()
          break
        case 'complete':
          this.markCompleteRandomNeed()
          break
        case 'confirm':
          this.confirmCompleteRandomNeed()
          break
      }
    },

    startSimulation() {
      if (this.isRunning) return

      this.isRunning = true
      this.logActivity('system', '模拟用户开始运行')

      const publishTimer = setInterval(() => {
        if (this.isRunning) {
          this.publishRandomNeed()
        }
      }, this.publishInterval)

      const acceptTimer = setInterval(() => {
        if (this.isRunning) {
          this.acceptRandomNeed()
        }
      }, this.acceptInterval)

      const messageTimer = setInterval(() => {
        if (this.isRunning) {
          this.sendRandomMessage()
        }
      }, 5000)

      const completeTimer = setInterval(() => {
        if (this.isRunning) {
          this.markCompleteRandomNeed()
        }
      }, this.completeInterval)

      const confirmTimer = setInterval(() => {
        if (this.isRunning) {
          this.confirmCompleteRandomNeed()
        }
      }, this.confirmInterval)

      const cancelTimer = setInterval(() => {
        if (this.isRunning && Math.random() < 0.3) {
          this.cancelRandomNeed()
        }
      }, 5000)

      this.simulationTimers = [publishTimer, acceptTimer, messageTimer, completeTimer, confirmTimer, cancelTimer]
    },

    stopSimulation() {
      this.isRunning = false
      this.simulationTimers.forEach(timer => clearInterval(timer))
      this.simulationTimers = []
      this.logActivity('system', '模拟用户已停止')
    },

    toggleUserActive(userId) {
      const user = this.simulationUsers.find(u => u.id === userId)
      if (user) {
        user.active = !user.active
        this.logActivity('system', `${user.nickname} ${user.active ? '上线了' : '下线了'}`)
      }
    },

    setPublishInterval(ms) {
      this.publishInterval = ms
      if (this.isRunning) {
        this.stopSimulation()
        this.startSimulation()
      }
    },

    setAcceptInterval(ms) {
      this.acceptInterval = ms
      if (this.isRunning) {
        this.stopSimulation()
        this.startSimulation()
      }
    },

    setCompleteInterval(ms) {
      this.completeInterval = ms
      if (this.isRunning) {
        this.stopSimulation()
        this.startSimulation()
      }
    },

    setConfirmInterval(ms) {
      this.confirmInterval = ms
      if (this.isRunning) {
        this.stopSimulation()
        this.startSimulation()
      }
    },

    clearLog() {
      this.activityLog = []
    },

    sendRandomMessage() {
      const orderStore = useOrderStore()
      const userStore = useUserStore()
      const activeOrders = orderStore.orders.filter(o => 
        o.status === 'accepted' || o.status === 'pending_confirm'
      )

      if (activeOrders.length === 0) {
        return { success: false, message: '没有活跃订单' }
      }

      const originalUserId = userStore.currentUser?.id || ''
      
      const ordersWithCurrentUser = activeOrders.filter(o => 
        o.publisher?.id === originalUserId || o.helper?.id === originalUserId
      )
      
      let order
      if (ordersWithCurrentUser.length > 0) {
        order = ordersWithCurrentUser[Math.floor(Math.random() * ordersWithCurrentUser.length)]
      } else {
        order = activeOrders[Math.floor(Math.random() * activeOrders.length)]
      }
      
      const publisher = order.publisher
      const helper = order.helper

      if (!publisher || !helper) {
        return { success: false, message: '订单信息不完整' }
      }

      let fromUser, toUser
      if (publisher.id === originalUserId) {
        fromUser = helper
        toUser = publisher
      } else if (helper.id === originalUserId) {
        fromUser = publisher
        toUser = helper
      } else {
        const isPublisher = Math.random() > 0.5
        fromUser = isPublisher ? publisher : helper
        toUser = isPublisher ? helper : publisher
      }

      const messageTypes = ['greeting', 'question', 'update', 'small_talk', 'emoji']
      
      let messageType
      if (order.status === 'accepted') {
        messageType = ['accepted', 'confirm', 'question', 'update', 'small_talk', 'emoji'][Math.floor(Math.random() * 6)]
      } else if (order.status === 'pending_confirm') {
        messageType = ['complete', 'thanks', 'confirm', 'small_talk', 'emoji'][Math.floor(Math.random() * 5)]
      } else {
        messageType = messageTypes[Math.floor(Math.random() * messageTypes.length)]
      }

      const messages = MESSAGE_TEMPLATES[messageType]
      const messageText = messages[Math.floor(Math.random() * messages.length)]

      const chatKey = this.getChatKey(fromUser.id, toUser.id)
      const allMessages = uni.getStorageSync('chatMessages') || {}
      if (!allMessages[chatKey]) {
        allMessages[chatKey] = []
      }

      const msg = {
        id: `msg_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
        type: 'text',
        text: messageText,
        time: Date.now(),
        isSelf: fromUser.id === originalUserId
      }

      allMessages[chatKey].push(msg)
      uni.setStorageSync('chatMessages', allMessages)

      this.updateConversation(fromUser, toUser, messageText, order, originalUserId)

      this.logActivity('message', `${fromUser.nickname} 给 ${toUser.nickname} 发了消息`, fromUser)

      return { success: true, from: fromUser, to: toUser, message: messageText, order }
    },

    getChatKey(id1, id2) {
      const ids = [id1, id2].sort()
      return `chat_${ids[0]}_${ids[1]}`
    },

    updateConversation(fromUser, toUser, messageText, order, originalUserId) {
      const allConvs = uni.getStorageSync('conversations') || []
      
      const convUserId = originalUserId === fromUser.id ? toUser.id : fromUser.id
      const convNickname = originalUserId === fromUser.id ? toUser.nickname : fromUser.nickname
      
      const existingIndex = allConvs.findIndex(c => c.userId === convUserId)
      
      let unread = 1
      if (existingIndex >= 0 && allConvs[existingIndex].unread !== undefined) {
        unread = allConvs[existingIndex].unread + 1
      }

      if (existingIndex >= 0) {
        const existing = allConvs[existingIndex]
        existing.lastMessage = messageText
        existing.lastTime = Date.now()
        existing.unread = unread
        existing.online = true
        existing.nickname = convNickname
        if (order) {
          existing.relatedOrder = {
            needId: order.needId || order.id,
            orderId: order.id,
            title: order.title,
            reward: order.reward,
            status: order.status,
            publisher: order.publisher ? { ...order.publisher } : existing.relatedOrder?.publisher,
            helper: order.helper ? { ...order.helper } : existing.relatedOrder?.helper
          }
        }
      } else {
        allConvs.unshift({
          id: `conv_${convUserId}`,
          userId: convUserId,
          nickname: convNickname,
          lastMessage: messageText,
          lastTime: Date.now(),
          unread: unread,
          online: true,
          relatedOrder: order ? {
            needId: order.needId || order.id,
            orderId: order.id,
            title: order.title,
            reward: order.reward,
            status: order.status,
            publisher: { ...order.publisher },
            helper: { ...order.helper }
          } : null
        })
      }
      uni.setStorageSync('conversations', allConvs)
      
      uni.$emit('updateMessageBadge')
    }
  },
})
