<template>
  <view class="container">
    <view class="header">
      <text class="header-title">评价订单</text>
      <view class="header-right"></view>
    </view>

    <scroll-view class="content" scroll-y v-if="order">
      <view class="order-card">
        <text class="order-title">{{ order.title }}</text>
        <view class="order-meta">
          <text class="meta-item">
            <IconFont name="coin" :size="12" style="margin-right: 4px;" />¥{{ order.reward }}
          </text>
          <text class="meta-item">
            <IconFont name="map-pin" :size="12" style="margin-right: 4px;" />{{ order.location }}
          </text>
        </view>
      </view>

      <view class="rate-section">
        <text class="section-title">为帮手掌柜打分</text>
        <view class="star-container">
          <view
            v-for="n in 5"
            :key="n"
            class="star"
            :class="{ active: n <= rating, animate: n === rating && animating }"
            @click="setRating(n)"
          >
            <IconFont :name="n <= rating ? 'star' : 'star-outline'" :size="48" />
          </view>
        </view>
        <text class="rate-text">{{ rateText }}</text>
      </view>

      <view class="comment-section">
        <text class="section-title">评价内容（选填）</text>
        <textarea
          class="comment-input"
          placeholder="说说这次服务的体验吧..."
          v-model="comment"
          maxlength="200"
        />
        <text class="char-count">{{ comment.length }}/200</text>
      </view>

      <view class="anonymous-section">
        <view class="anonymous-left">
          <IconFont name="eye-off" :size="20" class="anonymous-icon" />
          <view class="anonymous-info">
            <text class="anonymous-title">匿名评价</text>
            <text class="anonymous-desc">匿名后对方看不到您的昵称</text>
          </view>
        </view>
        <view
          class="toggle"
          :class="{ active: isAnonymous }"
          @click="isAnonymous = !isAnonymous"
        ></view>
      </view>

      <!-- 快捷标签 -->
      <view class="tags-section">
        <text class="section-title">快捷标签</text>
        <view class="tags-container">
          <text 
            v-for="tag in tags" 
            :key="tag"
            class="tag"
            :class="{ selected: selectedTags.includes(tag) }"
            @click="toggleTag(tag)"
          >{{ tag }}</text>
        </view>
      </view>

      <!-- 提交按钮 -->
      <view class="submit-btn" @click="submitRate" :class="{ disabled: rating === 0 }">
        <text class="btn-text">提交评价</text>
      </view>

      <view class="bottom-space"></view>
    </scroll-view>

    <view v-else class="loading">
      <text class="loading-text">加载中...</text>
    </view>
  </view>
</template>

<script>
import { useOrderStore } from '@/store/order'
import { useNeedStore } from '@/store/need'
import IconFont from '@/components/icon-font/icon-font.vue'

export default {
  components: {
    IconFont
  },
  setup() {
    const orderStore = useOrderStore()
    const needStore = useNeedStore()
    return { orderStore, needStore }
  },
  data() {
    return {
      order: null,
      rating: 0,
      comment: '',
      selectedTags: [],
      tags: ['速度快', '态度好', '准时', '很专业', '超出预期'],
      isAnonymous: false,
      animating: false
    }
  },
  computed: {
    rateText() {
      const texts = ['', '非常差', '差', '一般', '满意', '非常满意']
      return texts[this.rating] || ''
    }
  },
  onLoad(options) {
    const orderId = options.orderId
    let order = this.orderStore.orders.find(o => o.id === orderId)
    
    if (!order) {
      const needs = this.needStore.needs || []
      order = needs.find(n => n.id === orderId)
    }
    
    if (!order) {
      const localOrders = uni.getStorageSync('orders') || []
      order = localOrders.find(o => o.id === orderId)
    }
    
    if (!order) {
      const localNeeds = uni.getStorageSync('needs') || []
      order = localNeeds.find(n => n.id === orderId)
    }
    
    this.order = order
  },
  methods: {
    setRating(n) {
      if (this.rating === n) return
      this.rating = n
      this.animating = true
      setTimeout(() => {
        this.animating = false
      }, 300)
    },
    toggleTag(tag) {
      const index = this.selectedTags.indexOf(tag)
      if (index > -1) {
        this.selectedTags.splice(index, 1)
      } else {
        this.selectedTags.push(tag)
      }
    },
    submitRate() {
      if (this.rating === 0) {
        uni.showToast({ title: '请先选择评分', icon: 'none' })
        return
      }

      uni.showLoading({ title: '提交中...' })

      setTimeout(() => {
        uni.hideLoading()

        if (this.order) {
          this.order.rating = this.rating
          this.order.comment = this.comment
          this.order.tags = [...this.selectedTags]
          this.order.ratedAt = Date.now()
          this.order.isAnonymous = this.isAnonymous
          this.order.isRated = true

          const orderInStore = this.orderStore.orders.find(o => o.id === this.order.id)
          if (orderInStore) {
            Object.assign(orderInStore, this.order)
          }
          
          const needInStore = this.needStore.needs.find(n => n.id === this.order.id)
          if (needInStore) {
            Object.assign(needInStore, this.order)
          }

          const orders = uni.getStorageSync('orders') || []
          const orderIndex = orders.findIndex(o => o.id === this.order.id)
          if (orderIndex > -1) {
            orders[orderIndex] = this.order
          } else {
            orders.push(this.order)
          }
          uni.setStorageSync('orders', orders)

          const needs = uni.getStorageSync('needs') || []
          const needIndex = needs.findIndex(n => n.id === this.order.id)
          if (needIndex > -1) {
            needs[needIndex] = this.order
          }
          uni.setStorageSync('needs', needs)

          const userInfo = uni.getStorageSync('userInfo') || {}
          const ratings = uni.getStorageSync('orderRatings') || []
          ratings.push({
            id: Date.now(),
            orderId: this.order.id,
            orderTitle: this.order.title,
            userName: this.isAnonymous ? '匿名用户' : (userInfo.nickname || '用户'),
            rating: this.rating,
            comment: this.comment,
            tags: [...this.selectedTags],
            isAnonymous: this.isAnonymous,
            ratedAt: Date.now()
          })
          uni.setStorageSync('orderRatings', ratings)
        }

        uni.showToast({
          title: '评价成功',
          icon: 'success'
        })

        setTimeout(() => {
          uni.navigateBack()
        }, 1500)
      }, 1000)
    },
  }
}
</script>

