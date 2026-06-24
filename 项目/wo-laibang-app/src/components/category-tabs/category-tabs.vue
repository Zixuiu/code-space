<template>
	<scroll-view class="category-tabs" scroll-x :show-scrollbar="false">
		<view
			v-for="(item, index) in categories"
			:key="item.name || index"
			class="tab-item"
			:class="{ active: current === (item.name || item) }"
			@click="handleSelect(item)"
		>
			<view v-if="item.icon" class="tab-icon-wrap" :style="{ background: item.bgColor || '#F0FDF4' }">
				<IconFont :name="item.icon" :size="32" />
			</view>
			<text class="tab-text">{{ item.name || item }}</text>
		</view>
	</scroll-view>
</template>

<script>
import IconFont from '@/components/icon-font/icon-font.vue'

export default {
	name: 'CategoryTabs',
	components: { IconFont },
	props: {
		categories: {
			type: Array,
			required: true
		},
		current: {
			type: String,
			default: ''
		},
		mode: {
			type: String,
			default: 'text'
		}
	},
	methods: {
		handleSelect(item) {
			const name = item.name || item
			this.$emit('change', name, item)
		}
	}
}
</script>

<style scoped>
.category-tabs {
	white-space: nowrap;
	padding: 20rpx 0;
}
.tab-item {
	display: inline-flex;
	flex-direction: column;
	align-items: center;
	padding: 16rpx 28rpx;
	margin-right: 16rpx;
	border-radius: 16rpx;
	gap: 8rpx;
}
.tab-item:last-child {
	margin-right: 0;
}
.tab-item.active {
	background: #F0FDF4;
}
.tab-icon-wrap {
	width: 72rpx;
	height: 72rpx;
	border-radius: 20rpx;
	display: flex;
	align-items: center;
	justify-content: center;
}
.tab-text {
	font-size: 26rpx;
	color: #64748B;
	white-space: nowrap;
}
.tab-item.active .tab-text {
	color: #10B981;
	font-weight: 600;
}
</style>
