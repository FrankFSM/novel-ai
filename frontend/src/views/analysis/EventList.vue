<template>
  <div class="event-list-container">
    <el-card shadow="never">
      <template #header>
        <div class="page-header">
          <div class="header-left">
            <h2>事件分析</h2>
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
            
            <el-button 
              type="primary" 
              @click="loadEvents(selectedNovel, true)" 
              :disabled="!selectedNovel"
              :loading="loading"
              class="analyze-button"
            >
              <el-icon><Refresh /></el-icon>
              刷新事件
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
      
      <!-- 加载中状态 -->
      <div v-else-if="loading" class="loading-container">
        <el-skeleton :rows="5" animated />
        <div class="loading-text">正在获取事件数据...</div>
      </div>
      
      <!-- 角色或地点未分析的提示 -->
      <el-empty 
        v-else-if="!dataStatus.characters_exist || !dataStatus.locations_exist" 
        description="要进行事件分析，需要先完成角色和地点分析"
      >
        <div class="status-message">
          <el-alert
            v-if="!dataStatus.characters_exist"
            title="未找到角色数据"
            type="warning"
            :closable="false"
            show-icon
          >
            <p>请先分析小说角色，以便事件分析可以关联角色信息。</p>
            <el-button type="primary" @click="navigateToCharacterList">分析角色</el-button>
          </el-alert>
          
          <el-alert
            v-if="!dataStatus.locations_exist"
            title="未找到地点数据"
            type="warning"
            :closable="false"
            show-icon
            style="margin-top: 10px"
          >
            <p>请先分析小说地点，以便事件分析可以关联地点信息。</p>
            <el-button type="primary" @click="navigateToLocationList">分析地点</el-button>
          </el-alert>
        </div>
      </el-empty>
      
      <!-- 事件列表为空的提示 -->
      <el-empty 
        v-else-if="events.length === 0" 
        description="暂无事件数据，请点击分析事件按钮"
      >
        <el-button 
          type="primary" 
          @click="loadEvents(selectedNovel, true)" 
          :loading="loading"
        >
          分析事件
        </el-button>
      </el-empty>
      
      <!-- 事件列表 -->
      <div v-else class="event-container">
        <!-- 筛选器 -->
        <div class="filter-section">
          <el-card shadow="hover" class="filter-card">
            <template #header>
              <div class="filter-header">
                <h3>事件筛选</h3>
                <el-button size="small" @click="resetFilters">重置</el-button>
              </div>
            </template>
            
            <div class="filter-item">
              <span class="filter-label">按角色筛选：</span>
              <el-select
                v-model="filters.characterId"
                placeholder="选择角色"
                clearable
                @change="applyFilters"
                class="filter-select"
              >
                <el-option
                  v-for="character in characters"
                  :key="character.id"
                  :label="character.name"
                  :value="character.id"
                />
              </el-select>
            </div>
            
            <div class="filter-item">
              <span class="filter-label">按地点筛选：</span>
              <el-select
                v-model="filters.locationId"
                placeholder="选择地点"
                clearable
                @change="applyFilters"
                class="filter-select"
              >
                <el-option
                  v-for="location in locations"
                  :key="location.id"
                  :label="location.name"
                  :value="location.id"
                />
              </el-select>
            </div>
            
            <div class="filter-item">
              <span class="filter-label">最小重要性：</span>
              <el-rate
                v-model="filters.minImportance"
                @change="applyFilters"
                :colors="['#C6D1DE', '#F7BA2A', '#FF9900']"
              />
            </div>
            
            <div class="filter-summary">
              当前显示: {{ filteredEvents.length }} / {{ events.length }} 个事件
            </div>
          </el-card>
        </div>
        
        <!-- 事件列表 -->
        <div class="events-list">
          <el-card 
            v-for="event in filteredEvents" 
            :key="event.id"
            class="event-card"
            shadow="hover"
          >
            <div class="event-header">
              <h3 class="event-title">{{ event.name }}</h3>
              <div class="event-importance">
                <el-rate
                  v-model="event.importance"
                  disabled
                  :colors="['#C6D1DE', '#F7BA2A', '#FF9900']"
                />
              </div>
            </div>
            
            <div class="event-description">
              {{ event.description || '暂无描述' }}
            </div>
            
            <div class="event-meta">
              <div class="event-location" v-if="event.location">
                <el-tag type="success" size="small">
                  <el-icon><Location /></el-icon>
                  {{ event.location.name }}
                </el-tag>
              </div>
              
              <div class="event-chapter" v-if="event.chapter_id">
                <el-tag type="info" size="small">
                  <el-icon><DocumentAdd /></el-icon>
                  第{{ event.chapter_id }}章
                </el-tag>
              </div>
              
              <div class="event-time" v-if="event.time_description">
                <el-tag type="warning" size="small">
                  <el-icon><Clock /></el-icon>
                  {{ event.time_description }}
                </el-tag>
              </div>
            </div>
            
            <div class="event-participants" v-if="event.participants && event.participants.length > 0">
              <div class="participants-label">参与角色：</div>
              <div class="participants-list">
                <el-tag
                  v-for="(participant, index) in event.participants"
                  :key="index"
                  :type="getCharacterTagType(participant.importance)"
                  size="small"
                  class="participant-tag"
                >
                  {{ participant.name }}
                  <span v-if="participant.role">({{ participant.role }})</span>
                </el-tag>
              </div>
            </div>
            
            <div class="event-actions">
              <el-button 
                type="primary" 
                size="small" 
                @click="viewEventDetails(event.id)"
              >
                详细信息
              </el-button>
            </div>
          </el-card>
        </div>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useNovelStore } from '@/store/novel'
