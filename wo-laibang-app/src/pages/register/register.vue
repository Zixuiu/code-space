<template>
	<view class="register-container">
		<view class="header">
			<text class="header-title">注册账号</text>
			<view class="header-right"></view>
		</view>

		<scroll-view class="content-scroll" scroll-y>
			<view class="logo-section">
				<view class="logo-box">
					<IconFont name="flower" :size="48" />
			</view>
				<text class="logo-title">创建账号</text>
				<text class="logo-subtitle">加入邻里互助大家庭</text>
			</view>

			<view class="form-card">
				<view class="input-group">
					<label class="input-label">昵称</label>
					<view class="input-wrapper">
						<IconFont name="user" :size="32" class="input-icon" />
						<input
							class="input-field"
							placeholder="请输入昵称"
							v-model="form.nickname"
							maxlength="20"
						/>
					</view>
				</view>

				<view class="input-group">
					<label class="input-label">手机号码</label>
					<view class="input-wrapper">
						<text class="input-icon"><IconFont name="phone" :size="32" /></text>
						<input
							class="input-field"
							placeholder="请输入手机号"
							v-model="form.phone"
							type="number"
							maxlength="11"
						/>
					</view>
				</view>

				<view class="input-group">
					<label class="input-label">验证码</label>
					<view class="input-wrapper code-wrapper">
						<IconFont name="sparkles" :size="32" class="input-icon" />
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

				<view class="input-group">
					<label class="input-label">登录密码</label>
					<view class="input-wrapper">
						<IconFont name="lock" :size="72" class="input-icon" />
						<input
							class="input-field"
							type="password"
							placeholder="请设置密码"
							:password="!showPassword"
							v-model="form.password"
						/>
						<view class="toggle-pwd" @click="showPassword = !showPassword">
							<IconFont :name="showPassword ? 'eye-off' : 'eye'" :size="72" />
						</view>
					</view>
				</view>

				<view class="input-group">
					<label class="input-label">确认密码</label>
					<view class="input-wrapper">
						<text class="input-icon"><IconFont name="lock" :size="72" /></text>
						<input
							class="input-field"
							type="password"
							placeholder="请再次输入密码"
							:password="!showConfirmPassword"
							v-model="form.confirmPassword"
						/>
						<view class="toggle-pwd" @click="showConfirmPassword = !showConfirmPassword">
							<IconFont :name="showConfirmPassword ? 'eye-off' : 'eye'" :size="72" />
						</view>
					</view>
				</view>

				<view v-if="form.password" class="strength-card">
					<label class="input-label">密码强度</label>
					<view class="strength-bars">
						<view class="strength-bar" :class="strengthClass" id="b1"></view>
						<view class="strength-bar" :class="strengthClass" id="b2"></view>
						<view class="strength-bar" :class="strengthClass" id="b3"></view>
					</view>
					<text class="strength-text" :class="strengthClass">{{ strengthText }}</text>
				</view>

				<view class="rules-card">
					<view class="rule-item" :class="{ valid: ruleLength }">
						<text class="rule-icon">{{ ruleLength ? '✅' : '⚪' }}</text>
						<text>至少8个字符</text>
					</view>
					<view class="rule-item" :class="{ valid: ruleUpper }">
						<text class="rule-icon">{{ ruleUpper ? '✔️' : '⚪' }}</text>
						<text>包含大写字母</text>
					</view>
					<view class="rule-item" :class="{ valid: ruleNumber }">
						<text class="rule-icon">{{ ruleNumber ? '✅' : '⚪' }}</text>
						<text>包含数字</text>
					</view>
					<view class="rule-item" :class="{ valid: ruleSpecial }">
						<text class="rule-icon">{{ ruleSpecial ? '✅' : '⚪' }}</text>
						<text>包含特殊字符</text>
					</view>
				</view>

				<view class="agreement-row">
					<view class="checkbox-wrap" :class="{ checked: agreed }" @click="agreed = !agreed">
						<text v-if="agreed" class="check-icon">✅</text>
					</view>
					<text class="agreement-text">
						我已阅读并同意
						<text class="link" @click.stop="showAgreement">《用户协议》</text>
						和
						<text class="link" @click.stop="showPrivacy">《隐私政策》</text>
					</text>
				</view>

				<button class="btn-primary" @click="handleRegister" :class="{ disabled: !agreed || isSubmitting }">
					<view v-if="isSubmitting" class="spinner"></view>
					<text v-else>注 册</text>
				</button>

				<view class="login-link">
					<text class="link-prefix">已有账号？</text>
					<text class="link-action" @click="goLogin">立即登录</text>
				</view>
			</view>

			<view class="bottom-safe"></view>
		</scroll-view>
	</view>
