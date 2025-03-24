<template>
  <div class="item-lineage-container">
    <el-card shadow="never">
      <template #header>
        <div class="page-header">
          <h2>物品血统分析</h2>
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
              v-model="selectedItem"
              placeholder="选择物品"
              @change="handleItemChange"
              :disabled="!selectedNovel || !items.length"
            >
              <el-option
                v-for="item in items"
                :key="item.id"
                :label="item.name"
                :value="item.id"
              />
            </el-select>
            
            <el-button 
              type="primary" 
              @click="generateItemLineage" 
              :disabled="!selectedNovel || !selectedItem"
              :loading="analysisStore.loading"
            >
              生成血统分析
            </el-button>
          </div>
        </div>
      </template>
      
      <!-- 尚未选择小说或物品的提示 -->
      <el-empty 
        v-if="!selectedNovel || !selectedItem" 
        description="请从上方选择小说和物品"
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
          <el-button type="primary" @click="generateItemLineage">重试</el-button>
        </template>
      </el-result>
      
      <!-- 尚未生成物品血统的提示 -->
      <el-empty 
        v-else-if="!itemLineage" 
        description="点击上方按钮生成物品血统分析"
      >
        <el-button type="primary" @click="generateItemLineage">生成物品血统分析</el-button>
      </el-empty>
      
      <!-- 物品血统内容 -->
      <div v-else class="item-lineage-content">
        <!-- 物品基本信息卡片 -->
        <el-card class="item-info-card">
          <div class="item-info">
            <div class="item-image">
              <img :src="getItemImage()" alt="物品图像" class="item-img" />
            </div>
            <div class="item-details">
              <h3 class="item-name">
                {{ itemLineage.item.name }}
                <el-tag v-if="itemLineage.item.is_legendary" type="danger" size="small">传奇</el-tag>
              </h3>
              <div class="item-description">
                {{ itemLineage.item.description || '暂无描述' }}
              </div>
              <div class="item-attributes">
                <el-tag 
                  v-for="(attribute, index) in itemLineage.item.attributes" 
                  :key="index"
                  :type="getAttributeTagType(attribute.type)"
                  class="attribute-tag"
                >
                  {{ attribute.name }}: {{ attribute.value }}
                </el-tag>
              </div>
            </div>
            <div class="item-stats">
              <div class="stat-item">
                <div class="stat-value">{{ itemLineage.stats.owners_count }}</div>
                <div class="stat-label">拥有者数</div>
              </div>
              <div class="stat-item">
                <div class="stat-value">{{ itemLineage.stats.appearances_count }}</div>
                <div class="stat-label">出场次数</div>
              </div>
              <div class="stat-item">
                <div class="stat-value">{{ itemLineage.stats.power_level }}</div>
                <div class="stat-label">力量等级</div>
              </div>
            </div>
          </div>
        </el-card>
        
        <!-- 血统分析部分 -->
        <div class="lineage-analysis">
          <el-tabs v-model="activeTab">
            <!-- 血统树标签页 -->
            <el-tab-pane label="血统树" name="lineage">
              <div class="lineage-tree-container">
                <div ref="lineageTreeRef" class="lineage-tree"></div>
              </div>
              <div class="legend">
                <div class="legend-item">
                  <div class="legend-color" style="background-color: #F56C6C;"></div>
                  <div class="legend-label">传奇物品</div>
                </div>
                <div class="legend-item">
                  <div class="legend-color" style="background-color: #E6A23C;"></div>
                  <div class="legend-label">稀有物品</div>
                </div>
                <div class="legend-item">
                  <div class="legend-color" style="background-color: #409EFF;"></div>
                  <div class="legend-label">普通物品</div>
                </div>
              </div>
            </el-tab-pane>
            
            <!-- 拥有者历史标签页 -->
            <el-tab-pane label="拥有者历史" name="owners">
              <div class="owners-history">
                <el-timeline>
                  <el-timeline-item
                    v-for="(owner, index) in itemLineage.ownership_history"
                    :key="index"
                    :timestamp="`第${owner.chapter_id}章`"
                    placement="top"
                  >
                    <el-card class="owner-card">
                      <div class="owner-info">
                        <div class="owner-avatar">
                          <el-avatar :size="40" :src="getCharacterAvatar(owner.character_id)"></el-avatar>
                        </div>
                        <div class="owner-details">
                          <h4>{{ owner.character_name }}</h4>
                          <div class="ownership-details">
                            <div class="ownership-type">
                              <el-tag size="small" :type="getOwnershipType(owner.type)">
                                {{ owner.type }}
                              </el-tag>
                            </div>
                            <div class="ownership-period" v-if="owner.end_chapter_id">
                              持有期间：第{{ owner.chapter_id }}章 - 第{{ owner.end_chapter_id }}章
                            </div>
                            <div class="ownership-period" v-else>
                              获得于：第{{ owner.chapter_id }}章（至今持有）
                            </div>
                          </div>
                        </div>
                      </div>
                      <div class="acquisition-details">
                        <p>{{ owner.acquisition_method || '不详' }}</p>
                        <div class="event-link" v-if="owner.event_id">
                          <el-button type="primary" link @click="viewEvent(owner.event_id)">
                            查看相关事件
                          </el-button>
                        </div>
                      </div>
                    </el-card>
                  </el-timeline-item>
                </el-timeline>
              </div>
            </el-tab-pane>
            
            <!-- 能力变化标签页 -->
            <el-tab-pane label="能力变化" name="powers">
              <div class="powers-evolution">
                <div ref="powerChartRef" class="power-chart"></div>
                <div class="power-milestones">
                  <el-card v-for="(milestone, index) in itemLineage.power_milestones" :key="index" class="milestone-card">
                    <template #header>
                      <div class="milestone-header">
                        <h4>{{ milestone.name }}</h4>
                        <el-tag size="small">第{{ milestone.chapter_id }}章</el-tag>
                      </div>
                    </template>
                    <div class="milestone-content">
                      <p>{{ milestone.description }}</p>
                      <div class="milestone-effects">
                        <div v-for="(effect, effectIndex) in milestone.effects" :key="effectIndex" class="effect-item">
                          <span class="effect-name">{{ effect.name }}</span>
                          <el-progress 
                            :percentage="effect.value * 10" 
                            :stroke-width="8" 
                            :color="getEffectColor(effect.type)"
                          ></el-progress>
                        </div>
                      </div>
                    </div>
                  </el-card>
                </div>
              </div>
            </el-tab-pane>
            
            <!-- 相关物品标签页 -->
            <el-tab-pane label="相关物品" name="related">
              <div class="related-items">
                <el-row :gutter="20">
                  <el-col 
                    v-for="relatedItem in itemLineage.related_items" 
                    :key="relatedItem.id"
                    :xs="24" 
                    :sm="12" 
                    :md="8" 
                    :lg="6"
                  >
                    <el-card shadow="hover" class="related-item-card">
                      <div class="related-item-content">
                        <img :src="getItemImage(relatedItem.id)" class="related-item-image" />
                        <h4>{{ relatedItem.name }}</h4>
                        <p>{{ relatedItem.description || '暂无描述' }}</p>
                        <div class="item-relation">
                          <el-tag size="small" :type="getRelationTagType(relatedItem.relation_type)">
                            {{ relatedItem.relation_type }}
                          </el-tag>
                          <el-button 
                            type="primary" 
                            size="small" 
                            text 
                            @click="changeItem(relatedItem.id)"
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

