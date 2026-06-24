export const OrderStatus = {
  OPEN: 'open',
  PENDING: 'pending',
  ACCEPTED: 'accepted',
  IN_PROGRESS: 'in_progress',
  PENDING_CONFIRM: 'pending_confirm',
  COMPLETED: 'completed',
  CANCELLED: 'cancelled'
}

export const NeedStatus = {
  OPEN: 'open',
  ACCEPTED: 'accepted',
  PENDING_CONFIRM: 'pending_confirm',
  COMPLETED: 'completed',
  CANCELLED: 'cancelled'
}

export const PLATFORM_COMMISSION_RATE = 0.05
export const SHARE_COMMISSION_RATE = 0.02

export const CATEGORIES = [
  { name: '跑腿', icon: 'run' },
  { name: '家政', icon: 'housework' },
  { name: '技术', icon: 'wrench' },
  { name: '搬运', icon: 'truck' },
  { name: '代办', icon: 'clipboard-list' },
  { name: '其他', icon: 'others' }
]

export const STATUS_TEXT = {
  [OrderStatus.OPEN]: '待接单',
  [OrderStatus.PENDING]: '待接单',
  [OrderStatus.ACCEPTED]: '进行中',
  [OrderStatus.IN_PROGRESS]: '进行中',
  [OrderStatus.PENDING_CONFIRM]: '待确认',
  [OrderStatus.COMPLETED]: '已完成',
  [OrderStatus.CANCELLED]: '已取消'
}

export const SORT_OPTIONS = [
  { value: 'time', label: '最新' },
  { value: 'reward', label: '金额' },
  { value: 'distance', label: '距离' }
]

export default {
  OrderStatus,
  NeedStatus,
  PLATFORM_COMMISSION_RATE,
  SHARE_COMMISSION_RATE,
  CATEGORIES,
  STATUS_TEXT,
  SORT_OPTIONS
}
