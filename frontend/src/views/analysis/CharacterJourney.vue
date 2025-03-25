<template>
  <div class="journey-container">
    <el-card shadow="never">
      <template #header>
        <div class="page-header">
          <h2>角色旅程分析</h2>
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
              v-model="selectedCharacter"
              placeholder="选择角色"
              @change="handleCharacterChange"
              :disabled="!selectedNovel || !characters.length"
              :loading="loading"
            >
              <el-option
                v-for="character in characters"
                :key="character.id"
                :label="character.name"
                :value="character.id"
              />
            </el-select>
            
            <el-button 
              type="primary" 
              @click="analyzeCharacters" 
              :disabled="!selectedNovel"
              :loading="loading"
            >
              分析角色
            </el-button>
            
            <el-button 
              type="primary" 
              @click="generateJourney" 
              :disabled="!selectedNovel || !selectedCharacter"
              :loading="analysisStore.loading"
            >
              生成角色旅程
            </el-button>
          </div>
        </div>
      </template>
      
      <!-- 正在加载角色列表 -->
      <div v-if="loading" class="loading-container">
        <el-skeleton :rows="5" animated />
        <div class="loading-text">正在分析小说角色...</div>
      </div>
      
      <!-- 尚未选择小说或角色的提示 -->
      <el-empty 
        v-if="!selectedNovel || !selectedCharacter" 
        description="请从上方选择小说和角色"
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
          <el-button type="primary" @click="generateJourney">重试</el-button>
        </template>
      </el-result>
      
      <!-- 尚未生成角色旅程的提示 -->
      <el-empty 
        v-else-if="!analysisStore.characterJourney" 
        description="点击上方按钮生成角色旅程"
      >
        <el-button type="primary" @click="generateJourney">生成角色旅程</el-button>
      </el-empty>
      
      <!-- 角色旅程内容 -->
      <div v-else class="journey-content">
        <!-- 角色基本信息卡片 -->
        <el-card class="character-info-card">
          <div class="character-info">
            <div class="character-avatar">
              <el-avatar :size="80" :src="characterAvatar"></el-avatar>
            </div>
            <div class="character-details">
              <h3 class="character-name">
                {{ characterJourney.character.name }}
                <el-tag v-if="characterJourney.character.is_main" type="danger" size="small">主角</el-tag>
              </h3>
              <div class="character-description">
                {{ characterJourney.character.description || '暂无描述' }}
              </div>
              <div class="character-aliases" v-if="characterJourney.character.alias && characterJourney.character.alias.length">
                <span class="aliases-label">别名：</span>
                <el-tag 
                  v-for="alias in characterJourney.character.alias" 
                  :key="alias" 
                  size="small" 
                  effect="plain"
                  style="margin-right: 5px"
                >
                  {{ alias }}
                </el-tag>
              </div>
            </div>
            <div class="character-stats">
              <div class="stat-item">
                <div class="stat-value">{{ characterJourney.stats.chapters_count }}</div>
                <div class="stat-label">出场章节</div>
              </div>
              <div class="stat-item">
                <div class="stat-value">{{ characterJourney.stats.events_count }}</div>
                <div class="stat-label">相关事件</div>
              </div>
              <div class="stat-item">
                <div class="stat-value">{{ characterJourney.stats.relationships_count }}</div>
                <div class="stat-label">人物关系</div>
              </div>
            </div>
          </div>
        </el-card>
        
        <!-- 旅程可视化部分 -->
        <div class="journey-visualization">
          <el-tabs v-model="activeTab">
            <!-- 发展阶段标签页 -->
            <el-tab-pane label="发展阶段" name="stages">
              <div class="stages-container">
                <el-steps :active="characterJourney.stages.length" finish-status="success" :space="200" direction="vertical">
                  <el-step 
                    v-for="(stage, index) in characterJourney.stages" 
                    :key="index"
                    :title="stage.name"
                    :description="stage.description"
                  >
                    <template #icon>
                      <el-avatar :size="30" :src="getStageIcon(index)"></el-avatar>
                    </template>
                  </el-step>
                </el-steps>
              </div>
            </el-tab-pane>
            
            <!-- 关键事件标签页 -->
            <el-tab-pane label="关键事件" name="events">
              <div class="events-container">
                <el-timeline>
                  <el-timeline-item
                    v-for="event in characterJourney.key_events"
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
                      <div class="event-location" v-if="event.location">
                        <span class="location-label">发生地点：</span>
                        <el-tag type="warning" size="small">{{ event.location.name }}</el-tag>
                      </div>
                    </div>
                  </el-timeline-item>
                </el-timeline>
              </div>
            </el-tab-pane>
            
            <!-- 情感变化标签页 -->
            <el-tab-pane label="情感变化" name="emotions">
              <div class="emotions-container">
                <div ref="emotionChartRef" class="emotion-chart"></div>
              </div>
            </el-tab-pane>
            
            <!-- 人物关系标签页 -->
            <el-tab-pane label="人物关系" name="relationships">
              <div class="relationships-container">
                <div class="relationship-list">
                  <el-card 
                    v-for="relation in characterJourney.relationships" 
                    :key="relation.id"
                    class="relationship-card"
                    shadow="hover"
                  >
                    <div class="relationship-content">
                      <div class="relationship-avatars">
                        <el-avatar :size="40" :src="characterAvatar"></el-avatar>
                        <el-icon class="relation-icon"><ArrowRight /></el-icon>
                        <el-avatar :size="40" :src="getRandomAvatar(relation.target_character_id)"></el-avatar>
                      </div>
                      <div class="relationship-info">
                        <div class="relationship-title">
                          <span class="character-name">{{ characterJourney.character.name }}</span>
                          <el-tag size="small" :type="getRelationTagType(relation.relation_type)">
                            {{ relation.relation_type }}
                          </el-tag>
                          <span class="target-name">{{ relation.target_character_name }}</span>
                        </div>
                        <div class="relationship-description">
                          {{ relation.description || '暂无描述' }}
                        </div>
                        <div class="relationship-first-chapter" v-if="relation.first_chapter_id">
                          <el-tag size="small" effect="plain">关系建立于第{{ relation.first_chapter_id }}章</el-tag>
                        </div>
                      </div>
                    </div>
                  </el-card>
                </div>
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
import { ArrowRight } from '@element-plus/icons-vue'
import * as echarts from 'echarts'
import { characterApi } from '@/api'

