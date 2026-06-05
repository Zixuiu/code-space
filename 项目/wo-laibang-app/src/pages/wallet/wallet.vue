<template>
	<view class="wallet-container">
		<view class="header">
			<view class="header-left"></view>
			<text class="header-title">我的钱包</text>
			<view class="header-right"></view>
		</view>

		<scroll-view class="content-scroll" scroll-y
			refresher-enabled
			:refresher-triggered="refreshing"
			@refresherrefresh="onRefresh"
			:lower-threshold="50"
			@scrolltolower="loadMore"
		>
			<view class="balance-hero">
				<text class="balance-label">账户余额</text>
				<view class="balance-amount">
					<text class="currency-symbol">¥</text>
					<text class="amount">{{ balance.toFixed(2) }}</text>
				</view>
				<view class="balance-actions">
				<view class="action-btn action-recharge" @click="goRecharge">
					<IconFont name="wallet" :size="100" class="action-icon" />
					<text class="action-text">充值</text>
				</view>
				<view class="action-btn action-withdraw" @click="goWithdraw">
					<IconFont name="withdraw" :size="100" class="action-icon" />
					<text class="action-text">提现</text>
				</view>
				<view class="action-btn action-transfer" @click="goTransfer">
					<IconFont name="transfer" :size="100" class="action-icon" />
					<text class="action-text">转账</text>
				</view>
			</view>
			</view>

			<view class="stats-card">
				<view class="stat-item">
					<text class="stat-value">¥{{ totalIncome.toFixed(2) }}</text>
					<text class="stat-label">累计收入</text>
				</view>
				<view class="stat-divider"></view>
				<view class="stat-item">
					<text class="stat-value">¥{{ totalExpense.toFixed(2) }}</text>
					<text class="stat-label">累计支出</text>
				</view>
				<view class="stat-divider"></view>
				<view class="stat-item">
					<text class="stat-value">¥{{ commissionEarned.toFixed(2) }}</text>
					<text class="stat-label">分享佣金</text>
				</view>
			</view>

			<view class="section">
				<view class="section-header">
					<text class="section-title">交易记录</text>
					<text class="section-more" @click="showAll">查看全部 ›</text>
				</view>

				<view v-if="transactions.length === 0" class="empty-state">
					<IconFont name="list" :size="56" class="empty-icon" />
					<text class="empty-text">暂无交易记录</text>
				</view>

				<view v-else class="transaction-list">
					<view
						v-for="item in transactions.slice(0, 5)"
						:key="item.id"
						class="transaction-item"
					>
						<view class="trans-icon" :class="item.type">
						<IconFont v-if="item.type === 'recharge'" name="circle-plus" :size="32" />
					<IconFont v-else-if="item.type === 'withdraw'" name="upload" :size="32" />
					<IconFont v-else-if="item.type === 'transfer'" name="share" :size="32" />
						<IconFont v-else-if="item.type === 'order'" name="clipboard-list" :size="32" />
						<IconFont v-else-if="item.type === 'commission'" name="coin" :size="32" />
						<IconFont v-else name="circle" :size="32" />
					</view>
						<view class="trans-info">
							<text class="trans-title">{{ getTransTitle(item) }}</text>
							<text class="trans-time">{{ item.time }}</text>
						</view>
						<text class="trans-amount" :class="{ positive: item.amount > 0 }">
							{{ item.amount > 0 ? '+' : '' }}{{ item.amount.toFixed(2) }}
						</text>
					</view>
				</view>
			</view>

			<view class="bottom-safe"></view>
		</scroll-view>
	</view>
</template>

<script>
import { useUserStore } from '@/store/user'
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
			totalIncome: 0,
			totalExpense: 0,
			transactions: [],
			commissionEarned: 0,
			sharedNeeds: [],
			refreshing: false,
			hasMore: true,
			page: 1,
			pageSize: 10
		}
	},
	onShow() {
		this.loadData()
		this.userStore.updateBalanceFromWallet()
	},
	methods: {
		async onRefresh() {
			this.refreshing = true
			this.page = 1
			this.hasMore = true
			await this.loadData()
			this.refreshing = false
		},
		async loadMore() {
			if (!this.hasMore) return
			this.page++
			const walletKey = `wallet_${this.userStore.currentUser.id}`
			const wallet = uni.getStorageSync(walletKey) || { balance: 0 }
			this.balance = parseFloat(wallet.balance) || 0

			const transactions = uni.getStorageSync('walletTransactions') || []
			const start = (this.page - 1) * this.pageSize
			const end = start + this.pageSize
			const newTransactions = transactions.slice(start, end)

			if (newTransactions.length === 0) {
				this.hasMore = false
			} else {
				if (this.page === 1) {
					this.transactions = newTransactions
				} else {
					this.transactions = [...this.transactions, ...newTransactions]
				}
			}
		},
		loadData() {
			const walletKey = `wallet_${this.userStore.currentUser.id}`
			const wallet = uni.getStorageSync(walletKey) || { balance: 0 }
			this.balance = parseFloat(wallet.balance) || 0
			this.commissionEarned = wallet.commissionEarned || 0
			this.sharedNeeds = wallet.sharedNeeds || []

			const transactions = uni.getStorageSync('walletTransactions') || []
			this.transactions = transactions

			this.totalIncome = transactions
				.filter(t => t.amount > 0)
				.reduce((sum, t) => sum + t.amount, 0)

			this.totalExpense = transactions
				.filter(t => t.amount < 0)
				.reduce((sum, t) => sum + Math.abs(t.amount), 0)
		},
		getTransTitle(item) {
			const titles = {
				recharge: '充值',
				withdraw: '提现',
				transfer: item.amount < 0 ? '转账给' + (item.recipient || '用户') : '收到转账',
				order: '订单支付',
				commission: '分享佣金'
			}
			return titles[item.type] || '其他交易'
		},
		goRecharge() {
			uni.navigateTo({ url: '/pages/recharge/recharge' })
		},
		goWithdraw() {
			uni.navigateTo({ url: '/pages/withdraw/withdraw' })
		},
		goTransfer() {
			uni.navigateTo({ url: '/pages/transfer/transfer' })
		},
		showAll() {
			uni.showToast({ title: '查看全部交易记录', icon: 'none' })
		},
		}
}
</script>

