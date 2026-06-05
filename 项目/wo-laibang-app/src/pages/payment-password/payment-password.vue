<template>
	<view class="payment-password-container">
		<view class="header">
			<text class="header-title">支付密码</text>
			<view class="header-right"></view>
		</view>

		<scroll-view class="content-scroll" scroll-y>
			<view v-if="!isSet" class="set-form">
				<view class="desc-card">
					<text class="desc-icon">⊓</text>
					<text class="desc-title">设置支付密码</text>
					<text class="desc-text">用于支付验证，保障账户资金安全</text>
				</view>

				<view class="form-card">
					<view class="input-group">
						<label class="input-label">支付密码</label>
						<view class="input-wrapper">
							<input
								class="input-field"
								v-model="password"
								:password="!showPassword"
								placeholder="请输入6位数字密码"
								type="number"
								maxlength="6"
							/>
							<text class="toggle-pwd" @click="showPassword = !showPassword">{{ showPassword ? '🙈' : '◕' }}</text>
						</view>
					</view>

					<view class="input-group">
						<label class="input-label">确认密码</label>
						<view class="input-wrapper">
							<input
								class="input-field"
								v-model="confirmPassword"
								:password="!showConfirmPassword"
								placeholder="请再次输入密码"
								type="number"
								maxlength="6"
							/>
							<text class="toggle-pwd" @click="showConfirmPassword = !showConfirmPassword">{{ showConfirmPassword ? '🙈' : '◕' }}</text>
						</view>
					</view>
				</view>

				<view class="tips-section">
					<view class="tips-header">
						<text class="tips-icon"><IconFont name="sparkles" :size="32" /></text>
						<text class="tips-title">密码要求</text>
					</view>
					<text class="tips-text">• 必须为6位数字</text>
					<text class="tips-text">• 不能与登录密码相同</text>
					<text class="tips-text">• 请妥善保管，切勿泄露</text>
				</view>

				<button class="btn-primary" @click="handleSet" :disabled="!canSet || isSubmitting">
					<view v-if="isSubmitting" class="spinner"></view>
					<text v-else>确认设置</text>
				</button>
			</view>

			<view v-else class="manage-form">
				<view class="status-card">
					<view class="status-icon"><IconFont name="lock" :size="48" /></view>
					<text class="status-title">已设置支付密码</text>
					<text class="status-desc">您的账户安全已得到保障</text>
				</view>

				<view class="action-list">
					<view class="action-item" @click="changePassword">
						<text class="action-icon"><IconFont name="tool" :size="32" /></text>
						<text class="action-name">修改支付密码</text>
						<text class="action-arrow"><IconFont name="chevron-right" :size="24" /></text>
					</view>
					<view class="action-item" @click="resetPassword">
						<text class="action-icon"><IconFont name="refresh" :size="32" /></text>
						<text class="action-name">重置支付密码</text>
						<text class="action-arrow"><IconFont name="chevron-right" :size="24" /></text>
					</view>
				</view>
			</view>

			<view class="bottom-safe"></view>
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
			isSet: true,
			password: '',
			confirmPassword: '',
			showPassword: false,
			showConfirmPassword: false,
			isSubmitting: false
		}
	},
	computed: {
		canSet() {
			return this.password.length === 6 && this.confirmPassword.length === 6
		}
	},
	methods: {
		handleSet() {
			if (this.password !== this.confirmPassword) {
				uni.showToast({ title: '两次输入密码不一致', icon: 'none' })
				return
			}

			if (!/^\d{6}$/.test(this.password)) {
				uni.showToast({ title: '密码必须为6位数字', icon: 'none' })
				return
			}

			this.isSubmitting = true
			uni.showLoading({ title: '设置中...' })

			setTimeout(() => {
				uni.hideLoading()
				this.isSubmitting = false
				this.isSet = true

				const userInfo = uni.getStorageSync('currentUser') || {}
				userInfo.hasPayPassword = true
				uni.setStorageSync('currentUser', userInfo)

				uni.setStorageSync('payPassword', this.password)
				uni.setStorageSync('payPasswordSetTime', Date.now())

				uni.showToast({ title: '设置成功', icon: 'success' })
			}, 1500)
		},
		changePassword() {
			uni.navigateTo({ url: '/pages/change-payment-password/change-payment-password' })
		},
		resetPassword() {
			uni.navigateTo({ url: '/pages/forgot-payment-password/forgot-payment-password' })
		},
		}
	}
}
</script>

<style scoped>
.payment-password-container {
	min-height: 100vh;
	background: #F8FAFC;
}

.header {
	display: flex;
	align-items: center;
	justify-content: space-between;
	padding: 44px 24px 20px;
	background: #FFFFFF;
}

