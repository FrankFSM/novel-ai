<template>
  <div class="location-detail-container">
    <el-card shadow="never" v-loading="loading">
      <template #header>
        <div class="page-header">
          <div class="header-left">
            <el-button type="text" @click="goBack">
              <el-icon><ArrowLeft /></el-icon> 返回
            </el-button>
            <h2 v-if="locationDetail">{{ locationDetail.name }} - 详情</h2>
            <h2 v-else>地点详情</h2>
          </div>
          <div class="header-right">
            <el-button 
              type="primary" 
              @click="loadLocationDetails" 
              :loading="loading"
            >
              刷新数据
            </el-button>
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
      
      <!-- 地点详情内容 -->
      <div v-else class="location-detail-content">
        <!-- 基本信息卡片 -->
        <el-row :gutter="20">
          <el-col :xs="24" :sm="24" :md="8" :lg="8" :xl="8">
            <el-card shadow="hover" class="info-card">
              <div class="location-avatar">
                <el-avatar 
                  :size="120" 
                  :src="getLocationIcon(locationDetail.id)" 
                />
              </div>
              <h3 class="location-title">{{ locationDetail.name }}</h3>
              <div class="location-description">
                {{ locationDetail.description || '暂无描述' }}
              </div>
              
              <div class="location-hierarchy" v-if="locationDetail.parent">
                <div class="hierarchy-label">所属地点：</div>
                <el-tag 
                  type="info" 
                  @click="viewParentLocation(locationDetail.parent.id)"
                  style="cursor: pointer;"
                >
                  {{ locationDetail.parent.name }}
                </el-tag>
              </div>
              
              <div class="sub-locations" v-if="locationDetail.sub_locations && locationDetail.sub_locations.length">
                <div class="sub-label">子地点：</div>
                <div class="sub-tags">
                  <el-tag 
                    v-for="sub in locationDetail.sub_locations" 
                    :key="sub.id"
                    @click="viewSubLocation(sub.id)"
                    style="cursor: pointer; margin: 2px 4px;"
                  >
                    {{ sub.name }}
                  </el-tag>
                </div>
              </div>
              
              <div class="location-stats">
                <div class="stat-item">
                  <div class="stat-label">事件数量</div>
                  <div class="stat-value">{{ locationDetail.events.length }}</div>
                </div>
                <div class="stat-item">
                  <div class="stat-label">相关角色</div>
                  <div class="stat-value">{{ locationDetail.characters.length }}</div>
                </div>
                <div class="stat-item">
                  <div class="stat-label">子地点</div>
                  <div class="stat-value">{{ locationDetail.sub_locations.length }}</div>
                </div>
              </div>
            </el-card>
            
            <!-- 地点重要性分析 -->
            <el-card shadow="hover" class="significance-card" v-if="locationSignificance">
              <template #header>
                <div class="card-header">
                  <h3>地点重要性分析</h3>
                </div>
              </template>
              
              <div class="significance-tags" v-if="locationSignificance.significance">
                <div class="sig-label">地点特性：</div>
                <div class="sig-tags">
                  <el-tag 
                    v-for="(sig, index) in locationSignificance.significance" 
                    :key="index"
                    type="success"
                    style="margin: 3px;"
                  >
                    {{ sig }}
                  </el-tag>
                </div>
              </div>
              
              <div class="significance-analysis" v-if="locationSignificance.analysis">
                <div class="sig-label">分析：</div>
                <div class="sig-content">{{ locationSignificance.analysis }}</div>
              </div>
              
              <div class="significance-features" v-if="locationSignificance.features">
                <div class="sig-label">特点：</div>
                <el-collapse>
                  <el-collapse-item 
                    v-for="(feature, index) in locationSignificance.features" 
                    :key="index"
                    :title="feature.feature"
                  >
                    <div class="feature-description">{{ feature.description }}</div>
                    <div class="feature-evidence" v-if="feature.evidence">
                      <div class="evidence-label">依据：</div>
                      <div class="evidence-content">{{ feature.evidence }}</div>
                    </div>
                  </el-collapse-item>
                </el-collapse>
              </div>
            </el-card>
          </el-col>
          
          <!-- 右侧内容 -->
          <el-col :xs="24" :sm="24" :md="16" :lg="16" :xl="16">
            <!-- 地点相关事件 -->
            <el-card shadow="hover" class="events-card">
              <template #header>
                <div class="card-header">
                  <h3>地点相关事件</h3>
                </div>
              </template>
              
              <el-empty v-if="!locationDetail.events.length" description="暂无相关事件" />
              
              <el-timeline v-else>
                <el-timeline-item
                  v-for="event in locationDetail.events"
                  :key="event.id"
                  :type="getEventType(event.importance)"
                  :color="getEventColor(event.importance)"
                  :timestamp="event.time_description || '未知时间'"
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
                    <div v-if="event.chapter_id" class="event-chapter">
                      章节：第{{ event.chapter_id }}章
                    </div>
                  </el-card>
                </el-timeline-item>
              </el-timeline>
            </el-card>
            
            <!-- 地点相关角色 -->
            <el-card shadow="hover" class="characters-card">
              <template #header>
                <div class="card-header">
                  <h3>地点相关角色</h3>
                </div>
              </template>
              
              <el-empty v-if="!locationDetail.characters.length" description="暂无相关角色" />
              
              <div v-else class="character-list">
                <el-row :gutter="12">
                  <el-col 
                    v-for="character in locationDetail.characters" 
                    :key="character.id"
                    :xs="12" 
                    :sm="8" 
                    :md="8" 
                    :lg="6" 
                    :xl="4"
                  >
                    <el-card 
                      class="character-card" 
                      shadow="hover"
                      @click="viewCharacterDetail(character.id)"
                    >
                      <div class="character-avatar">
                        <el-avatar 
                          :size="50" 
                          :src="getCharacterAvatar(character.id)"
                        />
                      </div>
                      <div class="character-info">
                        <div class="character-name">{{ character.name }}</div>
                        <el-tag 
                          v-if="character.importance >= 4" 
                          size="small" 
                          type="danger"
                        >
                          主要
                        </el-tag>
                        <el-tag 
                          v-else-if="character.importance >= 3" 
                          size="small" 
                          type="warning"
                        >
                          重要
                        </el-tag>
                      </div>
                    </el-card>
                  </el-col>
                </el-row>
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
import { ElMessage } from 'element-plus'
import { ArrowLeft } from '@element-plus/icons-vue'
import { locationApi } from '@/api'

