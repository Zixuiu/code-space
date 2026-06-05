<template>
	<view class="container">
		<view class="header">
			
			<text class="header-title">评价历史</text>
			<view class="header-right"></view>
		</view>

		<scroll-view class="content-scroll" scroll-y>
			<view class="stats-card">
				<view class="stats-item">
					<view class="stats-value">{{ stats.totalOrders }}</view>
					<view class="stats-label">评价次数</view>
				</view>
				<view class="stats-divider"></view>
				<view class="stats-item">
					<view class="stats-value">{{ stats.avgRating }}</view>
					<view class="stats-label">平均评分</view>
				</view>
				<view class="stats-divider"></view>
				<view class="stats-item">
					<view class="stats-value">{{ stats.fiveStar }}%</view>
					<view class="stats-label">五星好评</view>
				</view>
			</view>

			<view v-if="ratings.length === 0" class="empty-state">
				<view class="empty-icon-wrapper">
					<IconFont name="star" :size="40" color="#10B981" />
				</view>
				<text class="empty-title">暂无评价</text>
				<text class="empty-subtitle">完成订单后即可查看评价~</text>
			</view>

			<view v-else class="rating-list">
				<view
					v-for="item in ratings"
					:key="item.id"
					class="rating-card"
				>
					<view class="rating-header">
						<view class="user-info">
							<view class="user-avatar">{{ item.userName[0] }}</view>
							<view class="user-detail">
								<text class="user-name">{{ item.userName }}</text>
								<text class="order-title">{{ item.orderTitle }}</text>
							</view>
						</view>
						<view class="rating-time">{{ formatTime(item.ratedAt) }}</view>
					</view>

					<view class="rating-stars">
						<IconFont
							v-for="n in 5"
							:key="n"
							:name="n <= item.rating ? 'star' : 'star-outline'"
							:size="20"
							:class="n <= item.rating ? 'active' : 'inactive'"
						/>
					</view>

					<view v-if="item.tags && item.tags.length > 0" class="rating-tags">
						<text v-for="tag in item.tags" :key="tag" class="rating-tag">{{ tag }}</text>
					</view>

					<view v-if="item.comment" class="rating-comment">
						{{ item.comment }}
					</view>

					<view v-if="item.reply" class="rating-reply">
						<view class="reply-label">我的回复</view>
						<text class="reply-text">{{ item.reply }}</text>
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
			ratings: [],
			stats: {
				totalOrders: 0,
				avgRating: '0.0',
				fiveStar: 0
			}
		}
	},
	onLoad() {
		this.loadRatings()
	},
	onShow() {
		uni.hideTabBar()
	},
	methods: {
		loadRatings() {
			const stored = uni.getStorageSync('orderRatings') || []
			this.ratings = stored.sort((a, b) => b.ratedAt - a.ratedAt)

			if (this.ratings.length > 0) {
				const totalRating = this.ratings.reduce((sum, r) => sum + r.rating, 0)
				const avgRating = (totalRating / this.ratings.length).toFixed(1)
				const fiveStarCount = this.ratings.filter(r => r.rating === 5).length
				const fiveStarPercent = Math.round((fiveStarCount / this.ratings.length) * 100)

				this.stats = {
					totalOrders: this.ratings.length,
					avgRating,
					fiveStar: fiveStarPercent
				}
			}
		},
		formatTime(timestamp) {
			if (!timestamp) return ''
			const date = new Date(timestamp)
			const month = date.getMonth() + 1
			const day = date.getDate()
			return `${month}月${day}日`
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
}

.stats-card {
	display: flex;
	background: linear-gradient(135deg, #10B981, #059669);
	margin: 24rpx;
	border-radius: 24rpx;
	padding: 32rpx 24rpx;
}

.stats-item {
	flex: 1;
	text-align: center;
}

.stats-value {
	font-size: 40rpx;
	font-weight: 800;
	color: #FFFFFF;
	margin-bottom: 8rpx;
}

.stats-label {
	font-size: 22rpx;
	color: rgba(255, 255, 255, 0.8);
}

.stats-divider {
	width: 1rpx;
	background: rgba(255, 255, 255, 0.3);
	margin: 0 16rpx;
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

.rating-list {
	padding: 0 24rpx;
}

.rating-card {
	background: #FFFFFF;
	border-radius: 20rpx;
	padding: 24rpx;
	margin-bottom: 16rpx;
	box-shadow: 0 2rpx 12rpx rgba(0, 0, 0, 0.04);
}

.rating-header {
	display: flex;
	justify-content: space-between;
	align-items: flex-start;
	margin-bottom: 16rpx;
}

.user-info {
	display: flex;
	align-items: center;
	gap: 12rpx;
}

.user-avatar {
	width: 64rpx;
	height: 64rpx;
	background: linear-gradient(135deg, #10B981, #34D399);
	border-radius: 18rpx;
	display: flex;
	align-items: center;
	justify-content: center;
	font-size: 26rpx;
	font-weight: 700;
	color: #FFFFFF;
}

.user-detail {
	display: flex;
	flex-direction: column;
}

.user-name {
	font-size: 28rpx;
	font-weight: 700;
	color: #1E293B;
	margin-bottom: 4rpx;
}

.order-title {
	font-size: 24rpx;
	color: #64748B;
}

.rating-time {
	font-size: 22rpx;
	color: #94A3B8;
}

.rating-stars {
	display: flex;
	gap: 6rpx;
	margin-bottom: 12rpx;
}

.rating-stars .active {
	color: #F59E0B;
}

.rating-stars :not(.active) {
	color: #E2E8F0;
}

.rating-tags {
	display: flex;
	flex-wrap: wrap;
	gap: 8rpx;
	margin-bottom: 12rpx;
}

.rating-tag {
	font-size: 22rpx;
	color: #059669;
	background: #F0FDF4;
	padding: 6rpx 16rpx;
	border-radius: 100rpx;
}

.rating-comment {
	font-size: 26rpx;
	color: #374151;
	line-height: 1.6;
}

.rating-reply {
	margin-top: 16rpx;
	padding: 16rpx;
	background: #F8FAFC;
	border-radius: 12rpx;
}

.reply-label {
	font-size: 22rpx;
	font-weight: 700;
	color: #10B981;
	margin-bottom: 8rpx;
}

.reply-text {
	font-size: 24rpx;
	color: #64748B;
	line-height: 1.5;
}

.bottom-space {
	height: 40rpx;
}
</style>