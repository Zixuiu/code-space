<template>
	<view class="container">
		<!-- Header -->
		<view class="header">
			<text class="header-title">我的任务</text>
		</view>

		<!-- Tabs (V5 Style) -->
		<view class="tabs">
			<view
				class="tab"
				:class="{ active: currentTab === 'active' }"
				@click="switchTab('active')"
			>
				<text class="tab-text">进行中</text>
			</view>
			<view
				class="tab"
				:class="{ active: currentTab === 'pending_rate' }"
				@click="switchTab('pending_rate')"
			>
				<text class="tab-text">待评价</text>
			</view>
			<view
				class="tab"
				:class="{ active: currentTab === 'completed' }"
				@click="switchTab('completed')"
			>
				<text class="tab-text">已完成</text>
			</view>
			<view
				class="tab"
				:class="{ active: currentTab === 'cancelled' }"
				@click="switchTab('cancelled')"
			>
				<text class="tab-text">已取消</text>
			</view>
		</view>

		<!-- Content -->
		<scroll-view 
			class="content-scroll" 
			scroll-y 
			refresher-enabled 
			:refresher-triggered="refreshing"
			@refresherrefresh="onRefresh"
		>
			<view v-if="currentList.length === 0" class="empty-state">
				<view class="empty-bg">
					<IconFont :name="getEmptyIcon()" :size="44" class="empty-icon" />
				</view>
				<text class="empty-title">{{ getEmptyTitle() }}</text>
				<text class="empty-subtitle">{{ getEmptySubtitle() }}</text>
				<view class="debug-btn" @click="generateTestOrder" v-if="currentTab === 'active'">
					<text class="debug-btn-text">生成测试订单</text>
				</view>
			</view>

			<view v-else class="order-list">
				<view 
					v-for="item in currentList" 
					:key="item.id"
					class="order-item"
					@click="goToDetail(item)"
					@longpress="showCancelDialog(item)"
				>
					<view class="item-main">
						<view class="item-icon">
							<IconFont :name="getOrderIcon(item)" :size="36" class="icon-text" />
						</view>
						<view class="item-info">
							<view class="info-top">
								<text class="order-title">{{ item.title }}</text>
								<text class="order-price" v-if="item.reward">¥{{ item.reward }}</text>
							</view>
							<view class="order-meta">
							<text class="order-desc">{{ formatTime(item.createdAt) }}</text>
							<view class="loc-tag">
								<IconFont name="map-pin" :size="20" class="loc-icon" />
								<text class="loc-text">{{ item.location }}</text>
							</view>
							<view class="dist-tag">
								<IconFont name="navigation" :size="16" class="dist-icon" />
								<text class="dist-text">{{ calculateDistance(item) || '未知' }}</text>
							</view>
						</view>
						</view>
					</view>
					<view class="item-footer">
						<text class="status-text" :class="item.status">{{ getStatusText(item) }}</text>
						<view class="action-btn" v-if="item.status === 'accepted' || item.status === 'pending_confirm'" @click.stop="contactUser(item)">
							<text class="btn-text">联系对方</text>
						</view>
						<view class="complete-btn" v-if="canMarkComplete(item)" @click.stop="markComplete(item)">
							<text class="complete-btn-text">标记完成</text>
						</view>
					</view>
				</view>
			</view>

			<!-- Bottom Space -->
			<view class="bottom-space"></view>
		</scroll-view>

		<!-- 自定义底部导航 -->
		<bottom-nav :current="2"></bottom-nav>

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
import BottomNav from '@/components/bottom-nav/bottom-nav.vue'
import IconFont from '@/components/icon-font/icon-font.vue'

