<template>
  <view class="simulation-container">
    <view class="header">
      <view class="title">模拟用户控制中心</view>
      <view class="subtitle">让虚拟邻居们帮你测试平台功能</view>
    </view>

    <view class="control-section">
      <view class="section-title">主控制</view>
      <view class="control-buttons">
        <button
          :class="['control-btn', simulationStore.isRunning ? 'running' : 'start']"
          @click="toggleSimulation"
        >
          {{ simulationStore.isRunning ? '⏹ 停止模拟' : '▶ 开始模拟' }}
        </button>
        <button class="control-btn single-action" @click="simulationStore.publishRandomNeed">
          发布需求
        </button>
        <button class="control-btn single-action" @click="simulationStore.acceptRandomNeed">
          接单
        </button>
        <button class="control-btn single-action" @click="simulationStore.sendRandomMessage">
          发送消息
        </button>
        <button class="control-btn single-action" @click="simulationStore.markCompleteRandomNeed">
          标记完成
        </button>
        <button class="control-btn single-action" @click="simulationStore.confirmCompleteRandomNeed">
          确认完成
        </button>
      </view>
    </view>

    <view class="control-section">
      <view class="section-title">模拟设置</view>
      <view class="setting-item">
        <view class="setting-label">发布间隔</view>
        <view class="setting-value">
          <slider
            :value="simulationStore.publishInterval / 1000"
            :min="1"
            :max="120"
            @change="onPublishIntervalChange"
            activeColor="#4F46E5"
            backgroundColor="#E5E7EB"
          />
          <text>{{ simulationStore.publishInterval / 1000 }} 秒</text>
        </view>
      </view>
      <view class="setting-item">
        <view class="setting-label">接单间隔</view>
        <view class="setting-value">
          <slider
            :value="simulationStore.acceptInterval / 1000"
            :min="1"
            :max="90"
            @change="onAcceptIntervalChange"
            activeColor="#4F46E5"
            backgroundColor="#E5E7EB"
          />
          <text>{{ simulationStore.acceptInterval / 1000 }} 秒</text>
        </view>
      </view>
      <view class="setting-item">
        <view class="setting-label">完成间隔</view>
        <view class="setting-value">
          <slider
            :value="simulationStore.completeInterval / 1000"
            :min="1"
            :max="60"
            @change="onCompleteIntervalChange"
            activeColor="#10B981"
            backgroundColor="#E5E7EB"
          />
          <text>{{ simulationStore.completeInterval / 1000 }} 秒</text>
        </view>
      </view>
      <view class="setting-item">
        <view class="setting-label">确认间隔</view>
        <view class="setting-value">
          <slider
            :value="simulationStore.confirmInterval / 1000"
            :min="1"
            :max="60"
            @change="onConfirmIntervalChange"
            activeColor="#F59E0B"
            backgroundColor="#E5E7EB"
          />
          <text>{{ simulationStore.confirmInterval / 1000 }} 秒</text>
        </view>
      </view>
    </view>

    <view class="control-section">
      <view class="section-title">当前需求列表</view>
      <scroll-view class="needs-scroll" scroll-y="true">
        <view v-if="needStore.needs.length === 0" class="empty-log">
          暂无需求
        </view>
        <view
          v-for="need in needStore.needs"
          :key="need.id"
          :class="['need-item', need.status]"
        >
          <view class="need-header">
            <text class="need-title">{{ need.title }}</text>
            <text :class="['need-status', need.status]">{{ getStatusText(need.status) }}</text>
          </view>
          <view class="need-info">
            <view class="need-row">
              <text class="need-label">酬劳</text>
              <text class="need-value reward">¥{{ need.reward }}</text>
            </view>
            <view class="need-row">
              <text class="need-label">位置</text>
              <text class="need-value">{{ need.location }}</text>
            </view>
            <view class="need-row">
              <text class="need-label">发布者</text>
              <text class="need-value">{{ need.publisher?.nickname || '未知' }}</text>
            </view>
            <view v-if="need.helper" class="need-row">
              <text class="need-label">接单人</text>
              <text class="need-value">{{ need.helper?.nickname || '未知' }}</text>
            </view>
          </view>
        </view>
      </scroll-view>
    </view>

    <view class="control-section">
      <view class="section-title">模拟用户</view>
      <view class="users-list">
        <view
          v-for="user in simulationStore.simulationUsers"
          :key="user.id"
          :class="['user-item', !user.active ? 'inactive' : '']"
        >
          <view class="user-avatar">
            <text>{{ user.nickname[0] }}</text>
          </view>
          <view class="user-info">
            <view class="user-name">{{ user.nickname }}</view>
            <view class="user-stats">
              <text class="stat">信誉: {{ user.reputation }}</text>
              <text class="stat">完成: {{ user.completedOrders }}</text>
            </view>
            <view class="user-skills">
              <text v-for="skill in user.skills" :key="skill" class="skill-tag">{{ skill }}</text>
            </view>
          </view>
          <view class="user-toggle">
            <switch
              :checked="user.active"
              @change="toggleUser(user.id)"
              color="#4F46E5"
            />
          </view>
        </view>
      </view>
    </view>

    <view class="control-section">
      <view class="section-title">活动日志
        <text class="clear-log" @click="simulationStore.clearLog">清空</text>
      </view>
      <scroll-view class="log-scroll" scroll-y="true">
        <view v-for="log in simulationStore.activityLog" :key="log.id" :class="['log-item', log.type]">
          <view class="log-time">{{ log.timestamp }}</view>
          <view class="log-icon">{{ getLogIcon(log.type) }}</view>
          <view class="log-message">{{ log.message }}</view>
        </view>
        <view v-if="simulationStore.activityLog.length === 0" class="empty-log">
          暂无活动记录
        </view>
      </scroll-view>
    </view>
  </view>
