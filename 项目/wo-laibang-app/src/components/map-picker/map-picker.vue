<template>
	<view class="map-picker-overlay" @click="handleOverlayClick">
		<view class="map-picker-container" @click.stop>
			<view class="picker-header">
				<view class="header-left" @click="close">
					<IconFont name="x" :size="40" class="close-icon" />
				</view>
				<text class="header-title">选择位置</text>
				<view class="header-right" @click="confirm">
					<text class="confirm-text">确认</text>
				</view>
			</view>

			<view class="search-bar">
				<IconFont name="search" :size="32" class="search-icon" />
				<input
					class="search-input"
					v-model="searchKeyword"
					placeholder="搜索地点"
					@input="onSearchInput"
					@confirm="onSearchConfirm"
				/>
				<view class="locate-btn" @click="getCurrentLocation">
					<IconFont name="map-location" :size="32" />
				</view>
			</view>

			<view class="map-wrapper">
				<map
					id="map"
					class="map"
					:latitude="centerLatitude"
					:longitude="centerLongitude"
					:markers="markers"
					:show-location="true"
					:enable-overlooking="true"
					@regionchange="onRegionChange"
					@tap="onMapTap"
				></map>
				<view class="center-marker">
					<view class="marker-ring"></view>
					<view class="marker-center"></view>
				</view>
			</view>

			<view class="location-panel">
				<view class="location-loading" v-if="loading">
					<view class="loading-spinner"></view>
					<text class="loading-text">正在获取地址...</text>
				</view>
				<view class="location-result" v-else>
					<view class="location-icon-wrapper">
						<IconFont name="map-pin" :size="40" class="loc-icon" />
					</view>
					<view class="location-content">
						<text class="location-address">{{ address || '拖动地图或搜索选择位置' }}</text>
						<text class="location-coords" v-if="selectedLongitude">
							{{ selectedLatitude.toFixed(6) }}, {{ selectedLongitude.toFixed(6) }}
						</text>
					</view>
				</view>

				<view class="search-results" v-if="showSearchResults && searchResults.length > 0">
					<view
						class="search-item"
						v-for="(item, index) in searchResults"
						:key="index"
						@click="onSearchResultClick(item)"
					>
						<IconFont name="location" :size="32" class="result-icon" />
						<view class="result-content">
							<text class="result-title">{{ item.title }}</text>
							<text class="result-address">{{ item.address }}</text>
						</view>
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
	props: {
		visible: {
			type: Boolean,
			default: false
		}
	},
	data() {
		return {
			centerLatitude: 39.908823,
			centerLongitude: 116.397470,
			selectedLatitude: 39.908823,
			selectedLongitude: 116.397470,
			address: '',
			loading: false,
			markers: [],
			searchKeyword: '',
			searchResults: [],
			showSearchResults: false,
			searchTimer: null
		}
	},
	methods: {
		handleOverlayClick() {
			this.close()
		},
		close() {
			this.$emit('close')
		},
		confirm() {
			if (!this.selectedLongitude) {
				uni.showToast({
					title: '请先选择位置',
					icon: 'none'
				})
				return
			}
			const locationData = {
				latitude: this.selectedLatitude,
				longitude: this.selectedLongitude,
				address: this.address,
				region: this.getRegionFromAddress(this.address)
			}
			this.$emit('select', locationData)
			this.close()
		},
		getRegionFromAddress(address) {
			if (!address) return ''
			const parts = address.split(/[，,]/)
			return parts[0] || address
		},
		onMapTap(e) {
			const lat = e.detail.latitude
			const lng = e.detail.longitude
			this.selectLocation(lat, lng)
		},
		onRegionChange(e) {
			if (e.detail.causedBy === 'drag' || e.detail.causedBy === 'Gesture') {
				const mapCtx = uni.createMapContext('map', this)
				mapCtx.getCenterLocation({
					success: (res) => {
						this.selectLocation(res.latitude, res.longitude)
					}
				})
			}
		},
		selectLocation(lat, lng) {
			this.selectedLatitude = lat
			this.selectedLongitude = lng
			this.loading = true
			this.reverseGeocode(lat, lng)
		},
		reverseGeocode(latitude, longitude) {
			const key = this.getMapKey()
			if (!key || key === 'YOUR_KEY' || key === '') {
				this.address = `${latitude.toFixed(4)}, ${longitude.toFixed(4)}`
				this.loading = false
				return
			}

			uni.request({
				url: 'https://restapi.amap.com/v3/geocode/regeo',
				data: {
					key: key,
					location: `${longitude},${latitude}`,
					extensions: 'all'
				},
				success: (res) => {
					if (res.data && res.data.status === '1' && res.data.regeocode) {
						this.address = res.data.regeocode.formatted_address
					} else {
						this.address = `${latitude.toFixed(4)}, ${longitude.toFixed(4)}`
					}
					this.loading = false
				},
				fail: () => {
					this.address = `${latitude.toFixed(4)}, ${longitude.toFixed(4)}`
					this.loading = false
				}
			})
		},
		getMapKey() {
			const manifest = uni.getStorageSync('__uniappaos_view_ext') || {}
			return manifest.mapKey || ''
		},
		onSearchInput() {
			if (this.searchTimer) {
				clearTimeout(this.searchTimer)
			}
			this.showSearchResults = true
			this.searchTimer = setTimeout(() => {
				this.searchPlaces()
			}, 300)
		},
		onSearchConfirm() {
			this.searchPlaces()
		},
		searchPlaces() {
			if (!this.searchKeyword.trim()) {
				this.searchResults = []
				return
			}

			const key = this.getMapKey()
			if (!key || key === 'YOUR_KEY' || key === '') {
				uni.showToast({
					title: '请配置地图Key',
					icon: 'none'
				})
				return
			}

			uni.request({
				url: 'https://restapi.amap.com/v3/place/text',
				data: {
					key: key,
					keywords: this.searchKeyword,
					city: '当前城市',
					offset: 10,
					page: 1
				},
				success: (res) => {
					if (res.data && res.data.status === '1' && res.data.pois) {
						this.searchResults = res.data.pois.map(poi => ({
							title: poi.name,
							address: poi.address || poi.pname + poi.cityname + poi.adname,
							latitude: parseFloat(poi.location.split(',')[1]),
							longitude: parseFloat(poi.location.split(',')[0])
						}))
					}
				}
			})
		},
		onSearchResultClick(item) {
			this.selectedLatitude = item.latitude
			this.selectedLongitude = item.longitude
			this.address = item.title
			this.showSearchResults = false
			this.centerLatitude = item.latitude
			this.centerLongitude = item.longitude
		},
		getCurrentLocation() {
			uni.getLocation({
				type: 'gcj02',
				success: (res) => {
					this.centerLatitude = res.latitude
					this.centerLongitude = res.longitude
					this.selectedLatitude = res.latitude
					this.selectedLongitude = res.longitude
					this.markers = [{
						id: 1,
						latitude: res.latitude,
						longitude: res.longitude,
						width: 24,
						height: 24
					}]
					this.reverseGeocode(res.latitude, res.longitude)
					this.showSearchResults = false
				},
				fail: () => {
					uni.showToast({
						title: '定位失败，请检查定位权限',
						icon: 'none'
					})
				}
			})
		}
	},
	created() {
		this.getCurrentLocation()
	}
}
</script>

