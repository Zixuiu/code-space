<template>
	<view class="settings-container">
		<view class="header">
			<text class="header-title">通用设置</text>
			<view class="header-right"></view>
		</view>

		<scroll-view class="content-scroll" scroll-y>
			<view class="settings-section">
				<view class="settings-card">
					<view class="setting-item" @click="goEditProfile">
						<IconFont name="user" :size="32" class="setting-icon" />
						<text class="setting-name">编辑资料</text>
						<IconFont name="chevron-right" :size="24" class="setting-arrow" />
					</view>
					<view class="setting-item" @click="goVerify">
						<IconFont name="circle-check" :size="32" class="setting-icon" />
						<text class="setting-name">实名认证</text>
						<text class="setting-tag success">已认证</text>
					</view>
					<view class="setting-item" @click="goPrivacy">
						<IconFont name="shield" :size="32" class="setting-icon" />
						<text class="setting-name">隐私安全</text>
						<IconFont name="chevron-right" :size="24" class="setting-arrow" />
					</view>
				</view>

				<view class="settings-card">
					<view class="setting-item" @click="goNotification">
						<IconFont name="bell" :size="32" class="setting-icon" />
						<text class="setting-name">消息通知</text>
						<IconFont name="chevron-right" :size="24" class="setting-arrow" />
					</view>
					<view class="setting-item" @click="toggleTheme">
						<IconFont name="moon" :size="32" class="setting-icon" />
						<text class="setting-name">深色模式</text>
						<view class="toggle-switch" :class="{ active: darkMode }"></view>
					</view>
					<view class="setting-item" @click="goLanguage">
						<IconFont name="language" :size="32" class="setting-icon" />
						<text class="setting-name">语言设置</text>
						<text class="setting-value">简体中文</text>
					</view>
				</view>

				<view class="settings-card">
					<view class="setting-item" @click="goHelp">
						<IconFont name="help-center" :size="32" class="setting-icon" />
						<text class="setting-name">帮助中心</text>
						<IconFont name="chevron-right" :size="24" class="setting-arrow" />
					</view>
					<view class="setting-item" @click="goSimulation">
						<IconFont name="users" :size="32" class="setting-icon" />
						<text class="setting-name">模拟用户</text>
						<IconFont name="chevron-right" :size="24" class="setting-arrow" />
					</view>
					<view class="setting-item" @click="goFeedback">
						<IconFont name="feedback" :size="32" class="setting-icon" />
						<text class="setting-name">意见反馈</text>
						<IconFont name="chevron-right" :size="24" class="setting-arrow" />
					</view>
					<view class="setting-item" @click="goAbout">
						<IconFont name="info-circle" :size="32" class="setting-icon" />
						<text class="setting-name">关于我们</text>
						<IconFont name="chevron-right" :size="24" class="setting-arrow" />
					</view>
				</view>

				<view class="settings-card">
					<view class="setting-item" @click="goClearCache">
						<IconFont name="trash" :size="32" class="setting-icon" />
						<text class="setting-name">清除缓存</text>
						<text class="setting-value">12.5 MB</text>
					</view>
					<view class="setting-item" @click="checkUpdate">
						<IconFont name="version-update" :size="32" class="setting-icon" />
						<text class="setting-name">版本更新</text>
						<text class="setting-value">V{{ appVersion }}</text>
					</view>
				</view>
			</view>

			<view class="logout-section">
				<view class="logout-btn" @click="handleLogout">退出登录</view>
			</view>

			<view class="bottom-safe"></view>
		</scroll-view>

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
					<view style="flex:1;height:96rpx;display:flex;align-items:center;justify-content:center;border-right:1rpx solid #F1F5F9;" @click="confirmVisible = false">
						<text style="font-size:30rpx;font-weight:600;color:#64748B;">{{ confirmCancelText }}</text>
					</view>
					<view style="flex:1;height:96rpx;display:flex;align-items:center;justify-content:center;" @click="confirmVisible = false; if(onConfirm) onConfirm()">
						<text style="font-size:30rpx;font-weight:700;color:#10B981;">{{ confirmConfirmText }}</text>
					</view>
				</view>
			</view>
		</view>
	</view>
</template>

