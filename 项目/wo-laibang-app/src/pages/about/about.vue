<template>
	<view class="about-container">
		<view class="header">
			<text class="header-title">关于我们</text>
			<view class="header-right"></view>
		</view>

		<scroll-view class="content-scroll" scroll-y>
			<view class="app-info-section">
				<view class="app-logo">
					<view class="logo-icon">🤝</view>
				</view>
				<text class="app-name">我来帮</text>
				<text class="app-slogan">邻里互助，温暖每一天</text>
				<text class="app-version">V{{ version }}</text>
			</view>

			<view class="card-section">
				<view class="card">
					<view class="card-item" @click="goPrivacy">
						<view class="card-left">
							<text class="card-icon">🔒</text>
							<text class="card-text">隐私政策</text>
						</view>
						<text class="card-arrow">›</text>
					</view>
					<view class="card-divider"></view>
					<view class="card-item" @click="goTerms">
						<view class="card-left">
							<text class="card-icon">📄</text>
							<text class="card-text">用户协议</text>
						</view>
						<text class="card-arrow">›</text>
					</view>
					<view class="card-divider"></view>
					<view class="card-item" @click="checkUpdate">
						<view class="card-left">
							<text class="card-icon">🔄</text>
							<text class="card-text">检查更新</text>
						</view>
						<text class="card-arrow">›</text>
					</view>
				</view>
			</view>

			<view class="card-section">
				<view class="card">
					<view class="card-item" @click="rateApp">
						<view class="card-left">
							<text class="card-icon">⭐</text>
							<text class="card-text">给我们评分</text>
						</view>
						<text class="card-arrow">›</text>
					</view>
					<view class="card-divider"></view>
					<view class="card-item" @click="shareApp">
						<view class="card-left">
							<text class="card-icon">📤</text>
							<text class="card-text">分享给好友</text>
						</view>
						<text class="card-arrow">›</text>
					</view>
				</view>
			</view>

			<view class="card-section">
				<view class="card">
					<view class="card-item">
						<view class="card-left">
							<text class="card-icon">📧</text>
							<text class="card-text">联系邮箱</text>
						</view>
						<text class="card-value">contact@wolaibang.com</text>
					</view>
					<view class="card-divider"></view>
					<view class="card-item">
						<view class="card-left">
							<text class="card-icon">📞</text>
							<text class="card-text">客服电话</text>
						</view>
						<text class="card-value">400-888-8888</text>
					</view>
					<view class="card-divider"></view>
					<view class="card-item">
						<view class="card-left">
							<text class="card-icon">🌐</text>
							<text class="card-text">官方网站</text>
						</view>
						<text class="card-value">www.wolaibang.com</text>
					</view>
				</view>
			</view>

			<view class="copyright-section">
				<text class="copyright-text">© 2024 我来帮 All Rights Reserved</text>
				<text class="icp-text">京ICP备12345678号-1</text>
			</view>

			<view class="bottom-safe"></view>
		</scroll-view>
	</view>
</template>

<script>
export default {
	data() {
		return {
			version: '1.0.0'
		}
	},
	onLoad() {
		this.getVersion()
	},
	methods: {
		getVersion() {
			const manifest = uni.getStorageSync('__uniapp_system_info') || {}
			if (manifest.uniCompileVersion) {
				this.version = manifest.uniCompileVersion
			}
			plus.runtime.getProperty(plus.runtime.appid, (widgetInfo) => {
				this.version = widgetInfo.version
			})
		},
		goPrivacy() {
			uni.navigateTo({
				url: '/pages/privacy-policy/privacy-policy'
			})
		},
		goTerms() {
			uni.navigateTo({
				url: '/pages/terms-of-service/terms-of-service'
			})
		},
		checkUpdate() {
			uni.showToast({
				title: '已是最新版本',
				icon: 'success'
			})
		},
		rateApp() {
			uni.showToast({
				title: '感谢您的支持',
				icon: 'none'
			})
		},
		shareApp() {
			uni.share({
				provider: 'weixin',
				scene: 'WXSceneSession',
				type: 0,
				href: 'https://wolaibang.com/download',
				title: '我来帮 - 邻里互助平台',
				summary: '邻里互助，温暖每一天。快来加入我们吧！',
				success: () => {
					uni.showToast({ title: '分享成功', icon: 'success' })
				},
				fail: () => {
					uni.showToast({ title: '分享失败', icon: 'none' })
				}
			})
		}
	}
}
</script>

<style scoped>
.about-container {
	min-height: 100vh;
	background: #F8FAFC;
}

.header {
	display: flex;
	align-items: center;
	justify-content: space-between;
	padding: 80rpx 48rpx 40rpx;
	background: #FFFFFF;
	position: relative;
}

.header-title {
	flex: 1;
	font-size: 36rpx;
	font-weight: 800;
	color: #1E293B;
	text-align: center;
}

.header-right {
	width: 88rpx;
}

.content-scroll {
	height: calc(100vh - 144rpx);
}

.app-info-section {
	text-align: center;
	padding: 80rpx 48rpx 64rpx;
	background: #FFFFFF;
	margin-bottom: 32rpx;
}

.app-logo {
	width: 200rpx;
	height: 200rpx;
	background: linear-gradient(135deg, #10B981, #34D399);
	border-radius: 48rpx;
	display: flex;
	align-items: center;
	justify-content: center;
	margin: 0 auto 40rpx;
	box-shadow: 0 24rpx 64rpx rgba(16, 185, 129, 0.25);
}

.logo-icon {
	font-size: 96rpx;
}

.app-name {
	font-size: 56rpx;
	font-weight: 800;
	color: #1E293B;
	display: block;
	margin-bottom: 16rpx;
}

.app-slogan {
	font-size: 28rpx;
	color: #64748B;
	display: block;
	margin-bottom: 24rpx;
}

.app-version {
	font-size: 26rpx;
	color: #94A3B8;
	background: #F1F5F9;
	padding: 12rpx 32rpx;
	border-radius: 40rpx;
	display: inline-block;
}

.card-section {
	padding: 0 48rpx;
	margin-bottom: 32rpx;
}

.card {
	background: #FFFFFF;
	border-radius: 40rpx;
	overflow: hidden;
	box-shadow: 0 4rpx 24rpx rgba(0, 0, 0, 0.04);
}

.card-item {
	display: flex;
	align-items: center;
	justify-content: space-between;
	padding: 36rpx 40rpx;
}

.card-left {
	display: flex;
	align-items: center;
}

.card-icon {
	font-size: 40rpx;
	margin-right: 28rpx;
}

.card-text {
	font-size: 30rpx;
	font-weight: 600;
	color: #1E293B;
}

.card-value {
	font-size: 26rpx;
	color: #94A3B8;
}

.card-arrow {
	font-size: 36rpx;
	color: #CBD5E1;
}

.card-divider {
	height: 2rpx;
	background: #F1F5F9;
	margin: 0 40rpx;
}

.copyright-section {
	text-align: center;
	padding: 64rpx 48rpx;
}

.copyright-text {
	font-size: 24rpx;
	color: #94A3B8;
	display: block;
	margin-bottom: 12rpx;
}

.icp-text {
	font-size: 22rpx;
	color: #CBD5E1;
}

.bottom-safe {
	height: 80rpx;
}
</style>
