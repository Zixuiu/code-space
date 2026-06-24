<template>
	<view class="container">
		<view class="header">
			<text class="header-title">投诉详情</text>
			<view class="header-right"></view>
		</view>

		<scroll-view class="content-scroll" scroll-y v-if="complaint">
			<view class="status-card">
				<view class="status-icon" :class="complaint.status">
					<IconFont :name="getStatusIcon(complaint.status)" :size="32" />
				</view>
				<view class="status-info">
					<text class="status-title">{{ getStatusTitle(complaint.status) }}</text>
					<text class="status-desc">{{ getStatusDesc(complaint.status) }}</text>
				</view>
			</view>

			<view class="section">
				<view class="section-title">处理进度</view>
				<view class="timeline">
					<view
						v-for="(step, index) in progressSteps"
						:key="index"
						class="timeline-item"
						:class="{ completed: step.completed, current: step.current }"
					>
						<view class="timeline-marker">
							<view class="timeline-dot">
								<IconFont v-if="step.completed" name="check" :size="12" />
							</view>
							<view v-if="index < progressSteps.length - 1" class="timeline-line"></view>
						</view>
						<view class="timeline-content">
							<text class="timeline-title">{{ step.title }}</text>
							<text class="timeline-time" v-if="step.time">{{ step.time }}</text>
						</view>
					</view>
				</view>
			</view>

			<view class="section">
				<view class="section-title">投诉信息</view>
				<view class="info-card">
					<view class="info-row">
						<text class="info-label">投诉订单</text>
						<text class="info-value">{{ complaint.orderTitle }}</text>
					</view>
					<view class="info-row">
						<text class="info-label">投诉类型</text>
						<text class="info-value">{{ getTypeText(complaint.type) }}</text>
					</view>
					<view class="info-row">
						<text class="info-label">投诉时间</text>
						<text class="info-value">{{ formatTime(complaint.createdAt) }}</text>
					</view>
				</view>
			</view>

			<view class="section">
				<view class="section-title">投诉描述</view>
				<view class="desc-card">
					{{ complaint.description }}
				</view>
			</view>

			<view class="section" v-if="complaint.images && complaint.images.length > 0">
				<view class="section-title">证据图片</view>
				<view class="images-grid">
					<image
						v-for="(img, index) in complaint.images"
						:key="index"
						:src="img"
						mode="aspectFill"
						class="evidence-image"
						lazy-load="true"
						@click="previewImage(img)"
					/>
				</view>
			</view>

			<view class="section" v-if="complaint.replies && complaint.replies.length > 0">
				<view class="section-title">客服回复</view>
				<view class="replies-list">
					<view
						v-for="reply in complaint.replies"
						:key="reply.id"
						class="reply-item"
					>
						<view class="reply-header">
							<view class="reply-avatar cs">
								<IconFont name="headphones" :size="18" />
							</view>
							<text class="reply-name">客服小帮</text>
							<text class="reply-time">{{ formatTime(reply.createdAt) }}</text>
						</view>
						<view class="reply-content">
							{{ reply.content }}
						</view>
					</view>
				</view>
			</view>

			<view class="section" v-if="complaint.status === 'pending'">
				<view class="section-title">补充说明</view>
				<textarea
					class="supplement-input"
					v-model="supplement"
					placeholder="如有补充说明请在此输入..."
				/>
				<button class="supplement-btn" @click="submitSupplement">
					提交补充
				</button>
			</view>

			<view class="bottom-space"></view>
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
			complaintId: '',
			complaint: null,
			supplement: ''
		}
	},
	computed: {
		progressSteps() {
			if (!this.complaint) return []
			const steps = [
				{
					title: '提交投诉',
					time: this.formatTime(this.complaint.createdAt),
					completed: true,
					current: false
				},
				{
					title: '客服受理',
					time: this.complaint.acceptedAt ? this.formatTime(this.complaint.acceptedAt) : '',
					completed: !!this.complaint.acceptedAt,
					current: !this.complaint.acceptedAt && this.complaint.status === 'pending'
				},
				{
					title: '处理中',
					time: '',
					completed: this.complaint.status === 'resolved' || this.complaint.status === 'rejected',
					current: this.complaint.status === 'pending'
				},
				{
					title: this.complaint.status === 'resolved' ? '已解决' : this.complaint.status === 'rejected' ? '已驳回' : '等待结果',
					time: this.complaint.resolvedAt ? this.formatTime(this.complaint.resolvedAt) : '',
					completed: this.complaint.status === 'resolved' || this.complaint.status === 'rejected',
					current: false
				}
			]
			return steps
		}
	},
	onLoad(options) {
		if (options.id) {
			this.complaintId = options.id
			this.loadComplaint()
		}
	},
	onShow() {
		uni.hideTabBar()
	},
	methods: {
		loadComplaint() {
			const complaints = uni.getStorageSync('complaints') || []
			this.complaint = complaints.find(c => c.id == this.complaintId)
		},
		getStatusIcon(status) {
			const icons = {
				pending: 'clock',
				resolved: 'check-circle',
				rejected: 'x-circle'
			}
			return icons[status] || 'help-circle'
		},
		getStatusTitle(status) {
			const titles = {
				pending: '处理中',
				resolved: '已解决',
				rejected: '已驳回'
			}
			return titles[status] || '未知状态'
		},
		getStatusDesc(status) {
			const descs = {
				pending: '客服正在处理中，请耐心等待',
				resolved: '问题已解决，感谢您的反馈',
				rejected: '投诉已被驳回，如有疑问请联系客服'
			}
			return descs[status] || ''
		},
		getTypeText(type) {
			const typeMap = {
				service: '未完成服务',
				attitude: '态度恶劣',
				price: '收费不合理',
				other: '其他问题'
			}
			return typeMap[type] || type
		},
		formatTime(timestamp) {
			if (!timestamp) return ''
			const date = new Date(timestamp)
			const month = date.getMonth() + 1
			const day = date.getDate()
			const hour = date.getHours().toString().padStart(2, '0')
			const min = date.getMinutes().toString().padStart(2, '0')
			return `${month}月${day}日 ${hour}:${min}`
		},
		previewImage(img) {
			uni.previewImage({ urls: [img] })
		},
		submitSupplement() {
			if (!this.supplement.trim()) {
				uni.showToast({ title: '请输入补充内容', icon: 'none' })
				return
			}

			const complaints = uni.getStorageSync('complaints') || []
			const index = complaints.findIndex(c => c.id == this.complaintId)
			if (index !== -1) {
				if (!complaints[index].replies) {
					complaints[index].replies = []
				}
				complaints[index].replies.push({
					id: Date.now(),
					type: 'user',
					content: this.supplement,
					createdAt: Date.now()
				})
				uni.setStorageSync('complaints', complaints)
				this.complaint = complaints[index]
				this.supplement = ''
				uni.showToast({ title: '补充已提交', icon: 'success' })
			}
		},
		}
}
</script>

