<template>
  <div class="timeline-container">
    <el-card shadow="never">
      <template #header>
        <div class="page-header">
          <h2>情节时间线</h2>
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
              placeholder="筛选角色（可选）"
              clearable
              @change="handleCharacterChange"
              :disabled="!selectedNovel || !characters.length"
            >
              <el-option
                v-for="character in characters"
                :key="character.id"
                :label="character.name"
                :value="character.id"
              />
            </el-select>
            
            <el-button-group>
              <el-tooltip content="按章节顺序">
                <el-button 
                  :type="timelineMode === 'chapter' ? 'primary' : ''" 
                  @click="timelineMode = 'chapter'"
                  :disabled="!selectedNovel"
                >
                  <el-icon><Menu /></el-icon>
                </el-button>
              </el-tooltip>
              
              <el-tooltip content="按时间顺序">
                <el-button 
                  :type="timelineMode === 'time' ? 'primary' : ''" 
                  @click="timelineMode = 'time'"
                  :disabled="!selectedNovel"
                >
                  <el-icon><Calendar /></el-icon>
                </el-button>
              </el-tooltip>
            </el-button-group>
            
            <el-button 
              type="primary" 
              @click="generateTimeline" 
              :disabled="!selectedNovel"
              :loading="analysisStore.loading"
            >
              生成时间线
            </el-button>
          </div>
        </div>
      </template>
      
      <!-- 尚未选择小说的提示 -->
      <el-empty 
        v-if="!selectedNovel" 
        description="请从上方选择一本小说以查看情节时间线"
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
          <el-button type="primary" @click="generateTimeline">重试</el-button>
        </template>
      </el-result>
      
      <!-- 尚未生成时间线的提示 -->
      <el-empty 
        v-else-if="!analysisStore.timeline" 
        description="点击上方按钮生成情节时间线"
      >
        <el-button type="primary" @click="generateTimeline">生成时间线</el-button>
      </el-empty>
      
      <!-- 时间线展示 -->
      <div v-else class="timeline-content">
        <div class="timeline-filter">
          <el-tag
            v-for="(tag, index) in availableTags"
            :key="index"
            :type="activeTags.includes(tag) ? '' : 'info'"
            effect="plain"
            class="filter-tag"
            @click="toggleTag(tag)"
          >
            {{ tag }}
          </el-tag>
        </div>
        
        <el-timeline>
          <el-timeline-item
            v-for="event in filteredEvents"
            :key="event.id"
            :timestamp="formatTimestamp(event)"
            :type="getEventType(event)"
            :color="getEventColor(event)"
            placement="top"
            :hollow="event.importance < 4"
          >
            <div class="timeline-event">
              <div class="event-header">
                <span class="event-title">{{ event.name }}</span>
                <div class="event-indicators">
                  <el-tag v-if="event.importance >= 4" size="small" type="danger">重要</el-tag>
                  <el-tag v-if="event.location" size="small" type="warning">{{ event.location.name }}</el-tag>
                </div>
              </div>
              
              <div class="event-body">
                <p class="event-description">{{ event.description }}</p>
                
                <div v-if="event.participants && event.participants.length > 0" class="event-participants">
                  <span class="label">相关角色：</span>
                  <el-tag
                    v-for="participant in event.participants"
                    :key="participant.character_id"
                    size="small"
                    style="margin-right: 5px"
                  >
                    {{ participant.character_name }}{{ participant.role ? `(${participant.role})` : '' }}
                  </el-tag>
                </div>
                
                <div class="event-actions">
                  <el-button link type="primary" size="small" @click="navigateToChapter(event.chapter_id)">
                    查看原文
                  </el-button>
                </div>
              </div>
            </div>
          </el-timeline-item>
        </el-timeline>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useNovelStore } from '@/store/novel'
import { useAnalysisStore } from '@/store/analysis'
import { ElMessage } from 'element-plus'
import { Menu, Calendar } from '@element-plus/icons-vue'

const router = useRouter()
const route = useRoute()
const novelStore = useNovelStore()
const analysisStore = useAnalysisStore()

// 本地状态
const selectedNovel = ref(null)
const selectedCharacter = ref(null)
const characters = ref([])
const timelineMode = ref('chapter')  // 'chapter' 或 'time'
const activeTags = ref(['重要事件', '战斗', '情感', '发现'])

// 从路由参数中获取小说ID和角色ID
onMounted(async () => {
  if (novelStore.novels.length === 0) {
    await novelStore.fetchNovels()
  }
  
  const novelId = Number(route.query.novelId)
  const characterId = Number(route.query.characterId)
  
  if (novelId && !isNaN(novelId) && novelStore.novels.find(n => n.id === novelId)) {
    selectedNovel.value = novelId
    await loadCharacters(novelId)
    
    if (characterId && !isNaN(characterId) && characters.value.find(c => c.id === characterId)) {
      selectedCharacter.value = characterId
    }
    
    // 自动生成时间线
    generateTimeline()
  }
})

// 计算属性：可用标签
const availableTags = computed(() => {
  if (!analysisStore.timeline) return ['重要事件', '战斗', '情感', '发现', '旅行']
  
  const tags = new Set(['重要事件'])
  
  analysisStore.timeline.events.forEach(event => {
    if (event.tags && event.tags.length) {
      event.tags.forEach(tag => tags.add(tag))
    }
  })
  
  return Array.from(tags)
})

