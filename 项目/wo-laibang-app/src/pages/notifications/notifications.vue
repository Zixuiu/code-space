<template>
	<view class="container">
		<view class="header">
			<text class="header-title">消息通知</text>
			<view class="header-right" @click="markAllRead" v-if="hasUnread">
				<text class="mark-read-btn">全部已读</text>
			</view>
		</view>

		<view class="filter-tabs">
			<view
				v-for="tab in filterTabs"
				:key="tab.value"
				class="filter-tab"
				:class="{ active: currentFilter === tab.value }"
				@click="switchFilter(tab.value)"
			>
				<text class="filter-text">{{ tab.label }}</text>
			</view>
		</view>

		<scroll-view class="content-scroll" scroll-y>
			<view v-if="notifications.length === 0" class="empty-state">
				<view class="empty-icon-wrapper">
					<IconFont name="bell" :size="40" color="#10B981" />
				</view>
				<text class="empty-title">暂无通知</text>
				<text class="empty-subtitle">有新的通知会在这里显示~</text>
			</view>

			<view v-else class="notification-content">
				<view v-for="(group, dateKey) in groupedNotifications" :key="dateKey" class="date-group">
					<view class="date-label">{{ getDateLabel(dateKey) }}</view>
					<view class="timeline">
						<view
							v-for="item in group"
							:key="item.id"
							class="timeline-item-wrapper"
							@touchstart="touchStart($event, item.id)"
							@touchmove="touchMove($event, item.id)"
							@touchend="touchEnd($event, item.id)"
						>
							<view
								class="delete-action"
								:class="{ show: deleteId === item.id }"
								@click.stop="deleteNotification(item.id)"
							>
								<IconFont name="trash-2" :size="18" />
								<text>删除</text>
							</view>
							<view
								class="timeline-item"
								:class="{ unread: !item.read, open: deleteId === item.id }"
								@click="handleNotification(item)"
							>
								<view class="timeline-dot"></view>
								<view v-if="!item.read" class="unread-line"></view>
								<view class="timeline-card">
									<view class="timeline-header">
										<view class="timeline-icon" :class="item.type">
											<IconFont :name="getIconName(item.type)" :size="20" />
										</view>
										<text class="timeline-title">{{ item.title }}</text>
										<text class="timeline-time">{{ formatTime(item.time) }}</text>
									</view>
									<text class="timeline-desc">{{ item.content }}</text>
								</view>
							</view>
						</view>
					</view>
				</view>
			</view>

			<view class="bottom-space"></view>
		</scroll-view>
	</view>
</template>

