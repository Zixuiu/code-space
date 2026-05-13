<template>
	<view class="received-help-container">
		<view class="header">
			<text class="header-title">获得帮助次数</text>
			<view class="header-right"></view>
		</view>

		<scroll-view class="content-scroll" scroll-y>
			<view class="stats-hero">
				<view class="total-stat">
					<text class="stat-value">{{ totalHelps }}</text>
					<text class="stat-label">累计帮助次数</text>
				</view>
			</view>

			<view class="stats-grid">
				<view class="stat-card">
					<text class="card-value">{{ monthHelps }}</text>
					<text class="card-label">本月帮助</text>
				</view>
				<view class="stat-card">
					<text class="card-value">{{ weekHelps }}</text>
					<text class="card-label">本周帮助</text>
				</view>
				<view class="stat-card">
					<text class="card-value">{{ todayHelps }}</text>
					<text class="card-label">今日帮助</text>
				</view>
			</view>

			<view class="section">
				<text class="section-title">帮助记录</text>

				<view v-if="records.length === 0" class="empty-state">
					<text class="empty-icon">🤝</text>
					<text class="empty-title">暂无帮助记录</text>
					<text class="empty-text">开始帮助他人，获得成就感</text>
				</view>

				<view v-else class="records-list">
					<view
						v-for="record in records"
						:key="record.id"
						class="record-card"
					>
						<view class="record-icon">
							<IconFont :name="record.type === 'skill' ? 'star' : 'coin'" :size="40" />
						</view>
						<view class="record-info">
							<text class="record-title">{{ record.title }}</text>
							<text class="record-time">{{ record.time }}</text>
						</view>
						<text class="record-amount">+{{ record.amount }}</text>
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
			totalHelps: 156,
			monthHelps: 23,
			weekHelps: 8,
			todayHelps: 2,
			records: [
				{ id: 1, type: 'skill', title: '完成家电维修服务', time: '2024-01-15 14:30', amount: 80 },
				{ id: 2, type: 'skill', title: '完成水管疏通服务', time: '2024-01-14 10:20', amount: 60 },
				{ id: 3, type: 'order', title: '帮助邻居代购', time: '2024-01-13 16:45', amount: 15 }
			]
		}
	},
	methods: {
	}
}
</script>

<style scoped>
.received-help-container {
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

.stats-hero {
	background: linear-gradient(135deg, #10B981, #059669);
	margin: 16px 24px;
	border-radius: 24px;
	padding: 32px;
	text-align: center;
	box-shadow: 0 12px 32px rgba(16, 185, 129, 0.3);
}

.total-stat {
	display: inline-block;
}

.stat-value {
	font-size: 56px;
	font-weight: 900;
	color: #FFFFFF;
	display: block;
	letter-spacing: -2px;
}

.stat-label {
	font-size: 14px;
	color: rgba(255, 255, 255, 0.8);
	font-weight: 600;
}

.stats-grid {
	display: flex;
	gap: 12px;
	padding: 0 24px;
	margin-bottom: 24px;
}

.stat-card {
	flex: 1;
	background: #FFFFFF;
	border-radius: 16px;
	padding: 16px 12px;
	text-align: center;
	box-shadow: 0 2px 12px rgba(0, 0, 0, 0.04);
}

.card-value {
	font-size: 22px;
	font-weight: 900;
	color: #10B981;
	display: block;
	margin-bottom: 4px;
}

.card-label {
	font-size: 11px;
	color: #94A3B8;
	font-weight: 600;
}

.section {
	padding: 0 24px;
}

.section-title {
	font-size: 17px;
	font-weight: 800;
	color: #1E293B;
	display: block;
	margin-bottom: 16px;
}

.empty-state {
	background: #FFFFFF;
	border-radius: 20px;
	padding: 48px 24px;
	text-align: center;
	box-shadow: 0 2px 12px rgba(0, 0, 0, 0.04);
}

.empty-icon {
	font-size: 48px;
	display: block;
	margin-bottom: 12px;
}

.empty-title {
	font-size: 16px;
	font-weight: 700;
	color: #1E293B;
	display: block;
	margin-bottom: 6px;
}

.empty-text {
	font-size: 13px;
	color: #94A3B8;
}

.records-list {
	display: flex;
	flex-direction: column;
	gap: 12px;
}

.record-card {
	background: #FFFFFF;
	border-radius: 16px;
	padding: 16px;
	display: flex;
	align-items: center;
	box-shadow: 0 2px 12px rgba(0, 0, 0, 0.04);
}

.record-icon {
	width: 44px;
	height: 44px;
	background: linear-gradient(135deg, #10B981, #34D399);
	border-radius: 12px;
	display: flex;
	align-items: center;
	justify-content: center;
}

.record-info {
	flex: 1;
}

.record-title {
	font-size: 14px;
	font-weight: 700;
	color: #1E293B;
	display: block;
	margin-bottom: 4px;
}

.record-time {
	font-size: 12px;
	color: #94A3B8;
}

.record-amount {
	font-size: 18px;
	font-weight: 800;
	color: #10B981;
}

.bottom-safe {
	height: 40px;
}
</style>