<template>
	<view class="container">
		<view class="header">
			<text class="header-title">支付验证</text>
			<view class="header-right"></view>
		</view>

		<scroll-view class="content-scroll" scroll-y>
			<view class="verify-card">
				<view class="verify-icon">
					<IconFont name="lock" :size="48" />
				</view>
				<text class="verify-title">请输入支付密码</text>
				<text class="verify-desc" v-if="amount">交易金额：¥{{ amount }}</text>
				<text class="verify-desc" v-else>{{ verifyTitle }}</text>
			</view>

			<view class="password-section">
				<view class="password-label">支付密码</view>
				<view class="password-input-wrapper" :class="{ error: passwordError, locked: isLocked }">
					<input
						class="password-input"
						v-model="password"
						type="password"
						:password="true"
						maxlength="6"
						:placeholder="isLocked ? '已锁定，请30分钟后再试' : '请输入6位支付密码'"
						:disabled="isLocked"
						@input="onPasswordInput"
					/>
				</view>
				<view class="error-hint" v-if="passwordError">
					<IconFont name="alert-circle" :size="14" />
					<text>{{ passwordError }}</text>
				</view>
				<view class="lock-hint" v-if="isLocked">
					<IconFont name="clock" :size="14" />
					<text>密码错误次数过多，请{{ lockTime }}秒后再试</text>
				</view>
			</view>

			<button
				class="verify-btn"
				:class="{ disabled: password.length !== 6 || isLocked }"
				@click="handleVerify"
				:disabled="password.length !== 6 || isLocked || isVerifying"
			>
				<view v-if="isVerifying" class="spinner"></view>
				<text v-else>确认</text>
			</button>

			<view class="forgot-link" @click="goForgotPassword">
				<text>忘记支付密码？</text>
			</view>

			<view class="tip-card">
				<IconFont name="shield" :size="16" class="tip-icon" />
				<text class="tip-text">您的支付安全由多种机制保障，请放心使用</text>
			</view>
		</scroll-view>
	</view>
</template>

<script>
import IconFont from '@/components/icon-font/icon-font.vue'
import paymentService from '@/utils/payment'

