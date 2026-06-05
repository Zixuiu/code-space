<template>
	<view class="container">
		<view class="header">
			<text class="header-title">修改支付密码</text>
			<view class="header-right"></view>
		</view>

		<scroll-view class="content-scroll" scroll-y>
			<view class="form-card">
				<view class="step-indicator">
					<view class="step" :class="{ active: step >= 1, completed: step > 1 }">
						<view class="step-num">{{ step > 1 ? '✓' : '1' }}</view>
						<text class="step-text">验证原密码</text>
					</view>
					<view class="step-line" :class="{ active: step > 1 }"></view>
					<view class="step" :class="{ active: step >= 2 }">
						<view class="step-num">2</view>
						<text class="step-text">设置新密码</text>
					</view>
					<view class="step-line" :class="{ active: step > 2 }"></view>
					<view class="step" :class="{ active: step >= 3 }">
						<view class="step-num">3</view>
						<text class="step-text">完成</text>
					</view>
				</view>

				<view v-if="step === 1" class="step-content">
					<view class="input-group">
						<label class="input-label">原支付密码</label>
						<view class="input-wrapper" :class="{ focused: focusedField === 'oldPassword' }">
							<IconFont name="lock" :size="20" class="input-icon" />
							<input
								class="input-field"
								v-model="oldPassword"
								:password="!showOldPassword"
								placeholder="请输入原支付密码"
								type="number"
								maxlength="6"
								@focus="focusedField = 'oldPassword'"
								@blur="focusedField = ''"
							/>
							<view class="toggle-pwd" @click="showOldPassword = !showOldPassword">
								<IconFont :name="showOldPassword ? 'eye-off' : 'eye'" :size="20" />
							</view>
						</view>
					</view>
				</view>

				<view v-if="step === 2" class="step-content">
					<view class="input-group">
						<label class="input-label">新支付密码</label>
						<view class="input-wrapper" :class="{ focused: focusedField === 'newPassword' }">
							<IconFont name="lock" :size="20" class="input-icon" />
							<input
								class="input-field"
								v-model="newPassword"
								:password="!showNewPassword"
								placeholder="请输入6位新密码"
								type="number"
								maxlength="6"
								@focus="focusedField = 'newPassword'"
								@blur="focusedField = ''"
							/>
							<view class="toggle-pwd" @click="showNewPassword = !showNewPassword">
								<IconFont :name="showNewPassword ? 'eye-off' : 'eye'" :size="20" />
							</view>
						</view>
					</view>

					<view class="input-group">
						<label class="input-label">确认新密码</label>
						<view class="input-wrapper" :class="{ focused: focusedField === 'confirmPassword' }">
							<IconFont name="lock" :size="20" class="input-icon" />
							<input
								class="input-field"
								v-model="confirmPassword"
								:password="!showConfirmPassword"
								placeholder="请再次输入新密码"
								type="number"
								maxlength="6"
								@focus="focusedField = 'confirmPassword'"
								@blur="focusedField = ''"
							/>
							<view class="toggle-pwd" @click="showConfirmPassword = !showConfirmPassword">
								<IconFont :name="showConfirmPassword ? 'eye-off' : 'eye'" :size="20" />
							</view>
						</view>
					</view>

					<view class="tips-section">
						<view class="tips-header">
							<IconFont name="info-circle" :size="16" class="tips-icon" />
							<text class="tips-title">密码要求</text>
						</view>
						<text class="tips-text">• 必须为6位数字</text>
						<text class="tips-text">• 不能与原密码相同</text>
					</view>
				</view>

				<view v-if="step === 3" class="step-content success-content">
					<view class="success-icon">
						<IconFont name="check-circle" :size="80" />
					</view>
					<text class="success-title">修改成功</text>
					<text class="success-desc">您的支付密码已更新</text>
				</view>
			</view>

			<button
				class="btn-primary"
				@click="handleNext"
				:disabled="!canNext || isSubmitting"
			>
				<view v-if="isSubmitting" class="spinner"></view>
				<text v-else>{{ step === 3 ? '完成' : '下一步' }}</text>
			</button>

			<view v-if="step === 1" class="forgot-link" @click="goForgot">
				<text>忘记原密码？</text>
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
			step: 1,
			oldPassword: '',
			newPassword: '',
			confirmPassword: '',
			showOldPassword: false,
			showNewPassword: false,
			showConfirmPassword: false,
			focusedField: '',
			isSubmitting: false
		}
	},
	computed: {
		canNext() {
			if (this.step === 1) {
				return this.oldPassword.length === 6
			} else if (this.step === 2) {
				return this.newPassword.length === 6 &&
					this.confirmPassword.length === 6 &&
					this.newPassword === this.confirmPassword
			}
			return true
		}
	},
	methods: {
		async handleNext() {
			if (this.step === 1) {
				const isValid = await this.verifyOldPassword()
				if (isValid) {
					this.step = 2
				}
			} else if (this.step === 2) {
				if (this.newPassword !== this.confirmPassword) {
					uni.showToast({ title: '两次密码不一致', icon: 'none' })
					return
				}
				this.isSubmitting = true
				await this.updatePassword()
			} else {
				uni.navigateBack()
			}
		},
		verifyOldPassword() {
			return new Promise((resolve) => {
				const userInfo = uni.getStorageSync('currentUser') || {}
				const savedPwd = uni.getStorageSync('payPassword') || '123456'

				if (this.oldPassword === savedPwd) {
					resolve(true)
				} else {
					uni.showToast({ title: '原密码错误', icon: 'none' })
					resolve(false)
				}
			})
		},
		updatePassword() {
			return new Promise((resolve) => {
				setTimeout(() => {
					uni.setStorageSync('payPassword', this.newPassword)
					uni.setStorageSync('payPasswordSetTime', Date.now())
					this.isSubmitting = false
					this.step = 3
					resolve(true)
				}, 1000)
			})
		},
		goForgot() {
			uni.navigateTo({ url: '/pages/forgot-payment-password/forgot-payment-password' })
		},
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
	font-size: 18px;
	font-weight: 800;
	color: #1E293B;
	text-align: center;
}

