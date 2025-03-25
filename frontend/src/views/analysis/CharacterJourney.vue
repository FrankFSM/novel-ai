<template>
  <div class="journey-container">
    <el-card shadow="never">
      <template #header>
        <div class="page-header">
          <div class="title-with-back">
            <el-button 
              type="text" 
              @click="navigateToCharacterList"
              icon="ArrowLeft"
            >
              返回列表
            </el-button>
            <h2>角色旅程分析</h2>
          </div>
          <div class="header-actions">
            <el-select 
              v-model="selectedNovel" 
              placeholder="请选择小说" 
              @change="handleNovelChange"
              :loading="novelStore.loading"
              class="select-with-label"
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
              class="select-with-label"
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
        v-else-if="!characterJourney" 
        description="点击上方按钮生成角色旅程"
      >
        <el-button type="primary" @click="generateJourney">生成角色旅程</el-button>
      </el-empty>
      
      <!-- 角色旅程内容 -->
      <div v-else class="journey-content">
        <!-- 角色基本信息卡片 -->
        <el-card class="character-info-card">
          <!-- 加载中状态 -->
          <el-skeleton :loading="!characterJourney.character" animated>
            <template #template>
              <div style="display: flex; align-items: center; gap: 20px;">
                <el-skeleton-item variant="circle" style="width: 80px; height: 80px;" />
                <div style="flex: 1;">
                  <el-skeleton-item variant="text" style="width: 30%; height: 20px;" />
                  <el-skeleton-item variant="text" style="width: 70%; margin-top: 15px" />
                </div>
              </div>
            </template>
            
            <template #default>
              <div class="character-info">
                <div class="character-avatar">
                  <el-avatar :size="80" :src="characterAvatar"></el-avatar>
                </div>
                <div class="character-details">
                  <h3 class="character-name">
                    {{ characterJourney.character?.name || '未知角色' }}
                    <el-tag v-if="characterJourney.character?.is_main" type="danger" size="small">主角</el-tag>
                  </h3>
                  <div class="character-description">
                    {{ characterJourney.character?.description || '暂无描述' }}
                  </div>
                  <div class="character-aliases" v-if="characterJourney.character?.alias && characterJourney.character.alias.length">
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
                    <div class="stat-value">{{ characterJourney.stats?.chapters_count || 0 }}</div>
                    <div class="stat-label">出场章节</div>
                  </div>
                  <div class="stat-item">
                    <div class="stat-value">{{ characterJourney.stats?.events_count || 0 }}</div>
                    <div class="stat-label">相关事件</div>
                  </div>
                  <div class="stat-item">
                    <div class="stat-value">{{ characterJourney.stats?.relationships_count || 0 }}</div>
                    <div class="stat-label">人物关系</div>
                  </div>
                </div>
              </div>
            </template>
          </el-skeleton>
        </el-card>
        
        <!-- 旅程可视化部分 -->
        <div class="journey-visualization">
          <el-tabs v-model="activeTab">
            <!-- 发展阶段标签页 -->
            <el-tab-pane label="发展阶段" name="stages">
              <div class="stages-container">
                <el-empty v-if="!characterJourney.stages || !characterJourney.stages.length" description="暂无发展阶段数据" />
                <el-steps v-else :active="characterJourney.stages.length" finish-status="success" :space="200" direction="vertical">
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
                <el-empty v-if="!characterJourney.key_events || !characterJourney.key_events.length" description="暂无关键事件数据" />
                <el-timeline v-else>
                  <el-timeline-item
                    v-for="(event, index) in characterJourney.key_events"
                    :key="event.id || `event-${index}`"
                    :timestamp="`第${event.chapter_id || '?'}章`"
                    :type="getEventType(event)"
                    :color="getEventColor(event)"
                    placement="top"
                  >
                    <div class="event-card">
                      <h4>{{ event.name || '未命名事件' }}</h4>
                      <p>{{ event.description || '暂无描述' }}</p>
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
                <el-empty v-if="!characterJourney.emotions || !characterJourney.emotions.length" description="暂无情感变化数据" />
                <div v-else ref="emotionChartRef" class="emotion-chart"></div>
              </div>
            </el-tab-pane>
            
            <!-- 人物关系标签页 -->
            <el-tab-pane label="人物关系" name="relationships">
              <div class="relationships-container">
                <el-empty v-if="!characterJourney.relationships || !characterJourney.relationships.length" description="暂无人物关系数据" />
                <div v-else class="relationship-list">
                  <el-card 
                    v-for="(relation, index) in characterJourney.relationships" 
                    :key="relation.id || `relation-${index}`"
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
                          <span class="character-name">{{ characterJourney.character?.name || '未知角色' }}</span>
                          <el-tag size="small" :type="getRelationTagType(relation.relation_type)">
                            {{ relation.relation_type || '未知关系' }}
                          </el-tag>
                          <span class="target-name">{{ relation.target_character_name || '未知角色' }}</span>
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
import { ref, computed, onMounted, nextTick, watch, onUnmounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useNovelStore } from '@/store/novel'
import { useAnalysisStore } from '@/store/analysis'
import { ElMessage } from 'element-plus'
import { ArrowRight, ArrowLeft } from '@element-plus/icons-vue'
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

