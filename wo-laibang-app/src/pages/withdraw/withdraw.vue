<template>
	<view class="container">
		<view class="header">
			<text class="header-title">提现</text>
			<view class="header-right"></view>
		</view>

		<scroll-view class="content-scroll" scroll-y>
			<view class="balance-card">
				<text class="balance-label">可提现余额</text>
				<view class="balance-amount">
					<text class="currency">¥</text>
					<text class="amount">{{ currentBalance }}</text>
				</view>
			</view>

			<view class="section-title">提现金额</view>
			<view class="amount-input-wrapper">
				<text class="amount-prefix">¥</text>
				<input
					class="amount-input"
					v-model="withdrawAmount"
					type="digit"
					placeholder="请输入提现金额"
					@input="onAmountInput"
				/>
			</view>

			<view class="quick-amounts">
				<view
					v-for="item in quickAmounts"
					:key="item"
					class="quick-item"
					:class="{ selected: selectedQuick === item }"
					@click="selectQuick(item)"
				>
					{{ item }}
				</view>
			</view>

			<view class="withdraw-info">
				<view class="info-row">
					<text class="info-label">最低提现金额</text>
					<text class="info-value">¥10.00</text>
				</view>
				<view class="info-row">
					<text class="info-label">实际到账</text>
					<text class="info-value highlight">¥{{ actualAmount }}</text>
				</view>
				<view class="info-row">
					<text class="info-label">手续费</text>
					<text class="info-value">¥0.00</text>
				</view>
			</view>

			<view class="section-title">选择到账方式</view>
			<view class="withdraw-methods">
				<view
					class="method-item"
					:class="{ selected: withdrawMethod === 'alipay' }"
					@click="selectMethod('alipay')"
				>
					<view class="method-icon alipay">
						<IconFont name="alipay" :size="24" />
					</view>
					<view class="method-info">
						<text class="method-name">支付宝</text>
						<text class="method-desc">{{ bindedAlipay ? '已绑定 ' + bindedAlipay : '未绑定' }}</text>
					</view>
					<view class="method-arrow" @click.stop="bindAlipay">
						<IconFont name="chevron-right" :size="18" />
					</view>
				</view>

				<view
					class="method-item"
					:class="{ selected: withdrawMethod === 'bank' }"
					@click="selectMethod('bank')"
				>
					<view class="method-icon bank">
						<IconFont name="credit-card" :size="24" />
					</view>
					<view class="method-info">
						<text class="method-name">银行卡</text>
						<text class="method-desc">{{ bindedBank ? '已绑定 ****' + bindedBank : '未绑定' }}</text>
					</view>
					<view class="method-arrow" @click.stop="bindBank">
						<IconFont name="chevron-right" :size="18" />
					</view>
				</view>
			</view>

			<view class="tip-card">
				<IconFont name="info-circle" :size="16" class="tip-icon" />
				<text class="tip-text">提现申请提交后，预计1-3个工作日到账</text>
			</view>

			<button
				class="withdraw-btn"
				:class="{ disabled: !canWithdraw }"
				@click="handleWithdraw"
				:disabled="!canWithdraw || isProcessing"
			>
				<view v-if="isProcessing" class="spinner"></view>
				<text v-else>立即提现 ¥{{ withdrawAmount || '0' }}</text>
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
			withdrawAmount: '',
			selectedQuick: null,
			withdrawMethod: 'alipay',
			bindedAlipay: '',
			bindedBank: '',
			isProcessing: false,
			quickAmounts: [50, 100, 200, 500, 1000]
		}
	},
	computed: {
		actualAmount() {
			const amount = parseFloat(this.withdrawAmount) || 0
			return amount.toFixed(2)
		},
		canWithdraw() {
			const amount = parseFloat(this.withdrawAmount)
			if (!amount || amount < 10) return false
			if (amount > parseFloat(this.currentBalance)) return false
			if (!this.withdrawMethod) return false
			return true
		}
	},
	async onLoad() {
		await this.loadData()
	},
	async onShow() {
		uni.hideTabBar()
		await this.loadData()
	},
	methods: {
		async loadData() {
			try {
				const wallet = await this.userStore.fetchWalletInfo()
				this.currentBalance = wallet.balance?.toFixed(2) || '0.00'
			} catch (e) {
				const walletKey = `wallet_${this.userStore.currentUser.id}`
				const wallet = uni.getStorageSync(walletKey) || {}
				this.currentBalance = wallet.balance?.toFixed(2) || '0.00'
			}

			const userInfo = uni.getStorageSync('userInfo') || {}
			this.bindedAlipay = userInfo.bindedAlipay || ''
			this.bindedBank = userInfo.bindedBank || ''
		},
		onAmountInput() {
			this.selectedQuick = null
		},
		selectQuick(amount) {
			this.withdrawAmount = amount.toString()
			this.selectedQuick = amount
		},
		selectMethod(method) {
			this.withdrawMethod = method
		},
		bindAlipay() {
			uni.navigateTo({ url: '/pages/bind-alipay/bind-alipay' })
		},
		bindBank() {
			uni.navigateTo({ url: '/pages/bind-bank/bind-bank' })
		},
		handleWithdraw() {
			if (!this.canWithdraw) return

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
				url: `/pages/payment-verify/payment-verify?amount=${this.withdrawAmount}&title=提现验证`
			})
		},
		onPaymentVerifySuccess() {
			this.executeWithdraw()
		},
		async executeWithdraw() {
			this.isProcessing = true

			try {
				const amount = parseFloat(this.withdrawAmount)
				const account = this.withdrawMethod === 'alipay' ? this.bindedAlipay : this.bindedBank
				const accountType = this.withdrawMethod === 'alipay' ? 'alipay' : 'bank'

				await walletApi.withdraw(amount, account, accountType)

				this.currentBalance = (parseFloat(this.currentBalance) - amount).toFixed(2)
				this.userStore.updateWalletBalance(parseFloat(this.currentBalance))

				const transactions = uni.getStorageSync('walletTransactions') || []
				transactions.unshift({
					id: Date.now(),
					type: 'expense',
					title: '提现到' + (this.withdrawMethod === 'alipay' ? '支付宝' : '银行卡'),
					amount: amount,
					time: Date.now(),
					status: 'pending'
				})
				uni.setStorageSync('walletTransactions', transactions)

				const notifications = uni.getStorageSync('notifications') || []
				notifications.unshift({
					id: Date.now(),
					type: 'system',
					title: '提现申请已提交',
					content: `提现 ¥${amount} 申请已提交，预计1-3个工作日到账`,
					read: false,
					createdAt: Date.now()
				})
				uni.setStorageSync('notifications', notifications)

				this.isProcessing = false
				uni.showToast({ title: '提现申请已提交', icon: 'success' })

				setTimeout(() => {
					uni.navigateBack()
				}, 1500)
			} catch (e) {
				this.isProcessing = false
				uni.showToast({ title: e.message || '提现失败', icon: 'none' })
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

.amount-input-wrapper {
	background: #FFFFFF;
	border-radius: 16rpx;
	padding: 24rpx;
	display: flex;
	align-items: center;
	border: 2rpx solid #E2E8F0;
	margin-bottom: 20rpx;
}

.amount-prefix {
	font-size: 48rpx;
	font-weight: 700;
	color: #1E293B;
	margin-right: 12rpx;
}

.amount-input {
	flex: 1;
	font-size: 40rpx;
	font-weight: 700;
	color: #1E293B;
	border: none;
	outline: none;
	background: transparent;
}

.quick-amounts {
	display: flex;
	gap: 12rpx;
	margin-bottom: 24rpx;
}

.quick-item {
	padding: 12rpx 24rpx;
	background: #FFFFFF;
	border-radius: 100rpx;
	font-size: 26rpx;
	font-weight: 600;
	color: #64748B;
	border: 1rpx solid #E2E8F0;
}

.quick-item.selected {
	background: #F0FDF4;
	color: #10B981;
	border-color: #10B981;
}

.withdraw-info {
	background: #FFFFFF;
	border-radius: 16rpx;
	padding: 20rpx 24rpx;
	margin-bottom: 32rpx;
}

.info-row {
	display: flex;
	justify-content: space-between;
	padding: 12rpx 0;
	border-bottom: 1rpx solid #F1F5F9;
}

.info-row:last-child {
	border-bottom: none;
}

.info-label {
	font-size: 26rpx;
	color: #64748B;
}

.info-value {
	font-size: 26rpx;
	font-weight: 600;
	color: #1E293B;
}

.info-value.highlight {
	color: #10B981;
}

.withdraw-methods {
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

.method-icon.alipay {
	background: #EFF6FF;
	color: #1677FF;
}

.method-icon.bank {
	background: #F5F3FF;
	color: #8B5CF6;
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

.method-arrow {
	color: #CBD5E1;
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

.withdraw-btn {
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

.withdraw-btn.disabled {
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