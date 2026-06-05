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
							<text class="input-icon"><IconFont name="lock" :size="32" /></text>
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
							<text class="input-icon"><IconFont name="mail" :size="32" /></text>
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
									<image :src="form.idCardFront" mode="aspectFill" class="preview-image"></image>
								</view>
								<view v-else class="id-card-placeholder">
									<text class="placeholder-icon">🪪</text>
									<text class="placeholder-text">身份证正面</text>
								</view>
								<view v-if="form.idCardFront" class="remove-btn" @click.stop="removeIdCardFront">✕</view>
							</view>
							<view class="id-card-item" @click="chooseIdCardBack">
								<view v-if="form.idCardBack" class="id-card-preview">
									<image :src="form.idCardBack" mode="aspectFill" class="preview-image"></image>
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

.status-card {
	text-align: center;
	padding: 40px 24px;
	background: #FFFFFF;
	margin: 16px 24px;
	border-radius: 24px;
	box-shadow: 0 2px 12px rgba(0, 0, 0, 0.04);
}

.status-icon {
	font-size: 64px;
	display: block;
	margin-bottom: 16px;
}

.status-icon-wrapper {
	width: 80px;
	height: 80px;
	background: linear-gradient(135deg, #FEF3C7, #FDE68A);
	border-radius: 24px;
	display: flex;
	align-items: center;
	justify-content: center;
	margin: 0 auto 16px;
}

.status-icon-emoji {
	font-size: 40px;
}

.status-title {
	font-size: 20px;
	font-weight: 800;
	color: #1E293B;
	display: block;
	margin-bottom: 8px;
}

.status-desc {
	font-size: 14px;
	color: #64748B;
}

.form-section {
	padding: 0 24px 16px;
}

.input-group {
	margin-bottom: 16px;
}

.input-label {
	font-size: 12px;
	color: #64748B;
	font-weight: 700;
	text-transform: uppercase;
	letter-spacing: 0.5px;
	margin-bottom: 8px;
	display: block;
}

.input-wrapper {
	background: #FFFFFF;
	border-radius: 14px;
	padding: 14px 16px;
	border: 1px solid transparent;
	display: flex;
	align-items: center;
	gap: 12px;
	transition: all 0.3s;
	box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
}

.input-wrapper:focus-within {
	border-color: #10B981;
	box-shadow: 0 6px 16px rgba(16, 185, 129, 0.08);
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

.code-wrapper {
	padding-right: 8px;
}

.code-btn {
	font-size: 13px;
	font-weight: 700;
	color: #10B981;
	background: transparent;
	border: none;
	padding: 8px 12px;
	white-space: nowrap;
	cursor: pointer;
}

.code-btn.disabled {
	color: #94A3B8;
	cursor: not-allowed;
}

.tips-section {
	margin: 0 24px 24px;
	padding: 16px;
	background: #F0FDF4;
	border-radius: 14px;
}

.id-card-upload {
	display: flex;
	gap: 16px;
	margin-bottom: 8px;
}

.id-card-item {
	flex: 1;
	height: 120px;
	border-radius: 14px;
	overflow: hidden;
	position: relative;
}

.id-card-placeholder {
	width: 100%;
	height: 100%;
	background: #FFFFFF;
	border: 2px dashed #E5E7EB;
	border-radius: 14px;
	display: flex;
	flex-direction: column;
	align-items: center;
	justify-content: center;
	gap: 8px;
}

.placeholder-icon {
	font-size: 32px;
}

.placeholder-text {
	font-size: 12px;
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
	top: 6px;
	right: 6px;
	width: 22px;
	height: 22px;
	background: rgba(0, 0, 0, 0.5);
	border-radius: 50%;
	display: flex;
	align-items: center;
	justify-content: center;
	font-size: 12px;
	color: #FFFFFF;
}

.upload-hint {
	font-size: 11px;
	color: #94A3B8;
	display: block;
	margin-top: 4px;
}

.tips-header {
	display: flex;
	align-items: center;
	margin-bottom: 10px;
}

.tips-icon {
	font-size: 16px;
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

.btn-primary {
	margin: 0 24px;
	width: calc(100% - 48px);
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

.btn-primary:disabled {
	opacity: 0.5;
	box-shadow: none;
}

.spinner {
	width: 20px;
	height: 20px;
	border: 2px solid rgba(255, 255, 255, 0.3);
	border-top-color: #FFFFFF;
	border-radius: 50%;
	animation: spin 0.8s linear infinite;
}

@keyframes spin {
	to { transform: rotate(360deg); }
}

.verified-state {
	padding: 24px;
}

.success-card {
	text-align: center;
	padding: 40px 24px;
	background: #FFFFFF;
	border-radius: 24px;
	margin-bottom: 16px;
	box-shadow: 0 2px 12px rgba(0, 0, 0, 0.04);
}

.success-icon {
	width: 80px;
	height: 80px;
	background: linear-gradient(135deg, #10B981, #34D399);
	border-radius: 50%;
	margin: 0 auto 20px;
	display: flex;
	align-items: center;
	justify-content: center;
	font-size: 40px;
	color: #FFFFFF;
	box-shadow: 0 12px 32px rgba(16, 185, 129, 0.3);
}

.success-title {
	font-size: 22px;
	font-weight: 900;
	color: #1E293B;
	display: block;
	margin-bottom: 8px;
}

.success-desc {
	font-size: 14px;
	color: #64748B;
}

.info-card {
	background: #FFFFFF;
	border-radius: 20px;
	padding: 20px;
	margin-bottom: 16px;
	box-shadow: 0 2px 12px rgba(0, 0, 0, 0.04);
}

.info-item {
	display: flex;
	justify-content: space-between;
	padding: 12px 0;
	border-bottom: 1px solid #F1F5F9;
}

.info-item:last-child {
	border-bottom: none;
}

.info-label {
	font-size: 14px;
	color: #64748B;
}

.info-value {
	font-size: 14px;
	font-weight: 700;
	color: #1E293B;
}

.benefit-section {
	background: #FFFFFF;
	border-radius: 20px;
	padding: 20px;
	box-shadow: 0 2px 12px rgba(0, 0, 0, 0.04);
}

.benefit-title {
	font-size: 15px;
	font-weight: 800;
	color: #1E293B;
	display: block;
	margin-bottom: 16px;
}

.benefit-item {
	display: flex;
	align-items: center;
	margin-bottom: 12px;
}

.benefit-item:last-child {
	margin-bottom: 0;
}

.benefit-icon {
	font-size: 16px;
	margin-right: 12px;
}

.benefit-text {
	font-size: 14px;
	color: #64748B;
}

.bottom-safe {
	height: 40px;
}
</style>