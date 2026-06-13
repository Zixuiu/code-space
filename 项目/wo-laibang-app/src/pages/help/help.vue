<template>
	<view class="help-container">
		<view class="header">
			<text class="header-title">帮助中心</text>
			<view class="header-right"></view>
		</view>

		<scroll-view class="content-scroll" scroll-y>
			<view class="search-section">
				<view class="search-box">
					<IconFont name="search" :size="72" class="search-icon" />
					<input
						class="search-input"
						v-model="keyword"
						placeholder="搜索帮助内容"
					/>
				</view>
			</view>

			<view class="category-section">
				<text class="section-title">常见问题分类</text>
				<view class="category-grid">
					<view
						v-for="cat in categories"
						:key="cat.id"
						class="category-item"
						@click="selectCategory(cat)"
					>
						<view class="cat-icon"><IconFont :name="cat.icon" :size="48" /></view>
						<text class="cat-name">{{ cat.name }}</text>
					</view>
				</view>
			</view>

			<view class="faq-section">
				<text class="section-title">热门问题</text>
				<view v-if="filteredFaqs.length === 0 && keyword" class="empty-search">
					<IconFont name="search" :size="48" class="empty-icon" />
					<text class="empty-title">没有找到相关帮助</text>
					<text class="empty-desc">试试其他关键词，或联系客服获取帮助</text>
					<view class="empty-actions">
						<view class="action-btn" @click="keyword = ''">
							<text>清除搜索</text>
						</view>
						<view class="action-btn primary" @click="scrollToContact">
							<text>联系客服</text>
						</view>
					</view>
				</view>
				<view v-else class="faq-list">
					<view
						v-for="(faq, index) in filteredFaqs"
						:key="faq.id"
						class="faq-item"
						:class="{ expanded: expandedIndex === index }"
						@click="toggleFaq(index)"
					>
						<view class="faq-header">
							<text class="faq-q">{{ faq.question }}</text>
							<IconFont :name="expandedIndex === index ? 'chevron-up' : 'chevron-down'" :size="24" class="faq-arrow" />
						</view>
						<view v-if="expandedIndex === index" class="faq-answer">
							<text>{{ faq.answer }}</text>
						</view>
					</view>
				</view>
			</view>

			<view class="contact-section">
				<text class="section-title">没有找到答案？</text>
				<view class="contact-card">
					<view class="contact-item">
						<IconFont name="phone" :size="48" class="contact-icon" />
						<view class="contact-info">
							<view class="label-row">
							<IconFont name="phone-call" :size="24" class="label-icon" />
							<text class="contact-label">客服热线</text>
						</view>
							<text class="contact-value">400-888-8888</text>
						</view>
					</view>
					<view class="contact-item">
						<IconFont name="message" :size="48" class="contact-icon" />
						<view class="contact-info">
							<text class="contact-label">在线客服</text>
							<text class="contact-value">点击在线咨询</text>
						</view>
					</view>
				</view>
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
			keyword: '',
			expandedIndex: null,
			categories: [
				{ id: 1, icon: 'wallet', name: '账户与钱包' },
				{ id: 2, icon: 'lock', name: '账户安全' },
				{ id: 3, icon: 'clipboard-list', name: '订单问题' },
				{ id: 4, icon: 'coin', name: '支付问题' },
				{ id: 5, icon: 'circle-check', name: '认证问题' },
				{ id: 6, icon: 'sparkles', name: '使用技巧' }
			],
			faqs: [
				{
					id: 1,
					question: '如何充值余额？',
					answer: '进入"我的钱包"页面，点击"充值"按钮，选择充值金额和支付方式即可完成充值。'
				},
				{
					id: 2,
					question: '如何设置支付密码？',
					answer: '进入"隐私安全"页面，点击"设置支付密码"，按提示完成支付密码的设置。'
				},
				{
					id: 3,
					question: '忘记登录密码怎么办？',
					answer: '在登录页面点击"忘记密码"，通过手机验证码验证后即可重置密码。'
				},
				{
					id: 4,
					question: '如何联系客服？',
					answer: '您可以拨打客服热线400-888-8888，或者在App内点击"在线客服"进行咨询。'
				},
				{
					id: 5,
					question: '提现需要多长时间到账？',
					answer: '微信提现即时到账，银行卡提现1-3个工作日到账。'
				}
			]
		}
	},
	computed: {
		filteredFaqs() {
			if (!this.keyword) return this.faqs
			return this.faqs.filter(faq =>
				faq.question.includes(this.keyword) || faq.answer.includes(this.keyword)
			)
		}
	},
	methods: {
		selectCategory(cat) {
			uni.showToast({ title: cat.name, icon: 'none' })
		},
		toggleFaq(index) {
			this.expandedIndex = this.expandedIndex === index ? null : index
		},
		scrollToContact() {
			uni.showToast({ title: '联系客服：400-888-8888', icon: 'none' })
		},
		}
}
</script>

