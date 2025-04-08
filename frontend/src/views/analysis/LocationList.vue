<template>
  <div class="location-list-container">
    <el-card shadow="never">
      <template #header>
        <div class="page-header">
          <div class="header-left">
            <h2>地点分析</h2>
          </div>
          <div class="header-right">
            <el-select 
              v-model="selectedNovel" 
              placeholder="请选择小说" 
              @change="handleNovelChange"
              :loading="novelStore.loading"
              class="full-width-select"
            >
              <el-option
                v-for="novel in novelStore.novels"
                :key="novel.id"
                :label="novel.title"
                :value="novel.id"
              />
            </el-select>
            
            <el-select 
              v-model="selectedChapter" 
              placeholder="选择章节" 
              @change="handleChapterChange"
              :disabled="!selectedNovel || !hasChapters"
              clearable
              class="chapter-select"
            >
              <el-option
                v-for="chapter in chapters"
                :key="chapter.id"
                :label="chapter.title || `第${chapter.number}章`"
                :value="chapter.id"
              />
            </el-select>
            
            <el-button 
              type="success" 
              @click="analyzeSpecificChapter(selectedChapter)" 
              :disabled="!selectedNovel || !selectedChapter"
              :loading="loading"
              class="analyze-button"
            >
              <el-icon><Position /></el-icon>
              分析当前章节
            </el-button>
            
            <el-button 
              type="primary" 
              @click="analyzeLocations" 
              :disabled="!selectedNovel"
              :loading="loading"
              class="analyze-button"
            >
              <el-icon><Search /></el-icon>
              分析全书地点
            </el-button>
            
            <el-button 
              type="success" 
              @click="analyzeAllEvents" 
              :disabled="!selectedNovel || locations.length === 0"
              :loading="eventAnalysisLoading" 
              class="analyze-button"
            >
              <el-icon><DataAnalysis /></el-icon>
              分析所有地点事件
            </el-button>
          </div>
        </div>
      </template>
      
      <!-- 未选择小说的提示 -->
      <el-empty 
        v-if="!selectedNovel" 
        description="请从上方选择小说"
      >
        <el-button type="primary" @click="navigateToNovelList">浏览小说列表</el-button>
      </el-empty>
      
      <!-- 选择了小说但还未分析的提示 -->
      <el-empty 
        v-else-if="locations.length === 0 && !loading" 
        description="请选择分析方式"
      >
        <template #description>
          <p>您可以:</p>
          <p>1. 选择章节后点击"分析当前章节"按钮分析特定章节</p>
          <p>2. 直接点击"分析全书地点"按钮分析整本小说的地点</p>
        </template>
        <div style="margin-top: 20px; display: flex; gap: 10px; justify-content: center;">
          <el-button type="success" :disabled="!selectedChapter" @click="analyzeSpecificChapter(selectedChapter)">
            分析当前章节
          </el-button>
          <el-button type="primary" @click="analyzeLocations">
            分析全书地点
          </el-button>
        </div>
      </el-empty>
      
      <!-- 加载中状态 -->
      <div v-else-if="loading" class="loading-container">
        <el-skeleton :rows="5" animated />
        <div class="loading-text">正在分析小说地点...</div>
      </div>
      
      <!-- 地点列表 -->
      <div v-else class="location-list">
        <!-- 章节筛选信息 -->
        <div class="chapter-filter-info" v-if="selectedChapter">
          <el-alert
            title="章节筛选已启用"
            type="info"
            :closable="false"
            show-icon
          >
            <template #default>
              <span>
                当前显示【{{ getChapterTitle(selectedChapter) }}】中的地点
                <el-button type="text" @click="selectedChapter = null">清除筛选</el-button>
              </span>
            </template>
          </el-alert>
        </div>

        <div v-if="filteredLocations.length === 0" class="no-locations-in-chapter">
          <el-empty :description="selectedChapter ? `在【${getChapterTitle(selectedChapter)}】中未发现地点` : '未找到地点信息'">
            <template #description>
              <p v-if="selectedChapter">在【{{ getChapterTitle(selectedChapter) }}】中未发现地点</p>
              <p v-else>未找到地点信息</p>
              <p v-if="selectedChapter">
                <el-button type="primary" size="small" @click="analyzeSpecificChapter(selectedChapter)">
                  分析当前章节地点
                </el-button>
                <el-button type="info" size="small" @click="selectedChapter = null">
                  查看所有地点
                </el-button>
              </p>
            </template>
          </el-empty>
        </div>

        <el-row :gutter="20" v-else>
          <el-col 
            v-for="location in filteredLocations" 
            :key="location.id"
            :xs="24" 
            :sm="12" 
            :md="8" 
            :lg="6"
            class="location-col"
          >
            <el-card 
              class="location-card" 
              :body-style="{ padding: '10px' }"
              shadow="hover"
            >
              <div class="location-icon">
                <el-avatar 
                  :size="80" 
                  :src="getLocationIcon(location.id)"
                />
              </div>
              
              <div class="location-info">
                <h3 class="location-name">
                  {{ location.name }}
                  <el-tag 
                    v-if="location.events_count >= 5" 
                    type="danger" 
                    size="small"
                  >
                    重要
                  </el-tag>
                  <el-tag 
                    v-else-if="location.events_count >= 3" 
                    type="warning" 
                    size="small"
                  >
                    主要
                  </el-tag>
                </h3>
                
                <div class="location-description">
                  {{ truncateText(location.description, 60) || '暂无描述' }}
                </div>
                
                <div class="location-events" v-if="location.events_count">
                  <div class="events-label">相关事件：</div>
                  <div class="event-count">
                    <el-badge 
                      :value="location.events_count" 
                      type="primary"
                    >
                      <el-tag type="info" size="small">事件数量</el-tag>
                    </el-badge>
                  </div>
                </div>
                
                <div class="location-actions">
                  <el-button 
                    type="primary" 
                    size="small" 
                    @click="viewLocationDetails(location.id)"
                  >
                    详细信息
                  </el-button>
                  
                  <el-button 
                    type="success" 
                    size="small" 
                    @click="viewLocationEvents(location.id)"
                  >
                    相关事件
                  </el-button>
                </div>
              </div>
            </el-card>
          </el-col>
        </el-row>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useNovelStore } from '@/store/novel'