.header-title {
	flex: 1;
	font-size: 18px;
	font-weight: 800;
	color: #1E293B;
	text-align: center;
}

.header-right {
	width: 44px;
}

.content-scroll {
	height: calc(100vh - 72px);
}

.desc-card {
	text-align: center;
	padding: 40px 24px;
	background: #FFFFFF;
	margin: 16px 24px;
	border-radius: 24px;
	box-shadow: 0 2px 12px rgba(0, 0, 0, 0.04);
}

.desc-icon {
	font-size: 64px;
	display: block;
	margin-bottom: 16px;
}

.desc-title {
	font-size: 20px;
	font-weight: 800;
	color: #1E293B;
	display: block;
	margin-bottom: 8px;
}

.desc-text {
	font-size: 14px;
	color: #64748B;
}

.form-card {
	background: #FFFFFF;
	margin: 0 24px 16px;
	border-radius: 20px;
	padding: 20px;
	box-shadow: 0 2px 12px rgba(0, 0, 0, 0.04);
}

.input-group {
	margin-bottom: 16px;
}

.input-group:last-child {
	margin-bottom: 0;
}

.input-label {
	font-size: 12px;
	color: #64748B;
	font-weight: 700;
	text-transform: uppercase;
	letter-spacing: 0.5px;
	margin-bottom: 8px;
	display: block;
}

.input-wrapper {
	background: #F8FAFC;
	border-radius: 14px;
	padding: 14px 16px;
	border: 1px solid transparent;
	display: flex;
	align-items: center;
	gap: 12px;
	transition: all 0.3s;
}

.input-wrapper:focus-within {
	background: #FFFFFF;
	border-color: #10B981;
	box-shadow: 0 6px 16px rgba(16, 185, 129, 0.08);
}

.input-field {
	flex: 1;
	font-size: 16px;
	font-weight: 700;
	color: #1E293B;
	border: none;
	outline: none;
	background: transparent;
	letter-spacing: 4px;
}

.toggle-pwd {
	font-size: 18px;
	cursor: pointer;
	padding: 4px;
}

.tips-section {
	margin: 0 24px 24px;
	padding: 16px;
	background: #F0FDF4;
	border-radius: 14px;
}

.tips-header {
	display: flex;
	align-items: center;
	margin-bottom: 10px;
}

.tips-icon {
	font-size: 16px;
	margin-right: 8px;
}

.tips-title {
	font-size: 13px;
	font-weight: 700;
	color: #059669;
}

.tips-text {
	font-size: 12px;
	color: #64748B;
	display: block;
	margin-bottom: 4px;
}

.btn-primary {
	margin: 0 24px;
	width: calc(100% - 48px);
	height: 52px;
	background: linear-gradient(135deg, #10B981, #059669);
	color: #FFFFFF;
	border-radius: 26px;
	font-weight: 800;
	font-size: 16px;
	border: none;
	box-shadow: 0 8px 24px rgba(16, 185, 129, 0.35);
	display: flex;
	align-items: center;
	justify-content: center;
	transition: all 0.3s;
}

.btn-primary:disabled {
	opacity: 0.5;
	box-shadow: none;
}

.spinner {
	width: 20px;
	height: 20px;
	border: 2px solid rgba(255, 255, 255, 0.3);
	border-top-color: #FFFFFF;
	border-radius: 50%;
	animation: spin 0.8s linear infinite;
}

@keyframes spin {
	to { transform: rotate(360deg); }
}

.status-card {
	text-align: center;
	padding: 40px 24px;
	background: #FFFFFF;
	margin: 16px 24px;
	border-radius: 24px;
	box-shadow: 0 2px 12px rgba(0, 0, 0, 0.04);
}

.status-icon {
	font-size: 64px;
	display: block;
	margin-bottom: 16px;
}

.status-title {
	font-size: 20px;
	font-weight: 800;
	color: #1E293B;
	display: block;
	margin-bottom: 8px;
}

.status-desc {
	font-size: 14px;
	color: #64748B;
}

.action-list {
	margin: 24px;
	background: #FFFFFF;
	border-radius: 20px;
	overflow: hidden;
	box-shadow: 0 2px 12px rgba(0, 0, 0, 0.04);
}

.action-item {
	display: flex;
	align-items: center;
	padding: 18px 20px;
	border-bottom: 1px solid #F1F5F9;
}

.action-item:last-child {
	border-bottom: none;
}

.action-icon {
	font-size: 20px;
	margin-right: 14px;
}

.action-name {
	flex: 1;
	font-size: 15px;
	font-weight: 600;
	color: #1E293B;
}

.action-arrow {
	font-size: 16px;
	color: #CBD5E1;
}

.bottom-safe {
	height: 40px;
}
</style>