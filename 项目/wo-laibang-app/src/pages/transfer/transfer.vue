<template>
	<view class="transfer-container">
		<view class="header">
			<text class="header-title">转账</text>
			<view class="header-right"></view>
		</view>

		<scroll-view class="content-scroll" scroll-y>
			<view class="balance-card">
				<text class="balance-label">账户余额</text>
				<view class="balance-amount">
					<text class="currency-symbol">¥</text>
					<text class="amount">{{ balance.toFixed(2) }}</text>
				</view>
			</view>

			<view class="transfer-form">
				<view class="form-card">
					<view class="input-group">
						<label class="input-label">收款人</label>
						<view class="input-wrapper">
							<IconFont name="phone" :size="32" class="input-icon" />
							<input
								class="input-field"
								v-model="recipientPhone"
								type="number"
								maxlength="11"
								placeholder="请输入收款人手机号"
								@blur="lookupRecipient"
							/>
						</view>
					</view>

					<view v-if="recipient" class="recipient-card">
						<view class="avatar"><IconFont name="user" :size="40" /></view>
						<view class="recipient-info">
							<text class="recipient-name">{{ recipient.nickname }}</text>
							<text class="recipient-phone">{{ recipientPhone }}</text>
						</view>
						<IconFont name="check" :size="32" class="check-icon" />
					</view>

					<view class="input-group">
						<label class="input-label">转账金额</label>
						<view class="amount-wrapper">
							<text class="currency-prefix">¥</text>
							<input
								class="amount-input"
								type="digit"
								v-model="amount"
								placeholder="0.00"
							/>
						</view>
					</view>

					<view class="quick-amounts">
						<view
							v-for="item in quickAmounts"
							:key="item"
							class="quick-item"
							:class="{ selected: selectedQuick === item }"
							@click="selectQuickAmount(item)"
						>
							<text class="quick-text">¥{{ item }}</text>
						</view>
					</view>
				</view>

				<view class="form-card">
					<label class="input-label">备注（选填）</label>
					<view class="textarea-wrapper">
						<textarea
							class="textarea"
							v-model="remark"
							placeholder="给收款人的留言..."
							maxlength="100"
							rows="3"
						></textarea>
					</view>
				</view>
			</view>

			<view class="tips-section">
				<view class="tips-header">
					<IconFont name="sparkles" :size="32" class="tips-icon" />
					<text class="tips-title">转账须知</text>
				</view>
				<text class="tips-text">• 转账即时到账，不可撤回</text>
				<text class="tips-text">• 请仔细核对收款人信息</text>
				<text class="tips-text">• 单笔转账最高10,000元</text>
			</view>

			<view class="bottom-action">
				<button
					class="btn-primary"
					:disabled="!canTransfer || isProcessing"
					@click="handleTransfer"
				>
					<view v-if="isProcessing" class="spinner"></view>
					<text v-else>确认转账 ¥{{ amount || '0.00' }}</text>
				</button>
			</view>

			<view class="bottom-safe"></view>
		</scroll-view>
	</view>
</template>