import { ElMessage } from 'element-plus'
import { locationApi, novelApi } from '@/api'
import { Search, DataAnalysis, Position } from '@element-plus/icons-vue'

const router = useRouter()
const route = useRoute()
const novelStore = useNovelStore()

// 本地状态
const selectedNovel = ref(null)
const locations = ref([])
const loading = ref(false)
const eventAnalysisLoading = ref(false)
const selectedChapter = ref(null)
const chapters = ref([])
const hasChapters = ref(true)

// 计算属性：根据章节筛选地点
const filteredLocations = computed(() => {
  if (!locations.value.length) return []
  
  // 如果未选择章节，显示所有地点
  if (!selectedChapter.value) return locations.value
  
  // 当通过analyzeSpecificChapter分析特定章节时，API返回的结果已经是该章节的地点
  // 此时直接返回locations即可，因为API已经做了筛选
  return locations.value
})

// 处理生命周期
onMounted(async () => {
  // 加载小说列表
  if (novelStore.novels.length === 0) {
    await novelStore.fetchNovels()
  }
  
  // 从URL参数获取小说ID和章节ID
  const novelId = Number(route.query.novelId)
  const chapterId = Number(route.query.chapterId) || null
  
  if (novelId && !isNaN(novelId)) {
    selectedNovel.value = novelId
    
    // 先加载章节列表
    await loadNovelChapters(novelId)
    
    // 如果提供了章节ID，设置选中章节并尝试从数据库获取数据
    if (chapterId && !isNaN(chapterId)) {
      selectedChapter.value = chapterId
      
      // 尝试从数据库获取现有数据
      loading.value = true
      
      try {
        const data = await locationApi.getChapterLocations(novelId, chapterId)
        
        if (data && Array.isArray(data) && data.length > 0) {
          // 数据库中有数据，直接显示
          locations.value = [...data].sort((a, b) => 
            (b.events_count || 0) - (a.events_count || 0)
          )
          ElMessage.success(`已加载【${getChapterTitle(chapterId)}】章节的${data.length}个地点`)
        } else {
          // 数据库中无数据，提示用户分析
          ElMessage.info('该章节未找到地点数据，请点击"分析当前章节"按钮进行分析')
        }
      } catch (error) {
        console.error('获取章节地点数据失败:', error)
        ElMessage.warning('无法获取该章节地点数据，您可以点击"分析当前章节"按钮重新分析')
      } finally {
        loading.value = false
      }
    } else {
      // 显示提示信息
      ElMessage.info('请选择章节并点击"分析当前章节"按钮，或点击"分析全书地点"按钮分析所有地点')
    }
  }
})

