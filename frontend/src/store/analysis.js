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
    loading.value = true;
    error.value = null;
    
    // 添加日志便于调试
    console.log(`[角色旅程] 开始获取, 小说ID: ${novelId}, 角色ID: ${characterId}`);
    
    try {
      const response = await analysisApi.getCharacterJourney(novelId, characterId);
      
      console.log("[角色旅程] API响应:", response.status, response.data ? "有数据" : "无数据");
      
      // 检查是否接收到有效数据并进行适当的处理
      if (response.data && typeof response.data === 'object') {
        // 确保数据有合适的结构以防止渲染错误
        const data = response.data;
        console.log("[角色旅程] 数据结构:", Object.keys(data).join(", "));
        
        // 为可能为null的对象提供默认值，防止渲染错误
        if (!data.character) {
          console.log("[角色旅程] 缺少character字段，创建默认值");
          data.character = { name: '', description: '', alias: [] };
        }
        
        if (!data.journey) {
          console.log("[角色旅程] 缺少journey字段，创建默认值");
          data.journey = {};
        }
        
        if (!data.stats) {
          console.log("[角色旅程] 缺少stats字段，创建默认值");
          data.stats = { chapters_count: 0, events_count: 0, relationships_count: 0 };
        }
        
        if (!data.stages) {
          console.log("[角色旅程] 缺少stages字段，创建默认值");
          data.stages = [];
        }
        
        if (!data.key_events) {
          console.log("[角色旅程] 缺少key_events字段，创建默认值");
          data.key_events = [];
        }
        
        if (!data.emotions) {
          console.log("[角色旅程] 缺少emotions字段，创建默认值");
          data.emotions = [];
        }
        
        if (!data.relationships) {
          console.log("[角色旅程] 缺少relationships字段，创建默认值");
          data.relationships = [];
        }
        
        console.log("[角色旅程] 处理后的数据:", { 
          character: data.character ? '已设置' : '缺失',
          stats: data.stats ? '已设置' : '缺失',
          stages: data.stages ? `${data.stages.length}项` : '缺失',
          events: data.key_events ? `${data.key_events.length}项` : '缺失',
          emotions: data.emotions ? `${data.emotions.length}项` : '缺失',
          relationships: data.relationships ? `${data.relationships.length}项` : '缺失'
        });
        
        characterJourney.value = data;
      } else {
        console.error('[角色旅程] 获取角色旅程返回的数据格式不正确:', response.data);
        error.value = '数据格式不正确';
        characterJourney.value = null;
      }
      
      return characterJourney.value;
    } catch (err) {
      console.error('[角色旅程] 获取角色旅程失败:', err);
      error.value = err.message || '获取角色旅程失败';
      characterJourney.value = null;
      throw err;
    } finally {
      loading.value = false;
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