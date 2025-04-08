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
  
  // 获取特定章节的已有地点数据(不会触发分析)
  getChapterLocations(novelId, chapterId) {
    return request({
      url: `/location-analysis/novels/${novelId}/chapters/${chapterId}/locations`,
      method: 'get'
    }).then(response => response.data)
      .catch(error => {
        console.error(`获取章节${chapterId}地点数据失败:`, error)
        // 如果没有数据，返回空数组
        return []
      })
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
  },
  
  // 按章节范围分析地点（新增）
  analyzeLocationsByChapter(novelId, startChapter, endChapter) {
    // 如果startChapter和endChapter相同，则表示只分析单个章节
    if (startChapter === endChapter) {
      return request({
        url: `/location-analysis/novels/${novelId}/chapters/${startChapter}/analyze`,
        method: 'get'
      }).then(response => response.data)
    } else {
      return request({
        url: `/location-analysis/novels/${novelId}/locations/analyze-by-chapter`,
        method: 'get',
        params: { 
          start_chapter: startChapter,
          end_chapter: endChapter
        }
      }).then(response => response.data)
    }
  }
} 