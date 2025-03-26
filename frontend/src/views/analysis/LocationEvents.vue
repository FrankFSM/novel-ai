<template>
  <div class="location-events-container">
    <el-card shadow="never" v-loading="loading">
      <template #header>
        <div class="page-header">
          <div class="header-left">
            <el-button type="text" @click="goBack">
              <el-icon><ArrowLeft /></el-icon> 返回
            </el-button>
            <h2 v-if="locationDetail">{{ locationDetail.name }} - 事件</h2>
            <h2 v-else>地点事件</h2>
          </div>
        </div>
      </template>
      
      <!-- 加载中状态 -->
      <div v-if="loading" class="loading-container">
        <el-skeleton :rows="10" animated />
      </div>
      
      <!-- 数据不存在提示 -->
      <el-empty 
        v-else-if="!locationDetail" 
        description="地点数据不存在或尚未加载"
      >
        <el-button type="primary" @click="goBack">返回地点列表</el-button>
      </el-empty>
      
      <!-- 地点事件内容 -->
      <div v-else class="events-content">
        <!-- 基本信息 -->
        <div class="location-info">
          <div class="location-avatar">
            <el-avatar 
              :size="80" 
              :src="getLocationIcon(locationDetail.id)" 
            />
          </div>
          <div class="location-details">
            <h3 class="location-name">{{ locationDetail.name }}</h3>
            <div class="location-description">{{ locationDetail.description || '暂无描述' }}</div>
          </div>
        </div>
        
        <el-divider>
          <el-tag type="info">事件时间线</el-tag>
        </el-divider>
        
        <!-- 事件为空的提示 -->
        <el-empty 
          v-if="!locationDetail.events || locationDetail.events.length === 0" 
          description="该地点尚无相关事件"
        >
          <el-button type="primary" @click="goToLocationDetail">查看地点详情</el-button>
        </el-empty>
        
        <!-- 事件时间线 -->
        <div v-else class="events-timeline">
          <el-timeline>
            <el-timeline-item
              v-for="event in sortedEvents"
              :key="event.id"
              :type="getEventType(event.importance)"
              :color="getEventColor(event.importance)"
              :timestamp="getEventTimestamp(event)"
            >
              <el-card class="event-card">
                <template #header>
                  <div class="event-header">
                    <span class="event-name">{{ event.name }}</span>
                    <el-tag 
                      v-if="event.importance" 
                      :type="getEventTagType(event.importance)"
                      size="small"
                    >
                      重要性: {{ event.importance }}
                    </el-tag>
                  </div>
                </template>
                <div class="event-description">
                  {{ event.description || '暂无描述' }}
                </div>
                
                <!-- 相关角色 -->
                <div v-if="getEventParticipants(event).length > 0" class="event-participants">
                  <div class="participants-label">相关角色:</div>
                  <div class="participants-list">
                    <el-tag 
                      v-for="participant in getEventParticipants(event)" 
                      :key="participant.id"
                      type="success"
                      size="small"
                      style="margin: 2px 4px;"
                      @click="viewCharacterDetail(participant.id)"
                    >
                      {{ participant.name }}
                    </el-tag>
                  </div>
                </div>
              </el-card>
            </el-timeline-item>
          </el-timeline>
        </div>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { ArrowLeft } from '@element-plus/icons-vue'
import { locationApi } from '@/api'

const router = useRouter()
const route = useRoute()

// 定义Props
const props = defineProps({
  locationId: {
    type: Number,
    required: true
  },
  novelId: {
    type: Number,
    required: true
  }
})

// 本地状态
const locationDetail = ref(null)
const loading = ref(false)

// 处理生命周期
onMounted(async () => {
  if (props.locationId) {
    await loadLocationDetails()
  } else {
    ElMessage.warning('未提供有效的地点ID')
  }
})

