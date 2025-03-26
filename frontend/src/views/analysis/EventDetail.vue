<template>
  <div class="event-detail-container">
    <el-card shadow="never" class="main-card">
      <template #header>
        <div class="page-header">
          <div class="back-button">
            <el-button @click="goBack" type="text">
              <el-icon><ArrowLeft /></el-icon> 返回事件列表
            </el-button>
          </div>
          <h2 v-if="eventDetail">{{ eventDetail.name }} - 详情</h2>
          <h2 v-else>事件详情</h2>
        </div>
      </template>
      
      <!-- 加载中状态 -->
      <div v-if="loading" class="loading-container">
        <el-skeleton :rows="10" animated />
        <div class="loading-text">正在加载事件详情...</div>
      </div>
      
      <!-- 事件不存在提示 -->
      <el-empty 
        v-else-if="!eventDetail" 
        description="事件不存在或已被删除"
      >
        <el-button type="primary" @click="goBack">返回事件列表</el-button>
      </el-empty>
      
      <!-- 事件详情内容 -->
      <div v-else class="event-detail-content">
        <!-- 基本信息部分 -->
        <el-card class="detail-section basic-info" shadow="hover">
          <template #header>
            <div class="section-header">
              <h3>基本信息</h3>
              <div class="event-importance">
                <span class="importance-label">重要性：</span>
                <el-rate
                  v-model="eventDetail.importance"
                  disabled
                  :colors="['#C6D1DE', '#F7BA2A', '#FF9900']"
                />
              </div>
            </div>
          </template>
          
          <div class="detail-item">
            <span class="detail-label">发生章节：</span>
            <span class="detail-value">
              <template v-if="eventDetail.chapter_id">
                第{{ eventDetail.chapter_id }}章
                <span v-if="eventDetail.chapter_title"> - {{ eventDetail.chapter_title }}</span>
              </template>
              <span v-else>未知章节</span>
            </span>
          </div>
          
          <div class="detail-item" v-if="eventDetail.time_description">
            <span class="detail-label">时间描述：</span>
            <span class="detail-value">{{ eventDetail.time_description }}</span>
          </div>
          
          <div class="detail-item">
            <span class="detail-label">事件描述：</span>
            <div class="event-description">{{ eventDetail.description || '无事件描述' }}</div>
          </div>
          
          <div class="detail-item" v-if="eventDetail.context_excerpt">
            <span class="detail-label">原文片段：</span>
            <div class="context-excerpt">{{ eventDetail.context_excerpt }}</div>
          </div>
        </el-card>
        
        <!-- 发生地点部分 -->
        <el-card class="detail-section" shadow="hover" v-if="eventDetail.location">
          <template #header>
            <div class="section-header">
              <h3>发生地点</h3>
            </div>
          </template>
          
          <div class="location-detail">
            <div class="location-icon">
              <el-avatar :size="80" :src="getLocationIcon(eventDetail.location.id)" />
            </div>
            
            <div class="location-info">
              <h4 class="location-name">{{ eventDetail.location.name }}</h4>
              <div class="location-description">{{ eventDetail.location.description || '暂无描述' }}</div>
              <div class="location-actions">
                <el-button 
                  type="primary" 
                  size="small"
                  @click="viewLocationDetails(eventDetail.location.id)"
                >
                  查看地点详情
                </el-button>
              </div>
            </div>
          </div>
        </el-card>
        
        <!-- 参与角色部分 -->
        <el-card class="detail-section" shadow="hover" v-if="eventDetail.participants && eventDetail.participants.length > 0">
          <template #header>
            <div class="section-header">
              <h3>参与角色</h3>
              <span class="participants-count">共{{ eventDetail.participants.length }}人</span>
            </div>
          </template>
          
          <el-row :gutter="20">
            <el-col 
              v-for="participant in eventDetail.participants" 
              :key="participant.id"
              :xs="24" 
              :sm="12" 
              :md="8"
              class="participant-col"
            >
              <div class="participant-card">
                <div class="participant-avatar">
                  <el-avatar 
                    :size="60" 
                    :src="getCharacterAvatar(participant.id, participant.name)"
                  />
                </div>
                
                <div class="participant-info">
                  <h4 class="participant-name">
                    {{ participant.name }}
                    <el-tag 
                      v-if="participant.importance >= 4" 
                      type="danger" 
                      size="small"
                    >
                      主角
                    </el-tag>
                    <el-tag 
                      v-else-if="participant.importance >= 3" 
                      type="warning" 
                      size="small"
                    >
                      重要
                    </el-tag>
                  </h4>
                  
                  <div class="participant-role" v-if="participant.role">
                    角色：{{ participant.role }}
                  </div>
                  
                  <div class="participant-actions">
                    <el-button 
                      type="primary" 
                      size="small"
                      @click="viewCharacterDetails(participant.id)"
                    >
                      查看角色
                    </el-button>
                  </div>
                </div>
              </div>
            </el-col>
          </el-row>
        </el-card>
        
        <!-- 事件重要性分析 -->
        <el-card class="detail-section" shadow="hover" v-if="eventSignificance">
          <template #header>
            <div class="section-header">
              <h3>事件分析</h3>
            </div>
          </template>
          
          <div class="significance-content">
            <div class="significance-tags" v-if="eventSignificance.significance && eventSignificance.significance.length > 0">
              <div class="tags-label">事件性质：</div>
              <div class="tags-list">
                <el-tag 
                  v-for="(tag, index) in eventSignificance.significance" 
                  :key="index"
                  type="success"
                  class="significance-tag"
                >
                  {{ tag }}
                </el-tag>
              </div>
            </div>
            
            <div class="event-impacts" v-if="eventSignificance.impact && eventSignificance.impact.length > 0">
              <div class="impacts-label">事件影响：</div>
              <div class="impacts-list">
                <el-card 
                  v-for="(impact, index) in eventSignificance.impact" 
                  :key="index"
                  class="impact-card"
                  shadow="never"
                >
                  <h4 class="impact-aspect">{{ impact.aspect }}</h4>
                  <div class="impact-description">{{ impact.description }}</div>
                  <div class="impact-evidence" v-if="impact.evidence">
                    <div class="evidence-label">依据：</div>
                    <div class="evidence-text">{{ impact.evidence }}</div>
                  </div>
                </el-card>
              </div>
            </div>
            
            <div class="significance-analysis" v-if="eventSignificance.analysis">
              <div class="analysis-label">综合分析：</div>
              <div class="analysis-text">{{ eventSignificance.analysis }}</div>
            </div>
          </div>
        </el-card>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { eventApi } from '@/api'