<style scoped>
.map-picker-overlay {
	position: fixed;
	top: 0;
	left: 0;
	right: 0;
	bottom: 0;
	background: rgba(0, 0, 0, 0.5);
	z-index: 9999;
	display: flex;
	flex-direction: column;
	justify-content: flex-end;
}

.map-picker-container {
	height: 90vh;
	background: #FFFFFF;
	border-radius: 40rpx 40rpx 0 0;
	overflow: hidden;
	display: flex;
	flex-direction: column;
}

.picker-header {
	display: flex;
	align-items: center;
	justify-content: space-between;
	padding: 44rpx 32rpx 24rpx;
	background: #FFFFFF;
	border-bottom: 1rpx solid #F1F5F9;
}

.header-left, .header-right {
	width: 80rpx;
}

.close-icon {
	color: #94A3B8;
}

.header-title {
	font-size: 34rpx;
	font-weight: 800;
	color: #1E293B;
}

.header-right {
	text-align: right;
}

.confirm-text {
	font-size: 32rpx;
	font-weight: 700;
	color: #10B981;
}

.search-bar {
	display: flex;
	align-items: center;
	padding: 20rpx 32rpx;
	background: #FFFFFF;
	gap: 16rpx;
}

.search-icon {
	color: #94A3B8;
	margin-right: 8rpx;
}

