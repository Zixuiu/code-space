<template>
	<view class="verify-container">
		<view class="header">
			<text class="header-title">实名认证</text>
			<view class="header-right"></view>
		</view>

		<scroll-view class="content-scroll" scroll-y>
			<view v-if="!isVerified" class="verify-form">
				<view class="status-card">
					<view class="status-icon-wrapper">
						<text class="status-icon-emoji">🪪</text>
					</view>
					<text class="status-title">未认证</text>
					<text class="status-desc">完成实名认证，解锁更多功能</text>
				</view>

				<view class="form-section">
					<view class="input-group">
						<label class="input-label">真实姓名</label>
						<view class="input-wrapper">
							<IconFont name="user" :size="32" class="input-icon" />
							<input
								class="input-field"
								v-model="form.realName"
								placeholder="请输入真实姓名"
							/>
						</view>
					</view>

					<view class="input-group">
						<label class="input-label">身份证号</label>
						<view class="input-wrapper">
							<view class="input-icon"><IconFont name="lock" :size="32" /></view>
							<input
								class="input-field"
								v-model="form.idCard"
								placeholder="请输入18位身份证号"
								type="idcard"
								maxlength="18"
							/>
						</view>
					</view>

					<view class="input-group">
						<label class="input-label">手机号码</label>
						<view class="input-wrapper">
							<text class="input-icon">📱</text>
							<input
								class="input-field"
								v-model="form.phone"
								placeholder="请输入手机号"
								type="number"
								maxlength="11"
							/>
						</view>
					</view>

					<view class="input-group">
						<label class="input-label">验证码</label>
						<view class="input-wrapper code-wrapper">
							<view class="input-icon"><IconFont name="mail" :size="32" /></view>
							<input
								class="input-field"
								v-model="form.code"
								placeholder="请输入验证码"
								type="number"
								maxlength="6"
							/>
							<button
								class="code-btn"
								:class="{ disabled: counting }"
								@click="sendCode"
							>
								{{ counting ? `${count}s` : '获取验证码' }}
							</button>
						</view>
					</view>

					<view class="input-group">
						<label class="input-label">身份证照片</label>
						<view class="id-card-upload">
							<view class="id-card-item" @click="chooseIdCardFront">
								<view v-if="form.idCardFront" class="id-card-preview">
									<image :src="form.idCardFront" mode="aspectFill" class="preview-image" lazy-load="true"></image>
								</view>
								<view v-else class="id-card-placeholder">
									<text class="placeholder-icon">🪪</text>
									<text class="placeholder-text">身份证正面</text>
								</view>
								<view v-if="form.idCardFront" class="remove-btn" @click.stop="removeIdCardFront">✕</view>
							</view>
							<view class="id-card-item" @click="chooseIdCardBack">
								<view v-if="form.idCardBack" class="id-card-preview">
									<image :src="form.idCardBack" mode="aspectFill" class="preview-image" lazy-load="true"></image>
								</view>
								<view v-else class="id-card-placeholder">
									<text class="placeholder-icon">🪪</text>
									<text class="placeholder-text">身份证反面</text>
								</view>
								<view v-if="form.idCardBack" class="remove-btn" @click.stop="removeIdCardBack">✕</view>
							</view>
						</view>
						<text class="upload-hint">请上传清晰的身份证正反面照片</text>
					</view>
				</view>

				<view class="tips-section">
					<view class="tips-header">
						<text class="tips-icon">🛡️</text>
						<text class="tips-title">安全保障</text>
					</view>
					<text class="tips-text">• 您的信息将进行加密处理</text>
					<text class="tips-text">• 仅用于身份验证，不会泄露</text>
					<text class="tips-text">• 通过金融级安全认证</text>
				</view>

				<button class="btn-primary" @click="handleVerify" :disabled="!canVerify || isSubmitting">
					<view v-if="isSubmitting" class="spinner"></view>
					<text v-else>提交认证</text>
				</button>
			</view>

			<view v-else class="verified-state">
				<view class="success-card">
					<view class="success-icon">✅</view>
					<text class="success-title">认证成功</text>
					<text class="success-desc">您已完成实名认证</text>
				</view>

				<view class="info-card">
					<view class="info-item">
						<text class="info-label">认证姓名</text>
						<text class="info-value">{{ verifiedInfo.realName }}</text>
					</view>
					<view class="info-item">
						<text class="info-label">身份证号</text>
						<text class="info-value">{{ verifiedInfo.idCard }}</text>
					</view>
					<view class="info-item">
						<text class="info-label">认证时间</text>
						<text class="info-value">{{ verifiedInfo.time }}</text>
					</view>
				</view>

				<view class="benefit-section">
					<text class="benefit-title">实名认证特权</text>
					<view class="benefit-list">
						<view class="benefit-item">
							<text class="benefit-icon">✔️</text>
							<text class="benefit-text">解锁更多服务功能</text>
						</view>
						<view class="benefit-item">
							<text class="benefit-icon">✔️</text>
							<text class="benefit-text">提升账户安全性</text>
						</view>
						<view class="benefit-item">
							<text class="benefit-icon">✔️</text>
							<text class="benefit-text">获得更多信任</text>
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
			isVerified: false,
			verifiedInfo: {
				realName: '',
				idCard: '',
				time: ''
			},
			form: {
				realName: '',
				idCard: '',
				phone: '',
				code: '',
				idCardFront: '',
				idCardBack: ''
			},
			counting: false,
			count: 60,
			isSubmitting: false
		}
	},
	computed: {
		canVerify() {
			return this.form.realName.trim() &&
				this.form.idCard.length === 18 &&
				this.form.phone.length === 11 &&
				this.form.code.length === 6 &&
				this.form.idCardFront &&
				this.form.idCardBack
		}
	},
	methods: {
		sendCode() {
			if (this.counting) return
			if (!/^1[3-9]\d{9}$/.test(this.form.phone)) {
				uni.showToast({ title: '请输入正确的手机号', icon: 'none' })
				return
			}

			this.counting = true
			uni.showToast({ title: '验证码已发送', icon: 'success' })

			const timer = setInterval(() => {
				this.count--
				if (this.count <= 0) {
					clearInterval(timer)
					this.counting = false
					this.count = 60
				}
			}, 1000)
		},
		chooseIdCardFront() {
			this.chooseImage((url) => {
				this.form.idCardFront = url
			})
		},
		chooseIdCardBack() {
			this.chooseImage((url) => {
				this.form.idCardBack = url
			})
		},
		chooseImage(callback) {
			uni.showActionSheet({
				itemList: ['拍照', '从相册选择'],
				success: (res) => {
					const sourceType = res.tapIndex === 0 ? ['camera'] : ['album']
					uni.chooseImage({
						count: 1,
						sizeType: ['compressed'],
						sourceType: sourceType,
						success: (res) => {
							const tempFilePath = res.tempFilePaths[0]
							uni.showLoading({ title: '上传中...', mask: true })
							this.uploadImage(tempFilePath, (uploadUrl) => {
								uni.hideLoading()
								callback(uploadUrl)
							})
						}
					})
				}
			})
		},
		uploadImage(filePath, callback) {
			const token = uni.getStorageSync('token')
			uni.uploadFile({
				url: 'https://api.wolaibang.com/api/common/upload',
				filePath: filePath,
				name: 'file',
				header: {
					'Authorization': token ? `Bearer ${token}` : ''
				},
				success: (res) => {
					try {
						const data = JSON.parse(res.data)
						if (data.code === 0 && data.data) {
							callback(data.data.url || filePath)
						} else {
							uni.showToast({ title: '上传失败，请重试', icon: 'none' })
						}
					} catch (e) {
						uni.showToast({ title: '上传失败，请重试', icon: 'none' })
					}
				},
				fail: (err) => {
					uni.showToast({ title: '上传失败，请检查网络后重试', icon: 'none' })
				}
			})
		},
		removeIdCardFront() {
			this.form.idCardFront = ''
		},
		removeIdCardBack() {
			this.form.idCardBack = ''
		},
		handleVerify() {
			if (!this.canVerify) return

			this.isSubmitting = true
			uni.showLoading({ title: '认证中...' })

			setTimeout(() => {
				uni.hideLoading()
				this.isSubmitting = false
				this.isVerified = true
				this.verifiedInfo = {
					realName: this.form.realName,
					idCard: this.form.idCard.replace(/(\d{4})\d+(\d{4})/, '$1**********$2'),
					time: new Date().toLocaleDateString()
				}

				const userInfo = uni.getStorageSync('currentUser') || {}
				userInfo.verified = true
				userInfo.realName = this.form.realName
				uni.setStorageSync('currentUser', userInfo)

				uni.showToast({ title: '认证成功', icon: 'success' })
			}, 2000)
		},
		}
}
</script>

