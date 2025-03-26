import request from '../request'

export default {
  // 获取小说中的所有事件
  getNovelEvents(novelId, forceRefresh = false) {
    return request({
      url: `/event-analysis/novels/${novelId}/events`,
      method: 'get',
      params: { force_refresh: forceRefresh }
    }).then(response => response.data)
  },
  
  // 获取事件详细信息
  getEventDetails(eventId) {
    return request({
      url: `/event-analysis/events/${eventId}/details`,
      method: 'get'
    }).then(response => response.data)
  },
  
  // 获取事件重要性分析
  getEventSignificance(eventId) {
    return request({
      url: `/event-analysis/events/${eventId}/significance`,
      method: 'get'
    }).then(response => response.data)
  },
  
  // 筛选事件
  filterEvents(novelId, options = {}) {
    const { characterId, locationId, minImportance } = options
    return request({
      url: `/event-analysis/events/filter`,
      method: 'get',
      params: {
        novel_id: novelId,
        character_id: characterId || undefined,
        location_id: locationId || undefined,
        min_importance: minImportance || undefined
      }
    }).then(response => response.data)
  }
} 