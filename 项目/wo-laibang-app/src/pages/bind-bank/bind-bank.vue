<template>
	<view class="container">
		<view class="header">
			<text class="header-title">绑定银行卡</text>
			<view class="header-right"></view>
		</view>

		<scroll-view class="content-scroll" scroll-y>
			<view class="form-card">
				<view class="input-group">
					<label class="input-label">持卡人姓名</label>
					<view class="input-wrapper">
						<IconFont name="user" :size="32" class="input-icon" />
						<input
							class="input-field"
							v-model="form.name"
							type="text"
							placeholder="请输入持卡人姓名"
						/>
					</view>
				</view>

				<view class="input-group">
					<label class="input-label">银行卡号</label>
					<view class="input-wrapper">
						<IconFont name="credit-card" :size="32" class="input-icon" />
						<input
							class="input-field"
							v-model="form.cardNumber"
							type="number"
							placeholder="请输入银行卡号"
							@input="onCardNumberInput"
						/>
					</view>
					<text class="input-hint">请输入16位或19位银行卡号</text>
				</view>

				<view class="input-group">
					<label class="input-label">开户银行</label>
					<view class="input-wrapper" @click="showBankPicker">
						<IconFont name="home" :size="32" class="input-icon" />
						<input
							class="input-field"
							v-model="form.bankName"
							type="text"
							placeholder="请选择开户银行"
							disabled
						/>
						<IconFont name="chevron-right" :size="24" class="arrow" />
					</view>
				</view>

				<view class="input-group">
					<label class="input-label">开户支行</label>
					<view class="input-wrapper">
						<IconFont name="map-pin" :size="32" class="input-icon" />
						<input
							class="input-field"
							v-model="form.branchName"
							type="text"
							placeholder="请输入开户支行名称"
						/>
					</view>
				</view>
			</view>

			<view class="tip-card">
				<IconFont name="shield" :size="32" class="tip-icon" />
				<view class="tip-content">
					<text class="tip-title">安全提示</text>
					<text class="tip-text">银行卡信息仅用于提现操作，我们不会泄露您的隐私信息</text>
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

const BANKS = [
	{ name: '中国工商银行', code: 'ICBC' },
	{ name: '中国建设银行', code: 'CCB' },
	{ name: '中国农业银行', code: 'ABC' },
	{ name: '中国银行', code: 'BOC' },
	{ name: '交通银行', code: 'BCOM' },
	{ name: '招商银行', code: 'CMB' },
	{ name: '浦发银行', code: 'SPDB' },
	{ name: '中信银行', code: 'CITIC' },
	{ name: '光大银行', code: 'CEB' },
	{ name: '民生银行', code: 'CMBC' }
]

export default {
	components: {
		IconFont
	},
	data() {
		return {
			form: {
				name: '',
				cardNumber: '',
				bankName: '',
				bankCode: '',
				branchName: ''
			},
			isSubmitting: false,
			banks: BANKS
		}
	},
	computed: {
		canSubmit() {
			return this.form.name.trim() &&
				   this.form.cardNumber.length >= 16 &&
				   this.form.bankName.trim() &&
				   this.form.branchName.trim()
		}
	},
	methods: {
		onCardNumberInput(e) {
			const value = e.detail.value.replace(/\D/g, '')
			if (value.length > 19) {
				this.form.cardNumber = value.slice(0, 19)
			} else {
				this.form.cardNumber = value
			}
		},
		showBankPicker() {
			const bankNames = this.banks.map(b => b.name)
			uni.showActionSheet({
				itemList: bankNames,
				success: (res) => {
					const selected = this.banks[res.tapIndex]
					this.form.bankName = selected.name
					this.form.bankCode = selected.code
				}
			})
		},
		validateCardNumber() {
			const num = this.form.cardNumber
			if (!/^\d{16,19}$/.test(num)) return false

			let sum = 0
			let digit = 0
			let tmpNum = 0
			let shouldDouble = false

			for (let i = num.length - 1; i >= 0; i--) {
				digit = parseInt(num.charAt(i))
				tmpNum = shouldDouble ? digit * 2 : digit
				if (tmpNum > 9) tmpNum -= 9
				sum += tmpNum
				shouldDouble = !shouldDouble
			}

			return sum % 10 === 0
		},
		handleSubmit() {
			if (!this.canSubmit) return

			if (!this.validateCardNumber()) {
				uni.showToast({ title: '请输入正确的银行卡号', icon: 'none' })
				return
			}

			this.isSubmitting = true

			setTimeout(() => {
				const userInfo = uni.getStorageSync('userInfo') || {}
				userInfo.bindedBank = this.form.cardNumber.slice(-4)
				userInfo.bankName = this.form.bankName
				userInfo.bankBranch = this.form.branchName
				userInfo.bankCardName = this.form.name
				uni.setStorageSync('userInfo', userInfo)

				const currentUser = uni.getStorageSync('currentUser') || {}
				currentUser.bindedBank = this.form.cardNumber.slice(-4)
				currentUser.bankName = this.form.bankName
				currentUser.bankBranch = this.form.branchName
				currentUser.bankCardName = this.form.name
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
	font-size: 36rpx;
	font-weight: 800;
	color: #1E293B;
	text-align: center;
}

.header-right {
	width: 80rpx;
}

.content-scroll {
	height: calc(100vh - 178rpx);
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
	font-size: 24rpx;
	color: #64748B;
	font-weight: 700;
	text-transform: uppercase;
	letter-spacing: 1rpx;
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
	width: 40rpx;
	display: flex;
	align-items: center;
	justify-content: center;
	color: #64748B;
}

.input-field {
	flex: 1;
	font-size: 30rpx;
	font-weight: 600;
	color: #1E293B;
	border: none;
	outline: none;
	background: transparent;
}

.input-field:disabled {
	color: #1E293B;
}

.arrow {
	color: #94A3B8;
}

.input-hint {
	font-size: 24rpx;
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
	font-size: 28rpx;
	font-weight: 700;
	color: #059669;
	display: block;
	margin-bottom: 8rpx;
}

.tip-text {
	font-size: 24rpx;
	color: #64748B;
	line-height: 1.5;
}

.submit-btn {
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
