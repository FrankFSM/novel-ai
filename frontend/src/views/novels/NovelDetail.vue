<template>
  <div class="novel-detail-container">
    <!-- 加载中 -->
    <div v-if="loading" class="loading-container">
      <el-skeleton style="width: 100%" animated>
        <template #template>
          <el-skeleton-item variant="image" style="width: 240px; height: 340px;" />
          <div style="padding: 14px">
            <el-skeleton-item variant="h1" style="width: 50%" />
            <div style="display: flex; align-items: center; margin-top: 16px">
              <el-skeleton-item variant="text" style="margin-right: 16px; width: 30%" />
              <el-skeleton-item variant="text" style="width: 30%" />
            </div>
            <el-skeleton-item variant="text" style="width: 100%; margin-top: 16px" />
            <el-skeleton-item variant="text" style="width: 100%" />
          </div>
        </template>
      </el-skeleton>
    </div>
    
    <!-- 小说不存在 -->
    <el-empty v-else-if="!novel" description="小说不存在或已被删除">
      <el-button type="primary" @click="navigateToList">返回列表</el-button>
    </el-empty>
    
    <!-- 小说详情 -->
    <div v-else>
      <!-- 基本信息卡片 -->
      <el-card shadow="never" class="info-card">
        <div class="novel-info">
          <div class="novel-cover">
            <el-image 
              :src="novel.cover_url || 'https://cube.elemecdn.com/3/7c/3ea6beec64369c2642b92c6726f1epng.png'" 
              fit="cover"
              :preview-src-list="novel.cover_url ? [novel.cover_url] : []"
            />
          </div>
          <div class="novel-details">
            <h1 class="novel-title">{{ novel.title }}</h1>
            <div class="novel-meta">
              <div class="meta-item">
                <el-icon><UserFilled /></el-icon>
                <span>{{ novel.author }}</span>
              </div>
              <div class="meta-item">
                <el-icon><Calendar /></el-icon>
                <span>创建于 {{ formatDate(novel.created_at) }}</span>
              </div>
              <div v-if="novel.chapters_count" class="meta-item">
                <el-icon><Document /></el-icon>
                <span>{{ novel.chapters_count }} 章节</span>
              </div>
              <div v-if="novel.characters_count" class="meta-item">
                <el-icon><Avatar /></el-icon>
                <span>{{ novel.characters_count }} 角色</span>
              </div>
            </div>
            <div class="novel-description">
              <p>{{ novel.description }}</p>
            </div>
            <div class="novel-actions">
              <el-button type="primary" @click="startQA">开始问答</el-button>
              <el-button type="success" @click="startAnalysis">分析小说</el-button>
              <el-button type="danger" @click="confirmDelete">删除小说</el-button>
            </div>
          </div>
        </div>
      </el-card>
      
      <!-- 内容标签页 -->
      <el-card shadow="never" class="content-card">
        <el-tabs v-model="activeTab">
          <!-- 统计信息 -->
          <el-tab-pane label="统计信息" name="statistics">
            <div class="statistics-container">
              <el-card v-if="!statisticsLoaded" shadow="hover" class="empty-statistics">
                <div class="centered-content">
                  <p>小说统计数据尚未生成</p>
                  <el-button type="primary" @click="generateStatistics" :loading="generatingStats">
                    {{ generatingStats ? '生成中...' : '生成统计数据' }}
                  </el-button>
                </div>
              </el-card>
              
              <div v-else class="statistics-grid">
                <el-card shadow="hover" class="stat-card">
                  <template #header>
                    <div class="stat-header">
                      <h3>章节统计</h3>
                    </div>
                  </template>
                  <div class="stat-content">
                    <div class="stat-item">
                      <div class="stat-value">{{ statistics.chapterCount || 0 }}</div>
                      <div class="stat-label">总章节数</div>
                    </div>
                    <div class="stat-item">
                      <div class="stat-value">{{ statistics.totalWords?.toLocaleString() || 0 }}</div>
                      <div class="stat-label">总字数</div>
                    </div>
                    <div class="stat-item">
                      <div class="stat-value">{{ formatNumber(statistics.avgWordsPerChapter) }}</div>
                      <div class="stat-label">平均章节字数</div>
                    </div>
                  </div>
                </el-card>
                
                <el-card shadow="hover" class="stat-card">
                  <template #header>
                    <div class="stat-header">
                      <h3>人物统计</h3>
                    </div>
                  </template>
                  <div class="stat-content">
                    <div class="stat-item">
                      <div class="stat-value">{{ statistics.characterCount || 0 }}</div>
                      <div class="stat-label">角色总数</div>
                    </div>
                    <div class="stat-item">
                      <div class="stat-value">{{ statistics.mainCharacterCount || 0 }}</div>
                      <div class="stat-label">主要角色</div>
                    </div>
                    <div class="stat-item">
                      <div class="stat-value">{{ statistics.relationshipCount || 0 }}</div>
                      <div class="stat-label">关系总数</div>
                    </div>
                  </div>
                </el-card>
                
                <el-card shadow="hover" class="stat-card">
                  <template #header>
                    <div class="stat-header">
                      <h3>其他统计</h3>
                    </div>
                  </template>
                  <div class="stat-content">
                    <div class="stat-item">
                      <div class="stat-value">{{ statistics.locationCount || 0 }}</div>
                      <div class="stat-label">地点数量</div>
                    </div>
                    <div class="stat-item">
                      <div class="stat-value">{{ statistics.itemCount || 0 }}</div>
                      <div class="stat-label">物品数量</div>
                    </div>
                    <div class="stat-item">
                      <div class="stat-value">{{ statistics.eventCount || 0 }}</div>
                      <div class="stat-label">事件数量</div>
                    </div>
                  </div>
                </el-card>
              </div>
            </div>
          </el-tab-pane>
          
          <!-- 章节列表 -->
          <el-tab-pane label="章节列表" name="chapters">
            <div class="chapters-container">
              <el-empty v-if="!chapters.length" description="暂无章节信息">
                <el-button type="primary" @click="extractEntities" :loading="extracting">提取实体</el-button>
              </el-empty>
              
              <el-table v-else :data="chapters" style="width: 100%" max-height="500">
                <el-table-column type="index" width="50" />
                <el-table-column prop="number" label="序号" width="80" />
                <el-table-column prop="title" label="章节标题" min-width="200" />
                <el-table-column prop="word_count" label="字数" width="100">
                  <template #default="scope">
                    {{ scope.row.word_count?.toLocaleString() || '-' }}
                  </template>
                </el-table-column>
                <el-table-column label="操作" width="180">
                  <template #default="scope">
                    <el-button link type="primary" @click="previewChapter(scope.row)">
                      预览
                    </el-button>
                  </template>
                </el-table-column>
              </el-table>
            </div>
          </el-tab-pane>
          
          <!-- 角色列表 -->
          <el-tab-pane label="角色列表" name="characters">
            <div class="characters-container">
              <el-empty v-if="!characters.length" description="暂无角色信息">
                <el-button type="primary" @click="extractEntities" :loading="extracting">提取实体</el-button>
              </el-empty>
              
              <el-table v-else :data="characters" style="width: 100%" max-height="500">
                <el-table-column type="index" width="50" />
                <el-table-column prop="name" label="名称" min-width="150" />
                <el-table-column prop="alias" label="别名" min-width="200">
                  <template #default="scope">
                    <el-tag v-for="alias in scope.row.alias" :key="alias" size="small" style="margin-right: 5px">
                      {{ alias }}
                    </el-tag>
                  </template>
                </el-table-column>
                <el-table-column prop="description" label="描述" min-width="250" :show-overflow-tooltip="true" />
                <el-table-column label="操作" width="180">
                  <template #default="scope">
                    <el-button link type="primary" @click="viewCharacterJourney(scope.row.id)">
                      角色旅程
                    </el-button>
                  </template>
                </el-table-column>
              </el-table>
            </div>
          </el-tab-pane>
        </el-tabs>
      </el-card>
    </div>
    
    <!-- 章节预览对话框 -->
    <el-dialog
      v-model="chapterDialogVisible"
      :title="selectedChapter?.title || '章节预览'"
      width="60%"
    >
      <div class="chapter-content" v-if="selectedChapter">
        <div class="chapter-header">
          <h3>{{ selectedChapter.title }}</h3>
          <div class="chapter-meta">
            <span>字数：{{ selectedChapter.word_count?.toLocaleString() || '未知' }}</span>
          </div>
        </div>
        <div class="chapter-text">
          <p v-for="(paragraph, index) in formatChapterContent(selectedChapter.content)" :key="index">
            {{ paragraph }}
          </p>
        </div>
      </div>
    </el-dialog>
    
    <!-- 删除确认对话框 -->
    <el-dialog
      v-model="deleteDialogVisible"
      title="确认删除"
      width="30%"
    >
      <span>确定要删除小说《{{ novel?.title }}》吗？此操作不可恢复！</span>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="deleteDialogVisible = false">取消</el-button>
          <el-button type="danger" @click="deleteNovel">确定删除</el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watchEffect } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useNovelStore } from '@/store/novel'
