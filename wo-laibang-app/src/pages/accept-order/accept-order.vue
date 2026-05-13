<template>
	<view class="container">
		<view class="header">
			<text class="header-title">确认接单</text>
			<view class="header-right"></view>
		</view>

		<scroll-view class="content-scroll" scroll-y v-if="order">
			<view class="order-card">
				<view class="card-header">
					<view class="category-tag">
						<IconFont :name="categoryIcon" :size="16" />
						<text>{{ categoryName }}</text>
					</view>
					<view class="reward-badge">
						<text class="reward-label">酬劳</text>
						<text class="reward-value">¥ {{ order.reward }}</text>
					</view>
				</view>

				<view class="order-title">{{ order.title }}</view>

				<view class="order-desc" v-if="order.description">
					{{ order.description }}
				</view>

				<view class="info-list">
					<view class="info-item">
						<IconFont name="map-pin" :size="18" class="info-icon" />
						<view class="info-content">
							<text class="info-label">服务地址</text>
							<text class="info-value">{{ order.location || '未指定地址' }}</text>
						</view>
					</view>

					<view class="info-item">
						<IconFont name="user" :size="18" class="info-icon" />
						<view class="info-content">
							<text class="info-label">发布者</text>
							<text class="info-value">{{ order.publisher?.nickname || '匿名用户' }}</text>
						</view>
					</view>

					<view class="info-item">
						<IconFont name="clock" :size="18" class="info-icon" />
						<view class="info-content">
							<text class="info-label">发布时间</text>
							<text class="info-value">{{ formatTime(order.createdAt) }}</text>
						</view>
					</view>
				</view>
			</view>

			<view class="notice-card">
				<view class="notice-header">
					<IconFont name="info-circle" :size="18" class="notice-icon" />
					<text class="notice-title">接单须知</text>
				</view>
				<view class="notice-list">
					<view class="notice-item">
						<IconFont name="check" :size="14" class="check-icon" />
						<text>请确保能在约定时间内完成服务</text>
					</view>
					<view class="notice-item">
						<IconFont name="check" :size="14" class="check-icon" />
						<text>服务完成后点击"确认完成"获取酬劳</text>
					</view>
					<view class="notice-item">
						<IconFont name="check" :size="14" class="check-icon" />
						<text>如需取消订单，请提前与发布者沟通</text>
					</view>
					<view class="notice-item">
						<IconFont name="check" :size="14" class="check-icon" />
						<text>请遵守平台规范，诚实守信</text>
					</view>
				</view>
			</view>

			<view class="agreement-section">
				<view
					class="checkbox"
					:class="{ checked: agreed }"
					@click="agreed = !agreed"
				>
					<IconFont v-if="agreed" name="check" :size="14" />
				</view>
				<text class="agreement-text">
					我已阅读并同意<text class="link" @click.stop="goTerms">《帮忙服务协议》</text>
				</text>
			</view>

			<button
				class="accept-btn"
				:class="{ disabled: !agreed || isAccepting }"
				@click="handleAccept"
				:disabled="!agreed || isAccepting"
			>
				<view v-if="isAccepting" class="spinner"></view>
				<text v-else>确认接单</text>
			</button>

			<view class="bottom-safe"></view>
		</scroll-view>

		<view v-else class="loading">
			<text>加载中...</text>
		</view>
	</view>
</template>

<script>
import { useUserStore } from '@/store/user'
import { useNeedStore } from '@/store/need'
import { useOrderStore } from '@/store/order'
import IconFont from '@/components/icon-font/icon-font.vue'