import { ElMessage } from 'element-plus'
import { eventApi, characterApi, locationApi } from '@/api'
import { Refresh, Location, DocumentAdd, Clock } from '@element-plus/icons-vue'

const router = useRouter()
const route = useRoute()
const novelStore = useNovelStore()

// 本地状态
const selectedNovel = ref(null)
const events = ref([])
const filteredEvents = ref([])
const characters = ref([])
const locations = ref([])
const loading = ref(false)
const dataStatus = ref({
  characters_exist: false,
  locations_exist: false,
  events_count: 0
})
const filters = ref({
  characterId: null,
  locationId: null,
  minImportance: 0
})

// 处理生命周期
onMounted(async () => {
  // 加载小说列表
  if (novelStore.novels.length === 0) {
    await novelStore.fetchNovels()
  }
  
  // 从URL参数获取小说ID
  const novelId = Number(route.query.novelId)
  if (novelId && !isNaN(novelId)) {
    selectedNovel.value = novelId
    await loadEvents(novelId)
    await loadCharacters(novelId)
    await loadLocations(novelId)
  }
})

// 监听过滤条件变化
watch(filters, () => {
  applyFilters()
}, { deep: true })

// 加载事件列表
async function loadEvents(novelId, forceRefresh = false) {
  if (!novelId) return
  
  try {
    events.value = []
    filteredEvents.value = []
    loading.value = true
    
    // 调用API获取事件列表
    const data = await eventApi.getNovelEvents(novelId, forceRefresh)
    console.log('事件分析API响应:', data)
    
    // 更新数据状态
    if (data && data.metadata) {
      dataStatus.value = {
        characters_exist: data.metadata.characters_exist || false,
        locations_exist: data.metadata.locations_exist || false,
        events_count: data.metadata.events_count || 0
      }
      console.log('数据状态:', dataStatus.value)
    }
    
    // 只有当角色和地点都存在时，才处理事件数据
    if (data && data.events && Array.isArray(data.events)) {
      events.value = data.events
      filteredEvents.value = [...data.events]
      
      if (data.events.length > 0) {
        ElMessage.success(`成功加载事件列表，共找到${data.events.length}个事件`)
      } else if (dataStatus.value.characters_exist && dataStatus.value.locations_exist) {
        ElMessage.info('当前小说暂无事件数据，可以点击"刷新事件"按钮进行分析')
      }
    } else {
      events.value = []
      filteredEvents.value = []
    }
  } catch (error) {
    console.error('获取事件列表失败:', error)
    ElMessage.error('获取事件列表失败: ' + (error.message || '未知错误'))
    events.value = []
    filteredEvents.value = []
  } finally {
    loading.value = false
  }
}

// 加载角色列表
async function loadCharacters(novelId) {
  if (!novelId) return
  
  try {
    // 获取小说角色列表，用于筛选
    const data = await characterApi.getNovelCharacters(novelId)
    if (data && data.characters && Array.isArray(data.characters)) {
      characters.value = data.characters
    } else {
      characters.value = []
    }
  } catch (error) {
    console.error('获取角色列表失败:', error)
    characters.value = []
  }
}

// 加载地点列表
async function loadLocations(novelId) {
  if (!novelId) return
  
  try {
    // 获取小说地点列表，用于筛选
    const data = await locationApi.getNovelLocations(novelId)
    if (data && data.locations && Array.isArray(data.locations)) {
      locations.value = data.locations
    } else {
      locations.value = []
    }
  } catch (error) {
    console.error('获取地点列表失败:', error)
    locations.value = []
  }
}