export default {
	components: {
		IconFont
	},
	data() {
		return {
			password: '',
			passwordError: '',
			isVerifying: false,
			isLocked: false,
			lockTime: 0,
			lockTimer: null,
			errorCount: 0,
			amount: '',
			verifyTitle: '验证身份',
			action: ''
		}
	},
	async onLoad(options) {
		if (options.amount) {
			this.amount = options.amount
		}
		if (options.title) {
			this.verifyTitle = options.title
		}
		if (options.action) {
			this.action = options.action
		}
		this.checkLockStatus()
		this.checkPasswordAge()
	},
	onUnload() {
		if (this.lockTimer) {
			clearInterval(this.lockTimer)
		}
	},
	methods: {
		checkPasswordAge() {
			const setTime = uni.getStorageSync('payPasswordSetTime')
			if (!setTime) return

			const daysSinceSet = Math.floor((Date.now() - setTime) / (1000 * 60 * 60 * 24))
			if (daysSinceSet >= 90) {
				uni.showModal({
					title: '安全提醒',
					content: `您的支付密码已使用${daysSinceSet}天，建议定期更换以保障账户安全。`,
					confirmText: '立即更换',
					cancelText: '暂不更换',
					success: (res) => {
						if (res.confirm) {
							uni.navigateTo({
								url: '/pages/change-payment-password/change-payment-password'
							})
						}
					}
				})
			}
		},
		checkLockStatus() {
			if (paymentService.isLocked()) {
				this.isLocked = true
				this.lockTime = paymentService.getRemainingLockTime()
				this.startLockTimer()
			} else {
				const lockData = paymentService.getVerifyLockStatus()
				this.errorCount = lockData.attempts || 0
			}
		},
		startLockTimer() {
			this.lockTimer = setInterval(() => {
				this.lockTime--
				if (this.lockTime <= 0) {
					this.isLocked = false
					this.errorCount = 0
					paymentService.clearVerifyLock()
					clearInterval(this.lockTimer)
					this.lockTimer = null
				}
			}, 1000)
		},
		onPasswordInput() {
			if (this.passwordError) {
				this.passwordError = ''
			}
		},
		async handleVerify() {
			if (this.password.length !== 6 || this.isLocked) return

			this.isVerifying = true

			try {
				const result = await paymentService.verifyPayPassword(this.password)

				this.errorCount = 0
				paymentService.clearVerifyLock()

				const pages = getCurrentPages()
				const prevPage = pages[pages.length - 2]

				if (prevPage && prevPage.onPaymentVerifySuccess) {
					prevPage.onPaymentVerifySuccess()
				}

				uni.showToast({ title: '验证成功', icon: 'success' })
				setTimeout(() => {
					uni.navigateBack()
				}, 1000)
			} catch (e) {
				this.isVerifying = false
				this.errorCount++
				this.password = ''

				if (paymentService.handleVerifyError()) {
					this.isLocked = true
					this.lockTime = 1800
					this.startLockTimer()
					this.passwordError = '密码错误次数过多，已锁定30分钟'
				} else {
					this.passwordError = `支付密码错误，剩余${3 - this.errorCount}次机会`
				}
			}
		},
		goForgotPassword() {
			uni.navigateTo({
				url: '/pages/forgot-payment-password/forgot-payment-password'
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

.verify-card {
	background: linear-gradient(135deg, #10B981, #059669);
	border-radius: 24rpx;
	padding: 48rpx 32rpx;
	text-align: center;
	margin-bottom: 40rpx;
}

.verify-icon {
	width: 100rpx;
	height: 100rpx;
	background: rgba(255, 255, 255, 0.2);
	border-radius: 50%;
	display: flex;
	align-items: center;
	justify-content: center;
	margin: 0 auto 24rpx;
	color: #FFFFFF;
}

.verify-title {
	font-size: 32rpx;
	font-weight: 800;
	color: #FFFFFF;
	display: block;
	margin-bottom: 12rpx;
}

.verify-desc {
	font-size: 26rpx;
	color: rgba(255, 255, 255, 0.8);
}

.password-section {
	margin-bottom: 40rpx;
}

.password-label {
	font-size: 26rpx;
	font-weight: 700;
	color: #1E293B;
	margin-bottom: 16rpx;
}

.password-input-wrapper {
	background: #FFFFFF;
	border-radius: 16rpx;
	padding: 28rpx 24rpx;
	border: 2rpx solid #E2E8F0;
	transition: all 0.3s;
}

.password-input-wrapper.error {
	border-color: #EF4444;
}

.password-input-wrapper.locked {
	background: #F8FAFC;
	border-color: #E2E8F0;
}

.password-input {
	width: 100%;
	font-size: 32rpx;
	font-weight: 700;
	color: #1E293B;
	border: none;
	outline: none;
	background: transparent;
	letter-spacing: 8rpx;
	text-align: center;
}

.error-hint {
	display: flex;
	align-items: center;
	gap: 8rpx;
	margin-top: 16rpx;
	color: #EF4444;
	font-size: 24rpx;
}

.lock-hint {
	display: flex;
	align-items: center;
	gap: 8rpx;
	margin-top: 16rpx;
	color: #F59E0B;
	font-size: 24rpx;
}

.verify-btn {
	width: 100%;
	height: 100rpx;
	background: linear-gradient(135deg, #10B981, #059669);
	color: #FFFFFF;
	border-radius: 50rpx;
	font-size: 32rpx;
	font-weight: 800;
	border: none;
	display: flex;
	align-items: center;
	justify-content: center;
	box-shadow: 0 8rpx 24rpx rgba(16, 185, 129, 0.35);
}

.verify-btn.disabled {
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

.tip-card {
	display: flex;
	align-items: center;
	gap: 12rpx;
	background: #F0FDF4;
	border-radius: 12rpx;
	padding: 20rpx;
	margin-top: 40rpx;
}

.tip-icon {
	color: #10B981;
	flex-shrink: 0;
}

.tip-text {
	font-size: 24rpx;
	color: #059669;
}
</style>
