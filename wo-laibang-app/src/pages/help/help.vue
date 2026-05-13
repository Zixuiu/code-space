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

.search-section {
	padding: 16px 24px;
}

.search-box {
	display: flex;
	align-items: center;
	background: #FFFFFF;
	border-radius: 24px;
	padding: 12px 20px;
	box-shadow: 0 2px 12px rgba(0, 0, 0, 0.04);
}

.search-icon {
	margin-right: 12px;
	display: flex;
	align-items: center;
}

.search-input {
	flex: 1;
	font-size: 15px;
	font-weight: 600;
	color: #1E293B;
	border: none;
	outline: none;
	background: transparent;
}

.category-section {
	padding: 0 24px 20px;
}

.section-title {
	font-size: 17px;
	font-weight: 800;
	color: #1E293B;
	display: block;
	margin-bottom: 16px;
}

.category-grid {
	display: grid;
	grid-template-columns: repeat(3, 1fr);
	gap: 12px;
}

.category-item {
	background: #FFFFFF;
	border-radius: 16px;
	padding: 20px 12px;
	text-align: center;
	box-shadow: 0 2px 12px rgba(0, 0, 0, 0.04);
}

.cat-icon {
	margin-bottom: 10px;
	display: flex;
	align-items: center;
	justify-content: center;
}

.cat-name {
	font-size: 12px;
	font-weight: 600;
	color: #1E293B;
}

.faq-section {
	padding: 0 24px 20px;
}

.faq-list {
	background: #FFFFFF;
	border-radius: 20px;
	overflow: hidden;
	box-shadow: 0 2px 12px rgba(0, 0, 0, 0.04);
}

.faq-item {
	padding: 16px 20px;
	border-bottom: 1px solid #F1F5F9;
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
	font-size: 14px;
	font-weight: 700;
	color: #1E293B;
	flex: 1;
}

.faq-arrow {
	color: #94A3B8;
	margin-left: 12px;
	display: flex;
	align-items: center;
}

.faq-answer {
	margin-top: 12px;
	padding-top: 12px;
	border-top: 1px dashed #E2E8F0;
	font-size: 13px;
	color: #64748B;
	line-height: 1.6;
}

.contact-section {
	padding: 0 24px 24px;
}

.contact-card {
	background: linear-gradient(135deg, #10B981, #059669);
	border-radius: 20px;
	padding: 24px;
	box-shadow: 0 8px 24px rgba(16, 185, 129, 0.25);
}

.contact-item {
	display: flex;
	align-items: center;
	margin-bottom: 20px;
}

.contact-item:last-child {
	margin-bottom: 0;
}

.contact-icon {
	margin-right: 16px;
	display: flex;
	align-items: center;
	justify-content: center;
}

.contact-emoji {
	font-size: 28px;
	margin-right: 16px;
}

.contact-info {
	flex: 1;
}

.contact-label {
	font-size: 12px;
	color: rgba(255, 255, 255, 0.8);
}

.label-row {
	display: flex;
	align-items: center;
	margin-bottom: 4px;
}

.label-icon {
	margin-right: 6px;
}

.contact-value {
	font-size: 15px;
	font-weight: 700;
	color: #FFFFFF;
}

.bottom-safe {
	height: 40px;
}

.empty-search {
	background: #FFFFFF;
	border-radius: 20px;
	padding: 48px 24px;
	text-align: center;
	box-shadow: 0 2px 12px rgba(0, 0, 0, 0.04);
}

.empty-icon {
	display: block;
	margin-bottom: 16px;
}

.empty-title {
	font-size: 16px;
	font-weight: 700;
	color: #1E293B;
	display: block;
	margin-bottom: 8px;
}

.empty-desc {
	font-size: 13px;
	color: #94A3B8;
	display: block;
	margin-bottom: 24px;
}

.empty-actions {
	display: flex;
	gap: 12px;
	justify-content: center;
}

.action-btn {
	padding: 12px 24px;
	background: #F8FAFC;
	border-radius: 24px;
	font-size: 13px;
	font-weight: 600;
	color: #64748B;
}

.action-btn.primary {
	background: linear-gradient(135deg, #10B981, #059669);
	color: #FFFFFF;
}
</style>