const router = useRouter()
const route = useRoute()
const novelStore = useNovelStore()
const analysisStore = useAnalysisStore()

// 本地状态
const selectedNovel = ref(null)
const selectedItem = ref(null)
const items = ref([])
const activeTab = ref('lineage')
const lineageTree = ref(null)
const lineageTreeRef = ref(null)
const powerChart = ref(null)
const powerChartRef = ref(null)

// 物品血统数据
const itemLineage = computed(() => analysisStore.itemLineage || null)

// 从路由参数中获取小说ID和物品ID
onMounted(async () => {
  if (novelStore.novels.length === 0) {
    await novelStore.fetchNovels()
  }
  
  const novelId = Number(route.query.novelId)
  const itemId = Number(route.query.itemId)
  
  if (novelId && !isNaN(novelId)) {
    selectedNovel.value = novelId
    await loadItems(novelId)
    
    if (itemId && !isNaN(itemId) && items.value.find(i => i.id === itemId)) {
      selectedItem.value = itemId
      
      // 自动生成物品血统分析
      generateItemLineage()
    }
  }
})

// 监听标签页变化
watch(activeTab, async (newValue) => {
  if (newValue === 'lineage' && itemLineage.value && !lineageTree.value) {
    await nextTick()
    renderLineageTree()
  } else if (newValue === 'powers' && itemLineage.value && !powerChart.value) {
    await nextTick()
    renderPowerChart()
  }
})

// 监听物品血统数据变化
watch(itemLineage, async () => {
  if (activeTab.value === 'lineage' && itemLineage.value) {
    await nextTick()
    renderLineageTree()
  } else if (activeTab.value === 'powers' && itemLineage.value) {
    await nextTick()
    renderPowerChart()
  }
})

// 加载物品列表
async function loadItems(novelId) {
  try {
    // TODO: 实际项目中应从API获取
    // const response = await novelApi.getNovelItems(novelId)
    // items.value = response.data
    
    // 模拟数据
    items.value = generateMockItems()
  } catch (error) {
    ElMessage.error('获取物品列表失败')
    items.value = []
  }
}

