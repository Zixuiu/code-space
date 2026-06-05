<template>
	<view class="privacy-container">
		<view class="header">
			<text class="header-title">隐私安全</text>
			<view class="header-right"></view>
		</view>

		<scroll-view class="content-scroll" scroll-y>
			<view class="section">
				<text class="section-title">账户安全</text>
				<view class="settings-card">
					<view class="setting-item" @click="goChangePassword">
						<IconFont name="key" :size="40" class="setting-icon" />
						<text class="setting-name">修改登录密码</text>
						<text class="setting-arrow"><IconFont name="chevron-right" :size="24" /></text>
					</view>
					<view class="setting-item" @click="goSetPayPassword">
						<IconFont name="lock" :size="40" class="setting-icon" />
						<text class="setting-name">设置支付密码</text>
						<text class="setting-tag success">{{ hasPayPassword ? '已设置' : '未设置' }}</text>
					</view>
					<view class="setting-item" @click="goBindPhone">
						<IconFont name="phone" :size="40" class="setting-icon" />
						<text class="setting-name">绑定手机号</text>
						<text class="setting-value">138****1234</text>
					</view>
				</view>
			</view>

			<view class="section">
				<text class="section-title">隐私设置</text>
				<view class="settings-card">
					<view class="setting-item">
						<IconFont name="eye-off" :size="40" class="setting-icon" />
						<text class="setting-name">展示我的信息</text>
						<view class="toggle-switch" :class="{ active: showProfile }" @click="showProfile = !showProfile"></view>
					</view>
					<view class="setting-item">
						<IconFont name="map-pin" :size="40" class="setting-icon" />
						<text class="setting-name">允许获取位置</text>
						<view class="toggle-switch" :class="{ active: allowLocation }" @click="allowLocation = !allowLocation"></view>
					</view>
					<view class="setting-item" @click="goBlacklist">
						<IconFont name="x" :size="40" class="setting-icon" />
						<text class="setting-name">黑名单管理</text>
						<text class="setting-arrow">›</text>
					</view>
				</view>
			</view>

			<view class="section">
				<text class="section-title">授权管理</text>
				<view class="settings-card">
					<view class="setting-item">
						<IconFont name="message" :size="40" class="setting-icon" />
						<text class="setting-name">微信授权</text>
						<text class="setting-tag success">已授权</text>
					</view>
					<view class="setting-item">
						<IconFont name="bookmark" :size="40" class="setting-icon" />
						<text class="setting-name">通讯录授权</text>
						<text class="setting-tag">未授权</text>
					</view>
				</view>
			</view>

			<view class="section">
				<text class="section-title">数据管理</text>
				<view class="settings-card">
					<view class="setting-item" @click="exportData">
						<IconFont name="upload" :size="40" class="setting-icon" />
						<text class="setting-name">导出个人数据</text>
						<text class="setting-arrow">›</text>
					</view>
					<view class="setting-item" @click="deleteAccount">
						<IconFont name="trash" :size="40" class="setting-icon" />
						<text class="setting-name delete">注销账户</text>
						<text class="setting-arrow">›</text>
					</view>
				</view>
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
					<view style="flex:1;height:96rpx;display:flex;align-items:center;justify-content:center;" v-if="confirmCancelText" @click="confirmVisible = false">
						<text style="font-size:32rpx;color:#64748B;">{{ confirmCancelText }}</text>
					</view>
					<view style="flex:1;height:96rpx;display:flex;align-items:center;justify-content:center;border-left:1rpx solid #F1F5F9;" @click="confirmOk">
						<text style="font-size:32rpx;color:#3B82F6;font-weight:600;">{{ confirmOkText }}</text>
					</view>
				</view>
			</view>
		</view>
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
			hasPayPassword: false,
			showProfile: true,
			allowLocation: true,
			confirmVisible: false,
			confirmTitle: '',
			confirmContent: '',
			confirmOkText: '确定',
			confirmCancelText: '取消'
		}
	},
	methods: {
		goChangePassword() {
			uni.navigateTo({ url: '/pages/forgot-password/forgot-password' })
		},
		goSetPayPassword() {
			uni.navigateTo({ url: '/pages/payment-password/payment-password' })
		},
		goBindPhone() {
			uni.navigateTo({ url: '/pages/bind-phone/bind-phone' })
		},
		goBlacklist() {
			uni.navigateTo({ url: '/pages/blacklist/blacklist' })
		},
		exportData() {
			this.showConfirm('导出数据', '确定要导出您的个人数据吗？', '导出', '取消')
		},
		deleteAccount() {
			this.showConfirm('注销账户', '注销后所有数据将无法恢复，确定要注销吗？', '注销', '取消')
		},
		showConfirm(title, content, okText = '确定', cancelText = '取消') {
			this.confirmTitle = title
			this.confirmContent = content
			this.confirmOkText = okText
			this.confirmCancelText = cancelText
			this.confirmVisible = true
		},
		confirmOk() {
			this.confirmVisible = false
			uni.showToast({ title: '操作成功', icon: 'success' })
		}
	}
}
</script>

<style scoped>
.privacy-container {
	min-height: 100vh;
	background: #F7F8FA;
}
.header {
	height: 88rpx;
	display: flex;
	align-items: center;
	justify-content: center;
	padding: 0 32rpx;
	background: #FFFFFF;
	border-bottom: 1rpx solid #F1F5F9;
}
.header-title {
	font-size: 34rpx;
	font-weight: 600;
	color: #1E293B;
}
.content-scroll {
	height: calc(100vh - 88rpx);
}
.section {
	padding: 32rpx 24rpx 0;
}
.section-title {
	font-size: 26rpx;
	color: #94A3B8;
	margin-bottom: 16rpx;
	display: block;
}
.settings-card {
	background: #FFFFFF;
	border-radius: 20rpx;
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
	color: #64748B;
}
.setting-name {
	flex: 1;
	font-size: 30rpx;
	color: #1E293B;
}
.setting-value {
	font-size: 28rpx;
	color: #94A3B8;
}
.setting-arrow {
	font-size: 28rpx;
	color: #CBD5E1;
}
.setting-tag {
	font-size: 24rpx;
	padding: 4rpx 12rpx;
	border-radius: 8rpx;
	background: #F1F5F9;
	color: #64748B;
}
.setting-tag.success {
	background: #DCFCE7;
	color: #16A34A;
}
.setting-name.delete {
	color: #EF4444;
}
.toggle-switch {
	width: 88rpx;
	height: 48rpx;
	background: #E2E8F0;
	border-radius: 24rpx;
	position: relative;
	transition: all 0.3s;
}
.toggle-switch.active {
	background: #3B82F6;
}
.toggle-switch::after {
	content: '';
	position: absolute;
	width: 40rpx;
	height: 40rpx;
	background: #FFFFFF;
	border-radius: 50%;
	top: 4rpx;
	left: 4rpx;
	transition: all 0.3s;
}
.toggle-switch.active::after {
	left: 44rpx;
}
.bottom-safe {
	height: 40rpx;
}
</style>