export default {
	components: {
		BottomNav,
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
			currentTab: 'active',
			refreshing: false,
			confirmVisible: false,
			confirmTitle: '提示',
			confirmContent: '',
			confirmConfirmText: '确定',
			confirmCancelText: '取消',
			onConfirm: null,
			userLatitude: 39.908823,
			userLongitude: 116.397470
		}
	},
	computed: {
		currentList() {
			if (this.currentTab === 'active') {
				return [
					...this.needStore.publishedNeeds.filter(i => i.status === 'accepted' || i.status === 'pending_confirm'),
					...this.orderStore.acceptedOrders.filter(i => i.status === 'accepted' || i.status === 'pending_confirm')
				]
			}
			if (this.currentTab === 'pending_rate') {
				return this.orderStore.completedOrders.filter(i => !i.isRated)
			}
			if (this.currentTab === 'completed') {
				return this.orderStore.completedOrders
			}
			if (this.currentTab === 'cancelled') {
				return [
					...this.needStore.publishedNeeds.filter(i => i.status === 'cancelled'),
					...this.orderStore.orders.filter(i => i.status === 'cancelled')
				]
			}
			return []
		}
	},
	onShow() {
		uni.hideTabBar()
	},
	methods: {
		switchTab(tab) {
			this.currentTab = tab
		},
		getOrderIcon(item) {
			const icons = {
				'快递': 'package',
				'跑腿': 'run',
				'维修': 'tool',
				'保洁': 'tool',
				'宠物': 'paw',
				'搬家': 'truck',
				'其他': 'star'
			}
			for (let key in icons) {
				if (item.title.includes(key)) return icons[key]
			}
			return 'box'
		},
		getStatusText(item) {
			const statusMap = {
				'open': '待接单',
				'accepted': '进行中',
				'pending_confirm': '待确认',
				'completed': '已完成',
				'cancelled': '已取消'
			}
			return statusMap[item.status] || item.status
		},
		formatTime(time) {
			if (!time) return ''
			const diff = Date.now() - time
			if (diff < 60000) return '刚刚'
			if (diff < 3600000) return `${Math.floor(diff/60000)}分钟前`
			if (diff < 86400000) return `${Math.floor(diff/3600000)}小时前`
			const date = new Date(time)
			return `${date.getMonth() + 1}月${date.getDate()}日`
		},
		getEmptyIcon() {
			if (this.currentTab === 'pending_rate') return 'star'
			if (this.currentTab === 'completed') return 'check-circle'
			if (this.currentTab === 'cancelled') return 'x-circle'
			return 'list'
		},
		getEmptyTitle() {
			if (this.currentTab === 'pending_rate') return '暂无待评价订单'
			if (this.currentTab === 'completed') return '暂无已完成订单'
			if (this.currentTab === 'cancelled') return '暂无已取消订单'
			return '暂无进行中订单'
		},
		getEmptySubtitle() {
			if (this.currentTab === 'pending_rate') return '完成订单后即可评价'
			if (this.currentTab === 'all') return '快去接单或发布需求吧'
			return '快去大厅接单吧~'
		},
		goToDetail(item) {
			if (item.status === 'completed') {
				uni.navigateTo({
					url: `/pages/order-detail/order-detail?id=${item.id}`
				})
			} else {
				const detailId = item.needId || item.id
				uni.navigateTo({
					url: `/pages/need-detail/need-detail?id=${detailId}`
				})
			}
		},
		contactUser(item) {
			const publisher = item.publisher || {}
			const helper = item.helper || {}
			const targetUser = helper.id === this.userStore.currentUser.id ? publisher : helper
			if (targetUser && targetUser.id) {
				uni.navigateTo({
					url: `/pages/chat/chat?userId=${targetUser.id}&nickname=${targetUser.nickname || '用户'}`
				})
			} else {
				uni.showToast({ title: '无法联系对方', icon: 'none' })
			}
		},
		canMarkComplete(item) {
			if (item.status !== 'accepted') return false
			const helper = item.helper || {}
			return helper.id === this.userStore.currentUser.id
		},
		async markComplete(item) {
			const needId = item.needId || item.id
			const result = await this.needStore.markComplete(needId)
			if (result.success) {
				item.status = 'pending_confirm'
				uni.showToast({ title: result.message, icon: 'success' })
			} else {
				uni.showToast({ title: result.message, icon: 'none' })
			}
		},
		calculateDistance(item) {
			if (!item.latitude || !item.longitude) return ''
			const R = 6371
			const dLat = this.deg2rad(item.latitude - this.userLatitude)
			const dLon = this.deg2rad(item.longitude - this.userLongitude)
			const a =
				Math.sin(dLat/2) * Math.sin(dLat/2) +
				Math.cos(this.deg2rad(this.userLatitude)) * Math.cos(this.deg2rad(item.latitude)) *
				Math.sin(dLon/2) * Math.sin(dLon/2)
			const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a))
			const d = R * c
			if (d < 1) {
				return `${Math.round(d * 1000)}m`
			}
			return `${d.toFixed(1)}km`
		},
		deg2rad(deg) {
			return deg * (Math.PI / 180)
		},
		generateTestOrder() {
			const titles = [
				'帮忙取快递',
				'上门喂猫',
				'陪老人散步',
				'维修电脑',
				'帮忙搬家',
				'代买东西',
				'帮忙打扫',
				'接送孩子'
			]
			const locations = [
				'阳光花园1栋',
				'绿景苑3单元',
				'智慧家园5栋',
				'幸福里小区',
				'和谐庭2栋'
			]
			const nicknames = [
				'李阿姨', '王叔叔', '张大哥', '刘大姐', '陈同学'
			]

			const randomItem = () => titles[Math.floor(Math.random() * titles.length)]
			const randomLoc = () => locations[Math.floor(Math.random() * locations.length)]
			const randomNick = () => nicknames[Math.floor(Math.random() * nicknames.length)]
			const randomReward = () => Math.floor(Math.random() * 50) + 5

			const testOrder = {
				id: `ord_test_${Date.now()}`,
				needId: `n_test_${Date.now()}`,
				title: randomItem(),
				description: '测试订单描述',
				reward: randomReward(),
				location: randomLoc(),
				latitude: this.userLatitude + (Math.random() - 0.5) * 0.02,
				longitude: this.userLongitude + (Math.random() - 0.5) * 0.02,
				publisher: {
					id: `u_test_${Date.now()}`,
					nickname: randomNick(),
					reputation: Math.floor(Math.random() * 20) + 80,
					completedOrders: Math.floor(Math.random() * 10)
				},
				helper: this.userStore.currentUser,
				status: 'accepted',
				createdAt: Date.now(),
				acceptedAt: Date.now()
			}

			this.orderStore.addOrder(testOrder)
			uni.showToast({ title: '已生成测试订单', icon: 'success' })
		},
		onRefresh() {
			this.refreshing = true
			if (this.orderStore.loadOrders) {
				this.orderStore.loadOrders()
			}
			if (this.needStore.loadNeeds) {
				this.needStore.loadNeeds()
			}
			setTimeout(() => {
				this.refreshing = false
				uni.showToast({ title: '刷新成功', icon: 'success' })
			}, 500)
		},
		showCancelDialog(item) {
			if (item.status !== 'accepted' && item.status !== 'pending_confirm') return
			this.confirmTitle = '取消订单'
			this.confirmContent = `确定要取消"${item.title}"吗？`
			this.confirmConfirmText = '确定'
			this.confirmCancelText = '取消'
			this.onConfirm = () => {
				this.cancelOrder(item)
			}
			this.confirmVisible = true
		},
		cancelOrder(item) {
			const needId = item.needId || item.id
			let result

			if (item.needId) {
				result = this.needStore.cancelNeed(item.needId)
			} else {
				result = this.orderStore.cancelOrder(item.id)
			}

			if (result.success) {
				item.status = 'cancelled'
				item.cancelledAt = Date.now()
				this.sendCancelNotification(item)
				uni.showToast({ title: '已取消订单', icon: 'success' })
			} else {
				uni.showToast({ title: result.message, icon: 'none' })
			}
		},
		sendCancelNotification(item) {
			const isPublisher = item.publisher?.id === this.userStore.currentUser.id
			const targetUser = isPublisher ? item.helper : item.publisher

			if (targetUser && targetUser.id) {
				const notifications = uni.getStorageSync('notifications') || []
				const message = isPublisher ? '发布者已取消订单' : '帮手已取消接单'
				notifications.unshift({
					id: Date.now(),
					type: 'order',
					title: '订单已取消',
					content: message,
					orderId: item.id,
					orderTitle: item.title,
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
		}
	}
}
</script>

<style scoped>
.container {
	min-height: 100vh;
	background: #F9FAFB;
	display: flex;
	flex-direction: column;
}

/* Header */
.header {
	padding: 80rpx 48rpx 32rpx;
	background: #FFFFFF;
	display: flex;
	justify-content: space-between;
	align-items: center;
}

.header-title {
	font-size: 36rpx;
	font-weight: 800;
	color: #1E293B;
	letter-spacing: -1rpx;
	text-align: center;
}

/* Tabs (V5 Style) */
.tabs {
	display: flex;
	justify-content: space-around;
	padding: 20rpx 40rpx 32rpx;
	background: #FFFFFF;
}

.tab {
	position: relative;
	padding: 16rpx 20rpx 12rpx;
	display: flex;
	flex-direction: column;
	align-items: center;
}

.tab-text {
	font-size: 30rpx;
	font-weight: 600;
	color: #6B7280;
	transition: all 0.3s;
}

.tab.active .tab-text {
	color: #10B981;
}

.tab.active::after {
	content: '';
	position: absolute;
	bottom: 0;
	left: 50%;
	transform: translateX(-50%);
	width: 40rpx;
	height: 6rpx;
	background: #10B981;
	border-radius: 3rpx;
}

/* Content */
.content-scroll {
	flex: 1;
	height: 0; /* 必须设置，否则 flex-1 在 scroll-view 不生效 */
}

.order-list {
	padding: 30rpx 40rpx;
}

.order-item {
	background: #FFFFFF;
	border-radius: 48rpx;
	padding: 40rpx;
	margin-bottom: 30rpx;
	box-shadow: 0 8rpx 24rpx rgba(16, 185, 129, 0.05);
	border: 2rpx solid rgba(16, 185, 129, 0.05);
}

.item-main {
	display: flex;
	gap: 30rpx;
	margin-bottom: 30rpx;
}

.item-icon {
	width: 104rpx;
	height: 104rpx;
	background: #ECFDF5;
	border-radius: 36rpx;
	display: flex;
	align-items: center;
	justify-content: center;
}

.icon-text {
	display: flex;
	align-items: center;
	justify-content: center;
}

.item-info {
	flex: 1;
}

.info-top {
	display: flex;
	justify-content: space-between;
	align-items: center;
	margin-bottom: 8rpx;
}

.order-title {
	font-size: 34rpx;
	font-weight: 700;
	color: #111827;
}

.order-price {
	font-size: 32rpx;
	font-weight: 800;
	color: #10B981;
}

.order-meta {
	display: flex;
	align-items: center;
	gap: 16rpx;
	flex-wrap: wrap;
}

.order-desc {
	font-size: 22rpx;
	color: #9CA3AF;
}

.loc-tag {
	display: inline-flex;
	align-items: center;
	gap: 4rpx;
	background: #F3F4F6;
	padding: 2rpx 8rpx;
	border-radius: 8rpx;
}

.loc-icon {
	font-size: 16rpx;
	color: #6B7280;
}

.loc-text {
	font-size: 18rpx;
	color: #6B7280;
	font-weight: 400;
	font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
}

.order-distance {
	font-size: 22rpx;
	color: #10B981;
	font-weight: 600;
}

.dist-tag {
	display: inline-flex;
	align-items: center;
	gap: 4rpx;
	background: #ECFDF5;
	padding: 2rpx 12rpx;
	border-radius: 8rpx;
}

.dist-icon {
	font-size: 16rpx;
	color: #10B981;
}

.dist-text {
	font-size: 18rpx;
	color: #10B981;
	font-weight: 600;
	font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
}

.item-footer {
	display: flex;
	justify-content: space-between;
	align-items: center;
	padding-top: 30rpx;
	border-top: 2rpx solid #F3F4F6;
}

.status-text {
	font-size: 24rpx;
	font-weight: 700;
	color: #9CA3AF;
	text-transform: uppercase;
	letter-spacing: 1rpx;
}

.status-text.accepted {
	color: #10B981;
}

.status-text.pending_confirm {
	color: #F59E0B;
}

.action-btn {
	background: #10B981;
	padding: 8rpx 24rpx;
	border-radius: 16rpx;
}

.btn-text {
	color: #FFFFFF;
	font-size: 22rpx;
	font-weight: 600;
}

.complete-btn {
	background: #F59E0B;
	padding: 8rpx 24rpx;
	border-radius: 16rpx;
	margin-left: 16rpx;
}

.complete-btn-text {
	color: #FFFFFF;
	font-size: 22rpx;
	font-weight: 600;
}

/* Empty State */
.empty-state {
	padding-top: 80rpx;
	display: flex;
	flex-direction: column;
	align-items: center;
}

.empty-bg {
	width: 160rpx;
	height: 160rpx;
	background: #ECFDF5;
	border-radius: 60rpx;
	display: flex;
	align-items: center;
	justify-content: center;
	margin-bottom: 40rpx;
}

.empty-icon {
	display: flex;
	align-items: center;
	justify-content: center;
}

.empty-title {
	font-size: 32rpx;
	font-weight: 700;
	color: #374151;
	margin-bottom: 16rpx;
}

.empty-subtitle {
	font-size: 28rpx;
	color: #9CA3AF;
}

.bottom-space {
	height: 200rpx;
}

.debug-btn {
	margin-top: 60rpx;
	padding: 24rpx 64rpx;
	background: #10B981;
	border-radius: 200rpx;
}

.debug-btn-text {
	color: #FFFFFF;
	font-size: 28rpx;
	font-weight: 600;
}
</style>