// 小说选择变化处理
async function handleNovelChange(novelId) {
  selectedItem.value = null
  analysisStore.reset()
  await loadItems(novelId)
  
  // 更新URL参数
  router.replace({
    query: { ...route.query, novelId, itemId: undefined }
  })
}

// 物品选择变化处理
function handleItemChange(itemId) {
  analysisStore.reset()
  
  // 更新URL参数
  router.replace({
    query: { ...route.query, itemId }
  })
}

// 生成物品血统分析
async function generateItemLineage() {
  if (!selectedNovel.value || !selectedItem.value) return
  
  try {
    await analysisStore.fetchItemLineage(
      selectedNovel.value,
      selectedItem.value
    )
  } catch (error) {
    ElMessage.error('生成物品血统分析失败')
  }
}

// 渲染血统树
function renderLineageTree() {
  if (!lineageTreeRef.value || !itemLineage.value?.lineage_tree) return
  
  if (!lineageTree.value) {
    lineageTree.value = echarts.init(lineageTreeRef.value)
  }
  
  const lineageData = itemLineage.value.lineage_tree
  
  const options = {
    tooltip: {
      trigger: 'item',
      triggerOn: 'mousemove'
    },
    series: [
      {
        type: 'tree',
        data: [lineageData],
        top: '10%',
        bottom: '10%',
        layout: 'orthogonal',
        orient: 'TB',
        symbol: 'roundRect',
        symbolSize: [90, 30],
        initialTreeDepth: -1,
        label: {
          position: 'inside',
          verticalAlign: 'middle',
          align: 'center',
          fontSize: 12
        },
        leaves: {
          label: {
            position: 'inside',
            verticalAlign: 'middle',
            align: 'center'
          }
        },
        itemStyle: {
          color: function(params) {
            const data = params.data
            if (data.is_legendary) return '#F56C6C' // 传奇
            if (data.is_rare) return '#E6A23C' // 稀有
            return '#409EFF' // 普通
          }
        },
        lineStyle: {
          color: '#ccc',
          width: 1.5,
          curveness: 0.5
        },
        emphasis: {
          focus: 'descendant'
        },
        expandAndCollapse: true,
        animationDuration: 550,
        animationDurationUpdate: 750
      }
    ]
  }
  
  lineageTree.value.setOption(options)
}

// 渲染能力变化图表
function renderPowerChart() {
  if (!powerChartRef.value || !itemLineage.value?.power_evolution) return
  
  if (!powerChart.value) {
    powerChart.value = echarts.init(powerChartRef.value)
  }
  
  const powerData = itemLineage.value.power_evolution
  const chapters = powerData.map(data => data.chapter_id)
  const powers = {}
  
  // 整理数据
  powerData.forEach(item => {
    Object.keys(item.powers).forEach(power => {
      if (!powers[power]) {
        powers[power] = []
      }
      powers[power].push(item.powers[power])
    })
  })
  
  // 构建系列数据
  const series = Object.keys(powers).map(power => ({
    name: power,
    type: 'line',
    stack: 'Total',
    areaStyle: {},
    emphasis: {
      focus: 'series'
    },
    data: powers[power]
  }))
  
  const options = {
    title: {
      text: '物品能力进化曲线'
    },
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'cross',
        label: {
          backgroundColor: '#6a7985'
        }
      }
    },
    legend: {
      data: Object.keys(powers)
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      containLabel: true
    },
    xAxis: [
      {
        type: 'category',
        boundaryGap: false,
        data: chapters,
        name: '章节'
      }
    ],
    yAxis: [
      {
        type: 'value',
        name: '能力值'
      }
    ],
    series: series
  }
  
  powerChart.value.setOption(options)
}

// 导航到小说列表
function navigateToNovelList() {
  router.push('/novels/list')
}

// 查看相关事件
function viewEvent(eventId) {
  // TODO: 实际项目中应导航到事件详情页面
  ElMessage.info(`查看事件ID: ${eventId}`)
}

// 切换到其他物品
function changeItem(itemId) {
  selectedItem.value = itemId
  generateItemLineage()
}

// 获取属性标签类型
function getAttributeTagType(attributeType) {
  const typeMap = {
    'offensive': 'danger',   // 攻击性
    'defensive': 'success',  // 防御性
    'utility': 'info',       // 实用性
    'unique': 'warning'      // 特殊性
  }
  
  return typeMap[attributeType] || ''
}

// 获取关系标签类型
function getRelationTagType(relationType) {
  const typeMap = {
    '同源': 'success',
    '对立': 'danger',
    '衍生': 'info',
    '配套': 'warning'
  }
  
  return typeMap[relationType] || ''
}

