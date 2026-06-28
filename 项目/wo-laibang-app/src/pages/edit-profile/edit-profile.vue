<template>
	<view class="edit-profile-container">
		<view class="header">
			<text class="header-title">编辑资料</text>
			<text class="save-btn" @click="saveProfile">保存</text>
		</view>

		<scroll-view class="content-scroll" scroll-y>
			<view class="avatar-section">
				<view class="avatar-wrapper" @click="changeAvatar">
					<view class="avatar">{{ avatarText }}</view>
					<view class="avatar-edit-icon">
						<IconFont name="camera" :size="24" />
					</view>
				</view>
				<text class="avatar-hint">点击更换头像</text>
			</view>

			<view class="form-section">
				<view class="form-card">
					<view class="form-item">
						<label class="form-label">昵称</label>
						<view class="form-input">
							<input
								v-model="form.nickname"
								placeholder="请输入昵称"
								maxlength="20"
							/>
						</view>
					</view>

					<view class="form-item">
						<label class="form-label">性别</label>
						<view class="gender-select">
							<view
								class="gender-item"
								:class="{ selected: form.gender === 'male' }"
								@click="form.gender = 'male'"
							>
								<text>♂</text>
								<text class="gender-text">男</text>
							</view>
							<view
								class="gender-item"
								:class="{ selected: form.gender === 'female' }"
								@click="form.gender = 'female'"
							>
								<text>♀</text>
								<text class="gender-text">女</text>
							</view>
							<view
								class="gender-item"
								:class="{ selected: form.gender === 'secret' }"
								@click="form.gender = 'secret'"
							>
								<text>🙈</text>
								<text class="gender-text">保密</text>
							</view>
						</view>
					</view>

					<view class="form-item">
						<label class="form-label">生日</label>
						<view class="form-input" @click="showDatePicker">
							<input
								v-model="form.birthday"
								placeholder="请选择生日"
								disabled
							/>
							<text class="arrow">›</text>
						</view>
					</view>

					<view class="form-item">
						<label class="form-label">地区</label>
						<view class="form-input" @click="openMapPicker">
							<input
								v-model="form.region"
								placeholder="请选择所在地区"
								disabled
							/>
							<text class="arrow">›</text>
						</view>
					</view>

					<view class="form-item">
						<label class="form-label">个性签名</label>
						<view class="form-textarea">
							<textarea
								v-model="form.bio"
								placeholder="介绍一下自己..."
								maxlength="200"
								rows="3"
							></textarea>
							<text class="char-count">{{ form.bio.length }}/200</text>
						</view>
					</view>
				</view>

				<view class="form-card">
					<view class="form-item">
						<label class="form-label">手机号</label>
						<view class="form-input">
							<input
								v-model="form.phone"
								placeholder="请输入手机号"
								type="number"
								maxlength="11"
								disabled
							/>
							<text class="tag">已绑定</text>
						</view>
					</view>
				</view>
			</view>

			<view class="bottom-safe"></view>
		</scroll-view>

		<MapPicker
			v-if="showMapPicker"
			@close="showMapPicker = false"
			@select="onLocationSelect"
		/>
	</view>
</template>

<script>
import MapPicker from '@/components/map-picker/map-picker.vue'
import IconFont from '@/components/icon-font/icon-font.vue'

export default {
	components: {
		MapPicker,
		IconFont
	},
	data() {
		return {
			form: {
				nickname: '',
				gender: 'secret',
				birthday: '',
				region: '',
				bio: '',
				phone: ''
			},
			selectedLocation: null,
			showMapPicker: false
		}
	},
	computed: {
		avatarText() {
			return this.form.nickname ? this.form.nickname.slice(0, 1).toUpperCase() : '👤'
		}
	},
	onShow() {
		const userInfo = uni.getStorageSync('currentUser') || {}
		this.form = {
			nickname: userInfo.nickname || '',
			gender: userInfo.gender || 'secret',
			birthday: userInfo.birthday || '',
			region: userInfo.region || '',
			bio: userInfo.bio || '',
			phone: userInfo.phone || ''
		}
		if (userInfo.location) {
			this.selectedLocation = userInfo.location
			this.form.region = userInfo.location.address || userInfo.location.region || ''
		}
	},
	methods: {
		changeAvatar() {
			uni.chooseImage({
				count: 1,
				sizeType: ['compressed'],
				sourceType: ['album', 'camera'],
				success: (res) => {
					const tempFilePath = res.tempFilePaths[0]
					uni.showLoading({ title: '上传中...' })
					uni.uploadFile({
						url: 'https://api.wolaibang.com/upload/avatar',
						filePath: tempFilePath,
						name: 'avatar',
						header: {
							'Authorization': 'Bearer ' + (uni.getStorageSync('token') || '')
						},
						success: (uploadRes) => {
							uni.hideLoading()
							const data = JSON.parse(uploadRes.data)
							if (data.code === 0) {
								this.form.avatar = data.data.url
								uni.showToast({ title: '头像上传成功', icon: 'success' })
							} else {
								uni.showToast({ title: '头像上传失败', icon: 'none' })
							}
						},
						fail: () => {
							uni.hideLoading()
							uni.showToast({ title: '上传失败，请重试', icon: 'none' })
						}
					})
				}
			})
		},
		showDatePicker() {
			const currentYear = new Date().getFullYear()
			uni.showDatePicker({
				currentDate: this.form.birthday || this.formatDateForPicker(new Date()),
				startDate: '1900-01-01',
				endDate: `${currentYear}-12-31`,
				success: (res) => {
					if (res.date) {
						this.form.birthday = res.date
					}
				}
			})
		},
		formatDateForPicker(date) {
			const year = date.getFullYear()
			const month = String(date.getMonth() + 1).padStart(2, '0')
			const day = String(date.getDate()).padStart(2, '0')
			return `${year}-${month}-${day}`
		},
		openMapPicker() {
			this.showMapPicker = true
		},
		onLocationSelect(location) {
			this.selectedLocation = location
			this.form.region = location.address || location.region || ''
			this.showMapPicker = false
		},
		saveProfile() {
			if (!this.form.nickname.trim()) {
				uni.showToast({ title: '请输入昵称', icon: 'none' })
				return
			}

			const userInfo = uni.getStorageSync('currentUser') || {}
			const updatedInfo = {
				...userInfo,
				...this.form,
				location: this.selectedLocation
			}
			uni.setStorageSync('currentUser', updatedInfo)

			uni.showToast({ title: '保存成功', icon: 'success' })

			setTimeout(() => {
				uni.navigateBack()
			}, 1000)
		},
		}
}
</script>