<script>
import { useUserStore } from '@/store/user'
import { walletApi } from '@/api/wallet'
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
			balance: 0,
			recipientPhone: '',
			recipient: null,
			amount: '',
			remark: '',
			quickAmounts: [100, 500, 1000, 5000],
			selectedQuick: null,
			isProcessing: false,
			transferAmount: 0
		}
	},
	computed: {
		canTransfer() {
			return this.recipient && this.amount && parseFloat(this.amount) > 0
		}
	},
	async onShow() {
		await this.loadWalletBalance()
	},
	methods: {
		async loadWalletBalance() {
			try {
				const wallet = await this.userStore.fetchWalletInfo()
				this.balance = parseFloat(wallet.balance) || 0
			} catch (e) {
				const walletKey = `wallet_${this.userStore.currentUser.id}`
				const wallet = uni.getStorageSync(walletKey) || { balance: 0 }
				this.balance = parseFloat(wallet.balance) || 0
			}
		},
		async lookupRecipient() {
			if (!this.recipientPhone || !/^1[3-9]\d{9}$/.test(this.recipientPhone)) {
				this.recipient = null
				return
			}

			if (this.recipientPhone === uni.getStorageSync('currentUser')?.phone) {
				uni.showToast({ title: '不能给自己转账', icon: 'none' })
				this.recipient = null
				return
			}

			try {
				const userInfo = await uni.request({
					url: `https://api.wolaibang.com/api/user/search?phone=${this.recipientPhone}`,
					method: 'GET'
				})
				if (userInfo.data?.data) {
					this.recipient = userInfo.data.data
					uni.showToast({ title: '已找到收款人', icon: 'success' })
				} else {
					uni.showToast({ title: '未找到该用户', icon: 'none' })
					this.recipient = null
				}
			} catch (e) {
				uni.showToast({ title: '查询失败', icon: 'none' })
				this.recipient = null
			}
		},
		selectQuickAmount(amount) {
			this.selectedQuick = amount
			this.amount = amount.toString()
		},
		handleTransfer() {
			const amt = parseFloat(this.amount)
			if (!this.recipient) {
				uni.showToast({ title: '请输入正确的收款人', icon: 'none' })
				return
			}
			if (!amt || amt <= 0) {
				uni.showToast({ title: '请输入转账金额', icon: 'none' })
				return
			}
			if (amt > this.balance) {
				uni.showToast({ title: '余额不足', icon: 'none' })
				return
			}
			if (amt > 10000) {
				uni.showToast({ title: '单笔转账最高10,000元', icon: 'none' })
				return
			}

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

			this.transferAmount = amt
			uni.navigateTo({
				url: `/pages/payment-verify/payment-verify?amount=${amt}&title=转账验证`
			})
		},
		onPaymentVerifySuccess() {
			this.executeTransfer()
		},
		async executeTransfer() {
			const amt = this.transferAmount
			this.isProcessing = true
			uni.showLoading({ title: '转账中...' })

			try {
				await walletApi.transfer(this.recipient.id, amt, this.remark)

				this.userStore.deductBalance(amt)
				this.balance = this.userStore.walletBalance

				this.userStore.addBalanceToUser(this.recipient.id, amt)

				const transactions = uni.getStorageSync('walletTransactions') || []
				transactions.unshift({
					id: Date.now(),
					type: 'transfer',
					title: `转账给${this.recipient.nickname}`,
					amount: -amt,
					recipientId: this.recipient.id,
					recipientName: this.recipient.nickname,
					remark: this.remark,
					time: Date.now()
				})
				uni.setStorageSync('walletTransactions', transactions)

				const recipientTransactions = uni.getStorageSync('recipientTransactions') || {}
				if (!recipientTransactions[this.recipient.id]) {
					recipientTransactions[this.recipient.id] = []
				}
				recipientTransactions[this.recipient.id].unshift({
					id: Date.now(),
					type: 'transfer_received',
					title: `收到${this.userStore.currentUser.nickname || '用户'}的转账`,
					amount: amt,
					fromUserId: this.userStore.currentUser.id,
					fromUserName: this.userStore.currentUser.nickname,
					remark: this.remark,
					time: Date.now()
				})
				uni.setStorageSync('recipientTransactions', recipientTransactions)

				this.isProcessing = false
				this.transferAmount = 0
				uni.showToast({
					title: '转账成功',
					icon: 'success'
				})

				setTimeout(() => {
					uni.navigateBack()
				}, 1500)
			} catch (e) {
				uni.hideLoading()
				this.isProcessing = false
				uni.showToast({
					title: e.message || '转账失败',
					icon: 'none'
				})
			}
		},
		}
}
</script>

<style scoped>
.transfer-container {
	min-height: 100vh;
	background: #F8FAFC;
}

.header {
	display: flex;
	align-items: center;
	justify-content: space-between;
	padding: 80rpx 48rpx 40rpx;
	background: #FFFFFF;
}

.header-title {
	flex: 1;
	font-size: 36rpx;
	font-weight: 800;
	color: #1E293B;
	text-align: center;
}

.header-right {
	width: 88rpx;
}

.content-scroll {
	height: calc(100vh - 144rpx);
}

