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
                <div v-else>
                  <div class="stages-summary" v-if="characterJourney.journey && characterJourney.journey.summary">
                    <h3>角色旅程概述</h3>
                    <p>{{ characterJourney.journey.summary }}</p>
                  </div>
                  <el-steps :active="characterJourney.stages.length" finish-status="success" :space="220" direction="vertical">
                    <el-step 
                      v-for="(stage, index) in characterJourney.stages" 
                      :key="index"
                      :title="stage.name"
                      :description="stage.description"
                    >
                      <template #icon>
                        <el-avatar :size="40" :src="getStageIcon(index, stage.name)"></el-avatar>
                      </template>
                      <template #description>
                        <div class="stage-details">
                          <p>{{ stage.description }}</p>
                          <div class="stage-chapter" v-if="stage.start_chapter && stage.end_chapter">
                            <el-tag size="small" effect="plain">第{{ stage.start_chapter }}章 - 第{{ stage.end_chapter }}章</el-tag>
                          </div>
                          <div class="stage-events" v-if="stage.key_events && stage.key_events.length">
                            <div class="stage-events-title">关键事件：</div>
                            <el-tag 
                              v-for="event in stage.key_events" 
                              :key="event"
                              size="small"
                              effect="light"
                              style="margin-right: 5px; margin-bottom: 5px;"
                            >
                              {{ event }}
                            </el-tag>
                          </div>
                        </div>
                      </template>
                    </el-step>
                  </el-steps>
                </div>
              </div>
            </el-tab-pane>
            
            <!-- 关键事件标签页 -->
            <el-tab-pane label="关键事件" name="events">
              <div class="events-container">
                <el-empty v-if="!characterJourney.key_events || !characterJourney.key_events.length" description="暂无关键事件数据" />
                <div v-else>
                  <div class="events-filter">
                    <div class="filter-item">
                      <span class="filter-label">事件类型：</span>
                      <el-select v-model="eventTypeFilter" placeholder="全部类型" clearable>
                        <el-option
                          v-for="type in eventTypes"
                          :key="type.value"
                          :label="type.label"
                          :value="type.value"
                        />
                      </el-select>
                    </div>
                    <div class="filter-item">
                      <span class="filter-label">排序方式：</span>
                      <el-radio-group v-model="eventSortOrder" size="small">
                        <el-radio-button label="asc">从早到晚</el-radio-button>
                        <el-radio-button label="desc">从晚到早</el-radio-button>
                      </el-radio-group>
                    </div>
                  </div>
                  
                  <el-divider />
                  
                  <el-timeline>
                    <el-timeline-item
                      v-for="(event, index) in filteredAndSortedEvents"
                      :key="event.id || `event-${index}`"
                      :timestamp="`第${event.chapter_id || '?'}章`"
                      :type="getEventType(event)"
                      :color="getEventColor(event)"
                      placement="top"
                      :hollow="event.importance_level === 'minor'"
                    >
                      <div class="event-card">
                        <div class="event-header">
                          <h4>{{ event.name || '未命名事件' }}</h4>
                          <el-tag 
                            size="small" 
                            :type="getEventTagType(event.importance_level)"
                          >
                            {{ getEventImportanceLabel(event.importance_level) }}
                          </el-tag>
                        </div>
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
              </div>
            </el-tab-pane>
            
            <!-- 情感变化标签页 -->
            <el-tab-pane label="情感变化" name="emotions">
              <div class="emotions-container">
                <el-empty v-if="!characterJourney.emotions || !characterJourney.emotions.length" description="暂无情感数据" />
                <div v-else>
                  <div class="emotions-summary">
                    <h3>情感变化概述</h3>
                    <p>角色情感平均值：<span class="emotion-value">{{ characterJourney.stats?.emotion_avg || 0 }}</span></p>
                    <el-alert 
                      v-if="characterJourney.stats?.emotion_avg < 4" 
                      type="warning" 
                      title="角色情感偏低" 
                      description="该角色情感状态整体偏低，在故事中可能经历了较多负面事件。" 
                      show-icon
                      :closable="false"
                    />
                    <el-alert 
                      v-else-if="characterJourney.stats?.emotion_avg > 7" 
                      type="success" 
                      title="角色情感积极" 
                      description="该角色情感状态整体良好，在故事中可能经历了较多积极事件。" 
                      show-icon
                      :closable="false"
                    />
                    <el-alert 
                      v-else 
                      type="info" 
                      title="角色情感平稳" 
                      description="该角色情感状态平稳，经历了起伏的情感变化。" 
                      show-icon
                      :closable="false"
                    />
                  </div>
                  <div ref="emotionChartContainer" class="emotion-chart-container"></div>
                  
                  <div class="emotion-markers">
                    <h4>情感标记点</h4>
                    <div class="markers-list">
                      <div
                        v-for="(emotion, index) in emotionMarkersWithEvents"
                        :key="index"
                        class="marker-item"
                      >
                        <span class="marker-chapter">
                          <el-tag size="small" type="info">第{{ emotion.chapter_id }}章</el-tag>
                        </span>
                        <span class="marker-value" :class="getEmotionValueClass(emotion.value)">
                          {{ Math.round(emotion.value * 10) / 10 }}
                        </span>
                        <span class="marker-event" v-if="emotion.event">
                          <el-popover
                            placement="top"
                            trigger="hover"
                            :content="emotion.event.description"
                          >
                            <template #reference>
                              <el-tag :type="getImportanceType(emotion.event.importance)">
                                {{ emotion.event.name }}
                              </el-tag>
                            </template>
                          </el-popover>
                        </span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </el-tab-pane>
            
            <!-- 人物关系标签页 -->
            <el-tab-pane label="人物关系" name="relationships">
              <div class="relationships-container">
                <el-empty v-if="!characterJourney.relationships || !characterJourney.relationships.length" description="暂无人物关系数据" />
                <div v-else>
                  <div class="relationship-filters">
                    <div class="filter-item">
                      <span class="filter-label">关系类型：</span>
                      <el-select v-model="relationshipTypeFilter" placeholder="全部类型" clearable>
                        <el-option
                          v-for="type in relationshipTypes"
                          :key="type.value"
                          :label="type.label"
                          :value="type.value"
                        />
                      </el-select>
                    </div>
                    <div class="filter-item">
                      <span class="filter-label">排序方式：</span>
                      <el-select v-model="relationshipSortType" placeholder="排序方式">
                        <el-option label="关系重要性" value="importance" />
                        <el-option label="首次出现章节" value="chapter" />
                        <el-option label="角色名称" value="name" />
                      </el-select>
                    </div>
                  </div>
                  
                  <el-divider>
                    <el-tag type="info">共 {{ filteredRelationships.length }} 个角色关系</el-tag>
                  </el-divider>
                  
                  <div class="relationship-groups" v-if="relationshipTypeFilter">
                    <div class="relationship-list">
                      <el-card 
                        v-for="(relation, index) in filteredRelationships" 
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
                            <div class="relationship-strength" v-if="relation.strength">
                              <span class="strength-label">关系强度：</span>
                              <el-progress 
                                :percentage="relation.strength" 
                                :color="getRelationStrengthColor(relation.strength)"
                                :stroke-width="10"
                                :show-text="false"
                              />
                              <span class="strength-value">{{ relation.strength }}%</span>
                            </div>
                          </div>
                        </div>
                      </el-card>
                    </div>
                  </div>
                  
                  <div class="relationship-groups" v-else>
                    <div v-for="(group, groupName) in groupedRelationships" :key="groupName">
                      <h3 class="group-title">
                        <el-tag :type="getRelationTagType(groupName)" effect="plain">{{ groupName }}</el-tag>
                        <span class="group-count">{{ group.length }}个关系</span>
                      </h3>
                      <div class="relationship-list">
                        <el-card 
                          v-for="(relation, index) in group" 
                          :key="relation.id || `${groupName}-${index}`"
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
                                <span class="target-name">{{ relation.target_character_name || '未知角色' }}</span>
                              </div>
                              <div class="relationship-description">
                                {{ relation.description || '暂无描述' }}
                              </div>
                              <div class="relationship-first-chapter" v-if="relation.first_chapter_id">
                                <el-tag size="small" effect="plain">关系建立于第{{ relation.first_chapter_id }}章</el-tag>
                              </div>
                              <div class="relationship-strength" v-if="relation.strength">
                                <span class="strength-label">关系强度：</span>
                                <el-progress 
                                  :percentage="relation.strength" 
                                  :color="getRelationStrengthColor(relation.strength)"
                                  :stroke-width="10"
                                  :show-text="false"
                                />
                                <span class="strength-value">{{ relation.strength }}%</span>
                              </div>
                            </div>
                          </div>
                        </el-card>
                      </div>
                    </div>
                  </div>
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
import * as echarts from 'echarts/core'
import { LineChart } from 'echarts/charts'
import {
  TitleComponent,
  TooltipComponent,
  GridComponent,
  LegendComponent,
  MarkLineComponent,
  MarkPointComponent
} from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'
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
const emotionChartContainer = ref(null)
let emotionChart = null

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