</template>

<script setup>
import { useSimulationStore } from '@/store/simulation'
import { useNeedStore } from '@/store/need'

const simulationStore = useSimulationStore()
const needStore = useNeedStore()

const toggleSimulation = () => {
  if (simulationStore.isRunning) {
    simulationStore.stopSimulation()
  } else {
    simulationStore.startSimulation()
  }
}

const toggleUser = (userId) => {
  simulationStore.toggleUserActive(userId)
}

const onPublishIntervalChange = (e) => {
  simulationStore.setPublishInterval(e.detail.value * 1000)
}

const onAcceptIntervalChange = (e) => {
  simulationStore.setAcceptInterval(e.detail.value * 1000)
}

const onCompleteIntervalChange = (e) => {
  simulationStore.setCompleteInterval(e.detail.value * 1000)
}

const onConfirmIntervalChange = (e) => {
  simulationStore.setConfirmInterval(e.detail.value * 1000)
}

const getLogIcon = (type) => {
  switch (type) {
    case 'publish': return '📝'
    case 'accept': return '✅'
    case 'cancel': return '❌'
    case 'complete': return '🎯'
    case 'confirm': return '🎉'
    case 'system': return '⚙️'
    default: return '📌'
  }
}

const getStatusText = (status) => {
  const map = {
    'open': '待接单',
    'accepted': '进行中',
    'pending_confirm': '待确认',
    'completed': '已完成',
    'cancelled': '已取消'
  }
  return map[status] || status
}
</script>