import { ArrowLeft } from '@element-plus/icons-vue'

const router = useRouter()
const route = useRoute()

// 本地状态
const loading = ref(false)
const eventDetail = ref(null)
const eventSignificance = ref(null)

// 处理生命周期
onMounted(async () => {
  await loadEventDetails()
})

// 加载事件详情
async function loadEventDetails() {
  const eventId = Number(route.params.eventId)
  if (!eventId || isNaN(eventId)) {
    ElMessage.warning('事件ID无效')
    return
  }
  
  try {
    loading.value = true
    
    // 并行加载事件详情和事件重要性分析
    const [detailsData, significanceData] = await Promise.all([
      eventApi.getEventDetails(eventId),
      eventApi.getEventSignificance(eventId)
    ])
    
    console.log('事件详情:', detailsData)
    console.log('事件重要性分析:', significanceData)
    
    eventDetail.value = detailsData
    eventSignificance.value = significanceData
    
  } catch (error) {
    console.error('获取事件详情失败:', error)
    ElMessage.error('获取事件详情失败: ' + (error.message || '未知错误'))
    eventDetail.value = null
  } finally {
    loading.value = false
  }
}

// 返回事件列表
function goBack() {
  // 如果是从事件列表页面来的，则返回上一页
  if (route.query.novelId) {
    router.push({
      name: 'EventList',
      query: { novelId: route.query.novelId }
    })
  } else {
    // 否则导航到事件列表页面
    router.push('/analysis/events')
  }
}

// 查看地点详情
function viewLocationDetails(locationId) {
  if (!locationId) {
    ElMessage.warning('地点ID无效')
    return
  }
  
  router.push({
    name: 'LocationDetail',
    params: { locationId },
    query: { novelId: route.query.novelId }
  })
}

// 查看角色详情
function viewCharacterDetails(characterId) {
  if (!characterId) {
    ElMessage.warning('角色ID无效')
    return
  }
  
  router.push({
    name: 'CharacterDetail',
    params: { characterId },
    query: { novelId: route.query.novelId }
  })
}