.header-right {
	width: 40px;
}

.content-scroll {
	height: calc(100vh - 89px);
	padding: 24rpx;
}

.form-card {
	background: #FFFFFF;
	border-radius: 24rpx;
	padding: 32rpx 24rpx;
	margin-bottom: 24rpx;
	box-shadow: 0 2px 12px rgba(0, 0, 0, 0.04);
}

.step-indicator {
	display: flex;
	align-items: center;
	justify-content: center;
	margin-bottom: 40rpx;
}

.step {
	display: flex;
	flex-direction: column;
	align-items: center;
}

.step-num {
	width: 48rpx;
	height: 48rpx;
	border-radius: 50%;
	background: #E2E8F0;
	color: #94A3B8;
	font-size: 22rpx;
	font-weight: 700;
	display: flex;
	align-items: center;
	justify-content: center;
	margin-bottom: 8rpx;
}

.step-text {
	font-size: 22rpx;
	color: #94A3B8;
	font-weight: 500;
}

.step.active .step-num {
	background: #10B981;
	color: #FFFFFF;
}

.step.active .step-text {
	color: #10B981;
}

.step.completed .step-num {
	background: #10B981;
	color: #FFFFFF;
}

.step-line {
	width: 80rpx;
	height: 2rpx;
	background: #E2E8F0;
	margin: 0 12rpx;
	margin-bottom: 28rpx;
}

.step-line.active {
	background: #10B981;
}

.step-content {
	padding: 0 12rpx;
}

.input-group {
	margin-bottom: 24rpx;
}

.input-label {
	font-size: 24rpx;
	color: #64748B;
	font-weight: 700;
	text-transform: uppercase;
	letter-spacing: 0.5px;
	margin-bottom: 12rpx;
	display: block;
}

.input-wrapper {
	background: #F8FAFC;
	border-radius: 16rpx;
	padding: 28rpx 20rpx;
	border: 2rpx solid transparent;
	display: flex;
	align-items: center;
	gap: 12rpx;
	transition: all 0.3s;
}

.input-wrapper.focused {
	background: #FFFFFF;
	border-color: #10B981;
	box-shadow: 0 6rpx 16rpx rgba(16, 185, 129, 0.08);
}

.input-icon {
	color: #94A3B8;
}

.input-field {
	flex: 1;
	font-size: 32rpx;
	font-weight: 700;
	color: #1E293B;
	border: none;
	outline: none;
	background: transparent;
	letter-spacing: 4rpx;
}

.toggle-pwd {
	padding: 8rpx;
	color: #94A3B8;
}

.tips-section {
	background: #F0FDF4;
	border-radius: 14rpx;
	padding: 20rpx;
	margin-top: 16rpx;
}

.tips-header {
	display: flex;
	align-items: center;
	gap: 8rpx;
	margin-bottom: 10rpx;
}

.tips-icon {
	color: #10B981;
}

.tips-title {
	font-size: 24rpx;
	font-weight: 700;
	color: #059669;
}

.tips-text {
	font-size: 22rpx;
	color: #64748B;
	display: block;
	margin-bottom: 6rpx;
}

.success-content {
	text-align: center;
	padding: 40rpx 0;
}

.success-icon {
	color: #10B981;
	margin-bottom: 24rpx;
}

.success-title {
	font-size: 36rpx;
	font-weight: 800;
	color: #1E293B;
	display: block;
	margin-bottom: 12rpx;
}

.success-desc {
	font-size: 28rpx;
	color: #64748B;
}

.btn-primary {
	width: 100%;
	height: 100rpx;
	background: linear-gradient(135deg, #10B981, #059669);
	color: #FFFFFF;
	border-radius: 50rpx;
	font-size: 32rpx;
	font-weight: 800;
	display: flex;
	align-items: center;
	justify-content: center;
	border: none;
	box-shadow: 0 8rpx 24rpx rgba(16, 185, 129, 0.35);
}

.btn-primary:disabled {
	opacity: 0.5;
	box-shadow: none;
}

.spinner {
	width: 40rpx;
	height: 40rpx;
	border: 4rpx solid rgba(255, 255, 255, 0.3);
	border-top-color: #FFFFFF;
	border-radius: 50%;
	animation: spin 0.8s linear infinite;
}

@keyframes spin {
	to { transform: rotate(360deg); }
}

.forgot-link {
	text-align: center;
	margin-top: 32rpx;
}

.forgot-link text {
	font-size: 26rpx;
	color: #10B981;
	font-weight: 600;
}

.bottom-safe {
	height: 60rpx;
}
</style>