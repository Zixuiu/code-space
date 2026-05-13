<template>
	<view class="container">
		<view class="header">
			
			<text class="header-title">充值</text>
			<view class="header-right"></view>
		</view>

		<scroll-view class="content-scroll" scroll-y>
			<view class="balance-card">
				<text class="balance-label">当前余额</text>
				<view class="balance-amount">
					<text class="currency">¥</text>
					<text class="amount">{{ currentBalance }}</text>
				</view>
			</view>

			<view class="section-title">选择充值金额</view>
			<view class="amount-grid">
				<view
					v-for="item in amountOptions"
					:key="item"
					class="amount-item"
					:class="{ selected: selectedAmount === item }"
					@click="selectAmount(item)"
				>
					<text class="amount-value">{{ item }}</text>
					<text class="amount-unit">元</text>
				</view>
			</view>

			<view class="custom-amount">
				<text class="custom-label">自定义金额</text>
				<view class="custom-input-wrapper">
					<text class="custom-prefix">¥</text>
					<input
						class="custom-input"
						v-model="customAmount"
						type="digit"
						placeholder="请输入金额"
						@input="onCustomInput"
					/>
				</view>
			</view>

			<view class="section-title">选择支付方式</view>
			<view class="payment-methods">
				<view
					class="method-item"
					:class="{ selected: paymentMethod === 'wechat' }"
					@click="selectPayment('wechat')"
				>
					<view class="method-icon wechat">
						<IconFont name="wechat" :size="24" />
					</view>
					<view class="method-info">
						<text class="method-name">微信支付</text>
						<text class="method-desc">推荐</text>
					</view>
					<view class="method-check" v-if="paymentMethod === 'wechat'">
						<IconFont name="check-circle" :size="22" />
					</view>
					<view class="method-radio" v-else></view>
				</view>

				<view
					class="method-item"
					:class="{ selected: paymentMethod === 'alipay' }"
					@click="selectPayment('alipay')"
				>
					<view class="method-icon alipay">
						<IconFont name="alipay" :size="24" />
					</view>
					<view class="method-info">
						<text class="method-name">支付宝</text>
						<text class="method-desc">安全便捷</text>
					</view>
					<view class="method-check" v-if="paymentMethod === 'alipay'">
						<IconFont name="check-circle" :size="22" />
					</view>
					<view class="method-radio" v-else></view>
				</view>
			</view>

			<view class="tip-card">
				<IconFont name="info-circle" :size="16" class="tip-icon" />
				<text class="tip-text">充值金额将直接到账钱包，可用于发布需求、支付订单等</text>
			</view>

			<button
				class="recharge-btn"
				:class="{ disabled: !canRecharge }"
				@click="handleRecharge"
				:disabled="!canRecharge || isProcessing"
			>
				<view v-if="isProcessing" class="spinner"></view>
				<text v-else>立即充值 ¥{{ finalAmount }}</text>
			</button>

			<view class="bottom-space"></view>
		</scroll-view>
	</view>
</template>

