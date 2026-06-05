<template>
	<view class="blacklist-container">
		<view class="header">
			<text class="header-title">黑名单</text>
			<view class="header-right"></view>
		</view>

		<scroll-view class="content-scroll" scroll-y>
			<view v-if="blacklist.length === 0" class="empty-state">
				<IconFont name="users" :size="96" class="empty-icon" />
				<text class="empty-title">暂无黑名单</text>
				<text class="empty-text">没有被拉黑的用户</text>
			</view>

			<view v-else class="blacklist-list">
				<view
					v-for="item in blacklist"
					:key="item.id"
					class="blacklist-item"
				>
					<view class="user-avatar">{{ item.nickname.slice(0, 1) }}</view>
					<view class="user-info">
						<text class="user-name">{{ item.nickname }}</text>
						<text class="user-phone">{{ item.phone }}</text>
					</view>
					<view class="action-btn" @click="removeFromBlacklist(item)">
						<text>移出</text>
					</view>
				</view>
			</view>

			<view class="tips-section">
				<view class="tips-header">
					<IconFont name="info-circle" :size="128" class="tips-icon" />
					<text class="tips-title">说明</text>
				</view>
				<text class="tips-text">• 被拉黑的用户无法查看您的信息</text>
				<text class="tips-text">• 被拉黑的用户无法向您发起订单</text>
				<text class="tips-text">• 您可以随时将用户移出黑名单</text>
			</view>

			<view class="bottom-safe"></view>
		</scroll-view>

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
import IconFont from '@/components/icon-font/icon-font.vue'

export default {
	components: {
		IconFont
	},
	data() {
		return {
			blacklist: [
				{ id: 1, nickname: '张三', phone: '138****1234' },
				{ id: 2, nickname: '李四', phone: '139****5678' }
			],
			confirmVisible: false,
			confirmTitle: '提示',
			confirmContent: '',
			confirmConfirmText: '确定',
			confirmCancelText: '取消',
			onConfirm: null
		}
	},
	methods: {
		removeFromBlacklist(item) {
			this.confirmTitle = '确认移出'
			this.confirmContent = '确定要将 "' + item.nickname + '" 移出黑名单吗？'
			this.confirmConfirmText = '确定'
			this.confirmCancelText = '取消'
			this.onConfirm = () => {
				this.blacklist = this.blacklist.filter(b => b.id !== item.id)
				uni.showToast({ title: '已移出黑名单', icon: 'success' })
			}
			this.confirmVisible = true
		},
		}
}
</script>

<style scoped>
.blacklist-container {
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

.empty-state {
	text-align: center;
	padding: 80px 24px;
}

.empty-icon {
	display: block;
	margin-bottom: 16px;
}

.empty-title {
	font-size: 18px;
	font-weight: 800;
	color: #1E293B;
	display: block;
	margin-bottom: 8px;
}

.empty-text {
	font-size: 14px;
	color: #94A3B8;
}

.blacklist-list {
	margin: 16px 24px;
	background: #FFFFFF;
	border-radius: 20px;
	overflow: hidden;
	box-shadow: 0 2px 12px rgba(0, 0, 0, 0.04);
}

.blacklist-item {
	display: flex;
	align-items: center;
	padding: 16px 20px;
	border-bottom: 1px solid #F1F5F9;
}

.blacklist-item:last-child {
	border-bottom: none;
}

.user-avatar {
	width: 48px;
	height: 48px;
	background: linear-gradient(135deg, #64748B, #94A3B8);
	border-radius: 50%;
	display: flex;
	align-items: center;
	justify-content: center;
	font-size: 18px;
	color: #FFFFFF;
	font-weight: 700;
	margin-right: 14px;
}

.user-info {
	flex: 1;
}

.user-name {
	font-size: 15px;
	font-weight: 700;
	color: #1E293B;
	display: block;
	margin-bottom: 4px;
}

.user-phone {
	font-size: 12px;
	color: #94A3B8;
}

.action-btn {
	padding: 8px 16px;
	background: #F8FAFC;
	border-radius: 12px;
	font-size: 12px;
	font-weight: 600;
	color: #64748B;
}

.tips-section {
	margin: 24px;
	padding: 16px;
	background: #F0FDF4;
	border-radius: 14px;
}

.tips-header {
	display: flex;
	align-items: center;
	margin-bottom: 10px;
}

.tips-icon {
	margin-right: 8px;
	display: flex;
	align-items: center;
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

.bottom-safe {
	height: 40px;
}
</style>