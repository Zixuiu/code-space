<template>
	<view class="container">
		<view class="header">
			<text class="header-title">忘记支付密码</text>
			<view class="header-right"></view>
		</view>

		<scroll-view class="content-scroll" scroll-y>
			<view class="form-card">
				<view class="step-indicator">
					<view class="step" :class="{ active: step >= 1, completed: step > 1 }">
						<view class="step-num">{{ step > 1 ? '✓' : '1' }}</view>
						<text class="step-text">身份验证</text>
					</view>
					<view class="step-line" :class="{ active: step > 1 }"></view>
					<view class="step" :class="{ active: step >= 2 }">
						<view class="step-num">2</view>
						<text class="step-text">重置密码</text>
					</view>
					<view class="step-line" :class="{ active: step > 2 }"></view>
					<view class="step" :class="{ active: step >= 3 }">
						<view class="step-num">3</view>
						<text class="step-text">完成</text>
					</view>
				</view>

				<view v-if="step === 1" class="step-content">
					<view class="desc-text">
						为保障账户安全，需要验证您的手机号
					</view>

					<view class="input-group">
						<label class="input-label">手机号</label>
						<view class="input-wrapper" :class="{ focused: focusedField === 'phone' }">
							<IconFont name="phone" :size="20" class="input-icon" />
							<input
								class="input-field"
								v-model="phone"
								placeholder="请输入绑定的手机号"
								type="number"
								maxlength="11"
								@focus="focusedField = 'phone'"
								@blur="focusedField = ''"
							/>
						</view>
					</view>

					<view class="input-group">
						<label class="input-label">验证码</label>
						<view class="input-wrapper code-wrapper" :class="{ focused: focusedField === 'code' }">
							<IconFont name="lock" :size="20" class="input-icon" />
							<input
								class="input-field"
								v-model="code"
								placeholder="请输入验证码"
								type="number"
								maxlength="6"
								@focus="focusedField = 'code'"
								@blur="focusedField = ''"
							/>
							<button
								class="code-btn"
								:class="{ disabled: counting }"
								@click="sendCode"
								:disabled="counting || phone.length !== 11"
							>
								{{ counting ? `${count}s` : '获取验证码' }}
							</button>
						</view>
					</view>
				</view>

				<view v-if="step === 2" class="step-content">
					<view class="desc-text">
						验证成功，请设置新的支付密码
					</view>

					<view class="input-group">
						<label class="input-label">新支付密码</label>
						<view class="input-wrapper" :class="{ focused: focusedField === 'newPassword' }">
							<IconFont name="lock" :size="20" class="input-icon" />
							<input
								class="input-field"
								v-model="newPassword"
								:password="!showPassword"
								placeholder="请输入6位新密码"
								type="number"
								maxlength="6"
								@focus="focusedField = 'newPassword'"
								@blur="focusedField = ''"
							/>
							<view class="toggle-pwd" @click="showPassword = !showPassword">
								<IconFont :name="showPassword ? 'eye-off' : 'eye'" :size="20" />
							</view>
						</view>
					</view>

					<view class="input-group">
						<label class="input-label">确认密码</label>
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
				</view>

				<view v-if="step === 3" class="step-content success-content">
					<view class="success-icon">
						<IconFont name="check-circle" :size="80" />
					</view>
					<text class="success-title">重置成功</text>
					<text class="success-desc">您的支付密码已重置</text>
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
			phone: '',
			code: '',
			newPassword: '',
			confirmPassword: '',
			showPassword: false,
			showConfirmPassword: false,
			focusedField: '',
			counting: false,
			count: 60,
			isSubmitting: false
		}
	},
	computed: {
		canNext() {
			if (this.step === 1) {
				return this.phone.length === 11 && this.code.length === 6
			} else if (this.step === 2) {
				return this.newPassword.length === 6 &&
					this.confirmPassword.length === 6 &&
					this.newPassword === this.confirmPassword
			}
			return true
		}
	},
	methods: {
		sendCode() {
			if (this.counting) return
			if (!/^1[3-9]\d{9}$/.test(this.phone)) {
				uni.showToast({ title: '请输入正确的手机号', icon: 'none' })
				return
			}

			this.counting = true
			uni.showToast({ title: '验证码已发送', icon: 'success' })

			const timer = setInterval(() => {
				this.count--
				if (this.count <= 0) {
					clearInterval(timer)
					this.counting = false
					this.count = 60
				}
			}, 1000)
		},
		async handleNext() {
			if (this.step === 1) {
				this.isSubmitting = true
				await this.verifyCode()
				this.isSubmitting = false
			} else if (this.step === 2) {
				if (this.newPassword !== this.confirmPassword) {
					uni.showToast({ title: '两次密码不一致', icon: 'none' })
					return
				}
				this.isSubmitting = true
				await this.resetPassword()
				this.isSubmitting = false
			} else {
				uni.navigateBack()
			}
		},
		verifyCode() {
			return new Promise((resolve) => {
				setTimeout(() => {
					if (this.code === '123456') {
						this.step = 2
						resolve(true)
					} else {
						uni.showToast({ title: '验证码错误', icon: 'none' })
						resolve(false)
					}
				}, 1000)
			})
		},
		resetPassword() {
			return new Promise((resolve) => {
				setTimeout(() => {
					uni.setStorageSync('payPassword', this.newPassword)
					this.step = 3
					resolve(true)
				}, 1000)
			})
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

.desc-text {
	font-size: 28rpx;
	color: #64748B;
	text-align: center;
	margin-bottom: 32rpx;
	line-height: 1.6;
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

.code-wrapper {
	padding-right: 12rpx;
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
}

.toggle-pwd {
	padding: 8rpx;
	color: #94A3B8;
}

.code-btn {
	font-size: 24rpx;
	font-weight: 700;
	color: #10B981;
	background: transparent;
	border: none;
	padding: 8rpx 16rpx;
	white-space: nowrap;
}

.code-btn.disabled {
	color: #94A3B8;
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

.bottom-safe {
	height: 60rpx;
}
</style>