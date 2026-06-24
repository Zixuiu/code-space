<template>
	<view class="empty-state">
		<view class="empty-icon-wrap" :style="{ background: iconBg }">
			<IconFont :name="icon" :size="iconSize" class="empty-icon" />
		</view>
		<text class="empty-title">{{ title }}</text>
		<text v-if="subtitle" class="empty-subtitle">{{ subtitle }}</text>
		<view v-if="actionText" class="empty-actions">
			<view class="action-btn" @click="handleAction">
				{{ actionText }}
			</view>
		</view>
	</view>
</template>

<script>
import IconFont from '@/components/icon-font/icon-font.vue'

export default {
	name: 'EmptyState',
	components: { IconFont },
	props: {
		icon: {
			type: String,
			default: 'inbox'
		},
		title: {
			type: String,
			default: '暂无数据'
		},
		subtitle: {
			type: String,
			default: ''
		},
		actionText: {
			type: String,
			default: ''
		},
		iconSize: {
			type: Number,
			default: 64
		},
		type: {
			type: String,
			default: 'default'
		}
	},
	computed: {
		iconBg() {
			const bgMap = {
				default: '#F8FAFC',
				search: '#F0FDF4',
				order: '#FEF9E7',
				message: '#F0F4FF',
				error: '#FEF2F2'
			}
			return bgMap[this.type] || bgMap.default
		}
	},
	methods: {
		handleAction() {
			this.$emit('action')
		}
	}
}
</script>

<style scoped>
.empty-state {
	display: flex;
	flex-direction: column;
	align-items: center;
	justify-content: center;
	padding: 80rpx 40rpx;
}
.empty-icon-wrap {
	width: 160rpx;
	height: 160rpx;
	border-radius: 50%;
	display: flex;
	align-items: center;
	justify-content: center;
	margin-bottom: 32rpx;
}
.empty-icon {
	color: #94A3B8;
}
.empty-title {
	font-size: 32rpx;
	font-weight: 600;
	color: #1E293B;
	margin-bottom: 12rpx;
}
.empty-subtitle {
	font-size: 26rpx;
	color: #94A3B8;
	text-align: center;
	line-height: 1.5;
}
.empty-actions {
	margin-top: 40rpx;
}
.action-btn {
	background: #10B981;
	color: #FFFFFF;
	font-size: 28rpx;
	font-weight: 600;
	padding: 20rpx 48rpx;
	border-radius: 100rpx;
}
</style>