// 关键事件筛选相关
const eventTypeFilter = ref('');
const eventSortOrder = ref('asc');
const eventTypes = [
  { label: '关键转折点', value: 'critical' },
  { label: '重要事件', value: 'major' },
  { label: '普通事件', value: 'normal' },
  { label: '次要事件', value: 'minor' }
];

// 过滤和排序后的事件列表
const filteredAndSortedEvents = computed(() => {
  if (!characterJourney.value?.key_events) return [];
  
  // 先过滤
  let events = characterJourney.value.key_events;
  if (eventTypeFilter.value) {
    events = events.filter(event => event.importance_level === eventTypeFilter.value);
  }
  
  // 再排序
  return events.slice().sort((a, b) => {
    const aChapter = a.chapter_id || 0;
    const bChapter = b.chapter_id || 0;
    return eventSortOrder.value === 'asc' ? aChapter - bChapter : bChapter - aChapter;
  });
});

// 关系筛选相关
const relationshipTypeFilter = ref('');
const relationshipSortType = ref('importance');
const relationshipTypes = [
  { label: '师徒关系', value: '师徒' },
  { label: '朋友关系', value: '朋友' },
  { label: '敌对关系', value: '敌人' },
  { label: '亲人关系', value: '亲人' },
  { label: '爱情关系', value: '恋人' },
  { label: '同门关系', value: '同门' }
];

