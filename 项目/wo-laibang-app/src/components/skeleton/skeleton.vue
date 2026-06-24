<template>
	<view class="skeleton-wrap">
		<view v-for="i in rows" :key="i" class="skeleton-row">
			<view v-if="avatar" class="skeleton-avatar"></view>
			<view class="skeleton-content">
				<view class="skeleton-line skeleton-title"></view>
				<view class="skeleton-line skeleton-subtitle"></view>
				<view class="skeleton-line skeleton-desc"></view>
			</view>
		</view>
	</view>
</template>

<script>
export default {
	name: 'Skeleton',
	props: {
		rows: {
			type: Number,
			default: 3
		},
		avatar: {
			type: Boolean,
			default: true
		},
		loading: {
			type: Boolean,
			default: true
		}
	}
}
</script>

<style scoped>
.skeleton-wrap {
	padding: 24rpx;
}
.skeleton-row {
	display: flex;
	gap: 24rpx;
	padding: 24rpx 0;
	border-bottom: 1rpx solid #F1F5F9;
}
.skeleton-row:last-child {
	border-bottom: none;
}
.skeleton-avatar {
	width: 80rpx;
	height: 80rpx;
	border-radius: 50%;
	background: linear-gradient(90deg, #F1F5F9 25%, #E2E8F0 50%, #F1F5F9 75%);
	background-size: 200% 100%;
	animation: shimmer 1.5s infinite;
	flex-shrink: 0;
}
.skeleton-content {
	flex: 1;
	display: flex;
	flex-direction: column;
	gap: 16rpx;
	justify-content: center;
}
.skeleton-line {
	height: 24rpx;
	border-radius: 12rpx;
	background: linear-gradient(90deg, #F1F5F9 25%, #E2E8F0 50%, #F1F5F9 75%);
	background-size: 200% 100%;
	animation: shimmer 1.5s infinite;
}
.skeleton-title {
	width: 60%;
	height: 28rpx;
}
.skeleton-subtitle {
	width: 40%;
	height: 22rpx;
}
.skeleton-desc {
	width: 80%;
	height: 20rpx;
}
@keyframes shimmer {
	0% {
		background-position: 200% 0;
	}
	100% {
		background-position: -200% 0;
	}
}
</style>