<style scoped>
.help-container {
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

.search-section {
	padding: 32rpx 48rpx;
}

.search-box {
	display: flex;
	align-items: center;
	background: #FFFFFF;
	border-radius: 48rpx;
	padding: 24rpx 40rpx;
	box-shadow: 0 4rpx 24rpx rgba(0, 0, 0, 0.04);
}

.search-icon {
	margin-right: 24rpx;
	display: flex;
	align-items: center;
}

.search-input {
	flex: 1;
	font-size: 30rpx;
	font-weight: 600;
	color: #1E293B;
	border: none;
	outline: none;
	background: transparent;
}

.category-section {
	padding: 0 48rpx 40rpx;
}

.section-title {
	font-size: 34rpx;
	font-weight: 800;
	color: #1E293B;
	display: block;
	margin-bottom: 32rpx;
}

.category-grid {
	display: grid;
	grid-template-columns: repeat(3, 1fr);
	gap: 24rpx;
}

.category-item {
	background: #FFFFFF;
	border-radius: 32rpx;
	padding: 40rpx 24rpx;
	text-align: center;
	box-shadow: 0 4rpx 24rpx rgba(0, 0, 0, 0.04);
}

.cat-icon {
	margin-bottom: 20rpx;
	display: flex;
	align-items: center;
	justify-content: center;
}

.cat-name {
	font-size: 24rpx;
	font-weight: 600;
	color: #1E293B;
}

.faq-section {
	padding: 0 48rpx 40rpx;
}

.faq-list {
	background: #FFFFFF;
	border-radius: 40rpx;
	overflow: hidden;
	box-shadow: 0 4rpx 24rpx rgba(0, 0, 0, 0.04);
}

.faq-item {
	padding: 32rpx 40rpx;
	border-bottom: 2rpx solid #F1F5F9;
}

.faq-item:last-child {
	border-bottom: none;
}

.faq-header {
	display: flex;
	justify-content: space-between;
	align-items: center;
}

.faq-q {
	font-size: 28rpx;
	font-weight: 700;
	color: #1E293B;
	flex: 1;
}

.faq-arrow {
	color: #94A3B8;
	margin-left: 24rpx;
	display: flex;
	align-items: center;
}

.faq-answer {
	margin-top: 24rpx;
	padding-top: 24rpx;
	border-top: 2rpx dashed #E2E8F0;
	font-size: 26rpx;
	color: #64748B;
	line-height: 1.6;
}

.contact-section {
	padding: 0 48rpx 48rpx;
}

.contact-card {
	background: linear-gradient(135deg, #10B981, #059669);
	border-radius: 40rpx;
	padding: 48rpx;
	box-shadow: 0 16rpx 48rpx rgba(16, 185, 129, 0.25);
}

.contact-item {
	display: flex;
	align-items: center;
	margin-bottom: 40rpx;
}

.contact-item:last-child {
	margin-bottom: 0;
}

.contact-icon {
	margin-right: 32rpx;
	display: flex;
	align-items: center;
	justify-content: center;
}

.contact-emoji {
	font-size: 56rpx;
	margin-right: 32rpx;
}

.contact-info {
	flex: 1;
}

.contact-label {
	font-size: 24rpx;
	color: rgba(255, 255, 255, 0.8);
}

.label-row {
	display: flex;
	align-items: center;
	margin-bottom: 8rpx;
}

.label-icon {
	margin-right: 12rpx;
}

.contact-value {
	font-size: 30rpx;
	font-weight: 700;
	color: #FFFFFF;
}

.bottom-safe {
	height: 80rpx;
}

.empty-search {
	background: #FFFFFF;
	border-radius: 40rpx;
	padding: 80rpx 48rpx;
	text-align: center;
	box-shadow: 0 4rpx 24rpx rgba(0, 0, 0, 0.04);
}

.empty-icon {
	display: block;
	margin-bottom: 32rpx;
}

.empty-title {
	font-size: 32rpx;
	font-weight: 700;
	color: #1E293B;
	display: block;
	margin-bottom: 16rpx;
}

.empty-desc {
	font-size: 26rpx;
	color: #94A3B8;
	display: block;
	margin-bottom: 48rpx;
}

.empty-actions {
	display: flex;
	gap: 24rpx;
	justify-content: center;
}

.action-btn {
	padding: 24rpx 48rpx;
	background: #F8FAFC;
	border-radius: 48rpx;
	font-size: 26rpx;
	font-weight: 600;
	color: #64748B;
}

.action-btn.primary {
	background: linear-gradient(135deg, #10B981, #059669);
	color: #FFFFFF;
}
</style>