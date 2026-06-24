<template>
	<view class="container">
		<!-- Header -->
		<view class="header">
			<text class="header-title">{{ currentStep === 1 ? '需求内容' : currentStep === 2 ? '地点时间' : currentStep === 3 ? '支付方式' : '发布成功' }}</text>

			<view class="header-right">
				<text class="test-btn" @click="fillTestData">测试</text>
			</view>
		</view>

		<view class="header-steps" style="padding:0 32rpx 16rpx;">
			<view class="hs-dot" :class="{ active: currentStep >= 1 }">1</view>
			<view class="hs-line" :class="{ active: currentStep >= 2 }"></view>
			<view class="hs-dot" :class="{ active: currentStep >= 2 }">2</view>
			<view class="hs-line" :class="{ active: currentStep >= 3 }"></view>
			<view class="hs-dot" :class="{ active: currentStep >= 3 }">3</view>
			<view class="hs-line" :class="{ active: currentStep >= 4 }"></view>
			<view class="hs-dot" :class="{ active: currentStep >= 4 }">4</view>
		</view>

		<!-- Content Area -->
		<view class="content-container">
			<!-- Step 1: 你想找人帮什么忙？ -->
			<view v-if="currentStep === 1" class="step-content animate-in">
				
				<view class="input-section">
					<view class="input-card">
						<text class="card-label">选择分类</text>
						<view class="category-grid">
							<view 
								v-for="(cat, index) in categories" 
								:key="index"
								class="category-item"
								:class="{ active: form.category === cat.name }"
								@click="selectCategory(cat.name)"
							>
								<IconFont :name="cat.icon" :size="40" class="cat-icon" />
								<text class="cat-name">{{ cat.name }}</text>
							</view>
						</view>
					</view>

					<view class="input-card" :class="{ focused: activeField === 'title' }">
						<text class="card-label">任务标题</text>
						<input
							class="card-input"
							placeholder="输入标题"
							v-model="form.title"
							@focus="activeField = 'title'"
							@blur="activeField = ''"
						/>
					</view>

					<view class="input-card textarea-card" :class="{ focused: activeField === 'description' }">
						<text class="card-label">详细描述 (可选)</text>
						<textarea 
							class="card-textarea" 
							placeholder="描述具体要求、物品重量等..."
							v-model="form.description"
							maxlength="500"
							@focus="activeField = 'description'"
							@blur="activeField = ''"
						/>
					</view>
					
					<view class="image-uploader" @click="chooseImage">
						<view v-if="!form.image" class="upload-placeholder">
							<IconFont name="camera" :size="72" class="camera-icon" />
							<text class="upload-text">添加现场照片 (可选)</text>
						</view>
						<view v-else class="preview-box">
							<image :src="form.image" mode="aspectFill" class="preview-img" lazy-load="true" />
							<view class="delete-img" @click.stop="deleteImage">×</view>
						</view>
					</view>
				</view>

				<view class="action-footer">
					<button class="next-btn" @click="nextStep">继续</button>
				</view>
			</view>

			<!-- Step 2: 具体地点和时间 -->
			<view v-if="currentStep === 2" class="step-content animate-in">
				<view class="input-section">
					<view class="input-card clickable" @click="openMapPicker" :class="{ focused: activeField === 'location' }">
						<text class="card-label">在哪里</text>
						<view class="location-display">
							<text class="loc-text" :class="{ placeholder: !form.location }">
								{{ form.location || '点击选择位置' }}
							</text>
							<IconFont name="map-pin" :size="32" class="map-marker" />
						</view>
					</view>

					<view v-if="form.location" class="input-card" :class="{ focused: activeField === 'detailAddress' }">
						<text class="card-label">详细地址</text>
						<input 
							class="card-input"
							placeholder="如：3栋2单元501室"
							v-model="form.detailAddress"
							@focus="activeField = 'detailAddress'"
							@blur="activeField = ''"
						/>
					</view>

					<view class="input-card clickable" :class="{ focused: activeField === 'time' }">
						<text class="card-label">什么时候要</text>
						<picker mode="multiSelector" :range="timeRange" :value="timeValue" @change="onTimeChange" @columnchange="onTimeColumnChange">
							<view class="location-display">
								<text class="loc-text" :class="{ placeholder: !form.time }">
									{{ form.time || '请选择时间' }}
								</text>
								<text class="map-marker">🕒</text>
							</view>
						</picker>
					</view>

					<view class="input-card clickable" :class="{ focused: activeField === 'deadline' }">
						<text class="card-label">最晚什么时候</text>
						<picker mode="multiSelector" :range="deadlineRange" :value="deadlineValue" @change="onDeadlineChange" @columnchange="onDeadlineColumnChange">
							<view class="location-display">
								<text class="loc-text" :class="{ placeholder: !form.deadline }">
									{{ form.deadline || '请选择截止时间' }}
								</text>
								<text class="map-marker">⏰</text>
							</view>
						</picker>
					</view>

					<view class="input-card" :class="{ focused: activeField === 'reward' }">
						<text class="card-label">预期报酬 (元)</text>
						<view class="reward-input-box">
							<text class="currency">¥</text>
							<input
								class="card-input amount"
								placeholder="0.00"
								v-model="form.reward"
								type="digit"
								@focus="activeField = 'reward'"
								@blur="activeField = ''"
							/>
						</view>
					</view>

					<view class="input-card urgent-toggle" :class="{ active: form.isUrgent }" @click="form.isUrgent = !form.isUrgent">
						<view class="urgent-left">
							<IconFont name="zap" :size="32" class="urgent-icon" />
							<view class="urgent-info">
								<text class="urgent-title">设为紧急订单</text>
								<text class="urgent-desc">紧急订单会在"急需帮手"区域优先展示</text>
							</view>
						</view>
						<view class="toggle-switch" :class="{ on: form.isUrgent }">
							<view class="toggle-knob"></view>
						</view>
					</view>
				</view>

				<view class="action-footer dual">
					<button class="back-link" @click="prevStep">上一步</button>
					<button class="next-btn" @click="nextStep">继续</button>
				</view>
			</view>

			<!-- Step 3: 支付方式 -->
			<view v-if="currentStep === 3" class="step-content animate-in">
				<view class="input-section">
					<view class="input-card">
						<text class="card-label">支付方式</text>
						<view class="payment-options">
							<view
								class="payment-option"
								:class="{ active: paymentMethod === 'wallet', disabled: walletBalance < form.reward }"
								@click="selectPayment('wallet')"
							>
								<view class="payment-left">
									<IconFont name="wallet" :size="28" class="payment-icon" />
									<view class="payment-info">
										<text class="payment-name">钱包余额</text>
										<text class="payment-balance">¥{{ walletBalance.toFixed(2) }}</text>
									</view>
								</view>
								<view class="payment-check">
									<IconFont v-if="paymentMethod === 'wallet'" name="check" :size="24" class="check-icon" />
								</view>
							</view>

							<view
								class="payment-option"
								:class="{ active: paymentMethod === 'wechat' }"
								@click="selectPayment('wechat')"
							>
								<view class="payment-left">
									<text class="payment-icon">💚</text>
									<view class="payment-info">
										<text class="payment-name">微信支付</text>
										<text class="payment-fee">需付0.6%手续费</text>
									</view>
								</view>
								<view class="payment-check">
									<view v-if="paymentMethod === 'wechat'" class="check-icon"><IconFont name="check" :size="24" /></view>
								</view>
							</view>

							<view
								class="payment-option"
								:class="{ active: paymentMethod === 'alipay' }"
								@click="selectPayment('alipay')"
							>
								<view class="payment-left">
									<text class="payment-icon">💙</text>
									<view class="payment-info">
										<text class="payment-name">支付宝</text>
										<text class="payment-fee">需付0.6%手续费</text>
									</view>
								</view>
								<view class="payment-check">
									<IconFont v-if="paymentMethod === 'alipay'" name="check" :size="24" class="check-icon" />
								</view>
							</view>
						</view>

						<view v-if="paymentMethod === 'wallet'" class="payment-tip success">
							<IconFont name="check" :size="24" style="margin-right: 12rpx;" />
							<text>使用钱包支付，0手续费</text>
						</view>
						<view v-else class="payment-tip warning">
							<IconFont name="sparkles" :size="24" style="margin-right: 12rpx;" />
							<text>建议使用钱包支付，0手续费更划算</text>
						</view>
					</view>

					<view class="order-summary-card">
						<text class="summary-label">订单摘要</text>
						<view class="summary-row">
							<text class="summary-key">任务标题</text>
							<text class="summary-value">{{ form.title || '未填写' }}</text>
						</view>
						<view class="summary-row">
							<text class="summary-key">服务地点</text>
							<text class="summary-value">{{ form.location || '未填写' }}</text>
						</view>
						<view class="summary-row">
							<text class="summary-key">服务时间</text>
							<text class="summary-value">{{ form.time || '未填写' }}</text>
						</view>
						<view class="summary-row total">
							<text class="summary-key">支付金额</text>
							<text class="summary-value price">¥{{ form.reward || '0.00' }}</text>
						</view>
					</view>
				</view>

				<view class="action-footer dual">
					<button class="back-link" @click="prevStep">上一步</button>
					<button class="next-btn" @click="handleSubmit">
						{{ isSubmitting ? '发布中...' : '确认发布' }}
					</button>
				</view>
			</view>

			<!-- Step 4: 发布成功 -->
			<view v-if="currentStep === 4" class="step-content success-step animate-in">
				<view class="success-icon">🎉</view>
				<view class="success-title">发布成功</view>
				<view class="success-desc">您的需求已发布，等待邻居来接单吧~</view>
				<view class="success-actions">
					<button class="action-btn primary" @click="goOrders">查看订单</button>
					<button class="action-btn secondary" @click="continuePublish">继续发布</button>
					<button class="action-btn ghost" @click="goHome">返回首页</button>
				</view>
			</view>
		</view>

		<!-- 自定义底部导航 -->
		<bottom-nav :current="1"></bottom-nav>

		<!-- 确认弹窗 -->
		<view v-if="confirmVisible" style="position:fixed;top:0;left:0;right:0;bottom:0;background:rgba(0,0,0,0.5);z-index:99999;display:flex;align-items:center;justify-content:center;" @click="confirmVisible = false">
			<view style="width:560rpx;background:#FFFFFF;border-radius:32rpx;overflow:hidden;" @click.stop>
				<view style="padding:40rpx 40rpx 20rpx;text-align:center;">
					<text style="font-size:34rpx;font-weight:700;color:#1E293B;">{{ confirmTitle }}</text>
				</view>
				<view style="padding:0 40rpx 30rpx;text-align:center;">
					<text style="font-size:28rpx;color:#64748B;line-height:1.6;">{{ confirmContent }}</text>
				</view>
				<view style="display:flex;border-top:1rpx solid #F1F5F9;">
					<view style="flex:1;height:96rpx;display:flex;align-items:center;justify-content:center;" v-if="confirmCancelText" @click="confirmVisible = false">
						<text style="font-size:30rpx;font-weight:600;color:#64748B;">{{ confirmCancelText }}</text>
					</view>
					<view style="flex:1;height:96rpx;display:flex;align-items:center;justify-content:center;border-left:1rpx solid #F1F5F9;" v-if="confirmCancelText" @click="confirmVisible = false; if(onConfirm) onConfirm()">
						<text style="font-size:30rpx;font-weight:700;color:#10B981;">{{ confirmConfirmText }}</text>
					</view>
					<view style="flex:1;height:96rpx;display:flex;align-items:center;justify-content:center;" v-else @click="confirmVisible = false; if(onConfirm) onConfirm()">
						<text style="font-size:30rpx;font-weight:700;color:#10B981;">{{ confirmConfirmText }}</text>
					</view>
				</view>
			</view>
		</view>
	</view>
