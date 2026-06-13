<template>
	<view class="container">
		<!-- 沉浸式头部 -->
		<view class="header-section">
			<view class="header-content">
				<view class="greeting-box">
					<text class="greeting">{{ getGreeting() }}，{{ userStore.currentUser.nickname || '邻居' }}</text>
					<text class="stats-summary">今天有 {{ needStore.filteredNeedsGetter.length }} 个新需求等待帮助</text>
				</view>
				<view class="location-picker" @click="getLocation">
					<IconFont name="location" :size="28" />
					<text class="loc-name">{{ locationName }}</text>
					<text class="loc-arrow"><IconFont name="chevron-right" :size="24" /></text>
				</view>
			</view>

			<!-- 搜索框 -->
			<view class="search-container">
				<view class="search-bar">
					<IconFont name="search" :size="32" class="search-icon" />
					<input
						class="search-input"
						placeholder="找点什么帮帮忙..."
						v-model="searchQuery"
						@input="onSearch"
					/>
					<IconFont v-if="searchQuery" name="close" :size="28" class="clear-icon" @click="clearSearch" />
				</view>
			</view>
		</view>

		<scroll-view class="main-scroll" scroll-y refresher-enabled :refresher-triggered="refreshing" @refresherrefresh="onRefresh">
			<!-- 灵动 Bento 网格 -->
			<view class="bento-grid">
				<!-- 今日推荐 (大卡片) -->
				<view class="bento-item recommend-card" @click="scrollToNeeds">
					<view class="card-content">
						<view class="card-tag">今日推荐</view>
						<view class="card-title">最适合你的 3 个任务</view>
						<view class="card-desc">基于您的技能和信用推荐</view>
					</view>
					<IconFont name="spark" :size="48" class="card-icon" />
				</view>

				<!-- 急需帮手 (中卡片) -->
				<view class="bento-item urgent-card" @click="filterUrgent">
					<view class="card-label">急需帮手</view>
					<view class="card-value">{{ urgentCount }}</view>
					<view class="card-sub">个紧急订单</view>
					<IconFont name="zap" :size="48" class="card-bg-icon" />
				</view>

				<!-- 高额赏金 (中卡片) -->
				<view class="bento-item reward-card" @click="filterHighReward">
					<view class="card-label">高额赏金</view>
					<view class="card-value">¥{{ maxReward }}</view>
					<view class="card-sub">最高可赚</view>
					<IconFont name="coin" :size="48" class="card-bg-icon" />
				</view>
			</view>

			<!-- 分类快速筛选标签栏 -->
			<view class="category-tabs">
				<scroll-view class="category-scroll" scroll-x show-scrollbar="false">
					<view 
						class="category-tab" 
						:class="{ active: activeCategory === '全部' }"
						@click="selectCategory('全部')"
					>
						<IconFont name="home" :size="40" class="tab-icon" />
						<text class="tab-name">全部</text>
					</view>
					<view 
						v-for="(cat, index) in categories" 
						:key="index"
						class="category-tab"
						:class="{ active: activeCategory === cat.name }"
						@click="selectCategory(cat.name)"
					>
						<IconFont :name="cat.icon" :size="40" class="tab-icon" />
						<text class="tab-name">{{ cat.name }}</text>
					</view>
				</scroll-view>
			</view>

			<!-- 附近需求列表 -->
			<view class="section-title-box">
				<text class="section-title">附近需求</text>
				<view class="sort-group">
					<view class="sort-btn" :class="{ active: sortBy === 'distance' }" @click="changeSort('distance')">
						<text>距离</text>
					</view>
					<view class="sort-btn" :class="{ active: sortBy === 'reward' }" @click="changeSort('reward')">
						<text>金额</text>
					</view>
					<view class="sort-btn" :class="{ active: sortBy === 'time' }" @click="changeSort('time')">
						<text>最新</text>
					</view>
					<view class="sort-btn filter-btn" :class="{ active: selectedDistance > 0 }" @click="toggleDistanceFilter">
						<IconFont name="map-pin" :size="24" class="filter-icon" />
						<text>范围</text>
					</view>
				</view>
			</view>

			<view class="needs-container">
				<view v-if="needStore.filteredNeedsGetter.length === 0 && (searchQuery || activeCategory !== '全部')" class="empty-state">
					<IconFont name="search" :size="56" class="empty-icon" />
					<text class="empty-title">搜不到</text>
					<text class="empty-subtitle">试试调整搜索词或清除筛选条件</text>
					<view class="empty-actions">
						<view class="action-chip" @click="clearFilters">
							<text>清除筛选</text>
						</view>
						<view class="action-chip primary" @click="goPublish">
							<text>发布需求</text>
						</view>
					</view>
				</view>

				<view v-else-if="needStore.filteredNeedsGetter.length === 0" class="empty-state">
					<IconFont name="flower" :size="64" class="empty-illustration" />
					<text class="empty-title">暂无新需求</text>
					<text class="empty-subtitle" v-if="!isSpecialFiltered">暂时没有需求，等待一会再来看看吧</text>
					<text class="empty-subtitle" v-else>筛选结果为空</text>
					<view class="empty-actions" v-if="isSpecialFiltered">
						<view class="action-chip primary" @click="restoreNeeds">
							<text>显示全部</text>
						</view>
					</view>
				</view>

				<view 
					v-for="need in needStore.filteredNeedsGetter" 
					:key="need.id" 
					class="need-bento-card"
					@click="goToDetail(need)"
				>
					<view class="card-top">
						<view class="user-info">
							<view class="avatar" :style="{ background: getAvatarBg(need.publisher.nickname) }">
								{{ need.publisher.nickname[0] }}
							</view>
							<view class="meta">
								<text class="name">{{ need.publisher.nickname }}</text>
								<text class="time">{{ formatTime(need.createdAt) }}</text>
							</view>
						</view>
						<text class="price">¥{{ need.reward }}</text>
					</view>
					<view class="card-body">
						<view class="title-row">
							<text v-if="need.isUrgent" class="urgent-badge">紧急</text>
							<text class="title">{{ need.title }}</text>
						</view>
						<text class="desc">{{ need.description }}</text>
					</view>
					<view class="card-footer">
						<view class="loc-wrap">
							<view class="loc-tag">
								<IconFont name="location" :size="24" class="icon" />
								<text class="loc-text">{{ need.location }}</text>
							</view>
							<text class="dist-tag" v-if="calculateDistance(need)">{{ calculateDistance(need) }}</text>
							<text class="dist-tag unknown" v-else>距离未知</text>
						</view>
						<view class="action-group">
							<view class="share-btn" @click.stop="shareNeed(need)">
								<IconFont name="share" :size="28" />
							</view>
							<view class="action-btn" @click.stop="acceptNeed(need)">接单</view>
						</view>
					</view>
				</view>
			</view>

			<view class="bottom-space"></view>
		</scroll-view>

		<!-- 自定义底部导航 -->
		<bottom-nav :current="0"></bottom-nav>

		<!-- 接单成功弹窗 -->
		<view v-if="acceptSuccessVisible" class="accept-mask" @click="acceptSuccessVisible = false">
			<view class="accept-popup" @click.stop>
				<view class="success-icon">
					<IconFont name="circle-check" :size="80" />
				</view>
				<text class="accept-title">接单成功！</text>
				<text class="accept-subtitle">请及时联系发布者，完成任务后记得完成订单</text>
				<view class="accept-actions">
					<view class="accept-btn" @click="acceptSuccessVisible = false">
						<text>知道了</text>
					</view>
				</view>
			</view>
		</view>

		<!-- 距离筛选弹窗 (移到scroll-view外部) -->
		<view class="filter-mask" v-if="showDistanceFilter" @click="closeFilter">
			<view class="filter-popup" @click.stop>
				<view class="p-title">筛选范围</view>
				<view class="p-options">
					<view 
						v-for="option in distanceOptions" 
						:key="option.value"
						class="p-opt"
						:class="{ active: selectedDistance === option.value }"
						@click="selectDistance(option.value)"
					>
						{{ option.label }}
					</view>
				</view>
			</view>
		</view>

		<!-- GPS提示弹窗 -->
		<view v-if="gpsModalVisible" style="position:fixed;top:0;left:0;right:0;bottom:0;background:rgba(0,0,0,0.5);z-index:99999;display:flex;align-items:center;justify-content:center;" @click="closeGpsModal">
			<view style="width:560rpx;background:#FFFFFF;border-radius:32rpx;overflow:hidden;" @click.stop>
				<view style="padding:40rpx 40rpx 20rpx;text-align:center;">
					<text style="font-size:34rpx;font-weight:700;color:#1E293B;">提示</text>
				</view>
				<view style="padding:0 40rpx 30rpx;text-align:center;">
					<text style="font-size:28rpx;color:#64748B;line-height:1.6;">请开启手机GPS定位，以获取更精准的附近需求信息</text>
				</view>
				<view style="display:flex;border-top:1rpx solid #F1F5F9;">
					<view style="flex:1;height:96rpx;display:flex;align-items:center;justify-content:center;" @click="closeGpsModal">
						<text style="font-size:30rpx;font-weight:600;color:#64748B;">稍后再说</text>
					</view>
					<view style="flex:1;height:96rpx;display:flex;align-items:center;justify-content:center;border-left:1rpx solid #F1F5F9;" @click="openLocationSettings">
						<text style="font-size:30rpx;font-weight:700;color:#10B981;">去开启</text>
					</view>
				</view>
			</view>
		</view>

		<!-- 自定义分享弹窗 -->
		<view v-if="shareModalVisible" style="position:fixed;top:0;left:0;right:0;bottom:0;background:rgba(0,0,0,0.7);z-index:9999;display:flex;flex-direction:column;justify-content:flex-end;">
			<view style="background:#fff;border-radius:40rpx 40rpx 0 0;padding:32rpx 40rpx 60rpx;">
				<view style="display:flex;justify-content:space-between;align-items:center;margin-bottom:32rpx;">
					<text style="font-size:36rpx;font-weight:800;color:#1E293B;">分享赚佣金</text>
					<view style="width:52rpx;height:52rpx;background:#F1F5F9;border-radius:50%;display:flex;align-items:center;justify-content:center;" @click="shareModalVisible = false">
						<IconFont name="close" :size="28" />
					</view>
				</view>

				<view style="background:linear-gradient(135deg, #F0FDF4, #ECFDF5);border-radius:24rpx;padding:28rpx;margin-bottom:32rpx;">
					<view style="display:flex;justify-content:space-between;align-items:center;margin-bottom:20rpx;">
						<text style="font-size:30rpx;font-weight:700;color:#1E293B;flex:1;">{{ currentShareNeed?.title || '' }}</text>
						<view style="display:flex;align-items:center;gap:8rpx;background:#10B981;padding:8rpx 16rpx;border-radius:100rpx;">
							<text style="font-size:22rpx;color:rgba(255,255,255,0.8);">赏金</text>
							<text style="font-size:26rpx;font-weight:800;color:#fff;">¥{{ currentShareNeed?.reward || 0 }}</text>
						</view>
					</view>

					<view style="display:flex;align-items:center;gap:12rpx;padding:16rpx 20rpx;background:rgba(255,255,255,0.8);border-radius:16rpx;margin-bottom:16rpx;">
						<IconFont name="spark" :size="32" />
						<text style="font-size:24rpx;color:#64748B;flex:1;">分享给好友，好友完成帮忙后你可获得 5% 佣金</text>
					</view>

					<view style="display:flex;justify-content:space-between;align-items:center;padding-top:16rpx;border-top:1rpx dashed #D1D5DB;">
						<text style="font-size:26rpx;color:#64748B;">预估佣金</text>
						<text style="font-size:40rpx;font-weight:900;color:#10B981;">¥{{ ((currentShareNeed?.reward || 0) * 0.05).toFixed(2) }}</text>
					</view>
				</view>

				<view style="display:flex;justify-content:space-around;margin-bottom:32rpx;">
					<view style="display:flex;flex-direction:column;align-items:center;gap:12rpx;" @click="doShare('wechat')">
						<view style="width:100rpx;height:100rpx;background:#F0FDF4;border-radius:24rpx;display:flex;align-items:center;justify-content:center;">
							<IconFont name="send" :size="48" />
						</view>
						<text style="font-size:24rpx;color:#64748B;font-weight:600;">微信好友</text>
					</view>
					<view style="display:flex;flex-direction:column;align-items:center;gap:12rpx;" @click="doShare('moments')">
						<view style="width:100rpx;height:100rpx;background:#FEF3C7;border-radius:24rpx;display:flex;align-items:center;justify-content:center;">
							<IconFont name="share" :size="48" />
						</view>
						<text style="font-size:24rpx;color:#64748B;font-weight:600;">朋友圈</text>
					</view>
					<view style="display:flex;flex-direction:column;align-items:center;gap:12rpx;" @click="doShare('copy')">
						<view style="width:100rpx;height:100rpx;background:#EFF6FF;border-radius:24rpx;display:flex;align-items:center;justify-content:center;">
							<IconFont name="link" :size="48" />
						</view>
						<text style="font-size:24rpx;color:#64748B;font-weight:600;">复制链接</text>
					</view>
				</view>

				<view style="width:100%;height:96rpx;background:#F1F5F9;border-radius:48rpx;display:flex;align-items:center;justify-content:center;" @click="shareModalVisible = false">
					<text style="font-size:32rpx;font-weight:700;color:#64748B;">取消</text>
				</view>
			</view>
		</view>
	</view>