// 获取所有权类型
function getOwnershipType(ownershipType) {
  const typeMap = {
    '创造': 'danger',
    '继承': 'success',
    '赠予': 'info',
    '夺取': 'warning',
    '购买': '',
    '偶得': 'info'
  }
  
  return typeMap[ownershipType] || ''
}

// 获取效果颜色
function getEffectColor(effectType) {
  const colorMap = {
    'positive': '#67C23A',   // 正面效果
    'negative': '#F56C6C',   // 负面效果
    'neutral': '#909399'     // 中性效果
  }
  
  return colorMap[effectType] || '#409EFF'
}

// 获取物品图像
function getItemImage(id = null) {
  const itemId = id || selectedItem.value
  const baseUrl = 'https://picsum.photos/seed/'
  return `${baseUrl}item-${itemId}/300/300`
}

// 获取角色头像
function getCharacterAvatar(characterId) {
  return `https://avatars.dicebear.com/api/avataaars/${characterId}.svg`
}

// 窗口大小变化时重绘图表
window.addEventListener('resize', () => {
  if (lineageTree.value) {
    lineageTree.value.resize()
  }
  if (powerChart.value) {
    powerChart.value.resize()
  }
})

// 生成模拟物品数据
function generateMockItems() {
  const count = 10
  const items = []
  
  const names = ['青龙剑', '玄武盾', '朱雀羽', '白虎爪', '混元珠', '九天琴', '太虚镜', '破晓枪', '归墟钟', '幽冥鼎']
  
  for (let i = 0; i < count; i++) {
    items.push({
      id: i + 1,
      name: names[i % names.length]
    })
  }
  
  return items
}
</script>

<style scoped>
.item-lineage-container {
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

.item-lineage-content {
  margin-top: 20px;
}

.item-info-card {
  margin-bottom: 20px;
}

.item-info {
  display: flex;
  align-items: center;
  gap: 20px;
}

.item-image {
  width: 120px;
  height: 120px;
  border-radius: 8px;
  overflow: hidden;
}

.item-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.item-details {
  flex: 1;
}

.item-name {
  margin-top: 0;
  margin-bottom: 10px;
  display: flex;
  align-items: center;
  gap: 10px;
}

.item-description {
  color: #606266;
  margin-bottom: 10px;
}

.item-attributes {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.attribute-tag {
  margin-right: 5px;
}

.item-stats {
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

.lineage-analysis {
  min-height: 400px;
}

.lineage-tree-container {
  padding: 10px;
}

.lineage-tree {
  width: 100%;
  height: 500px;
}

.legend {
  display: flex;
  justify-content: center;
  gap: 20px;
  margin-top: 10px;
}

.legend-item {
  display: flex;
  align-items: center;
}

.legend-color {
  width: 16px;
  height: 16px;
  border-radius: 4px;
  margin-right: 8px;
}

.legend-label {
  font-size: 14px;
  color: #606266;
}

.owners-history {
  padding: 10px;
}

.owner-card {
  margin-bottom: 10px;
}

.owner-info {
  display: flex;
  align-items: center;
  gap: 15px;
  margin-bottom: 10px;
}

.owner-details {
  flex: 1;
}

.owner-details h4 {
  margin: 0 0 5px 0;
}

.ownership-details {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  align-items: center;
  color: #606266;
  font-size: 14px;
}

.acquisition-details {
  color: #606266;
  font-size: 14px;
}

.acquisition-details p {
  margin-top: 0;
}

.event-link {
  margin-top: 5px;
  text-align: right;
}

.powers-evolution {
  padding: 10px;
}

.power-chart {
  width: 100%;
  height: 300px;
  margin-bottom: 20px;
}

.power-milestones {
  margin-top: 20px;
}

.milestone-card {
  margin-bottom: 20px;
}

.milestone-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.milestone-header h4 {
  margin: 0;
}

.milestone-content p {
  margin-top: 0;
  color: #606266;
}

.milestone-effects {
  margin-top: 15px;
}

.effect-item {
  margin-bottom: 10px;
}

.effect-name {
  display: block;
  margin-bottom: 5px;
  font-weight: bold;
  font-size: 14px;
}

.related-items {
  padding: 10px;
}

.related-item-card {
  margin-bottom: 20px;
  height: 100%;
}

.related-item-content {
  display: flex;
  flex-direction: column;
  height: 100%;
}

.related-item-image {
  width: 100%;
  height: 150px;
  object-fit: cover;
  border-radius: 4px;
  margin-bottom: 10px;
}

.related-item-content h4 {
  margin-top: 0;
  margin-bottom: 10px;
}

.related-item-content p {
  color: #606266;
  margin-top: 0;
  margin-bottom: 10px;
  flex-grow: 1;
}

.item-relation {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
</style> 