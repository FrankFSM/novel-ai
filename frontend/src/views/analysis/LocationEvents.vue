<template>
  <div class="location-events-container">
    <el-card shadow="never">
      <template #header>
        <div class="page-header">
          <h2>地点事件分析</h2>
          <div class="header-actions">
            <el-select 
              v-model="selectedNovel" 
              placeholder="请选择小说" 
              @change="handleNovelChange"
              :loading="novelStore.loading"
            >
              <el-option
                v-for="novel in novelStore.novels"
                :key="novel.id"
                :label="novel.title"
                :value="novel.id"
              />
            </el-select>
            
            <el-select
              v-model="selectedLocation"
              placeholder="选择地点"
              @change="handleLocationChange"
              :disabled="!selectedNovel || !locations.length"
            >
              <el-option
                v-for="location in locations"
                :key="location.id"
                :label="location.name"
                :value="location.id"
              />
            </el-select>
            
            <el-button 
              type="primary" 
              @click="generateLocationEvents" 
              :disabled="!selectedNovel || !selectedLocation"
              :loading="analysisStore.loading"
            >
              生成地点分析
            </el-button>
          </div>
        </div>
      </template>
      
      <!-- 尚未选择小说或地点的提示 -->
      <el-empty 
        v-if="!selectedNovel || !selectedLocation" 
        description="请从上方选择小说和地点"
      >
        <el-button type="primary" @click="navigateToNovelList">浏览小说列表</el-button>
      </el-empty>
      
      <!-- 加载中状态 -->
      <div v-else-if="analysisStore.loading" class="loading-container">
        <el-skeleton :rows="15" animated />
      </div>
      
      <!-- 错误状态 -->
      <el-result 
        v-else-if="analysisStore.error" 
        icon="error" 
        :title="'加载失败'" 
        :sub-title="analysisStore.error"
      >
        <template #extra>
          <el-button type="primary" @click="generateLocationEvents">重试</el-button>
        </template>
      </el-result>
      
      <!-- 尚未生成地点事件的提示 -->
      <el-empty 
        v-else-if="!locationEvents" 
        description="点击上方按钮生成地点事件分析"
      >
        <el-button type="primary" @click="generateLocationEvents">生成地点事件分析</el-button>
      </el-empty>
      
      <!-- 地点事件内容 -->
      <div v-else class="location-events-content">
        <!-- 地点基本信息卡片 -->
        <el-card class="location-info-card">
          <div class="location-info">
            <div class="location-image">
              <img :src="getLocationImage()" alt="地点图像" class="location-img" />
            </div>
            <div class="location-details">
              <h3 class="location-name">
                {{ locationEvents.location.name }}
                <el-tag v-if="locationEvents.location.is_important" type="danger" size="small">重要地点</el-tag>
              </h3>
              <div class="location-description">
                {{ locationEvents.location.description || '暂无描述' }}
              </div>
              <div class="location-parent" v-if="locationEvents.location.parent_name">
                <span>所属区域：</span>
                <el-tag size="small" effect="plain">{{ locationEvents.location.parent_name }}</el-tag>
              </div>
            </div>
            <div class="location-stats">
              <div class="stat-item">
                <div class="stat-value">{{ locationEvents.stats.events_count }}</div>
                <div class="stat-label">相关事件</div>
              </div>
              <div class="stat-item">
                <div class="stat-value">{{ locationEvents.stats.characters_count }}</div>
                <div class="stat-label">相关角色</div>
              </div>
              <div class="stat-item">
                <div class="stat-value">{{ locationEvents.stats.chapters_count }}</div>
                <div class="stat-label">出现章节</div>
              </div>
            </div>
          </div>
        </el-card>
        
        <!-- 事件分析部分 -->
        <div class="events-analysis">
          <el-tabs v-model="activeTab">
            <!-- 事件时间线标签页 -->
            <el-tab-pane label="事件时间线" name="timeline">
              <div class="events-timeline-container">
                <el-timeline>
                  <el-timeline-item
                    v-for="event in locationEvents.events"
                    :key="event.id"
                    :timestamp="`第${event.chapter_id}章`"
                    :type="getEventType(event)"
                    :color="getEventColor(event)"
                    placement="top"
                  >
                    <div class="event-card">
                      <h4>{{ event.name }}</h4>
                      <p>{{ event.description }}</p>
                      <div class="event-participants" v-if="event.participants && event.participants.length">
                        <span class="participants-label">相关角色：</span>
                        <el-tag
                          v-for="participant in event.participants"
                          :key="participant.character_id"
                          size="small"
                          style="margin-right: 5px"
                        >
                          {{ participant.character_name }}
                        </el-tag>
                      </div>
                      <div class="event-time" v-if="event.time_description">
                        <span class="time-label">时间：</span>
                        <el-tag type="info" size="small">{{ event.time_description }}</el-tag>
                      </div>
                    </div>
                  </el-timeline-item>
                </el-timeline>
              </div>
            </el-tab-pane>
            
            <!-- 角色分布标签页 -->
            <el-tab-pane label="角色分布" name="characters">
              <div class="characters-distribution">
                <div ref="characterChartRef" class="character-chart"></div>
              </div>
            </el-tab-pane>
            
            <!-- 词云分析标签页 -->
            <el-tab-pane label="关键词分析" name="keywords">
              <div class="keywords-analysis">
                <div ref="wordCloudRef" class="word-cloud"></div>
                <div class="keywords-list">
                  <el-table :data="locationEvents.keywords" style="width: 100%">
                    <el-table-column prop="word" label="关键词"></el-table-column>
                    <el-table-column prop="weight" label="权重">
                      <template #default="scope">
                        <el-progress 
                          :percentage="scope.row.weight * 10" 
                          :color="getKeywordColor(scope.row.weight)"
                        ></el-progress>
                      </template>
                    </el-table-column>
                    <el-table-column prop="context" label="上下文"></el-table-column>
                  </el-table>
                </div>
              </div>
            </el-tab-pane>
            
            <!-- 相关地点标签页 -->
            <el-tab-pane label="相关地点" name="related">
              <div class="related-locations">
                <el-row :gutter="20">
                  <el-col 
                    v-for="location in locationEvents.related_locations" 
                    :key="location.id"
                    :xs="24" 
                    :sm="12" 
                    :md="8" 
                    :lg="6"
                  >
                    <el-card shadow="hover" class="related-location-card">
                      <div class="related-location-content">
                        <img :src="getLocationImage(location.id)" class="related-location-image" />
                        <h4>{{ location.name }}</h4>
                        <p>{{ location.description || '暂无描述' }}</p>
                        <div class="location-relation">
                          <el-tag size="small" :type="getRelationTagType(location.relation_type)">
                            {{ location.relation_type }}
                          </el-tag>
                          <el-button 
                            type="primary" 
                            size="small" 
                            text 
                            @click="changeLocation(location.id)"
                          >
                            查看详情
                          </el-button>
                        </div>
                      </div>
                    </el-card>
                  </el-col>
                </el-row>
              </div>
            </el-tab-pane>
          </el-tabs>
        </div>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, nextTick, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useNovelStore } from '@/store/novel'
