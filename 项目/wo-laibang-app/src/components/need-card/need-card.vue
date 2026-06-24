<template>
	<view class="need-card" @click="handleClick">
		<view class="card-top">
			<view class="user-info">
				<view class="avatar" :style="{ background: avatarBg }">
					{{ avatarText }}
				</view>
				<view class="meta">
					<text class="name">{{ need.publisher?.nickname || '匿名用户' }}</text>
					<text class="time">{{ formattedTime }}</text>
				</view>
			</view>
			<text class="price">¥{{ need.reward }}</text>
		</view>
		<view class="card-body">
			<view class="title-row">
				<text v-if="need.isUrgent" class="urgent-badge">紧急</text>
				<text class="title">{{ need.title }}</text>
			</view>
			<text class="desc">{{ need.description }}</text>
		</view>
		<view class="card-footer">
			<view class="loc-wrap">
				<view class="loc-tag">
					<IconFont name="location" :size="24" class="icon" />
					<text class="loc-text">{{ need.location || '位置未设置' }}</text>
				</view>
				<text v-if="distanceText" class="dist-tag">{{ distanceText }}</text>
				<text v-else class="dist-tag unknown">距离未知</text>
			</view>
			<view class="action-group">
				<view v-if="showShare" class="share-btn" @click.stop="handleShare">
					<IconFont name="share" :size="28" />
				</view>
				<view v-if="actionText" class="action-btn" @click.stop="handleAction">
					{{ actionText }}
				</view>
			</view>
		</view>
	</view>
</template>

<script>
import IconFont from '@/components/icon-font/icon-font.vue'
import { formatTime } from '@/utils/format'
import { getDistanceText } from '@/utils/distance'

export default {
	name: 'NeedCard',
	components: { IconFont },
	props: {
		need: {
			type: Object,
			required: true
		},
		actionText: {
			type: String,
			default: '接单'
		},
		showShare: {
			type: Boolean,
			default: true
		},
		userLat: {
			type: Number,
			default: 0
		},
		userLng: {
			type: Number,
			default: 0
		}
	},
	computed: {
		avatarText() {
			const name = this.need.publisher?.nickname || '匿'
			return name[0] || '匿'
		},
		avatarBg() {
			const name = this.need.publisher?.nickname || ''
			const colors = [
				'#F0FDF4', '#FEF9E7', '#F0F4FF', '#FDF2F8',
				'#FFF7ED', '#F0F9FF', '#FAF5FF', '#F0FDFA'
			]
			let hash = 0
			for (let i = 0; i < name.length; i++) {
				hash = name.charCodeAt(i) + ((hash << 5) - hash)
			}
			const index = Math.abs(hash) % colors.length
			return colors[index]
		},
		formattedTime() {
			return this.need.createdAt ? formatTime(this.need.createdAt) : ''
		},
		distanceText() {
			if (this.userLat && this.userLng && this.need.latitude && this.need.longitude) {
				return getDistanceText(this.userLat, this.userLng, this.need.latitude, this.need.longitude)
			}
			return ''
		}
	},
	methods: {
		handleClick() {
			this.$emit('click', this.need)
		},
		handleShare() {
			this.$emit('share', this.need)
		},
		handleAction() {
			this.$emit('action', this.need)
		}
	}
}
</script>

<style scoped>
.need-card {
	background: #FFFFFF;
	border-radius: 24rpx;
	padding: 32rpx;
	margin-bottom: 24rpx;
	box-shadow: 0 2rpx 12rpx rgba(0, 0, 0, 0.04);
}
.card-top {
	display: flex;
	justify-content: space-between;
	align-items: center;
	margin-bottom: 24rpx;
}
.user-info {
	display: flex;
	align-items: center;
	gap: 16rpx;
}
.avatar {
	width: 72rpx;
	height: 72rpx;
	border-radius: 50%;
	display: flex;
	align-items: center;
	justify-content: center;
	font-size: 28rpx;
	font-weight: 600;
	color: #1E293B;
}
.meta {
	display: flex;
	flex-direction: column;
	gap: 4rpx;
}
.name {
	font-size: 28rpx;
	font-weight: 600;
	color: #1E293B;
}
.time {
	font-size: 22rpx;
	color: #94A3B8;
}
.price {
	font-size: 36rpx;
	font-weight: 700;
	color: #10B981;
}
.card-body {
	margin-bottom: 24rpx;
}
.title-row {
	display: flex;
	align-items: center;
	gap: 12rpx;
	margin-bottom: 12rpx;
}
.urgent-badge {
	font-size: 20rpx;
	color: #EF4444;
	background: #FEF2F2;
	padding: 4rpx 12rpx;
	border-radius: 8rpx;
	font-weight: 600;
}
.title {
	font-size: 32rpx;
	font-weight: 600;
	color: #1E293B;
	flex: 1;
}
.desc {
	font-size: 26rpx;
	color: #64748B;
	line-height: 1.5;
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
.loc-wrap {
	display: flex;
	align-items: center;
	gap: 12rpx;
}
.loc-tag {
	display: flex;
	align-items: center;
	gap: 8rpx;
}
.loc-tag .icon {
	font-size: 24rpx;
	color: #94A3B8;
}
.loc-text {
	font-size: 24rpx;
	color: #64748B;
}
.dist-tag {
	font-size: 22rpx;
	color: #10B981;
	background: #F0FDF4;
	padding: 4rpx 12rpx;
	border-radius: 8rpx;
}
.dist-tag.unknown {
	color: #94A3B8;
	background: #F1F5F9;
}
.action-group {
	display: flex;
	align-items: center;
	gap: 16rpx;
}
.share-btn {
	width: 56rpx;
	height: 56rpx;
	display: flex;
	align-items: center;
	justify-content: center;
	color: #94A3B8;
}
.action-btn {
	background: #10B981;
	color: #FFFFFF;
	font-size: 26rpx;
	font-weight: 600;
	padding: 12rpx 32rpx;
	border-radius: 100rpx;
}
</style>