<script>
export default {
	data() {
		return {
			notifications: [],
			currentFilter: 'all',
			deleteId: null,
			startX: 0,
			filterTabs: [
				{ label: '全部', value: 'all' },
				{ label: '订单', value: 'order' },
				{ label: '系统', value: 'system' }
			]
		}
	},
	computed: {
		filteredNotifications() {
			if (this.currentFilter === 'all') {
				return this.notifications
			}
			return this.notifications.filter(n => n.type === this.currentFilter)
		},
		groupedNotifications() {
			const groups = {}
			const today = new Date().setHours(0, 0, 0, 0)
			const yesterday = today - 86400000

			this.filteredNotifications.forEach(item => {
				const itemDate = new Date(item.time).setHours(0, 0, 0, 0)
				let key
				if (itemDate === today) {
					key = 'today'
				} else if (itemDate === yesterday) {
					key = 'yesterday'
				} else {
					key = 'earlier'
				}
				if (!groups[key]) {
					groups[key] = []
				}
				groups[key].push(item)
			})

			return groups
		},
		hasUnread() {
			return this.notifications.some(n => !n.read)
		}
	},
	onShow() {
		uni.hideTabBar()
		this.loadNotifications()
	},
	methods: {
		loadNotifications() {
			const all = uni.getStorageSync('notifications') || []
			this.notifications = all.sort((a, b) => b.time - a.time)
		},
		switchFilter(filter) {
			this.currentFilter = filter
		},
		getIconName(type) {
			const icons = {
				order: 'clipboard',
				message: 'message',
				system: 'info-circle',
				reward: 'wallet',
				complete: 'check-circle'
			}
			return icons[type] || 'alert-circle'
		},
		getDateLabel(dateKey) {
			const labels = {
				today: '今天',
				yesterday: '昨天',
				earlier: '更早'
			}
			return labels[dateKey] || dateKey
		},
		formatTime(timestamp) {
			const now = Date.now()
			const diff = now - timestamp
			const minutes = Math.floor(diff / 60000)
			const hours = Math.floor(diff / 3600000)
			const days = Math.floor(diff / 86400000)

			if (minutes < 1) return '刚刚'
			if (minutes < 60) return `${minutes}分钟前`
			if (hours < 24) return `${hours}小时前`
			if (days < 7) return `${days}天前`

			const date = new Date(timestamp)
			return `${date.getMonth() + 1}/${date.getDate()}`
		},
		handleNotification(item) {
			if (!item.read) {
				item.read = true
				const all = uni.getStorageSync('notifications') || []
				const index = all.findIndex(n => n.id === item.id)
				if (index >= 0) {
					all[index].read = true
					uni.setStorageSync('notifications', all)
				}
				this.updateBadge()
			}

			if (item.action) {
				if (item.action === 'order') {
					uni.switchTab({ url: '/pages/orders/orders' })
				} else if (item.action === 'message') {
					uni.switchTab({ url: '/pages/messages/messages' })
				}
			}
		},
		updateBadge() {
			const notifications = uni.getStorageSync('notifications') || []
			const unreadNotifications = notifications.filter(n => !n.read).length
			const conversations = uni.getStorageSync('conversations') || []
			const unreadMessages = conversations.reduce((sum, c) => sum + (c.unread || 0), 0)
			const totalUnread = unreadNotifications + unreadMessages
			if (totalUnread > 0) {
				uni.setTabBarBadge({
					index: 3,
					text: totalUnread > 99 ? '99+' : String(totalUnread)
				})
			} else {
				uni.removeTabBarBadge({ index: 3 })
			}
			uni.$emit('updateBadge')
		},
		markAllRead() {
			this.notifications.forEach(n => {
				n.read = true
			})
			uni.setStorageSync('notifications', this.notifications)
			this.updateBadge()
			uni.showToast({ title: '已全部设为已读', icon: 'success' })
		},
		deleteNotification(id) {
			this.notifications = this.notifications.filter(n => n.id !== id)
			uni.setStorageSync('notifications', this.notifications)
			this.deleteId = null
			this.updateBadge()
			uni.showToast({ title: '已删除', icon: 'success' })
		},
		touchStart(e, id) {
			this.startX = e.touches[0].clientX
			this.deleteId = null
		},
		touchMove(e, id) {
			const moveX = e.touches[0].clientX
			if (this.startX - moveX > 60) {
				this.deleteId = id
			} else if (moveX - this.startX > 60) {
				this.deleteId = null
			}
		},
		touchEnd(e, id) {
			this.startX = 0
		},
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
	padding: 64rpx 24rpx 16rpx;
	background: #FFFFFF;
	display: flex;
	align-items: center;
	gap: 16rpx;
	border-bottom: 1rpx solid #F1F5F9;
}

.header-title {
	flex: 1;
	font-size: 18px;
	font-weight: 700;
	color: #1E293B;
	text-align: center;
}

.header-right {
	width: 40px;
	display: flex;
	align-items: center;
	justify-content: center;
}

.mark-read-btn {
	font-size: 13px;
	color: #10B981;
	font-weight: 600;
}

.filter-tabs {
	display: flex;
	background: #FFFFFF;
	padding: 0 24rpx;
	border-bottom: 1rpx solid #F1F5F9;
}

.filter-tab {
	flex: 1;
	text-align: center;
	padding: 24rpx 0;
	position: relative;
}

.filter-text {
	font-size: 28rpx;
	font-weight: 600;
	color: #94A3B8;
}

.filter-tab.active .filter-text {
	color: #10B981;
	font-weight: 700;
}

.filter-tab.active::after {
	content: '';
	position: absolute;
	bottom: 0;
	left: 50%;
	transform: translateX(-50%);
	width: 48rpx;
	height: 4rpx;
	background: #10B981;
	border-radius: 2rpx;
}

.content-scroll {
	height: calc(100vh - 140px);
}

.empty-state {
	padding-top: 120px;
	display: flex;
	flex-direction: column;
	align-items: center;
}

.empty-icon-wrapper {
	width: 100px;
	height: 100px;
	background: linear-gradient(135deg, #ECFDF5, #D1FAE5);
	border-radius: 28px;
	display: flex;
	align-items: center;
	justify-content: center;
	margin-bottom: 20px;
}

.empty-title {
	font-size: 16px;
	font-weight: 700;
	color: #374151;
	margin-bottom: 8px;
}

.empty-subtitle {
	font-size: 14px;
	color: #9CA3AF;
}

.notification-content {
	padding: 20rpx 20rpx;
}

.date-group {
	margin-bottom: 24rpx;
}

.date-label {
	font-size: 13px;
	font-weight: 700;
	color: #64748B;
	margin-bottom: 16rpx;
	padding-left: 8rpx;
}

.timeline {
	position: relative;
	padding-left: 32rpx;
}

.timeline::before {
	content: '';
	position: absolute;
	left: 11rpx;
	top: 8rpx;
	bottom: -8rpx;
	width: 2rpx;
	background: linear-gradient(180deg, #10B981, #E2E8F0);
}

.timeline-item {
	position: relative;
	margin-bottom: 16rpx;
}

.timeline-item-wrapper {
	position: relative;
	overflow: hidden;
}

.delete-action {
	position: absolute;
	right: 0;
	top: 0;
	bottom: 0;
	width: 120rpx;
	background: #EF4444;
	display: flex;
	flex-direction: column;
	align-items: center;
	justify-content: center;
	gap: 6rpx;
	transform: translateX(100%);
	transition: transform 0.3s;
	z-index: 1;
	color: #FFFFFF;
	font-size: 22rpx;
}

.delete-action.show {
	transform: translateX(0);
}

.timeline-item.open {
	transform: translateX(-120rpx);
}

.timeline-dot {
	position: absolute;
	left: -28rpx;
	top: 16rpx;
	width: 12rpx;
	height: 12rpx;
	border-radius: 50%;
	border: 3rpx solid #10B981;
	background: #FFFFFF;
}

.timeline-item.unread .timeline-dot {
	background: #10B981;
	border-color: #10B981;
}

.timeline-item.read .timeline-dot {
	background: #FFFFFF;
	border-color: #94A3B8;
}

.unread-line {
	position: absolute;
	right: 16rpx;
	top: 20rpx;
	width: 8rpx;
	height: 8rpx;
	background: #10B981;
	border-radius: 50%;
}

.timeline-card {
	background: #FFFFFF;
	border-radius: 18rpx;
	padding: 16rpx;
	box-shadow: 0 2rpx 8rpx rgba(0, 0, 0, 0.04);
}

.timeline-item.unread .timeline-card {
	background: linear-gradient(135deg, #F0FDF4, #ECFDF5);
	border: 1rpx solid rgba(16, 185, 129, 0.15);
}

.timeline-header {
	display: flex;
	align-items: center;
	gap: 10rpx;
	margin-bottom: 10rpx;
}

.timeline-icon {
	width: 40rpx;
	height: 40rpx;
	border-radius: 12rpx;
	display: flex;
	align-items: center;
	justify-content: center;
}

.timeline-icon.order {
	background: linear-gradient(135deg, #D1FAE5, #A7F3D0);
	color: #059669;
}

.timeline-icon.message {
	background: linear-gradient(135deg, #FCE7F3, #FBCFE8);
	color: #DB2777;
}

.timeline-icon.system {
	background: linear-gradient(135deg, #E0E7FF, #C7D2FE);
	color: #4F46E5;
}

.timeline-icon.reward {
	background: linear-gradient(135deg, #FEF3C7, #FDE68A);
	color: #D97706;
}

.timeline-icon.complete {
	background: linear-gradient(135deg, #D1FAE5, #A7F3D0);
	color: #059669;
}

.timeline-title {
	font-size: 15px;
	font-weight: 700;
	color: #1E293B;
	flex: 1;
}

.timeline-time {
	font-size: 11px;
	color: #94A3B8;
}

.timeline-desc {
	font-size: 13px;
	color: #64748B;
	line-height: 1.5;
	display: -webkit-box;
	-webkit-line-clamp: 2;
	-webkit-box-orient: vertical;
	overflow: hidden;
}

.bottom-space {
	height: 40rpx;
}
</style>