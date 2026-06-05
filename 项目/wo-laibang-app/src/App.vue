<script>
import { useUserStore } from '@/store/user'
import apiService from '@/utils/api'
import websocketService from '@/utils/websocket'

const NEED_LOGIN_PAGES = [
  '/pages/orders/orders',
  '/pages/wallet/wallet',
  '/pages/messages/messages',
  '/pages/recharge/recharge',
  '/pages/withdraw/withdraw',
  '/pages/transfer/transfer',
  '/pages/profile/profile',
  '/pages/edit-profile/edit-profile',
  '/pages/settings/settings',
  '/pages/verify/verify',
  '/pages/order-detail/order-detail',
  '/pages/accept-order/accept-order',
  '/pages/rate/rate',
  '/pages/skills/skills',
  '/pages/blacklist/blacklist',
  '/pages/received-help/received-help',
  '/pages/rating-history/rating-history',
  '/pages/notification-settings/notification-settings',
  '/pages/feedback/feedback',
  '/pages/transaction/transaction',
  '/pages/bind-alipay/bind-alipay',
  '/pages/bind-bank/bind-bank',
  '/pages/complaint/complaint',
  '/pages/complaint-list/complaint-list',
  '/pages/complaint-detail/complaint-detail'
]

export default {
	data() {
		return {
			privacyModalVisible: false
		}
	},
	onLaunch: function() {
		console.log('App Launch')
		uni.hideTabBar()
		this.checkShareSource()
		this.initNavigateMethods()
		this.checkPrivacyAgreement()
		this.checkGuidePage()
		this.setupRouterGuard()
		this.initServices()
		this.setupMessageBadgeListener()
	},
	onShow: function() {
		console.log('App Show')
		this.checkShareSource()
		this.updateTabBarBadge()
		this.resumeServices()
	},
	onHide: function() {
		console.log('App Hide')
		this.pauseServices()
	},
	methods: {
		initServices() {
			apiService.init()
		},
		resumeServices() {
			const isLoggedIn = uni.getStorageSync('isLoggedIn')
			if (isLoggedIn) {
				apiService.initWebSocket()
				this.initWebSocketListeners()
			}
		},
		initWebSocketListeners() {
			websocketService.on('chat_message', (payload) => {
				this.incrementUnreadForIncomingMessage(payload)
				this.updateTabBarBadge()
			})
			websocketService.on('notification', () => {
				this.updateTabBarBadge()
			})
		},
		incrementUnreadForIncomingMessage(payload) {
			if (!payload || !payload.fromUserId) return
			const conversations = uni.getStorageSync('conversations') || []
			const convIndex = conversations.findIndex(c => c.userId == payload.fromUserId)
			if (convIndex >= 0) {
				conversations[convIndex].unread = (conversations[convIndex].unread || 0) + 1
				conversations[convIndex].lastMessage = payload.content
				conversations[convIndex].lastTime = payload.timestamp || Date.now()
			} else {
				conversations.unshift({
					id: `conv_${payload.fromUserId}`,
					userId: payload.fromUserId,
					nickname: payload.fromNickname || '未知用户',
					lastMessage: payload.content,
					lastTime: payload.timestamp || Date.now(),
					unread: 1,
					online: true
				})
			}
			uni.setStorageSync('conversations', conversations)
		},
		pauseServices() {
			apiService.disconnect()
		},
		checkGuidePage() {
			const hasSeenGuide = uni.getStorageSync('hasSeenGuide')
			if (!hasSeenGuide) {
				uni.reLaunch({ url: '/pages/guide/guide' })
			}
		},
		setupRouterGuard() {
			const originalNavigateTo = uni.navigateTo
			const originalSwitchTab = uni.switchTab
			const originalRedirectTo = uni.redirectTo
			const originalReLaunch = uni.reLaunch

			uni.navigateTo = (options) => {
				if (this.shouldCheckLogin(options.url)) {
					uni.setStorageSync('redirectAfterLogin', this.extractPath(options.url))
					uni.showToast({ title: '请先登录', icon: 'none' })
					setTimeout(() => {
						originalNavigateTo.call(uni, { url: '/pages/login/login' })
					}, 500)
					return
				}
				return originalNavigateTo.call(uni, options)
			}

			uni.switchTab = (options) => {
				if (this.shouldCheckLogin(options.url)) {
					uni.setStorageSync('redirectAfterLogin', this.extractPath(options.url))
					uni.showToast({ title: '请先登录', icon: 'none' })
					setTimeout(() => {
						uni.reLaunch({ url: '/pages/login/login' })
					}, 500)
					return
				}
				return originalSwitchTab.call(uni, options)
			}

			uni.redirectTo = (options) => {
				if (this.shouldCheckLogin(options.url)) {
					uni.setStorageSync('redirectAfterLogin', this.extractPath(options.url))
					uni.showToast({ title: '请先登录', icon: 'none' })
					setTimeout(() => {
						originalRedirectTo.call(uni, { url: '/pages/login/login' })
					}, 500)
					return
				}
				return originalRedirectTo.call(uni, options)
			}

			uni.reLaunch = (options) => {
				if (this.shouldCheckLogin(options.url)) {
					uni.setStorageSync('redirectAfterLogin', this.extractPath(options.url))
					uni.showToast({ title: '请先登录', icon: 'none' })
					setTimeout(() => {
						originalReLaunch.call(uni, { url: '/pages/login/login' })
					}, 500)
					return
				}
				return originalReLaunch.call(uni, options)
			}
		},

		setupMessageBadgeListener() {
			uni.$on('updateMessageBadge', () => {
				this.updateTabBarBadge()
			})
			uni.$on('clearMessageBadge', () => {
				this.updateTabBarBadge()
			})
		},

		shouldCheckLogin(url) {
			const path = this.extractPath(url)
			const isNeedLogin = NEED_LOGIN_PAGES.some(page => path.startsWith(page))
			if (!isNeedLogin) return false

			const isLoggedIn = uni.getStorageSync('isLoggedIn') || false
			const token = uni.getStorageSync('token')
			return !isLoggedIn || !token
		},

		extractPath(url) {
			if (url.startsWith('/')) {
				return url.split('?')[0]
			}
			return '/' + url.split('?')[0]
		},

		updateTabBarBadge() {
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

			uni.setStorageSync('totalUnreadCount', totalUnread)
			uni.$emit('updateBadge')
		},
		initNavigateMethods() {
			uni.oldNavigateTo = uni.navigateTo
			uni.navigateTo = (options) => {
				options.animationType = 'none'
				return uni.oldNavigateTo(options)
			}
			uni.oldRedirectTo = uni.redirectTo
			uni.redirectTo = (options) => {
				options.animationType = 'none'
				return uni.oldRedirectTo(options)
			}
			uni.oldreLaunch = uni.reLaunch
			uni.reLaunch = (options) => {
				options.animationType = 'none'
				return uni.oldreLaunch(options)
			}
			uni.oldswitchTab = uni.switchTab
			uni.switchTab = (options) => {
				options.animationType = 'none'
				return uni.oldswitchTab(options)
			}
		},
		checkShareSource() {
			// #ifdef APP-PLUS
			const launchOptions = plus.runtime.launchScene
			console.log('启动参数:', launchOptions)
			// #endif
			// 检查启动时是否有分享来源（通过页面参数传递）
			const currentPage = getCurrentPages()
			if (currentPage.length > 0) {
				const current = currentPage[currentPage.length - 1]
				const options = current.options || current.$cm?.options
				if (options && options.from) {
					this.setShareSource(options.from, options.needId)
				}
			}
		},
		setShareSource(fromUserId, needId) {
			if (fromUserId) {
				const shareInfo = {
					fromUserId,
					needId: needId || null,
					timestamp: Date.now()
				}
				uni.setStorageSync('currentShareSource', shareInfo)
				console.log('记录分享来源:', shareInfo)
			}
		},
		getShareSource() {
			return uni.getStorageSync('currentShareSource') || null
		},
		clearShareSource() {
			uni.removeStorageSync('currentShareSource')
		},
		checkPrivacyAgreement() {
			const hasAgreed = uni.getStorageSync('hasAgreedPrivacyPolicy')
			if (!hasAgreed) {
				this.privacyModalVisible = true
			}
		},
		confirmPrivacy() {
			uni.setStorageSync('hasAgreedPrivacyPolicy', true)
			this.privacyModalVisible = false
		},
		viewPrivacyPolicy() {
			uni.navigateTo({
				url: '/pages/privacy-policy/privacy-policy'
			})
		},
		preventClose() {
		}
	}
}
</script>