// 过滤后的关系列表
const filteredRelationships = computed(() => {
  if (!characterJourney.value?.relationships) return [];
  
  let relationships = characterJourney.value.relationships;
  
  // 按类型筛选
  if (relationshipTypeFilter.value) {
    relationships = relationships.filter(relation => 
      relation.relation_type === relationshipTypeFilter.value
    );
  }
  
  // 按选择的方式排序
  return sortRelationships(relationships);
});

// 按关系类型分组
const groupedRelationships = computed(() => {
  if (!characterJourney.value?.relationships) return {};
  
  // 先创建分组
  const groups = {};
  
  // 将关系按类型分组
  characterJourney.value.relationships.forEach(relation => {
    const type = relation.relation_type || '其他';
    if (!groups[type]) {
      groups[type] = [];
    }
    groups[type].push(relation);
  });
  
  // 对每个分组内的关系进行排序
  Object.keys(groups).forEach(type => {
    groups[type] = sortRelationships(groups[type]);
  });
  
  return groups;
});

// 排序关系
function sortRelationships(relationships) {
  return [...relationships].sort((a, b) => {
    if (relationshipSortType.value === 'chapter') {
      return (a.first_chapter_id || 9999) - (b.first_chapter_id || 9999);
    } else if (relationshipSortType.value === 'name') {
      return (a.target_character_name || '').localeCompare(b.target_character_name || '');
    } else { // 默认按重要性
      return (b.strength || 0) - (a.strength || 0);
    }
  });
}

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
  if (newValue === 'emotions' && characterJourney.value && !emotionChart) {
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

// 情感变化图表数据处理
const emotionChartData = computed(() => {
  if (!characterJourney.value?.emotions || !characterJourney.value.emotions.length) {
    return {
      chapters: [],
      values: []
    };
  }

  // 按章节ID排序
  const sortedEmotions = [...characterJourney.value.emotions].sort((a, b) => 
    a.chapter_id - b.chapter_id
  );

  return {
    chapters: sortedEmotions.map(e => `第${e.chapter_id}章`),
    values: sortedEmotions.map(e => e.value)
  };
});

// 情感标记点与事件关联
const emotionMarkersWithEvents = computed(() => {
  if (!characterJourney.value?.emotions || !characterJourney.value?.journey?.events) {
    return [];
  }

  const eventsByChapter = {};
  // 按章节ID组织事件，只保留每章最重要的事件
  characterJourney.value.journey.events.forEach(event => {
    if (!event.chapter_id) return;
    
    if (!eventsByChapter[event.chapter_id] || 
        eventsByChapter[event.chapter_id].importance < event.importance) {
      eventsByChapter[event.chapter_id] = event;
    }
  });

  // 为情感数据关联事件
  return characterJourney.value.emotions.map(emotion => {
    return {
      ...emotion,
      event: eventsByChapter[emotion.chapter_id] || null
    };
  }).sort((a, b) => a.chapter_id - b.chapter_id);
});

// 情感值样式
const getEmotionValueClass = (value) => {
  if (value < 4) return 'emotion-negative';
  if (value > 7) return 'emotion-positive';
  return 'emotion-neutral';
};

// 事件重要性对应的标签类型
const getImportanceType = (importance) => {
  if (!importance) return 'info';
  if (importance >= 5) return 'danger';
  if (importance >= 4) return 'warning';
  if (importance >= 3) return 'success';
  return 'info';
};

// 渲染情感变化图表
const renderEmotionChart = () => {
  if (!emotionChartContainer.value || !characterJourney.value?.emotions) return;
  
  if (emotionChart) {
    emotionChart.dispose();
  }
  
  const data = emotionChartData.value;
  
  // 标记关键事件点
  const markPoints = [];
  emotionMarkersWithEvents.value.forEach((item, index) => {
    if (item.event && item.event.importance >= 4) {
      markPoints.push({
        name: item.event.name,
        value: item.event.name,
        xAxis: index,
        yAxis: item.value,
        itemStyle: {
          color: item.event.importance >= 5 ? '#F56C6C' : '#E6A23C'
        },
        tooltilp: {
          formatter: function(params) {
            return `${params.name}<br/>${item.event.description}`;
          }
        }
      });
    }
  });
  
  // 计算平均值线
  const avgValue = characterJourney.value.stats?.emotion_avg || 0;
  
  emotionChart = echarts.init(emotionChartContainer.value);
  emotionChart.setOption({
    title: {
      text: '角色情感变化曲线',
      left: 'center'
    },
    tooltip: {
      trigger: 'axis',
      formatter: function(params) {
        const dataIndex = params[0].dataIndex;
        const emotion = emotionMarkersWithEvents.value[dataIndex];
        let tip = params[0].name + '<br/>情感值: ' + params[0].value.toFixed(1);
        
        if (emotion && emotion.event) {
          tip += '<br/>事件: ' + emotion.event.name;
          if (emotion.event.description) {
            tip += '<br/>描述: ' + emotion.event.description;
          }
        }
        
        return tip;
      }
    },
    xAxis: {
      type: 'category',
      data: data.chapters,
      axisLabel: {
        interval: Math.ceil(data.chapters.length / 10)  // 控制显示的密度
      }
    },
    yAxis: {
      type: 'value',
      min: 0,
      max: 10,
      name: '情感值',
      nameLocation: 'end',
      nameTextStyle: {
        padding: [0, 0, 0, -30]  // 调整位置
      },
      axisLabel: {
        formatter: '{value}'
      }
    },
    series: [
      {
        name: '情感值',
        type: 'line',
        data: data.values,
        smooth: true,
        symbolSize: 8,
        lineStyle: {
          width: 3
        },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(128, 255, 165, 0.3)' },
            { offset: 1, color: 'rgba(1, 191, 236, 0.1)' }
          ])
        },
        markLine: {
          data: [
            {
              name: '平均值',
              yAxis: avgValue,
              lineStyle: {
                color: '#409EFF',
                type: 'dashed'
              },
              label: {
                formatter: '平均情感值: {c}'
              }
            }
          ]
        },
        markPoint: {
          data: markPoints
        }
      }
    ],
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      containLabel: true
    }
  });
};