// 加载地点详情
async function loadLocationDetails() {
  if (!props.locationId) return
  
  try {
    loading.value = true
    
    const data = await locationApi.getLocationDetails(props.locationId)
    console.log('地点详情API响应:', data)
    
    if (data) {
      locationDetail.value = data
      ElMessage.success('成功加载地点事件数据')
    } else {
      ElMessage.warning('地点详情数据为空')
    }
  } catch (error) {
    console.error('获取地点详情失败:', error)
    ElMessage.error('获取地点详情失败: ' + (error.message || '未知错误'))
  } finally {
    loading.value = false
  }
}

// 返回上一页
function goBack() {
  router.go(-1)
}

// 前往地点详情页
function goToLocationDetail() {
  router.push({
    name: 'LocationDetail',
    params: { locationId: props.locationId },
    query: { novelId: props.novelId }
  })
}

// 查看角色详情
function viewCharacterDetail(characterId) {
  router.push({
    path: '/analysis/characters/journey',
    query: {
      novelId: props.novelId,
      characterId: characterId
    }
  })
}

// 获取事件参与者
function getEventParticipants(event) {
  // 这里模拟从事件中获取参与者信息
  // 实际应该根据你的API返回的数据结构来获取
  return locationDetail.value.characters.slice(0, 3)
}

// 按章节顺序排序的事件
const sortedEvents = computed(() => {
  if (!locationDetail.value || !locationDetail.value.events) return []
  
  return [...locationDetail.value.events].sort((a, b) => {
    if (a.chapter_id && b.chapter_id) {
      return a.chapter_id - b.chapter_id
    }
    if (a.chapter_id) return -1
    if (b.chapter_id) return 1
    return 0
  })
})

// 获取事件时间戳显示
function getEventTimestamp(event) {
  if (event.time_description) return event.time_description
  if (event.chapter_id) return `第${event.chapter_id}章`
  return '未知时间'
}

// 获取事件类型（用于时间线）
function getEventType(importance) {
  if (!importance) return 'info'
  if (importance >= 4) return 'danger'
  if (importance >= 3) return 'warning'
  if (importance >= 2) return 'success'
  return 'info'
}

// 获取事件颜色（用于时间线）
function getEventColor(importance) {
  if (!importance) return '#909399'
  if (importance >= 4) return '#F56C6C'
  if (importance >= 3) return '#E6A23C'
  if (importance >= 2) return '#67C23A'
  return '#909399'
}

// 获取事件标签类型
function getEventTagType(importance) {
  if (!importance) return 'info'
  if (importance >= 4) return 'danger'
  if (importance >= 3) return 'warning'
  if (importance >= 2) return 'success'
  return 'info'
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
</script>

<style scoped>
.location-events-container {
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
  position: sticky;
  top: 0;
  background-color: white;
  z-index: 10;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 10px;
}

.header-left h2 {
  margin: 0;
}

.events-content {
  margin-top: 20px;
}

.location-info {
  display: flex;
  align-items: center;
  gap: 20px;
  margin-bottom: 20px;
  padding: 15px;
  background-color: #f5f7fa;
  border-radius: 8px;
}

.location-details {
  flex: 1;
}

.location-name {
  margin: 0 0 10px 0;
}

.location-description {
  color: #606266;
}

.events-timeline {
  margin-top: 20px;
}

.event-card {
  margin-bottom: 10px;
}

.event-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.event-name {
  font-weight: bold;
}

.event-description {
  margin-bottom: 15px;
  text-align: justify;
}

.event-participants {
  margin-top: 10px;
}

.participants-label {
  color: #909399;
  font-size: 0.9rem;
  margin-bottom: 5px;
}

.participants-list {
  display: flex;
  flex-wrap: wrap;
  gap: 5px;
}

@media (max-width: 768px) {
  .page-header {
    flex-direction: column;
    align-items: flex-start;
  }
  
  .location-info {
    flex-direction: column;
    align-items: center;
    text-align: center;
  }
}
</style> 