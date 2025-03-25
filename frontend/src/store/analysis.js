import { defineStore } from 'pinia'
import { ref } from 'vue'
import { analysisApi } from '@/api'

export const useAnalysisStore = defineStore('analysis', () => {
  // 状态
  const relationshipGraph = ref(null)
  const timeline = ref(null)
  const characterJourney = ref(null)
  const itemLineage = ref(null)
  const locationEvents = ref(null)
  const loading = ref(false)
  const error = ref(null)
  
  // 缓存状态
  const analysisCache = ref({
    relationship: {}, // 格式: {novelId_characterId_depth: data}
  })
  
  // 获取关系图
  async function fetchRelationshipGraph(novelId, characterId = null, depth = 1, forceRefresh = false) {
    loading.value = true
    error.value = null
    
    console.log(`[DEBUG] fetchRelationshipGraph 调用参数:`, { novelId, characterId, depth, forceRefresh })
    
    const cacheKey = `${novelId}_${characterId || 'null'}_${depth}`
    
    // 如果缓存中有数据且不是强制刷新，则使用缓存数据
    if (!forceRefresh && analysisCache.value.relationship[cacheKey]) {
      console.log(`[DEBUG] 使用缓存数据 (cacheKey=${cacheKey})`)
      relationshipGraph.value = analysisCache.value.relationship[cacheKey]
      loading.value = false
      return relationshipGraph.value
    }
    
    try {
      // 在获取新数据时，保留旧数据直到新数据返回
      const oldGraph = relationshipGraph.value
      
      console.log(`[DEBUG] 发送API请求 (forceRefresh=${forceRefresh})`)
      const response = await analysisApi.getRelationshipGraph({
        novel_id: novelId,
        character_id: characterId,
        depth,
        force_refresh: forceRefresh
      })
      
      console.log(`[DEBUG] 收到API响应:`, response.data ? '数据有效' : '数据无效')
      relationshipGraph.value = response.data
      
      // 将数据添加到缓存
      analysisCache.value.relationship[cacheKey] = response.data
      
      return response.data
    } catch (err) {
      console.error(`[DEBUG] API请求失败:`, err)
      error.value = err.message || '获取关系图失败'
      throw err
    } finally {
      loading.value = false
    }
  }
  
  // 检查关系图是否已缓存
  function hasRelationshipCache(novelId, characterId = null, depth = 1) {
    const cacheKey = `${novelId}_${characterId || 'null'}_${depth}`
    return !!analysisCache.value.relationship[cacheKey]
  }
  
  // 获取时间线
  async function fetchTimeline(novelId, characterId = null, startChapter = null, endChapter = null) {
    loading.value = true
    error.value = null
    
    try {
      const response = await analysisApi.getTimeline({
        novel_id: novelId,
        character_id: characterId,
        start_chapter: startChapter,
        end_chapter: endChapter
      })
      
      timeline.value = response.data
      return response.data
    } catch (err) {
      error.value = err.message || '获取时间线失败'
      throw err
    } finally {
      loading.value = false
    }
  }
  
  // 获取角色旅程
  async function fetchCharacterJourney(novelId, characterId) {
    loading.value = true
    error.value = null
    
    try {
      const response = await analysisApi.getCharacterJourney(novelId, characterId)
      
      characterJourney.value = response.data
      return response.data
    } catch (err) {
      error.value = err.message || '获取角色旅程失败'
      throw err
    } finally {
      loading.value = false
    }
  }
  
  // 获取物品传承
  async function fetchItemLineage(novelId, itemId) {
    loading.value = true
    error.value = null
    
    try {
      const response = await analysisApi.getItemLineage(novelId, itemId)
      
      itemLineage.value = response.data
      return response.data
    } catch (err) {
      error.value = err.message || '获取物品传承失败'
      throw err
    } finally {
      loading.value = false
    }
  }
  
  // 获取地点事件
  async function fetchLocationEvents(novelId, locationId) {
    loading.value = true
    error.value = null
    
    try {
      const response = await analysisApi.getLocationEvents(novelId, locationId)
      
      locationEvents.value = response.data
      return response.data
    } catch (err) {
      error.value = err.message || '获取地点事件失败'
      throw err
    } finally {
      loading.value = false
    }
  }
  
  // 重置数据
  function reset() {
    relationshipGraph.value = null
    timeline.value = null
    characterJourney.value = null
    itemLineage.value = null
    locationEvents.value = null
    error.value = null
  }
  
  return {
    relationshipGraph,
    timeline,
    characterJourney,
    itemLineage,
    locationEvents,
    loading,
    error,
    fetchRelationshipGraph,
    fetchTimeline,
    fetchCharacterJourney,
    fetchItemLineage,
    fetchLocationEvents,
    hasRelationshipCache,
    reset
  }
}) 