import { ElMessage, ElMessageBox } from 'element-plus'
import { 
  UserFilled, 
  Calendar, 
  Document, 
  Avatar 
} from '@element-plus/icons-vue'
import { novelApi } from '@/api'

const route = useRoute()
const router = useRouter()
const novelStore = useNovelStore()

// 本地状态
const loading = ref(true)
const activeTab = ref('statistics')
const chapters = ref([])
const characters = ref([])
const statistics = ref({})
const statisticsLoaded = ref(false)
const generatingStats = ref(false)
const extracting = ref(false)

// 章节预览状态
const chapterDialogVisible = ref(false)
const selectedChapter = ref(null)

// 删除确认状态
const deleteDialogVisible = ref(false)

// 小说ID和详情
const novelId = computed(() => Number(route.params.id))
const novel = computed(() => {
  return novelStore.novels.find(n => n.id === novelId.value) || null
})

// 初始化
onMounted(async () => {
  try {
    await loadNovelData()
  } catch (error) {
    ElMessage.error('获取小说详情失败')
  } finally {
    loading.value = false
  }
})

// 加载小说数据
async function loadNovelData() {
  // 如果小说列表为空，先获取列表
  if (novelStore.novels.length === 0) {
    await novelStore.fetchNovels()
  }
  
  // 如果小说不存在或需要获取详情，获取详情
  if (!novel.value || !novel.value.chapters_count) {
    await novelStore.fetchNovelDetail(novelId.value)
  }
  
  // 加载统计数据
  await loadStatistics()
  
  // 加载章节列表（模拟数据）
  // TODO: 实际项目中应从 API 获取
  chapters.value = generateMockChapters()
  
  // 加载角色列表（模拟数据）
  // TODO: 实际项目中应从 API 获取 
  characters.value = generateMockCharacters()
}

