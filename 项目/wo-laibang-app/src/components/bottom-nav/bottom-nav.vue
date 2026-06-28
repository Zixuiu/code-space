<template>
	<view class="bottom-nav">
		<view
			v-for="(item, index) in list"
			:key="index"
			class="nav-item"
			:class="{ active: current === index }"
			@click="switchTab(index)"
		>
			<view class="icon-wrapper">
				<IconFont :name="item.icon" :size="48" class="nav-icon" />
				<view v-if="item.badge > 0" class="badge">
					<text class="badge-text">{{ item.badge > 99 ? '99+' : item.badge }}</text>
				</view>
			</view>
			<text class="nav-text">{{ item.text }}</text>
		</view>
	</view>
</template>

<script>
import IconFont from '@/components/icon-font/icon-font.vue'

export default {
	name: 'BottomNav',
	components: {
		IconFont
	},
	props: {
		current: { type: Number, default: 0 }
	},
	data() {
		return {
			messageUnreadCount: 0
		}
	},
	computed: {
		list() {
			return [
				{ pagePath: '/pages/index/index', text: '发现', icon: 'home', badge: 0 },
				{ pagePath: '/pages/publish/publish', text: '发布', icon: 'plus', badge: 0 },
				{ pagePath: '/pages/orders/orders', text: '订单', icon: 'clipboard-list', badge: 0 },
				{ pagePath: '/pages/messages/messages', text: '消息', icon: 'mail', badge: this.messageUnreadCount },
				{ pagePath: '/pages/profile/profile', text: '我的', icon: 'user', badge: 0 }
			]
		}
	},
	created() {
		this.updateBadges()
		uni.$on('clearMessageBadge', () => {
			this.messageUnreadCount = 0
		})
		uni.$on('updateBadge', () => {
			this.updateBadges()
		})
	},
	mounted() {
		this.updateBadges()
		this.badgeTimer = setInterval(() => {
			this.updateBadges()
		}, 3000)
	},
	beforeDestroy() {
		uni.$off('clearMessageBadge')
		uni.$off('updateBadge')
		if (this.badgeTimer) {
			clearInterval(this.badgeTimer)
			this.badgeTimer = null
		}
	},
	methods: {
		switchTab(index) {
			if (this.current !== index) {
				uni.switchTab({ url: this.list[index].pagePath })
			}
		},
		updateBadges() {
			const currentUserId = uni.getStorageSync('userInfo')?.id
			const conversations = uni.getStorageSync('conversations') || []
			const messageUnreadCount = conversations
				.filter(conv => {
					if (!conv.relatedOrder) return true
					const order = conv.relatedOrder
					const isPublisher = order.publisher?.id === currentUserId
					const isHelper = order.helper?.id === currentUserId
					const isPublisherSim = order.publisher?.id && order.publisher.id.startsWith('sim')
					const isHelperSim = order.helper?.id && order.helper.id.startsWith('sim')
					if (isPublisherSim && isHelperSim && !isPublisher && !isHelper) return false
					return isPublisher || isHelper
				})
				.reduce((sum, c) => sum + (c.unread || 0), 0)

			const notifications = uni.getStorageSync('notifications') || []
			const unreadNotifications = notifications.filter(n => !n.read).length

			this.messageUnreadCount = messageUnreadCount
			const totalUnread = unreadNotifications + messageUnreadCount
			uni.setStorageSync('totalUnreadCount', totalUnread)

			if (totalUnread > 0) {
				uni.setTabBarBadge({ index: 3, text: totalUnread > 99 ? '99+' : String(totalUnread) })
			} else {
				uni.removeTabBarBadge({ index: 3 })
			}
		},
		clearMessageBadge() {
			this.messageUnreadCount = 0
		}
	}
}
</script>

<style scoped>
.bottom-nav {
	position: fixed;
	bottom: 0;
	left: 0;
	right: 0;
	height: 100rpx;
	background: white;
	display: flex;
	justify-content: space-around;
	align-items: center;
	padding-bottom: constant(safe-area-inset-bottom);
	padding-bottom: env(safe-area-inset-bottom);
	border-top: 2rpx solid #eee;
	z-index: 9999;
}
.nav-item {
	display: flex;
	flex-direction: column;
	align-items: center;
	justify-content: center;
	padding: 0 20rpx;
	position: relative;
}
.icon-wrapper {
	position: relative;
}
.nav-icon {
	margin-bottom: 4rpx;
	color: #999;
}
.nav-text { font-size: 24rpx; color: #999; }
.nav-item.active .nav-icon {
	color: #10B981;
}
.nav-item.active .nav-text { color: #10B981; }
.green-icon { color: #10B981 !important; }
.green-text { color: #10B981 !important; }
.badge {
	position: absolute;
	top: -12rpx;
	right: -20rpx;
	min-width: 36rpx;
	height: 36rpx;
	background: #EF4444;
	border-radius: 18rpx;
	display: flex;
	align-items: center;
	justify-content: center;
	padding: 0 10rpx;
}
.badge-text {
	font-size: 20rpx;
	font-weight: 700;
	color: #FFFFFF;
}
</style>