<script>
export default {
	data() {
		return {
			darkMode: false,
			confirmVisible: false,
			confirmTitle: '',
			confirmContent: '',
			confirmCancelText: '取消',
			confirmConfirmText: '确认',
			onConfirm: null,
			appVersion: '1.0.0'
		}
	},
	onLoad() {
		this.getAppVersion()
	},
	methods: {
		getAppVersion() {
			try {
				plus.runtime.getProperty(plus.runtime.appid, (widgetInfo) => {
					this.appVersion = widgetInfo.version
				})
			} catch (e) {
				console.log('获取版本失败', e)
			}
		},
		goEditProfile() {
			uni.navigateTo({ url: '/pages/edit-profile/edit-profile' })
		},
		goVerify() {
			uni.navigateTo({ url: '/pages/verify/verify' })
		},
		goPrivacy() {
			uni.navigateTo({ url: '/pages/privacy/privacy' })
		},
		goNotification() {
			uni.navigateTo({ url: '/pages/notifications/notifications' })
		},
		toggleTheme() {
			this.darkMode = !this.darkMode
			uni.showToast({ title: '功能开发中', icon: 'none' })
		},
		goLanguage() {
			uni.showToast({ title: '功能开发中', icon: 'none' })
		},
		goHelp() {
			uni.navigateTo({ url: '/pages/help/help' })
		},
		goSimulation() {
			uni.navigateTo({ url: '/pages/simulation/simulation' })
		},
		goFeedback() {
			uni.navigateTo({ url: '/pages/feedback/feedback' })
		},
		goAbout() {
			uni.navigateTo({ url: '/pages/about/about' })
		},
		goClearCache() {
			this.showConfirm({
				title: '清除缓存',
				content: '确定要清除所有缓存数据吗？',
				confirmText: '清除',
				onConfirm: () => {
					uni.showToast({ title: '清除成功', icon: 'success' })
				}
			})
		},
		checkUpdate() {
			uni.showLoading({ title: '检查中...', mask: true })
			setTimeout(() => {
				uni.hideLoading()
				uni.showModal({
					title: '版本更新',
					content: '当前已是最新版本 V' + this.appVersion,
					showCancel: false,
					confirmText: '知道了'
				})
			}, 1000)
		},
		handleLogout() {
			this.showConfirm({
				title: '退出登录',
				content: '确定要退出当前账号吗？',
				confirmText: '退出',
				onConfirm: () => {
					uni.reLaunch({ url: '/pages/login/login' })
				}
			})
		},
		showConfirm({ title, content, cancelText = '取消', confirmText = '确认', onConfirm }) {
			this.confirmTitle = title
			this.confirmContent = content
			this.confirmCancelText = cancelText
			this.confirmConfirmText = confirmText
			this.onConfirm = onConfirm
			this.confirmVisible = true
		}
	}
}
</script>

<style scoped>
.settings-container {
	height: 100vh;
	background: #F8FAFC;
	display: flex;
	flex-direction: column;
}

.header {
	padding: 64rpx 24rpx 16rpx;
	display: flex;
	align-items: center;
	justify-content: center;
	background: #FFFFFF;
	position: relative;
}

.header-title {
	font-size: 32rpx;
	font-weight: 700;
	color: #1E293B;
}

.content-scroll {
	flex: 1;
}

.settings-section {
	padding: 24rpx;
}

.settings-card {
	background: #FFFFFF;
	border-radius: 24rpx;
	margin-bottom: 24rpx;
	overflow: hidden;
}

.setting-item {
	display: flex;
	align-items: center;
	padding: 28rpx 24rpx;
	border-bottom: 1rpx solid #F1F5F9;
}

.setting-item:last-child {
	border-bottom: none;
}

.setting-icon {
	margin-right: 20rpx;
	width: 64rpx;
	height: 64rpx;
	background: #F1F5F9;
	border-radius: 16rpx;
	display: flex;
	align-items: center;
	justify-content: center;
}

.setting-name {
	flex: 1;
	font-size: 30rpx;
	color: #1E293B;
	font-weight: 600;
}

.setting-arrow {
	color: #94A3B8;
}

.setting-value {
	font-size: 28rpx;
	color: #94A3B8;
	margin-right: 12rpx;
}

.setting-tag {
	font-size: 24rpx;
	padding: 6rpx 16rpx;
	border-radius: 100rpx;
	margin-right: 12rpx;
	font-weight: 600;
}

.setting-tag.success {
	background: #DCFCE7;
	color: #16A34A;
}

.toggle-switch {
	width: 96rpx;
	height: 52rpx;
	background: #E2E8F0;
	border-radius: 26rpx;
	position: relative;
	transition: all 0.3s;
}

.toggle-switch::after {
	content: '';
	position: absolute;
	width: 44rpx;
	height: 44rpx;
	background: #FFFFFF;
	border-radius: 50%;
	top: 4rpx;
	left: 4rpx;
	transition: all 0.3s;
	box-shadow: 0 2rpx 8rpx rgba(0,0,0,0.1);
}

.toggle-switch.active {
	background: #10B981;
}

.toggle-switch.active::after {
	left: 48rpx;
}

.logout-section {
	padding: 0 24rpx;
	margin-top: 24rpx;
}

.logout-btn {
	background: #FFFFFF;
	border-radius: 24rpx;
	height: 96rpx;
	display: flex;
	align-items: center;
	justify-content: center;
	font-size: 30rpx;
	font-weight: 700;
	color: #EF4444;
}

.bottom-safe {
	height: 40rpx;
}
</style>