import { useAnalysisStore } from '@/store/analysis'
import { ElMessage } from 'element-plus'
import * as echarts from 'echarts'
import 'echarts-wordcloud'

const router = useRouter()
const route = useRoute()
const novelStore = useNovelStore()
const analysisStore = useAnalysisStore()

// 本地状态
const selectedNovel = ref(null)
const selectedLocation = ref(null)
const locations = ref([])
const activeTab = ref('timeline')
const characterChart = ref(null)
const characterChartRef = ref(null)
const wordCloud = ref(null)
const wordCloudRef = ref(null)

// 地点事件数据
const locationEvents = computed(() => analysisStore.locationEvents || null)

// 从路由参数中获取小说ID和地点ID
onMounted(async () => {
  if (novelStore.novels.length === 0) {
    await novelStore.fetchNovels()
  }
  
  const novelId = Number(route.query.novelId)
  const locationId = Number(route.query.locationId)
  
  if (novelId && !isNaN(novelId)) {
    selectedNovel.value = novelId
    await loadLocations(novelId)
    
    if (locationId && !isNaN(locationId) && locations.value.find(l => l.id === locationId)) {
      selectedLocation.value = locationId
      
      // 自动生成地点事件分析
      generateLocationEvents()
    }
  }
})

// 监听标签页变化
watch(activeTab, async (newValue) => {
  if (newValue === 'characters' && locationEvents.value && !characterChart.value) {
    await nextTick()
    renderCharacterChart()
  } else if (newValue === 'keywords' && locationEvents.value && !wordCloud.value) {
    await nextTick()
    renderWordCloud()
  }
})