// 应用筛选
function applyFilters() {
  if (events.value.length === 0) return
  
  let filtered = [...events.value]
  
  // 按角色筛选
  if (filters.value.characterId) {
    filtered = filtered.filter(event => 
      event.participants && 
      event.participants.some(p => p.id === filters.value.characterId)
    )
  }
  
  // 按地点筛选
  if (filters.value.locationId) {
    filtered = filtered.filter(event => 
      event.location && event.location.id === filters.value.locationId
    )
  }
  
  // 按重要性筛选
  if (filters.value.minImportance > 0) {
    filtered = filtered.filter(event => 
      event.importance && event.importance >= filters.value.minImportance
    )
  }
  
  filteredEvents.value = filtered
}

// 重置筛选
function resetFilters() {
  filters.value = {
    characterId: null,
    locationId: null,
    minImportance: 0
  }
  filteredEvents.value = [...events.value]
}

// 小说选择变化处理
async function handleNovelChange(novelId) {
  resetFilters()
  await loadEvents(novelId)
  await loadCharacters(novelId)
  await loadLocations(novelId)
  
  // 更新URL参数
  router.replace({
    query: { ...route.query, novelId }
  })
}

// 导航到小说列表
function navigateToNovelList() {
  router.push('/novels/list')
}

// 导航到地点列表
function navigateToLocationList() {
  router.push({
    name: 'LocationList',
    query: { novelId: selectedNovel.value }
  })
}

// 导航到角色列表
function navigateToCharacterList() {
  router.push({
    name: 'CharacterList',
    query: { novelId: selectedNovel.value }
  })
}

// 查看事件详情
function viewEventDetails(eventId) {
  if (!eventId) {
    ElMessage.warning('事件ID无效')
    return
  }
  
  if (!selectedNovel.value) {
    ElMessage.warning('请先选择小说')
    return
  }
  
  router.push({
    name: 'EventDetail',
    params: { eventId },
    query: { novelId: selectedNovel.value }
  })
}

// 根据角色重要性获取标签类型
function getCharacterTagType(importance) {
  if (!importance) return ''
  if (importance >= 4) return 'danger'
  if (importance >= 3) return 'warning'
  if (importance >= 2) return 'success'
  return 'info'
}
</script>

<style scoped>
.event-list-container {
  min-height: 100%;
  height: auto;
  width: 100%;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  position: relative;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 15px;
  margin-bottom: 15px;
  position: sticky;
  top: 0;
  background-color: white;
  z-index: 10;
  padding: 10px 0;
}

.page-header h2 {
  margin: 0;
}

.header-right {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
  align-items: center;
}

.full-width-select {
  min-width: 180px;
}

.analyze-button {
  white-space: nowrap;
}

.loading-container {
  padding: 20px 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 200px;
}

.loading-text {
  text-align: center;
  margin-top: 20px;
  color: #909399;
}

.event-container {
  display: flex;
  gap: 20px;
  margin-top: 20px;
}

.filter-section {
  width: 300px;
  flex-shrink: 0;
  align-self: flex-start;
  position: sticky;
  top: 80px;
}

.filter-card {
  margin-bottom: 20px;
}

.filter-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.filter-header h3 {
  margin: 0;
}

.filter-item {
  margin-bottom: 15px;
}

.filter-label {
  display: block;
  margin-bottom: 8px;
  color: #606266;
  font-size: 14px;
}

.filter-select {
  width: 100%;
}

.filter-summary {
  text-align: center;
  margin-top: 10px;
  color: #909399;
  font-size: 14px;
}

.events-list {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.event-card {
  margin-bottom: 15px;
  transition: transform 0.2s;
}

.event-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 8px 16px rgba(0,0,0,0.1);
}

.event-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}

.event-title {
  margin: 0;
  font-size: 18px;
  color: #303133;
}

.event-description {
  margin-bottom: 15px;
  color: #606266;
  line-height: 1.6;
}

.event-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-bottom: 15px;
}

.event-participants {
  margin-bottom: 15px;
}

.participants-label {
  margin-bottom: 8px;
  color: #909399;
  font-size: 14px;
}

.participants-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.participant-tag {
  margin-right: 0;
}

.event-actions {
  display: flex;
  justify-content: flex-end;
}

@media (max-width: 992px) {
  .event-container {
    flex-direction: column;
  }
  
  .filter-section {
    width: 100%;
    position: static;
  }
}

@media (max-width: 768px) {
  .page-header {
    flex-direction: column;
    align-items: flex-start;
    width: 100%;
  }
  
  .header-right {
    flex-direction: column;
    width: 100%;
    gap: 15px;
    margin-top: 10px;
  }
  
  .full-width-select {
    width: 100%;
  }
  
  .analyze-button {
    width: 100%;
    margin-left: 0 !important;
  }
  
  .event-header {
    flex-direction: column;
    align-items: flex-start;
  }
  
  .event-importance {
    margin-top: 8px;
  }
}
</style> 