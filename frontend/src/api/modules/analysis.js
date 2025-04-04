import request from '../request'

export default {
  // 获取关系网络图
  getRelationshipGraph(data) {
    // 确保data中包含force_refresh字段，并且强制为布尔值
    const forceRefresh = !!data.force_refresh; // 确保是布尔值
    
    const requestData = {
      ...data,
      force_refresh: forceRefresh,
      // 添加时间戳确保请求不被缓存
      _t: forceRefresh ? new Date().getTime() : undefined
    }
    
    console.log('[DEBUG API] getRelationshipGraph requestData:', JSON.stringify(requestData));
    
    return request({
      url: '/analysis/relationship-graph',
      method: 'post',
      data: requestData,
      // 强制要求不缓存
      headers: forceRefresh ? {
        'Cache-Control': 'no-cache, no-store, must-revalidate',
        'Pragma': 'no-cache',
        'Expires': '0'
      } : {}
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
    console.log(`[API] 请求角色旅程数据: 小说ID=${novelId}, 角色ID=${characterId}`);
    
    return request({
      url: `/analysis/character-journey/${novelId}/${characterId}`,
      method: 'get',
      // 添加错误处理配置
      validateStatus: function (status) {
        return status >= 200 && status < 500; // 只要不是500错误都返回
      },
      // 添加超时设置，因为角色旅程生成可能需要时间
      timeout: 30000 // 30秒
    }).catch(err => {
      console.error(`[API] 角色旅程请求失败:`, err);
      // 将错误重新抛出，以便在store中处理
      throw err;
    });
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