// 监听地点事件数据变化
watch(locationEvents, async () => {
  if (activeTab.value === 'characters' && locationEvents.value) {
    await nextTick()
    renderCharacterChart()
  } else if (activeTab.value === 'keywords' && locationEvents.value) {
    await nextTick()
    renderWordCloud()
  }
})

// 加载地点列表
async function loadLocations(novelId) {
  try {
    // TODO: 实际项目中应从API获取
    // const response = await novelApi.getNovelLocations(novelId)
    // locations.value = response.data
    
    // 模拟数据
    locations.value = generateMockLocations()
  } catch (error) {
    ElMessage.error('获取地点列表失败')
    locations.value = []
  }
}

// 小说选择变化处理
async function handleNovelChange(novelId) {
  selectedLocation.value = null
  analysisStore.reset()
  await loadLocations(novelId)
  
  // 更新URL参数
  router.replace({
    query: { ...route.query, novelId, locationId: undefined }
  })
}

// 地点选择变化处理
function handleLocationChange(locationId) {
  analysisStore.reset()
  
  // 更新URL参数
  router.replace({
    query: { ...route.query, locationId }
  })
}

// 生成地点事件分析
async function generateLocationEvents() {
  if (!selectedNovel.value || !selectedLocation.value) return
  
  try {
    await analysisStore.fetchLocationEvents(
      selectedNovel.value,
      selectedLocation.value
    )
  } catch (error) {
    ElMessage.error('生成地点事件分析失败')
  }
}

// 渲染角色分布图表
function renderCharacterChart() {
  if (!characterChartRef.value || !locationEvents.value?.character_stats) return
  
  if (!characterChart.value) {
    characterChart.value = echarts.init(characterChartRef.value)
  }
  
  const characterStats = locationEvents.value.character_stats
  const characters = characterStats.map(item => item.character_name)
  const appearanceCounts = characterStats.map(item => item.appearance_count)
  
  const options = {
    title: {
      text: '角色出现频率',
      left: 'center'
    },
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'shadow'
      }
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      containLabel: true
    },
    xAxis: {
      type: 'value',
      boundaryGap: [0, 0.01]
    },
    yAxis: {
      type: 'category',
      data: characters
    },
    series: [
      {
        name: '出现次数',
        type: 'bar',
        data: appearanceCounts,
        itemStyle: {
          color: function(params) {
            const colorList = [
              '#5470c6', '#91cc75', '#fac858', '#ee6666', '#73c0de', 
              '#3ba272', '#fc8452', '#9a60b4', '#ea7ccc'
            ]
            return colorList[params.dataIndex % colorList.length]
          }
        }
      }
    ]
  }
  
  characterChart.value.setOption(options)
}

// 渲染词云图
function renderWordCloud() {
  if (!wordCloudRef.value || !locationEvents.value?.keywords) return
  
  if (!wordCloud.value) {
    wordCloud.value = echarts.init(wordCloudRef.value)
  }
  
  const keywords = locationEvents.value.keywords
  const data = keywords.map(item => ({
    name: item.word,
    value: item.weight * 100,
    textStyle: {
      color: getKeywordColor(item.weight)
    }
  }))
  
  const options = {
    series: [{
      type: 'wordCloud',
      shape: 'circle',
      left: 'center',
      top: 'center',
      width: '80%',
      height: '80%',
      right: null,
      bottom: null,
      sizeRange: [12, 50],
      rotationRange: [-90, 90],
      rotationStep: 45,
      gridSize: 8,
      drawOutOfBound: false,
      textStyle: {
        fontFamily: 'sans-serif',
        fontWeight: 'bold'
      },
      emphasis: {
        textStyle: {
          shadowBlur: 10,
          shadowColor: '#333'
        }
      },
      data: data
    }]
  }
  
  wordCloud.value.setOption(options)
}

// 导航到小说列表
function navigateToNovelList() {
  router.push('/novels/list')
}

// 切换到其他地点
function changeLocation(locationId) {
  selectedLocation.value = locationId
  generateLocationEvents()
}

// 获取事件类型
function getEventType(event) {
  const typeMap = {
    'critical': 'danger',  // 关键转折点
    'major': 'warning',    // 重要事件
    'normal': 'primary',   // 普通事件
    'minor': 'info'        // 次要事件
  }
  
  return typeMap[event.importance_level] || 'primary'
}

