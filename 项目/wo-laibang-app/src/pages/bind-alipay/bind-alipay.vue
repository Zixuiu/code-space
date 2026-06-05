<template>
	<view class="container">
		<view class="header">
			<text class="header-title">绑定支付宝</text>
			<view class="header-right"></view>
		</view>

		<scroll-view class="content-scroll" scroll-y>
			<view class="form-card">
				<view class="input-group">
					<label class="input-label">支付宝账号</label>
					<view class="input-wrapper">
						<IconFont name="phone" :size="32" class="input-icon" />
						<input
							class="input-field"
							v-model="form.account"
							type="text"
							placeholder="请输入手机号或邮箱"
						/>
					</view>
					<text class="input-hint">输入您支付宝绑定的手机号或邮箱</text>
				</view>

				<view class="input-group">
					<label class="input-label">真实姓名</label>
					<view class="input-wrapper">
						<IconFont name="user" :size="32" class="input-icon" />
						<input
							class="input-field"
							v-model="form.name"
							type="text"
							placeholder="请输入真实姓名"
						/>
					</view>
				</view>
			</view>

			<view class="tip-card">
				<IconFont name="shield" :size="32" class="tip-icon" />
				<view class="tip-content">
					<text class="tip-title">安全提示</text>
					<text class="tip-text">您的账户信息将加密处理，仅用于提现操作我们不会泄露您的个人信息</text>
				</view>
			</view>

			<button
				class="submit-btn"
				:class="{ disabled: !canSubmit }"
				@click="handleSubmit"
				:disabled="!canSubmit || isSubmitting"
			>
				<view v-if="isSubmitting" class="spinner"></view>
				<text v-else>确认绑定</text>
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
			form: {
				account: '',
				name: ''
			},
			isSubmitting: false
		}
	},
	computed: {
		canSubmit() {
			return this.form.account.trim() && this.form.name.trim()
		}
	},
	methods: {
		validateAccount() {
			const account = this.form.account.trim()
			const phoneRegex = /^1[3-9]\d{9}$/
			const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
			return phoneRegex.test(account) || emailRegex.test(account)
		},
		handleSubmit() {
			if (!this.canSubmit) return

			if (!this.validateAccount()) {
				uni.showToast({ title: '请输入正确的手机号或邮箱', icon: 'none' })
				return
			}

			this.isSubmitting = true

			setTimeout(() => {
				const userInfo = uni.getStorageSync('userInfo') || {}
				userInfo.bindedAlipay = this.form.account
				userInfo.alipayName = this.form.name
				uni.setStorageSync('userInfo', userInfo)

				const currentUser = uni.getStorageSync('currentUser') || {}
				currentUser.bindedAlipay = this.form.account
				currentUser.alipayName = this.form.name
				uni.setStorageSync('currentUser', currentUser)

				this.isSubmitting = false
				uni.showToast({ title: '绑定成功', icon: 'success' })

				setTimeout(() => {
					uni.navigateBack()
				}, 1500)
			}, 1000)
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
	padding: 32rpx;
	margin-bottom: 24rpx;
	box-shadow: 0 2rpx 12rpx rgba(0, 0, 0, 0.04);
}

.input-group {
	margin-bottom: 24rpx;
}

.input-label {
	font-size: 12px;
	color: #64748B;
	font-weight: 700;
	text-transform: uppercase;
	letter-spacing: 0.5px;
	margin-bottom: 12rpx;
	display: block;
}

.input-wrapper {
	background: #F8FAFC;
	border-radius: 14rpx;
	padding: 16rpx 20rpx;
	border: 2rpx solid transparent;
	display: flex;
	align-items: center;
	gap: 12rpx;
	transition: all 0.3s;
}

.input-wrapper:focus-within {
	background: #FFFFFF;
	border-color: #10B981;
	box-shadow: 0 6rpx 16rpx rgba(16, 185, 129, 0.08);
}

.input-icon {
	width: 20px;
	display: flex;
	align-items: center;
	justify-content: center;
	color: #64748B;
}

.input-field {
	flex: 1;
	font-size: 15px;
	font-weight: 600;
	color: #1E293B;
	border: none;
	outline: none;
	background: transparent;
}

.input-hint {
	font-size: 12px;
	color: #94A3B8;
	margin-top: 8rpx;
	display: block;
}

.tip-card {
	background: #F0FDF4;
	border-radius: 16rpx;
	padding: 24rpx;
	display: flex;
	gap: 16rpx;
	margin-bottom: 32rpx;
}

.tip-icon {
	color: #10B981;
	flex-shrink: 0;
}

.tip-content {
	flex: 1;
}

.tip-title {
	font-size: 14px;
	font-weight: 700;
	color: #059669;
	display: block;
	margin-bottom: 8rpx;
}

.tip-text {
	font-size: 12px;
	color: #64748B;
	line-height: 1.5;
}

.submit-btn {
	width: 100%;
	height: 100rpx;
	background: linear-gradient(135deg, #10B981, #059669);
	color: #FFFFFF;
	border-radius: 50rpx;
	font-size: 16px;
	font-weight: 800;
	border: none;
	display: flex;
	align-items: center;
	justify-content: center;
	box-shadow: 0 8rpx 24rpx rgba(16, 185, 129, 0.35);
}

.submit-btn.disabled {
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
	height: 40rpx;
}
</style>
