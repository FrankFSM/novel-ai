import request from '../request'

export default {
  // 获取关系网络图
  getRelationshipGraph(data) {
    return request({
      url: '/analysis/relationship-graph',
      method: 'post',
      data
    })
  },
  
  // 获取时间线
  getTimeline(data) {
    return request({
      url: '/analysis/timeline',
      method: 'post',
      data
    })
  },
  
  // 获取角色旅程
  getCharacterJourney(novelId, characterId) {
    return request({
      url: `/analysis/character-journey/${novelId}/${characterId}`,
      method: 'get'
    })
  },
  
  // 获取物品传承历史
  getItemLineage(novelId, itemId) {
    return request({
      url: `/analysis/item-lineage/${novelId}/${itemId}`,
      method: 'get'
    })
  },
  
  // 获取地点相关事件
  getLocationEvents(novelId, locationId) {
    return request({
      url: `/analysis/location-events/${novelId}/${locationId}`,
      method: 'get'
    })
  }
} 