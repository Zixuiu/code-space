import CONFIG from './config'

class MapService {
  constructor() {
    this.mapContext = null
    this.markers = []
  }

  async getLocation(type = 'gcj02') {
    return new Promise((resolve, reject) => {
      uni.getLocation({
        type,
        success: (res) => {
          resolve({
            latitude: res.latitude,
            longitude: res.longitude,
            address: res.address || '',
            name: res.name || ''
          })
        },
        fail: (err) => {
          console.error('MapService: getLocation failed', err)
          uni.showToast({ title: '获取位置失败', icon: 'none' })
          reject(err)
        }
      })
    })
  }

  async chooseLocation() {
    return new Promise((resolve, reject) => {
      uni.chooseLocation({
        success: (res) => {
          resolve({
            latitude: res.latitude,
            longitude: res.longitude,
            address: res.address,
            name: res.name
          })
        },
        fail: (err) => {
          if (err.errMsg && err.errMsg.includes('auth deny')) {
            uni.showModal({
              title: '提示',
              content: '需要您授权位置权限',
              confirmText: '去设置',
              success: (res) => {
                if (res.confirm) {
                  uni.openSetting()
                }
              }
            })
          }
          reject(err)
        }
      })
    })
  }

  async openLocation(latitude, longitude, name = '', address = '') {
    return new Promise((resolve, reject) => {
      uni.openLocation({
        latitude,
        longitude,
        name: name || '位置',
        address: address || '',
        fail: (err) => {
          console.error('MapService: openLocation failed', err)
          uni.showToast({ title: '打开地图失败', icon: 'none' })
          reject(err)
        }
      })
    })
  }

  calculateDistance(lat1, lon1, lat2, lon2) {
    const R = 6371
    const dLat = this.deg2rad(lat2 - lat1)
    const dLon = this.deg2rad(lon2 - lon1)
    const a =
      Math.sin(dLat / 2) * Math.sin(dLat / 2) +
      Math.cos(this.deg2rad(lat1)) * Math.cos(this.deg2rad(lat2)) *
      Math.sin(dLon / 2) * Math.sin(dLon / 2)
    const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a))
    const d = R * c
    return d
  }

  deg2rad(deg) {
    return deg * (Math.PI / 180)
  }

  formatDistance(distance) {
    if (distance < 1) {
      return `${Math.round(distance * 1000)}m`
    } else if (distance < 10) {
      return `${distance.toFixed(1)}km`
    } else {
      return `${Math.round(distance)}km`
    }
  }

  initMap(mapId) {
    if (this.mapContext) return this.mapContext
    this.mapContext = uni.createMapContext(mapId)
    return this.mapContext
  }

  moveToLocation(latitude, longitude, mapId = 'mainMap') {
    const mapContext = this.initMap(mapId)
    mapContext.moveToLocation({
      latitude,
      longitude,
      success: (res) => {
        console.log('MapService: moveToLocation success')
      }
    })
  }

  createMarker(latitude, longitude, iconPath, width = 30, height = 30) {
    return {
      latitude,
      longitude,
      iconPath,
      width,
      height,
      callout: {
        display: 'ALWAYS',
        padding: 10,
        borderRadius: 10
      }
    }
  }

  async getAddressFromCoords(latitude, longitude) {
    return new Promise((resolve, reject) => {
      uni.request({
        url: 'https://apis.map.qq.com/ws/geocoder/v1/',
        data: {
          location: `${latitude},${longitude}`,
          key: CONFIG.TENCENT_MAP_KEY || '',
          get_poi: 1
        },
        success: (res) => {
          if (res.data.status === 0) {
            resolve({
              address: res.data.result.address,
              name: res.data.result.formatted_addresses?.recommend || '',
              city: res.data.result.ad_info?.city || ''
            })
          } else {
            reject(res.data)
          }
        },
        fail: reject
      })
    })
  }

  async searchNearby(keyword, latitude, longitude, radius = 3000) {
    return new Promise((resolve, reject) => {
      uni.request({
        url: 'https://apis.map.qq.com/ws/geocoder/v1/',
        data: {
          keyword,
          boundary: `nearby(${latitude},${longitude},${radius})`,
          key: CONFIG.TENCENT_MAP_KEY || ''
        },
        success: (res) => {
          if (res.data.status === 0) {
            resolve(res.data.data || [])
          } else {
            reject(res.data)
          }
        },
        fail: reject
      })
    })
  }
}

const mapService = new MapService()

export default mapService
