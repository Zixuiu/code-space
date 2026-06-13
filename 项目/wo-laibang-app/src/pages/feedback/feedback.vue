<template>
	<view class="feedback-container">
		<view class="header">
			<text class="header-title">意见反馈</text>
			<view class="header-right"></view>
		</view>

		<scroll-view class="content-scroll" scroll-y>
			<view class="type-section">
				<text class="section-title">反馈类型</text>
				<view class="type-grid">
					<view
						v-for="type in feedbackTypes"
						:key="type.value"
						class="type-item"
						:class="{ selected: selectedType === type.value }"
						@click="selectedType = type.value"
					>
						<IconFont :name="type.icon" :size="72" class="type-icon" />
						<text class="type-name">{{ type.name }}</text>
					</view>
				</view>
			</view>

			<view class="content-section">
				<text class="section-title">反馈内容</text>
				<view class="textarea-card">
					<textarea
						class="textarea"
						v-model="content"
						placeholder="请详细描述您遇到的问题或提出的建议..."
						maxlength="500"
						rows="6"
					></textarea>
					<text class="word-count">{{ content.length }}/500</text>
				</view>
			</view>

			<view class="contact-section">
				<text class="section-title">联系方式（选填）</text>
				<view class="input-card">
					<text class="input-icon"><IconFont name="mail" :size="32" /></text>
					<input
						class="input-field"
						v-model="contact"
						placeholder="手机号或邮箱"
						type="text"
					/>
				</view>
			</view>

			<view class="submit-section">
				<button class="btn-primary" @click="submitFeedback" :disabled="!canSubmit">
					<text>提交反馈</text>
				</button>
			</view>

			<view class="tips-section">
				<view class="tips-header">
					<text class="tips-icon"><IconFont name="bell" :size="32" /></text>
					<text class="tips-title">温馨提示</text>
				</view>
				<text class="tips-text">• 我们重视每一位用户的反馈</text>
				<text class="tips-text">• 您的反馈将帮助我们做得更好</text>
				<text class="tips-text">• 我们会在1-3个工作日内回复您</text>
			</view>

			<view class="bottom-safe"></view>
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
			feedbackTypes: [
			{ icon: 'alert', name: '功能异常', value: 'bug' },
			{ icon: 'sparkles', name: '功能建议', value: 'suggest' },
			{ icon: 'bolt', name: '体验优化', value: 'optimize' },
			{ icon: 'lock', name: '安全问题', value: 'security' },
			{ icon: 'help', name: '其他问题', value: 'other' }
		],
			selectedType: 'suggest',
			content: '',
			contact: ''
		}
	},
	computed: {
		canSubmit() {
			return this.content.trim().length >= 10
		}
	},
	methods: {
		submitFeedback() {
			if (!this.canSubmit) {
				uni.showToast({ title: '请至少输入10个字符', icon: 'none' })
				return
			}

			uni.showLoading({ title: '提交中...' })

			setTimeout(() => {
				uni.hideLoading()
				uni.showToast({
					title: '反馈已提交',
					icon: 'success'
				})

				setTimeout(() => {
					uni.navigateBack()
				}, 1500)
			}, 1500)
		},
		}
}
</script>

<style scoped>
.feedback-container {
	min-height: 100vh;
	background: #F8FAFC;
}

.header {
	display: flex;
	align-items: center;
	justify-content: space-between;
	padding: 80rpx 48rpx 40rpx;
	background: #FFFFFF;
}

.header-title {
	flex: 1;
	font-size: 36rpx;
	font-weight: 800;
	color: #1E293B;
	text-align: center;
}

.header-right {
	width: 88rpx;
}

.content-scroll {
	height: calc(100vh - 144rpx);
}

.type-section {
	padding: 48rpx 48rpx 32rpx;
}

.section-title {
	font-size: 30rpx;
	font-weight: 800;
	color: #1E293B;
	display: block;
	margin-bottom: 28rpx;
}

.type-grid {
	display: grid;
	grid-template-columns: repeat(3, 1fr);
	gap: 24rpx;
}

.type-item {
	background: #FFFFFF;
	border-radius: 32rpx;
	padding: 40rpx 24rpx;
	text-align: center;
	border: 4rpx solid transparent;
	transition: all 0.2s;
	box-shadow: 0 4rpx 16rpx rgba(0, 0, 0, 0.04);
}

.type-item.selected {
	border-color: #10B981;
	background: #F0FDF4;
}

.type-icon {
	display: block;
	margin: 0 auto 20rpx;
}

.type-name {
	font-size: 24rpx;
	font-weight: 600;
	color: #64748B;
}

.type-item.selected .type-name {
	color: #10B981;
}

.content-section {
	padding: 0 48rpx 32rpx;
}

.textarea-card {
	background: #FFFFFF;
	border-radius: 32rpx;
	padding: 32rpx;
	box-shadow: 0 4rpx 16rpx rgba(0, 0, 0, 0.04);
}

.textarea {
	width: 100%;
	font-size: 30rpx;
	font-weight: 600;
	color: #1E293B;
	border: none;
	outline: none;
	background: transparent;
	resize: none;
	line-height: 1.6;
}

.word-count {
	font-size: 24rpx;
	color: #94A3B8;
	text-align: right;
	display: block;
	margin-top: 16rpx;
}

.contact-section {
	padding: 0 48rpx 32rpx;
}

.input-card {
	background: #FFFFFF;
	border-radius: 32rpx;
	padding: 28rpx 32rpx;
	display: flex;
	align-items: center;
	gap: 24rpx;
	box-shadow: 0 4rpx 16rpx rgba(0, 0, 0, 0.04);
}

.input-icon {
	font-size: 36rpx;
	width: 40rpx;
	text-align: center;
}

.input-field {
	flex: 1;
	font-size: 30rpx;
	font-weight: 600;
	color: #1E293B;
	border: none;
	outline: none;
	background: transparent;
}

.submit-section {
	padding: 32rpx 48rpx;
}

.btn-primary {
	width: 100%;
	height: 104rpx;
	background: linear-gradient(135deg, #10B981, #059669);
	color: #FFFFFF;
	border-radius: 52rpx;
	font-weight: 800;
	font-size: 32rpx;
	border: none;
	box-shadow: 0 16rpx 48rpx rgba(16, 185, 129, 0.35);
	display: flex;
	align-items: center;
	justify-content: center;
	transition: all 0.3s;
}

.btn-primary:active:not(:disabled) {
	transform: translateY(-4rpx);
	box-shadow: 0 24rpx 64rpx rgba(16, 185, 129, 0.4);
}

.btn-primary:disabled {
	opacity: 0.5;
	box-shadow: none;
}

.tips-section {
	margin: 0 48rpx;
	padding: 32rpx;
	background: #F0FDF4;
	border-radius: 28rpx;
}

.tips-header {
	display: flex;
	align-items: center;
	margin-bottom: 20rpx;
}

.tips-icon {
	font-size: 36rpx;
	width: 40rpx;
	text-align: center;
	margin-right: 16rpx;
}

.tips-title {
	font-size: 26rpx;
	font-weight: 700;
	color: #059669;
}

.tips-text {
	font-size: 24rpx;
	color: #64748B;
	display: block;
	margin-bottom: 8rpx;
}

.bottom-safe {
	height: 80rpx;
}
</style>