const router = useRouter()
const route = useRoute()

// 本地状态
const locationId = ref(null)
const novelId = ref(null)
const locationDetail = ref(null)
const locationSignificance = ref(null)
const loading = ref(false)

// 处理生命周期
onMounted(async () => {
  locationId.value = Number(route.query.locationId)
  novelId.value = Number(route.query.novelId)
  
  if (locationId.value && !isNaN(locationId.value)) {
    await loadLocationDetails()
    await loadLocationSignificance()
  } else {
    ElMessage.warning('未提供有效的地点ID')
  }
})

// 加载地点详情
async function loadLocationDetails() {
  if (!locationId.value) return
  
  try {
    loading.value = true
    
    const data = await locationApi.getLocationDetails(locationId.value)
    console.log('地点详情API响应:', data)
    
    if (data) {
      locationDetail.value = data
      ElMessage.success('成功加载地点详情')
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

// 加载地点重要性分析
async function loadLocationSignificance() {
  if (!locationId.value) return
  
  try {
    const data = await locationApi.getLocationSignificance(locationId.value)
    console.log('地点重要性分析API响应:', data)
    
    if (data) {
      locationSignificance.value = data
    }
  } catch (error) {
    console.error('获取地点重要性分析失败:', error)
    // 不显示错误消息，因为这只是补充信息
  }
}

// 返回上一页
function goBack() {
  router.go(-1)
}

// 查看父地点
function viewParentLocation(parentId) {
  router.push({
    path: '/analysis/locations/detail',
    query: {
      novelId: novelId.value,
      locationId: parentId
    }
  })
}

// 查看子地点
function viewSubLocation(subId) {
  router.push({
    path: '/analysis/locations/detail',
    query: {
      novelId: novelId.value,
      locationId: subId
    }
  })
}

// 查看角色详情
function viewCharacterDetail(characterId) {
  router.push({
    path: '/analysis/characters/journey',
    query: {
      novelId: novelId.value,
      characterId: characterId
    }
  })
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

// 获取角色头像
function getCharacterAvatar(id) {
  return `https://avatars.dicebear.com/api/avataaars/${id || Math.random()}.svg`
}
</script>

<style scoped>
.location-detail-container {
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

.location-detail-content {
  margin-top: 20px;
}

.info-card,
.events-card,
.characters-card,
.significance-card {
  margin-bottom: 20px;
}

.location-avatar {
  display: flex;
  justify-content: center;
  margin-bottom: 20px;
}

.location-title {
  text-align: center;
  font-size: 1.5rem;
  margin: 10px 0;
}

.location-description {
  text-align: center;
  color: #606266;
  margin-bottom: 20px;
}

.location-hierarchy,
.sub-locations {
  margin: 15px 0;
  text-align: center;
}

.hierarchy-label,
.sub-label {
  color: #909399;
  margin-bottom: 5px;
}

.sub-tags {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: 5px;
}

.location-stats {
  display: flex;
  justify-content: space-around;
  margin-top: 20px;
  border-top: 1px solid #EBEEF5;
  padding-top: 15px;
}

.stat-item {
  text-align: center;
}

.stat-label {
  color: #909399;
  font-size: 0.9rem;
  margin-bottom: 5px;
}

.stat-value {
  font-size: 1.5rem;
  font-weight: bold;
  color: #409EFF;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.card-header h3 {
  margin: 0;
}

.significance-tags,
.significance-analysis,
.significance-features {
  margin-bottom: 15px;
}

.sig-label {
  color: #606266;
  font-weight: bold;
  margin-bottom: 8px;
}

.sig-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 5px;
}

.sig-content {
  line-height: 1.6;
  text-align: justify;
}

.feature-description {
  margin-bottom: 10px;
}

.evidence-label {
  color: #909399;
  font-size: 0.9rem;
  margin-bottom: 5px;
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
  margin-bottom: 10px;
  text-align: justify;
}

.event-chapter {
  color: #909399;
  font-size: 0.9rem;
}

.character-list {
  margin-top: 10px;
}

.character-card {
  text-align: center;
  cursor: pointer;
  margin-bottom: 15px;
  transition: transform 0.2s;
}

.character-card:hover {
  transform: translateY(-3px);
}

.character-avatar {
  display: flex;
  justify-content: center;
  margin-bottom: 10px;
}

.character-info {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 5px;
}

.character-name {
  font-weight: bold;
  margin-bottom: 5px;
}

@media (max-width: 768px) {
  .page-header {
    flex-direction: column;
    align-items: flex-start;
  }
  
  .header-right {
    margin-top: 10px;
    width: 100%;
  }
  
  .header-right button {
    width: 100%;
  }
  
  .location-stats {
    flex-direction: column;
    gap: 15px;
  }
}
</style> 