// 加载统计数据
async function loadStatistics() {
  try {
    // TODO: 实际项目中应从 API 获取
    // const response = await novelApi.getNovelStatistics(novelId.value)
    // statistics.value = response.data
    
    // 模拟数据
    statistics.value = {
      chapterCount: novel.value?.chapters_count || 0,
      totalWords: 150000,
      avgWordsPerChapter: 5000,
      characterCount: novel.value?.characters_count || 0,
      mainCharacterCount: 5,
      relationshipCount: 20,
      locationCount: 15,
      itemCount: 30,
      eventCount: 45
    }
    
    statisticsLoaded.value = true
  } catch (error) {
    console.error('获取统计数据失败', error)
    statisticsLoaded.value = false
  }
}

// 生成统计数据
async function generateStatistics() {
  generatingStats.value = true
  
  try {
    // TODO: 实际项目中应调用 API 生成统计
    // await novelApi.generateStatistics(novelId.value)
    
    // 模拟延迟
    await new Promise(resolve => setTimeout(resolve, 1500))
    
    // 重新加载统计
    await loadStatistics()
    
    ElMessage.success('统计数据生成成功')
  } catch (error) {
    ElMessage.error('统计数据生成失败')
  } finally {
    generatingStats.value = false
  }
}

// 提取实体
async function extractEntities() {
  extracting.value = true
  
  try {
    // 调用API提取实体
    await novelApi.extractNovelEntities(novelId.value)
    
    ElMessage.success('实体提取任务已启动，将在后台处理')
    
    // 模拟延迟后加载数据
    setTimeout(async () => {
      try {
        await loadNovelData()
        ElMessage.success('实体提取完成')
      } finally {
        extracting.value = false
      }
    }, 3000)
  } catch (error) {
    ElMessage.error('实体提取失败')
    extracting.value = false
  }
}

// 预览章节
function previewChapter(chapter) {
  selectedChapter.value = chapter
  chapterDialogVisible.value = true
}

// 查看角色旅程
function viewCharacterJourney(characterId) {
  router.push(`/analysis/characters?novelId=${novelId.value}&characterId=${characterId}`)
}

// 开始问答
function startQA() {
  // 设置当前小说
  novelStore.setCurrentNovel(novelId.value)
  // 导航到问答页面
  router.push('/qa')
}

// 开始分析
function startAnalysis() {
  router.push(`/analysis/relationships?novelId=${novelId.value}`)
}

// 确认删除
function confirmDelete() {
  deleteDialogVisible.value = true
}

// 删除小说
async function deleteNovel() {
  try {
    await novelStore.deleteNovel(novelId.value)
    deleteDialogVisible.value = false
    ElMessage.success('小说删除成功')
    router.push('/novels/list')
  } catch (error) {
    ElMessage.error('删除小说失败')
  }
}

// 返回列表
function navigateToList() {
  router.push('/novels/list')
}

