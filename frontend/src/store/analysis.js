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
  
  // 获取关系图
  async function fetchRelationshipGraph(novelId, characterId = null, depth = 1) {
    loading.value = true
    error.value = null
    
    try {
      const response = await analysisApi.getRelationshipGraph({
        novel_id: novelId,
        character_id: characterId,
        depth
      })
      
      relationshipGraph.value = response.data
      return response.data
    } catch (err) {
      error.value = err.message || '获取关系图失败'
      throw err
    } finally {
      loading.value = false
    }
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
    reset
  }
}) 