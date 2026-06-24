import { storage, StorageKeys } from './storage'
import { OrderStatus, PLATFORM_COMMISSION_RATE, SHARE_COMMISSION_RATE } from './constants'

export { OrderStatus, PLATFORM_COMMISSION_RATE, SHARE_COMMISSION_RATE }

function generateId(prefix = 'id') {
  return `${prefix}_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
}

function getChatKey(userId1, userId2) {
  const ids = [String(userId1 || 'anonymous'), String(userId2 || 'unknown')].sort()
  return `chat_${ids[0]}_${ids[1]}`
}

export function addTransaction(userId, type, amount, description, relatedId = null) {
  const transactions = storage.getArray(`walletTransactions_${userId}`)
  const transaction = {
    id: generateId('tx'),
    userId,
    type,
    amount,
    description,
    relatedId,
    time: Date.now()
  }
  transactions.unshift(transaction)
  storage.set(`walletTransactions_${userId}`, transactions)
  return transaction
}

export function updateWalletBalance(userId, delta, description, type = 'other', relatedId = null) {
  const balanceKey = `wallet_${userId}`
  const currentBalance = storage.getNumber(balanceKey, 0)
  const newBalance = Math.max(0, currentBalance + delta)
  storage.set(balanceKey, newBalance)

  if (delta !== 0) {
    addTransaction(userId, type, delta, description, relatedId)
  }

  return newBalance
}

export function getWalletBalance(userId) {
  return storage.getNumber(`wallet_${userId}`, 0)
}

export function acceptOrder(need, helper, { shareSource = null } = {}) {
  const reward = Number(need.reward) || 0
  const platformCommission = Number((reward * PLATFORM_COMMISSION_RATE).toFixed(2))
  let shareCommission = 0
  let sharerId = null

  if (shareSource && shareSource.sharerId && shareSource.sharerId !== need.publisher.id) {
    shareCommission = Number((reward * SHARE_COMMISSION_RATE).toFixed(2))
    sharerId = shareSource.sharerId
  }

  const helperEarnings = Number((reward - platformCommission - shareCommission).toFixed(2))

  const order = {
    id: generateId('o'),
    needId: need.id,
    needTitle: need.title,
    needDescription: need.description,
    needCategory: need.category,
    publisher: need.publisher,
    helper,
    reward,
    platformCommission,
    shareCommission,
    sharerId,
    status: OrderStatus.ACCEPTED,
    acceptedAt: Date.now(),
    createdAt: need.createdAt || Date.now()
  }

  updateWalletBalance(
    need.publisher.id,
    -reward,
    `发布需求「${need.title}」冻结金额`,
    'freeze',
    order.id
  )

  return { order, helperEarnings, platformCommission, shareCommission }
}

export function cancelOrder(order, cancelledBy = 'publisher') {
  const isPublisher = cancelledBy === 'publisher'
  const isHelper = cancelledBy === 'helper'

  order.status = OrderStatus.CANCELLED
  order.cancelledAt = Date.now()
  order.cancelledBy = cancelledBy

  if (isPublisher) {
    updateWalletBalance(
      order.publisher.id,
      Number(order.reward),
      `需求「${order.needTitle}」取消，退还冻结金额`,
      'refund',
      order.id
    )
  }

  return order
}

export function completeOrder(order) {
  const reward = Number(order.reward) || 0
  const platformCommission = Number(order.platformCommission) || 0
  const shareCommission = Number(order.shareCommission) || 0
  const helperEarnings = Number((reward - platformCommission - shareCommission).toFixed(2))

  order.status = OrderStatus.PENDING_CONFIRM
  order.pendingConfirmAt = Date.now()

  return { order, helperEarnings }
}

export function confirmOrder(order) {
  const reward = Number(order.reward) || 0
  const platformCommission = Number(order.platformCommission) || 0
  const shareCommission = Number(order.shareCommission) || 0
  const helperEarnings = Number((reward - platformCommission - shareCommission).toFixed(2))

  order.status = OrderStatus.COMPLETED
  order.completedAt = Date.now()

  if (order.helper) {
    updateWalletBalance(
      order.helper.id,
      helperEarnings,
      `完成需求「${order.needTitle}」获得收入`,
      'income',
      order.id
    )
  }

  if (shareCommission > 0 && order.sharerId) {
    updateWalletBalance(
      order.sharerId,
      shareCommission,
      `分享需求「${order.needTitle}」获得佣金`,
      'share_income',
      order.id
    )
  }

  return { order, helperEarnings, platformCommission, shareCommission }
}

export function createConversation(publisher, helper, need, order = null) {
  const chatKey = getChatKey(publisher.id, helper.id)
  const allConvs = storage.getArray(StorageKeys.CONVERSATIONS)
  const existingIndex = allConvs.findIndex((c) => c.chatKey === chatKey)

  const conversation = {
    chatKey,
    otherUserId: helper.id,
    otherUser: helper,
    publisher,
    helper,
    lastMessage: '我们聊聊需求详情吧~',
    lastTime: Date.now(),
    unread: 1,
    relatedNeed: need ? { id: need.id, title: need.title } : null,
    relatedOrder: order ? { id: order.id, status: order.status } : null
  }

  const systemMsg = {
    id: generateId('msg'),
    type: 'system',
    content: '你们已匹配成功，开始沟通需求详情吧！',
    time: Date.now()
  }
  const welcomeMsg = {
    id: generateId('msg'),
    sender: helper.id,
    type: 'text',
    text: '你好，我可以帮你完成这个需求，我们聊聊具体细节吧~',
    time: Date.now(),
    sendStatus: 'sent'
  }

  const allMessages = storage.getObject(StorageKeys.CHAT_MESSAGES)
  if (!allMessages[chatKey]) {
    allMessages[chatKey] = []
  }
  allMessages[chatKey].push(systemMsg)
  allMessages[chatKey].push(welcomeMsg)
  storage.set(StorageKeys.CHAT_MESSAGES, allMessages)

  if (existingIndex > -1) {
    allConvs[existingIndex] = { ...allConvs[existingIndex], ...conversation }
  } else {
    allConvs.unshift(conversation)
  }
  storage.set(StorageKeys.CONVERSATIONS, allConvs)

  return conversation
}

export function updateConversationLastMessage(chatKey, message, time = Date.now()) {
  const allConvs = storage.getArray(StorageKeys.CONVERSATIONS)
  const index = allConvs.findIndex((c) => c.chatKey === chatKey)
  if (index > -1) {
    allConvs[index].lastMessage = message
    allConvs[index].lastTime = time
    allConvs[index].unread = (allConvs[index].unread || 0) + 1
    storage.set(StorageKeys.CONVERSATIONS, allConvs)
  }
}

export function addNotification(userId, type, title, content, relatedId = null) {
  const notifications = storage.getArray(StorageKeys.NOTIFICATIONS)
  const notification = {
    id: generateId('notif'),
    userId,
    type,
    title,
    content,
    relatedId,
    read: false,
    time: Date.now()
  }
  notifications.unshift(notification)
  storage.set(StorageKeys.NOTIFICATIONS, notifications)

  if (typeof uni !== 'undefined' && uni.$emit) {
    uni.$emit('updateBadge')
  }

  return notification
}

export default {
  OrderStatus,
  PLATFORM_COMMISSION_RATE,
  SHARE_COMMISSION_RATE,
  generateId,
  getChatKey,
  addTransaction,
  updateWalletBalance,
  getWalletBalance,
  acceptOrder,
  cancelOrder,
  completeOrder,
  confirmOrder,
  createConversation,
  updateConversationLastMessage,
  addNotification
}