// 加载地点列表
async function loadLocations(novelId, forceRefresh = false) {
  if (!novelId) return
  
  try {
    locations.value = []
    loading.value = true
    
    // 调用API获取地点列表
    const data = await locationApi.analyzeLocations(novelId, forceRefresh)
    console.log('地点分析API响应:', data)
    
    if (data && Array.isArray(data)) {
      // 以重要性排序
      locations.value = [...data].sort((a, b) => 
        (b.events_count || 0) - (a.events_count || 0)
      )
      if (!forceRefresh) {
        ElMessage.success(`成功加载${data.length}个地点`)
      } else {
        ElMessage.success(`地点分析完成，共发现${data.length}个地点`)
      }
    } else {
      ElMessage.warning('获取到的地点列表为空')
      locations.value = []
    }
  } catch (err) {
    console.error('获取地点列表失败:', err)
    ElMessage.error('获取地点列表失败: ' + (err.message || '未知错误'))
    locations.value = []
  } finally {
    loading.value = false
  }
}

// 小说选择变化处理
async function handleNovelChange(novelId) {
  if (!novelId) return
  
  try {
    selectedChapter.value = null // 清空章节选择
    locations.value = [] // 清空地点列表
    await loadNovelChapters(novelId) // 加载章节列表
    
    // 不再自动分析地点，只更新URL参数
    router.replace({
      query: { ...route.query, novelId, chapterId: null }
    })
    
    // 显示提示信息
    ElMessage.info('请选择章节并点击"分析当前章节"按钮，或点击"分析全书地点"按钮分析所有地点')
  } catch (err) {
    console.error('处理小说选择变化失败:', err)
    ElMessage.error('加载小说信息失败: ' + (err.message || '未知错误'))
  }
}

// 章节选择变化处理
async function handleChapterChange(chapterId) {
  if (!selectedNovel.value) return
  
  selectedChapter.value = chapterId
  
  // 更新URL参数，保留原有参数
  router.replace({
    query: { ...route.query, chapterId }
  })
  
  if (chapterId) {
    // 先尝试从数据库获取现有数据
    loading.value = true
    locations.value = []
    
    try {
      const data = await locationApi.getChapterLocations(selectedNovel.value, chapterId)
      
      if (data && Array.isArray(data) && data.length > 0) {
        // 数据库中有数据，直接显示
        locations.value = [...data].sort((a, b) => 
          (b.events_count || 0) - (a.events_count || 0)
        )
        ElMessage.success(`已加载【${getChapterTitle(chapterId)}】章节的${data.length}个地点`)
      } else {
        // 数据库中无数据，提示用户分析
        ElMessage.info('该章节未找到地点数据，请点击"分析当前章节"按钮进行分析')
      }
    } catch (error) {
      console.error('获取章节地点数据失败:', error)
      ElMessage.warning('无法获取该章节地点数据，您可以点击"分析当前章节"按钮重新分析')
    } finally {
      loading.value = false
    }
  } else {
    // 如果清除了章节选择，清空地点列表
    locations.value = []
    ElMessage.info('请选择章节或点击"分析全书地点"按钮')
  }
}

// 获取小说章节列表
async function loadNovelChapters(novelId) {
  try {
    loading.value = true
    const response = await novelApi.getNovelChapters(novelId)
    console.log('获取章节列表响应:', response)
    
    if (response && response.data) {
      chapters.value = response.data || []
      hasChapters.value = chapters.value.length > 0
    } else {
      chapters.value = []
      hasChapters.value = false
    }
  } catch (error) {
    console.error('获取章节列表失败:', error)
    chapters.value = []
    hasChapters.value = false
    throw error
  } finally {
    loading.value = false
  }
}

// 手动分析地点按钮处理
async function analyzeLocations() {
  if (!selectedNovel.value) return
  
  try {
    // 清空章节选择
    selectedChapter.value = null
    
    // 更新URL参数
    router.replace({
      query: { ...route.query, chapterId: null }
    })
    
    // 调用API分析全书地点
    await loadLocations(selectedNovel.value, true) // 强制刷新
    
    ElMessage.success('分析全书地点成功，您可以选择特定章节查看该章节的地点')
  } catch (error) {
    ElMessage.error('分析地点失败: ' + (error.message || '未知错误'))
  }
}

// 分析所有地点事件
async function analyzeAllEvents() {
  if (!selectedNovel.value || locations.value.length === 0) return
  
  try {
    eventAnalysisLoading.value = true
    await locationApi.analyzeAllLocationEvents(selectedNovel.value)
    await loadLocations(selectedNovel.value, true) // 强制刷新
    ElMessage.success('成功分析所有地点事件')
  } catch (error) {
    console.error('分析所有地点事件失败:', error)
    ElMessage.error('分析所有地点事件失败: ' + (error.message || '未知错误'))
  } finally {
    eventAnalysisLoading.value = false
  }
}