// 格式化日期
function formatDate(dateString) {
  if (!dateString) return '-'
  
  const date = new Date(dateString)
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

// 格式化数字
function formatNumber(num) {
  if (num === undefined || num === null) return '0'
  return Number(num).toLocaleString()
}

// 格式化章节内容
function formatChapterContent(content) {
  if (!content) return []
  
  // 按段落分割
  return content.split('\n').filter(paragraph => paragraph.trim() !== '')
}

// 生成模拟章节数据
function generateMockChapters() {
  const count = novel.value?.chapters_count || 10
  const chapters = []
  
  for (let i = 1; i <= count; i++) {
    chapters.push({
      id: i,
      number: i,
      title: `第${i}章 ${i % 3 === 0 ? '惊天大战' : i % 3 === 1 ? '神秘来客' : '隐藏真相'}`,
      word_count: Math.floor(3000 + Math.random() * 4000),
      content: `这是第${i}章的内容。\n\n这是一个段落。\n\n这是另一个段落，包含了这一章的主要内容和情节发展。`
    })
  }
  
  return chapters
}

// 生成模拟角色数据
function generateMockCharacters() {
  const count = novel.value?.characters_count || 5
  const characters = []
  
  const names = ['林远', '沈清雪', '张天志', '李墨', '王霜', '赵云', '钱多多', '孙小圣']
  const descriptions = [
    '主角，拥有神秘血脉',
    '女主角，冰系法术天才',
    '男主角的挚友，武道奇才',
    '隐世宗门弟子',
    '神秘组织成员',
    '资深猎人，身手不凡',
    '富商之女，精通商业',
    '顽皮捣蛋，身份成谜'
  ]
  
  for (let i = 0; i < count; i++) {
    const nameIndex = i % names.length
    characters.push({
      id: i + 1,
      name: names[nameIndex],
      alias: generateAliases(names[nameIndex]),
      description: descriptions[nameIndex]
    })
  }
  
  return characters
}

// 生成模拟别名
function generateAliases(name) {
  const count = Math.floor(Math.random() * 3)
  const aliases = []
  
  const prefixes = ['小', '老', '大']
  const suffixes = ['哥', '姐', '兄', '弟']
  
  for (let i = 0; i < count; i++) {
    if (i === 0 && name.length <= 2) {
      aliases.push(name.charAt(name.length - 1))
    } else {
      const prefix = prefixes[Math.floor(Math.random() * prefixes.length)]
      const suffix = suffixes[Math.floor(Math.random() * suffixes.length)]
      aliases.push(i % 2 === 0 ? prefix + name.charAt(name.length - 1) : name.charAt(name.length - 1) + suffix)
    }
  }
  
  return aliases
}
</script>

<style scoped>
.novel-detail-container {
  height: 100%;
}

.loading-container {
  padding: 20px;
}

.info-card {
  margin-bottom: 20px;
}

.novel-info {
  display: flex;
  gap: 30px;
}

.novel-cover {
  width: 240px;
  height: 340px;
  flex-shrink: 0;
  border-radius: 4px;
  overflow: hidden;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
}

.novel-cover :deep(.el-image) {
  width: 100%;
  height: 100%;
}

.novel-details {
  flex: 1;
}

.novel-title {
  margin-top: 0;
  margin-bottom: 20px;
  font-size: 24px;
}

.novel-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 20px;
  margin-bottom: 20px;
}

.meta-item {
  display: flex;
  align-items: center;
  color: #606266;
}

.meta-item .el-icon {
  margin-right: 5px;
}

.novel-description {
  margin-bottom: 30px;
  color: #606266;
  line-height: 1.6;
}

.novel-actions {
  display: flex;
  gap: 10px;
}

.content-card {
  min-height: 500px;
}

/* 统计样式 */
.statistics-container {
  min-height: 300px;
}

.empty-statistics {
  height: 200px;
}

.centered-content {
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  height: 100%;
  gap: 20px;
}

.statistics-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 20px;
}

.stat-card {
  height: 100%;
}

.stat-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.stat-header h3 {
  margin: 0;
}

.stat-content {
  display: flex;
  justify-content: space-around;
  padding: 20px 0;
}

.stat-item {
  text-align: center;
}

.stat-value {
  font-size: 28px;
  font-weight: bold;
  color: #409EFF;
  margin-bottom: 5px;
}

.stat-label {
  color: #909399;
  font-size: 14px;
}

/* 章节内容样式 */
.chapter-content {
  max-height: 60vh;
  overflow-y: auto;
}

.chapter-header {
  margin-bottom: 20px;
  padding-bottom: 10px;
  border-bottom: 1px solid #ebeef5;
}

.chapter-header h3 {
  margin: 0 0 10px 0;
}

.chapter-meta {
  color: #909399;
  font-size: 14px;
}

.chapter-text {
  line-height: 1.8;
  text-indent: 2em;
}
</style> 