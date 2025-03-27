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
  
  // 获取小说的所有角色（无需重新分析）
  getNovelCharacters(novelId) {
    return request({
      url: `/character-analysis/novels/${novelId}/characters`,
      method: 'get'
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
  },
  
  // 按章节范围分析角色（新增）
  analyzeCharactersByChapter(novelId, startChapter, endChapter) {
    return request({
      url: `/character-analysis/novels/${novelId}/characters/analyze-by-chapter`,
      method: 'get',
      params: { 
        start_chapter: startChapter,
        end_chapter: endChapter
      }
    }).then(response => response.data)
  }
} 