// 分析特定章节
async function analyzeSpecificChapter(chapterId) {
  if (!selectedNovel.value || !chapterId) return
  
  try {
    locations.value = []
    loading.value = true
    
    // 调用API分析特定章节的地点
    const data = await locationApi.analyzeLocationsByChapter(
      selectedNovel.value,
      chapterId,
      chapterId
    )
    
    console.log('章节地点分析API响应:', data)
    
    if (data && Array.isArray(data)) {
      // 以重要性排序
      locations.value = [...data].sort((a, b) => 
        (b.events_count || 0) - (a.events_count || 0)
      )
      ElMessage.success(`章节地点分析完成，共发现${data.length}个地点`)
    } else {
      ElMessage.warning('获取到的地点列表为空')
      locations.value = []
    }
  } catch (error) {
    console.error('章节地点分析失败:', error)
    ElMessage.error('章节地点分析失败: ' + (error.message || '未知错误'))
    locations.value = []
  } finally {
    loading.value = false
  }
}

// 导航到小说列表
function navigateToNovelList() {
  router.push('/novels/list')
}

// 查看地点详情
function viewLocationDetails(locationId) {
  if (!locationId) {
    ElMessage.warning('地点ID无效')
    return
  }
  
  if (!selectedNovel.value) {
    ElMessage.warning('请先选择小说')
    return
  }
  
  console.log(`导航到地点详情页：地点ID=${locationId}, 小说ID=${selectedNovel.value}`);
  
  // 使用强制刷新模式导航，确保组件重新加载
  router.push({
    name: 'LocationDetail',
    params: { locationId: locationId.toString() },
    query: { novelId: selectedNovel.value.toString(), _t: Date.now() }
  });
}

// 查看地点相关事件
function viewLocationEvents(locationId) {
  if (!locationId) {
    ElMessage.warning('地点ID无效')
    return
  }
  
  if (!selectedNovel.value) {
    ElMessage.warning('请先选择小说')
    return
  }
  
  console.log(`导航到地点相关事件页：地点ID=${locationId}, 小说ID=${selectedNovel.value}`);
  
  // 使用强制刷新模式导航，确保组件重新加载
  router.push({
    name: 'LocationEvents',
    params: { locationId: locationId.toString() },
    query: { novelId: selectedNovel.value.toString(), _t: Date.now() }
  });
}

// 获取地点图标（使用基于ID的确定性图标）
function getLocationIcon(id) {
  const icons = [
    'castle', 'home', 'mountain', 'forest', 'city',
    'beach', 'cave', 'building', 'palace', 'village'
  ]
  const iconIndex = id % icons.length
  return `https://api.dicebear.com/7.x/bottts/svg?seed=${icons[iconIndex]}_${id}`
}

// 截断文本
function truncateText(text, maxLength) {
  if (!text) return text
  if (text.length <= maxLength) return text
  return text.substring(0, maxLength) + '...'
}

// 获取章节标题
function getChapterTitle(chapterId) {
  const chapter = chapters.value.find(c => c.id === chapterId)
  return chapter ? chapter.title : `第${chapterId}章`
}
</script>

<style scoped>
.location-list-container {
  width: 100%;
  margin: 0 auto;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 10px;
}

.full-width-select {
  width: 200px;
}

.chapter-select {
  width: 200px;
}

.analyze-button {
  white-space: nowrap;
}

.loading-container {
  padding: 20px;
  text-align: center;
}

.loading-text {
  margin-top: 20px;
  color: #909399;
}

.location-card {
  margin-bottom: 15px;
  border-radius: 8px;
  height: 100%;
  transition: all 0.3s;
}

.location-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 5px 15px rgba(0, 0, 0, 0.1);
}

.location-col {
  margin-bottom: 20px;
}

.location-icon {
  text-align: center;
  margin-bottom: 10px;
}

.location-name {
  font-size: 1.1rem;
  margin-top: 0;
  margin-bottom: 10px;
  display: flex;
  align-items: center;
  gap: 5px;
}

.location-description {
  color: #606266;
  margin-bottom: 10px;
  font-size: 0.9rem;
}

.location-events {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
  font-size: 0.9rem;
}

.events-label {
  color: #606266;
}

.location-actions {
  display: flex;
  gap: 10px;
}

.chapter-filter-info {
  margin-bottom: 15px;
}

.no-locations-in-chapter {
  margin: 40px 0;
  text-align: center;
}
</style> 