export default {
	components: {
		IconFont
	},
	setup() {
		const userStore = useUserStore()
		const needStore = useNeedStore()
		const orderStore = useOrderStore()
		return { userStore, needStore, orderStore }
	},
	data() {
		return {
			order: null,
			agreed: false,
			isAccepting: false,
			categoryMap: {
				run: { icon: 'run', name: '跑腿' },
				housework: { icon: 'housework', name: '家务' },
				professional: { icon: 'professional', name: '专业' },
				others: { icon: 'others', name: '其他' }
			}
		}
	},
	computed: {
		categoryIcon() {
			if (!this.order?.category) return 'help'
			return this.categoryMap[this.order.category]?.icon || 'help'
		},
		categoryName() {
			if (!this.order?.category) return '其他'
			return this.categoryMap[this.order.category]?.name || '其他'
		}
	},
	onLoad(options) {
		const id = options.id
		if (!id) {
			uni.showToast({ title: '参数错误', icon: 'none' })
			return
		}

		this.loadOrder(id)
	},
	methods: {
		loadOrder(id) {
			const sources = [
				...(this.needStore.needs || []),
				...(this.orderStore.orders || [])
			]
			this.order = sources.find(item => item.id == id || (item.needId && item.needId == id))

			if (!this.order) {
				const localOrders = uni.getStorageSync('orders') || []
				const localNeeds = uni.getStorageSync('needs') || []
				const localSources = [...localOrders, ...localNeeds]
				this.order = localSources.find(item => item.id == id || (item.needId && item.needId == id))
			}

			if (!this.order) {
				uni.showToast({ title: '订单不存在', icon: 'none' })
				setTimeout(() => uni.navigateBack(), 1500)
			}
		},
		formatTime(timestamp) {
			if (!timestamp) return ''
			const date = new Date(timestamp)
			const month = date.getMonth() + 1
			const day = date.getDate()
			const hour = date.getHours().toString().padStart(2, '0')
			const min = date.getMinutes().toString().padStart(2, '0')
			return `${month}月${day}日 ${hour}:${min}`
		},
		async handleAccept() {
			if (!this.agreed || this.isAccepting) return

			const isConfirmed = await new Promise((resolve) => {
				uni.showModal({
					title: '确认接单',
					content: `确定要接下"${this.order.title}"这个任务吗？`,
					confirmColor: '#10B981',
					success: (res) => resolve(res.confirm)
				})
			})

			if (!isConfirmed) return

			this.isAccepting = true

			const result = await this.needStore.acceptNeed(this.order.id)

			this.isAccepting = false

			if (result.success) {
				this.sendNotification('accepted', '有新订单被接单')
				uni.showToast({ title: '接单成功', icon: 'success' })
				setTimeout(() => {
					uni.navigateBack()
				}, 1500)
			} else {
				uni.showToast({ title: result.message, icon: 'none' })
			}
		},
		sendNotification(status, message) {
			const notifications = uni.getStorageSync('notifications') || []
			const titleMap = {
				'accepted': '订单已被接单',
				'pending_confirm': '订单待确认',
				'completed': '订单已完成',
				'cancelled': '订单已取消'
			}
			const newNotification = {
				id: Date.now(),
				type: 'order',
				title: titleMap[status] || '订单状态更新',
				content: message,
				orderId: this.order.id,
				orderTitle: this.order.title,
				status: status,
				read: false,
				createdAt: Date.now()
			}
			notifications.unshift(newNotification)
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
		},
		goTerms() {
			uni.navigateTo({ url: '/pages/terms-of-service/terms-of-service' })
		}
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

.content-scroll {
	height: calc(100vh - 89px);
	padding: 24rpx;
}

.order-card {
	background: #FFFFFF;
	border-radius: 24rpx;
	padding: 28rpx 24rpx;
	margin-bottom: 20rpx;
	box-shadow: 0 2rpx 12rpx rgba(0, 0, 0, 0.04);
}

.card-header {
	display: flex;
	justify-content: space-between;
	align-items: center;
	margin-bottom: 20rpx;
}

.category-tag {
	display: flex;
	align-items: center;
	gap: 8rpx;
	padding: 8rpx 16rpx;
	background: #F0FDF4;
	border-radius: 100rpx;
	font-size: 24rpx;
	font-weight: 700;
	color: #10B981;
}

.reward-badge {
	display: flex;
	flex-direction: column;
	align-items: flex-end;
}

.reward-label {
	font-size: 20rpx;
	color: #94A3B8;
}

.reward-value {
	font-size: 36rpx;
	font-weight: 800;
	color: #10B981;
}

.order-title {
	font-size: 32rpx;
	font-weight: 800;
	color: #1E293B;
	margin-bottom: 12rpx;
	line-height: 1.4;
}

.order-desc {
	font-size: 26rpx;
	color: #64748B;
	line-height: 1.6;
	margin-bottom: 24rpx;
}

.info-list {
	border-top: 1rpx solid #F1F5F9;
	padding-top: 20rpx;
}

.info-item {
	display: flex;
	align-items: flex-start;
	margin-bottom: 20rpx;
}

.info-item:last-child {
	margin-bottom: 0;
}

.info-icon {
	color: #94A3B8;
	margin-right: 12rpx;
	margin-top: 4rpx;
}

.info-content {
	display: flex;
	flex-direction: column;
}

.info-label {
	font-size: 22rpx;
	color: #94A3B8;
	margin-bottom: 4rpx;
}

.info-value {
	font-size: 26rpx;
	font-weight: 600;
	color: #1E293B;
}

.notice-card {
	background: #FEF9E7;
	border-radius: 20rpx;
	padding: 24rpx;
	margin-bottom: 20rpx;
}

.notice-header {
	display: flex;
	align-items: center;
	gap: 10rpx;
	margin-bottom: 16rpx;
}

.notice-icon {
	color: #D97706;
}

.notice-title {
	font-size: 28rpx;
	font-weight: 700;
	color: #92400E;
}

.notice-list {
	display: flex;
	flex-direction: column;
	gap: 12rpx;
}

.notice-item {
	display: flex;
	align-items: flex-start;
	gap: 10rpx;
}

.check-icon {
	color: #10B981;
	margin-top: 4rpx;
	flex-shrink: 0;
}

.notice-item text {
	font-size: 24rpx;
	color: #78350F;
	line-height: 1.5;
}

.agreement-section {
	display: flex;
	align-items: center;
	gap: 12rpx;
	margin-bottom: 24rpx;
	padding: 0 8rpx;
}

.checkbox {
	width: 36rpx;
	height: 36rpx;
	border: 2rpx solid #CBD5E1;
	border-radius: 8rpx;
	display: flex;
	align-items: center;
	justify-content: center;
	background: #FFFFFF;
	transition: all 0.2s;
}

.checkbox.checked {
	background: #10B981;
	border-color: #10B981;
	color: #FFFFFF;
}

.agreement-text {
	font-size: 24rpx;
	color: #64748B;
}

.agreement-text .link {
	color: #10B981;
	font-weight: 600;
}

.accept-btn {
	width: 100%;
	height: 100rpx;
	background: linear-gradient(135deg, #10B981, #059669);
	color: #FFFFFF;
	border-radius: 50rpx;
	font-size: 32rpx;
	font-weight: 800;
	display: flex;
	align-items: center;
	justify-content: center;
	border: none;
	box-shadow: 0 8rpx 24rpx rgba(16, 185, 129, 0.35);
}

.accept-btn.disabled {
	opacity: 0.5;
	box-shadow: none;
}

.spinner {
	width: 40rpx;
	height: 40rpx;
	border: 4rpx solid rgba(255, 255, 255, 0.3);
	border-top-color: #FFFFFF;
	border-radius: 50%;
	animation: spin 0.8s linear infinite;
}

@keyframes spin {
	to { transform: rotate(360deg); }
}

.bottom-safe {
	height: 60rpx;
}

.loading {
	display: flex;
	align-items: center;
	justify-content: center;
	height: 100vh;
}

.loading text {
	font-size: 28rpx;
	color: #94A3B8;
}
</style>