</template>

<script>
import { userApi } from '@/api/user'
import IconFont from '@/components/icon-font/icon-font.vue'

export default {
	components: {
		IconFont
	},
	data() {
		return {
			form: {
				nickname: '',
				phone: '',
				code: '',
				password: '',
				confirmPassword: ''
			},
			agreed: false,
			counting: false,
			count: 60,
			isSubmitting: false,
			showPassword: false,
			showConfirmPassword: false
		}
	},
	computed: {
		ruleLength() {
			return this.form.password.length >= 8
		},
		ruleUpper() {
			return /[A-Z]/.test(this.form.password)
		},
		ruleNumber() {
			return /[0-9]/.test(this.form.password)
		},
		ruleSpecial() {
			return /[!@#$%^&*(),.?":{}|<>]/.test(this.form.password)
		},
		strengthClass() {
			const score = [this.ruleLength, this.ruleUpper, this.ruleNumber, this.ruleSpecial].filter(v => v).length
			if (score <= 1) return 'weak'
			if (score <= 2) return 'medium'
			return 'strong'
		},
		strengthText() {
			const score = [this.ruleLength, this.ruleUpper, this.ruleNumber, this.ruleSpecial].filter(v => v).length
			if (score <= 1) return '弱'
			if (score <= 2) return '中等'
			if (score <= 3) return '良好'
			return '强'
		}
	},
	methods: {
		async sendCode() {
			if (this.counting) return
			if (!/^1[3-9]\d{9}$/.test(this.form.phone)) {
				uni.showToast({ title: '请输入正确的手机号', icon: 'none' })
				return
			}

			try {
				await userApi.getCaptcha(this.form.phone)
				uni.showToast({ title: '验证码已发送', icon: 'success' })
			} catch (err) {
				uni.showToast({ title: '验证码发送失败', icon: 'none' })
			}

			this.counting = true
			const timer = setInterval(() => {
				this.count--
				if (this.count <= 0) {
					clearInterval(timer)
					this.counting = false
					this.count = 60
				}
			}, 1000)
		},
		validate() {
			if (!this.form.nickname.trim()) {
				uni.showToast({ title: '请输入昵称', icon: 'none' })
				return false
			}

			const registeredUsers = uni.getStorageSync('registeredUsers') || []
			const isNicknameTaken = registeredUsers.some(user =>
				user.nickname.toLowerCase() === this.form.nickname.trim().toLowerCase()
			)
			if (isNicknameTaken) {
				uni.showToast({ title: '该昵称已被占用', icon: 'none' })
				return false
			}

			if (!/^1[3-9]\d{9}$/.test(this.form.phone)) {
				uni.showToast({ title: '请输入正确的手机号', icon: 'none' })
				return false
			}
			if (!/^\d{6}$/.test(this.form.code)) {
				uni.showToast({ title: '请输入6位验证码', icon: 'none' })
				return false
			}
			if (this.form.password.length < 8) {
				uni.showToast({ title: '密码长度至少为8位', icon: 'none' })
				return false
			}
			if (this.form.password !== this.form.confirmPassword) {
				uni.showToast({ title: '两次输入的密码不一致', icon: 'none' })
				return false
			}
			if (!this.agreed) {
				uni.showToast({ title: '请同意用户协议和隐私政策', icon: 'none' })
				return false
			}
			return true
		},
		async handleRegister() {
			if (!this.validate()) return

			this.isSubmitting = true
			uni.showLoading({ title: '注册中...' })

			try {
				await userApi.register({
					nickname: this.form.nickname,
					phone: this.form.phone,
					password: this.form.password,
					code: this.form.code
				})

				uni.hideLoading()
				uni.showToast({
					title: '注册成功',
					icon: 'success'
				})

				setTimeout(() => {
					uni.navigateBack()
				}, 1500)
			} catch (err) {
				uni.hideLoading()
				this.fallbackMockRegister()
			} finally {
				this.isSubmitting = false
			}
		},
		fallbackMockRegister() {
			const userInfo = {
				id: Date.now(),
				nickname: this.form.nickname,
				phone: this.form.phone,
				reputation: 100,
				completedOrders: 0
			}
			uni.setStorageSync('currentUser', userInfo)

			const registeredUsers = uni.getStorageSync('registeredUsers') || []
			registeredUsers.push(userInfo)
			uni.setStorageSync('registeredUsers', registeredUsers)

			uni.showToast({
				title: '注册成功(模拟)',
				icon: 'success'
			})

			setTimeout(() => {
				uni.navigateBack()
			}, 1500)
		},
		showAgreement() {
			uni.navigateTo({
				url: '/pages/terms-of-service/terms-of-service'
			})
		},
		showPrivacy() {
			uni.navigateTo({
				url: '/pages/privacy-policy/privacy-policy'
			})
		},
		goLogin() {
			uni.navigateBack()
		},
		}
}
</script>

<style scoped>
.register-container {
	min-height: 100vh;
	background: #FFFFFF;
}

.header {
	display: flex;
	align-items: center;
	justify-content: space-between;
	padding: 44px 24px 20px;
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
	padding: 32px 24px 28px;
}

.logo-box {
	width: 72px;
	height: 72px;
	background: linear-gradient(135deg, #10B981, #34D399);
	border-radius: 22px;
	margin: 0 auto 16px;
	display: flex;
	align-items: center;
	justify-content: center;
	box-shadow: 0 10px 28px rgba(16, 185, 129, 0.25);
}

.logo-title {
	font-size: 24px;
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
	width: 20px;
	display: flex;
	align-items: center;
	justify-content: center;
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
	cursor: pointer;
	padding: 4px;
	display: flex;
	align-items: center;
	justify-content: center;
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

.strength-card {
	margin-bottom: 16px;
}

.strength-bars {
	display: flex;
	gap: 6px;
	margin-bottom: 6px;
}

.strength-bar {
	flex: 1;
	height: 4px;
	background: #E2E8F0;
	border-radius: 2px;
	transition: all 0.3s;
}

.strength-bar.weak { background: #EF4444; }
.strength-bar.medium { background: #F59E0B; }
.strength-bar.strong { background: #10B981; }

.strength-text {
	font-size: 12px;
	font-weight: 600;
}

.strength-text.weak { color: #EF4444; }
.strength-text.medium { color: #F59E0B; }
.strength-text.strong { color: #10B981; }

.rules-card {
	background: #F8FAFC;
	border-radius: 12px;
	padding: 12px 14px;
	margin-bottom: 20px;
}

.rule-item {
	display: flex;
	align-items: center;
	gap: 8px;
	font-size: 12px;
	color: #64748B;
	margin-bottom: 6px;
}

.rule-item:last-child {
	margin-bottom: 0;
}

.rule-icon {
	width: 16px;
	height: 16px;
	border-radius: 50%;
	display: flex;
	align-items: center;
	justify-content: center;
	font-size: 10px;
	font-weight: 800;
	background: #E2E8F0;
	color: white;
	transition: all 0.2s;
}

.rule-item.valid .rule-icon {
	background: #10B981;
}

.agreement-row {
	display: flex;
	align-items: flex-start;
	gap: 12px;
	margin-bottom: 24px;
}

.checkbox-wrap {
	width: 22px;
	height: 22px;
	border-radius: 6px;
	border: 2px solid #E2E8F0;
	display: flex;
	align-items: center;
	justify-content: center;
	flex-shrink: 0;
	margin-top: 2px;
	transition: all 0.2s;
}

.checkbox-wrap.checked {
	background: linear-gradient(135deg, #10B981, #059669);
	border-color: transparent;
}

.check-icon {
	color: #FFFFFF;
	font-size: 14px;
	font-weight: bold;
}

.agreement-text {
	font-size: 13px;
	color: #64748B;
	line-height: 1.5;
	flex: 1;
}

.link {
	color: #10B981;
	font-weight: 700;
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

.btn-primary.disabled {
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

.login-link {
	display: flex;
	justify-content: center;
	align-items: center;
	margin-top: 24px;
}

.link-prefix {
	font-size: 14px;
	color: #64748B;
}

.link-action {
	font-size: 14px;
	color: #10B981;
	font-weight: 700;
	margin-left: 4px;
}

.bottom-safe {
	height: 40px;
}
</style>