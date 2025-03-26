<template>
  <div class="location-detail-container">
    <el-card shadow="never" v-loading="loading">
      <template #header>
        <div class="page-header">
          <div class="header-left">
            <el-button type="text" @click="goBack">
              <el-icon><ArrowLeft /></el-icon> 返回
            </el-button>
            <h2 v-if="locationDetail && locationDetail.name">{{ locationDetail.name }} - 详情</h2>
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
      <div v-else-if="locationDetail" class="location-detail-content">
        <!-- 基本信息卡片 -->
        <el-row :gutter="20">
          <el-col :xs="24" :sm="24" :md="8" :lg="8" :xl="8">
            <el-card shadow="hover" class="info-card">
              <div v-if="locationDetail" class="location-avatar">
                <el-icon :size="50"><component :is="getLocationIcon(locationDetail.id)" /></el-icon>
              </div>
              <h3 class="location-title">{{ locationDetail ? (locationDetail.name || '未命名地点') : '加载中...' }}</h3>
              <div class="location-description">
                {{ locationDetail ? (locationDetail.description || '暂无描述') : '' }}
              </div>
              
              <div class="location-hierarchy" v-if="locationDetail && locationDetail.parent">
                <div class="hierarchy-label">所属地点：</div>
                <el-tag 
                  type="info" 
                  @click="viewParentLocation(locationDetail.parent.id)"
                  style="cursor: pointer;"
                >
                  {{ locationDetail.parent.name || '未命名父地点' }}
                </el-tag>
              </div>
              
              <div v-if="locationDetail && locationDetail.sub_locations && locationDetail.sub_locations.length" class="sub-locations">
                <div class="sub-label">子地点：</div>
                <div class="sub-tags">
                  <el-tag 
                    v-for="(sub, index) in locationDetail.sub_locations" 
                    :key="sub.id || index"
                    @click="viewSubLocation(sub.id)"
                    style="cursor: pointer; margin: 2px 4px;"
                  >
                    {{ sub.name || '未命名地点' }}
                  </el-tag>
                </div>
              </div>
              
              <div class="location-stats">
                <div class="stat-item">
                  <div class="stat-label">事件数量</div>
                  <div class="stat-value">{{ locationDetail && locationDetail.events ? locationDetail.events.length : 0 }}</div>
                </div>
                <div class="stat-item">
                  <div class="stat-label">相关角色</div>
                  <div class="stat-value">{{ locationDetail && locationDetail.characters ? locationDetail.characters.length : 0 }}</div>
                </div>
                <div class="stat-item">
                  <div class="stat-label">子地点</div>
                  <div class="stat-value">{{ locationDetail && locationDetail.sub_locations ? locationDetail.sub_locations.length : 0 }}</div>
                </div>
              </div>

              <!-- 时间线按钮 放在地点基本信息卡片底部 -->
              <div class="flex justify-end mt-4">
                <n-button type="primary" ghost @click="showTimeline = !showTimeline">
                  {{ showTimeline ? '隐藏时间线' : '查看时间线' }}
                  <template #icon>
                    <el-icon><timer /></el-icon>
                  </template>
                </n-button>
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
            <!-- 在相关角色卡片前添加时间线卡片 -->
            <n-card v-if="showTimeline" class="mb-6" :bordered="false">
              <template #header>
                <div class="flex items-center justify-between">
                  <div class="flex items-center">
                    <el-icon class="mr-2 text-xl"><timer /></el-icon>
                    <span class="text-lg font-medium">时间线</span>
                  </div>
                  <div class="flex items-center">
                    <n-button-group>
                      <n-button 
                        size="small" 
                        :type="timelineMode === 'chapter' ? 'primary' : 'default'"
                        @click="timelineMode = 'chapter'">
                        按章节
                      </n-button>
                      <n-button 
                        size="small" 
                        :type="timelineMode === 'time' ? 'primary' : 'default'"
                        @click="timelineMode = 'time'">
                        按时间
                      </n-button>
                    </n-button-group>
                  </div>
                </div>
              </template>
              
              <div class="my-2">
                <n-space>
                  <n-tag 
                    v-for="tag in availableTags" 
                    :key="tag"
                    :type="activeTags.includes(tag) ? 'primary' : 'default'"
                    :bordered="false"
                    style="cursor: pointer"
                    @click="toggleTag(tag)">
                    {{ tag }}
                  </n-tag>
                </n-space>
              </div>
              
              <n-skeleton v-if="timelineLoading" :repeat="5" />
              
              <div v-else-if="!timeline || !timeline.events || timeline.events.length === 0" class="py-10 text-center">
                <n-empty description="暂无时间线数据" size="small">
                  <template #extra>
                    <n-button size="small" @click="loadLocationTimeline">重新加载</n-button>
                  </template>
                </n-empty>
              </div>
              
              <n-timeline v-else>
                <n-timeline-item
                  v-for="event in filteredEvents"
                  :key="event.id"
                  :type="getEventType(event.importance)"
                  :title="formatTimestamp(event)"
                  :content="event.name"
                  :color="getEventColor(event.importance)"
                  :time="false">
                  <template #meta>
                    <div class="mb-1">
                      <n-tag 
                        v-for="tag in event.tags || []" 
                        :key="tag" 
                        size="small" 
                        class="mr-1">
                        {{ tag }}
                      </n-tag>
                    </div>
                  </template>
                  
                  <div class="text-gray-600 my-1">{{ event.description }}</div>
                  
                  <div v-if="event.characters && event.characters.length > 0" class="mt-2">
                    <n-avatar-group :options="getEventCharacters(event)" :max="5" />
                  </div>
                </n-timeline-item>
              </n-timeline>
            </n-card>
            
            <!-- 地点相关事件 -->
            <el-card shadow="hover" class="events-card">
              <template #header>
                <div class="card-header">
                  <h3>地点相关事件</h3>
                </div>
              </template>
              
              <el-empty v-if="!locationDetail || !locationDetail.events || !locationDetail.events.length" description="暂无相关事件" />
              
              <el-timeline v-else>
                <el-timeline-item
                  v-for="(event, index) in locationDetail.events"
                  :key="event.id || index"
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
              
              <el-empty v-if="!locationDetail || !locationDetail.characters || !locationDetail.characters.length" description="暂无相关角色" />
              
              <div v-else class="character-list">
                <el-row :gutter="12">
                  <el-col 
                    v-for="(character, index) in locationDetail.characters" 
                    :key="character.id || index"
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
                        <div class="character-name">{{ character.name || '未命名角色' }}</div>
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
import { ref, onMounted, computed, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import {
  ArrowLeft,
  ArrowUp,
  HomeFilled,
  Location,
  MapLocation,
  School,
  OfficeBuilding,
  House,
  Notebook,
  ShoppingBag,
  Edit,
  Refresh,
  Calendar,
  Timer,
  Menu
} from '@element-plus/icons-vue'
import locationApi from '@/api/modules/location'

// 导入Naive UI组件
import {
  NCard,
  NButton,
  NButtonGroup,
  NSkeleton,
  NEmpty,
  NTimeline,
  NTimelineItem,
  NTag,
  NSpace,
  NAvatarGroup
} from 'naive-ui'

const router = useRouter()
const route = useRoute()

// 定义Props
const props = defineProps({
  locationId: {
    type: [Number, String],
    required: true
  },
  novelId: {
    type: [Number, String],
    required: true
  }
})

// 将字符串ID转为数字
const locationIdNum = computed(() => {
  const id = Number(props.locationId);
  console.log('计算属性处理locationId:', props.locationId, '→', id);
  return id;
});

const novelIdNum = computed(() => {
  const id = Number(props.novelId);
  console.log('计算属性处理novelId:', props.novelId, '→', id);
  return id;
});

// 本地状态
const locationDetail = ref(null)
const locationSignificance = ref(null)
const loading = ref(false)
const showTimeline = ref(false)
const timeline = ref(null)
const timelineLoading = ref(false)
const timelineMode = ref('chapter')  // 'chapter' 或 'time'
const activeTags = ref(['重要事件', '战斗', '情感', '发现'])

// 处理生命周期
onMounted(async () => {
  // 初始化默认值以防止渲染错误
  locationDetail.value = {
    id: 0,
    name: '加载中...',
    description: '',
    events: [],
    characters: [],
    sub_locations: []
  }
  
  // 使用路由参数替代props，确保每次都从路由获取最新的ID
  const routeLocationId = Number(route.params.locationId);
  const routeNovelId = Number(route.query.novelId);
  
  console.log('LocationDetail组件挂载，路由参数:', {
    locationId: routeLocationId,
    novelId: routeNovelId,
    propsLocationId: props.locationId,
    propsNovelId: props.novelId
  });
  
  // 优先使用路由参数，如果没有则回退到props
  const locationId = routeLocationId || locationIdNum.value;
  const novelId = routeNovelId || novelIdNum.value;
  
  if (locationId) {
    await loadLocationDetails(locationId);
    await loadLocationSignificance(locationId);
  } else {
    ElMessage.warning('未提供有效的地点ID')
  }
})

// 监听时间线显示状态
watch(showTimeline, async (newVal) => {
  if (newVal && !timeline.value) {
    // 获取当前路由参数，确保使用最新的ID
    const routeLocationId = Number(route.params.locationId);
    const routeNovelId = Number(route.query.novelId);
    
    // 使用路由参数优先，如果没有则使用props
    const locationId = routeLocationId || locationIdNum.value;
    const novelId = routeNovelId || novelIdNum.value;
    
    await loadLocationTimeline(locationId, novelId);
  }
})

// 加载地点详情
async function loadLocationDetails(overrideLocationId) {
  // 优先使用传入的ID，否则使用计算属性
  const locationId = overrideLocationId || locationIdNum.value;
  
  if (!locationId || isNaN(locationId)) {
    ElMessage.warning('无效的地点ID: ' + (overrideLocationId || props.locationId));
    return;
  }
  
  try {
    loading.value = true;
    console.log('正在加载地点ID:', locationId, '的详情');
    
    const data = await locationApi.getLocationDetails(locationId);
    console.log('地点详情API响应:', data);
    
    if (data) {
      // 确保数据结构完整
      if (!data.events) data.events = [];
      if (!data.characters) data.characters = [];
      if (!data.sub_locations) data.sub_locations = [];
      
      // 确保每个事件都有基本属性
      data.events = data.events.map(event => ({
        id: event.id || 0,
        name: event.name || '未命名事件',
        description: event.description || '',
        importance: event.importance || 1,
        chapter_id: event.chapter_id || null,
        time_description: event.time_description || '',
        characters: Array.isArray(event.characters) ? event.characters : []
      }));
      
      // 确保每个角色都有基本属性
      data.characters = data.characters.map(char => ({
        id: char.id || 0,
        name: char.name || '未命名角色',
        importance: char.importance || 1
      }));
      
      locationDetail.value = data;
      console.log('成功设置地点详情:', locationDetail.value);
      ElMessage.success('成功加载地点详情');
    } else {
      ElMessage.warning('地点详情数据为空');
      // 初始化默认值以防止渲染错误
      locationDetail.value = {
        id: locationId,
        name: '未找到地点',
        description: '无法获取地点详情',
        events: [],
        characters: [],
        sub_locations: []
      };
    }
  } catch (error) {
    console.error('获取地点详情失败:', error);
    ElMessage.error('获取地点详情失败: ' + (error.message || '未知错误'));
    // 初始化默认值以防止渲染错误
    locationDetail.value = {
      id: locationId,
      name: '加载失败',
      description: '地点详情加载失败',
      events: [],
      characters: [],
      sub_locations: []
    };
  } finally {
    loading.value = false;
  }
}

// 加载地点重要性分析
async function loadLocationSignificance(overrideLocationId) {
  // 优先使用传入的ID，否则使用计算属性
  const locationId = overrideLocationId || locationIdNum.value;
  
  if (!locationId || isNaN(locationId)) {
    console.warn('无法加载地点重要性分析，无效的地点ID:', overrideLocationId || props.locationId);
    return;
  }
  
  try {
    console.log('正在加载地点ID:', locationId, '的重要性分析');
    const data = await locationApi.getLocationSignificance(locationId);
    console.log('地点重要性分析API响应:', data);
    
    if (data) {
      locationSignificance.value = data;
    } else {
      console.warn('地点重要性分析数据为空');
    }
  } catch (error) {
    console.error('获取地点重要性分析失败:', error);
    // 不显示错误消息，因为这只是补充信息
  }
}

// 加载地点时间线
async function loadLocationTimeline(overrideLocationId, overrideNovelId) {
  // 优先使用传入的ID，否则使用计算属性
  const locationId = overrideLocationId || locationIdNum.value;
  const novelId = overrideNovelId || novelIdNum.value;
  
  if (!locationId || isNaN(locationId)) {
    console.warn('无法加载地点时间线，无效的地点ID:', overrideLocationId || props.locationId);
    return;
  }
  
  if (!novelId || isNaN(novelId)) {
    console.warn('无法加载地点时间线，无效的小说ID:', overrideNovelId || props.novelId);
    return;
  }
  
  try {
    timelineLoading.value = true;
    console.log('正在加载地点ID:', locationId, '小说ID:', novelId, '的时间线');
    
    const data = await locationApi.getLocationTimeline(locationId, novelId);
    console.log('地点时间线API响应:', data);
    
    if (data && data.events) {
      // 确保每个事件都有必要的属性
      data.events = data.events.map(event => ({
        id: event.id || 0,
        name: event.name || '未命名事件',
        description: event.description || '',
        importance: event.importance || 1,
        chapter_id: event.chapter_id || null,
        time_description: event.time_description || '',
        time_position: event.time_position || 0,
        tags: Array.isArray(event.tags) ? event.tags : [],
        characters: Array.isArray(event.characters) ? 
          event.characters.filter(char => char && typeof char === 'object') : []
      }));
      
      timeline.value = data;
      ElMessage.success('成功加载地点时间线');
    } else {
      timeline.value = { events: [] };
      console.warn('地点时间线数据为空');
      ElMessage.warning('地点时间线数据为空');
    }
  } catch (error) {
    console.error('获取地点时间线失败:', error);
    ElMessage.error('获取地点时间线失败: ' + (error.message || '未知错误'));
    timeline.value = { events: [] }; // 设置默认值避免未定义错误
  } finally {
    timelineLoading.value = false;
  }
}

// 返回上一页
function goBack() {
  router.go(-1)
}

// 查看父地点
function viewParentLocation(parentId) {
  if (!parentId) {
    ElMessage.warning('父地点ID无效')
    return
  }
  
  router.push({
    name: 'LocationDetail',
    params: { locationId: parentId },
    query: { novelId: props.novelId }
  })
}

// 查看子地点
function viewSubLocation(subId) {
  if (!subId) {
    ElMessage.warning('子地点ID无效')
    return
  }
  
  router.push({
    name: 'LocationDetail',
    params: { locationId: subId },
    query: { novelId: props.novelId }
  })
}

// 查看角色详情
function viewCharacterDetail(characterId) {
  if (!characterId) {
    ElMessage.warning('角色ID无效')
    return
  }
  
  router.push({
    path: '/analysis/characters/journey',
    query: {
      novelId: props.novelId,
      characterId: characterId
    }
  })
}

// 切换标签筛选
function toggleTag(tag) {
  if (activeTags.value.includes(tag)) {
    activeTags.value = activeTags.value.filter(t => t !== tag)
  } else {
    activeTags.value.push(tag)
  }
}

// 格式化时间戳显示
function formatTimestamp(event) {
  if (timelineMode.value === 'time' && event.time_description) {
    return event.time_description
  }
  return `第${event.chapter_id || '?'}章`
}

// 计算属性：按排序的事件
const sortedEvents = computed(() => {
  if (!locationDetail.value || !locationDetail.value.events) return []
  
  return [...locationDetail.value.events].sort((a, b) => {
    // 先按章节排序
    if (a.chapter_id !== b.chapter_id) {
      return a.chapter_id - b.chapter_id
    }
    // 同章节按重要性排序
    return b.importance - a.importance
  })
})

// 计算属性：按重要性排序的角色
const sortedCharacters = computed(() => {
  if (!locationDetail.value || !locationDetail.value.characters) return []
  
  return [...locationDetail.value.characters].sort((a, b) => b.importance - a.importance)
})

// 计算属性：可用标签
const availableTags = computed(() => {
  if (!timeline.value || !timeline.value.events) return ['重要事件', '战斗', '情感', '发现', '旅行']
  
  const tags = new Set(['重要事件'])
  
  timeline.value.events.forEach(event => {
    if (event && event.tags && Array.isArray(event.tags) && event.tags.length) {
      event.tags.forEach(tag => tag && tags.add(tag))
    }
  })
  
  return Array.from(tags)
})

// 计算属性：过滤后的事件
const filteredEvents = computed(() => {
  if (!timeline.value || !timeline.value.events) return []
  
  // 首先根据标签过滤
  let events = timeline.value.events.filter(event => {
    if (!event) return false
    
    if (!event.tags || !Array.isArray(event.tags) || !event.tags.length) {
      // 没有标签的事件，只有在选择了"重要事件"且该事件重要性>=4时才显示
      return activeTags.value.includes('重要事件') && (event.importance || 0) >= 4
    }
    
    // 事件标签与激活的标签有重叠则显示
    return event.tags.some(tag => tag && activeTags.value.includes(tag))
  })
  
  // 根据模式排序
  if (timelineMode.value === 'chapter') {
    events = [...events].sort((a, b) => {
      // 先按章节排序
      const chapterA = a.chapter_id || 0
      const chapterB = b.chapter_id || 0
      if (chapterA !== chapterB) {
        return chapterA - chapterB
      }
      // 同一章节内按重要性排序
      return (b.importance || 0) - (a.importance || 0)
    })
  } else {
    events = [...events].sort((a, b) => {
      // 按时间位置排序
      const posA = a.time_position || 0
      const posB = b.time_position || 0
      return posA - posB
    })
  }
  
  return events
})

// 获取事件类型（用于时间线）
function getEventType(importance) {
  if (importance >= 5) return 'success'
  if (importance >= 3) return 'info'
  return 'default'
}

// 获取事件颜色（用于时间线）
function getEventColor(importance) {
  if (importance >= 5) return '#18a058'
  if (importance >= 3) return '#2080f0'
  return '#d9d9d9'
}

// 获取事件中的角色头像（用于时间线）
function getEventCharacters(event) {
  if (!event || !event.characters || !Array.isArray(event.characters) || event.characters.length === 0) return []
  
  return event.characters.map(char => {
    if (!char) return { name: '未知角色', src: '' }
    
    return {
      name: char.name || '未知角色',
      src: char.id ? getCharacterAvatar(char.id) : ''
    }
  }).filter(item => item !== null)
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
function getLocationIcon(locationId) {
  if (!locationId) return HomeFilled;
  
  // 根据ID生成一个0-9的数字
  const iconIndex = (locationId % 10);
  
  const icons = [
    HomeFilled,       // 首页图标
    Location,         // 位置图标
    MapLocation,      // 地图位置图标
    School,           // 学校图标
    OfficeBuilding,   // 办公楼图标
    House,            // 房子图标
    Notebook,         // 笔记本图标（可用于书籍场景）
    ShoppingBag,      // 购物袋图标（可用于商店场景）
    HomeFilled,       // 重复首页图标
    Location          // 重复位置图标
  ];
  
  return icons[iconIndex];
}

// 获取角色头像
function getCharacterAvatar(characterId) {
  if (!characterId) return '';
  
  const avatarStyles = [
    'adventurer', 'adventurer-neutral', 'big-ears', 
    'big-smile', 'bottts', 'croodles', 'fun-emoji', 
    'icons', 'identicon', 'lorelei', 'micah', 'miniavs', 
    'pixelart'
  ];
  
  const styleIndex = characterId % avatarStyles.length;
  return `https://api.dicebear.com/7.x/${avatarStyles[styleIndex]}/svg?seed=character_${characterId}`;
}

// 添加路由参数变化监听
watch(() => route.params.locationId, async (newLocationId, oldLocationId) => {
  console.log('locationId路由参数变化', oldLocationId, '->', newLocationId);
  if (newLocationId && newLocationId !== oldLocationId) {
    const locationId = Number(newLocationId);
    await loadLocationDetails(locationId);
    await loadLocationSignificance(locationId);
    // 重置时间线
    timeline.value = null;
    showTimeline.value = false;
  }
}, { immediate: false });

// 添加novelId查询参数变化监听
watch(() => route.query.novelId, async (newNovelId, oldNovelId) => {
  console.log('novelId查询参数变化', oldNovelId, '->', newNovelId);
  // 如果novelId变化，可能需要重新加载一些依赖小说ID的数据
  if (newNovelId && newNovelId !== oldNovelId && timeline.value) {
    // 仅当已加载过时间线时才重新加载
    timeline.value = null;
    if (showTimeline.value) {
      await loadLocationTimeline();
    }
  }
}, { immediate: false });
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