// 计算属性：过滤后的事件
const filteredEvents = computed(() => {
  if (!analysisStore.timeline) return []
  
  let events = analysisStore.timeline.events
  
  // 根据模式排序
  if (timelineMode.value === 'chapter') {
    events = [...events].sort((a, b) => {
      // 先按章节排序
      if (a.chapter_id !== b.chapter_id) {
        return a.chapter_id - b.chapter_id
      }
      // 同一章节内按重要性排序
      return b.importance - a.importance
    })
  } else {
    events = [...events].sort((a, b) => {
      // 如果有明确的时间表述，按时间排序
      if (a.time_description && b.time_description) {
        return a.time_position - b.time_position
      }
      // 否则按章节排序
      return a.chapter_id - b.chapter_id
    })
  }
  
  // 过滤标签
  if (activeTags.value.length > 0) {
    events = events.filter(event => {
      // 重要事件标签特殊处理
      if (activeTags.value.includes('重要事件') && event.importance >= 4) return true
      
      // 检查其他标签
      if (event.tags && event.tags.some(tag => activeTags.value.includes(tag))) return true
      
      return false
    })
  }
  
  // 根据角色过滤
  if (selectedCharacter.value) {
    events = events.filter(event => 
      event.participants && event.participants.some(p => p.character_id === selectedCharacter.value)
    )
  }
  
  return events
})

// 加载角色列表
async function loadCharacters(novelId) {
  try {
    // TODO: 实际项目中应从API获取
    // const response = await novelApi.getNovelCharacters(novelId)
    // characters.value = response.data
    
    // 模拟数据
    characters.value = generateMockCharacters()
  } catch (error) {
    ElMessage.error('获取角色列表失败')
    characters.value = []
  }
}

// 小说选择变化处理
async function handleNovelChange(novelId) {
  selectedCharacter.value = null
  analysisStore.reset()
  await loadCharacters(novelId)
  
  // 更新URL参数
  router.replace({
    query: { ...route.query, novelId }
  })
}

// 角色选择变化处理
function handleCharacterChange(characterId) {
  // 更新URL参数
  if (characterId) {
    router.replace({
      query: { ...route.query, characterId }
    })
  } else {
    const { characterId, ...query } = route.query
    router.replace({ query })
  }
}

// 生成时间线
async function generateTimeline() {
  if (!selectedNovel.value) return
  
  try {
    await analysisStore.fetchTimeline(
      selectedNovel.value,
      selectedCharacter.value
    )
  } catch (error) {
    ElMessage.error('生成时间线失败')
  }
}

// 切换标签过滤
function toggleTag(tag) {
  if (activeTags.value.includes(tag)) {
    activeTags.value = activeTags.value.filter(t => t !== tag)
  } else {
    activeTags.value.push(tag)
  }
}

// 导航到小说列表
function navigateToNovelList() {
  router.push('/novels/list')
}

// 导航到章节
function navigateToChapter(chapterId) {
  // TODO: 实际项目中应导航到章节预览页面
  ElMessage.info(`查看第${chapterId}章原文`)
}

// 格式化时间戳
function formatTimestamp(event) {
  if (timelineMode.value === 'time' && event.time_description) {
    return event.time_description
  } else {
    return `第${event.chapter_id}章`
  }
}

// 获取事件类型（颜色）
function getEventType(event) {
  if (event.importance >= 5) return 'danger'
  if (event.importance >= 4) return 'warning'
  if (event.importance >= 3) return 'primary'
  return 'info'
}

// 获取事件颜色
function getEventColor(event) {
  // 通过事件类型决定颜色
  if (event.tags) {
    if (event.tags.includes('战斗')) return '#F56C6C'
    if (event.tags.includes('情感')) return '#FC9DB1'
    if (event.tags.includes('发现')) return '#E6A23C'
    if (event.tags.includes('旅行')) return '#409EFF'
  }
  return ''
}

// 生成模拟角色数据
function generateMockCharacters() {
  const count = 10
  const characters = []
  
  const names = ['林远', '沈清雪', '张天志', '李墨', '王霜', '赵云', '钱多多', '孙小圣', '周天', '吴明']
  
  for (let i = 0; i < count; i++) {
    characters.push({
      id: i + 1,
      name: names[i % names.length]
    })
  }
  
  return characters
}
</script>

<style scoped>
.timeline-container {
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

.timeline-content {
  margin-top: 20px;
}

.timeline-filter {
  margin-bottom: 20px;
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.filter-tag {
  cursor: pointer;
}

.timeline-event {
  background-color: #f5f7fa;
  border-radius: 4px;
  padding: 12px;
  margin-bottom: 10px;
}

.event-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.event-title {
  font-weight: bold;
  font-size: 16px;
}

.event-indicators {
  display: flex;
  gap: 5px;
}

.event-description {
  margin-top: 0;
  margin-bottom: 10px;
  color: #606266;
  line-height: 1.5;
}

.event-participants {
  margin-bottom: 10px;
  display: flex;
  align-items: center;
  flex-wrap: wrap;
}

.event-participants .label {
  color: #909399;
  margin-right: 5px;
}

.event-actions {
  display: flex;
  justify-content: flex-end;
}
</style> 