<template>
	<view class="container">
		<!-- Simple Nav -->
		<view class="nav-header">
		</view>

		<!-- Content -->
		<scroll-view class="screen" scroll-y v-if="need">
			<view class="hero-title">{{ need.title }}</view>

			<view class="detail-item">
				<view class="label">当前状态</view>
				<view class="value status" :class="need.status">{{ getStatusText(need.status) }}</view>
			</view>

			<view class="detail-item">
				<view class="label">服务位置</view>
				<view class="value">{{ need.location }}</view>
				<view v-if="need.latitude && need.longitude" class="map-link" @click="openMap">
					<IconFont name="map-location" :size="18" color="#EF4444" class="map-icon" /> 查看地图
				</view>
			</view>

			<view class="detail-item" v-if="need.detailAddress">
				<view class="label">具体位置</view>
				<view class="value">{{ need.detailAddress }}</view>
			</view>

			<view class="detail-item">
				<view class="label">订单报酬</view>
				<view class="value">¥ {{ need.reward }}</view>
			</view>

			<view class="detail-item" v-if="need.description">
				<view class="label">详情描述</view>
				<view class="value desc">{{ need.description }}</view>
			</view>

			<view class="detail-item">
				<view class="label">现场图片</view>
				<view v-if="need.image" class="image-wrapper">
					<image :src="need.image" mode="aspectFill" class="need-image" @click="previewImage(need.image)" />
				</view>
				<view v-else class="no-image">暂无图片展示</view>
			</view>

			<view class="detail-item">
				<view class="value">{{ formatTime(need.createdAt) }}</view>
			</view>

			<view class="detail-item" v-if="need.deadline">
				<view class="label">最晚什么时候</view>
				<view class="value deadline-text">{{ need.deadline }}</view>
			</view>

			<!-- Action Button -->
			<view class="btn-group">
				<!-- Case 1: Open need, not mine -->
				<button v-if="need.status === 'open' && need.publisher.id !== userStore.currentUser.id"
					class="btn btn-p" @click="acceptNeed">✋ 接单帮忙</button>

				<!-- Case 2: Publisher in accepted - show 立即沟通 -->
				<button v-if="need.status === 'accepted' && need.publisher.id === userStore.currentUser.id"
					class="btn btn-p" @click="goToChat">立即沟通</button>

				<!-- Case 3: Helper in accepted - show 申请完成 -->
				<button v-if="need.status === 'accepted' && isHelper"
					class="btn btn-p" @click="applyComplete">申请完成</button>

				<!-- Case 4: Helper in accepted - show 联系发布者 -->
				<button v-if="need.status === 'accepted' && isHelper"
					class="btn btn-s" @click="goToChat">联系发布者</button>

				<!-- Case 5: Pending confirm, I am the publisher -->
				<button v-else-if="need.status === 'pending_confirm' && need.publisher.id === userStore.currentUser.id"
					class="btn btn-confirm" @click="confirmComplete">确认完成</button>

				<!-- Case 6: Pending confirm, I am the helper - show 等待确认 -->
				<button v-else-if="need.status === 'pending_confirm' && isHelper"
					class="btn btn-s" disabled>等待发布者确认</button>

				<!-- Case 7: Completed need, need rating -->
				<button v-if="need.status === 'completed' && need.publisher.id === userStore.currentUser.id && !need.isRated"
					class="btn btn-p" @click="rateOrder">评价帮手</button>
				<button v-if="need.status === 'completed' && need.publisher.id === userStore.currentUser.id"
					class="btn btn-s" @click="goToChat">联系帮手</button>
				<button v-if="need.status === 'completed' && isHelper"
					class="btn btn-s" @click="goToChat">联系发布者</button>

				<!-- Case 9: Cancelled, my own need - republish -->
				<button v-else-if="need.status === 'cancelled' && need.publisher.id === userStore.currentUser.id"
					class="btn btn-p" @click="republishNeed">再次发布</button>

				<!-- Case 10: Cancelled -->
				<button v-else-if="need.status === 'cancelled'"
					class="btn btn-s" disabled>已取消</button>

				<!-- Case 11: My own open need -->
				<button v-else-if="need.status === 'open' && need.publisher.id === userStore.currentUser.id"
					class="btn btn-s" @click="cancelNeed">取消发布</button>
			</view>
		</scroll-view>

		<!-- 加载中 -->
		<view v-else class="loading">
			<text class="loading-text">加载中...</text>
		</view>

		<!-- 接单成功弹窗 -->
		<view v-if="acceptSuccessVisible" class="accept-mask" @click="acceptSuccessVisible = false">
			<view class="accept-popup" @click.stop>
				<view class="success-icon">
					<IconFont name="circle-check" :size="80" />
				</view>
				<text class="accept-title">接单成功！</text>
				<text class="accept-subtitle">请及时联系发布者，完成任务后记得完成订单</text>
				<view class="accept-actions">
					<view class="accept-btn" @click="acceptSuccessVisible = false">
						<text>知道了</text>
					</view>
				</view>
			</view>
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
			need: null,
			userLatitude: 39.908823,
			userLongitude: 116.397470,
			distanceText: '',
			mapMarkers: [],
			confirmVisible: false,
			confirmTitle: '提示',
			confirmContent: '',
			confirmConfirmText: '确定',
			confirmCancelText: '取消',
			acceptSuccessVisible: false,
			onConfirm: null
		}
	},
	computed: {
		isAccepter() {
			return this.need && (
				(this.need.helper && this.need.helper.id === this.userStore.currentUser.id) ||
				(this.need.accepterId === this.userStore.currentUser.id)
			)
		},
		isHelper() {
			return this.need && this.need.helper && this.need.helper.id === this.userStore.currentUser.id
		}
	},
	onLoad(options) {
		const id = options.id
		if (!id) return;

		// 汇总所有数据源，增强查找逻辑
		const findFromAll = () => {
			const sources = [
				...(this.needStore.needs || []),
				...(this.orderStore.orders || [])
			]
			// 尝试匹配 id 或 needId，并使用 == 避免类型问题
			return sources.find(item => item.id == id || (item.needId && item.needId == id))
		}

		this.need = findFromAll()
		
		// 如果还没找到，尝试从本地缓存中找（兜底逻辑）
		if (!this.need) {
			const localNeeds = uni.getStorageSync('needs') || []
			const localOrders = uni.getStorageSync('orders') || []
			const localSources = [...localNeeds, ...localOrders]
			this.need = localSources.find(item => item.id == id || (item.needId && item.needId == id))
		}

		if (this.need) {
			this.getUserLocation()
		}
	},
	methods: {
		getStatusText(status) {
			const map = {
				'open': '等待接单',
				'accepted': '帮手已接单',
				'pending_confirm': '待确认完成',
				'completed': '订单已完成',
				'cancelled': '已取消'
			}
			return map[status] || status
		},
		getUserLocation() {
			uni.getLocation({
				type: 'gcj02',
				success: (res) => {
					this.userLatitude = res.latitude
					this.userLongitude = res.longitude
				},
				fail: () => {}
			})
		},
		openMap() {
			if (!this.need.latitude || !this.need.longitude) return
			uni.openLocation({
				latitude: this.need.latitude,
				longitude: this.need.longitude,
				name: this.need.location,
				address: this.need.location
			})
		},
		formatTime(timestamp) {
			if (!timestamp) return ''
			const date = new Date(timestamp)
			return `${date.getFullYear()}-${(date.getMonth() + 1).toString().padStart(2, '0')}-${date.getDate().toString().padStart(2, '0')} ${date.getHours().toString().padStart(2, '0')}:${date.getMinutes().toString().padStart(2, '0')}`
		},
		async acceptNeed() {
			if (!this.userStore.isLoggedIn || !this.userStore.token) {
				uni.showToast({ title: '请先登录后再接单', icon: 'none' })
				setTimeout(() => {
					uni.navigateTo({ url: '/pages/login/login' })
				}, 500)
				return
			}
			const result = await this.needStore.acceptNeed(this.need.id)
			if (result.success) {
				this.need.status = 'accepted'
				this.acceptSuccessVisible = true
				setTimeout(() => {
					this.acceptSuccessVisible = false
				}, 3000)
			} else {
				uni.showToast({ title: result.message, icon: 'none' })
			}
		},
		goToChat() {
			const targetUser = this.need.publisher.id === this.userStore.currentUser.id ?
				this.need.helper :
				this.need.publisher;

			if (!targetUser || !targetUser.id) {
				uni.showToast({ title: '暂无可沟通的对方', icon: 'none' });
				return;
			}

			uni.navigateTo({
				url: `/pages/chat/chat?userId=${targetUser.id}&nickname=${targetUser.nickname}`
			})
		},
		applyComplete() {
			this.confirmTitle = '申请完成'
			this.confirmContent = '确定服务已完成，申请结案吗？等待发布者确认后订单将正式完成。'
			this.confirmConfirmText = '确认'
			this.confirmCancelText = '取消'
			this.onConfirm = async () => {
				const result = await this.needStore.markComplete(this.need.id)
				if (result.success) {
					this.need.status = 'pending_confirm'
					this.need.markedCompleteAt = Date.now()
					this.$forceUpdate()
					uni.showToast({ title: result.message, icon: 'success' })
				} else {
					uni.showToast({ title: result.message, icon: 'none' })
				}
			}
			this.confirmVisible = true
		},
		rateOrder() {
			uni.showToast({ title: '评价功能开发中', icon: 'none' })
		},
		cancelNeed() {
			this.confirmTitle = '提示'
			this.confirmContent = '确定要取消这个需求吗？'
			this.confirmConfirmText = '确定'
			this.confirmCancelText = '取消'
			this.onConfirm = () => {
				this.need.status = 'cancelled'
				this.need.cancelledAt = Date.now()
				const needInStore = this.needStore.needs.find(n => n.id === this.need.id)
				if (needInStore) {
					needInStore.status = 'cancelled'
					needInStore.cancelledAt = Date.now()
				}
				const orderInStore = this.orderStore.orders.find(o => o.needId === this.need.id)
				if (orderInStore) {
					orderInStore.status = 'cancelled'
					orderInStore.cancelledAt = Date.now()
				}
				this.sendCancelNotification()
				this.$forceUpdate()
				uni.showToast({ title: '已取消', icon: 'success' })
			}
			this.confirmVisible = true
		},
		confirmComplete() {
			this.confirmTitle = '确认完成'
			this.confirmContent = '确认帮手已完成任务吗？确认后报酬将发放给帮手。'
			this.confirmConfirmText = '确认完成'
			this.confirmCancelText = '取消'
			this.onConfirm = async () => {
				const result = await this.needStore.confirmComplete(this.need.id)
				if (result.success) {
					this.need.status = 'completed'
					this.need.completedAt = Date.now()
					const needInStore = this.needStore.needs.find(n => n.id === this.need.id)
					if (needInStore) {
						needInStore.status = 'completed'
						needInStore.completedAt = Date.now()
					}
					this.$forceUpdate()
					uni.showToast({ title: result.message, icon: 'success' })
				} else {
					uni.showToast({ title: result.message, icon: 'none' })
				}
			}
			this.confirmVisible = true
		},
		sendCancelNotification() {
			if (this.need.helper && this.need.helper.id) {
				const notifications = uni.getStorageSync('notifications') || []
				notifications.unshift({
					id: Date.now(),
					type: 'order',
					title: '订单已取消',
					content: '发布者已取消订单',
					orderId: this.need.id,
					orderTitle: this.need.title,
					status: 'cancelled',
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
		previewImage(image) {
			uni.previewImage({ urls: [image] })
		},
		republishNeed() {
			const needData = {
				title: this.need.title,
				description: this.need.description,
				reward: this.need.reward,
				location: this.need.location,
				detailAddress: this.need.detailAddress || '',
				address: this.need.address,
				latitude: this.need.latitude,
				longitude: this.need.longitude,
				image: this.need.image || '',
				time: this.need.time || '',
				deadline: this.need.deadline || '',
				category: this.need.category || '其他'
			}
			uni.setStorageSync('republishData', needData)
			uni.switchTab({
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
	padding: 44px 20px 10px;
}

.screen {
	padding: 0 30px;
	height: calc(100vh - 80px);
}

.hero-title {
	font-size: 32px;
	font-weight: 800;
	margin: 20px 0 40px;
	letter-spacing: -1px;
	color: #1F2937;
	line-height: 1.2;
}

.detail-item {
	margin-bottom: 35px;
	border-left: 3px solid #D1FAE5;
	padding-left: 20px;
}

.label {
	font-size: 12px;
	color: #6B7280;
	margin-bottom: 8px;
	font-weight: 700;
	text-transform: uppercase;
	letter-spacing: 1px;
}

.value {
	font-size: 18px;
	font-weight: 600;
	color: #1F2937;
}

.value.status {
	color: #10B981;
}
.value.status.pending_confirm {
	color: #F59E0B;
}
.value.status.completed {
	color: #6B7280;
}

.value.desc {
	font-size: 15px;
	font-weight: 400;
	color: #4B5563;
	line-height: 1.6;
}

.map-link {
	margin-top: 10px;
	font-size: 13px;
	color: #10B981;
	font-weight: 600;
}

.map-icon {
	margin-right: 4px;
	vertical-align: middle;
}

.image-wrapper {
	margin-top: 10px;
	border-radius: 12px;
	overflow: hidden;
}

.need-image {
	width: 100%;
	height: 200px;
	border-radius: 12px;
}

.no-image {
	font-size: 14px;
	color: #9CA3AF;
	font-style: italic;
	margin-top: 8px;
}

.deadline-text {
	color: #EF4444;
	font-weight: 700;
}

.btn-group {
	margin-top: 40px;
	padding-bottom: 40px;
}

button {
	-webkit-appearance: none;
	appearance: none;
	border: none;
	outline: none;
}

button::after {
	border: none;
}

.btn {
	height: 56px;
	border-radius: 28px;
	display: flex;
	align-items: center;
	justify-content: center;
	font-weight: 700;
	font-size: 16px;
	border: 0;
	border-style: solid;
	border-width: 0;
	border-color: transparent;
	outline: none;
	width: 100%;
	cursor: pointer;
}

.btn::after {
	border: none;
}

.btn-p {
	background: #10B981;
	color: white;
	box-shadow: 0 10px 20px rgba(16, 185, 129, 0.2);
}

.btn-confirm {
	background: #F59E0B;
	color: white;
	box-shadow: 0 10px 20px rgba(245, 158, 11, 0.2);
}

.btn-s {
	background: #F3F4F6;
	color: #6B7280;
	border: none;
	border-width: 0;
	border-style: none;
	border-color: transparent;
	box-shadow: none;
}

.btn-s::after {
	border: none;
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

/* 接单成功弹窗样式 */
.accept-mask {
	position: fixed;
	top: 0;
	left: 0;
	right: 0;
	bottom: 0;
	background: rgba(0, 0, 0, 0.6);
	z-index: 99999;
	display: flex;
	align-items: center;
	justify-content: center;
}

.accept-popup {
	width: 560rpx;
	background: #FFFFFF;
	border-radius: 32rpx;
	padding: 60rpx 40rpx 40rpx;
	text-align: center;
	box-shadow: 0 20rpx 60rpx rgba(0, 0, 0, 0.15);
}

.success-icon {
	margin-bottom: 24rpx;
}

.accept-title {
	display: block;
	font-size: 36rpx;
	font-weight: 700;
	color: #1E293B;
	margin-bottom: 16rpx;
}

.accept-subtitle {
	display: block;
	font-size: 26rpx;
	color: #64748B;
	line-height: 1.6;
	margin-bottom: 40rpx;
}

.accept-actions {
	display: flex;
	justify-content: center;
}

.accept-btn {
	flex: 1;
	height: 80rpx;
	display: flex;
	align-items: center;
	justify-content: center;
	background: #10B981;
	border-radius: 20rpx;
	color: #FFFFFF;
	font-size: 30rpx;
	font-weight: 600;
}
</style>
