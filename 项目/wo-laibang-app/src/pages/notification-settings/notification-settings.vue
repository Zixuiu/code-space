<template>
	<view class="container">
		<view class="header">
			<text class="header-title">通知设置</text>
			<view class="header-right"></view>
		</view>

		<scroll-view class="content-scroll" scroll-y>
			<view class="main-toggle-card">
				<view class="main-toggle-left">
					<IconFont name="bell" :size="24" />
					<view class="main-toggle-info">
						<text class="main-toggle-title">接收通知</text>
						<text class="main-toggle-desc">关闭后将不再收到任何推送</text>
					</view>
				</view>
				<view
					class="toggle"
					:class="{ active: settings.enabled }"
					@click="toggleMain"
				></view>
			</view>

			<view class="settings-group" :class="{ disabled: !settings.enabled }">
				<view class="group-title">订单通知</view>
				<view class="settings-card">
					<view class="settings-item">
						<view class="item-content">
							<view class="item-icon order-icon">
								<IconFont name="shopping-bag" :size="20" />
							</view>
							<view class="item-info">
								<text class="item-title">订单状态变更</text>
								<text class="item-desc">订单被接单、完成、取消等状态变化</text>
							</view>
						</view>
						<view
							class="toggle"
							:class="{ active: settings.orderStatus }"
							@click="toggleSetting('orderStatus')"
						></view>
					</view>
					<view class="settings-item">
						<view class="item-content">
							<view class="item-icon msg-icon">
								<IconFont name="message" :size="20" />
							</view>
							<view class="item-info">
								<text class="item-title">新消息提醒</text>
								<text class="item-desc">收到帮助者或请求者的消息</text>
							</view>
						</view>
						<view
							class="toggle"
							:class="{ active: settings.newMessage }"
							@click="toggleSetting('newMessage')"
						></view>
					</view>
					<view class="settings-item">
						<view class="item-content">
							<view class="item-icon payment-icon">
								<IconFont name="wallet" :size="20" />
							</view>
							<view class="item-info">
								<text class="item-title">收款通知</text>
								<text class="item-desc">账户收到款项时通知</text>
							</view>
						</view>
						<view
							class="toggle"
							:class="{ active: settings.payment }"
							@click="toggleSetting('payment')"
						></view>
					</view>
				</view>
			</view>

			<view class="settings-group" :class="{ disabled: !settings.enabled }">
				<view class="group-title">系统通知</view>
				<view class="settings-card">
					<view class="settings-item">
						<view class="item-content">
							<view class="item-icon promo-icon">
								<IconFont name="megaphone" :size="20" />
							</view>
							<view class="item-info">
								<text class="item-title">活动优惠</text>
								<text class="item-desc">平台活动、优惠券等促销信息</text>
							</view>
						</view>
						<view
							class="toggle"
							:class="{ active: settings.promotion }"
							@click="toggleSetting('promotion')"
						></view>
					</view>
					<view class="settings-item">
						<view class="item-content">
							<view class="item-icon update-icon">
								<IconFont name="refresh-cw" :size="20" />
							</view>
							<view class="item-info">
								<text class="item-title">版本更新</text>
								<text class="item-desc">新版本发布时的提醒</text>
							</view>
						</view>
						<view
							class="toggle"
							:class="{ active: settings.update }"
							@click="toggleSetting('update')"
						></view>
					</view>
					<view class="settings-item">
						<view class="item-content">
							<view class="item-icon system-icon">
								<IconFont name="info" :size="20" />
							</view>
							<view class="item-info">
								<text class="item-title">系统公告</text>
								<text class="item-desc">重要的平台通知和公告</text>
							</view>
						</view>
						<view
							class="toggle"
							:class="{ active: settings.system }"
							@click="toggleSetting('system')"
						></view>
					</view>
				</view>
			</view>

			<view class="settings-group" :class="{ disabled: !settings.enabled }">
				<view class="group-title">提醒方式</view>
				<view class="settings-card">
					<view class="settings-item">
						<view class="item-content">
							<view class="item-icon sound-icon">
								<IconFont name="volume" :size="20" />
							</view>
							<view class="item-info">
								<text class="item-title">声音</text>
								<text class="item-desc">收到通知时播放提示音</text>
							</view>
						</view>
						<view
							class="toggle"
							:class="{ active: settings.sound }"
							@click="toggleSetting('sound')"
						></view>
					</view>
					<view class="settings-item">
						<view class="item-content">
							<view class="item-icon vibrate-icon">
								<IconFont name="vibrate" :size="20" />
							</view>
							<view class="item-info">
								<text class="item-title">震动</text>
								<text class="item-desc">收到通知时震动提醒</text>
							</view>
						</view>
						<view
							class="toggle"
							:class="{ active: settings.vibrate }"
							@click="toggleSetting('vibrate')"
						></view>
					</view>
				</view>
			</view>

			<view class="tip-card">
				<IconFont name="shield" :size="20" class="tip-icon" />
				<view class="tip-content">
					<text class="tip-title">隐私保护</text>
					<text class="tip-desc">您可以在手机系统设置中单独管理应用通知权限</text>
				</view>
			</view>

			<view class="bottom-space"></view>
		</scroll-view>
	</view>
</template>

<script>
import IconFont from '@/components/icon-font/icon-font.vue'

