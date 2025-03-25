<template>
  <div class="relationship-container">
    <el-card shadow="never" style="width: 100%;">
      <template #header>
        <div class="page-header">
          <h2>关系网络分析</h2>
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
              placeholder="选择角色（可选）"
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
            
            <el-select
              v-model="graphDepth"
              placeholder="关系深度"
              :disabled="!selectedNovel"
            >
              <el-option
                v-for="n in 3"
                :key="n"
                :label="`${n}级关系`"
                :value="n"
              />
            </el-select>
            
            <el-button 
              type="primary" 
              @click="generateGraph()" 
              :disabled="!selectedNovel"
              :loading="analysisStore.loading"
            >
              生成关系图
            </el-button>
            
            <el-button
              type="warning"
              @click="() => {
                console.log('[DEBUG] 点击重新分析按钮，设置forceRefresh=true');
                const forceRefresh = true;
                forceReanalyze();
              }"
              :disabled="!selectedNovel || analysisStore.loading"
              v-if="hasCachedGraph"
            >
              重新分析
            </el-button>
          </div>
        </div>
      </template>
      
      <!-- 尚未选择小说的提示 -->
      <el-empty 
        v-if="!selectedNovel" 
        description="请从上方选择一本小说以查看人物关系网络"
      >
        <el-button type="primary" @click="navigateToNovelList">浏览小说列表</el-button>
      </el-empty>
      
      <!-- 加载中状态 - 仅在没有图表的情况下显示 -->
      <div v-else-if="analysisStore.loading && !analysisStore.relationshipGraph" class="loading-container">
        <el-skeleton :rows="10" animated />
      </div>
      
      <!-- 错误状态 -->
      <el-result 
        v-else-if="analysisStore.error" 
        icon="error" 
        :title="'加载失败'" 
        :sub-title="analysisStore.error"
      >
        <template #extra>
          <el-button type="primary" @click="generateGraph">重试</el-button>
        </template>
      </el-result>
      
      <!-- 尚未生成图的提示 -->
      <el-empty 
        v-else-if="!analysisStore.relationshipGraph" 
        description="点击上方按钮生成关系网络图"
      >
        <div>
          <el-button type="primary" @click="generateGraph()">生成关系图</el-button>
          <p v-if="hasCachedGraph" class="text-muted">已有缓存数据，点击生成按钮可快速加载</p>
        </div>
      </el-empty>
      
      <!-- 关系图 - 包含加载状态覆盖 -->
      <div v-else class="graph-container">
        <!-- 当强制刷新时显示的加载指示器 -->
        <div v-if="analysisStore.loading" class="loading-overlay">
          <el-icon class="is-loading"><Loading /></el-icon>
          <span>正在重新分析...</span>
        </div>
        
        <div class="graph-toolbar">
          <el-radio-group v-model="graphMode" size="small">
            <el-radio-button value="force">力导向图</el-radio-button>
            <el-radio-button value="circular">环形图</el-radio-button>
          </el-radio-group>
          
          <el-select 
            v-model="selectedRelationTypes" 
            multiple 
            collapse-tags
            clearable 
            placeholder="筛选关系类型" 
            size="small"
          >
            <el-option
              v-for="type in relationTypes"
              :key="type"
              :label="type"
              :value="type"
            >
              <span style="display: flex; align-items: center;">
                <span class="relation-color-dot" :style="{backgroundColor: getRelationColor(type)}"></span>
                {{ type }}
              </span>
            </el-option>
          </el-select>
          
          <el-tooltip content="将图表导出为图片">
            <el-button size="small" @click="exportImage">
              <el-icon><Download /></el-icon>
            </el-button>
          </el-tooltip>
        </div>
        
        <div class="relation-legend" v-if="relationTypes.length > 0">
          <span 
            v-for="type in relationTypes" 
            :key="type" 
            class="legend-item"
            :class="{
              'legend-item-active': selectedRelationTypes.length === 0 || selectedRelationTypes.includes(type),
              'legend-item-inactive': selectedRelationTypes.length > 0 && !selectedRelationTypes.includes(type)
            }"
            @click="toggleRelationType(type)"
          >
            <span class="relation-color-dot" :style="{backgroundColor: getRelationColor(type)}"></span>
            {{ type }}
          </span>
        </div>
        
        <div class="graph-view" ref="graphRef"></div>
        
        <div class="graph-info">
          <div v-if="selectedNode" class="node-info">
            <h3>{{ selectedNode.name }}</h3>
            <p>{{ selectedNode.description || '暂无描述' }}</p>
            <div class="relations-list">
              <h4>相关关系：</h4>
              <el-tag 
                v-for="relation in selectedNodeRelations" 
                :key="relation.id"
                :type="getRelationTagType(relation.type)"
                style="margin: 0 5px 5px 0"
                :effect="relation.direction === 'outgoing' ? 'light' : 'plain'"
              >
                <el-tooltip 
                  v-if="relation.description" 
                  :content="relation.description" 
                  placement="top"
                >
                  <span>
                    {{ relation.source }} 
                    <el-icon v-if="relation.direction === 'outgoing'" style="margin: 0 2px;"><ArrowRight /></el-icon>
                    <el-icon v-else style="margin: 0 2px;"><ArrowLeft /></el-icon>
                    {{ relation.type }} 
                    {{ relation.target }}
                  </span>
                </el-tooltip>
                <span v-else>
                  {{ relation.source }} 
                  <el-icon v-if="relation.direction === 'outgoing'" style="margin: 0 2px;"><ArrowRight /></el-icon>
                  <el-icon v-else style="margin: 0 2px;"><ArrowLeft /></el-icon>
                  {{ relation.type }} 
                  {{ relation.target }}
                </span>
              </el-tag>
              <div v-if="selectedNodeRelations.length === 0" class="no-relations">
                暂无关联的角色关系
              </div>
            </div>
          </div>
          <div v-else class="graph-hint">
            <p>选择一个角色节点可查看详细信息</p>
            <p>拖拽节点可调整位置，滚轮可缩放图表</p>
          </div>
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
import { Download, ArrowRight, ArrowLeft, Loading } from '@element-plus/icons-vue'
import * as echarts from 'echarts'
import { analysisApi } from '@/api'

