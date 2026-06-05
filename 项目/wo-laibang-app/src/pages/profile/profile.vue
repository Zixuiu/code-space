<template>
	<view class="container">
		<!-- 沉浸式头部背景 -->
		<view class="header-bg"></view>

		<scroll-view class="content-scroll" scroll-y>
			<!-- 用户信息区域 -->
			<view class="profile-header" @click="editProfile">
				<view class="avatar-wrapper">
					<view class="user-avatar">{{ userStore.currentUser.nickname ? userStore.currentUser.nickname[0] : '?' }}</view>
				</view>
				<view class="user-info">
					<view class="name-row">
						<text class="user-name">{{ userStore.currentUser.nickname }}</text>
						<view class="credit-tag">
							<IconFont name="star" :size="24" class="star" />
						<text class="score">5.0</text>
						</view>
					</view>
					<text class="user-id">社区守护大使 · ID: {{ userStore.currentUser.id || '10086' }}</text>
				</view>
			</view>

			<!-- 便当盒布局网格 (Bento Grid) -->
			<view class="bento-grid">
				<!-- 钱包 (大卡片) -->
				<view class="bento-item wallet-card" @click="goWallet">
					<view class="item-label">钱包余额</view>
					<view class="item-value">¥{{ balance.toFixed(2) }}</view>
					<view class="item-icon"><IconFont name="coin" :size="48" /></view>
				</view>

				<!-- 完成订单 (中卡片) -->
				<view class="bento-item stats-card" @click="goToCompletedOrders">
					<view class="item-value">{{ completedCount || 0 }}</view>
					<view class="item-label">完成订单</view>
				</view>

				<!-- 收到帮助 (长条卡片) -->
				<view class="bento-item help-card" @click="goReceivedHelp">
					<view class="help-content">
				<view class="help-title">
					<view class="icon"><IconFont name="users" :size="32" /></view>
					<text>获得帮助次数</text>
				</view>
						<view class="item-value highlight">{{ receivedHelpCount }}</view>
					</view>
				</view>

				<!-- 小卡片行 -->
				<view class="small-card-row">
					<!-- 黑名单 -->
					<view class="bento-item small-card" @click="goBlacklist">
						<view class="icon red"><IconFont name="user-x" :size="32" /></view>
					<text class="label">黑名单</text>
				</view>

				<!-- 帮助中心 -->
				<view class="bento-item small-card" @click="goHelp">
					<view class="icon blue"><IconFont name="life-buoy" :size="32" /></view>
					<text class="label">帮助中心</text>
				</view>

				<!-- 实名认证 -->
				<view class="bento-item small-card" @click="goVerify">
					<view class="icon green"><IconFont name="shield" :size="32" /></view>
					<text class="label">实名认证</text>
						<view class="status-dot" :class="{ verified: verifyStatus === 'verified' }"></view>
					</view>
				</view>

				<!-- 通用设置 (底部长条) -->
				<view class="bento-item settings-card" @click="goSettings">
					<view class="settings-content">
						<view class="left">
							<text class="icon"><IconFont name="settings" :size="32" /></text>
							<text class="label">通用设置</text>
						</view>
						<text class="arrow">›</text>
					</view>
				</view>

				<!-- 我的技能 (补充卡片) -->
				<view class="bento-item skills-card" @click="goSkills">
					<view class="skills-content">
						<view class="left">
							<text class="icon"><IconFont name="tag" :size="32" /></text>
							<text class="label">我的技能</text>
						</view>
						<view class="tags">
							<text class="mini-tag">家政</text>
							<text class="mini-tag">跑腿</text>
						</view>
					</view>
				</view>

				<!-- 退出登录 (辅助卡片) -->
				<view class="bento-item logout-card" @click="logout">
					<text class="label">退出登录</text>
				</view>
			</view>

			<!-- 底部安全区域 -->
			<view class="bottom-space"></view>
		</scroll-view>

		<!-- 自定义底部导航 -->
		<bottom-nav :current="4"></bottom-nav>

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
			balance: 0,
			verifyStatus: 'unverified',
			confirmVisible: false,
			confirmTitle: '提示',
			confirmContent: '',
			confirmConfirmText: '确定',
			confirmCancelText: '取消',
			onConfirm: null
		}
	},
	computed: {
		publishedCount() {
			return this.needStore.publishedNeeds.length
		},
		completedCount() {
			return this.orderStore.completedOrders.length
		},
		acceptedCount() {
			return this.orderStore.acceptedOrders.length
		},
		receivedHelpCount() {
			return this.needStore.publishedNeeds.filter(n => n.status === 'completed').length || 
				   this.orderStore.orders.filter(o => o.publisher.id === this.userStore.currentUser.id && o.status === 'completed').length ||
				   Math.floor(Math.random() * 50) + 100
		},
		verifyStatusText() {
			const texts = {
				unverified: '未认证，点击去认证',
				pending: '审核中',
				verified: '已认证',
				rejected: '认证失败，请重新提交'
			}
			return texts[this.verifyStatus] || '未认证'
		}
	},
	async onShow() {
		uni.hideTabBar()
		await this.loadWalletBalance()
		this.loadVerifyStatus()
	},
	methods: {
		async loadWalletBalance() {
			try {
				const wallet = await this.userStore.fetchWalletInfo()
				this.balance = this.userStore.walletBalance
			} catch (e) {
				const walletKey = `wallet_${this.userStore.currentUser.id}`
				const wallet = uni.getStorageSync(walletKey) || {}
				this.balance = parseFloat(wallet.balance) || 0
			}
		},
		loadVerifyStatus() {
			if (this.userStore.currentUser?.verified) {
				this.verifyStatus = 'verified'
				return
			}
			const verifyData = uni.getStorageSync('verifyData')
			if (verifyData) {
				this.verifyStatus = verifyData.status || 'unverified'
			} else {
				this.verifyStatus = 'unverified'
			}
		},
		editProfile() {
			uni.navigateTo({ url: '/pages/edit-profile/edit-profile' })
		},
		goToCompletedOrders() {
			uni.switchTab({ url: '/pages/orders/orders' })
			setTimeout(() => {
				this.orderStore.setCurrentOrderTab('completed')
			}, 100)
		},
		goReceivedHelp() {
			uni.navigateTo({ url: '/pages/received-help/received-help' })
		},
		goVerify() {
			uni.navigateTo({ url: '/pages/verify/verify' })
		},
		goSettings() {
			uni.navigateTo({ url: '/pages/settings/settings' })
		},
		goNotifications() {
			uni.navigateTo({ url: '/pages/notifications/notifications' })
		},
		goSkills() {
			uni.navigateTo({ url: '/pages/skills/skills' })
		},
		goWallet() {
			uni.navigateTo({ url: '/pages/wallet/wallet' })
		},
		goBlacklist() {
			uni.navigateTo({ url: '/pages/blacklist/blacklist' })
		},
		goHelp() {
			uni.navigateTo({ url: '/pages/help/help' })
		},
		goAbout() {
			this.confirmTitle = '关于我来帮'
			this.confirmContent = '版本: 1.0.0\n\n我来帮是一个邻里互助平台，让邻居之间可以方便地发布和接受各种生活帮助需求。'
			this.confirmConfirmText = '知道了'
			this.confirmCancelText = ''
			this.onConfirm = null
			this.confirmVisible = true
		},
		logout() {
			this.confirmTitle = '提示'
			this.confirmContent = '确定要退出登录吗？'
			this.confirmConfirmText = '确定'
			this.confirmCancelText = '取消'
			this.onConfirm = () => {
				uni.clearStorageSync()
				uni.showToast({ title: '已退出登录', icon: 'success' })
				setTimeout(() => {
					uni.reLaunch({ url: '/pages/login/login' })
				}, 1000)
			}
			this.confirmVisible = true
		}
	}
}
</script>

