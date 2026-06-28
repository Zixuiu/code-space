<template>
	<view class="guide-container">
		<swiper
			class="guide-swiper"
			:current="currentIndex"
			@change="onSwiperChange"
			:circular="false"
		>
			<swiper-item v-for="(page, index) in pages" :key="index">
				<view class="guide-page">
					<view class="guide-icon-wrapper">
						<text class="guide-icon">{{ page.icon }}</text>
					</view>
					<view class="guide-text-wrapper">
						<text class="guide-title">{{ page.title }}</text>
						<text class="guide-desc">{{ page.desc }}</text>
					</view>
				</view>
			</swiper-item>
		</swiper>

		<view class="indicator">
			<view
				v-for="(page, index) in pages"
				:key="index"
				class="dot"
				:class="{ active: currentIndex === index }"
			></view>
		</view>

		<view class="action-btn" v-if="currentIndex === pages.length - 1" @click="startExperience">
			<text class="btn-text">开始体验</text>
		</view>

		<view class="skip-btn" v-else @click="startExperience">
			<text class="skip-text">跳过</text>
		</view>
	</view>
</template>

<script>
export default {
	data() {
		return {
			currentIndex: 0,
			pages: [
				{
					icon: '📋',
					title: '轻松发布需求',
					desc: '一键发布各类生活需求，找到靠谱帮手'
				},
				{
					icon: '💬',
					title: '实时聊天沟通',
					desc: '与帮手实时交流，确保需求准确完成'
				},
				{
					icon: '🛡️',
					title: '安全交易保障',
					desc: '平台托管资金，满意后再确认付款'
				},
				{
					icon: '🤝',
					title: '邻里互助',
					desc: '互帮互助，传递温暖，共建和谐社区'
				}
			]
		}
	},
	onLoad() {
	},
	methods: {
		onSwiperChange(e) {
			this.currentIndex = e.detail.current
		},
		startExperience() {
			uni.setStorageSync('hasSeenGuide', true)
			uni.switchTab({ url: '/pages/index/index' })
		}
	}
}
</script>

<style scoped>
.guide-container {
	min-height: 100vh;
	background: linear-gradient(180deg, #FFFFFF 0%, #F0FDF4 100%);
	position: relative;
}

.guide-swiper {
	height: calc(100vh - 280rpx);
}

.guide-page {
	display: flex;
	flex-direction: column;
	align-items: center;
	justify-content: center;
	padding: 60rpx 60rpx;
}

.guide-icon-wrapper {
	width: 320rpx;
	height: 320rpx;
	background: linear-gradient(135deg, #10B981 0%, #34D399 100%);
	border-radius: 80rpx;
	display: flex;
	align-items: center;
	justify-content: center;
	margin-bottom: 80rpx;
	box-shadow: 0 24rpx 48rpx rgba(16, 185, 129, 0.25);
}

.guide-icon {
	font-size: 160rpx;
}

.guide-text-wrapper {
	text-align: center;
}

.guide-title {
	font-size: 48rpx;
	font-weight: 800;
	color: #1E293B;
	display: block;
	margin-bottom: 24rpx;
}

.guide-desc {
	font-size: 28rpx;
	color: #64748B;
	line-height: 1.6;
	max-width: 500rpx;
	display: block;
}

.indicator {
	display: flex;
	justify-content: center;
	gap: 16rpx;
	padding: 60rpx 0;
}

.dot {
	width: 16rpx;
	height: 16rpx;
	border-radius: 8rpx;
	background: #E2E8F0;
	transition: all 0.3s;
}

.dot.active {
	width: 48rpx;
	background: #10B981;
}

.action-btn {
	position: absolute;
	bottom: 160rpx;
	left: 60rpx;
	right: 60rpx;
	height: 100rpx;
	background: linear-gradient(135deg, #10B981, #059669);
	border-radius: 50rpx;
	display: flex;
	align-items: center;
	justify-content: center;
	box-shadow: 0 8rpx 24rpx rgba(16, 185, 129, 0.35);
}

.btn-text {
	color: #FFFFFF;
	font-size: 32rpx;
	font-weight: 700;
}

.skip-btn {
	position: absolute;
	bottom: 160rpx;
	left: 60rpx;
	right: 60rpx;
	height: 100rpx;
	background: #F1F5F9;
	border-radius: 50rpx;
	display: flex;
	align-items: center;
	justify-content: center;
}

.skip-text {
	color: #64748B;
	font-size: 32rpx;
	font-weight: 600;
}
</style>
