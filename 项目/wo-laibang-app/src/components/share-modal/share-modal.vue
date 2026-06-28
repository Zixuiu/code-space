<template>
	<view class="share-modal" v-if="visible" @click="close">
		<view class="share-sheet" @click.stop>
			<view class="sheet-header">
				<text class="share-title">↑ 分享赚佣金</text>
				<view class="close-btn" @click="close">✕</view>
			</view>

			<view class="share-content">
				<view class="need-info">
					<text class="need-title">{{ needTitle }}</text>
					<view class="need-reward">
						<text class="reward-label">赏金</text>
						<text class="reward-amount">¥{{ reward }}</text>
					</view>
				</view>

				<view class="commission-tip">
					<text class="tip-icon">✨</text>
					<text class="tip-text">分享给好友，好友完成帮忙后你可获得 5% 佣金</text>
				</view>

				<view class="commission-amount">
					<text class="commission-label">预估佣金</text>
					<text class="commission-value">¥{{ commission }}</text>
				</view>
			</view>

			<view class="share-actions">
				<view class="share-btn wechat" @click="shareTo('wechat')">
					<view class="btn-icon">💚</view>
					<text class="btn-text">微信好友</text>
				</view>
				<view class="share-btn moments" @click="shareTo('moments')">
					<view class="btn-icon">🌐</view>
					<text class="btn-text">朋友圈</text>
				</view>
				<view class="share-btn copy" @click="shareTo('copy')">
					<view class="btn-icon">🔗</view>
					<text class="btn-text">复制链接</text>
				</view>
			</view>

			<view class="cancel-btn" @click="close">
				<text>取消</text>
			</view>
		</view>
	</view>
</template>

<script>
export default {
	name: 'share-modal',
	props: {
		visible: {
			type: Boolean,
			default: false
		},
		needId: {
			type: String,
			default: ''
		},
		needTitle: {
			type: String,
			default: ''
		},
		reward: {
			type: [Number, String],
			default: 0
		}
	},
	computed: {
		commission() {
			const r = typeof this.reward === 'number' ? this.reward : parseFloat(this.reward) || 0
			return (r * 0.05).toFixed(2)
		}
	},
	methods: {
		close() {
			this.$emit('update:visible', false)
			this.$emit('close')
		},
		shareTo(type) {
			const shareUrl = `https://wolaibang.com/download?need=${this.needId}`
			const shareText = `【我来帮】帮你${this.needTitle}，赏金${this.reward}元！点击链接查看：${shareUrl}`

			switch (type) {
				case 'wechat':
					this.shareToWechat(shareText, shareUrl)
					break
				case 'moments':
					this.shareToMoments(shareText, shareUrl)
					break
				case 'copy':
					this.copyLink(shareText)
					break
			}
		},
		shareToWechat(text, url) {
			uni.share({
				provider: 'weixin',
				scene: 'WXSceneSession',
				type: 0,
				href: url,
				title: '我来帮 - 邻里互助',
				summary: text,
				success: () => {
					this.$emit('success', 'wechat')
					this.close()
				},
				fail: () => {
					this.copyLink(text)
				}
			})
		},
		shareToMoments(text, url) {
			uni.share({
				provider: 'weixin',
				scene: 'WXSenceTimeline',
				type: 0,
				href: url,
				title: '我来帮 - 邻里互助',
				summary: text,
				success: () => {
					this.$emit('success', 'moments')
					this.close()
				},
				fail: () => {
					this.copyLink(text)
				}
			})
		},
		copyLink(text) {
			uni.setClipboardData({
				data: text,
				success: () => {
					uni.showToast({
						title: '链接已复制，去分享给好友吧！',
						icon: 'success'
					})
					this.$emit('success', 'copy')
					this.close()
				}
			})
		}
	}
}
</script>

<style scoped>
.share-modal {
	position: fixed;
	inset: 0;
	background: rgba(0, 0, 0, 0.5);
	z-index: 9999;
	display: flex;
	align-items: flex-end;
	justify-content: center;
	backdrop-filter: blur(8rpx);
}

.share-sheet {
	width: 100%;
	background: #FFFFFF;
	border-radius: 40rpx 40rpx 0 0;
	padding: 32rpx 40rpx 60rpx;
	animation: slideUp 0.3s ease-out;
}

@keyframes slideUp {
	from {
		transform: translateY(100%);
	}
	to {
		transform: translateY(0);
	}
}

.sheet-header {
	display: flex;
	justify-content: space-between;
	align-items: center;
	margin-bottom: 32rpx;
}

.share-title {
	font-size: 36rpx;
	font-weight: 800;
	color: #1E293B;
}

.close-btn {
	width: 52rpx;
	height: 52rpx;
	background: #F1F5F9;
	border-radius: 50%;
	display: flex;
	align-items: center;
	justify-content: center;
	font-size: 24rpx;
	color: #64748B;
}

.share-content {
	background: linear-gradient(135deg, #F0FDF4, #ECFDF5);
	border-radius: 24rpx;
	padding: 28rpx;
	margin-bottom: 32rpx;
}

.need-info {
	display: flex;
	justify-content: space-between;
	align-items: center;
	margin-bottom: 20rpx;
}

.need-title {
	font-size: 30rpx;
	font-weight: 700;
	color: #1E293B;
	flex: 1;
	margin-right: 16rpx;
}

.need-reward {
	display: flex;
	align-items: center;
	gap: 8rpx;
	background: #10B981;
	padding: 8rpx 16rpx;
	border-radius: 100rpx;
}

.reward-label {
	font-size: 22rpx;
	color: rgba(255, 255, 255, 0.8);
}

.reward-amount {
	font-size: 26rpx;
	font-weight: 800;
	color: #FFFFFF;
}

.commission-tip {
	display: flex;
	align-items: center;
	gap: 12rpx;
	padding: 16rpx 20rpx;
	background: rgba(255, 255, 255, 0.8);
	border-radius: 16rpx;
	margin-bottom: 16rpx;
}

.tip-icon {
	font-size: 28rpx;
}

.tip-text {
	font-size: 24rpx;
	color: #64748B;
	flex: 1;
}

.commission-amount {
	display: flex;
	justify-content: space-between;
	align-items: center;
	padding-top: 16rpx;
	border-top: 1rpx dashed #D1D5DB;
}

.commission-label {
	font-size: 26rpx;
	color: #64748B;
}

.commission-value {
	font-size: 40rpx;
	font-weight: 900;
	color: #10B981;
}

.share-actions {
	display: flex;
	justify-content: space-around;
	margin-bottom: 32rpx;
}

.share-btn {
	display: flex;
	flex-direction: column;
	align-items: center;
	gap: 12rpx;
}

.btn-icon {
	width: 100rpx;
	height: 100rpx;
	background: #FFFFFF;
	border-radius: 24rpx;
	display: flex;
	align-items: center;
	justify-content: center;
	font-size: 48rpx;
	box-shadow: 0 4rpx 20rpx rgba(0, 0, 0, 0.06);
}

.btn-text {
	font-size: 24rpx;
	color: #64748B;
	font-weight: 600;
}

.share-btn.wechat .btn-icon {
	background: #F0FDF4;
}

.share-btn.moments .btn-icon {
	background: #FEF3C7;
}

.share-btn.copy .btn-icon {
	background: #EFF6FF;
}

.cancel-btn {
	width: 100%;
	height: 96rpx;
	background: #F1F5F9;
	border-radius: 48rpx;
	display: flex;
	align-items: center;
	justify-content: center;
}

.cancel-btn text {
	font-size: 32rpx;
	font-weight: 700;
	color: #64748B;
}
</style>