// 保留计算属性以便在内部使用
const selectedNovelTitle = computed(() => {
  if (!selectedNovel.value) return '';
  const novel = novelStore.novels.find(n => n.id === Number(selectedNovel.value));
  return novel ? novel.title : '';
});

const selectedCharacterName = computed(() => {
  if (!selectedCharacter.value) return '';
  const character = characters.value.find(c => c.id === Number(selectedCharacter.value));
  return character ? character.name : '';
});

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
  // 明确转换为数字类型
  selectedNovel.value = Number(novelId);
  selectedCharacter.value = null;
  analysisStore.reset();
  await loadCharacters(novelId);
  
  // 更新URL参数
  router.replace({
    query: { ...route.query, novelId, characterId: undefined }
  });
}

// 角色选择变化处理
function handleCharacterChange(characterId) {
  // 明确转换为数字类型
  selectedCharacter.value = Number(characterId);
  analysisStore.reset();
  
  // 更新URL参数
  router.replace({
    query: { ...route.query, characterId }
  });
}

// 生成角色旅程 - 增强版，确保显示错误信息
async function generateJourney() {
  if (!selectedNovel.value || !selectedCharacter.value) {
    ElMessage.warning('请先选择小说和角色');
    return;
  }
  
  try {
    console.log(`正在生成角色旅程，小说ID: ${selectedNovel.value}，角色ID: ${selectedCharacter.value}`);
    await analysisStore.fetchCharacterJourney(
      selectedNovel.value,
      selectedCharacter.value
    );
    
    if (analysisStore.characterJourney) {
      ElMessage.success('角色旅程生成成功');
    } else if (analysisStore.error) {
      ElMessage.error(`生成失败: ${analysisStore.error}`);
    }
  } catch (error) {
    console.error('生成角色旅程出错:', error);
    ElMessage.error(`生成角色旅程失败: ${error.message || '未知错误'}`);
  }
}

// 渲染情感变化图表
function renderEmotionChart() {
  if (!emotionChartRef.value || !characterJourney.value?.emotions || !characterJourney.value.emotions.length) {
    console.log('[角色旅程图表] 没有可用的情感数据或图表容器不存在，跳过渲染');
    return;
  }
  
  try {
    // 确保DOM已经渲染完成
    nextTick(() => {
      try {
        console.log('[角色旅程图表] 开始渲染情感图表');
        // 处理可能存在的旧图表
        if (emotionChart.value) {
          console.log('[角色旅程图表] 销毁旧图表实例');
          emotionChart.value.dispose();
          emotionChart.value = null;
        }
        
        // 初始化图表
        console.log('[角色旅程图表] 创建新图表实例');
        emotionChart.value = echarts.init(emotionChartRef.value);
        
        const emotions = characterJourney.value.emotions;
        console.log(`[角色旅程图表] 数据点数量: ${emotions.length}`);
        
        const options = {
          title: {
            text: '角色情感变化趋势',
            left: 'center'
          },
          tooltip: {
            trigger: 'axis',
            formatter: function(params) {
              return `第${params[0].name}章<br/>${params[0].marker}${params[0].seriesName}: ${params[0].value}`;
            }
          },
          grid: {
            left: '5%',
            right: '5%',
            bottom: '10%',
            containLabel: true
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
        };
        
        console.log('[角色旅程图表] 设置图表选项');
        emotionChart.value.setOption(options);
        
        // 添加窗口大小调整监听，以确保图表响应式调整大小
        const resizeHandler = () => {
          if (emotionChart.value) {
            console.log('[角色旅程图表] 调整图表大小');
            emotionChart.value.resize();
          }
        };
        
        window.removeEventListener('resize', resizeHandler);
        window.addEventListener('resize', resizeHandler);
        
        console.log('[角色旅程图表] 图表渲染完成');
      } catch (innerError) {
        console.error('[角色旅程图表] 渲染过程中出错:', innerError);
      }
    });
  } catch (error) {
    console.error('[角色旅程图表] 渲染情感图表失败:', error);
  }
}

// 确保组件销毁时清理图表资源
onUnmounted(() => {
  if (emotionChart.value) {
    console.log('[角色旅程图表] 组件卸载，销毁图表');
    emotionChart.value.dispose();
    emotionChart.value = null;
  }
  // 移除所有resize事件监听器
  window.removeEventListener('resize', () => {});
});

// 导航到角色列表
function navigateToCharacterList() {
  if (selectedNovel.value) {
    router.push({
      path: '/analysis/characters/list',
      query: { novelId: selectedNovel.value }
    })
  } else {
    router.push('/analysis/characters/list')
  }
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

.title-with-back {
  display: flex;
  align-items: center;
  gap: 10px;
}

.selected-info {
  display: none;
}

/* 调整下拉框样式 */
.select-with-label {
  min-width: 150px;
}

/* 确保下拉框中的文本不会被截断 */
:deep(.el-select-dropdown__item) {
  white-space: normal;
  height: auto;
  padding: 8px 20px;
  line-height: 1.5;
}

:deep(.el-input__inner) {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
</style> 