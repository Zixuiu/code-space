<template>
	<view class="container">
		<view class="header">
			<text class="header-title">投诉</text>
			<view class="header-right"></view>
		</view>

		<scroll-view class="content-scroll" scroll-y>
			<view v-if="!orderId" class="order-select-section">
				<view class="section-title">选择投诉订单</view>
				<view class="order-list">
					<view
						v-for="order in availableOrders"
						:key="order.id"
						class="order-item"
						:class="{ selected: selectedOrder?.id === order.id }"
						@click="selectOrder(order)"
					>
						<view class="order-info">
							<text class="order-title">{{ order.title }}</text>
							<text class="order-reward">酬劳 ¥{{ order.reward }}</text>
						</view>
						<view class="order-check" v-if="selectedOrder?.id === order.id">
							<IconFont name="check-circle" :size="22" />
						</view>
					</view>
					<view v-if="availableOrders.length === 0" class="empty-orders">
						<text>暂无可投诉的订单</text>
					</view>
				</view>
			</view>

			<view v-else class="complaint-form">
				<view class="selected-order-card">
					<text class="card-label">投诉订单</text>
					<view class="order-detail">
						<text class="order-title">{{ selectedOrder?.title }}</text>
						<text class="order-reward">酬劳 ¥{{ selectedOrder?.reward }}</text>
					</view>
					<view class="change-order" @click="changeOrder">
						<text>更换订单</text>
					</view>
				</view>
			</view>

			<view class="section-title" v-if="orderId">投诉类型</view>
			<view class="type-grid" v-if="orderId">
				<view
					v-for="type in complaintTypes"
					:key="type.value"
					class="type-item"
					:class="{ selected: selectedType === type.value }"
					@click="selectType(type.value)"
				>
					<IconFont :name="type.icon" :size="24" class="type-icon" />
					<text class="type-label">{{ type.label }}</text>
				</view>
			</view>

			<view class="section-title" v-if="orderId">投诉描述</view>
			<view class="desc-section" v-if="orderId">
				<textarea
					class="desc-input"
					v-model="description"
					placeholder="请详细描述您遇到的问题（至少10个字）"
					@input="onDescInput"
				/>
				<text class="desc-count">{{ description.length }}/200</text>
			</view>

			<view class="section-title" v-if="orderId">上传证据</view>
			<view class="upload-section" v-if="orderId">
				<view class="upload-grid">
					<view
						v-for="(img, index) in images"
						:key="index"
						class="upload-item"
					>
						<image :src="img" mode="aspectFill" class="upload-image" />
						<view class="upload-remove" @click="removeImage(index)">
							<IconFont name="x" :size="14" />
						</view>
					</view>
					<view v-if="images.length < 3" class="upload-add" @click="chooseImage">
						<IconFont name="plus" :size="28" />
						<text class="upload-text">添加图片</text>
					</view>
				</view>
				<text class="upload-hint">最多上传3张图片作为证据</text>
			</view>

			<view class="section-title" v-if="orderId">联系方式</view>
			<view class="contact-section" v-if="orderId">
				<input
					class="contact-input"
					v-model="contact"
					placeholder="请输入手机号码"
					type="number"
					maxlength="11"
				/>
			</view>

			<view class="agreement-section" v-if="orderId">
				<view
					class="checkbox"
					:class="{ checked: agreed }"
					@click="agreed = !agreed"
				>
					<IconFont v-if="agreed" name="check" :size="14" />
				</view>
				<text class="agreement-text">
					我已阅读并同意<text class="link" @click.stop="goTerms">《投诉协议》</text>
				</text>
			</view>

			<button
				class="submit-btn"
				:class="{ disabled: !canSubmit }"
				@click="handleSubmit"
				:disabled="!canSubmit || isSubmitting"
				v-if="orderId"
			>
				<view v-if="isSubmitting" class="spinner"></view>
				<text v-else>提交投诉</text>
			</button>

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
			orderId: '',
			selectedOrder: null,
			selectedType: '',
			description: '',
			images: [],
			contact: '',
			agreed: false,
			isSubmitting: false,
			complaintTypes: [
				{ value: 'service', label: '未完成服务', icon: 'alert-circle' },
				{ value: 'attitude', label: '态度恶劣', icon: 'frown' },
				{ value: 'price', label: '收费不合理', icon: 'dollar-sign' },
				{ value: 'other', label: '其他问题', icon: 'help-circle' }
			]
		}
	},
	computed: {
		availableOrders() {
			const orders = uni.getStorageSync('orders') || []
			return orders.filter(o => o.status === 'completed' || o.status === 'cancelled')
		},
		canSubmit() {
			return this.orderId &&
				this.selectedType &&
				this.description.length >= 10 &&
				this.contact.length === 11 &&
				this.agreed
		}
	},
	onLoad(options) {
		if (options.orderId) {
			this.orderId = options.orderId
			const orders = uni.getStorageSync('orders') || []
			this.selectedOrder = orders.find(o => o.id == options.orderId)
		}
	},
	onShow() {
		uni.hideTabBar()
	},
	methods: {
		selectOrder(order) {
			this.selectedOrder = order
			this.orderId = order.id
		},
		changeOrder() {
			this.selectedOrder = null
			this.orderId = ''
			this.selectedType = ''
			this.description = ''
			this.images = []
			this.contact = ''
			this.agreed = false
		},
		selectType(type) {
			this.selectedType = type
		},
		onDescInput() {
		},
		chooseImage() {
			if (this.images.length >= 3) {
				uni.showToast({ title: '最多上传3张图片', icon: 'none' })
				return
			}
			uni.chooseImage({
				count: 3 - this.images.length,
				success: (res) => {
					this.images = [...this.images, ...res.tempFilePaths]
				}
			})
		},
		removeImage(index) {
			this.images.splice(index, 1)
		},
		async handleSubmit() {
			if (!this.canSubmit || this.isSubmitting) return

			const isConfirmed = await new Promise((resolve) => {
				uni.showModal({
					title: '确认提交',
					content: '确定要提交此投诉吗？',
					confirmColor: '#10B981',
					success: (res) => resolve(res.confirm)
				})
			})

			if (!isConfirmed) return

			this.isSubmitting = true

			setTimeout(() => {
				const complaints = uni.getStorageSync('complaints') || []
				const newComplaint = {
					id: Date.now(),
					orderId: this.orderId,
					orderTitle: this.selectedOrder?.title,
					type: this.selectedType,
					description: this.description,
					images: this.images,
					contact: this.contact,
					status: 'pending',
					createdAt: Date.now()
				}
				complaints.unshift(newComplaint)
				uni.setStorageSync('complaints', complaints)

				const notifications = uni.getStorageSync('notifications') || []
				notifications.unshift({
					id: Date.now(),
					type: 'system',
					title: '投诉已提交',
					content: '您的投诉已提交，客服将在24小时内处理',
					read: false,
					createdAt: Date.now()
				})
				uni.setStorageSync('notifications', notifications)

				this.isSubmitting = false
				uni.showToast({ title: '投诉提交成功', icon: 'success' })

				setTimeout(() => {
					uni.navigateBack()
				}, 1500)
			}, 1500)
		},
		goTerms() {
			uni.navigateTo({ url: '/pages/terms-of-service/terms-of-service' })
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
	font-size: 18px;
	font-weight: 800;
	color: #1E293B;
	text-align: center;
}

.header-right {
	width: 40px;
}

.content-scroll {
	height: calc(100vh - 89px);
	padding: 24rpx;
}

.section-title {
	font-size: 28rpx;
	font-weight: 700;
	color: #1E293B;
	margin-bottom: 20rpx;
}

.order-select-section {
	margin-bottom: 32rpx;
}

.order-list {
	background: #FFFFFF;
	border-radius: 20rpx;
	overflow: hidden;
}

.order-item {
	display: flex;
	align-items: center;
	justify-content: space-between;
	padding: 24rpx;
	border-bottom: 1rpx solid #F1F5F9;
}

.order-item:last-child {
	border-bottom: none;
}

.order-item.selected {
	background: #F0FDF4;
}

.order-info {
	flex: 1;
}

.order-title {
	font-size: 28rpx;
	font-weight: 700;
	color: #1E293B;
	display: block;
	margin-bottom: 6rpx;
}

.order-reward {
	font-size: 24rpx;
	color: #10B981;
}

.order-check {
	color: #10B981;
}

.empty-orders {
	padding: 48rpx;
	text-align: center;
	color: #94A3B8;
	font-size: 26rpx;
}

.selected-order-card {
	background: #F0FDF4;
	border-radius: 16rpx;
	padding: 24rpx;
	margin-bottom: 32rpx;
}

.card-label {
	font-size: 22rpx;
	color: #059669;
	font-weight: 700;
	display: block;
	margin-bottom: 12rpx;
}

.order-detail {
	margin-bottom: 12rpx;
}

.change-order {
	font-size: 24rpx;
	color: #10B981;
	font-weight: 600;
}

.type-grid {
	display: grid;
	grid-template-columns: repeat(2, 1fr);
	gap: 16rpx;
	margin-bottom: 32rpx;
}

.type-item {
	background: #FFFFFF;
	border-radius: 16rpx;
	padding: 28rpx 20rpx;
	text-align: center;
	border: 2rpx solid #E2E8F0;
	transition: all 0.2s;
}

.type-item.selected {
	border-color: #10B981;
	background: #F0FDF4;
}

.type-icon {
	color: #64748B;
	margin-bottom: 12rpx;
}

.type-item.selected .type-icon {
	color: #10B981;
}

.type-label {
	font-size: 26rpx;
	font-weight: 600;
	color: #1E293B;
}

.desc-section {
	background: #FFFFFF;
	border-radius: 16rpx;
	padding: 24rpx;
	margin-bottom: 32rpx;
	position: relative;
}

.desc-input {
	width: 100%;
	height: 200rpx;
	font-size: 28rpx;
	color: #1E293B;
	border: none;
	outline: none;
	resize: none;
}

.desc-count {
	position: absolute;
	bottom: 16rpx;
	right: 24rpx;
	font-size: 22rpx;
	color: #94A3B8;
}

.upload-section {
	margin-bottom: 32rpx;
}

.upload-grid {
	display: flex;
	flex-wrap: wrap;
	gap: 16rpx;
	margin-bottom: 12rpx;
}

.upload-item {
	width: 200rpx;
	height: 200rpx;
	border-radius: 12rpx;
	position: relative;
	overflow: hidden;
}

.upload-image {
	width: 100%;
	height: 100%;
}

.upload-remove {
	position: absolute;
	top: 8rpx;
	right: 8rpx;
	width: 40rpx;
	height: 40rpx;
	background: rgba(0, 0, 0, 0.5);
	border-radius: 50%;
	display: flex;
	align-items: center;
	justify-content: center;
	color: #FFFFFF;
}

.upload-add {
	width: 200rpx;
	height: 200rpx;
	background: #FFFFFF;
	border-radius: 12rpx;
	border: 2rpx dashed #CBD5E1;
	display: flex;
	flex-direction: column;
	align-items: center;
	justify-content: center;
	color: #94A3B8;
}

.upload-text {
	font-size: 22rpx;
	margin-top: 8rpx;
}

.upload-hint {
	font-size: 22rpx;
	color: #94A3B8;
}

.contact-section {
	margin-bottom: 32rpx;
}

.contact-input {
	background: #FFFFFF;
	border-radius: 16rpx;
	padding: 24rpx;
	font-size: 28rpx;
	border: 2rpx solid #E2E8F0;
}

.agreement-section {
	display: flex;
	align-items: center;
	gap: 12rpx;
	margin-bottom: 32rpx;
}

.checkbox {
	width: 36rpx;
	height: 36rpx;
	border: 2rpx solid #CBD5E1;
	border-radius: 8rpx;
	display: flex;
	align-items: center;
	justify-content: center;
	background: #FFFFFF;
}

.checkbox.checked {
	background: #10B981;
	border-color: #10B981;
	color: #FFFFFF;
}

.agreement-text {
	font-size: 24rpx;
	color: #64748B;
}

.agreement-text .link {
	color: #10B981;
	font-weight: 600;
}

.submit-btn {
	width: 100%;
	height: 100rpx;
	background: linear-gradient(135deg, #10B981, #059669);
	color: #FFFFFF;
	border-radius: 50rpx;
	font-size: 32rpx;
	font-weight: 800;
	border: none;
	display: flex;
	align-items: center;
	justify-content: center;
	box-shadow: 0 8rpx 24rpx rgba(16, 185, 129, 0.35);
}

.submit-btn.disabled {
	opacity: 0.5;
	box-shadow: none;
}

.spinner {
	width: 40rpx;
	height: 40rpx;
	border: 4rpx solid rgba(255, 255, 255, 0.3);
	border-top-color: #FFFFFF;
	border-radius: 50%;
	animation: spin 0.8s linear infinite;
}

@keyframes spin {
	to { transform: rotate(360deg); }
}

.bottom-space {
	height: 40rpx;
}
</style>