<style scoped>
.container {
	min-height: 100vh;
	background: #F8FAFC;
}

.header {
	display: flex;
	align-items: center;
	padding: 64rpx 24rpx 16rpx;
	background: #FFFFFF;
	gap: 16rpx;
	border-bottom: 1rpx solid #F1F5F9;
}

.header-title {
	flex: 1;
	font-size: 36rpx;
	font-weight: 800;
	color: #1E293B;
	text-align: center;
}

.header-right {
	width: 80rpx;
}

.content-scroll {
	height: calc(100vh - 178rpx);
	padding: 24rpx;
}

.status-card {
	background: #FFFFFF;
	border-radius: 20rpx;
	padding: 28rpx 24rpx;
	display: flex;
	align-items: center;
	gap: 20rpx;
	margin-bottom: 24rpx;
}

.status-icon {
	width: 80rpx;
	height: 80rpx;
	border-radius: 20rpx;
	display: flex;
	align-items: center;
	justify-content: center;
}

.status-icon.pending {
	background: #FEF3C7;
	color: #D97706;
}

.status-icon.resolved {
	background: #F0FDF4;
	color: #10B981;
}

.status-icon.rejected {
	background: #FEE2E2;
	color: #EF4444;
}

.status-info {
	flex: 1;
}

.status-title {
	font-size: 30rpx;
	font-weight: 700;
	color: #1E293B;
	display: block;
	margin-bottom: 6rpx;
}