.balance-card {
	background: linear-gradient(135deg, #10B981, #059669);
	margin: 32rpx 48rpx;
	border-radius: 40rpx;
	padding: 48rpx;
	box-shadow: 0 16rpx 48rpx rgba(16, 185, 129, 0.25);
}

.balance-label {
	font-size: 26rpx;
	color: rgba(255, 255, 255, 0.8);
	font-weight: 600;
	display: block;
	margin-bottom: 16rpx;
}

.balance-amount {
	display: flex;
	align-items: baseline;
}

.currency-symbol {
	font-size: 36rpx;
	color: #FFFFFF;
	font-weight: 600;
	margin-right: 8rpx;
}

.amount {
	font-size: 72rpx;
	font-weight: 900;
	color: #FFFFFF;
	letter-spacing: -2rpx;
}

.transfer-form {
	margin: 0 48rpx;
}

.form-card {
	background: #FFFFFF;
	border-radius: 40rpx;
	padding: 40rpx;
	margin-bottom: 32rpx;
	box-shadow: 0 4rpx 24rpx rgba(0, 0, 0, 0.04);
}

.input-group {
	margin-bottom: 32rpx;
}

.input-label {
	font-size: 24rpx;
	color: #64748B;
	font-weight: 700;
	text-transform: uppercase;
	letter-spacing: 1rpx;
	margin-bottom: 16rpx;
	display: block;
}

.input-wrapper {
	background: #F8FAFC;
	border-radius: 28rpx;
	padding: 28rpx 32rpx;
	border: 2rpx solid transparent;
	display: flex;
	align-items: center;
	gap: 24rpx;
	transition: all 0.3s;
}

.input-wrapper:focus-within {
	background: #FFFFFF;
	border-color: #10B981;
	box-shadow: 0 12rpx 32rpx rgba(16, 185, 129, 0.08);
}

.input-icon {
	width: 40rpx;
	display: flex;
	align-items: center;
	justify-content: center;
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

.recipient-card {
	background: #F0FDF4;
	border-radius: 28rpx;
	padding: 28rpx 32rpx;
	margin-top: 24rpx;
	display: flex;
	align-items: center;
	border: 2rpx solid #10B981;
}

.avatar {
	width: 88rpx;
	height: 88rpx;
	background: linear-gradient(135deg, #10B981, #34D399);
	border-radius: 50%;
	display: flex;
	align-items: center;
	justify-content: center;
	margin-right: 24rpx;
}

.recipient-info {
	flex: 1;
}

.recipient-name {
	font-size: 30rpx;
	font-weight: 700;
	color: #1E293B;
	display: block;
}

.recipient-phone {
	font-size: 24rpx;
	color: #64748B;
	margin-top: 4rpx;
}

.check-icon {
	width: 48rpx;
	height: 48rpx;
	background: #10B981;
	border-radius: 50%;
	display: flex;
	align-items: center;
	justify-content: center;
	color: #FFFFFF;
}

.amount-wrapper {
	display: flex;
	align-items: center;
	border-bottom: 4rpx solid #E2E8F0;
	padding-bottom: 24rpx;
}

.currency-prefix {
	font-size: 48rpx;
	font-weight: 700;
	color: #1E293B;
	margin-right: 16rpx;
}

.amount-input {
	flex: 1;
	font-size: 56rpx;
	font-weight: 900;
	color: #1E293B;
	border: none;
	outline: none;
	background: transparent;
}

.quick-amounts {
	display: flex;
	gap: 20rpx;
	flex-wrap: wrap;
}

.quick-item {
	padding: 16rpx 32rpx;
	background: #F8FAFC;
	border-radius: 40rpx;
	border: 2rpx solid #E2E8F0;
}

.quick-item.selected {
	background: #F0FDF4;
	border-color: #10B981;
}

.quick-text {
	font-size: 26rpx;
	font-weight: 600;
	color: #64748B;
}

.quick-item.selected .quick-text {
	color: #10B981;
}

.textarea-wrapper {
	background: #F8FAFC;
	border-radius: 28rpx;
	padding: 28rpx 32rpx;
	border: 2rpx solid transparent;
	transition: all 0.3s;
}

.textarea-wrapper:focus-within {
	background: #FFFFFF;
	border-color: #10B981;
	box-shadow: 0 12rpx 32rpx rgba(16, 185, 129, 0.08);
}

.textarea {
	width: 100%;
	font-size: 30rpx;
	font-weight: 600;
	color: #1E293B;
	border: none;
	outline: none;
	background: transparent;
	resize: none;
}

.tips-section {
	margin: 0 48rpx 32rpx;
	padding: 32rpx;
	background: #F0FDF4;
	border-radius: 28rpx;
}

.tips-header {
	display: flex;
	align-items: center;
	margin-bottom: 20rpx;
}

.tips-icon {
	margin-right: 16rpx;
	display: flex;
	align-items: center;
}

.tips-title {
	font-size: 26rpx;
	font-weight: 700;
	color: #059669;
}

.tips-text {
	font-size: 24rpx;
	color: #64748B;
	display: block;
	margin-bottom: 8rpx;
}

.bottom-action {
	padding: 32rpx 48rpx;
}

.btn-primary {
	width: 100%;
	height: 104rpx;
	background: linear-gradient(135deg, #10B981, #059669);
	color: #FFFFFF;
	border-radius: 52rpx;
	font-weight: 800;
	font-size: 32rpx;
	border: none;
	box-shadow: 0 16rpx 48rpx rgba(16, 185, 129, 0.35);
	display: flex;
	align-items: center;
	justify-content: center;
	transition: all 0.3s;
}

.btn-primary:active:not(:disabled) {
	transform: translateY(-4rpx);
	box-shadow: 0 24rpx 64rpx rgba(16, 185, 129, 0.4);
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
	height: 80rpx;
}
</style>