</template>

<script>
import { useUserStore } from '@/store/user'
import { useNeedStore } from '@/store/need'
import BottomNav from '@/components/bottom-nav/bottom-nav.vue'
import IconFont from '@/components/icon-font/icon-font.vue'

export default {
	components: {
		BottomNav,
		IconFont
	},
	setup() {
		const userStore = useUserStore()
		const needStore = useNeedStore()
		return { userStore, needStore }
	},
	data() {
		return {
			refreshing: false,
			searchQuery: '',
			shareModalVisible: false,
			currentShareNeed: null,
			locationName: '阳光花园',
			userLatitude: 39.908823,
			userLongitude: 116.397470,
			selectedDistance: 0,
			showDistanceFilter: false,
			gpsModalVisible: false,
			acceptSuccessVisible: false,
			activeCategory: '全部',
			sortBy: 'time',
			isSpecialFiltered: false,
			locationInitialized: false,
			distanceOptions: [
				{ label: '全部距离', value: 0 },
				{ label: '1km 内', value: 1 },
				{ label: '3km 内', value: 3 },
				{ label: '5km 内', value: 5 }
			],
			categories: [
				{ name: '跑腿', icon: 'run', bgColor: '#F0FDF4' },
				{ name: '家务', icon: 'housework', bgColor: '#FEF9E7' },
				{ name: '专业', icon: 'professional', bgColor: '#F0F4FF' },
				{ name: '其他', icon: 'others', bgColor: '#FDF2F8' }
			]
		}
	},
	onShow() {
		uni.hideTabBar()
	},
	computed: {
		currentDistanceLabel() {
			const option = this.distanceOptions.find(o => o.value === this.selectedDistance)
			return option ? option.label : '全部距离'
		},
		urgentCount() {
			return this.needStore.filteredNeedsGetter.filter(n => n.isUrgent).length
		},
		maxReward() {
			const rewards = this.needStore.filteredNeedsGetter.map(n => n.reward)
			return rewards.length > 0 ? Math.max(...rewards) : 200
		}
	},
	methods: {
		checkGpsAndShowModal() {
			// 如果用户已经选择过位置或关闭过GPS提示，就不再显示
			const hasDismissedGps = uni.getStorageSync('hasDismissedGps')
			if (hasDismissedGps) {
				return
			}
			
			// 检查是否已经有保存的位置信息（包括从存储加载的）
			if (this.locationName && this.locationName !== '阳光花园') {
				return
			}
			
			// 如果GPS已经开启，就不再提示，直接标记为已处理
			const gpsEnabled = uni.getStorageSync('gpsEnabled')
			if (gpsEnabled) {
				uni.setStorageSync('hasDismissedGps', true)
				return
			}
			
			// 只在第一次打开时显示一次GPS提示
			// 这样避免了GPS检测不准确导致的反复弹窗
			this.gpsModalVisible = true
			// 记录已经显示过提示，防止反复弹出
			uni.setStorageSync('hasDismissedGps', true)
		},
		getAvatarBg(name) {
			const colors = ['#10B981', '#3B82F6', '#F59E0B', '#EF4444', '#8B5CF6']
			if (!name || name.length === 0) return colors[0]
			let hash = 0
			for (let i = 0; i < name.length; i++) {
				hash = name.charCodeAt(i) + ((hash << 5) - hash)
			}
			return colors[Math.abs(hash) % colors.length]
		},
		formatTime(timestamp) {
			const diff = Date.now() - timestamp
			if (diff < 3600000) return `${Math.floor(diff/60000)}分钟前`
			if (diff < 86400000) return `${Math.floor(diff/3600000)}小时前`
			return `${Math.floor(diff/86400000)}天前`
		},
		calculateDistance(need) {
			if (!need.latitude || !need.longitude) return ''
			const R = 6371
			const dLat = this.deg2rad(need.latitude - this.userLatitude)
			const dLon = this.deg2rad(need.longitude - this.userLongitude)
			const a = 
				Math.sin(dLat/2) * Math.sin(dLat/2) +
				Math.cos(this.deg2rad(this.userLatitude)) * Math.cos(this.deg2rad(need.latitude)) *
				Math.sin(dLon/2) * Math.sin(dLon/2)
			const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a))
			const d = R * c
			if (d < 1) {
				return `${Math.round(d * 1000)}m`
			}
			return `${d.toFixed(1)}km`
		},
		deg2rad(deg) {
			return deg * (Math.PI / 180)
		},
		getGreeting() {
			const hour = new Date().getHours()
			if (hour >= 5 && hour < 12) return '早安'
			if (hour >= 12 && hour < 14) return '午安'
			if (hour >= 14 && hour < 18) return '下午好'
			if (hour >= 18 && hour < 22) return '晚上好'
			return '夜深了'
		},
		onSearch() {
			this.needStore.setSearchQuery(this.searchQuery)
			this.applyFilters()
		},
		clearSearch() {
			this.searchQuery = ''
			this.needStore.setSearchQuery('')
			this.applyFilters()
		},
		clearFilters() {
			this.searchQuery = ''
			this.activeCategory = '全部'
			this.sortBy = 'time'
			this.needStore.setSearchQuery('')
			this.applyFilters()
			uni.showToast({ title: '已清除筛选条件', icon: 'success' })
		},
		goPublish() {
			uni.navigateTo({ url: '/pages/publish/publish' })
		},
		selectCategory(name) {
			this.activeCategory = name === this.activeCategory && name !== '全部' ? '全部' : name
			this.isSpecialFiltered = false
			this.applyFilters()
		},
		clearCategory() {
			this.activeCategory = '全部'
			this.isSpecialFiltered = false
			this.applyFilters()
			uni.showToast({ title: '已清除分类筛选', icon: 'none' })
		},
		filterUrgent() {
			uni.showToast({ title: '已为您筛选紧急需求', icon: 'none' })
			const urgent = this.needStore.filteredNeedsGetter.filter(n => n.isUrgent)
			if (urgent.length > 0) {
				this.needStore.setFilteredNeeds(urgent)
				this.isSpecialFiltered = true
			} else {
				uni.showToast({ title: '暂无紧急需求', icon: 'none' })
			}
		},
		filterHighReward() {
			uni.showToast({ title: '已为您筛选高额赏金', icon: 'none' })
			const highReward = this.needStore.filteredNeedsGetter.filter(n => n.reward >= 30)
			if (highReward.length > 0) {
				this.needStore.setFilteredNeeds(highReward)
				this.isSpecialFiltered = true
			} else {
				uni.showToast({ title: '暂无高额赏金需求', icon: 'none' })
			}
		},
		restoreNeeds() {
			this.isSpecialFiltered = false
			this.applyFilters()
			uni.showToast({ title: '已显示全部需求', icon: 'none' })
		},
		applyFilters() {
			let needs = this.needStore.needs.filter(n => n.status === 'open')

			if (this.searchQuery.trim()) {
				const query = this.searchQuery.toLowerCase()
				needs = needs.filter(n =>
					n.title.toLowerCase().includes(query) ||
					n.description.toLowerCase().includes(query) ||
					n.location.toLowerCase().includes(query)
				)
			}

			if (this.activeCategory !== '全部') {
				needs = needs.filter(n => n.category === this.activeCategory)
			}

			// 距离筛选
			if (this.selectedDistance > 0) {
				needs = needs.filter(n => {
					if (!n.latitude || !n.longitude) return false
					const dist = this.getDistance(n.latitude, n.longitude)
					return dist <= this.selectedDistance
				})
			}

			needs = this.sortNeeds(needs)

			this.needStore.setFilteredNeeds(needs)
		},
		changeSort(type) {
			if (this.sortBy === type) {
				return
			}
			
			this.sortBy = type
			this.needStore.setSortBy(type)
			this.applyFilters()
			
			const sortNames = {
				distance: '距离最近',
				reward: '金额最高',
				time: '最新发布'
			}
			uni.showToast({ title: `已按${sortNames[type]}排序`, icon: 'none' })
		},
		sortNeeds(needs) {
			const sorted = [...needs]
			
			switch(this.sortBy) {
				case 'distance':
					sorted.sort((a, b) => {
						const distA = this.getDistance(a.latitude, a.longitude)
						const distB = this.getDistance(b.latitude, b.longitude)
						return distA - distB
					})
					break
				case 'reward':
					sorted.sort((a, b) => b.reward - a.reward)
					break
				case 'time':
				default:
					sorted.sort((a, b) => b.createdAt - a.createdAt)
					break
			}
			
			return sorted
		},
		getDistance(lat, lng) {
			if (!lat || !lng || isNaN(lat) || isNaN(lng)) {
				return Number.MAX_VALUE
			}
			const R = 6371
			const dLat = (lat - this.userLatitude) * Math.PI / 180
			const dLng = (lng - this.userLongitude) * Math.PI / 180
			const a = Math.sin(dLat/2) * Math.sin(dLat/2) +
					  Math.cos(this.userLatitude * Math.PI / 180) * Math.cos(lat * Math.PI / 180) *
					  Math.sin(dLng/2) * Math.sin(dLng/2)
			const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a))
			return R * c
		},
		scrollToNeeds() {
			// 简单的滚动提示
			uni.showToast({ title: '为您匹配最佳任务', icon: 'none' })
		},
		async acceptNeed(need) {
			if (!this.userStore.isLoggedIn || !this.userStore.token) {
				uni.showToast({ title: '请先登录后再接单', icon: 'none' })
				setTimeout(() => {
					uni.navigateTo({ url: '/pages/login/login' })
				}, 500)
				return
			}
			const result = await this.needStore.acceptNeed(need.id)
			if (result.success) {
				need.status = 'accepted'
				this.acceptSuccessVisible = true
				setTimeout(() => {
					this.acceptSuccessVisible = false
				}, 3000)
			} else {
				uni.showToast({ title: result.message, icon: 'none' })
			}
		},
		shareNeed(need) {
			this.currentShareNeed = need
			this.shareModalVisible = true
			this.userStore.addSharedNeed(need.id, need.title, need.reward)
		},
		doShare(type) {
			if (!this.currentShareNeed) return

			const shareUrl = `https://wolaibang.com/download?need=${this.currentShareNeed.id}`
			const shareText = `【我来帮】帮你${this.currentShareNeed.title}，赏金${this.currentShareNeed.reward}元！点击链接查看：${shareUrl}`

			if (type === 'copy') {
				uni.setClipboardData({
					data: shareText,
					success: () => {
						uni.showToast({ title: '链接已复制，去分享给好友吧！', icon: 'success' })
						this.shareModalVisible = false
					},
					fail: () => {
						uni.showToast({ title: '复制失败，请重试', icon: 'none' })
					}
				})
			} else if (type === 'wechat') {
				uni.share({
					provider: 'weixin',
					scene: 'WXSceneSession',
					type: 0,
					href: shareUrl,
					title: '我来帮 - 邻里互助',
					summary: shareText,
					success: () => {
						this.shareModalVisible = false
					},
					fail: (err) => {
						if (err.errMsg && err.errMsg.includes('cancel')) {
							return
						}
						uni.showToast({ title: '请先安装微信或检查分享配置', icon: 'none', duration: 2000 })
					}
				})
			} else if (type === 'moments') {
				uni.share({
					provider: 'weixin',
					scene: 'WXSenceTimeline',
					type: 0,
					href: shareUrl,
					title: '我来帮 - 邻里互助',
					summary: shareText,
					success: () => {
						this.shareModalVisible = false
					},
					fail: (err) => {
						if (err.errMsg && err.errMsg.includes('cancel')) {
							return
						}
						uni.showToast({ title: '请先安装微信或检查分享配置', icon: 'none', duration: 2000 })
					}
				})
			}
		},
		goToDetail(need) {
			uni.navigateTo({
				url: `/pages/need-detail/need-detail?id=${need.id}`
			})
		},
		onRefresh() {
			this.refreshing = true
			setTimeout(() => {
				this.refreshing = false
				uni.showToast({ title: '刷新成功', icon: 'success' })
			}, 1000)
		},
		selectDistance(value) {
			this.selectedDistance = value
			this.showDistanceFilter = false
			
			// 应用距离筛选
			this.applyFilters()
			
			if (value === 0) {
				uni.showToast({ title: '显示全部需求', icon: 'none' })
			} else {
				uni.showToast({ title: `已筛选${value}km内的需求`, icon: 'none' })
			}
		},
		toggleDistanceFilter() {
			this.showDistanceFilter = !this.showDistanceFilter
		},
		closeFilter() {
			this.showDistanceFilter = false
		},
		closeGpsModal() {
			this.gpsModalVisible = false
			// 记录用户已经关闭过GPS提示，以后不再显示
			uni.setStorageSync('hasDismissedGps', true)
		},
		openLocationSettings() {
			this.gpsModalVisible = false
			// 记录用户已经处理过GPS提示，以后不再显示
			uni.setStorageSync('hasDismissedGps', true)
			// #ifdef APP-PLUS
			if (plus.os.name === 'Android') {
				const main = plus.android.runtimeMainActivity()
				const Intent = plus.android.importClass('android.content.Intent')
				const intent = new Intent()
				intent.setAction('android.settings.LOCATION_SOURCE_SETTINGS')
				main.startActivity(intent)
			} else {
				const NSURL = plus.ios.import('NSURL')
				const url = NSURL.URLWithString('App-Prefs:root=Privacy&path=LOCATION')
				const app = plus.ios.import('UIApplication').sharedApplication()
				app.openURL(url)
			}
			// #endif
		},
		getLocation() {
			// 设置超时，如果检测超过0.1秒就直接弹窗提示
			const timeout = setTimeout(() => {
				this.gpsModalVisible = true
			}, 100)
			
			// 检测GPS状态
			let isGpsEnabled = false
			// #ifdef APP-PLUS
			try {
				if (plus.os.name === 'Android') {
					const main = plus.android.runtimeMainActivity()
					const Context = plus.android.importClass('android.content.Context')
					const LocationManager = plus.android.importClass('android.location.LocationManager')
					const lm = main.getSystemService(Context.LOCATION_SERVICE)
					if (lm) {
						isGpsEnabled = lm.isProviderEnabled(LocationManager.GPS_PROVIDER) || 
									   lm.isProviderEnabled(LocationManager.NETWORK_PROVIDER)
					}
				} else if (plus.os.name === 'iOS') {
					const CLLocationManager = plus.ios.import('CLLocationManager')
					isGpsEnabled = CLLocationManager.locationServicesEnabled()
				}
			} catch (e) {
				console.log('GPS检测失败', e)
			}
			// #endif
			
			// 清除超时定时器
			clearTimeout(timeout)
			
			if (isGpsEnabled) {
				// GPS已开启，直接进入地图选点
				uni.chooseLocation({
					success: (res) => {
						if (res.name) {
							this.needStore.setUserLocation({
								latitude: res.latitude,
								longitude: res.longitude
							})
							this.userLatitude = res.latitude
							this.userLongitude = res.longitude
							this.locationName = res.name || '当前位置'
							uni.setStorageSync('userLocation', {
								name: this.locationName,
								latitude: res.latitude,
								longitude: res.longitude
							})
						}
					},
					fail: (err) => {
						if (err.errMsg && (err.errMsg.includes('cancel') || err.errMsg.includes('cancelLocation'))) {
							console.log('用户取消了位置选择')
						} else {
							uni.showToast({
								title: '定位失败，请检查位置权限设置',
								icon: 'none'
							})
						}
					}
				})
			} else {
				// GPS未开启，弹出提示窗口
				this.gpsModalVisible = true
			}
		}
	}
}
</script>