<style scoped>
.wallet-container {
	min-height: 100vh;
	background: #F8FAFC;
}

.header {
	display: flex;
	align-items: center;
	justify-content: space-between;
	padding: calc(44px + env(safe-area-inset-top)) 24px 20px;
	background: #FFFFFF;
}

.header-left {
	width: 44px;
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

.balance-hero {
	background: linear-gradient(135deg, #10B981, #059669);
	margin: 16px 24px;
	border-radius: 24px;
	padding: 28px;
	box-shadow: 0 12px 32px rgba(16, 185, 129, 0.3);
}

.balance-label {
	font-size: 14px;
	color: rgba(255, 255, 255, 0.8);
	font-weight: 600;
	display: block;
	margin-bottom: 8px;
}

.balance-amount {
	display: flex;
	align-items: baseline;
	margin-bottom: 24px;
}

.currency-symbol {
	font-size: 22px;
	color: #FFFFFF;
	font-weight: 600;
	margin-right: 4px;
}

.amount {
	font-size: 44px;
	font-weight: 900;
	color: #FFFFFF;
	letter-spacing: -1px;
}

.balance-actions {
	display: flex;
	gap: 16px;
	padding: 0 8px;
}

.action-btn {
	flex: 1;
	border-radius: 20px;
	padding: 16px 8px;
	text-align: center;
	backdrop-filter: blur(10px);
}

.action-recharge {
	background: rgba(74, 222, 128, 0.25);
}

.action-withdraw {
	background: rgba(251, 191, 36, 0.25);
}

.action-transfer {
	background: rgba(96, 165, 250, 0.25);
}

.action-icon {
	display: block;
	margin-bottom: 8px;
}

.action-text {
	font-size: 14px;
	font-weight: 700;
	color: #FFFFFF;
}

.stats-card {
	display: flex;
	align-items: center;
	background: #FFFFFF;
	margin: 0 24px 16px;
	border-radius: 20px;
	padding: 20px;
	box-shadow: 0 2px 12px rgba(0, 0, 0, 0.04);
}

.stat-item {
	flex: 1;
	text-align: center;
}

.stat-value {
	font-size: 18px;
	font-weight: 900;
	color: #1E293B;
	display: block;
	margin-bottom: 4px;
}

.stat-label {
	font-size: 12px;
	color: #64748B;
	font-weight: 600;
}

.stat-divider {
	width: 1px;
	height: 40px;
	background: #E2E8F0;
}

.section {
	margin: 0 24px;
}

.section-header {
	display: flex;
	justify-content: space-between;
	align-items: center;
	margin-bottom: 16px;
}

.section-title {
	font-size: 17px;
	font-weight: 800;
	color: #1E293B;
}

.section-more {
	font-size: 13px;
	color: #10B981;
	font-weight: 600;
}

.empty-state {
	background: #FFFFFF;
	border-radius: 20px;
	padding: 48px 24px;
	text-align: center;
	box-shadow: 0 2px 12px rgba(0, 0, 0, 0.04);
}

.empty-icon {
	display: block;
	margin-bottom: 12px;
}

.empty-text {
	font-size: 14px;
	color: #94A3B8;
	font-weight: 600;
}

.transaction-list {
	background: #FFFFFF;
	border-radius: 20px;
	overflow: hidden;
	box-shadow: 0 2px 12px rgba(0, 0, 0, 0.04);
}

.transaction-item {
	display: flex;
	align-items: center;
	padding: 16px 20px;
	border-bottom: 1px solid #F1F5F9;
}

.transaction-item:last-child {
	border-bottom: none;
}

.trans-icon {
	width: 44px;
	height: 44px;
	border-radius: 12px;
	display: flex;
	align-items: center;
	justify-content: center;
	font-size: 20px;
	margin-right: 14px;
}

.trans-icon.recharge {
	background: #F0FDF4;
}

.trans-icon.withdraw {
	background: #FEF3C7;
}

.trans-icon.transfer {
	background: #EFF6FF;
}

.trans-icon.order {
	background: #FDF2F8;
}

.trans-info {
	flex: 1;
}

.trans-title {
	font-size: 14px;
	font-weight: 700;
	color: #1E293B;
	display: block;
	margin-bottom: 4px;
}

.trans-time {
	font-size: 12px;
	color: #94A3B8;
}

.trans-amount {
	font-size: 16px;
	font-weight: 800;
	color: #1E293B;
}

.trans-amount.positive {
	color: #10B981;
}

.bottom-safe {
	height: 40px;
}
</style>