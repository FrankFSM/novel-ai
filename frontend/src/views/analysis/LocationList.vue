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
            
            <el-button 
              type="primary" 
              @click="analyzeLocations" 
              :disabled="!selectedNovel"
              :loading="loading"
              class="analyze-button"
            >
              <el-icon><Search /></el-icon>
              分析地点
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
      
      <!-- 加载中状态 -->
      <div v-else-if="loading" class="loading-container">
        <el-skeleton :rows="5" animated />
        <div class="loading-text">正在分析小说地点...</div>
      </div>
      
      <!-- 地点列表为空的提示 -->
      <el-empty 
        v-else-if="locations.length === 0" 
        description="暂无地点数据，点击上方按钮分析地点"
      >
        <el-button type="primary" @click="analyzeLocations">分析地点</el-button>
      </el-empty>
      
      <!-- 地点列表 -->
      <div v-else class="location-list">
        <el-row :gutter="20">
          <el-col 
            v-for="location in locations" 
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
import { ref, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useNovelStore } from '@/store/novel'
import { ElMessage } from 'element-plus'
import { locationApi } from '@/api'
import { Search, DataAnalysis } from '@element-plus/icons-vue'

const router = useRouter()
const route = useRoute()
const novelStore = useNovelStore()

// 本地状态
const selectedNovel = ref(null)
const locations = ref([])
const loading = ref(false)
const eventAnalysisLoading = ref(false)

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
    await loadLocations(novelId)
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
      // 按事件数量排序
      locations.value = [...data].sort((a, b) => 
        (b.events_count || 0) - (a.events_count || 0)
      )
      ElMessage.success(`成功加载小说地点，共发现${data.length}个地点`)
    } else {
      ElMessage.warning('获取到的地点列表为空')
      locations.value = []
    }
  } catch (error) {
    console.error('获取地点列表失败:', error)
    ElMessage.error('获取地点列表失败: ' + (error.message || '未知错误'))
    locations.value = []
  } finally {
    loading.value = false
  }
}

// 小说选择变化处理
async function handleNovelChange(novelId) {
  await loadLocations(novelId)
  
  // 更新URL参数
  router.replace({
    query: { ...route.query, novelId }
  })
}

// 手动分析地点按钮处理
async function analyzeLocations() {
  if (!selectedNovel.value) return
  
  try {
    await loadLocations(selectedNovel.value, true) // 强制刷新
  } catch (error) {
    ElMessage.error('分析地点失败')
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
</script>

<style scoped>
.location-list-container {
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

.header-actions {
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

.location-list {
  margin-top: 20px;
  overflow: visible;
  padding-bottom: 30px;
}

.location-col {
  margin-bottom: 20px;
}

.location-card {
  height: 100%;
  transition: transform 0.3s;
  display: flex;
  flex-direction: column;
}

.location-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 10px 20px rgba(0,0,0,0.1);
}

.location-icon {
  display: flex;
  justify-content: center;
  margin-bottom: 10px;
  padding-top: 15px;
}

.location-info {
  text-align: center;
  flex: 1;
  display: flex;
  flex-direction: column;
  padding: 0 10px 10px;
}

.location-name {
  margin: 10px 0;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-wrap: wrap;
  gap: 8px;
}

.location-description {
  color: #606266;
  margin-bottom: 10px;
  min-height: 60px;
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
}

.location-events {
  margin-bottom: 15px;
  flex: 1;
}

.events-label {
  color: #909399;
  font-size: 12px;
  margin-bottom: 5px;
}

.event-count {
  display: flex;
  justify-content: center;
  gap: 5px;
  margin-bottom: 5px;
}

.location-actions {
  display: flex;
  justify-content: center;
  gap: 10px;
  margin-top: 15px;
  flex-wrap: wrap;
}

/* 确保内容在所有设备上都可滚动 */
:deep(.el-card__body) {
  overflow-y: visible;
  height: auto;
}

:deep(.el-card) {
  overflow: visible;
}

/* 针对滚动条的样式 */
::-webkit-scrollbar {
  width: 6px;
  height: 6px;
}

::-webkit-scrollbar-track {
  background: #f1f1f1;
  border-radius: 3px;
}

::-webkit-scrollbar-thumb {
  background: #c0c4cc;
  border-radius: 3px;
}

::-webkit-scrollbar-thumb:hover {
  background: #909399;
}

@media (max-width: 768px) {
  .page-header {
    flex-direction: column;
    align-items: flex-start;
    width: 100%;
  }
  
  .header-actions {
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
  
  .location-actions {
    flex-direction: column;
    width: 100%;
  }
  
  .location-actions .el-button {
    margin-right: 0;
    margin-bottom: 8px;
    width: 100%;
  }
  
  .location-card {
    margin-bottom: 10px;
  }
  
  .location-icon {
    padding-top: 10px;
  }
  
  :deep(.el-empty__image) {
    width: 120px !important;
    height: 120px !important;
  }
}

/* 触摸设备滚动优化 */
@media (pointer: coarse) {
  .location-list-container {
    -webkit-overflow-scrolling: touch;
  }
}
</style> 