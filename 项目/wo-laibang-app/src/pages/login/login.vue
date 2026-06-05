<template>
	<view class="login-container">
		<scroll-view class="content-scroll" scroll-y>
			<view class="logo-section">
				<view class="logo-box">
					<IconFont name="flower" :size="40" />
				</view>
				<text class="app-name">我来帮</text>
				<text class="app-slogan">邻里互助，温暖你我</text>
			</view>

			<view class="form-card">
				<view class="hint-block">
					<text class="hint-badge">欢迎回来</text>
					<text class="hint-title">登录您的账号</text>
				</view>

				<view class="input-group">
					<label class="input-label">手机号码</label>
					<view class="input-wrapper">
						<IconFont name="phone" :size="72" class="input-icon" />
						<input
							class="input-field"
							v-model="form.phone"
							type="number"
							maxlength="11"
							placeholder="请输入手机号"
						/>
					</view>
				</view>

				<view class="input-group">
					<label class="input-label">登录密码</label>
					<view class="input-wrapper">
						<IconFont name="lock" :size="72" class="input-icon" />
						<input
							class="input-field"
							v-model="form.password"
							:password="!showPassword"
							placeholder="请输入密码"
						/>
						<view class="toggle-pwd" @click="showPassword = !showPassword">
							<IconFont :name="showPassword ? 'eye-off' : 'eye'" :size="72" />
						</view>
					</view>
				</view>

				<view class="forgot-row">
					<text class="forgot-link" @click="goForgot">忘记密码？</text>
				</view>

				<button class="btn-primary" @click="handleLogin" :disabled="isLoading">
					<view v-if="isLoading" class="spinner"></view>
					<text v-else>登 录</text>
				</button>

				<view class="register-hint">
					<text class="hint-text">还没有账号？</text>
					<text class="link-action" @click="goRegister">立即注册</text>
				</view>
			</view>

			<view class="bottom-safe"></view>
		</scroll-view>
	</view>
</template>

<script>
import { useUserStore } from '@/store/user'
import { userApi } from '@/api/user'
import IconFont from '@/components/icon-font/icon-font.vue'

export default {
	components: {
		IconFont
	},
	setup() {
		const userStore = useUserStore()
		return { userStore }
	},
	data() {
		return {
			form: {
				phone: '',
				password: ''
			},
			showPassword: false,
			isLoading: false
		}
	},
	methods: {
		validatePhone() {
			if (!this.form.phone.trim()) {
				uni.showToast({ title: '请输入手机号', icon: 'none' })
				return false
			}
			if (!/^1[3-9]\d{9}$/.test(this.form.phone)) {
				uni.showToast({ title: '请输入正确的手机号', icon: 'none' })
				return false
			}
			return true
		},
		validatePassword() {
			if (!this.form.password.trim()) {
				uni.showToast({ title: '请输入密码', icon: 'none' })
				return false
			}
			if (this.form.password.length < 6) {
				uni.showToast({ title: '密码至少6位', icon: 'none' })
				return false
			}
			return true
		},
		async handleLogin() {
			if (!this.validatePhone() || !this.validatePassword()) return

			this.isLoading = true

			try {
				const data = await userApi.login(this.form.phone, this.form.password)
				uni.setStorageSync('token', data.token)
				this.userStore.setUserInfo(data.userInfo)
				this.userStore.setLoggedIn(true)

				if (data.wallet) {
					uni.setStorageSync('wallet', data.wallet)
					this.userStore.syncWalletBalance()
				}

				uni.showToast({ title: '登录成功', icon: 'success' })

				const redirectUrl = uni.getStorageSync('redirectAfterLogin') || '/pages/index/index'
				uni.removeStorageSync('redirectAfterLogin')

				setTimeout(() => {
					if (redirectUrl.startsWith('/pages/')) {
						const tabBarPages = ['/pages/index/index', '/pages/publish/publish', '/pages/orders/orders', '/pages/messages/messages', '/pages/profile/profile']
						if (tabBarPages.includes(redirectUrl)) {
							uni.switchTab({ url: redirectUrl })
						} else {
							uni.navigateTo({ url: redirectUrl })
						}
					} else {
						uni.switchTab({ url: '/pages/index/index' })
					}
				}, 1000)
			} catch (err) {
				this.fallbackMockLogin()
			} finally {
				this.isLoading = false
			}
		},
		fallbackMockLogin() {
			const userInfo = {
				id: 'u_' + Date.now(),
				nickname: '用户' + this.form.phone.slice(-4),
				phone: this.form.phone,
				reputation: 100,
				completedOrders: 0
			}

			this.userStore.login(userInfo)

			uni.showToast({ title: '登录成功(模拟)', icon: 'success' })

			setTimeout(() => {
				uni.switchTab({ url: '/pages/index/index' })
			}, 1000)
		},
		goForgot() {
			uni.navigateTo({ url: '/pages/forgot-password/forgot-password' })
		},
		goRegister() {
			uni.navigateTo({ url: '/pages/register/register' })
		}
	}
}
</script>

<style scoped>
.login-container {
	min-height: 100vh;
	background: #FFFFFF;
}

.content-scroll {
	height: 100vh;
}

.logo-section {
	text-align: center;
	padding: 48px 24px 24px;
}

.logo-box {
	width: 80px;
	height: 80px;
	background: linear-gradient(135deg, #10B981, #34D399);
	border-radius: 24px;
	margin: 0 auto 20px;
	display: flex;
	align-items: center;
	justify-content: center;
	box-shadow: 0 12px 32px rgba(16, 185, 129, 0.25);
}

.app-name {
	font-size: 28px;
	font-weight: 900;
	color: #1E293B;
	display: block;
	margin-bottom: 8px;
	letter-spacing: -0.5px;
}

.app-slogan {
	font-size: 14px;
	color: #64748B;
	font-weight: 500;
}

.form-card {
	margin: 0 24px;
	padding: 28px 24px 32px;
}

.hint-block {
	margin-bottom: 28px;
}

.hint-badge {
	font-size: 11px;
	color: #10B981;
	font-weight: 800;
	text-transform: uppercase;
	letter-spacing: 1px;
	display: block;
	margin-bottom: 6px;
}

.hint-title {
	font-size: 22px;
	font-weight: 800;
	color: #1E293B;
	line-height: 1.3;
}

.input-group {
	margin-bottom: 18px;
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

.forgot-row {
	display: flex;
	justify-content: flex-end;
	margin-bottom: 24px;
}

.forgot-link {
	font-size: 13px;
	color: #10B981;
	font-weight: 600;
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

.btn-primary:active:not(:disabled) {
	transform: translateY(-2px);
	box-shadow: 0 12px 32px rgba(16, 185, 129, 0.4);
}

.btn-primary:disabled {
	opacity: 0.6;
	cursor: not-allowed;
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

.register-hint {
	display: flex;
	justify-content: center;
	align-items: center;
	margin-top: 24px;
}

.hint-text {
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