const router = useRouter()
const route = useRoute()
const novelStore = useNovelStore()
const analysisStore = useAnalysisStore()

// 本地状态
const selectedNovel = ref(null)
const selectedCharacter = ref(null)
const characters = ref([])
const graphRef = ref(null)
const graphChart = ref(null)
const graphDepth = ref(1)
const graphMode = ref('force')
const selectedRelationTypes = ref([])
const selectedNode = ref(null)

// 计算属性：判断是否有缓存的关系图
const hasCachedGraph = computed(() => {
  if (!selectedNovel.value) return false
  return analysisStore.hasRelationshipCache(
    selectedNovel.value,
    selectedCharacter.value,
    graphDepth.value
  )
})

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
    
    // 检查是否有缓存，有则加载，没有则等待用户手动触发生成
    if (analysisStore.hasRelationshipCache(novelId, characterId, graphDepth.value)) {
      // 直接使用缓存数据，不发送API请求
      await generateGraph(false)
    }
  }
})

// 监听图表模式变化
watch(graphMode, () => {
  if (analysisStore.relationshipGraph) {
    nextTick(() => {
      renderGraph()
    })
  }
})

// 监听关系类型筛选变化
watch(selectedRelationTypes, () => {
  if (analysisStore.relationshipGraph) {
    nextTick(() => {
      renderGraph()
    })
  }
})

// 计算属性：关系类型列表
const relationTypes = computed(() => {
  if (!analysisStore.relationshipGraph) return []
  
  const types = new Set()
  analysisStore.relationshipGraph.edges.forEach(edge => {
    types.add(edge.relation)
  })
  
  return Array.from(types)
})

// 计算属性：当前选中节点的关系
const selectedNodeRelations = computed(() => {
  if (!selectedNode.value || !analysisStore.relationshipGraph) return []
  
  // 获取分析数据中的所有边
  const allEdges = analysisStore.relationshipGraph.edges
  
  // 过滤出与当前选中节点相关的所有边
  const relatedEdges = allEdges.filter(edge => 
    edge.source_id === selectedNode.value.id || 
    edge.target_id === selectedNode.value.id
  )
  
  // 将边转换为更易于渲染的格式
  return relatedEdges.map(edge => {
    // 确定关系方向，使显示更有意义
    let source, target, direction
    
    if (edge.source_id === selectedNode.value.id) {
      // 当前节点是关系的源节点
      source = selectedNode.value.name
      target = edge.target_name
      direction = 'outgoing'
    } else {
      // 当前节点是关系的目标节点
      source = edge.source_name
      target = selectedNode.value.name
      direction = 'incoming'
    }
    
    return {
      id: edge.id,
      source: source,
      target: target,
      type: edge.relation,
      description: edge.description,
      direction: direction
    }
  })
})

