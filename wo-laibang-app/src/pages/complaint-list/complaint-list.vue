<template>
	<view class="container">
		<view class="header">
			<text class="header-title">投诉记录</text>
			<view class="header-right"></view>
		</view>

		<scroll-view class="content-scroll" scroll-y>
			<view v-if="complaints.length === 0" class="empty-state">
				<view class="empty-icon-wrapper">
					<IconFont name="shield" :size="40" color="#10B981" />
				</view>
				<text class="empty-title">暂无投诉记录</text>
				<text class="empty-subtitle">如有纠纷可在订单详情中发起投诉~</text>
			</view>

			<view v-else class="complaint-list">
				<view
					v-for="item in complaints"
					:key="item.id"
					class="complaint-card"
					@click="goDetail(item)"
				>
					<view class="card-header">
						<view class="status-badge" :class="item.status">
							{{ getStatusText(item.status) }}
						</view>
						<text class="card-time">{{ formatTime(item.createdAt) }}</text>
					</view>

					<view class="card-content">
						<text class="card-title">{{ item.orderTitle }}</text>
						<text class="card-type">{{ getTypeText(item.type) }}</text>
					</view>

					<view class="card-desc">
						{{ item.description }}
					</view>

					<view class="card-footer">
						<view class="reply-status" v-if="item.replies && item.replies.length > 0">
							<IconFont name="message-circle" :size="16" />
							<text>{{ item.replies.length }} 条回复</text>
						</view>
						<view class="arrow">
							<IconFont name="chevron-right" :size="18" />
						</view>
					</view>
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
			complaints: []
		}
	},
	onLoad() {
		this.loadComplaints()
	},
	onShow() {
		uni.hideTabBar()
		this.loadComplaints()
	},
	methods: {
		loadComplaints() {
			const stored = uni.getStorageSync('complaints') || []
			this.complaints = stored
		},
		getStatusText(status) {
			const statusMap = {
				pending: '处理中',
				resolved: '已解决',
				rejected: '已驳回'
			}
			return statusMap[status] || status
		},
		getTypeText(type) {
			const typeMap = {
				service: '未完成服务',
				attitude: '态度恶劣',
				price: '收费不合理',
				other: '其他问题'
			}
			return typeMap[type] || type
		},
		formatTime(timestamp) {
			if (!timestamp) return ''
			const date = new Date(timestamp)
			const month = date.getMonth() + 1
			const day = date.getDate()
			return `${month}月${day}日`
		},
		goDetail(item) {
			uni.navigateTo({ url: `/pages/complaint-detail/complaint-detail?id=${item.id}` })
		},
		}
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
}

.empty-state {
	padding-top: 120rpx;
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

.complaint-list {
	padding: 24rpx;
}

.complaint-card {
	background: #FFFFFF;
	border-radius: 20rpx;
	padding: 24rpx;
	margin-bottom: 16rpx;
	box-shadow: 0 2rpx 12rpx rgba(0, 0, 0, 0.04);
}

.card-header {
	display: flex;
	justify-content: space-between;
	align-items: center;
	margin-bottom: 16rpx;
}

.status-badge {
	font-size: 22rpx;
	font-weight: 700;
	padding: 6rpx 16rpx;
	border-radius: 100rpx;
}

.status-badge.pending {
	background: #FEF3C7;
	color: #D97706;
}

.status-badge.resolved {
	background: #F0FDF4;
	color: #10B981;
}

.status-badge.rejected {
	background: #FEE2E2;
	color: #EF4444;
}

.card-time {
	font-size: 22rpx;
	color: #94A3B8;
}

.card-content {
	margin-bottom: 12rpx;
}

.card-title {
	font-size: 28rpx;
	font-weight: 700;
	color: #1E293B;
	display: block;
	margin-bottom: 6rpx;
}

.card-type {
	font-size: 22rpx;
	color: #64748B;
}

.card-desc {
	font-size: 26rpx;
	color: #374151;
	line-height: 1.5;
	margin-bottom: 16rpx;
	display: -webkit-box;
	-webkit-line-clamp: 2;
	-webkit-box-orient: vertical;
	overflow: hidden;
}

.card-footer {
	display: flex;
	justify-content: space-between;
	align-items: center;
}

.reply-status {
	display: flex;
	align-items: center;
	gap: 6rpx;
	font-size: 22rpx;
	color: #64748B;
}

.arrow {
	color: #CBD5E1;
}

.bottom-space {
	height: 40rpx;
}
</style>