<template>
	<view id="app">
		<!-- 隐私协议弹窗 -->
		<view v-if="privacyModalVisible" class="privacy-overlay" @click.stop="preventClose">
			<view class="privacy-modal" @click.stop>
				<view class="privacy-header">
					<text class="privacy-title">隐私保护指引</text>
				</view>
				<scroll-view class="privacy-content" scroll-y>
					<text class="privacy-desc">感谢您使用「我来帮」！\n\n在您使用我们的服务前，请您仔细阅读并同意以下内容：</text>
					<view class="privacy-item">
						<text class="privacy-item-title">📋 信息收集</text>
						<text class="privacy-item-text">我们将收集您的位置信息、设备信息等，以为您提供更好的邻里互助服务。</text>
					</view>
					<view class="privacy-item">
						<text class="privacy-item-title">🔒 信息保护</text>
						<text class="privacy-item-text">我们承诺保护您的个人信息安全，不对外泄露您的隐私。</text>
					</view>
					<view class="privacy-item">
						<text class="privacy-item-title">📖 详细条款</text>
						<text class="privacy-item-text">阅读完整的隐私政策条款请点击下方链接。</text>
					</view>
					<text class="privacy-tip">请您务必审慎阅读并充分理解上述内容，如有任何疑问可联系我们。</text>
				</scroll-view>
				<view class="privacy-footer">
					<button class="privacy-btn" @click="confirmPrivacy">同意并继续</button>
					<view class="privacy-link" @click="viewPrivacyPolicy">
						<text class="privacy-link-text">查看完整隐私政策 ›</text>
					</view>
				</view>
			</view>
		</view>
	</view>