// 加载角色列表
async function loadCharacters(novelId) {
  try {
    // 从API获取小说的角色列表
    const response = await novelStore.fetchNovelDetail(novelId);
    
    // 如果返回了角色数据
    if (response && response.characters) {
      characters.value = response.characters;
    } else {
      // 如果没有角色数据，使用空数组
      characters.value = [];
      
      // 通知用户可能需要先进行角色提取
      if (characters.value.length === 0) {
        ElMessage.info('该小说尚未提取角色数据，系统将在分析时自动提取');
      }
    }
  } catch (error) {
    ElMessage.error('获取角色列表失败');
    characters.value = [];
  }
}

// 小说选择变化处理
async function handleNovelChange(novelId) {
  // 仅在小说真正改变时才重置数据
  if (selectedNovel.value !== novelId) {
    selectedCharacter.value = null
    analysisStore.reset()
    await loadCharacters(novelId)
  }
  
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

// 生成关系图
async function generateGraph(forceRefresh = false) {
  if (!selectedNovel.value) return
  
  // 确保forceRefresh是布尔值
  const shouldForceRefresh = forceRefresh === true;
  console.log(`[DEBUG] generateGraph 调用，forceRefresh=${shouldForceRefresh} (${typeof shouldForceRefresh})`);
  
  try {
    // 保持当前的图表可见，直到新数据加载完成
    // 调用后端API获取真实的关系网络数据，添加forceRefresh参数
    await analysisStore.fetchRelationshipGraph(
      selectedNovel.value,
      selectedCharacter.value,
      graphDepth.value,
      shouldForceRefresh
    )
    
    // 请求完成后再渲染图表
    nextTick(() => {
      renderGraph()
    })
  } catch (error) {
    ElMessage.error('生成关系图失败')
  }
}

// 渲染关系图
function renderGraph() {
  if (!graphRef.value) return
  // 确保有关系图数据才进行渲染
  if (!analysisStore.relationshipGraph) {
    return
  }
  
  if (!graphChart.value) {
    graphChart.value = echarts.init(graphRef.value)
    
    // 添加点击事件
    graphChart.value.on('click', { dataType: 'node' }, (params) => {
      selectNode(params.data)
    })
    
    // 监听容器大小变化
    window.addEventListener('resize', () => {
      graphChart.value && graphChart.value.resize()
    })
  } else {
    // 强制刷新图表大小以适应容器
    graphChart.value.resize()
  }
  
  const graph = analysisStore.relationshipGraph
  
  // 过滤关系
  const filteredEdges = selectedRelationTypes.value.length
    ? graph.edges.filter(edge => selectedRelationTypes.value.includes(edge.relation))
    : graph.edges
  
  // 获取有效节点ID集合
  const validNodeIds = new Set()
  filteredEdges.forEach(edge => {
    validNodeIds.add(edge.source_id)
    validNodeIds.add(edge.target_id)
  })
  
  // 过滤节点
  const filteredNodes = graph.nodes.filter(node => validNodeIds.has(node.id))
  
  // 准备数据 - 为echarts创建正确格式的节点和边
  const nodes = filteredNodes.map(node => ({
    id: node.id,
    name: node.name,
    symbolSize: node.importance * 10 || 20,
    category: node.category || 0,
    label: {
      show: true
    },
    ...node
  }))
  
  // 创建一个从节点ID到数组索引的映射，解决边连接问题
  const nodeIdMap = {}
  nodes.forEach((node, index) => {
    nodeIdMap[node.id] = index
  })
  
  // 修改边的数据格式，确保source和target使用ECharts期望的格式
  const edges = filteredEdges.map(edge => {
    // 验证源节点和目标节点存在于节点列表中
    const sourceIndex = nodeIdMap[edge.source_id]
    const targetIndex = nodeIdMap[edge.target_id]
    
    // 只有当源节点和目标节点都存在时才创建边
    if (sourceIndex !== undefined && targetIndex !== undefined) {
      return {
        // 使用节点数组索引作为source和target (ECharts默认行为)
        source: sourceIndex,
        target: targetIndex,
        // 保留原始ID以便其他操作
        source_id: edge.source_id,
        target_id: edge.target_id,
        value: edge.relation,
        // 为边添加标签，显示关系类型
        label: {
          show: true,
          formatter: edge.relation,
          fontSize: 12,
          color: getRelationColor(edge.relation),
          backgroundColor: 'rgba(255, 255, 255, 0.7)',
          padding: [2, 4],
          borderRadius: 2
        },
        lineStyle: {
          width: edge.importance ? edge.importance * 1 : 2,
          curveness: 0.2,
          color: getRelationColor(edge.relation),
          type: getRelationLineType(edge.relation) // 使用不同的线条样式区分关系类型
        },
        emphasis: {
          lineStyle: {
            width: edge.importance ? edge.importance * 2 : 4,
            shadowBlur: 5,
            shadowColor: getRelationColor(edge.relation)
          },
          label: {
            fontSize: 14
          }
        },
        ...edge
      }
    }
    return null
  }).filter(edge => edge !== null)  // 过滤掉无效的边
  
  // 配置选项
  const options = {
    tooltip: {
      trigger: 'item',
      formatter: (params) => {
        if (params.dataType === 'node') {
          return `<strong>${params.data.name}</strong><br/>${params.data.description || ''}`
        } else {
          return `<strong>关系详情</strong><br/>
                 ${params.data.source_name} 
                 <span style="color:${getRelationColor(params.data.relation)}">
                   ${params.data.relation}
                 </span> 
                 ${params.data.target_name}<br/>
                 <span style="font-size:12px;color:#666">${params.data.description || ''}</span>`
        }
      },
      backgroundColor: 'rgba(255, 255, 255, 0.9)',
      borderColor: '#eee',
      borderWidth: 1,
      textStyle: {
        color: '#333'
      },
      extraCssText: 'box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);'
    },
    legend: {
      data: Array.from(new Set(nodes.map(node => node.category))).map(category => ({
        name: category || '其他'
      })),
      orient: 'vertical',
      right: 10,
      top: 20,
      textStyle: {
        color: '#666'
      },
      itemGap: 10,
      itemWidth: 15,
      itemHeight: 10
    },
    series: [{
      type: 'graph',
      layout: graphMode.value,
      data: nodes,
      links: edges,
      edgeSymbol: ['none', 'arrow'],
      edgeSymbolSize: 8,
      // 更好的视觉编码
      itemStyle: {
        borderWidth: 2,
        borderColor: '#fff',
        shadowColor: 'rgba(0, 0, 0, 0.2)',
        shadowBlur: 5
      },
      categories: Array.from(new Set(nodes.map(node => node.category))).map(category => ({
        name: category || '其他'
      })),
      roam: true,
      draggable: true,  // 允许节点拖拽
      focusNodeAdjacency: true,  // 鼠标悬停时突出相邻节点
      label: {
        position: 'right',
        formatter: '{b}',
        fontSize: 12,
        color: '#333',
        backgroundColor: 'rgba(255, 255, 255, 0.7)',
        padding: [3, 5],
        borderRadius: 3,
        show: true
      },
      emphasis: {
        focus: 'adjacency',
        lineStyle: {
          width: 4
        },
        label: {
          fontSize: 13,
          fontWeight: 'bold'
        },
        itemStyle: {
          shadowBlur: 10,
          shadowColor: 'rgba(0, 0, 0, 0.3)'
        }
      },
      force: {
        repulsion: 200,  // 增加节点间斥力，使图形更清晰
        gravity: 0.1,
        edgeLength: [80, 150],
        friction: 0.6
      },
      lineStyle: {
        color: 'source',
        curveness: 0.3,
        opacity: 0.8
      }
    }]
  }
  
  graphChart.value.setOption(options, true)
  
  // 重置选中节点
  selectedNode.value = null
}

// 选择节点
function selectNode(node) {
  selectedNode.value = node
}

// 导出图片
function exportImage() {
  if (!graphChart.value) return
  
  try {
    const url = graphChart.value.getDataURL({
      pixelRatio: 2,
      backgroundColor: '#fff'
    })
    
    const link = document.createElement('a')
    link.download = `关系网络图_${new Date().getTime()}.png`
    link.href = url
    link.click()
  } catch (error) {
    ElMessage.error('导出图片失败')
  }
}

// 导航到小说列表
function navigateToNovelList() {
  router.push('/novels/list')
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

// 获取关系线条颜色
function getRelationColor(relationType) {
  const colorMap = {
    '师徒': '#67C23A',
    '朋友': '#409EFF',
    '敌人': '#F56C6C',
    '亲人': '#E6A23C',
    '恋人': '#FC9DB1',
    '同门': '#9B55FF'
  }
  
  return colorMap[relationType] || '#909399'
}

// 获取关系线条类型
function getRelationLineType(relationType) {
  const typeMap = {
    '师徒': 'solid',
    '朋友': 'dashed',
    '敌人': 'dotted',
    '亲人': 'solid',
    '恋人': 'solid',
    '同门': 'dashed',
    '邻居': 'dotted',
    '主仆': 'dashed',
    '交易': 'dotted'
  }
  
  return typeMap[relationType] || 'solid'
}

// 切换关系类型筛选
function toggleRelationType(type) {
  // 获取当前选择的关系类型数组
  const currentTypes = selectedRelationTypes.value;
  
  // 检查点击的类型是否已被选中
  const index = currentTypes.indexOf(type);
  
  if (currentTypes.length === 0) {
    // 如果当前没有选择任何类型（显示全部），则只选中点击的类型
    selectedRelationTypes.value = [type];
  } else if (index === -1) {
    // 如果点击的类型不在当前选择中，添加它
    selectedRelationTypes.value.push(type);
  } else if (currentTypes.length === 1) {
    // 如果当前只有一个选择且点击的就是它，则清空选择（显示全部）
    selectedRelationTypes.value = [];
  } else {
    // 如果有多个选择，则移除点击的类型
    selectedRelationTypes.value.splice(index, 1);
  }
  
  // 重新渲染图表
  nextTick(() => {
    renderGraph();
  });
}

// 专门用于强制重新分析的函数
async function forceReanalyze() {
  if (!selectedNovel.value) return
  
  try {
    // 修改为使用store中的loading状态
    analysisStore.loading = true
    
    // 直接发起API请求，绕过store的缓存逻辑
    console.log('[DEBUG] 直接发起强制刷新请求');
    
    const response = await analysisApi.getRelationshipGraph({
      novel_id: selectedNovel.value,
      character_id: selectedCharacter.value,
      depth: graphDepth.value,
      force_refresh: true, // 强制设置为true
      _timestamp: new Date().getTime() // 添加时间戳避免缓存
    });
    
    // 更新图表数据
    analysisStore.relationshipGraph = response.data;
    
    // 渲染图表
    nextTick(() => {
      renderGraph();
    });
    
    // 提示用户
    ElMessage.success('已成功重新分析关系网络');
  } catch (error) {
    ElMessage.error('强制重新分析失败');
    console.error('[DEBUG] 强制重新分析失败:', error);
  } finally {
    analysisStore.loading = false;
  }
}
</script>

<style scoped>
.relationship-container {
  height: 100%;
  width: 100%;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 10px;
  width: 100%;
}

.page-header h2 {
  margin: 0;
}

.header-actions {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

.loading-container {
  padding: 20px 0;
  width: 100%;
}

.graph-container {
  display: flex;
  flex-direction: column;
  height: calc(100vh - 260px);
  min-height: 500px;
  width: 100%;
  position: relative;
}

.graph-toolbar {
  display: flex;
  justify-content: space-between;
  margin-bottom: 10px;
  padding: 5px 0;
  width: 100%;
}

.graph-view {
  flex: 1;
  border: 1px solid #ebeef5;
  border-radius: 4px;
  overflow: hidden;
  width: 100%;
}

.graph-info {
  margin-top: 20px;
  height: 150px;
  overflow-y: auto;
  padding: 10px;
  border: 1px solid #ebeef5;
  border-radius: 4px;
  background-color: #f5f7fa;
}

.node-info h3 {
  margin-top: 0;
  margin-bottom: 10px;
}

.node-info p {
  color: #606266;
}

.relations-list {
  margin-top: 10px;
}

.relations-list h4 {
  margin-top: 0;
  margin-bottom: 10px;
}

.graph-hint {
  color: #909399;
  text-align: center;
  padding: 20px 0;
}

.text-muted {
  font-size: 12px;
  color: #909399;
  margin-top: 8px;
  text-align: center;
}

.no-relations {
  color: #909399;
  font-size: 13px;
  margin-top: 5px;
  font-style: italic;
}

.relation-legend {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 10px;
  padding: 5px;
  background-color: #f5f7fa;
  border-radius: 4px;
}

.legend-item {
  display: flex;
  align-items: center;
  padding: 2px 8px;
  font-size: 12px;
  color: #666;
  border-radius: 3px;
  cursor: pointer;
  border: 1px solid transparent;
  opacity: 0.7;
  transition: all 0.2s;
}

.legend-item:hover {
  background-color: #eee;
  opacity: 1;
}

.legend-item-active {
  border-color: #dcdfe6;
  background-color: #fff;
  opacity: 1;
}

.legend-item-inactive {
  opacity: 0.4;
}

.relation-color-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  margin-right: 5px;
  display: inline-block;
}

.loading-overlay {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-color: rgba(255, 255, 255, 0.8);
  display: flex;
  justify-content: center;
  align-items: center;
  flex-direction: column;
  z-index: 10;
  border-radius: 4px;
}

.loading-overlay .el-icon {
  font-size: 24px;
  color: var(--el-color-primary);
  margin-bottom: 10px;
}

.loading-overlay span {
  color: var(--el-color-primary);
  font-size: 14px;
}
</style> 