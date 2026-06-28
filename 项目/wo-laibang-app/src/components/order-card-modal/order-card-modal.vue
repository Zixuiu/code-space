<template>
  <view v-if="visible" class="order-card-mask" @click="handleMaskClick">
    <view class="order-card-popup" @click.stop>
      <view class="order-card-content">
        <view class="order-card-header">
          <text class="order-card-title">订单详情</text>
          <view class="order-card-status" :class="'order-status-' + order?.status">
            {{ getStatusText(order?.status) }}
          </view>
        </view>
        <view class="order-card-order-title">{{ order?.title }}</view>
        <view class="order-card-reward-row">
          <text class="order-card-reward-label">酬劳</text>
          <text class="order-card-reward-value">¥{{ order?.reward }}</text>
        </view>
        <view class="order-card-participants">
          <view class="order-card-participant">
            <view class="order-card-avatar order-card-avatar-publisher">
              <text class="order-card-avatar-text">发</text>
            </view>
            <text class="order-card-participant-name">{{ order?.publisher?.nickname || '发布者' }}</text>
          </view>
          <view class="order-card-participant">
            <view class="order-card-avatar order-card-avatar-helper">
              <text class="order-card-avatar-text">帮</text>
            </view>
            <text class="order-card-participant-name">{{ order?.helper?.nickname || '帮手' }}</text>
          </view>
        </view>
        <view class="order-card-actions">
          <view class="order-card-btn order-card-btn-secondary" @click="handleClose">
            <text class="order-card-btn-text">关闭</text>
          </view>
          <view class="order-card-btn order-card-btn-primary" @click="handleViewDetail">
            <text class="order-card-btn-text order-card-btn-text-primary">查看详情</text>
          </view>
        </view>
      </view>
    </view>
  </view>
</template>

<script>
export default {
  name: 'OrderCardModal',
  props: {
    visible: {
      type: Boolean,
      default: false
    },
    order: {
      type: Object,
      default: null
    }
  },
  methods: {
    getStatusText(status) {
      const map = {
        'open': '待接单',
        'accepted': '进行中',
        'pending_confirm': '待确认',
        'completed': '已完成',
        'cancelled': '已取消'
      }
      return map[status] || status
    },
    handleMaskClick() {
      this.$emit('update:visible', false)
      this.$emit('close')
    },
    handleClose() {
      this.$emit('update:visible', false)
      this.$emit('close')
    },
    handleViewDetail() {
      if (this.order?.needId) {
        this.$emit('view-detail', this.order)
      }
    }
  }
}
</script>

<style scoped>
.order-card-mask {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  z-index: 99999;
  display: flex;
  align-items: center;
  justify-content: center;
}

.order-card-popup {
  width: 600rpx;
  background: #FFFFFF;
  border-radius: 32rpx;
  overflow: hidden;
}

.order-card-content {
  padding: 32rpx;
}

.order-card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20rpx;
}

.order-card-title {
  font-size: 32rpx;
  font-weight: 800;
  color: #1E293B;
}

.order-card-status {
  font-size: 24rpx;
  padding: 8rpx 16rpx;
  border-radius: 16rpx;
}

.order-status-accepted {
  background: #ECFDF5;
  color: #10B981;
}

.order-status-pending_confirm {
  background: #FFFBEB;
  color: #F59E0B;
}

.order-status-completed {
  background: #F1F5F9;
  color: #64748B;
}

.order-status-cancelled {
  background: #FEE2E2;
  color: #EF4444;
}

.order-status-open {
  background: #DBEAFE;
  color: #3B82F6;
}

.order-card-order-title {
  font-size: 28rpx;
  font-weight: 700;
  color: #1E293B;
  margin-bottom: 16rpx;
}

.order-card-reward-row {
  display: flex;
  align-items: center;
  gap: 8rpx;
  margin-bottom: 12rpx;
}

.order-card-reward-label {
  font-size: 24rpx;
  color: #64748B;
}

.order-card-reward-value {
  font-size: 32rpx;
  font-weight: 800;
  color: #10B981;
}

.order-card-participants {
  border-top: 1rpx solid #F1F5F9;
  padding-top: 20rpx;
  margin-top: 20rpx;
}

.order-card-participant {
  display: flex;
  align-items: center;
  gap: 12rpx;
  margin-bottom: 16rpx;
}

.order-card-participant:last-child {
  margin-bottom: 0;
}

.order-card-avatar {
  width: 40rpx;
  height: 40rpx;
  border-radius: 20rpx;
  display: flex;
  align-items: center;
  justify-content: center;
}

.order-card-avatar-publisher {
  background: #ECFDF5;
}

.order-card-avatar-helper {
  background: #F1F5F9;
}

.order-card-avatar-text {
  font-size: 20rpx;
  font-weight: 700;
}

.order-card-avatar-publisher .order-card-avatar-text {
  color: #10B981;
}

.order-card-avatar-helper .order-card-avatar-text {
  color: #64748B;
}

.order-card-participant-name {
  font-size: 28rpx;
  color: #1E293B;
  font-weight: 600;
}

.order-card-actions {
  display: flex;
  gap: 16rpx;
  margin-top: 24rpx;
}

.order-card-btn {
  flex: 1;
  height: 88rpx;
  border-radius: 22rpx;
  display: flex;
  align-items: center;
  justify-content: center;
}

.order-card-btn-secondary {
  background: #F1F5F9;
}

.order-card-btn-primary {
  background: linear-gradient(135deg, #10B981, #059669);
}

.order-card-btn-text {
  font-size: 28rpx;
  font-weight: 700;
}

.order-card-btn-secondary .order-card-btn-text {
  color: #64748B;
}

.order-card-btn-text-primary {
  color: #FFFFFF;
}
</style>