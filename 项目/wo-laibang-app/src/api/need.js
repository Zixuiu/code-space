import { post, get, put, del } from '@/utils/request'

export const needApi = {
  publishNeed(needInfo) {
    return post('/api/need/publish', needInfo)
  },

  getNeedList(params) {
    return get('/api/need/list', params)
  },

  getNeedDetail(needId) {
    return get(`/api/need/detail/${needId}`)
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

  getMyNeeds() {
    return get('/api/need/my')
  },

  getAcceptedNeeds() {
    return get('/api/need/accepted')
  },

  completeNeed(needId) {
    return put(`/api/need/complete/${needId}`)
  }
}