</template>

<style>
	/*每个页面公共css */
	@import "@/static/css/common.css";

	.privacy-overlay {
		position: fixed;
		top: 0;
		left: 0;
		right: 0;
		bottom: 0;
		background: rgba(0, 0, 0, 0.5);
		z-index: 9999;
		display: flex;
		align-items: center;
		justify-content: center;
	}

	.privacy-modal {
		width: 640rpx;
		max-height: 80vh;
		background: #F8FAFC;
		border-radius: 24rpx;
		overflow: hidden;
		display: flex;
		flex-direction: column;
		box-shadow: 0 20rpx 60rpx rgba(0, 0, 0, 0.15);
	}

	.privacy-header {
		padding: 40rpx 40rpx 20rpx;
		text-align: center;
	}

	.privacy-title {
		font-size: 36rpx;
		font-weight: 800;
		color: #1E293B;
	}

	.privacy-content {
		flex: 1;
		padding: 0 40rpx;
		max-height: 50vh;
	}

	.privacy-desc {
		font-size: 28rpx;
		color: #64748B;
		line-height: 1.6;
		display: block;
		margin-bottom: 30rpx;
	}

	.privacy-item {
		background: #ECFDF5;
		border-radius: 16rpx;
		padding: 24rpx;
		margin-bottom: 20rpx;
	}

	.privacy-item-title {
		font-size: 30rpx;
		font-weight: 700;
		color: #059669;
		display: block;
		margin-bottom: 12rpx;
	}

	.privacy-item-text {
		font-size: 26rpx;
		color: #64748B;
		line-height: 1.5;
		display: block;
	}

	.privacy-tip {
		font-size: 24rpx;
		color: #94A3B8;
		line-height: 1.6;
		display: block;
		margin-top: 20rpx;
		margin-bottom: 30rpx;
	}

	.privacy-footer {
		padding: 20rpx 40rpx 40rpx;
	}

	.privacy-link {
		text-align: center;
		margin-bottom: 20rpx;
	}

	.privacy-link-text {
		font-size: 28rpx;
		color: #10B981;
		text-decoration: underline;
	}

	.privacy-btn {
		width: 100%;
		height: 96rpx;
		background: linear-gradient(135deg, #10B981, #059669);
		color: #FFFFFF;
		font-size: 32rpx;
		font-weight: 800;
		border-radius: 48rpx;
		border: none;
		display: flex;
		align-items: center;
		justify-content: center;
		box-shadow: 0 8rpx 20rpx rgba(16, 185, 129, 0.25);
	}

	.privacy-btn::after {
		border: none;
	}

	.privacy-btn::after {
		border: none;
	}
</style>