export default {
	components: {
		IconFont
	},
	data() {
		return {
			settings: {
				enabled: true,
				orderStatus: true,
				newMessage: true,
				payment: true,
				promotion: false,
				update: true,
				system: true,
				sound: true,
				vibrate: true
			}
		}
	},
	onLoad() {
		this.loadSettings()
	},
	methods: {
		loadSettings() {
			const stored = uni.getStorageSync('notificationSettings')
			if (stored) {
				this.settings = { ...this.settings, ...stored }
			}
		},
		saveSettings() {
			uni.setStorageSync('notificationSettings', this.settings)
		},
		toggleMain() {
			this.settings.enabled = !this.settings.enabled
			this.saveSettings()
			if (this.settings.enabled) {
				uni.showToast({ title: '已开启通知', icon: 'success' })
			} else {
				uni.showToast({ title: '已关闭通知', icon: 'none' })
			}
		},
		toggleSetting(key) {
			if (!this.settings.enabled) return
			this.settings[key] = !this.settings[key]
			this.saveSettings()
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
	display: flex;
	align-items: center;
	padding: 64rpx 24rpx 16rpx;
	background: #FFFFFF;
	gap: 16rpx;
	border-bottom: 1rpx solid #F1F5F9;
}

.header-title {
	flex: 1;
	font-size: 36rpx;
	font-weight: 800;
	color: #1E293B;
	text-align: center;
}

.header-right {
	width: 80rpx;
}

.content-scroll {
	height: calc(100vh - 178rpx);
	padding: 24rpx;
}

.main-toggle-card {
	background: #FFFFFF;
	border-radius: 20rpx;
	padding: 28rpx 24rpx;
	display: flex;
	align-items: center;
	justify-content: space-between;
	margin-bottom: 24rpx;
	box-shadow: 0 2rpx 12rpx rgba(0, 0, 0, 0.04);
}

.main-toggle-left {
	display: flex;
	align-items: center;
	gap: 16rpx;
}

.main-toggle-left > IconFont {
	color: #10B981;
}

.main-toggle-info {
	display: flex;
	flex-direction: column;
}

.main-toggle-title {
	font-size: 30rpx;
	font-weight: 700;
	color: #1E293B;
	margin-bottom: 6rpx;
}

.main-toggle-desc {
	font-size: 24rpx;
	color: #94A3B8;
}

.toggle {
	width: 96rpx;
	height: 56rpx;
	background: #E2E8F0;
	border-radius: 28rpx;
	position: relative;
	cursor: pointer;
	transition: all 0.3s;
}

.toggle.active {
	background: #10B981;
}

.toggle::after {
	content: '';
	position: absolute;
	width: 44rpx;
	height: 44rpx;
	background: #FFFFFF;
	border-radius: 50%;
	top: 6rpx;
	left: 6rpx;
	transition: all 0.3s;
	box-shadow: 0 2rpx 4rpx rgba(0, 0, 0, 0.1);
}

.toggle.active::after {
	left: 46rpx;
}

.settings-group {
	margin-bottom: 24rpx;
	transition: opacity 0.3s;
}

.settings-group.disabled {
	opacity: 0.5;
	pointer-events: none;
}

.group-title {
	font-size: 24rpx;
	font-weight: 700;
	color: #64748B;
	text-transform: uppercase;
	letter-spacing: 2rpx;
	margin-bottom: 12rpx;
	padding-left: 4rpx;
}

.settings-card {
	background: #FFFFFF;
	border-radius: 20rpx;
	overflow: hidden;
	box-shadow: 0 2rpx 12rpx rgba(0, 0, 0, 0.04);
}

.settings-item {
	display: flex;
	align-items: center;
	justify-content: space-between;
	padding: 24rpx 20rpx;
	border-bottom: 1rpx solid #F1F5F9;
}

.settings-item:last-child {
	border-bottom: none;
}

.item-content {
	display: flex;
	align-items: center;
	flex: 1;
}

.item-icon {
	width: 72rpx;
	height: 72rpx;
	border-radius: 16rpx;
	display: flex;
	align-items: center;
	justify-content: center;
	margin-right: 16rpx;
}

.order-icon {
	background: #F0FDF4;
	color: #10B981;
}

.msg-icon {
	background: #EFF6FF;
	color: #3B82F6;
}

.payment-icon {
	background: #FEF3C7;
	color: #F59E0B;
}

.promo-icon {
	background: #FDF2F8;
	color: #EC4899;
}

.update-icon {
	background: #ECFDF5;
	color: #10B981;
}

.system-icon {
	background: #F5F3FF;
	color: #8B5CF6;
}

.sound-icon {
	background: #FEF2F2;
	color: #EF4444;
}

.vibrate-icon {
	background: #ECFEFF;
	color: #06B6D4;
}

.item-info {
	display: flex;
	flex-direction: column;
}

.item-title {
	font-size: 28rpx;
	font-weight: 700;
	color: #1E293B;
	margin-bottom: 4rpx;
}

.item-desc {
	font-size: 22rpx;
	color: #94A3B8;
}

.tip-card {
	background: #F0FDF4;
	border-radius: 16rpx;
	padding: 20rpx;
	display: flex;
	gap: 12rpx;
	margin-top: 8rpx;
}

.tip-icon {
	color: #10B981;
	flex-shrink: 0;
}

.tip-content {
	display: flex;
	flex-direction: column;
}

.tip-title {
	font-size: 26rpx;
	font-weight: 700;
	color: #059669;
	margin-bottom: 4rpx;
}

.tip-desc {
	font-size: 24rpx;
	color: #64748B;
	line-height: 1.5;
}

.bottom-space {
	height: 40rpx;
}
</style>