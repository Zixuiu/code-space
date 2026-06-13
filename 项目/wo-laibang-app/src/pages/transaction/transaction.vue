<template>
	<view class="container">
		<view class="header">
			
			<text class="header-title">交易流水</text>
			<view class="header-right"></view>
		</view>

		<view class="stats-bar">
			<view class="stat-item">
				<text class="stat-label">总收入</text>
				<text class="stat-value income">+{{ totalIncome }}</text>
			</view>
			<view class="stat-divider"></view>
			<view class="stat-item">
				<text class="stat-label">总支出</text>
				<text class="stat-value expense">-{{ totalExpense }}</text>
			</view>
		</view>

		<view class="tabs">
			<view
				class="tab"
				:class="{ active: currentTab === 'all' }"
				@click="switchTab('all')"
			>
				<text class="tab-text">全部</text>
			</view>
			<view
				class="tab"
				:class="{ active: currentTab === 'income' }"
				@click="switchTab('income')"
			>
				<text class="tab-text">收入</text>
			</view>
			<view
				class="tab"
				:class="{ active: currentTab === 'expense' }"
				@click="switchTab('expense')"
			>
				<text class="tab-text">支出</text>
			</view>
		</view>

		<scroll-view class="content-scroll" scroll-y>
			<view v-if="filteredList.length === 0" class="empty-state">
				<view class="empty-icon-wrapper">
					<IconFont name="wallet" :size="40" color="#10B981" />
				</view>
				<text class="empty-title">暂无交易记录</text>
				<text class="empty-subtitle">完成订单后即可查看交易明细~</text>
			</view>

			<view v-else class="transaction-list">
				<view
					v-for="item in filteredList"
					:key="item.id"
					class="transaction-card"
				>
					<view class="tx-left">
						<view class="tx-icon" :class="item.type">
							<IconFont :name="getIcon(item.type)" :size="20" />
						</view>
						<view class="tx-info">
							<text class="tx-title">{{ item.title }}</text>
							<text class="tx-time">{{ formatTime(item.time) }}</text>
						</view>
					</view>
					<text class="tx-amount" :class="item.type">
						{{ item.type === 'income' ? '+' : '-' }}{{ item.amount }}
					</text>
				</view>
			</view>

			<view class="bottom-space"></view>
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
			currentTab: 'all',
			transactions: []
		}
	},
	computed: {
		filteredList() {
			if (this.currentTab === 'all') {
				return this.transactions
			}
			return this.transactions.filter(t => t.type === this.currentTab)
		},
		totalIncome() {
			return this.transactions
				.filter(t => t.type === 'income')
				.reduce((sum, t) => sum + parseFloat(t.amount), 0)
				.toFixed(2)
		},
		totalExpense() {
			return this.transactions
				.filter(t => t.type === 'expense')
				.reduce((sum, t) => sum + parseFloat(t.amount), 0)
				.toFixed(2)
		}
	},
	onLoad() {
		this.loadTransactions()
	},
	onShow() {
		uni.hideTabBar()
	},
	methods: {
		loadTransactions() {
			const stored = uni.getStorageSync('walletTransactions') || []
			this.transactions = stored.sort((a, b) => b.time - a.time)
		},
		switchTab(tab) {
			this.currentTab = tab
		},
		getIcon(type) {
			const icons = {
				income: 'arrow-down-circle',
				expense: 'arrow-up-circle',
				reward: 'gift',
				refund: 'rotate-ccw'
			}
			return icons[type] || 'circle'
		},
		formatTime(timestamp) {
			if (!timestamp) return ''
			const date = new Date(timestamp)
			const month = date.getMonth() + 1
			const day = date.getDate()
			const hour = date.getHours().toString().padStart(2, '0')
			const min = date.getMinutes().toString().padStart(2, '0')
			return `${month}月${day}日 ${hour}:${min}`
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

.stats-bar {
	display: flex;
	background: linear-gradient(135deg, #10B981, #059669);
	padding: 32rpx 24rpx;
}

.stat-item {
	flex: 1;
	text-align: center;
}

.stat-label {
	font-size: 24rpx;
	color: rgba(255, 255, 255, 0.8);
	display: block;
	margin-bottom: 8rpx;
}

.stat-value {
	font-size: 36rpx;
	font-weight: 800;
	color: #FFFFFF;
}

.stat-divider {
	width: 1rpx;
	background: rgba(255, 255, 255, 0.3);
	margin: 0 24rpx;
}

.tabs {
	display: flex;
	background: #FFFFFF;
	padding: 0 24rpx;
	border-bottom: 1rpx solid #F1F5F9;
}

.tab {
	flex: 1;
	text-align: center;
	padding: 24rpx 0;
	position: relative;
}

.tab-text {
	font-size: 28rpx;
	font-weight: 600;
	color: #94A3B8;
}

.tab.active .tab-text {
	color: #10B981;
	font-weight: 700;
}

.tab.active::after {
	content: '';
	position: absolute;
	bottom: 0;
	left: 50%;
	transform: translateX(-50%);
	width: 48rpx;
	height: 4rpx;
	background: #10B981;
	border-radius: 2rpx;
}

.content-scroll {
	height: calc(100vh - 560rpx);
}

.empty-state {
	padding-top: 60rpx;
	display: flex;
	flex-direction: column;
	align-items: center;
}

.empty-icon-wrapper {
	width: 120rpx;
	height: 120rpx;
	background: #F0FDF4;
	border-radius: 30rpx;
	display: flex;
	align-items: center;
	justify-content: center;
	margin-bottom: 24rpx;
}

.empty-title {
	font-size: 32rpx;
	font-weight: 700;
	color: #1E293B;
	margin-bottom: 12rpx;
}

.empty-subtitle {
	font-size: 26rpx;
	color: #94A3B8;
}

.transaction-list {
	padding: 20rpx 24rpx;
}

.transaction-card {
	background: #FFFFFF;
	border-radius: 20rpx;
	padding: 24rpx;
	margin-bottom: 16rpx;
	display: flex;
	align-items: center;
	justify-content: space-between;
	box-shadow: 0 2rpx 12rpx rgba(0, 0, 0, 0.04);
}

.tx-left {
	display: flex;
	align-items: center;
}

.tx-icon {
	width: 72rpx;
	height: 72rpx;
	border-radius: 18rpx;
	display: flex;
	align-items: center;
	justify-content: center;
	margin-right: 16rpx;
}

.tx-icon.income {
	background: #F0FDF4;
	color: #10B981;
}

.tx-icon.expense {
	background: #FEF2F2;
	color: #EF4444;
}

.tx-icon.reward {
	background: #FEF3C7;
	color: #F59E0B;
}

.tx-icon.refund {
	background: #EFF6FF;
	color: #3B82F6;
}

.tx-info {
	display: flex;
	flex-direction: column;
}

.tx-title {
	font-size: 28rpx;
	font-weight: 700;
	color: #1E293B;
	margin-bottom: 6rpx;
}

.tx-time {
	font-size: 22rpx;
	color: #94A3B8;
}

.tx-amount {
	font-size: 32rpx;
	font-weight: 800;
}

.tx-amount.income {
	color: #10B981;
}

.tx-amount.expense {
	color: #1E293B;
}

.bottom-space {
	height: 40rpx;
}
</style>