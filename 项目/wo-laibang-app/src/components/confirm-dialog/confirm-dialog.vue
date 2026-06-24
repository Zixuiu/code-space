<template>
	<view v-if="visible" class="confirm-overlay" @click="handleOverlayClick">
		<view class="confirm-modal" @click.stop>
			<view class="confirm-header" v-if="title">
				<text class="confirm-title">{{ title }}</text>
			</view>
			<view class="confirm-content" v-if="content">
				<text class="confirm-content-text">{{ content }}</text>
			</view>
			<view class="confirm-footer" :class="{ single: !showCancel }">
				<view v-if="showCancel" class="confirm-btn cancel" @click="handleCancel">
					<text class="btn-text">{{ cancelText }}</text>
				</view>
				<view class="confirm-btn confirm" @click="handleConfirm">
					<text class="btn-text">{{ confirmText }}</text>
				</view>
			</view>
		</view>
	</view>
</template>

<script>
export default {
	name: 'ConfirmDialog',
	props: {
		visible: {
			type: Boolean,
			default: false
		},
		title: {
			type: String,
			default: '提示'
		},
		content: {
			type: String,
			default: ''
		},
		confirmText: {
			type: String,
			default: '确定'
		},
		cancelText: {
			type: String,
			default: '取消'
		},
		showCancel: {
			type: Boolean,
			default: true
		},
		closeOnClickOverlay: {
			type: Boolean,
			default: true
		}
	},
	methods: {
		handleOverlayClick() {
			if (this.closeOnClickOverlay) {
				this.handleCancel()
			}
		},
		handleCancel() {
			this.$emit('update:visible', false)
			this.$emit('cancel')
		},
		handleConfirm() {
			this.$emit('update:visible', false)
			this.$emit('confirm')
		}
	}
}
</script>

<style lang="scss" scoped>
.confirm-overlay {
	position: fixed;
	top: 0;
	left: 0;
	right: 0;
	bottom: 0;
	background: rgba(0, 0, 0, 0.5);
	z-index: 9999;
	display: flex;
	align-items: center;
	justify-content: center;
}

.confirm-modal {
	width: 560rpx;
	background: #FFFFFF;
	border-radius: 32rpx;
	overflow: hidden;
	box-shadow: 0 20rpx 60rpx rgba(0, 0, 0, 0.15);
}

.confirm-header {
	padding: 40rpx 40rpx 20rpx;
	text-align: center;
}

.confirm-title {
	font-size: 34rpx;
	font-weight: 700;
	color: #1E293B;
}

.confirm-content {
	padding: 0 40rpx 30rpx;
	text-align: center;
}

.confirm-content-text {
	font-size: 28rpx;
	color: #64748B;
	line-height: 1.6;
}

.confirm-footer {
	display: flex;
	border-top: 1rpx solid #F1F5F9;

	&.single {
		.confirm-btn.confirm {
			border-left: none;
		}
	}
}

.confirm-btn {
	flex: 1;
	height: 96rpx;
	display: flex;
	align-items: center;
	justify-content: center;

	&.cancel {
		.btn-text {
			font-weight: 600;
			color: #64748B;
		}
	}

	&.confirm {
		border-left: 1rpx solid #F1F5F9;

		.btn-text {
			font-weight: 700;
			color: #10B981;
		}
	}
}

.btn-text {
	font-size: 30rpx;
}
</style>