<style scoped>
.container {
	min-height: 100vh;
	background: #F8FAFC;
}

/* 头部样式 */
.header-section {
	padding: 60rpx 40rpx 30rpx;
	background: #FFFFFF;
	border-radius: 0 0 60rpx 60rpx;
	box-shadow: 0 4rpx 30rpx rgba(0, 0, 0, 0.02);
}

.header-content {
	display: flex;
	justify-content: space-between;
	align-items: flex-start;
	margin-bottom: 40rpx;
}

.greeting {
	font-size: 48rpx;
	font-weight: 800;
	color: #1E293B;
	display: block;
}

.stats-summary {
	font-size: 26rpx;
	color: #64748B;
	margin-top: 8rpx;
	display: block;
}

.location-picker {
	background: #ECFDF5;
	padding: 12rpx 24rpx;
	border-radius: 100rpx;
	display: flex;
	align-items: center;
	gap: 8rpx;
	max-width: 240rpx;
}

.loc-icon { font-size: 24rpx; }
.loc-name { 
	font-size: 22rpx; 
	color: #10B981; 
	font-weight: 700;
	white-space: nowrap;
	overflow: hidden;
	text-overflow: ellipsis;
}
.loc-arrow { color: #10B981; font-size: 28rpx; }

/* 搜索框 */
.search-container {
	margin-top: 10rpx;
}

.search-bar {
	background: #F1F5F9;
	height: 90rpx;
	border-radius: 30rpx;
	display: flex;
	align-items: center;
	padding: 0 30rpx;
}

.search-icon { font-size: 32rpx; margin-right: 20rpx; }
.search-input { flex: 1; font-size: 28rpx; color: #1E293B; }
.clear-icon { padding: 10rpx; color: #94A3B8; }

.main-scroll {
	height: calc(100vh - 350rpx);
}

/* Bento 网格 */
.bento-grid {
	padding: 40rpx;
	display: grid;
	grid-template-columns: repeat(2, 1fr);
	grid-auto-rows: 200rpx;
	gap: 24rpx;
}

.bento-item {
	background: #FFFFFF;
	border-radius: 48rpx;
	padding: 30rpx;
	position: relative;
	overflow: hidden;
	box-shadow: 0 4rpx 20rpx rgba(0, 0, 0, 0.02);
}

.recommend-card {
	grid-column: span 2;
	grid-row: span 1;
	background: linear-gradient(135deg, #10B981, #34D399);
	color: #FFFFFF;
	display: flex;
	justify-content: space-between;
	align-items: center;
}

.recommend-card .card-tag {
	font-size: 22rpx;
	background: rgba(255, 255, 255, 0.2);
	padding: 4rpx 16rpx;
	border-radius: 10rpx;
	width: fit-content;
	margin-bottom: 12rpx;
}

.recommend-card .card-title {
	font-size: 36rpx;
	font-weight: 800;
}

.recommend-card .card-desc {
	font-size: 22rpx;
	opacity: 0.8;
	margin-top: 4rpx;
}

.recommend-card .card-icon {
	font-size: 80rpx;
	opacity: 0.9;
}

.urgent-card {
	background: #FFF7ED;
}

.urgent-card .card-label { font-size: 24rpx; color: #EA580C; font-weight: 700; }
.urgent-card .card-value { font-size: 56rpx; font-weight: 800; color: #EA580C; margin: 4rpx 0; }
.urgent-card .card-sub { font-size: 22rpx; color: #F97316; }

.reward-card {
	background: #F0F9FF;
}

.reward-card .card-label { font-size: 24rpx; color: #0284C7; font-weight: 700; }
.reward-card .card-value { font-size: 50rpx; font-weight: 800; color: #0284C7; margin: 4rpx 0; }
.reward-card .card-sub { font-size: 22rpx; color: #0EA5E9; }

.card-bg-icon {
	position: absolute;
	right: -10rpx;
	bottom: -10rpx;
	font-size: 80rpx;
	opacity: 0.1;
	transform: rotate(-15deg);
}

/* 分类 Bento 盒子 */
.category-bento-box {
	grid-column: span 2;
	display: grid;
	grid-template-columns: repeat(4, 1fr);
	gap: 20rpx;
}

.cat-mini-card {
	background: #FFFFFF;
	border-radius: 36rpx;
	display: flex;
	flex-direction: column;
	align-items: center;
	justify-content: center;
	padding: 20rpx 0;
	box-shadow: 0 4rpx 20rpx rgba(0, 0, 0, 0.02);
	transition: all 0.2s;
}

.cat-mini-card.active {
	background: #ECFDF5;
	border: 2rpx solid #10B981;
}

.cat-mini-card.clear-btn {
	background: #FEF2F2;
	border: 2rpx solid #FECACA;
}

.cat-mini-card.clear-btn .cat-emoji {
	color: #EF4444;
}

.cat-mini-card.clear-btn .cat-name {
	color: #EF4444;
}

.cat-mini-card .cat-emoji { font-size: 40rpx; margin-bottom: 8rpx; }
.cat-mini-card .cat-name { font-size: 22rpx; font-weight: 600; color: #64748B; }

/* 分类快速筛选标签栏 */
.category-tabs {
	padding: 0 40rpx 20rpx;
	background: #FFFFFF;
}

.category-scroll {
	white-space: nowrap;
}

.category-tab {
	display: inline-flex;
	align-items: center;
	padding: 16rpx 28rpx;
	margin-right: 16rpx;
	background: #F1F5F9;
	border-radius: 100rpx;
	transition: all 0.2s;
	white-space: nowrap;
}

.category-tab .tab-icon {
	font-size: 36rpx;
	margin-right: 10rpx;
}

.category-tab .tab-name {
	font-size: 26rpx;
	font-weight: 600;
	color: #64748B;
}

.category-tab.active {
	background: linear-gradient(135deg, #10B981, #059669);
	box-shadow: 0 4rpx 12rpx rgba(16, 185, 129, 0.25);
}

.category-tab.active .tab-name {
	color: #FFFFFF;
}

/* 列表标题 */
.section-title-box {
	padding: 20rpx 40rpx;
	display: flex;
	justify-content: space-between;
	align-items: center;
}

.section-title {
	font-size: 34rpx;
	font-weight: 800;
	color: #1E293B;
}

.sort-group {
	display: flex;
	gap: 12rpx;
}

.sort-btn {
	background: #F1F5F9;
	padding: 10rpx 18rpx;
	border-radius: 100rpx;
	font-size: 22rpx;
	color: #64748B;
	transition: all 0.2s;
}

.sort-btn.active {
	background: linear-gradient(135deg, #10B981, #059669);
	color: #FFFFFF;
	box-shadow: 0 4rpx 12rpx rgba(16, 185, 129, 0.25);
}

.sort-btn.filter-btn {
	padding: 10rpx 18rpx;
	display: flex;
	align-items: center;
	gap: 4rpx;
}

.filter-icon {
	display: flex;
	align-items: center;
}

/* 需求卡片 (Bento 风格) */
.needs-container {
	padding: 0 40rpx 40rpx;
}

.need-bento-card {
	background: #FFFFFF;
	border-radius: 48rpx;
	padding: 30rpx;
	margin-bottom: 24rpx;
	box-shadow: 0 4rpx 24rpx rgba(0, 0, 0, 0.02);
}

.need-bento-card .card-top {
	display: flex;
	justify-content: space-between;
	align-items: center;
	margin-bottom: 20rpx;
}

.need-bento-card .user-info {
	display: flex;
	align-items: center;
	gap: 16rpx;
}

.need-bento-card .avatar {
	width: 64rpx;
	height: 64rpx;
	border-radius: 20rpx;
	display: flex;
	align-items: center;
	justify-content: center;
	color: #FFFFFF;
	font-weight: 800;
	font-size: 28rpx;
}

.need-bento-card .meta {
	display: flex;
	flex-direction: column;
}

.need-bento-card .name { font-size: 26rpx; font-weight: 700; color: #1E293B; }
.need-bento-card .time { font-size: 20rpx; color: #94A3B8; }

.need-bento-card .price { font-size: 34rpx; font-weight: 800; color: #10B981; }

.need-bento-card .title-row {
	display: flex;
	align-items: center;
	gap: 8rpx;
	margin-bottom: 8rpx;
}

.need-bento-card .urgent-badge {
	background: #FFF7ED;
	color: #EA580C;
	font-size: 20rpx;
	font-weight: 700;
	padding: 4rpx 12rpx;
	border-radius: 8rpx;
	flex-shrink: 0;
}

.need-bento-card .title {
	font-size: 30rpx;
	font-weight: 800;
	color: #1E293B;
	display: inline;
}

.need-bento-card .desc {
	font-size: 26rpx;
	color: #64748B;
	line-height: 1.5;
	display: -webkit-box;
	-webkit-line-clamp: 2;
	-webkit-box-orient: vertical;
	overflow: hidden;
}

.need-bento-card .card-footer {
	margin-top: 24rpx;
	display: flex;
	justify-content: space-between;
	align-items: center;
}

.action-group {
	display: flex;
	gap: 12rpx;
	align-items: center;
}

.share-btn {
	width: 64rpx;
	height: 64rpx;
	background: #F0F9FF;
	border-radius: 100rpx;
	display: flex;
	align-items: center;
	justify-content: center;
	font-size: 28rpx;
}

.need-bento-card .action-btn {
	background: #10B981;
	color: #FFFFFF;
	font-size: 24rpx;
	font-weight: 700;
	padding: 12rpx 36rpx;
	border-radius: 100rpx;
}

.loc-wrap {
	display: inline-flex;
	align-items: center;
	gap: 16rpx;
	flex-wrap: wrap;
}

.loc-tag {
	display: inline-flex;
	align-items: center;
	gap: 8rpx;
	background: #F3F4F6;
	padding: 8rpx 16rpx;
	border-radius: 12rpx;
}

.loc-tag .icon {
	font-size: 20rpx;
	color: #6B7280;
}

.loc-text {
	font-size: 22rpx;
	color: #6B7280;
	font-weight: 400;
}

.dist-tag {
	font-size: 20rpx;
	color: #10B981;
	font-weight: 600;
	background: #ECFDF5;
	padding: 8rpx 16rpx;
	border-radius: 12rpx;
}

.dist-tag.unknown {
	color: #9CA3AF;
	background: #F3F4F6;
}

/* 弹窗筛选 */
.filter-mask {
	position: fixed;
	inset: 0;
	background: rgba(0, 0, 0, 0.4);
	backdrop-filter: blur(4rpx);
	z-index: 10000;
	display: flex;
	align-items: flex-end;
}

.filter-popup {
	width: 100%;
	background: #FFFFFF;
	border-radius: 60rpx 60rpx 0 0;
	padding: 40rpx 40rpx calc(40rpx + env(safe-area-inset-bottom));
}

.filter-popup .p-title {
	font-size: 32rpx;
	font-weight: 800;
	color: #1E293B;
	margin-bottom: 30rpx;
}

.filter-popup .p-options {
	display: flex;
	flex-wrap: wrap;
	gap: 16rpx;
}

.filter-popup .p-opt {
	background: #F1F5F9;
	padding: 24rpx;
	border-radius: 24rpx;
	text-align: center;
	font-size: 26rpx;
	font-weight: 600;
	color: #64748B;
}

.filter-popup .p-opt.active {
	background: #10B981;
	color: #FFFFFF;
}

.bottom-space { height: 100rpx; }

.empty-state {
	padding: 60rpx 40rpx;
	text-align: center;
	display: flex;
	flex-direction: column;
	align-items: center;
}

.empty-icon { font-size: 100rpx; margin-bottom: 20rpx; display: block; }
.empty-title { font-size: 30rpx; font-weight: 700; color: #64748B; }
.empty-subtitle { font-size: 24rpx; color: #94A3B8; margin-top: 8rpx; }

.empty-illustration {
	font-size: 120rpx;
	margin-bottom: 24rpx;
}

.empty-actions {
	display: flex;
	gap: 20rpx;
	margin-top: 32rpx;
}

.action-chip {
	padding: 16rpx 32rpx;
	background: #F1F5F9;
	border-radius: 100rpx;
	font-size: 26rpx;
	font-weight: 600;
	color: #64748B;
}

.action-chip.primary {
	background: linear-gradient(135deg, #10B981, #059669);
	color: #FFFFFF;
}

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

.share-actions .share-btn {
	display: flex;
	flex-direction: column;
	align-items: center;
	gap: 12rpx;
}

.share-actions .btn-icon {
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

.share-actions .btn-text {
	font-size: 24rpx;
	color: #64748B;
	font-weight: 600;
}

.share-actions .share-btn.wechat .btn-icon {
	background: #F0FDF4;
}

.share-actions .share-btn.moments .btn-icon {
	background: #FEF3C7;
}

.share-actions .share-btn.copy .btn-icon {
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

/* 接单成功弹窗 */
.accept-mask {
	position: fixed;
	top: 0;
	left: 0;
	right: 0;
	bottom: 0;
	background: rgba(0, 0, 0, 0.5);
	display: flex;
	align-items: center;
	justify-content: center;
	z-index: 9999;
}

.accept-popup {
	width: 600rpx;
	background: #FFFFFF;
	border-radius: 40rpx;
	padding: 30rpx 40rpx 40rpx;
	text-align: center;
	box-shadow: 0 20rpx 60rpx rgba(0, 0, 0, 0.15);
	animation: popup 0.3s ease;
}

@keyframes popup {
	0% { transform: scale(0.8); opacity: 0; }
	100% { transform: scale(1); opacity: 1; }
}

.success-icon {
	width: 120rpx;
	height: 120rpx;
	background: #ECFDF5;
	border-radius: 50%;
	display: flex;
	align-items: center;
	justify-content: center;
	margin: 0 auto 30rpx;
}

.accept-title {
	font-size: 40rpx;
	font-weight: 800;
	color: #1E293B;
	margin-bottom: 16rpx;
	display: block;
}

.accept-subtitle {
	font-size: 28rpx;
	color: #64748B;
	line-height: 1.6;
	display: block;
	margin-bottom: 40rpx;
}

.accept-actions {
	width: 100%;
}

.accept-btn {
	width: 100%;
	height: 96rpx;
	background: linear-gradient(135deg, #10B981, #34D399);
	border-radius: 48rpx;
	display: flex;
	align-items: center;
	justify-content: center;
}

.accept-btn text {
	font-size: 32rpx;
	font-weight: 700;
	color: #FFFFFF;
}
</style>