// 监听数据变化和窗口大小变化，重新渲染图表
watch(() => characterJourney.value, async () => {
  await nextTick();
  if (activeTab.value === 'emotions') {
    renderEmotionChart();
  }
}, { deep: true });

watch(() => activeTab.value, async (newValue) => {
  if (newValue === 'emotions') {
    await nextTick();
    renderEmotionChart();
  }
});

// 处理窗口大小变化
const handleResize = () => {
  if (emotionChart) {
    emotionChart.resize();
  }
};

// 组件挂载和卸载时的处理
onMounted(() => {
  window.addEventListener('resize', handleResize);
});

onUnmounted(() => {
  window.removeEventListener('resize', handleResize);
  if (emotionChart) {
    emotionChart.dispose();
    emotionChart = null;
  }
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

// 获取事件标签类型
function getEventTagType(importanceLevel) {
  const typeMap = {
    'critical': 'danger',
    'major': 'warning',
    'normal': '',
    'minor': 'info'
  }
  
  return typeMap[importanceLevel] || ''
}

// 获取事件重要性标签文本
function getEventImportanceLabel(importanceLevel) {
  const labelMap = {
    'critical': '关键转折点',
    'major': '重要事件',
    'normal': '普通事件',
    'minor': '次要事件'
  }
  
  return labelMap[importanceLevel] || '未知类型'
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

// 获取关系强度颜色
function getRelationStrengthColor(strength) {
  // 根据关系强度返回不同颜色
  if (strength >= 80) return '#67C23A'; // 强关系
  if (strength >= 50) return '#409EFF'; // 中等关系
  if (strength >= 30) return '#E6A23C'; // 一般关系
  return '#909399'; // 较弱关系
}

// 获取阶段图标 - 优化版
function getStageIcon(index, stageName = '') {
  // 根据阶段名称选择合适的图标
  const stageTypes = {
    '初登场': 'bottts/stage-intro.svg',
    '成长': 'bottts/stage-growth.svg',
    '转折': 'bottts/stage-turning.svg',
    '高潮': 'bottts/stage-climax.svg',
    '结局': 'bottts/stage-finale.svg'
  };
  
  // 判断阶段名称是否包含特定关键词
  let iconType = 'bottts/stage-default.svg';
  for (const [keyword, icon] of Object.entries(stageTypes)) {
    if (stageName.includes(keyword)) {
      iconType = icon;
      break;
    }
  }
  
  // 如果没有匹配，使用默认顺序图标
  if (iconType === 'bottts/stage-default.svg') {
    const defaultIcons = [
      'bottts/stage1.svg',
      'bottts/stage2.svg',
      'bottts/stage3.svg',
      'bottts/stage4.svg',
      'bottts/stage5.svg'
    ];
    iconType = defaultIcons[index % defaultIcons.length];
  }
  
  return `https://avatars.dicebear.com/api/${iconType}`;
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

.stages-summary {
  background-color: #f5f7fa;
  border-left: 4px solid #409EFF;
  padding: 15px;
  margin-bottom: 20px;
  border-radius: 4px;
}

.stages-summary h3 {
  margin-top: 0;
  margin-bottom: 10px;
  color: #303133;
}

.stages-summary p {
  color: #606266;
  line-height: 1.6;
  margin: 0;
}

.stage-details {
  padding: 5px 0;
}

.stage-chapter {
  margin: 10px 0;
}

.stage-events {
  margin-top: 10px;
}

.stage-events-title {
  font-size: 13px;
  color: #909399;
  margin-bottom: 5px;
}

:deep(.el-step__description) {
  max-width: 100%;
  width: 100%;
  padding-right: 30px;
  box-sizing: border-box;
}

:deep(.el-step__icon) {
  background-color: transparent !important;
}

.events-container {
  padding: 10px;
}

.events-filter {
  display: flex;
  flex-wrap: wrap;
  justify-content: space-between;
  margin-bottom: 10px;
  gap: 15px;
}

.filter-item {
  display: flex;
  align-items: center;
  gap: 8px;
}

.filter-label {
  font-size: 14px;
  color: #606266;
}

.event-card {
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

.event-header h4 {
  margin: 0;
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
  padding: 20px;
}

.emotions-summary {
  margin-bottom: 20px;
}

.emotion-chart-container {
  width: 100%;
  height: 400px;
  margin-bottom: 30px;
}

.emotion-markers {
  margin-top: 20px;
}

.markers-list {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-top: 10px;
}

.marker-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 5px 10px;
  border-radius: 4px;
  background-color: #f5f7fa;
}

.emotion-positive {
  color: #67C23A;
  font-weight: bold;
}

.emotion-negative {
  color: #F56C6C;
  font-weight: bold;
}

.emotion-neutral {
  color: #409EFF;
  font-weight: bold;
}

.emotion-value {
  font-size: 18px;
  font-weight: bold;
  color: #409EFF;
}

.relationships-container {
  padding: 10px;
}

.relationship-filters {
  display: flex;
  flex-wrap: wrap;
  justify-content: space-between;
  margin-bottom: 10px;
  gap: 15px;
}

.group-title {
  margin-top: 15px;
  margin-bottom: 10px;
  font-size: 16px;
  display: flex;
  align-items: center;
  gap: 10px;
}

.group-count {
  font-size: 14px;
  color: #909399;
  font-weight: normal;
}

.relationship-list {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 15px;
  margin-bottom: 20px;
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

.relationship-first-chapter {
  margin-bottom: 10px;
}

.relationship-strength {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 0 10px;
}

.strength-label {
  color: #909399;
  font-size: 13px;
  white-space: nowrap;
}

.strength-value {
  color: #606266;
  font-size: 13px;
  white-space: nowrap;
}

:deep(.el-progress) {
  flex: 1;
  margin: 0;
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