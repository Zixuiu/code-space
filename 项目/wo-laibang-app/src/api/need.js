import { post, get, put, del } from '@/utils/request'

const DEFAULT_CACHE_TTL = 60 * 1000

export const needApi = {
  publishNeed(needInfo) {
    return post('/api/need/publish', needInfo)
  },

  getNeedList(params, options = {}) {
    return get('/api/need/list', params, options)
  },

  getNeedDetail(needId, options = {}) {
    return get(`/api/need/detail/${needId}`, null, {
      cache: DEFAULT_CACHE_TTL,
      ...options
    })
  },

  updateNeed(needId, needInfo) {
    return put(`/api/need/update/${needId}`, needInfo)
  },

  cancelNeed(needId) {
    return put(`/api/need/cancel/${needId}`)
  },

  deleteNeed(needId) {
    return del(`/api/need/delete/${needId}`)
  },

  acceptNeed(needId) {
    return post(`/api/need/accept/${needId}`)
  },

  getMyNeeds(options = {}) {
    return get('/api/need/my', null, options)
  },

  getAcceptedNeeds(options = {}) {
    return get('/api/need/accepted', null, options)
  },

  completeNeed(needId) {
    return put(`/api/need/complete/${needId}`)
  }
}