<style scoped>
.container {
  min-height: 100vh;
  background: #F8FAFC;
}

.header {
  display: flex;
  align-items: center;
  padding: 64rpx 24rpx 16rpx;
  background: #FFFFFF;
  gap: 16rpx;
  border-bottom: 1rpx solid #F1F5F9;
}



.header-title {
  flex: 1;
  font-size: 18px;
  font-weight: 800;
  color: #1E293B;
  text-align: center;
}

.header-right {
  width: 40px;
}

.content {
  padding: 24rpx;
}

.bottom-space {
  height: 40px;
}

/* 订单卡片 */
.order-card {
  background: #FFFFFF;
  border-radius: 16px;
  padding: 16px;
  margin-bottom: 20px;
  border-left: 4px solid #10B981;
}

.order-title {
  font-size: 16px;
  font-weight: 600;
  color: #1E293B;
  margin-bottom: 8px;
  display: block;
}

.order-meta {
  display: flex;
  gap: 16px;
}

.meta-item {
  font-size: 13px;
  color: #64748B;
}

/* 评分区域 */
.rate-section {
  background: #FFFFFF;
  border-radius: 16px;
  padding: 20px;
  margin-bottom: 20px;
  text-align: center;
}

.section-title {
  font-size: 15px;
  font-weight: 600;
  color: #1E293B;
  margin-bottom: 16px;
  display: block;
}

.star-container {
  display: flex;
  justify-content: center;
  gap: 8px;
  margin-bottom: 12px;
}

.star {
  cursor: pointer;
  color: #E2E8F0;
  transition: transform 0.2s;
}

.star.active {
  color: #F59E0B;
}

.star.animate {
  animation: starPop 0.3s ease-out;
}

@keyframes starPop {
  0% { transform: scale(1); }
  50% { transform: scale(1.3); }
  100% { transform: scale(1); }
}

.rate-text {
  font-size: 14px;
  color: #10B981;
  font-weight: 600;
}

/* 匿名评价 */
.anonymous-section {
  background: #FFFFFF;
  border-radius: 16px;
  padding: 20px;
  margin-bottom: 20px;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.anonymous-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.anonymous-icon {
  color: #64748B;
}

.anonymous-info {
  display: flex;
  flex-direction: column;
}

.anonymous-title {
  font-size: 15px;
  font-weight: 600;
  color: #1E293B;
}

.anonymous-desc {
  font-size: 12px;
  color: #94A3B8;
}

.toggle {
  width: 96rpx;
  height: 56rpx;
  background: #E2E8F0;
  border-radius: 28rpx;
  position: relative;
  cursor: pointer;
  transition: all 0.3s;
}

.toggle.active {
  background: #10B981;
}

.toggle::after {
  content: '';
  position: absolute;
  width: 44rpx;
  height: 44rpx;
  background: #FFFFFF;
  border-radius: 50%;
  top: 6rpx;
  left: 6rpx;
  transition: all 0.3s;
  box-shadow: 0 2rpx 4rpx rgba(0, 0, 0, 0.1);
}

.toggle.active::after {
  left: 46rpx;
}

/* 评价内容 */
.comment-section {
  background: #FFFFFF;
  border-radius: 16px;
  padding: 16px;
  margin-bottom: 20px;
}

.comment-input {
  width: 100%;
  min-height: 100px;
  padding: 12px;
  background: #F8FAFC;
  border-radius: 12px;
  font-size: 14px;
  color: #1E293B;
  margin-bottom: 8px;
}

.char-count {
  font-size: 12px;
  color: #94A3B8;
  text-align: right;
  display: block;
}

/* 快捷标签 */
.tags-section {
  background: #FFFFFF;
  border-radius: 16px;
  padding: 16px;
  margin-bottom: 20px;
}

.tags-container {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.tag {
  font-size: 13px;
  color: #64748B;
  background: #F1F5F9;
  padding: 8px 14px;
	border-radius: 20px;
}

.tag.selected {
  background: #D1FAE5;
  color: #059669;
}

/* 提交按钮 */
.submit-btn {
  background: #10B981;
  border-radius: 14px;
  padding: 16px 0;
  text-align: center;
  box-shadow: 0 4px 12px rgba(16, 185, 129, 0.2);
}

.submit-btn.disabled {
  opacity: 0.5;
}

.btn-text {
  color: #FFFFFF;
  font-size: 16px;
  font-weight: 600;
}

/* 加载中 */
.loading {
  display: flex;
  align-items: center;
  justify-content: center;
  height: calc(100vh - 80px);
}

.loading-text {
  font-size: 16px;
  color: #64748B;
}
</style>