.search-input {
	flex: 1;
	height: 80rpx;
	background: #F1F5F9;
	border-radius: 20rpx;
	padding: 0 24rpx;
	font-size: 28rpx;
	color: #1E293B;
}

.search-input::placeholder {
	color: #94A3B8;
}

.locate-btn {
	width: 80rpx;
	height: 80rpx;
	background: #F0FDF4;
	border-radius: 20rpx;
	display: flex;
	align-items: center;
	justify-content: center;
	color: #10B981;
}

.map-wrapper {
	flex: 1;
	position: relative;
}

.map {
	width: 100%;
	height: 100%;
}

.center-marker {
	position: absolute;
	top: 50%;
	left: 50%;
	transform: translate(-50%, -100%);
	z-index: 10;
	pointer-events: none;
	display: flex;
	flex-direction: column;
	align-items: center;
}

.marker-ring {
	width: 64rpx;
	height: 64rpx;
	border: 4rpx solid #10B981;
	border-radius: 50%;
	background: rgba(16, 185, 129, 0.1);
	animation: pulse 1.5s ease-in-out infinite;
}

.marker-center {
	width: 24rpx;
	height: 24rpx;
	background: #10B981;
	border-radius: 50%;
	margin-top: -44rpx;
}

@keyframes pulse {
	0%, 100% {
		transform: scale(1);
		opacity: 1;
	}
	50% {
		transform: scale(1.2);
		opacity: 0.7;
	}
}

.location-panel {
	background: #FFFFFF;
	border-radius: 32rpx 32rpx 0 0;
	box-shadow: 0 -8rpx 30rpx rgba(0, 0, 0, 0.08);
	padding: 24rpx 32rpx calc(24rpx + env(safe-area-inset-bottom));
	min-height: 160rpx;
}

.location-loading {
	display: flex;
	align-items: center;
	justify-content: center;
	gap: 16rpx;
	padding: 20rpx 0;
}

.loading-spinner {
	width: 32rpx;
	height: 32rpx;
	border: 4rpx solid #E2E8F0;
	border-top-color: #10B981;
	border-radius: 50%;
	animation: spin 0.8s linear infinite;
}

@keyframes spin {
	to {
		transform: rotate(360deg);
	}
}

.loading-text {
	font-size: 28rpx;
	color: #64748B;
}

.location-result {
	display: flex;
	align-items: flex-start;
	gap: 20rpx;
}

.location-icon-wrapper {
	width: 64rpx;
	height: 64rpx;
	background: #ECFDF5;
	border-radius: 16rpx;
	display: flex;
	align-items: center;
	justify-content: center;
}

.loc-icon {
	color: #10B981;
}

.location-content {
	flex: 1;
}

.location-address {
	display: block;
	font-size: 30rpx;
	font-weight: 600;
	color: #1E293B;
	line-height: 1.4;
}

.location-coords {
	display: block;
	font-size: 22rpx;
	color: #94A3B8;
	margin-top: 8rpx;
}

.search-results {
	margin-top: 20rpx;
	max-height: 300rpx;
	overflow-y: auto;
}

.search-item {
	display: flex;
	align-items: flex-start;
	gap: 16rpx;
	padding: 20rpx 0;
	border-bottom: 1rpx solid #F1F5F9;
}

.search-item:last-child {
	border-bottom: none;
}

.result-icon {
	color: #94A3B8;
	margin-top: 4rpx;
}

.result-content {
	flex: 1;
}

.result-title {
	display: block;
	font-size: 28rpx;
	font-weight: 600;
	color: #1E293B;
	margin-bottom: 4rpx;
}

.result-address {
	display: block;
	font-size: 24rpx;
	color: #64748B;
}
</style>