.status-desc {
	font-size: 24rpx;
	color: #64748B;
}

.section {
	margin-bottom: 24rpx;
}

.section-title {
	font-size: 28rpx;
	font-weight: 700;
	color: #1E293B;
	margin-bottom: 16rpx;
}

.info-card {
	background: #FFFFFF;
	border-radius: 16rpx;
	padding: 20rpx 24rpx;
}

.info-row {
	display: flex;
	justify-content: space-between;
	padding: 12rpx 0;
	border-bottom: 1rpx solid #F1F5F9;
}

.info-row:last-child {
	border-bottom: none;
}

.info-label {
	font-size: 26rpx;
	color: #64748B;
}

.info-value {
	font-size: 26rpx;
	font-weight: 600;
	color: #1E293B;
}

.desc-card {
	background: #FFFFFF;
	border-radius: 16rpx;
	padding: 24rpx;
	font-size: 28rpx;
	color: #374151;
	line-height: 1.6;
}

.images-grid {
	display: flex;
	flex-wrap: wrap;
	gap: 12rpx;
}

.evidence-image {
	width: 200rpx;
	height: 200rpx;
	border-radius: 12rpx;
}

.replies-list {
	display: flex;
	flex-direction: column;
	gap: 16rpx;
}

.reply-item {
	background: #FFFFFF;
	border-radius: 16rpx;
	padding: 20rpx;
}

.reply-header {
	display: flex;
	align-items: center;
	margin-bottom: 12rpx;
}

.reply-avatar {
	width: 48rpx;
	height: 48rpx;
	border-radius: 50%;
	display: flex;
	align-items: center;
	justify-content: center;
	margin-right: 12rpx;
}

.reply-avatar.cs {
	background: #10B981;
	color: #FFFFFF;
}

.reply-name {
	font-size: 26rpx;
	font-weight: 700;
	color: #1E293B;
	margin-right: 12rpx;
}

.reply-time {
	font-size: 22rpx;
	color: #94A3B8;
}

.reply-content {
	font-size: 28rpx;
	color: #374151;
	line-height: 1.5;
}

.supplement-input {
	width: 100%;
	background: #FFFFFF;
	border-radius: 16rpx;
	padding: 24rpx;
	font-size: 28rpx;
	min-height: 160rpx;
	resize: none;
	margin-bottom: 16rpx;
}

.supplement-btn {
	width: 100%;
	height: 88rpx;
	background: linear-gradient(135deg, #10B981, #059669);
	color: #FFFFFF;
	border-radius: 44rpx;
	font-size: 30rpx;
	font-weight: 800;
	border: none;
}

.bottom-space {
	height: 40rpx;
}

/* 进度时间线 */
.timeline {
	background: #FFFFFF;
	border-radius: 16rpx;
	padding: 24rpx;
}

.timeline-item {
	display: flex;
	margin-bottom: 24rpx;
}

.timeline-item:last-child {
	margin-bottom: 0;
}

.timeline-marker {
	display: flex;
	flex-direction: column;
	align-items: center;
	margin-right: 16rpx;
}

.timeline-dot {
	width: 36rpx;
	height: 36rpx;
	border-radius: 50%;
	background: #E2E8F0;
	display: flex;
	align-items: center;
	justify-content: center;
	color: #FFFFFF;
}

.timeline-item.completed .timeline-dot {
	background: #10B981;
}

.timeline-item.current .timeline-dot {
	background: #10B981;
	box-shadow: 0 0 0 6rpx rgba(16, 185, 129, 0.2);
}

.timeline-line {
	width: 2rpx;
	flex: 1;
	min-height: 40rpx;
	background: #E2E8F0;
	margin-top: 8rpx;
}

.timeline-item.completed .timeline-line {
	background: #10B981;
}

.timeline-content {
	flex: 1;
	padding-top: 4rpx;
}

.timeline-title {
	font-size: 26rpx;
	font-weight: 600;
	color: #1E293B;
	display: block;
}

.timeline-item.completed .timeline-title {
	color: #10B981;
}

.timeline-item.current .timeline-title {
	color: #D97706;
}

.timeline-time {
	font-size: 22rpx;
	color: #94A3B8;
	margin-top: 4rpx;
	display: block;
}
</style>