const router = useRouter()
const route = useRoute()
const novelStore = useNovelStore()
const analysisStore = useAnalysisStore()

// 本地状态
const selectedNovel = ref(null)
const selectedCharacter = ref(null)
const characters = ref([])
const loading = ref(false)
const activeTab = ref('stages')
const emotionChart = ref(null)
const emotionChartRef = ref(null)

// 角色旅程数据
const characterJourney = computed(() => analysisStore.characterJourney || null)

// 角色头像（模拟数据）
const characterAvatar = computed(() => {
  return `https://avatars.dicebear.com/api/avataaars/${selectedCharacter.value || 'default'}.svg`
})

// 从路由参数中获取小说ID和角色ID
onMounted(async () => {
  if (novelStore.novels.length === 0) {
    await novelStore.fetchNovels()
  }
  
  const novelId = Number(route.query.novelId)
  const characterId = Number(route.query.characterId)
  
  if (novelId && !isNaN(novelId)) {
    selectedNovel.value = novelId
    await loadCharacters(novelId)
    
    if (characterId && !isNaN(characterId) && characters.value.find(c => c.id === characterId)) {
      selectedCharacter.value = characterId
      
      // 自动生成角色旅程
      generateJourney()
    }
  }
})

// 监听标签页变化
watch(activeTab, async (newValue) => {
  if (newValue === 'emotions' && characterJourney.value && !emotionChart.value) {
    await nextTick()
    renderEmotionChart()
  }
})

// 监听角色旅程数据变化
watch(characterJourney, async () => {
  if (activeTab.value === 'emotions' && characterJourney.value) {
    await nextTick()
    renderEmotionChart()
  }
})

// 加载角色列表
async function loadCharacters(novelId, forceRefresh = false) {
  if (!novelId) return
  
  try {
    characters.value = []
    loading.value = true
    
    // 调用新API获取角色列表
    const data = await characterApi.analyzeCharacters(novelId, forceRefresh)
    console.log('角色分析API响应:', data)
    
    // API函数已经提取了data部分
    if (data && Array.isArray(data)) {
      characters.value = data
      ElMessage.success(`成功加载小说角色，共发现${data.length}个角色`)
    } else {
      ElMessage.warning('获取到的角色列表为空')
      characters.value = []
    }
  } catch (error) {
    console.error('获取角色列表失败:', error)
    ElMessage.error('获取角色列表失败: ' + (error.message || '未知错误'))
    characters.value = []
  } finally {
    loading.value = false
  }
}

// 小说选择变化处理
async function handleNovelChange(novelId) {
  selectedCharacter.value = null
  analysisStore.reset()
  await loadCharacters(novelId)
  
  // 更新URL参数
  router.replace({
    query: { ...route.query, novelId, characterId: undefined }
  })
}

// 角色选择变化处理
function handleCharacterChange(characterId) {
  analysisStore.reset()
  
  // 更新URL参数
  router.replace({
    query: { ...route.query, characterId }
  })
}

// 生成角色旅程
async function generateJourney() {
  if (!selectedNovel.value || !selectedCharacter.value) return
  
  try {
    await analysisStore.fetchCharacterJourney(
      selectedNovel.value,
      selectedCharacter.value
    )
  } catch (error) {
    ElMessage.error('生成角色旅程失败')
  }
}