</template>

<script>
import { useNeedStore } from '@/store/need'
import { useUserStore } from '@/store/user'
import BottomNav from '@/components/bottom-nav/bottom-nav.vue'
import IconFont from '@/components/icon-font/icon-font.vue'

export default {
	components: {
		BottomNav,
		IconFont
	},
	setup() {
		const needStore = useNeedStore()
		const userStore = useUserStore()
		return { needStore, userStore }
	},
	data() {
		return {
			currentStep: 1,
			categories: [
				{ name: '跑腿', icon: 'run' },
				{ name: '家务', icon: 'housework' },
				{ name: '专业', icon: 'professional' },
				{ name: '其他', icon: 'others' }
			],
			form: {
				title: '',
				description: '',
				reward: '',
				isUrgent: false,
				location: '',
				detailAddress: '',
				address: '',
				latitude: '',
				longitude: '',
				image: '',
				time: '',
				deadline: '',
				category: ''
			},
			timeRange: [[], []],
			timeValue: [0, 0],
			deadlineRange: [[], []],
			deadlineValue: [0, 0],
			activeField: '',
			isSubmitting: false,
			paymentMethod: 'wallet',
			confirmVisible: false,
			confirmTitle: '提示',
			confirmContent: '',
			confirmConfirmText: '确定',
			confirmCancelText: '取消',
			onConfirm: null
		}
	},
	computed: {
		walletBalance() {
			return this.userStore.currentUser?.walletBalance || 0
		}
	},
	onLoad() {
		this.initTimePicker()
		this.initDeadlinePicker()
		const republishData = uni.getStorageSync('republishData')
		if (republishData) {
			this.form = { ...this.form, ...republishData }
			this.currentStep = 1
			uni.removeStorageSync('republishData')
			uni.removeStorageSync('publishDraft')
		} else {
			const draft = uni.getStorageSync('publishDraft')
			if (draft) {
				this.form = { ...this.form, ...draft }
			}
		}
	},
	onShow() {
		uni.hideTabBar()
		const republishData = uni.getStorageSync('republishData')
		if (republishData) {
			this.form = { ...this.form, ...republishData }
			this.currentStep = 1
			uni.removeStorageSync('republishData')
			uni.removeStorageSync('publishDraft')
		}
	},
	watch: {
		form: {
			deep: true,
			handler(newVal) {
				uni.setStorageSync('publishDraft', newVal)
			}
		}
	},
	methods: {
		fillTestData() {
			this.form = {
				title: '帮忙取快递',
				description: '在门卫帮忙取一下快递，是一个箱子，不大',
				reward: '10',
				category: '跑腿',
				location: '阳光花园',
				detailAddress: '7栋302室',
				address: { name: '阳光花园', latitude: 39.908823, longitude: 116.397470 },
				latitude: 39.908823,
				longitude: 116.397470,
				time: '今天 14:00',
				deadline: '今天 18:00',
				image: ''
			}
			uni.showToast({ title: '已填充测试数据', icon: 'success' })
		},
		selectCategory(name) {
			this.form.category = name
		},
		initTimePicker() {
			const days = ['今天', '明天', '后天']
			for (let i = 3; i <= 30; i++) {
				const date = new Date()
				date.setDate(date.getDate() + i)
				const month = date.getMonth() + 1
				const day = date.getDate()
				days.push(`${month}月${day}日`)
			}
			const hours = Array.from({ length: 24 }, (_, i) => `${i < 10 ? '0' + i : i}:00`)
			this.timeRange = [days, hours]
		},
		onTimeChange(e) {
			const [dayIdx, hourIdx] = e.detail.value
			const day = this.timeRange[0][dayIdx]
			const hour = this.timeRange[1][hourIdx]
			this.form.time = `${day} ${hour}`
			this.timeValue = [dayIdx, hourIdx]
		},
		onTimeColumnChange(e) {
			if (e.detail.column === 0) {
				this.timeValue[0] = e.detail.value
			} else {
				this.timeValue[1] = e.detail.value
			}
		},
		initDeadlinePicker() {
			const days = ['今天', '明天', '后天']
			for (let i = 3; i <= 30; i++) {
				const date = new Date()
				date.setDate(date.getDate() + i)
				const month = date.getMonth() + 1
				const day = date.getDate()
				days.push(`${month}月${day}日`)
			}
			const hours = Array.from({ length: 24 }, (_, i) => `${i < 10 ? '0' + i : i}:00`)
			this.deadlineRange = [days, hours]
		},
		onDeadlineChange(e) {
			const [dayIdx, hourIdx] = e.detail.value
			const day = this.deadlineRange[0][dayIdx]
			const hour = this.deadlineRange[1][hourIdx]
			this.form.deadline = `${day} ${hour}`
			this.deadlineValue = [dayIdx, hourIdx]
		},
		onDeadlineColumnChange(e) {
			if (e.detail.column === 0) {
				this.deadlineValue[0] = e.detail.value
			} else {
				this.deadlineValue[1] = e.detail.value
			}
		},
		nextStep() {
			// Step 1 validation
			if (this.currentStep === 1) {
				if (!this.form.category) {
					uni.showToast({ title: '请先选择分类', icon: 'none' })
					return
				}
				if (!this.form.title.trim()) {
					uni.showToast({ title: '请先输入需求标题', icon: 'none' })
					return
				}
				this.currentStep++
			}
			// Step 2 validation
			else if (this.currentStep === 2) {
				if (!this.form.location.trim()) {
					uni.showToast({ title: '请选择服务地点', icon: 'none' })
					return
				}
				if (!this.form.time) {
					uni.showToast({ title: '请选择服务时间', icon: 'none' })
					return
				}
				this.currentStep++
			}
		},
		prevStep() {
			if (this.currentStep > 1) {
				this.currentStep--
			}
		},
		openMapPicker() {
			this.activeField = 'location'
			uni.chooseLocation({
				success: (res) => {
					if (res.name) {
						this.form.location = res.name
						this.form.address = res.address || res.name
						this.form.latitude = res.latitude
						this.form.longitude = res.longitude
						// 标记用户已经选择过位置，不再显示GPS提示
						uni.setStorageSync('gpsEnabled', true)
						uni.setStorageSync('hasDismissedGps', true)
					}
				},
				complete: () => {
					this.activeField = ''
				}
			})
		},
		handleBack() {
			if (this.currentStep > 1) {
				this.prevStep()
			} else {
				this.confirmTitle = '提示'
				this.confirmContent = '确定要放弃编辑吗？'
				this.confirmConfirmText = '确定'
				this.confirmCancelText = '取消'
				this.onConfirm = () => {
					this.resetForm()
					uni.navigateBack()
				}
				this.confirmVisible = true
			}
		},
		goHome() {
			this.resetForm()
			uni.switchTab({ url: '/pages/index/index' })
		},
		goOrders() {
			this.resetForm()
			const lastPublishedNeedId = uni.getStorageSync('lastPublishedNeedId')
			if (lastPublishedNeedId) {
				uni.navigateTo({
					url: `/pages/need-detail/need-detail?id=${lastPublishedNeedId}`
				})
				uni.removeStorageSync('lastPublishedNeedId')
			} else {
				uni.switchTab({ url: '/pages/orders/orders' })
			}
		},
		continuePublish() {
			this.resetForm()
			this.currentStep = 1
		},
		chooseImage() {
			uni.chooseImage({
				count: 1,
				success: (res) => {
					this.form.image = res.tempFilePaths[0]
				}
			})
		},
		deleteImage() {
			this.confirmTitle = '提示'
			this.confirmContent = '确定要删除这张照片吗？'
			this.confirmConfirmText = '确定'
			this.confirmCancelText = '取消'
			this.onConfirm = () => {
				this.form.image = ''
			}
			this.confirmVisible = true
		},
		validate() {
			if (!this.form.category) {
				uni.showToast({ title: '请先选择分类', icon: 'none' })
				return false
			}
			if (!this.form.title.trim()) {
				uni.showToast({ title: '请输入需求标题', icon: 'none' })
				return false
			}
			if (!this.form.location.trim()) {
				uni.showToast({ title: '请选择服务地点', icon: 'none' })
				return false
			}
			if (!this.form.time) {
				uni.showToast({ title: '请选择服务时间', icon: 'none' })
				return false
			}
			if (!this.form.reward || Number(this.form.reward) <= 0) {
				uni.showToast({ title: '请输入有效的报酬金额', icon: 'none' })
				return false
			}
			return true
		},
		selectPayment(method) {
			if (method === 'wallet' && this.walletBalance < this.form.reward) {
				uni.showToast({ title: '钱包余额不足，请选择其他支付方式', icon: 'none' })
				return
			}
			this.paymentMethod = method
		},
		resetForm() {
			this.form = {
				title: '',
				description: '',
				reward: '',
				isUrgent: false,
				location: '',
				detailAddress: '',
				address: '',
				latitude: '',
				longitude: '',
				image: '',
				time: '',
				deadline: '',
				category: ''
			}
			this.currentStep = 1
			this.activeField = ''
			this.paymentMethod = 'wallet'
			this.timeValue = [0, 0]
			this.deadlineValue = [0, 0]
		},
		async handleSubmit() {
			if (this.isSubmitting) return
			
			if (!this.validate()) return
			
			this.isSubmitting = true
			try {
				const rewardAmount = Number(this.form.reward) || 0
				
				if (this.paymentMethod === 'wallet') {
					if (this.walletBalance < rewardAmount) {
						uni.showToast({ title: '钱包余额不足', icon: 'none' })
						this.isSubmitting = false
						return
					}
					this.userStore.deductBalance(rewardAmount)
				} else {
					const payMethodName = this.paymentMethod === 'wechat' ? '微信' : '支付宝'
					const payConfirmed = await new Promise((resolve) => {
						uni.showModal({
							title: '确认支付',
							content: `需支付 ¥${rewardAmount}（${payMethodName}），确认后将从钱包扣除`,
							confirmColor: '#10B981',
							success: (res) => resolve(res.confirm)
						})
					})
					if (!payConfirmed) {
						this.isSubmitting = false
						return
					}
					if (this.walletBalance < rewardAmount) {
						uni.showToast({ title: '钱包余额不足，请先充值', icon: 'none' })
						this.isSubmitting = false
						return
					}
					this.userStore.deductBalance(rewardAmount)
				}
				const transactions = uni.getStorageSync('walletTransactions') || []
				transactions.unshift({
					id: Date.now(),
					type: 'expense',
					title: `发布需求：${this.form.title}`,
					amount: -rewardAmount,
					time: Date.now()
				})
				uni.setStorageSync('walletTransactions', transactions)
				
				const newNeed = await this.needStore.addNeed({
					title: this.form.title.trim(),
					description: this.form.description.trim(),
					reward: rewardAmount,
					isUrgent: this.form.isUrgent,
					location: this.form.location.trim() + (this.form.detailAddress ? ' ' + this.form.detailAddress.trim() : ''),
					address: this.form.address,
					detailAddress: this.form.detailAddress.trim(),
					latitude: this.form.latitude,
					longitude: this.form.longitude,
					image: this.form.image,
					time: this.form.time,
					deadline: this.form.deadline || ''
				})
				
				uni.removeStorageSync('publishDraft')
				uni.setStorageSync('lastPublishedNeedId', newNeed.id)
				this.currentStep = 4
			} catch (e) {
				uni.showToast({ title: '发布失败，请重试', icon: 'none' })
			} finally {
				this.isSubmitting = false
			}
		}
	}
}
</script>

