<template>
	<view class="container">
		<!-- Simple Nav -->
		<view class="nav-header">
		</view>

		<!-- Content -->
		<scroll-view class="screen" scroll-y v-if="order">
			<view class="hero-title">{{ order.title }}</view>

			<view class="detail-item">
				<view class="label">当前状态</view>
				<view class="value status" :class="order.status">{{ statusTitle }}</view>
			</view>

			<view class="detail-item">
				<view class="label">服务位置</view>
				<view class="value">{{ order.location }}</view>
			</view>

			<view class="detail-item" v-if="order.detailAddress">
				<view class="label">具体位置</view>
				<view class="value">{{ order.detailAddress }}</view>
			</view>

			<view class="detail-item">
				<view class="label">订单报酬</view>
				<view class="value highlight">¥ {{ order.reward }}</view>
			</view>

			<view class="detail-item" v-if="order.description">
				<view class="label">需求描述</view>
				<view class="value desc">{{ order.description }}</view>
			</view>

			<view class="detail-item">
				<view class="label">现场图片</view>
				<view v-if="order.image" class="image-wrapper">
					<image :src="order.image" mode="aspectFill" class="order-image" lazy-load="true" @click="previewImage(order.image)" />
				</view>
				<view v-else class="no-image">暂无图片展示</view>
			</view>

			<view class="detail-item" v-if="order.deadline">
				<view class="label">最晚什么时候</view>
				<view class="value deadline-text">{{ order.deadline }}</view>
			</view>

			<!-- 参与人员 (V3风格简化版) -->
			<view class="detail-item">
				<view class="label">参与人员</view>
				<view class="people-minimal">
					<view class="person">
						<text class="p-role">发布者</text>
						<text class="p-name">{{ order.publisher?.nickname || '未知' }}</text>
					</view>
					<view class="person" v-if="order.helper">
						<text class="p-role">帮手</text>
						<text class="p-name">{{ order.helper?.nickname || '未知' }}</text>
					</view>
				</view>
			</view>

			<!-- 评价信息 (如果有) -->
			<view class="detail-item" v-if="order.status === 'completed' && order.rating">
				<view class="label">服务评价</view>
				<view class="value">
						<IconFont name="star" :size="24" style="margin-right: 8rpx; color: #F59E0B;" />{{ order.rating }} 分
					</view>
				<view class="value desc" v-if="order.comment" style="margin-top: 10rpx;">"{{ order.comment }}"</view>
			</view>

			<view class="detail-item">
				<view class="label">时间节点</view>
				<view class="value time-node">{{ statusTime }}</view>
			</view>

			<!-- Action Buttons -->
			<view class="btn-group">
				<!-- 发布者取消按钮 -->
				<button v-if="order.status === 'open' && isPublisher" class="btn btn-cancel" @click="cancelOrder">取消订单</button>
				<!-- 发布者取消已接单订单 -->
				<button v-if="order.status === 'accepted' && isPublisher" class="btn btn-cancel" @click="cancelOrder">取消订单</button>
				<!-- 帮手取消按钮 -->
				<button v-if="order.status === 'accepted' && !isPublisher" class="btn btn-cancel" @click="cancelOrder">取消接单</button>
				<!-- 帮手申请完成按钮 -->
				<button v-if="order.status === 'accepted' && !isPublisher && !order.helperConfirmed" class="btn btn-p" @click="applyComplete">申请完成</button>
				<!-- 帮手已申请完成提示 -->
				<button v-if="order.status === 'pending_confirm' && !isPublisher && order.helperConfirmed && !order.publisherConfirmed" class="btn btn-s" disabled>等待发布者确认</button>
				<!-- 发布者等待帮手确认 -->
				<button v-if="order.status === 'pending_confirm' && isPublisher && order.publisherConfirmed && !order.helperConfirmed" class="btn btn-s" disabled>等待帮手确认</button>
				<!-- 发布者确认完成按钮 -->
				<button v-if="order.status === 'pending_confirm' && isPublisher && !order.publisherConfirmed" class="btn btn-p" @click="confirmComplete">确认完成</button>
				<!-- 联系对方 -->
				<button v-if="order.status === 'accepted' || order.status === 'pending_confirm'" class="btn btn-s" @click="contactUser">联系对方</button>
				<!-- 去评价 -->
				<button v-if="order.status === 'completed' && !order.rating && !isPublisher" class="btn btn-p" @click="goRate">去评价</button>
				<!-- 已完成的联系按钮 -->
				<button v-if="order.status === 'completed'" class="btn btn-s" @click="contactUser">联系对方</button>
				<!-- 订单已结束 -->
				<button v-if="order.status === 'completed'" class="btn btn-s" disabled>订单已结束</button>
				<!-- 已取消 - 再次发布 -->
				<button v-if="order.status === 'cancelled' && isPublisher" class="btn btn-p" @click="republishOrder">再次发布</button>
			</view>
		</scroll-view>

		<!-- 加载中 -->
		<view v-else class="loading">
			<text class="loading-text">加载中...</text>
		</view>

		<!-- 确认弹窗 -->
		<view v-if="confirmVisible" style="position:fixed;top:0;left:0;right:0;bottom:0;background:rgba(0,0,0,0.5);z-index:99999;display:flex;align-items:center;justify-content:center;" @click="confirmVisible = false">
			<view style="width:560rpx;background:#FFFFFF;border-radius:32rpx;overflow:hidden;" @click.stop>
				<view style="padding:40rpx 40rpx 20rpx;text-align:center;">
					<text style="font-size:34rpx;font-weight:700;color:#1E293B;">{{ confirmTitle }}</text>
				</view>
				<view style="padding:0 40rpx 30rpx;text-align:center;">
					<text style="font-size:28rpx;color:#64748B;line-height:1.6;">{{ confirmContent }}</text>
				</view>
				<view style="display:flex;border-top:1rpx solid #F1F5F9;">
					<view style="flex:1;height:96rpx;display:flex;align-items:center;justify-content:center;" v-if="confirmCancelText" @click="confirmVisible = false">
						<text style="font-size:30rpx;font-weight:600;color:#64748B;">{{ confirmCancelText }}</text>
					</view>
					<view style="flex:1;height:96rpx;display:flex;align-items:center;justify-content:center;border-left:1rpx solid #F1F5F9;" v-if="confirmCancelText" @click="confirmVisible = false; if(onConfirm) onConfirm()">
						<text style="font-size:30rpx;font-weight:700;color:#10B981;">{{ confirmConfirmText }}</text>
					</view>
					<view style="flex:1;height:96rpx;display:flex;align-items:center;justify-content:center;" v-else @click="confirmVisible = false; if(onConfirm) onConfirm()">
						<text style="font-size:30rpx;font-weight:700;color:#10B981;">{{ confirmConfirmText }}</text>
					</view>
				</view>
			</view>
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
			isPublisher: false,
			userLatitude: 39.908823,
			userLongitude: 116.397470,
			distanceText: '',
			confirmVisible: false,
			confirmTitle: '提示',
			confirmContent: '',
			confirmConfirmText: '确定',
			confirmCancelText: '取消',
			onConfirm: null
		}
	},
	computed: {
		statusTitle() {
			const titles = {
				open: '等待接单',
				accepted: '进行中',
				pending_confirm: '待双方确认',
				completed: '已完成',
				cancelled: '已取消'
			}
			return titles[this.order?.status] || '未知状态'
		},
		statusTime() {
			if (this.order?.status === 'completed') {
				return `完成于 ${this.formatTime(this.order.completedAt)}`
			} else if (this.order?.status === 'accepted') {
				return `接单于 ${this.formatTime(this.order.acceptedAt)}`
			} else if (this.order?.status === 'pending_confirm') {
				return `申请完成于 ${this.formatTime(this.order.pendingConfirmAt)}`
			}
			return `发布于 ${this.formatTime(this.order?.createdAt)}`
		}
	},
	onLoad(options) {
		const id = options.id
		if (!id) return;
		
		// 汇总所有数据源，无论是在 needs 还是 orders 里的都要找到
		const findFromAll = () => {
			const sources = [
				...(this.needStore.needs || []),
				...(this.orderStore.orders || [])
			]
			// 尝试匹配 id 或 needId，并使用 == 避免类型问题
			return sources.find(item => item.id == id || (item.needId && item.needId == id))
		}

		this.order = findFromAll()
		
		// 如果没找到，尝试本地缓存
		if (!this.order) {
			const localOrders = uni.getStorageSync('orders') || []
			const localNeeds = uni.getStorageSync('needs') || []
			const localSources = [...localOrders, ...localNeeds]
			this.order = localSources.find(item => item.id == id || (item.needId && item.needId == id))
		}
		
		if (this.order && this.userStore.currentUser) {
			this.isPublisher = this.order.publisher?.id === this.userStore.currentUser.id
		}
	},
	methods: {
		formatTime(timestamp) {
			if (!timestamp) return ''
			const date = new Date(timestamp)
			return `${date.getFullYear()}-${(date.getMonth() + 1).toString().padStart(2, '0')}-${date.getDate().toString().padStart(2, '0')} ${date.getHours().toString().padStart(2, '0')}:${date.getMinutes().toString().padStart(2, '0')}`
		},
		async completeOrder() {
			this.confirmTitle = '确认完成'
			this.confirmContent = '确认该订单已完成吗？完成后将支付酬劳给帮手掌柜。'
			this.confirmConfirmText = '确定'
			this.confirmCancelText = '取消'
			this.onConfirm = async () => {
				const result = this.orderStore.completeOrder(this.order.id)
				if (result.success) {
					this.order.status = 'completed'
					this.order.completedAt = Date.now()
					this.sendNotification('completed', '订单已完成')
					uni.showToast({ title: '订单已完成', icon: 'success' })
				} else {
					uni.showToast({ title: result.message, icon: 'none' })
				}
			}
			this.confirmVisible = true
		},
		async applyComplete() {
			const isConfirmed = await new Promise((resolve) => {
				uni.showModal({
					title: '申请完成',
					content: '确定服务已完成，申请结案吗？等待发布者确认后订单将正式完成。',
					confirmColor: '#10B981',
					success: (res) => resolve(res.confirm)
				})
			})

			if (!isConfirmed) return

			// 同步 orderStore 和 needStore 的状态
			const result = this.orderStore.applyComplete(this.order.id)
			if (result.success) {
				this.order.status = 'pending_confirm'
				this.order.helperConfirmed = true
				this.order.pendingConfirmAt = Date.now()

				// 同步 needStore 状态，确保 need 也进入 pending_confirm
				const needId = this.order.needId || this.order.id
				const needResult = this.needStore.markComplete(needId)
				if (needResult.success) {
					// needStore 也同步更新成功
				}

				this.sendNotification('pending_confirm', '帮手已申请完成，等待您确认')
				uni.showToast({ title: '已申请完成', icon: 'success' })
			} else {
				uni.showToast({ title: result.message, icon: 'none' })
			}
		},
		async confirmComplete() {
			const role = this.isPublisher ? '发布者' : '帮手'
			const isConfirmed = await new Promise((resolve) => {
				uni.showModal({
					title: '确认完成',
					content: `确认该订单已完成吗？${role}确认后订单将正式结束。`,
					confirmColor: '#10B981',
					success: (res) => resolve(res.confirm)
				})
			})

			if (!isConfirmed) return

			const needId = this.order.needId || this.order.id

			if (this.isPublisher) {
				// 发布者确认：走 needStore.confirmComplete（含结算逻辑）
				const result = this.needStore.confirmComplete(needId)

				if (result.success) {
					this.order.publisherConfirmed = true
					this.order.status = 'completed'
					this.order.completedAt = Date.now()
					this.sendNotification('completed', '订单已完成，双方已确认')

					// 同步更新 orderStore 中的订单状态
					const orderInStore = this.orderStore.orders.find(o => o.id === this.order.id)
					if (orderInStore) {
						orderInStore.publisherConfirmed = true
						orderInStore.status = 'completed'
						orderInStore.completedAt = Date.now()
					}

					uni.showToast({ title: result.message, icon: 'success' })
				} else {
					uni.showToast({ title: result.message, icon: 'none' })
				}
			} else {
				// 帮手确认：走 orderStore.confirmComplete（双方确认模式，含结算逻辑）
				const result = this.orderStore.confirmComplete(this.order.id)

				if (result.success) {
					this.order.helperConfirmed = true

					// 同步更新 needStore 中的 need 状态
					const needInStore = this.needStore.needs.find(n => n.id === needId)
					if (needInStore) {
						needInStore.status = this.order.status
						if (this.order.status === 'completed') {
							needInStore.completedAt = Date.now()
						}
					}

					if (this.order.status === 'completed') {
						this.order.completedAt = Date.now()
						this.sendNotification('completed', '订单已完成，双方已确认')
					} else {
						this.sendNotification('pending_confirm', '帮手已确认完成，等待发布者确认')
					}

					uni.showToast({ title: this.order.status === 'completed' ? '订单已完成' : '已确认，等待发布者确认', icon: 'success' })
				} else {
					uni.showToast({ title: result.message, icon: 'none' })
				}
			}
		},
		contactUser() {
			const targetUser = this.isPublisher ? this.order.helper : this.order.publisher
			if (!targetUser || !targetUser.id) {
				uni.showToast({ title: '暂无联系人信息', icon: 'none' })
				return
			}
			uni.navigateTo({
				url: `/pages/chat/chat?userId=${targetUser.id}&nickname=${targetUser.nickname}`
			})
		},
		async cancelOrder() {
			const isConfirmed = await new Promise((resolve) => {
				uni.showModal({
					title: this.isPublisher ? '取消订单' : '取消接单',
					content: this.isPublisher
						? '确定要取消这个订单吗？取消后将无法恢复。'
						: '确定要取消接单吗？取消后发布者可以重新选择帮手。',
					confirmColor: '#EF4444',
					success: (res) => resolve(res.confirm)
				})
			})

			if (!isConfirmed) return

			const orderId = this.order.id
			const result = this.orderStore.cancelOrder(orderId)

			if (result.success) {
				this.order.status = 'cancelled'
				this.order.cancelledAt = Date.now()
				this.sendCancelNotification()
				uni.showToast({
					title: this.isPublisher ? '订单已取消' : '已取消接单',
					icon: 'success'
				})
				setTimeout(() => {
					uni.navigateBack()
				}, 1500)
			} else {
				uni.showToast({ title: result.message, icon: 'none' })
			}
		},
		sendCancelNotification() {
			const targetUser = this.isPublisher ? this.order.helper : this.order.publisher
			if (targetUser && targetUser.id) {
				const notifications = uni.getStorageSync('notifications') || []
				notifications.unshift({
					id: Date.now(),
					type: 'order',
					title: '订单已取消',
					content: this.isPublisher ? '发布者已取消订单' : '帮手已取消接单',
					orderId: this.order.id,
					orderTitle: this.order.title,
					status: 'cancelled',
					read: false,
					createdAt: Date.now()
				})
				uni.setStorageSync('notifications', notifications)

				const unreadCount = notifications.filter(n => !n.read).length
				if (unreadCount > 0) {
					uni.setTabBarBadge({ index: 3, text: unreadCount > 99 ? '99+' : String(unreadCount) })
				} else {
					uni.removeTabBarBadge({ index: 3 })
				}
			}
		},
		sendNotification(status, message) {
			const notifications = uni.getStorageSync('notifications') || []
			const titleMap = {
				'accepted': '订单已被接单',
				'pending_confirm': '订单待确认',
				'completed': '订单已完成',
				'cancelled': '订单已取消',
				'helper_confirmed': '帮手已确认完成',
				'publisher_confirmed': '发布者已确认'
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
		goRate() {
			uni.navigateTo({
				url: `/pages/rate/rate?orderId=${this.order.id}`
			})
		},
		previewImage(image) {
			uni.previewImage({ urls: [image] })
		},
		republishOrder() {
			const orderData = {
				title: this.order.title,
				description: this.order.description,
				reward: this.order.reward,
				location: this.order.location,
				latitude: this.order.latitude,
				longitude: this.order.longitude,
				image: this.order.image || '',
				deadline: this.order.deadline || '',
				category: this.order.category || '其他'
			}
			uni.setStorageSync('republishData', orderData)
			uni.navigateTo({
				url: '/pages/publish/publish'
			})
		}
	}
}
</script>

<style scoped>
.container {
	min-height: 100vh;
	background: #FFFFFF;
}

.nav-header {
	padding: 80rpx 40rpx 20rpx;
}

.screen {
	padding: 0 60rpx;
	height: calc(100vh - 160rpx);
}

.hero-title {
	font-size: 64rpx;
	font-weight: 800;
	margin: 40rpx 0 80rpx;
	letter-spacing: -2rpx;
	color: #1F2937;
	line-height: 1.2;
}

.detail-item {
	margin-bottom: 70rpx;
	border-left: 6rpx solid #D1FAE5;
	padding-left: 40rpx;
}

.label {
	font-size: 24rpx;
	color: #6B7280;
	margin-bottom: 16rpx;
	font-weight: 700;
	text-transform: uppercase;
	letter-spacing: 2rpx;
}

.value {
	font-size: 36rpx;
	font-weight: 600;
	color: #1F2937;
}

.value.status {
	color: #10B981;
}
.value.status.completed {
	color: #6B7280;
}

.value.highlight {
	color: #10B981;
	font-size: 44rpx;
	font-weight: 800;
}

.value.desc {
	font-size: 30rpx;
	font-weight: 400;
	color: #4B5563;
	line-height: 1.6;
}

.value.time-node {
	font-size: 28rpx;
	color: #6B7280;
}

.image-wrapper {
	margin-top: 20rpx;
	border-radius: 24rpx;
	overflow: hidden;
}

.order-image {
	width: 100%;
	height: 400rpx;
	border-radius: 24rpx;
}

.no-image {
	font-size: 28rpx;
	color: #9CA3AF;
	font-style: italic;
	margin-top: 16rpx;
}

.deadline-text {
	color: #EF4444;
	font-weight: 700;
}

.people-minimal {
	display: flex;
	flex-direction: column;
	gap: 20rpx;
}

.person {
	display: flex;
	justify-content: space-between;
	align-items: center;
}

.p-role {
	font-size: 28rpx;
	color: #9CA3AF;
}

.p-name {
	font-size: 30rpx;
	font-weight: 600;
	color: #374151;
}

.btn-group {
	margin-top: 80rpx;
	padding-bottom: 80rpx;
	display: flex;
	flex-direction: column;
	gap: 30rpx;
}

button {
	border: none !important;
	outline: none !important;
	box-shadow: none !important;
	-webkit-appearance: none !important;
	background: transparent !important;
	background-color: transparent !important;
	margin: 0 !important;
	padding: 0 !important;
}

.btn {
	height: 112rpx;
	border-radius: 56rpx;
	display: flex;
	align-items: center;
	justify-content: center;
	font-weight: 700;
	font-size: 32rpx;
	border: none !important;
	outline: none !important;
	box-shadow: none !important;
	-webkit-appearance: none !important;
	background-color: transparent !important;
}

.btn::after {
	border: none !important;
}

.btn-p {
	background: #10B981;
	color: white;
	box-shadow: 0 20rpx 40rpx rgba(16, 185, 129, 0.2);
}

.btn-s {
	background: #F3F4F6;
	color: #6B7280;
}

.btn-cancel {
	background: #FEF2F2;
	color: #EF4444;
}

.loading {
	display: flex;
	align-items: center;
	justify-content: center;
	height: 100vh;
}

.loading-text {
	color: #6B7280;
}
</style>
