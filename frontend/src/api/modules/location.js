import request from '../request'

export default {
  // 分析小说中的地点
  analyzeLocations(novelId, forceRefresh = false) {
    return request({
      url: `/location-analysis/novels/${novelId}/locations/analyze`,
      method: 'get',
      params: { force_refresh: forceRefresh }
    }).then(response => response.data)
  },
  
  // 获取小说的所有地点
  getNovelLocations(novelId) {
    return request({
      url: `/location-analysis/novels/${novelId}/locations`,
      method: 'get'
    }).then(response => response.data)
  },
  
  // 获取地点详细信息
  getLocationDetails(locationId) {
    return request({
      url: `/location-analysis/locations/${locationId}/details`,
      method: 'get'
    }).then(response => response.data)
  },
  
  // 获取地点重要性分析
  getLocationSignificance(locationId) {
    return request({
      url: `/location-analysis/locations/${locationId}/significance`,
      method: 'get'
    }).then(response => response.data)
  },
  
  // 获取地点的时间线
  getLocationTimeline(locationId, novelId, startChapter = null, endChapter = null) {
    return request({
      url: `/location-analysis/locations/${locationId}/timeline`,
      method: 'get',
      params: {
        novel_id: novelId,
        start_chapter: startChapter,
        end_chapter: endChapter
      }
    }).then(response => response.data)
  },
  
  // 全局分析小说中所有地点的相关事件
  analyzeAllLocationEvents(novelId, forceRefresh = false) {
    return request({
      url: `/location-analysis/novels/${novelId}/locations/events/analyze`,
      method: 'post',
      params: {
        force_refresh: forceRefresh
      }
    }).then(response => response.data)
  }
} 