<style scoped>
.container {
	min-height: 100vh;
	background: #FFFFFF;
	display: flex;
	flex-direction: column;
}

.content-container {
	flex: 1;
	padding-bottom: 120rpx;
}

/* Header */
.header {
	padding: 80rpx 32rpx 8rpx;
	display: flex;
	justify-content: space-between;
	align-items: flex-start;
	background: #FFFFFF;
}
.header-title { font-size: 36rpx; font-weight: 800; color: #1E293B; }
.header-right { width: 100rpx; }
.header-steps { display: flex; align-items: center; justify-content: center; gap: 24rpx; }
.hs-dot { width: 40rpx; height: 40rpx; border-radius: 20rpx; background: #F3F4F6; color: #9CA3AF; font-size: 20rpx; font-weight: 700; display: flex; align-items: center; justify-content: center; }
.hs-dot.active { background: #10B981; color: #fff; }
.hs-line { width: 72rpx; height: 4rpx; background: #F3F4F6; }
.hs-line.active { background: #10B981; }
.header-right .test-btn {
	font-size: 28rpx;
	color: #10B981;
	font-weight: 700;
}

/* Steps Bar */
.steps-bar {
	display: flex;
	justify-content: space-between;
	padding: 0;
	position: relative;
	min-height: 60rpx;
}
.step-line {
	position: absolute;
	top: 18rpx;
	left: 40rpx;
	right: 40rpx;
	height: 4rpx;
	background: #F3F4F6;
	z-index: 1;
}
.step-item {
	display: flex;
	flex-direction: column;
	align-items: center;
	z-index: 2;
	position: relative;
}
.step-dot {
	width: 32rpx;
	height: 32rpx;
	border-radius: 16rpx;
	background: #F3F4F6;
	color: #9CA3AF;
	display: flex;
	align-items: center;
	justify-content: center;
	font-size: 18rpx;
	font-weight: 700;
	margin-bottom: 4rpx;
	transition: all 0.3s;
}
.step-label {
	font-size: 18rpx;
	color: #9CA3AF;
	font-weight: 600;
}
.step-item.active .step-dot {
	background: #10B981;
	color: #FFFFFF;
	box-shadow: 0 8rpx 20rpx rgba(16, 185, 129, 0.2);
}
.step-item.active .step-label {
	color: #10B981;
}

/* Side Hint */
.side-hint {
	border-left: 10rpx solid #10B981;
	padding-left: 40rpx;
	margin: 40rpx 50rpx 80rpx;
}
.hint-label {
	font-size: 24rpx;
	color: #10B981;
	font-weight: 800;
	text-transform: uppercase;
	letter-spacing: 2rpx;
	margin-bottom: 10rpx;
}
.hint-title {
	font-size: 52rpx;
	font-weight: 800;
	color: #1F2937;
	letter-spacing: -1rpx;
}

/* Category Grid */
.category-grid {
	display: grid;
	grid-template-columns: repeat(4, 1fr);
	gap: 16rpx;
	margin-top: 12rpx;
}

.category-item {
	display: flex;
	flex-direction: column;
	align-items: center;
	justify-content: center;
	padding: 20rpx 0;
	background: #F9FAFB;
	border-radius: 16rpx;
	border: 2rpx solid transparent;
	transition: all 0.2s;
}

.category-item .cat-icon {
	font-size: 32rpx;
	margin-bottom: 8rpx;
}

.category-item .cat-name {
	font-size: 22rpx;
	font-weight: 600;
	color: #6B7280;
}

.category-item.active {
	background: #ECFDF5;
	border-color: #10B981;
}

.category-item.active .cat-name {
	color: #10B981;
}

/* Input Section */
.input-section {
	padding: 0 50rpx;
}
.input-card {
	background: #F9FAFB;
	border-radius: 40rpx;
	padding: 32rpx 40rpx;
	margin-bottom: 32rpx;
	border: 2rpx solid transparent;
	transition: all 0.2s;
}
.input-card.focused {
	background: #FFFFFF;
	border-color: #10B981;
	box-shadow: 0 20rpx 50rpx rgba(16, 185, 129, 0.05);
}
.card-label {
	font-size: 22rpx;
	color: #6B7280;
	font-weight: 700;
	margin-bottom: 12rpx;
	display: block;
}
.card-input {
	font-size: 34rpx;
	font-weight: 600;
	color: #1F2937;
	width: 100%;
}
.textarea-card {
	min-height: 240rpx;
}
.card-textarea {
	font-size: 34rpx;
	font-weight: 600;
	color: #1F2937;
	width: 100%;
	height: 160rpx;
}

/* Image Uploader */
.image-uploader {
	margin-top: 20rpx;
}
.upload-placeholder {
	height: 200rpx;
	border: 4rpx dashed #E5E7EB;
	border-radius: 40rpx;
	display: flex;
	flex-direction: column;
	align-items: center;
	justify-content: center;
	gap: 16rpx;
}
.camera-icon { font-size: 48rpx; }
.upload-text { font-size: 26rpx; color: #9CA3AF; font-weight: 600; }
.preview-box {
	position: relative;
	width: 100%;
	height: 300rpx;
	border-radius: 40rpx;
	overflow: hidden;
}
.preview-img { width: 100%; height: 100%; }
.delete-img {
	position: absolute;
	top: 20rpx;
	right: 20rpx;
	width: 48rpx;
	height: 48rpx;
	background: rgba(0,0,0,0.5);
	color: white;
	border-radius: 24rpx;
	display: flex;
	align-items: center;
	justify-content: center;
	font-size: 32rpx;
}

/* Location & Reward */
.location-display {
	display: flex;
	justify-content: space-between;
	align-items: center;
}
.loc-text {
	font-size: 32rpx;
	font-weight: 600;
	color: #1F2937;
}
.loc-text.placeholder { color: #9CA3AF; font-weight: 500; }
.map-marker { font-size: 36rpx; }

.reward-input-box {
	display: flex;
	align-items: center;
}
.currency {
	font-size: 40rpx;
	font-weight: 700;
	color: #10B981;
	margin-right: 20rpx;
}
.card-input.amount {
	font-size: 48rpx;
	font-weight: 800;
	color: #10B981;
}

/* Payment Options */
.payment-options {
	display: flex;
	flex-direction: column;
	gap: 24rpx;
	margin-top: 24rpx;
}

.payment-option {
	display: flex;
	align-items: center;
	justify-content: space-between;
	padding: 32rpx;
	background: #F9FAFB;
	border-radius: 28rpx;
	border: 4rpx solid transparent;
	transition: all 0.2s;
}

.payment-option.active {
	background: #ECFDF5;
	border-color: #10B981;
}

.payment-option.disabled {
	opacity: 0.5;
}

.payment-left {
	display: flex;
	align-items: center;
	gap: 24rpx;
}

.payment-icon {
	font-size: 48rpx;
}

.payment-info {
	display: flex;
	flex-direction: column;
}

.payment-name {
	font-size: 30rpx;
	font-weight: 600;
	color: #1F2937;
}

.payment-balance {
	font-size: 26rpx;
	color: #10B981;
	font-weight: 700;
}

.payment-fee {
	font-size: 24rpx;
	color: #9CA3AF;
}

.payment-check {
	width: 44rpx;
	height: 44rpx;
	border-radius: 50%;
	background: #E5E7EB;
	display: flex;
	align-items: center;
	justify-content: center;
}

.payment-option.active .payment-check {
	background: #10B981;
}

.check-icon {
	color: white;
	font-size: 24rpx;
	font-weight: bold;
}

.payment-tip {
	padding: 24rpx 32rpx;
	border-radius: 20rpx;
	font-size: 26rpx;
	margin-top: 24rpx;
}

.payment-tip.success {
	background: #ECFDF5;
	color: #10B981;
}

.payment-tip.warning {
	background: #FEF3C7;
	color: #D97706;
}

/* Order Summary Card */
.order-summary-card {
	background: #F9FAFB;
	border-radius: 40rpx;
	padding: 40rpx;
	margin-top: 40rpx;
}

.summary-label {
	font-size: 28rpx;
	font-weight: 700;
	color: #1E293B;
	margin-bottom: 32rpx;
	display: block;
}

.summary-row {
	display: flex;
	justify-content: space-between;
	align-items: center;
	padding: 20rpx 0;
	border-bottom: 2rpx solid #F1F5F9;
}

.summary-row:last-child {
	border-bottom: none;
}

.summary-row.total {
	margin-top: 20rpx;
	padding-top: 32rpx;
	border-top: 4rpx solid #E5E7EB;
	border-bottom: none;
}

.summary-key {
	font-size: 28rpx;
	color: #64748B;
	font-weight: 500;
}

.summary-value {
	font-size: 28rpx;
	color: #1E293B;
	font-weight: 600;
	max-width: 60%;
	text-align: right;
}

.summary-value.price {
	font-size: 40rpx;
	color: #10B981;
	font-weight: 800;
}

/* Footer Actions */
.action-footer {
	padding: 80rpx 50rpx;
	margin-top: auto;
}
.next-btn {
	height: 112rpx;
	background: #10B981;
	color: #FFFFFF;
	border-radius: 56rpx;
	font-weight: 800;
	font-size: 34rpx;
	display: flex;
	align-items: center;
	justify-content: center;
	border: none;
	outline: none;
	box-shadow: 0 20rpx 50rpx rgba(16, 185, 129, 0.25);
}
.next-btn::after {
	border: none;
}
.action-footer.dual {
	display: flex;
	gap: 30rpx;
	align-items: center;
}
.back-link {
	flex: 1;
	height: 112rpx;
	background: #F3F4F6;
	color: #4B5563;
	border-radius: 56rpx;
	font-weight: 700;
	font-size: 32rpx;
	border: 0;
	outline: none;
	box-shadow: none;
	display: flex;
	align-items: center;
	justify-content: center;
	line-height: 112rpx;
}
.back-link::after {
	border: 0;
}
.action-footer.dual .next-btn {
	flex: 2;
}

/* Animation */
.animate-in {
	animation: slideUp 0.4s cubic-bezier(0.16, 1, 0.3, 1);
}
@keyframes slideUp {
	from { opacity: 0; transform: translateY(40rpx); }
	to { opacity: 1; transform: translateY(0); }
}

.success-step {
	display: flex;
	flex-direction: column;
	align-items: center;
	justify-content: center;
	padding: 200rpx 80rpx;
	text-align: center;
}

.urgent-toggle {
	display: flex;
	align-items: center;
	justify-content: space-between;
	padding: 20rpx 24rpx;
}

.urgent-toggle .urgent-left {
	display: flex;
	align-items: center;
	gap: 16rpx;
}

.urgent-toggle .urgent-icon {
	color: #94A3B8;
}

.urgent-toggle.active .urgent-icon {
	color: #EA580C;
}

.urgent-toggle .urgent-info {
	display: flex;
	flex-direction: column;
}

.urgent-toggle .urgent-title {
	font-size: 28rpx;
	font-weight: 700;
	color: #1E293B;
}

.urgent-toggle .urgent-desc {
	font-size: 22rpx;
	color: #94A3B8;
	margin-top: 4rpx;
}

.urgent-toggle.active {
	background: #FFF7ED;
	border-color: #FB923C;
}

.toggle-switch {
	width: 88rpx;
	height: 48rpx;
	border-radius: 24rpx;
	background: #E5E7EB;
	position: relative;
	transition: all 0.3s;
}

.toggle-switch.on {
	background: #10B981;
}

.toggle-knob {
	width: 40rpx;
	height: 40rpx;
	border-radius: 50%;
	background: #FFFFFF;
	position: absolute;
	top: 4rpx;
	left: 4rpx;
	transition: all 0.3s;
	box-shadow: 0 2rpx 4rpx rgba(0,0,0,0.1);
}

.toggle-switch.on .toggle-knob {
	left: 44rpx;
}
.success-icon {
	font-size: 160rpx;
	margin-bottom: 40rpx;
}
.success-title {
	font-size: 40rpx;
	font-weight: 800;
	color: #1E293B;
	margin-bottom: 16rpx;
}
.success-desc {
	font-size: 28rpx;
	color: #64748B;
	margin-bottom: 60rpx;
}
.success-actions {
	width: 100%;
	display: flex;
	flex-direction: column;
	gap: 20rpx;
}
.success-actions .action-btn {
	height: 88rpx;
	border-radius: 44rpx;
	font-size: 30rpx;
	font-weight: 700;
	display: flex;
	align-items: center;
	justify-content: center;
	border: none;
	outline: none;
}
.success-actions .action-btn::after {
	border: none;
}
.success-actions .action-btn.primary {
	background: #10B981;
	color: #FFFFFF;
}
.success-actions .action-btn.secondary {
	background: #F1F5F9;
	color: #1E293B;
}
.success-actions .action-btn.ghost {
	background: transparent;
	color: #64748B;
	font-size: 26rpx;
	font-weight: 500;
	outline: none;
}
.success-actions .action-btn.ghost::after {
	border: none;
}
</style>