// 获取地点图标
function getLocationIcon(id) {
  const icons = [
    'castle', 'home', 'mountain', 'forest', 'city',
    'beach', 'cave', 'building', 'palace', 'village'
  ]
  const iconIndex = id % icons.length
  return `https://api.dicebear.com/7.x/bottts/svg?seed=${icons[iconIndex]}_${id}`
}

// 获取角色头像
function getCharacterAvatar(id, name) {
  // 使用角色ID和名称生成确定性头像
  return `https://api.dicebear.com/7.x/personas/svg?seed=${name}_${id}`
}
</script>

<style scoped>
.event-detail-container {
  width: 100%;
  min-height: 100%;
  height: auto;
}

.main-card {
  height: 100%;
}

.page-header {
  display: flex;
  align-items: center;
  position: relative;
}

.back-button {
  margin-right: 20px;
}

.page-header h2 {
  margin: 0;
  flex-grow: 1;
}

.loading-container {
  padding: 20px 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
}

.loading-text {
  text-align: center;
  margin-top: 20px;
  color: #909399;
}

.event-detail-content {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.detail-section {
  margin-bottom: 0;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.section-header h3 {
  margin: 0;
}

.detail-item {
  margin-bottom: 15px;
}

.detail-label {
  font-weight: bold;
  color: #606266;
  margin-right: 8px;
}

.event-description {
  margin-top: 8px;
  line-height: 1.6;
  color: #303133;
  white-space: pre-wrap;
}

.context-excerpt {
  margin-top: 8px;
  line-height: 1.6;
  color: #606266;
  white-space: pre-wrap;
  background-color: #f8f8f8;
  padding: 12px;
  border-radius: 4px;
  border-left: 4px solid #409eff;
  font-family: 'Courier New', monospace;
}

.importance-label {
  color: #606266;
  margin-right: 8px;
}

.location-detail {
  display: flex;
  gap: 20px;
}

.location-info {
  flex: 1;
}

.location-name {
  margin-top: 0;
  margin-bottom: 10px;
}

.location-description {
  color: #606266;
  margin-bottom: 15px;
  line-height: 1.6;
}

.participants-count {
  font-size: 14px;
  color: #909399;
}

.participant-col {
  margin-bottom: 20px;
}

.participant-card {
  display: flex;
  align-items: center;
  gap: 15px;
  padding: 15px;
  border: 1px solid #ebeef5;
  border-radius: 4px;
  transition: all 0.3s;
}

.participant-card:hover {
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
  transform: translateY(-5px);
}

.participant-info {
  flex: 1;
}

.participant-name {
  margin: 0 0 8px 0;
  display: flex;
  align-items: center;
  gap: 8px;
}

.participant-role {
  font-size: 14px;
  color: #606266;
  margin-bottom: 10px;
}

.significance-content {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.significance-tags, .event-impacts, .significance-analysis {
  margin-bottom: 20px;
}

.tags-label, .impacts-label, .analysis-label, .evidence-label {
  font-weight: bold;
  color: #606266;
  margin-bottom: 10px;
}

.tags-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.significance-tag {
  margin-right: 0;
}

.impacts-list {
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.impact-card {
  border-left: 3px solid #67c23a;
  background-color: #f0f9eb;
}

.impact-aspect {
  margin: 0 0 10px 0;
  color: #67c23a;
}

.impact-description {
  margin-bottom: 10px;
  line-height: 1.6;
}

.evidence-text {
  font-style: italic;
  color: #606266;
}

.analysis-text {
  line-height: 1.8;
  color: #303133;
  background-color: #ecf5ff;
  padding: 15px;
  border-radius: 4px;
}

@media (max-width: 768px) {
  .page-header {
    flex-direction: column;
    align-items: flex-start;
  }
  
  .back-button {
    margin-bottom: 10px;
    margin-right: 0;
  }
  
  .location-detail {
    flex-direction: column;
    align-items: center;
    text-align: center;
  }
  
  .participant-card {
    flex-direction: column;
    text-align: center;
  }
  
  .participant-name {
    justify-content: center;
  }
  
  .section-header {
    flex-direction: column;
    align-items: flex-start;
  }
  
  .event-importance {
    margin-top: 10px;
  }
  
  .participants-count {
    margin-top: 5px;
  }
}
</style> 