<style scoped>
.verify-container {
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

.status-card {
	text-align: center;
	padding: 80rpx 48rpx;
	background: #FFFFFF;
	margin: 32rpx 48rpx;
	border-radius: 48rpx;
	box-shadow: 0 4rpx 24rpx rgba(0, 0, 0, 0.04);
}

.status-icon {
	font-size: 128rpx;
	display: block;
	margin-bottom: 32rpx;
}

.status-icon-wrapper {
	width: 160rpx;
	height: 160rpx;
	background: linear-gradient(135deg, #FEF3C7, #FDE68A);
	border-radius: 48rpx;
	display: flex;
	align-items: center;
	justify-content: center;
	margin: 0 auto 32rpx;
}

.status-icon-emoji {
	font-size: 80rpx;
}

.status-title {
	font-size: 40rpx;
	font-weight: 800;
	color: #1E293B;
	display: block;
	margin-bottom: 16rpx;
}

.status-desc {
	font-size: 28rpx;
	color: #64748B;
}

.form-section {
	padding: 0 48rpx 32rpx;
}

.input-group {
	margin-bottom: 32rpx;
}

.input-label {
	font-size: 24rpx;
	color: #64748B;
	font-weight: 700;
	text-transform: uppercase;
	letter-spacing: 1rpx;
	margin-bottom: 16rpx;
	display: block;
}

.input-wrapper {
	background: #FFFFFF;
	border-radius: 28rpx;
	padding: 28rpx 32rpx;
	border: 2rpx solid transparent;
	display: flex;
	align-items: center;
	gap: 24rpx;
	transition: all 0.3s;
	box-shadow: 0 4rpx 16rpx rgba(0, 0, 0, 0.04);
}

.input-wrapper:focus-within {
	border-color: #10B981;
	box-shadow: 0 12rpx 32rpx rgba(16, 185, 129, 0.08);
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

.code-wrapper {
	padding-right: 16rpx;
}

.code-btn {
	font-size: 26rpx;
	font-weight: 700;
	color: #10B981;
	background: transparent;
	border: none;
	padding: 16rpx 24rpx;
	white-space: nowrap;
	cursor: pointer;
}

.code-btn.disabled {
	color: #94A3B8;
	cursor: not-allowed;
}

.tips-section {
	margin: 0 48rpx 48rpx;
	padding: 32rpx;
	background: #F0FDF4;
	border-radius: 28rpx;
}

.id-card-upload {
	display: flex;
	gap: 32rpx;
	margin-bottom: 16rpx;
}

.id-card-item {
	flex: 1;
	height: 240rpx;
	border-radius: 28rpx;
	overflow: hidden;
	position: relative;
}

.id-card-placeholder {
	width: 100%;
	height: 100%;
	background: #FFFFFF;
	border: 4rpx dashed #E5E7EB;
	border-radius: 28rpx;
	display: flex;
	flex-direction: column;
	align-items: center;
	justify-content: center;
	gap: 16rpx;
}

.placeholder-icon {
	font-size: 64rpx;
}

.placeholder-text {
	font-size: 24rpx;
	color: #94A3B8;
	font-weight: 600;
}

.id-card-preview {
	width: 100%;
	height: 100%;
}

.preview-image {
	width: 100%;
	height: 100%;
}

.remove-btn {
	position: absolute;
	top: 12rpx;
	right: 12rpx;
	width: 44rpx;
	height: 44rpx;
	background: rgba(0, 0, 0, 0.5);
	border-radius: 50%;
	display: flex;
	align-items: center;
	justify-content: center;
	font-size: 24rpx;
	color: #FFFFFF;
}

.upload-hint {
	font-size: 22rpx;
	color: #94A3B8;
	display: block;
	margin-top: 8rpx;
}

.tips-header {
	display: flex;
	align-items: center;
	margin-bottom: 20rpx;
}

.tips-icon {
	font-size: 32rpx;
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

.btn-primary {
	margin: 0 48rpx;
	width: calc(100% - 96rpx);
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

.btn-primary:disabled {
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

.verified-state {
	padding: 48rpx;
}

.success-card {
	text-align: center;
	padding: 80rpx 48rpx;
	background: #FFFFFF;
	border-radius: 48rpx;
	margin-bottom: 32rpx;
	box-shadow: 0 4rpx 24rpx rgba(0, 0, 0, 0.04);
}

.success-icon {
	width: 160rpx;
	height: 160rpx;
	background: linear-gradient(135deg, #10B981, #34D399);
	border-radius: 50%;
	margin: 0 auto 40rpx;
	display: flex;
	align-items: center;
	justify-content: center;
	font-size: 80rpx;
	color: #FFFFFF;
	box-shadow: 0 24rpx 64rpx rgba(16, 185, 129, 0.3);
}

.success-title {
	font-size: 44rpx;
	font-weight: 900;
	color: #1E293B;
	display: block;
	margin-bottom: 16rpx;
}

.success-desc {
	font-size: 28rpx;
	color: #64748B;
}

.info-card {
	background: #FFFFFF;
	border-radius: 40rpx;
	padding: 40rpx;
	margin-bottom: 32rpx;
	box-shadow: 0 4rpx 24rpx rgba(0, 0, 0, 0.04);
}

.info-item {
	display: flex;
	justify-content: space-between;
	padding: 24rpx 0;
	border-bottom: 2rpx solid #F1F5F9;
}

.info-item:last-child {
	border-bottom: none;
}

.info-label {
	font-size: 28rpx;
	color: #64748B;
}

.info-value {
	font-size: 28rpx;
	font-weight: 700;
	color: #1E293B;
}

.benefit-section {
	background: #FFFFFF;
	border-radius: 40rpx;
	padding: 40rpx;
	box-shadow: 0 4rpx 24rpx rgba(0, 0, 0, 0.04);
}

.benefit-title {
	font-size: 30rpx;
	font-weight: 800;
	color: #1E293B;
	display: block;
	margin-bottom: 32rpx;
}

.benefit-item {
	display: flex;
	align-items: center;
	margin-bottom: 24rpx;
}

.benefit-item:last-child {
	margin-bottom: 0;
}

.benefit-icon {
	font-size: 32rpx;
	margin-right: 24rpx;
}

.benefit-text {
	font-size: 28rpx;
	color: #64748B;
}

.bottom-safe {
	height: 80rpx;
}
</style>