<script>
import { useUserStore } from '@/store/user'
import { walletApi } from '@/api/wallet'
import paymentService from '@/utils/payment'
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
			currentBalance: '0.00',
			selectedAmount: 100,
			customAmount: '',
			paymentMethod: 'wechat',
			amountOptions: [10, 50, 100, 200, 500, 1000],
			isProcessing: false
		}
	},
	computed: {
		finalAmount() {
			if (this.customAmount) {
				return this.customAmount
			}
			return this.selectedAmount
		},
		canRecharge() {
			const amount = parseFloat(this.finalAmount)
			return amount > 0
		}
	},
	async onLoad() {
		await this.loadBalance()
	},
	async onShow() {
		uni.hideTabBar()
		await this.loadBalance()
	},
	methods: {
		async loadBalance() {
			try {
				const wallet = await this.userStore.fetchWalletInfo()
				this.currentBalance = wallet.balance?.toFixed(2) || '0.00'
			} catch (e) {
				const walletKey = `wallet_${this.userStore.currentUser.id}`
				const wallet = uni.getStorageSync(walletKey) || {}
				this.currentBalance = wallet.balance?.toFixed(2) || '0.00'
			}
		},
		selectAmount(amount) {
			this.selectedAmount = amount
			this.customAmount = ''
		},
		onCustomInput() {
			this.selectedAmount = null
		},
		selectPayment(method) {
			this.paymentMethod = method
		},
		handleRecharge() {
			if (!this.canRecharge) return

			const payPassword = uni.getStorageSync('payPassword')
			if (!payPassword) {
				uni.showModal({
					title: '提示',
					content: '您还未设置支付密码，请先设置',
					confirmColor: '#10B981',
					success: (res) => {
						if (res.confirm) {
							uni.navigateTo({ url: '/pages/payment-password/payment-password' })
						}
					}
				})
				return
			}

			uni.navigateTo({
				url: `/pages/payment-verify/payment-verify?amount=${this.finalAmount}&title=钱包充值验证`
			})
		},
		onPaymentVerifySuccess() {
			this.executeRecharge()
		},
		async executeRecharge() {
			this.isProcessing = true

			try {
				const amount = parseFloat(this.finalAmount)

				const payMethod = this.paymentMethod === 'wechat' ? 'wx' : 'ali'

				const result = await paymentService.recharge(amount, payMethod)

				if (result.payOrder) {
					await paymentService[payMethod === 'wx' ? 'wechatPayment' : 'alipayPayment'](result.payOrder)
				}

				await this.userStore.fetchWalletInfo()
				this.currentBalance = this.userStore.walletBalance.toFixed(2)

				const transactions = uni.getStorageSync('walletTransactions') || []
				transactions.unshift({
					id: Date.now(),
					type: 'income',
					title: '钱包充值',
					amount: amount,
					time: Date.now()
				})
				uni.setStorageSync('walletTransactions', transactions)

				this.isProcessing = false
				this.closePasswordVerify()
				uni.showToast({ title: '充值成功', icon: 'success' })
			} catch (e) {
				this.isProcessing = false
				if (e.errMsg?.includes('cancel')) {
					return
				}
				uni.showToast({ title: e.message || '充值失败', icon: 'none' })
			}
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

.balance-card {
	background: linear-gradient(135deg, #10B981, #059669);
	border-radius: 24rpx;
	padding: 32rpx;
	text-align: center;
	margin-bottom: 32rpx;
}

.balance-label {
	font-size: 26rpx;
	color: rgba(255, 255, 255, 0.8);
	display: block;
	margin-bottom: 12rpx;
}

.balance-amount {
	display: flex;
	align-items: baseline;
	justify-content: center;
}

.currency {
	font-size: 32rpx;
	font-weight: 700;
	color: #FFFFFF;
}

.amount {
	font-size: 56rpx;
	font-weight: 800;
	color: #FFFFFF;
}

.section-title {
	font-size: 28rpx;
	font-weight: 700;
	color: #1E293B;
	margin-bottom: 20rpx;
}

.amount-grid {
	display: grid;
	grid-template-columns: repeat(3, 1fr);
	gap: 16rpx;
	margin-bottom: 24rpx;
}

.amount-item {
	background: #FFFFFF;
	border-radius: 16rpx;
	padding: 28rpx 0;
	text-align: center;
	border: 2rpx solid #E2E8F0;
	transition: all 0.2s;
}

.amount-item.selected {
	border-color: #10B981;
	background: #F0FDF4;
}

.amount-value {
	font-size: 36rpx;
	font-weight: 800;
	color: #1E293B;
	display: block;
}

.amount-unit {
	font-size: 22rpx;
	color: #94A3B8;
}

.amount-item.selected .amount-value {
	color: #10B981;
}

.custom-amount {
	margin-bottom: 32rpx;
}

.custom-label {
	font-size: 26rpx;
	color: #64748B;
	display: block;
	margin-bottom: 12rpx;
}

.custom-input-wrapper {
	background: #FFFFFF;
	border-radius: 16rpx;
	padding: 24rpx;
	display: flex;
	align-items: center;
	border: 2rpx solid #E2E8F0;
}

.custom-prefix {
	font-size: 36rpx;
	font-weight: 700;
	color: #1E293B;
	margin-right: 12rpx;
}

.custom-input {
	flex: 1;
	font-size: 32rpx;
	font-weight: 700;
	color: #1E293B;
	border: none;
	outline: none;
	background: transparent;
}

.payment-methods {
	margin-bottom: 24rpx;
}

.method-item {
	background: #FFFFFF;
	border-radius: 16rpx;
	padding: 24rpx;
	margin-bottom: 12rpx;
	display: flex;
	align-items: center;
	border: 2rpx solid #E2E8F0;
	transition: all 0.2s;
}

.method-item.selected {
	border-color: #10B981;
}

.method-icon {
	width: 72rpx;
	height: 72rpx;
	border-radius: 16rpx;
	display: flex;
	align-items: center;
	justify-content: center;
	margin-right: 16rpx;
}

.method-icon.wechat {
	background: #F0FDF4;
	color: #07C160;
}

.method-icon.alipay {
	background: #EFF6FF;
	color: #1677FF;
}

.method-info {
	flex: 1;
}

.method-name {
	font-size: 28rpx;
	font-weight: 700;
	color: #1E293B;
	display: block;
	margin-bottom: 4rpx;
}

.method-desc {
	font-size: 22rpx;
	color: #94A3B8;
}

.method-check {
	color: #10B981;
}

.method-radio {
	width: 36rpx;
	height: 36rpx;
	border: 2rpx solid #CBD5E1;
	border-radius: 50%;
}

.tip-card {
	background: #F0FDF4;
	border-radius: 12rpx;
	padding: 16rpx 20rpx;
	display: flex;
	align-items: center;
	gap: 10rpx;
	margin-bottom: 32rpx;
}

.tip-icon {
	color: #10B981;
	flex-shrink: 0;
}

.tip-text {
	font-size: 24rpx;
	color: #059669;
}

.recharge-btn {
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

.recharge-btn.disabled {
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

.bottom-space {
	height: 40rpx;
}
</style>