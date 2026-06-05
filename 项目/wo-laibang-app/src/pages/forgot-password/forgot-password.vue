<template>
	<view class="forgot-container">
		<view class="header">
			<text class="header-title">找回密码</text>
			<view class="header-right"></view>
		</view>

		<scroll-view class="content-scroll" scroll-y>
			<view class="logo-section">
				<view class="logo-box"><IconFont name="lock" :size="48" /></view>
				<text class="logo-title">忘记密码了？</text>
				<text class="logo-subtitle">没关系，我们来帮您找回</text>
			</view>

			<view class="form-card">
				<view class="step-indicator">
					<view class="step-item" :class="{ active: step >= 1, completed: step > 1 }">
						<view class="step-circle">
							<text v-if="step <= 1">1</text>
							<text v-else><IconFont name="check" :size="20" /></text>
						</view>
						<text class="step-label">验证身份</text>
					</view>
					<view class="step-line" :class="{ active: step > 1 }"></view>
					<view class="step-item" :class="{ active: step >= 2, completed: step > 2 }">
						<view class="step-circle">
							<text v-if="step <= 2">2</text>
							<text v-else>✓</text>
						</view>
						<text class="step-label">重置密码</text>
					</view>
					<view class="step-line" :class="{ active: step > 2 }"></view>
					<view class="step-item" :class="{ active: step >= 3 }">
						<view class="step-circle">3</view>
						<text class="step-label">完成</text>
					</view>
				</view>

				<view v-if="step === 1" class="step-content">
					<view class="input-group">
						<label class="input-label">手机号码</label>
						<view class="input-wrapper">
							<text class="input-icon"><IconFont name="phone" :size="32" /></text>
							<input
								class="input-field"
								placeholder="请输入注册的手机号"
								v-model="form.phone"
								type="number"
								maxlength="11"
							/>
						</view>
					</view>

					<view class="input-group">
						<label class="input-label">验证码</label>
						<view class="input-wrapper code-wrapper">
							<text class="input-icon"><IconFont name="mail" :size="32" /></text>
							<input
								class="input-field"
								placeholder="请输入验证码"
								v-model="form.code"
								type="number"
								maxlength="6"
							/>
							<button
								class="code-btn"
								:class="{ disabled: counting }"
								@click="sendCode"
							>
								{{ counting ? `${count}s` : '获取验证码' }}
							</button>
						</view>
					</view>

					<button class="btn-primary" @click="verifyCode">
						<text>验证并下一步</text>
					</button>
				</view>

				<view v-if="step === 2" class="step-content">
					<view class="input-group">
						<label class="input-label">新密码</label>
						<view class="input-wrapper">
							<text class="input-icon"><IconFont name="lock" :size="32" /></text>
							<input
								class="input-field"
								placeholder="请设置新密码（8-20位）"
								v-model="form.password"
								:password="!showPassword"
								maxlength="20"
							/>
							<text class="toggle-pwd" @click="showPassword = !showPassword">{{ showPassword ? '🙈' : '◕' }}</text>
						</view>
					</view>

					<view class="input-group">
						<label class="input-label">确认密码</label>
						<view class="input-wrapper">
							<text class="input-icon"><IconFont name="lock" :size="32" /></text>
							<input
								class="input-field"
								placeholder="请再次输入新密码"
								v-model="form.confirmPassword"
								:password="!showConfirmPassword"
								maxlength="20"
							/>
							<text class="toggle-pwd" @click="showConfirmPassword = !showConfirmPassword">{{ showConfirmPassword ? '🙈' : '◕' }}</text>
						</view>
					</view>

					<view class="tips-card">
						<text class="tips-title">密码要求：</text>
						<text class="tips-item">• 长度为8-20个字符</text>
						<text class="tips-item">• 包含大小写字母和数字</text>
						<text class="tips-item">• 不允许连续三位相同字符</text>
					</view>

					<button class="btn-primary" @click="resetPassword">
						<text>确认重置</text>
					</button>
				</view>

				<view v-if="step === 3" class="step-content success-content">
					<view class="success-icon">✅</view>
					<text class="success-title">密码重置成功</text>
					<text class="success-subtitle">您的密码已成功修改，请使用新密码登录</text>

					<view class="countdown-card">
						<text class="countdown-text">{{ countdown }} 秒后自动跳转</text>
					</view>

					<button class="btn-primary" @click="goLogin">
						<text>返回登录</text>
					</button>
				</view>
			</view>
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
			form: {
				phone: '',
				code: '',
				password: '',
				confirmPassword: ''
			},
			counting: false,
			count: 60,
			showPassword: false,
			showConfirmPassword: false,
			countdown: 5
		}
	},
	methods: {
		sendCode() {
			if (this.counting) return
			if (!/^1[3-9]\d{9}$/.test(this.form.phone)) {
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
		verifyCode() {
			if (!/^1[3-9]\d{9}$/.test(this.form.phone)) {
				uni.showToast({ title: '请输入正确的手机号', icon: 'none' })
				return
			}
			if (!/^\d{6}$/.test(this.form.code)) {
				uni.showToast({ title: '请输入6位验证码', icon: 'none' })
				return
			}

			uni.showToast({ title: '验证成功', icon: 'success' })
			this.step = 2
		},
		resetPassword() {
			if (this.form.password.length < 8) {
				uni.showToast({ title: '密码长度至少为8位', icon: 'none' })
				return
			}
			if (this.form.password !== this.form.confirmPassword) {
				uni.showToast({ title: '两次输入的密码不一致', icon: 'none' })
				return
			}

			uni.showLoading({ title: '重置中...' })

			setTimeout(() => {
				uni.hideLoading()
				uni.showToast({ title: '密码重置成功', icon: 'success' })
				this.step = 3
				this.startCountdown()
			}, 1500)
		},
		startCountdown() {
			this.countdown = 5
			const timer = setInterval(() => {
				this.countdown--
				if (this.countdown <= 0) {
					clearInterval(timer)
					this.goLogin()
				}
			}, 1000)
		},
		goLogin() {
			uni.redirectTo({ url: '/pages/login/login' })
		},
		}
}
</script>

<style scoped>
.forgot-container {
	min-height: 100vh;
	background: #FFFFFF;
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

.logo-section {
	text-align: center;
	padding: 32px 24px 24px;
}

.logo-box {
	width: 72px;
	height: 72px;
	background: linear-gradient(135deg, #10B981, #34D399);
	border-radius: 50%;
	margin: 0 auto 16px;
	display: flex;
	align-items: center;
	justify-content: center;
	font-size: 36px;
	box-shadow: 0 10px 28px rgba(16, 185, 129, 0.25);
}

.logo-title {
	font-size: 22px;
	font-weight: 900;
	color: #1E293B;
	display: block;
	margin-bottom: 6px;
	letter-spacing: -0.5px;
}

.logo-subtitle {
	font-size: 14px;
	color: #64748B;
	font-weight: 500;
}

.form-card {
	margin: 0 24px;
	padding: 28px 24px 32px;
}

.step-indicator {
	display: flex;
	align-items: center;
	justify-content: center;
	margin-bottom: 32px;
}

.step-item {
	display: flex;
	flex-direction: column;
	align-items: center;
	gap: 6px;
}

.step-circle {
	width: 32px;
	height: 32px;
	border-radius: 50%;
	background: #E2E8F0;
	color: #94A3B8;
	font-size: 14px;
	font-weight: 700;
	display: flex;
	align-items: center;
	justify-content: center;
	transition: all 0.3s;
}

.step-item.active .step-circle {
	background: linear-gradient(135deg, #10B981, #059669);
	color: #FFFFFF;
	box-shadow: 0 6px 16px rgba(16, 185, 129, 0.3);
}

.step-item.completed .step-circle {
	background: #10B981;
	color: #FFFFFF;
}

.step-label {
	font-size: 11px;
	color: #94A3B8;
	font-weight: 600;
	white-space: nowrap;
}

.step-item.active .step-label {
	color: #10B981;
}

.step-line {
	width: 40px;
	height: 2px;
	background: #E2E8F0;
	margin: 0 8px;
	margin-bottom: 20px;
	transition: all 0.3s;
}

.step-line.active {
	background: #10B981;
}

.step-content {
	animation: fadeIn 0.3s ease;
}

@keyframes fadeIn {
	from { opacity: 0; transform: translateY(10px); }
	to { opacity: 1; transform: translateY(0); }
}

.input-group {
	margin-bottom: 16px;
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

.input-icon {
	font-size: 18px;
	width: 20px;
	text-align: center;
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

.toggle-pwd {
	font-size: 18px;
	cursor: pointer;
	padding: 4px;
}

.code-wrapper {
	padding-right: 8px;
}

.code-btn {
	font-size: 13px;
	font-weight: 700;
	color: #10B981;
	background: transparent;
	border: none;
	padding: 8px 12px;
	white-space: nowrap;
	cursor: pointer;
}

.code-btn.disabled {
	color: #94A3B8;
	cursor: not-allowed;
}

.tips-card {
	background: #F0FDF4;
	border-radius: 12px;
	padding: 14px 16px;
	margin-bottom: 20px;
}

.tips-title {
	font-size: 12px;
	color: #059669;
	font-weight: 700;
	display: block;
	margin-bottom: 6px;
}

.tips-item {
	font-size: 12px;
	color: #64748B;
	display: block;
	margin-bottom: 2px;
}

.btn-primary {
	width: 100%;
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

.btn-primary:active {
	transform: translateY(-2px);
	box-shadow: 0 12px 32px rgba(16, 185, 129, 0.4);
}

.success-content {
	text-align: center;
	padding: 20px 0;
}

.success-icon {
	width: 80px;
	height: 80px;
	background: linear-gradient(135deg, #10B981, #34D399);
	border-radius: 50%;
	margin: 0 auto 24px;
	display: flex;
	align-items: center;
	justify-content: center;
	font-size: 40px;
	color: #FFFFFF;
	box-shadow: 0 12px 32px rgba(16, 185, 129, 0.3);
}

.success-title {
	font-size: 22px;
	font-weight: 900;
	color: #1E293B;
	display: block;
	margin-bottom: 8px;
}

.success-subtitle {
	font-size: 14px;
	color: #64748B;
	display: block;
	margin-bottom: 24px;
}

.countdown-card {
	background: #F8FAFC;
	border-radius: 12px;
	padding: 14px;
	margin-bottom: 24px;
}

.countdown-text {
	font-size: 14px;
	color: #64748B;
	font-weight: 600;
}
</style>