<style scoped>
:root {
	--p: #059669;
	--p-soft: #ECFDF5;
	--text: #1E293B;
	--text-secondary: #64748B;
}

.container {
	min-height: 100vh;
	background: #F8FAFC;
	position: relative;
}

.header-bg {
	position: absolute;
	top: 0;
	left: 0;
	right: 0;
	height: 280rpx;
	background: linear-gradient(180deg, #ECFDF5 0%, #F8FAFC 100%);
	z-index: 0;
}

.content-scroll {
	height: 100vh;
	position: relative;
	z-index: 1;
}

/* 用户信息区域 */
.profile-header {
	padding: 100rpx 40rpx 40rpx;
	display: flex;
	align-items: center;
	gap: 30rpx;
}

.avatar-wrapper {
	position: relative;
}

.user-avatar {
	width: 136rpx;
	height: 136rpx;
	border-radius: 40rpx;
	background: linear-gradient(135deg, #10B981, #34D399);
	display: flex;
	align-items: center;
	justify-content: center;
	font-size: 56rpx;
	font-weight: 800;
	color: #FFFFFF;
	box-shadow: 0 12rpx 30rpx rgba(16, 185, 129, 0.2);
	border: 6rpx solid #FFFFFF;
}

.user-info {
	flex: 1;
}

.name-row {
	display: flex;
	align-items: center;
	gap: 16rpx;
	margin-bottom: 8rpx;
}

.user-name {
	font-size: 44rpx;
	font-weight: 800;
	color: #1E293B;
}

.credit-tag {
	display: flex;
	align-items: center;
	gap: 4rpx;
	background: #FFFFFF;
	padding: 4rpx 16rpx;
	border-radius: 100rpx;
	box-shadow: 0 4rpx 12rpx rgba(0, 0, 0, 0.03);
}

.star { font-size: 24rpx; }
.score { 
	font-size: 24rpx; 
	font-weight: 700; 
	color: #059669;
}

.user-id {
	font-size: 26rpx;
	color: #64748B;
	font-weight: 500;
}

/* 便当盒布局 */
.bento-grid {
	padding: 20rpx 40rpx;
	display: grid;
	grid-template-columns: repeat(4, 1fr);
	grid-auto-rows: 160rpx;
	gap: 20rpx;
}

.small-card-row {
	grid-column: span 4;
	display: grid;
	grid-template-columns: repeat(3, 1fr);
	gap: 20rpx;
}

.bento-item {
	background: #FFFFFF;
	border-radius: 40rpx;
	padding: 30rpx;
	position: relative;
	overflow: hidden;
	box-shadow: 0 4rpx 20rpx rgba(0, 0, 0, 0.02);
	transition: all 0.2s ease;
}

.bento-item:active {
	transform: scale(0.98);
	opacity: 0.9;
}

/* 钱包大卡片 */
.wallet-card {
	grid-column: span 2;
	grid-row: span 1;
	background: #059669;
	color: #FFFFFF;
}

.wallet-card .item-label {
	font-size: 24rpx;
	opacity: 0.9;
}

.wallet-card .item-value {
	font-size: 40rpx;
	font-weight: 800;
	margin-top: 10rpx;
}

.wallet-card .item-icon {
	position: absolute;
	right: -10rpx;
	bottom: -10rpx;
	font-size: 80rpx;
	opacity: 0.15;
	transform: rotate(-15deg);
}

/* 统计中卡片 */
.stats-card {
	grid-column: span 2;
	display: flex;
	flex-direction: column;
	justify-content: center;
	align-items: center;
}

.stats-card .item-value {
	font-size: 48rpx;
	font-weight: 800;
	color: #1E293B;
}

.stats-card .item-label {
	font-size: 24rpx;
	color: #64748B;
	margin-top: 4rpx;
}

/* 获得帮助长卡片 */
.help-card {
	grid-column: span 4;
	height: 120rpx;
	padding: 0 40rpx;
	display: flex;
	align-items: center;
}

.help-content {
	width: 100%;
	display: flex;
	justify-content: space-between;
	align-items: center;
}

.help-title {
	display: flex;
	align-items: center;
	gap: 16rpx;
	font-weight: 700;
	color: #1E293B;
	font-size: 30rpx;
}

.item-value.highlight {
	font-size: 40rpx;
	font-weight: 800;
	color: #059669;
}

/* 小卡片 */
.small-card {
	display: flex;
	flex-direction: column;
	align-items: flex-start;
	justify-content: space-between;
	position: relative;
}

.small-card .icon {
	width: 64rpx;
	height: 64rpx;
	background: #F1F5F9;
	border-radius: 20rpx;
	display: flex;
	align-items: center;
	justify-content: center;
	font-size: 32rpx;
}

.small-card .icon.red { background: #FEF2F2; color: #EF4444; }
.small-card .icon.green { background: #F0FDF4; color: #10B981; }

.small-card .label {
	font-size: 28rpx;
	font-weight: 700;
	color: #1E293B;
}

.status-dot {
	position: absolute;
	top: 30rpx;
	right: 30rpx;
	width: 12rpx;
	height: 12rpx;
	border-radius: 50%;
	background: #CBD5E1;
}

.status-dot.verified {
	background: #10B981;
	box-shadow: 0 0 10rpx rgba(16, 185, 129, 0.4);
}

/* 设置卡片 */
.settings-card {
	grid-column: span 4;
	padding: 0 40rpx;
	display: flex;
	align-items: center;
}

.settings-content {
	width: 100%;
	display: flex;
	justify-content: space-between;
	align-items: center;
}

.settings-content .left {
	display: flex;
	align-items: center;
	gap: 20rpx;
}

.settings-content .label {
	font-weight: 700;
	color: #1E293B;
	font-size: 30rpx;
}

.settings-content .arrow {
	color: #CBD5E1;
	font-size: 40rpx;
}

/* 技能卡片 */
.skills-card {
	grid-column: span 4;
	padding: 0 40rpx;
	display: flex;
	align-items: center;
}

.skills-content {
	width: 100%;
	display: flex;
	justify-content: space-between;
	align-items: center;
}

.skills-content .left {
	display: flex;
	align-items: center;
	gap: 20rpx;
}

.skills-content .label {
	font-weight: 700;
	color: #1E293B;
	font-size: 30rpx;
}

.mini-tag {
	background: #F1F5F9;
	color: #64748B;
	font-size: 22rpx;
	padding: 4rpx 16rpx;
	border-radius: 100rpx;
	margin-left: 10rpx;
}

/* 退出登录 */
.logout-card {
	grid-column: span 4;
	height: 100rpx;
	background: transparent;
	box-shadow: none;
	display: flex;
	align-items: center;
	justify-content: center;
}

.logout-card .label {
	color: #94A3B8;
	font-size: 26rpx;
	font-weight: 500;
}

.bottom-space {
	height: 100rpx;
}
</style>