<style scoped>
.edit-profile-container {
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

.save-btn {
	font-size: 30rpx;
	font-weight: 700;
	color: #10B981;
	width: 88rpx;
	text-align: right;
}

.content-scroll {
	height: calc(100vh - 144rpx);
}

.avatar-section {
	text-align: center;
	padding: 64rpx 48rpx;
	background: #FFFFFF;
	margin-bottom: 32rpx;
}

.avatar-wrapper {
	position: relative;
	display: inline-block;
}

.avatar {
	width: 192rpx;
	height: 192rpx;
	background: linear-gradient(135deg, #10B981, #34D399);
	border-radius: 50%;
	display: flex;
	align-items: center;
	justify-content: center;
	font-size: 80rpx;
	color: #FFFFFF;
	font-weight: 800;
}

.avatar-edit-icon {
	position: absolute;
	bottom: 0;
	right: 0;
	width: 72rpx;
	height: 72rpx;
	background: #FFFFFF;
	border-radius: 50%;
	display: flex;
	align-items: center;
	justify-content: center;
	box-shadow: 0 4rpx 12rpx rgba(0, 0, 0, 0.15);
	color: #10B981;
}

.avatar-hint {
	font-size: 24rpx;
	color: #94A3B8;
	margin-top: 24rpx;
	display: block;
}

.form-section {
	padding: 0 48rpx;
}

.form-card {
	background: #FFFFFF;
	border-radius: 40rpx;
	padding: 16rpx 0;
	margin-bottom: 32rpx;
	box-shadow: 0 4rpx 24rpx rgba(0, 0, 0, 0.04);
}

.form-item {
	padding: 28rpx 40rpx;
	border-bottom: 2rpx solid #F1F5F9;
}

.form-item:last-child {
	border-bottom: none;
}

.form-label {
	font-size: 24rpx;
	color: #64748B;
	font-weight: 700;
	text-transform: uppercase;
	letter-spacing: 1rpx;
	display: block;
	margin-bottom: 16rpx;
}

.form-input {
	display: flex;
	align-items: center;
	justify-content: space-between;
}

.form-input input {
	flex: 1;
	font-size: 30rpx;
	font-weight: 600;
	color: #1E293B;
	border: none;
	outline: none;
	background: transparent;
}

.arrow {
	font-size: 36rpx;
	color: #94A3B8;
}

.tag {
	font-size: 22rpx;
	color: #10B981;
	background: #F0FDF4;
	padding: 8rpx 20rpx;
	border-radius: 20rpx;
	font-weight: 700;
}

.gender-select {
	display: flex;
	gap: 24rpx;
}

.gender-item {
	flex: 1;
	display: flex;
	flex-direction: column;
	align-items: center;
	padding: 24rpx;
	background: #F8FAFC;
	border-radius: 28rpx;
	border: 4rpx solid transparent;
	font-size: 48rpx;
}

.gender-item.selected {
	background: #F0FDF4;
	border-color: #10B981;
}

.gender-text {
	font-size: 24rpx;
	color: #64748B;
	margin-top: 8rpx;
	font-weight: 600;
}

.gender-item.selected .gender-text {
	color: #10B981;
}

.form-textarea textarea {
	width: 100%;
	font-size: 30rpx;
	font-weight: 600;
	color: #1E293B;
	border: none;
	outline: none;
	background: transparent;
	resize: none;
}

.char-count {
	font-size: 22rpx;
	color: #94A3B8;
	text-align: right;
	display: block;
	margin-top: 8rpx;
}

.bottom-safe {
	height: 80rpx;
}
</style>