// 渲染情感变化图表
function renderEmotionChart() {
  if (!emotionChartRef.value || !characterJourney.value?.emotions) return
  
  if (!emotionChart.value) {
    emotionChart.value = echarts.init(emotionChartRef.value)
  }
  
  const emotions = characterJourney.value.emotions
  
  const options = {
    title: {
      text: '角色情感变化趋势',
      left: 'center'
    },
    tooltip: {
      trigger: 'axis',
      formatter: function(params) {
        return `第${params[0].name}章<br/>${params[0].marker}${params[0].seriesName}: ${params[0].value}`
      }
    },
    xAxis: {
      type: 'category',
      data: emotions.map(item => item.chapter_id),
      name: '章节',
      nameLocation: 'middle',
      nameGap: 30
    },
    yAxis: {
      type: 'value',
      name: '情感值',
      min: -100,
      max: 100,
      interval: 50,
      axisLabel: {
        formatter: '{value}'
      }
    },
    visualMap: {
      show: false,
      dimension: 1,
      pieces: [
        {gte: 50, color: '#d94e5d'},  // 喜悦
        {gte: 10, lt: 50, color: '#eac736'},  // 平静
        {gte: -10, lt: 10, color: '#50a3ba'},  // 中性
        {gte: -50, lt: -10, color: '#4b5cc4'},  // 低落
        {lt: -50, color: '#594d9c'}  // 悲伤
      ]
    },
    series: [
      {
        name: '情感值',
        type: 'line',
        smooth: true,
        data: emotions.map(item => item.value),
        markPoint: {
          data: [
            { type: 'max', name: '最高值' },
            { type: 'min', name: '最低值' }
          ]
        },
        markLine: {
          data: [
            { type: 'average', name: '平均值' }
          ]
        }
      }
    ]
  }
  
  emotionChart.value.setOption(options)
}

// 导航到小说列表
function navigateToNovelList() {
  router.push('/novels/list')
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
    '师徒': 'success',
    '朋友': 'info',
    '敌人': 'danger',
    '亲人': 'warning',
    '恋人': '',
    '同门': 'info'
  }
  
  return typeMap[relationType] || ''
}

// 获取阶段图标
function getStageIcon(index) {
  // 使用固定图标集合
  const icons = [
    'https://avatars.dicebear.com/api/bottts/stage1.svg',
    'https://avatars.dicebear.com/api/bottts/stage2.svg',
    'https://avatars.dicebear.com/api/bottts/stage3.svg',
    'https://avatars.dicebear.com/api/bottts/stage4.svg',
    'https://avatars.dicebear.com/api/bottts/stage5.svg'
  ]
  
  return icons[index % icons.length]
}

// 获取随机头像
function getRandomAvatar(id) {
  return `https://avatars.dicebear.com/api/avataaars/${id || Math.random()}.svg`
}

// 窗口大小变化时重绘图表
window.addEventListener('resize', () => {
  if (emotionChart.value) {
    emotionChart.value.resize()
  }
})

// 手动分析角色按钮处理
async function analyzeCharacters() {
  if (!selectedNovel.value) return
  
  try {
    await loadCharacters(selectedNovel.value, true) // 传递true表示强制刷新
  } catch (error) {
    ElMessage.error('分析角色失败')
  }
}
</script>

<style scoped>
.journey-container {
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

.journey-content {
  margin-top: 20px;
}

.character-info-card {
  margin-bottom: 20px;
}

.character-info {
  display: flex;
  align-items: center;
  gap: 20px;
}

.character-details {
  flex: 1;
}

.character-name {
  margin-top: 0;
  margin-bottom: 10px;
  display: flex;
  align-items: center;
  gap: 10px;
}

.character-description {
  color: #606266;
  margin-bottom: 10px;
}

.character-aliases {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
}

.aliases-label {
  color: #909399;
  margin-right: 5px;
}

.character-stats {
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

.journey-visualization {
  min-height: 400px;
}

.stages-container {
  padding: 20px;
  width: 100%;
}

.events-container {
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

.event-participants {
  margin-bottom: 8px;
  display: flex;
  align-items: center;
  flex-wrap: wrap;
}

.participants-label, .location-label {
  color: #909399;
  margin-right: 5px;
}

.emotions-container {
  width: 100%;
  padding: 10px;
}

.emotion-chart {
  width: 100%;
  height: 400px;
}

.relationships-container {
  padding: 10px;
}

.relationship-list {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 15px;
}

.relationship-card {
  height: 100%;
}

.relationship-content {
  display: flex;
  flex-direction: column;
}

.relationship-avatars {
  display: flex;
  align-items: center;
  justify-content: space-around;
  margin-bottom: 15px;
}

.relation-icon {
  font-size: 20px;
  color: #409EFF;
}

.relationship-info {
  text-align: center;
}

.relationship-title {
  font-weight: bold;
  margin-bottom: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
}

.relationship-description {
  color: #606266;
  margin-bottom: 10px;
}
</style> 