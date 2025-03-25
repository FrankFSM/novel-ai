import request from '../request'

export default {
  // 分析小说中的角色
  analyzeCharacters(novelId, forceRefresh = false) {
    return request({
      url: `/character-analysis/novels/${novelId}/characters/analyze`,
      method: 'get',
      params: { force_refresh: forceRefresh }
    }).then(response => response.data)
  },
  
  // 获取角色详细信息
  getCharacterDetails(characterId) {
    return request({
      url: `/character-analysis/characters/${characterId}/details`,
      method: 'get'
    }).then(response => response.data)
  },
  
  // 获取角色性格分析
  getCharacterPersonality(characterId) {
    return request({
      url: `/character-analysis/characters/${characterId}/personality`,
      method: 'get'
    }).then(response => response.data)
  }
} 