// 获取事件颜色
function getEventColor(event) {
  const colorMap = {
    'critical': '#F56C6C',
    'major': '#E6A23C',
    'normal': '#409EFF',
    'minor': '#909399'
  }
  
  return colorMap[event.importance_level] || ''
}

// 获取关系标签类型
function getRelationTagType(relationType) {
  const typeMap = {
    '包含': 'success',
    '邻近': 'info',
    '对立': 'danger',
    '附属': 'warning'
  }
  
  return typeMap[relationType] || ''
}

// 获取关键词颜色
function getKeywordColor(weight) {
  // weight范围0-10
  if (weight >= 8) return '#F56C6C' // 高频关键词
  if (weight >= 5) return '#E6A23C' // 中高频关键词
  if (weight >= 3) return '#409EFF' // 中频关键词
  return '#909399' // 低频关键词
}

// 获取地点图像
function getLocationImage(id = null) {
  const locationId = id || selectedLocation.value
  const baseUrl = 'https://picsum.photos/seed/'
  return `${baseUrl}location-${locationId}/300/200`
}

// 窗口大小变化时重绘图表
window.addEventListener('resize', () => {
  if (characterChart.value) {
    characterChart.value.resize()
  }
  if (wordCloud.value) {
    wordCloud.value.resize()
  }
})

// 生成模拟地点数据
function generateMockLocations() {
  const count = 8
  const locations = []
  
  const names = ['华山', '洛阳城', '东海湾', '天山派', '幽冥谷', '江南水乡', '皇宫', '黑风寨']
  
  for (let i = 0; i < count; i++) {
    locations.push({
      id: i + 1,
      name: names[i % names.length]
    })
  }
  
  return locations
}
</script>

<style scoped>
.location-events-container {
  height: 100%;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 10px;
}

.page-header h2 {
  margin: 0;
}

.header-actions {
  display: flex;
  gap: 10px;
}

.loading-container {
  padding: 20px 0;
}

.location-events-content {
  margin-top: 20px;
}

.location-info-card {
  margin-bottom: 20px;
}

.location-info {
  display: flex;
  align-items: center;
  gap: 20px;
}

.location-image {
  width: 200px;
  height: 150px;
  border-radius: 8px;
  overflow: hidden;
}

.location-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.location-details {
  flex: 1;
}

.location-name {
  margin-top: 0;
  margin-bottom: 10px;
  display: flex;
  align-items: center;
  gap: 10px;
}

.location-description {
  color: #606266;
  margin-bottom: 10px;
}

.location-parent {
  display: flex;
  align-items: center;
  gap: 5px;
  color: #909399;
}

.location-stats {
  display: flex;
  gap: 20px;
}

.stat-item {
  text-align: center;
}

.stat-value {
  font-size: 24px;
  font-weight: bold;
  color: #409EFF;
  margin-bottom: 5px;
}

.stat-label {
  color: #909399;
  font-size: 14px;
}

.events-analysis {
  min-height: 400px;
}

.events-timeline-container {
  padding: 10px;
}

.event-card {
  background-color: #f5f7fa;
  border-radius: 4px;
  padding: 12px;
  margin-bottom: 10px;
}

.event-card h4 {
  margin-top: 0;
  margin-bottom: 8px;
}

.event-card p {
  margin-top: 0;
  margin-bottom: 10px;
  color: #606266;
}

.event-participants, .event-time {
  margin-bottom: 8px;
  display: flex;
  align-items: center;
  flex-wrap: wrap;
}

.participants-label, .time-label {
  color: #909399;
  margin-right: 5px;
}

.characters-distribution {
  padding: 10px;
}

.character-chart {
  width: 100%;
  height: 400px;
}

.keywords-analysis {
  padding: 10px;
}

.word-cloud {
  width: 100%;
  height: 300px;
  margin-bottom: 20px;
}

.keywords-list {
  margin-top: 20px;
}

.related-locations {
  padding: 10px;
}

.related-location-card {
  margin-bottom: 20px;
  height: 100%;
}

.related-location-content {
  display: flex;
  flex-direction: column;
  height: 100%;
}

.related-location-image {
  width: 100%;
  height: 120px;
  object-fit: cover;
  border-radius: 4px;
  margin-bottom: 10px;
}

.related-location-content h4 {
  margin-top: 0;
  margin-bottom: 10px;
}

.related-location-content p {
  color: #606266;
  margin-top: 0;
  margin-bottom: 10px;
  flex-grow: 1;
}

.location-relation {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
</style> 