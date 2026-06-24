<template>
	<view class="skills-container">
		<view class="header">
			<text class="header-title">我的技能</text>
			<text class="add-btn" @click="addSkill">+ 添加</text>
		</view>

		<scroll-view class="content-scroll" scroll-y>
			<view class="stats-card">
				<view class="stat-item">
					<text class="stat-value">{{ skills.length }}</text>
					<text class="stat-label">我的技能</text>
				</view>
				<view class="stat-divider"></view>
				<view class="stat-item">
					<text class="stat-value">{{ totalOrders }}</text>
					<text class="stat-label">完成订单</text>
				</view>
				<view class="stat-divider"></view>
				<view class="stat-item">
					<text class="stat-value">{{ avgRating }}</text>
					<text class="stat-label">平均评分</text>
				</view>
			</view>

			<view class="section">
				<text class="section-title">我的技能列表</text>

				<view v-if="skills.length === 0" class="empty-state">
					<view class="empty-icon"><IconFont name="tool" :size="56" /></view>
					<text class="empty-title">暂无技能</text>
					<text class="empty-text">点击右上角"添加"来发布你的技能</text>
				</view>

				<view v-else class="skills-list">
					<view
						v-for="skill in skills"
						:key="skill.id"
						class="skill-card"
					>
						<view class="skill-header">
							<view class="skill-icon"><IconFont :name="skill.icon || 'star'" :size="40" /></view>
							<view class="skill-info">
								<text class="skill-name">{{ skill.name }}</text>
								<text class="skill-category">{{ skill.category }}</text>
							</view>
							<view class="skill-status" :class="skill.status">
								{{ skill.status === 'active' ? '接单中' : '已暂停' }}
							</view>
						</view>

						<view class="skill-desc">{{ skill.description }}</view>

						<view class="skill-footer">
							<view class="skill-price">
								<text class="price-symbol">¥</text>
								<text class="price-value">{{ skill.price }}</text>
								<text class="price-unit">/次</text>
							</view>
							<view class="skill-stats">
								<text class="stat">接单 {{ skill.orders }}</text>
								<view class="stat"><IconFont name="star" :size="24" /> {{ skill.rating }}</view>
							</view>
						</view>

						<view class="skill-actions">
							<view class="action-btn" @click="editSkill(skill)">
								<text>✏️ 编辑</text>
							</view>
							<view class="action-btn" @click="toggleStatus(skill)">
								<text>{{ skill.status === 'active' ? '⏸️ 暂停' : '▶️ 开启' }}</text>
							</view>
							<view class="action-btn delete" @click="deleteSkill(skill)">
								<view><IconFont name="trash" :size="28" /> 删除</view>
							</view>
						</view>
					</view>
				</view>
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
			skills: [
				{
					id: 1,
					name: '家电维修',
					category: '维修服务',
					description: '专业家电维修，擅长空调、冰箱、洗衣机等各类家电故障排查与维修',
					price: 80,
					orders: 156,
					rating: 4.9,
					status: 'active',
					icon: 'star'
				},
				{
					id: 2,
					name: '水管疏通',
					category: '维修服务',
					description: '快速解决各类水管堵塞问题，提供下水道、马桶、浴缸疏通服务',
					price: 60,
					orders: 89,
					rating: 4.8,
					status: 'active',
					icon: 'message'
				}
			],
			confirmVisible: false,
			confirmTitle: '提示',
			confirmContent: '',
			confirmConfirmText: '确定',
			confirmCancelText: '取消',
			onConfirm: null
		}
	},
	computed: {
		totalOrders() {
			return this.skills.reduce((sum, s) => sum + s.orders, 0)
		},
		avgRating() {
			if (this.skills.length === 0) return '0.0'
			const total = this.skills.reduce((sum, s) => sum + s.rating, 0)
			return (total / this.skills.length).toFixed(1)
		}
	},
	methods: {
		addSkill() {
			uni.showToast({ title: '添加技能功能', icon: 'none' })
		},
		editSkill(skill) {
			uni.showToast({ title: '编辑技能：' + skill.name, icon: 'none' })
		},
		toggleStatus(skill) {
			skill.status = skill.status === 'active' ? 'inactive' : 'active'
			uni.showToast({
				title: skill.status === 'active' ? '已开启接单' : '已暂停接单',
				icon: 'success'
			})
		},
		deleteSkill(skill) {
			this.confirmTitle = '确认删除'
			this.confirmContent = '确定要删除技能"' + skill.name + '"吗？'
			this.confirmConfirmText = '确定'
			this.confirmCancelText = '取消'
			this.onConfirm = () => {
				this.skills = this.skills.filter(s => s.id !== skill.id)
				uni.showToast({ title: '删除成功', icon: 'success' })
			}
			this.confirmVisible = true
		},
		}
}
</script>

