<script>
import { useUserStore } from '@/store/user'
import apiService from '@/utils/api'
import websocketService from '@/utils/websocket'
import { setupRouterGuard } from '@/utils/router-guard'
import { storage, StorageKeys } from '@/utils/storage'
import badgeService from '@/utils/badge-service'
import messageService from '@/utils/message-service'

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
		this.checkPrivacyAgreement()
		this.checkGuidePage()
		setupRouterGuard()
		this.initServices()
		this.setupBadgeListener()
	},
	onShow: function() {
		console.log('App Show')
		this.checkShareSource()
		badgeService.updateTabBarBadge()
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
			const isLoggedIn = storage.getBoolean(StorageKeys.IS_LOGGED_IN)
			if (isLoggedIn) {
				apiService.initWebSocket()
				messageService.bindWebSocketListeners()
			}
		},
		pauseServices() {
			apiService.disconnect()
		},
		checkGuidePage() {
			const hasSeenGuide = storage.getBoolean(StorageKeys.HAS_SEEN_GUIDE)
			if (!hasSeenGuide) {
				uni.reLaunch({ url: '/pages/guide/guide' })
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
				storage.set(StorageKeys.CURRENT_SHARE_SOURCE, shareInfo)
				console.log('记录分享来源:', shareInfo)
			}
		},
		getShareSource() {
			return storage.getObject(StorageKeys.CURRENT_SHARE_SOURCE, null)
		},
		clearShareSource() {
			storage.remove(StorageKeys.CURRENT_SHARE_SOURCE)
		},
		checkPrivacyAgreement() {
			const hasAgreed = storage.getBoolean(StorageKeys.HAS_AGREED_PRIVACY)
			if (!hasAgreed) {
				this.privacyModalVisible = true
			}
		},
		confirmPrivacy() {
			storage.set(StorageKeys.HAS_AGREED_PRIVACY, true)
			this.privacyModalVisible = false
		},
		viewPrivacyPolicy() {
			uni.navigateTo({
				url: '/pages/privacy-policy/privacy-policy'
			})
		},
		setupBadgeListener() {
			badgeService.setupListeners()
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
</style>