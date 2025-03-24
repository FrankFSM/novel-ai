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
              @click="generateGraph" 
              :disabled="!selectedNovel"
              :loading="analysisStore.loading"
            >
              生成关系图
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
      
      <!-- 加载中状态 -->
      <div v-else-if="analysisStore.loading" class="loading-container">
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
        <el-button type="primary" @click="generateGraph">生成关系图</el-button>
      </el-empty>
      
      <!-- 关系图 -->
      <div v-else class="graph-container">
        <div class="graph-toolbar">
          <el-radio-group v-model="graphMode" size="small">
            <el-radio-button value="force">力导向图</el-radio-button>
            <el-radio-button value="circular">环形图</el-radio-button>
          </el-radio-group>
          
          <el-select v-model="selectedRelationType" clearable placeholder="筛选关系类型" size="small">
            <el-option
              v-for="type in relationTypes"
              :key="type"
              :label="type"
              :value="type"
            />
          </el-select>
          
          <el-tooltip content="将图表导出为图片">
            <el-button size="small" @click="exportImage">
              <el-icon><Download /></el-icon>
            </el-button>
          </el-tooltip>
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
              >
                {{ relation.source }} {{ relation.type }} {{ relation.target }}
              </el-tag>
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
import { Download } from '@element-plus/icons-vue'
import * as echarts from 'echarts'

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
const selectedRelationType = ref('')
const selectedNode = ref(null)

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
    
    // 自动生成图表
    generateGraph()
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
watch(selectedRelationType, () => {
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
  
  return analysisStore.relationshipGraph.edges
    .filter(edge => 
      edge.source_id === selectedNode.value.id || 
      edge.target_id === selectedNode.value.id
    )
    .map(edge => ({
      id: edge.id,
      source: edge.source_name,
      target: edge.target_name,
      type: edge.relation
    }))
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

// 生成关系图
async function generateGraph() {
  if (!selectedNovel.value) return
  
  try {
    // 调用后端API获取真实的关系网络数据
    await analysisStore.fetchRelationshipGraph(
      selectedNovel.value,
      selectedCharacter.value,
      graphDepth.value
    )
    
    nextTick(() => {
      renderGraph()
    })
  } catch (error) {
    ElMessage.error('生成关系图失败')
  }
}

// 渲染关系图
function renderGraph() {
  if (!graphRef.value || !analysisStore.relationshipGraph) return
  
  if (!graphChart.value) {
    graphChart.value = echarts.init(graphRef.value)
    
    // 添加点击事件
    graphChart.value.on('click', { dataType: 'node' }, (params) => {
      selectNode(params.data)
    })
    
    // 监听容器大小变化
    window.addEventListener('resize', () => {
      graphChart.value.resize()
    })
  } else {
    // 强制刷新图表大小以适应容器
    graphChart.value.resize()
  }
  
  const graph = analysisStore.relationshipGraph
  
  // 过滤关系
  const filteredEdges = selectedRelationType.value
    ? graph.edges.filter(edge => edge.relation === selectedRelationType.value)
    : graph.edges
  
  // 获取有效节点ID集合
  const validNodeIds = new Set()
  filteredEdges.forEach(edge => {
    validNodeIds.add(edge.source_id)
    validNodeIds.add(edge.target_id)
  })
  
  // 过滤节点
  const filteredNodes = graph.nodes.filter(node => validNodeIds.has(node.id))
  
  // 准备数据
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
  
  const edges = filteredEdges.map(edge => ({
    source: edge.source_id,
    target: edge.target_id,
    value: edge.relation,
    lineStyle: {
      width: edge.importance ? edge.importance * 1 : 2,
      curveness: 0.2,
      color: getRelationColor(edge.relation)
    },
    ...edge
  }))
  
  // 配置选项
  const options = {
    tooltip: {
      trigger: 'item',
      formatter: (params) => {
        if (params.dataType === 'node') {
          return `<strong>${params.data.name}</strong><br/>${params.data.description || ''}`
        } else {
          return `${params.data.source_name} <strong>${params.data.relation}</strong> ${params.data.target_name}`
        }
      }
    },
    legend: {
      data: Array.from(new Set(nodes.map(node => node.category))).map(category => ({
        name: category || '其他'
      })),
      orient: 'vertical',
      right: 10,
      top: 20
    },
    series: [{
      type: 'graph',
      layout: graphMode.value,
      data: nodes,
      links: edges,
      categories: Array.from(new Set(nodes.map(node => node.category))).map(category => ({
        name: category || '其他'
      })),
      roam: true,
      label: {
        position: 'right',
        formatter: '{b}'
      },
      emphasis: {
        focus: 'adjacency',
        lineStyle: {
          width: 4
        }
      },
      force: {
        repulsion: 100,
        gravity: 0.1,
        edgeLength: [50, 100]
      },
      lineStyle: {
        color: 'source',
        curveness: 0.3
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
</style> 