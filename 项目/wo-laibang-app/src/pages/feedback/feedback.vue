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
	padding: 44px 24px 20px;
	background: #FFFFFF;
}

.header-title {
	flex: 1;
	font-size: 18px;
	font-weight: 800;
	color: #1E293B;
	text-align: center;
}

.header-right {
	width: 44px;
}

.content-scroll {
	height: calc(100vh - 72px);
}

.type-section {
	padding: 24px 24px 16px;
}

.section-title {
	font-size: 15px;
	font-weight: 800;
	color: #1E293B;
	display: block;
	margin-bottom: 14px;
}

.type-grid {
	display: grid;
	grid-template-columns: repeat(3, 1fr);
	gap: 12px;
}

.type-item {
	background: #FFFFFF;
	border-radius: 16px;
	padding: 20px 12px;
	text-align: center;
	border: 2px solid transparent;
	transition: all 0.2s;
	box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
}

.type-item.selected {
	border-color: #10B981;
	background: #F0FDF4;
}

.type-icon {
	display: block;
	margin: 0 auto 10px;
}

.type-name {
	font-size: 12px;
	font-weight: 600;
	color: #64748B;
}

.type-item.selected .type-name {
	color: #10B981;
}

.content-section {
	padding: 0 24px 16px;
}

.textarea-card {
	background: #FFFFFF;
	border-radius: 16px;
	padding: 16px;
	box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
}

.textarea {
	width: 100%;
	font-size: 15px;
	font-weight: 600;
	color: #1E293B;
	border: none;
	outline: none;
	background: transparent;
	resize: none;
	line-height: 1.6;
}

.word-count {
	font-size: 12px;
	color: #94A3B8;
	text-align: right;
	display: block;
	margin-top: 8px;
}

.contact-section {
	padding: 0 24px 16px;
}

.input-card {
	background: #FFFFFF;
	border-radius: 16px;
	padding: 14px 16px;
	display: flex;
	align-items: center;
	gap: 12px;
	box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
}

.input-icon {
	font-size: 18px;
	width: 20px;
	text-align: center;
}

.input-field {
	flex: 1;
	font-size: 15px;
	font-weight: 600;
	color: #1E293B;
	border: none;
	outline: none;
	background: transparent;
}

.submit-section {
	padding: 16px 24px;
}

.btn-primary {
	width: 100%;
	height: 52px;
	background: linear-gradient(135deg, #10B981, #059669);
	color: #FFFFFF;
	border-radius: 26px;
	font-weight: 800;
	font-size: 16px;
	border: none;
	box-shadow: 0 8px 24px rgba(16, 185, 129, 0.35);
	display: flex;
	align-items: center;
	justify-content: center;
	transition: all 0.3s;
}

.btn-primary:active:not(:disabled) {
	transform: translateY(-2px);
	box-shadow: 0 12px 32px rgba(16, 185, 129, 0.4);
}

.btn-primary:disabled {
	opacity: 0.5;
	box-shadow: none;
}

.tips-section {
	margin: 0 24px;
	padding: 16px;
	background: #F0FDF4;
	border-radius: 14px;
}

.tips-header {
	display: flex;
	align-items: center;
	margin-bottom: 10px;
}

.tips-icon {
	font-size: 18px;
	width: 20px;
	text-align: center;
	margin-right: 8px;
}

.tips-title {
	font-size: 13px;
	font-weight: 700;
	color: #059669;
}

.tips-text {
	font-size: 12px;
	color: #64748B;
	display: block;
	margin-bottom: 4px;
}

.bottom-safe {
	height: 40px;
}
</style>