<style scoped>
.skills-container {
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

.add-btn {
	font-size: 30rpx;
	font-weight: 700;
	color: #10B981;
	width: 120rpx;
	text-align: right;
}

.content-scroll {
	height: calc(100vh - 144rpx);
}

.stats-card {
	display: flex;
	align-items: center;
	background: linear-gradient(135deg, #10B981, #059669);
	margin: 32rpx 48rpx;
	border-radius: 40rpx;
	padding: 48rpx;
	box-shadow: 0 16rpx 48rpx rgba(16, 185, 129, 0.25);
}

.stat-item {
	flex: 1;
	text-align: center;
}

.stat-value {
	font-size: 48rpx;
	font-weight: 900;
	color: #FFFFFF;
	display: block;
	margin-bottom: 8rpx;
}

.stat-label {
	font-size: 24rpx;
	color: rgba(255, 255, 255, 0.8);
	font-weight: 600;
}

.stat-divider {
	width: 2rpx;
	height: 80rpx;
	background: rgba(255, 255, 255, 0.3);
}

.section {
	padding: 0 48rpx;
}

.section-title {
	font-size: 34rpx;
	font-weight: 800;
	color: #1E293B;
	display: block;
	margin-bottom: 32rpx;
}

.empty-state {
	background: #FFFFFF;
	border-radius: 40rpx;
	padding: 80rpx 48rpx;
	text-align: center;
	box-shadow: 0 4rpx 24rpx rgba(0, 0, 0, 0.04);
}

.empty-icon {
	font-size: 96rpx;
	display: block;
	margin-bottom: 24rpx;
}

.empty-title {
	font-size: 32rpx;
	font-weight: 700;
	color: #1E293B;
	display: block;
	margin-bottom: 12rpx;
}

.empty-text {
	font-size: 26rpx;
	color: #94A3B8;
}

.skills-list {
	display: flex;
	flex-direction: column;
	gap: 32rpx;
}

.skill-card {
	background: #FFFFFF;
	border-radius: 40rpx;
	padding: 40rpx;
	box-shadow: 0 4rpx 24rpx rgba(0, 0, 0, 0.04);
}

.skill-header {
	display: flex;
	align-items: center;
	margin-bottom: 24rpx;
}

.skill-icon {
	width: 104rpx;
	height: 104rpx;
	background: linear-gradient(135deg, #10B981, #34D399);
	border-radius: 28rpx;
	display: flex;
	align-items: center;
	justify-content: center;
	font-size: 52rpx;
	margin-right: 28rpx;
}

.skill-info {
	flex: 1;
}

.skill-name {
	font-size: 32rpx;
	font-weight: 800;
	color: #1E293B;
	display: block;
	margin-bottom: 8rpx;
}

.skill-category {
	font-size: 24rpx;
	color: #94A3B8;
}

.skill-status {
	font-size: 22rpx;
	font-weight: 700;
	padding: 8rpx 24rpx;
	border-radius: 24rpx;
}

.skill-status.active {
	background: #F0FDF4;
	color: #10B981;
}

.skill-status.inactive {
	background: #FEE2E2;
	color: #EF4444;
}

.skill-desc {
	font-size: 26rpx;
	color: #64748B;
	line-height: 1.5;
	margin-bottom: 28rpx;
}

.skill-footer {
	display: flex;
	justify-content: space-between;
	align-items: center;
	padding-bottom: 28rpx;
	border-bottom: 2rpx solid #F1F5F9;
}

.skill-price {
	display: flex;
	align-items: baseline;
}

.price-symbol {
	font-size: 28rpx;
	color: #10B981;
	font-weight: 700;
}

.price-value {
	font-size: 44rpx;
	font-weight: 900;
	color: #10B981;
}

.price-unit {
	font-size: 24rpx;
	color: #94A3B8;
	margin-left: 4rpx;
}

.skill-stats {
	display: flex;
	gap: 32rpx;
}

.stat {
	font-size: 24rpx;
	color: #64748B;
	font-weight: 600;
}

.skill-actions {
	display: flex;
	gap: 24rpx;
	margin-top: 28rpx;
}

.action-btn {
	flex: 1;
	text-align: center;
	padding: 20rpx;
	background: #F8FAFC;
	border-radius: 24rpx;
	font-size: 24rpx;
	color: #64748B;
	font-weight: 600;
}

.action-btn.delete {
	color: #EF4444;
}

.bottom-safe {
	height: 80rpx;
}
</style>