<style scoped>
.simulation-container {
  min-height: 100vh;
  background: linear-gradient(135deg, #f5f7fa 0%, #e4e8f0 100%);
  padding: 20rpx;
}

.header {
  text-align: center;
  padding: 40rpx 0;
  background: linear-gradient(135deg, #4F46E5 0%, #7C3AED 100%);
  border-radius: 24rpx;
  margin-bottom: 30rpx;
  color: white;
}

.title {
  font-size: 40rpx;
  font-weight: 700;
  margin-bottom: 10rpx;
}

.subtitle {
  font-size: 26rpx;
  opacity: 0.9;
}

.control-section {
  background: white;
  border-radius: 24rpx;
  padding: 30rpx;
  margin-bottom: 24rpx;
  box-shadow: 0 4rpx 20rpx rgba(0,0,0,0.05);
}

.section-title {
  font-size: 32rpx;
  font-weight: 600;
  color: #111827;
  margin-bottom: 24rpx;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.clear-log {
  font-size: 24rpx;
  color: #6B7280;
  font-weight: 400;
}

.control-buttons {
  display: flex;
  flex-direction: column;
  gap: 16rpx;
}

.control-btn {
  width: 100%;
  padding: 28rpx;
  border: none;
  border-radius: 16rpx;
  font-size: 30rpx;
  font-weight: 600;
  transition: all 0.3s;
}

.control-btn.start {
  background: linear-gradient(135deg, #10B981 0%, #059669 100%);
  color: white;
}

.control-btn.running {
  background: linear-gradient(135deg, #EF4444 0%, #DC2626 100%);
  color: white;
}

.control-btn.single-action {
  background: #F3F4F6;
  color: #374151;
  font-weight: 500;
}

.setting-item {
  padding: 20rpx 0;
  border-bottom: 1rpx solid #F3F4F6;
}

.setting-item:last-child {
  border-bottom: none;
}

.setting-label {
  font-size: 28rpx;
  color: #374151;
  margin-bottom: 12rpx;
}

.setting-value {
  display: flex;
  align-items: center;
  gap: 16rpx;
}

.setting-value slider {
  flex: 1;
}

.setting-value text {
  font-size: 26rpx;
  color: #6B7280;
  min-width: 120rpx;
}

.needs-scroll {
  height: 600rpx;
}

.need-item {
  padding: 20rpx;
  background: #F9FAFB;
  border-radius: 16rpx;
  margin-bottom: 16rpx;
  border-left: 4rpx solid #4F46E5;
}

.need-item.open {
  border-left-color: #3B82F6;
}

.need-item.accepted {
  border-left-color: #10B981;
}

.need-item.pending_confirm {
  border-left-color: #F59E0B;
}

.need-item.completed {
  border-left-color: #6B7280;
}

.need-item.cancelled {
  border-left-color: #DC2626;
}

.need-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16rpx;
}

.need-title {
  font-size: 30rpx;
  font-weight: 600;
  color: #111827;
}

.need-status {
  font-size: 22rpx;
  padding: 6rpx 12rpx;
  border-radius: 8rpx;
  font-weight: 500;
}

.need-status.open {
  background: #DBEAFE;
  color: #3B82F6;
}

.need-status.accepted {
  background: #ECFDF5;
  color: #10B981;
}

.need-status.pending_confirm {
  background: #FFFBEB;
  color: #F59E0B;
}

.need-status.completed {
  background: #F1F5F9;
  color: #6B7280;
}

.need-status.cancelled {
  background: #FEE2E2;
  color: #DC2626;
}

.need-info {
  display: flex;
  flex-direction: column;
  gap: 10rpx;
}

.need-row {
  display: flex;
  align-items: center;
  gap: 8rpx;
}

.need-label {
  font-size: 24rpx;
  color: #6B7280;
  min-width: 70rpx;
}

.need-value {
  font-size: 26rpx;
  color: #111827;
  font-weight: 500;
}

.need-value.reward {
  color: #10B981;
  font-weight: 700;
}

.users-list {
  display: flex;
  flex-direction: column;
  gap: 16rpx;
}

.user-item {
  display: flex;
  align-items: center;
  padding: 24rpx;
  background: #F9FAFB;
  border-radius: 16rpx;
  transition: all 0.3s;
}

.user-item.inactive {
  opacity: 0.5;
}

.user-avatar {
  width: 88rpx;
  height: 88rpx;
  border-radius: 50%;
  background: linear-gradient(135deg, #4F46E5 0%, #7C3AED 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 36rpx;
  font-weight: 700;
  margin-right: 20rpx;
}

.user-info {
  flex: 1;
}

.user-name {
  font-size: 30rpx;
  font-weight: 600;
  color: #111827;
  margin-bottom: 8rpx;
}

.user-stats {
  display: flex;
  gap: 20rpx;
  margin-bottom: 8rpx;
}

.stat {
  font-size: 24rpx;
  color: #6B7280;
}

.user-skills {
  display: flex;
  gap: 8rpx;
  flex-wrap: wrap;
}

.skill-tag {
  font-size: 22rpx;
  padding: 6rpx 16rpx;
  background: #EEF2FF;
  color: #4F46E5;
  border-radius: 100rpx;
}

.user-toggle {
  padding-left: 20rpx;
}

.log-scroll {
  height: 500rpx;
}

.log-item {
  display: flex;
  align-items: flex-start;
  gap: 16rpx;
  padding: 20rpx 0;
  border-bottom: 1rpx solid #F3F4F6;
}

.log-item:last-child {
  border-bottom: none;
}

.log-time {
  font-size: 22rpx;
  color: #9CA3AF;
  min-width: 120rpx;
  padding-top: 4rpx;
}

.log-icon {
  font-size: 32rpx;
  padding-top: 2rpx;
}

.log-message {
  flex: 1;
  font-size: 28rpx;
  color: #374151;
  line-height: 1.5;
}

.log-item.publish .log-message {
  color: #7C3AED;
}

.log-item.accept .log-message {
  color: #059669;
}

.log-item.cancel .log-message {
  color: #DC2626;
}

.log-item.complete .log-message {
  color: #F59E0B;
}

.log-item.confirm .log-message {
  color: #10B981;
}

.empty-log {
  text-align: center;
  padding: 80rpx 0;
  color: #9CA3AF;
  font-size: 28rpx;
}
</style>
