<template>
	<view class="search-bar">
		<view class="search-input-wrap">
			<IconFont name="search" :size="32" class="search-icon" />
			<input
				class="search-input"
				type="text"
				:value="modelValue"
				:placeholder="placeholder"
				placeholder-class="search-placeholder"
				@input="handleInput"
				@focus="handleFocus"
				@blur="handleBlur"
				@confirm="handleConfirm"
			/>
			<view v-if="modelValue" class="clear-btn" @click="handleClear">
				<IconFont name="close" :size="28" />
			</view>
		</view>
	</view>
</template>

<script>
import IconFont from '@/components/icon-font/icon-font.vue'
import { debounce } from '@/utils/format'

export default {
	name: 'SearchBar',
	components: { IconFont },
	props: {
		modelValue: {
			type: String,
			default: ''
		},
		placeholder: {
			type: String,
			default: '搜索需求...'
		},
		debounceTime: {
			type: Number,
			default: 300
		}
	},
	data() {
		return {
			focused: false,
			debouncedInput: null
		}
	},
	created() {
		this.debouncedInput = debounce((value) => {
			this.$emit('update:modelValue', value)
			this.$emit('search', value)
		}, this.debounceTime)
	},
	methods: {
		handleInput(e) {
			const value = e.detail.value
			this.debouncedInput(value)
		},
		handleClear() {
			this.$emit('update:modelValue', '')
			this.$emit('search', '')
			this.$emit('clear')
		},
		handleFocus() {
			this.focused = true
			this.$emit('focus')
		},
		handleBlur() {
			this.focused = false
			this.$emit('blur')
		},
		handleConfirm(e) {
			this.$emit('confirm', e.detail.value)
		}
	}
}
</script>

<style scoped>
.search-bar {
	padding: 20rpx 0;
}
.search-input-wrap {
	display: flex;
	align-items: center;
	background: #F8FAFC;
	border-radius: 100rpx;
	padding: 16rpx 28rpx;
	gap: 16rpx;
}
.search-icon {
	font-size: 32rpx;
	color: #94A3B8;
	flex-shrink: 0;
}
.search-input {
	flex: 1;
	font-size: 28rpx;
	color: #1E293B;
	background: transparent;
}
.search-placeholder {
	color: #94A3B8;
}
.clear-btn {
	width: 40rpx;
	height: 40rpx;
	display: flex;
	align-items: center;
	justify-content: center;
	color: #94A3B8;
	flex-shrink: 0;
}
</style>
