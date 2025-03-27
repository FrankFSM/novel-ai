<template>
  <div class="character-list-container">
    <el-card shadow="never">
      <template #header>
        <div class="page-header">
          <h2>角色列表</h2>
          <div class="header-actions">
            <el-select 
              v-model="selectedNovel" 
              placeholder="请选择小说" 
              @change="handleNovelChange"
              :loading="novelStore.loading"
              class="full-width-select"
            >
              <el-option
                v-for="novel in novelStore.novels"
                :key="novel.id"
                :label="novel.title"
                :value="novel.id"
              />
            </el-select>
            
            <el-button 
              type="primary" 
              @click="analyzeCharacters" 
              :disabled="!selectedNovel"
              :loading="loading"
              class="analyze-button"
            >
              分析角色
            </el-button>
          </div>
        </div>
      </template>
      
      <!-- 未选择小说的提示 -->
      <el-empty 
        v-if="!selectedNovel" 
        description="请从上方选择小说"
      >
        <el-button type="primary" @click="navigateToNovelList">浏览小说列表</el-button>
      </el-empty>
      
      <!-- 加载中状态 -->
      <div v-else-if="loading" class="loading-container">
        <el-skeleton :rows="5" animated />
        <div class="loading-text">正在分析小说角色...</div>
      </div>
      
      <!-- 角色列表为空的提示 -->
      <el-empty 
        v-else-if="characters.length === 0" 
        description="暂无角色数据，点击上方按钮分析角色"
      >
        <el-button type="primary" @click="analyzeCharacters">分析角色</el-button>
      </el-empty>
      
      <!-- 角色列表 -->
      <div v-else class="character-list">
        <el-row :gutter="20">
          <el-col 
            v-for="character in characters" 
            :key="character.id"
            :xs="24" 
            :sm="12" 
            :md="8" 
            :lg="6"
            class="character-col"
          >
            <el-card 
              class="character-card" 
              :body-style="{ padding: '10px' }"
              shadow="hover"
            >
              <div class="character-avatar">
                <el-avatar 
                  :size="80" 
                  :src="getRandomAvatar(character.id)"
                />
              </div>
              
              <div class="character-info">
                <h3 class="character-name">
                  {{ character.name }}
                  <el-tag 
                    v-if="character.importance >= 5" 
                    type="danger" 
                    size="small"
                  >
                    主角
                  </el-tag>
                  <el-tag 
                    v-else-if="character.importance >= 4" 
                    type="warning" 
                    size="small"
                  >
                    重要
                  </el-tag>
                </h3>
                
                <div class="character-description">
                  {{ truncateText(character.description, 60) || '暂无描述' }}
                </div>
                
                <div class="character-aliases" v-if="character.alias && character.alias.length">
                  <div class="aliases-label">别名：</div>
                  <div class="alias-tags">
                    <el-tag 
                      v-for="alias in character.alias.slice(0, 3)" 
                      :key="alias" 
                      size="small" 
                      effect="plain"
                      class="alias-tag"
                    >
                      {{ alias }}
                    </el-tag>
                    <span v-if="character.alias.length > 3">等{{ character.alias.length }}个</span>
                  </div>
                </div>
                
                <div class="character-actions">
                  <el-button 
                    type="primary" 
                    size="small" 
                    @click="viewCharacterDetails(character.id)"
                  >
                    详细信息
                  </el-button>
                  
                  <el-button 
                    type="success" 
                    size="small" 
                    @click="viewCharacterJourney(character.id)"
                  >
                    角色旅程
                  </el-button>
                </div>
              </div>
            </el-card>
          </el-col>
        </el-row>
      </div>
    </el-card>

    <!-- 新增: 章节选择对话框 -->
    <el-dialog
      v-model="chapterDialogVisible"
      title="选择章节进行分析"
      width="500px"
    >
      <div class="chapter-selection-content">
        <p class="dialog-description">选择要分析的章节范围：</p>
        
        <el-form label-position="top">
          <el-form-item label="起始章节">
            <el-select 
              v-model="startChapter" 
              placeholder="选择起始章节"
              class="full-width-select"
            >
              <el-option
                v-for="chapter in chapters"
                :key="chapter.id"
                :label="chapter.title || `第${chapter.chapter_number}章`"
                :value="chapter.id"
              />
            </el-select>
          </el-form-item>
          
          <el-form-item label="结束章节">
            <el-select 
              v-model="endChapter" 
              placeholder="选择结束章节"
              class="full-width-select"
            >
              <el-option
                v-for="chapter in chapters"
                :key="chapter.id"
                :label="chapter.title || `第${chapter.chapter_number}章`"
                :value="chapter.id"
              />
            </el-select>
          </el-form-item>
        </el-form>
      </div>
      
      <template #footer>
        <div class="dialog-footer">
          <el-button @click="chapterDialogVisible = false">取消</el-button>
          <el-button 
            type="primary" 
            @click="analyzeCharactersByChapter"
            :loading="loading"
          >
            开始分析
          </el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useNovelStore } from '@/store/novel'
import { ElMessage } from 'element-plus'
import { characterApi } from '@/api'
import { novelApi } from '@/api'

const router = useRouter()
const route = useRoute()
const novelStore = useNovelStore()

// 本地状态
const selectedNovel = ref(null)
const characters = ref([])
const loading = ref(false)

// 新增: 章节选择对话框相关状态
const chapterDialogVisible = ref(false)
const chapters = ref([])
const startChapter = ref(null)
const endChapter = ref(null)

// 处理生命周期
onMounted(async () => {
  // 加载小说列表
  if (novelStore.novels.length === 0) {
    await novelStore.fetchNovels()
  }
  
  // 从URL参数获取小说ID
  const novelId = Number(route.query.novelId)
  if (novelId && !isNaN(novelId)) {
    selectedNovel.value = novelId
    await loadCharacters(novelId)
  }
})

// 加载角色列表
async function loadCharacters(novelId, forceRefresh = false) {
  if (!novelId) return
  
  try {
    characters.value = []
    loading.value = true
    
    // 调用API获取角色列表 - 根据forceRefresh参数决定是获取现有角色还是分析角色
    let data
    if (forceRefresh) {
      // 强制刷新时分析角色
      data = await characterApi.analyzeCharacters(novelId, forceRefresh)
      console.log('角色分析API响应:', data)
      ElMessage.success(`角色分析完成，共发现${data.length}个角色`)
    } else {
      // 非强制刷新时只获取现有角色
      data = await characterApi.getNovelCharacters(novelId)
      console.log('获取角色列表响应:', data)
      // 处理不同的API响应格式
      if (data && data.characters) {
        data = data.characters
      }
    }
    
    if (data && Array.isArray(data)) {
      // 按重要性排序
      characters.value = [...data].sort((a, b) => 
        (b.importance || 0) - (a.importance || 0)
      )
      if (!forceRefresh) {
        ElMessage.success(`成功加载${data.length}个角色`)
      }
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
  await loadCharacters(novelId, false)  // 不强制刷新，只获取现有角色
  
  // 更新URL参数
  router.replace({
    query: { ...route.query, novelId }
  })
}

// 手动分析角色按钮处理
async function analyzeCharacters() {
  if (!selectedNovel.value) return
  
  try {
    // 显示章节选择对话框
    await loadNovelChapters(selectedNovel.value)
    chapterDialogVisible.value = true
  } catch (error) {
    ElMessage.error('无法加载章节列表: ' + (error.message || '未知错误'))
  }
}

// 获取小说章节列表
async function loadNovelChapters(novelId) {
  try {
    loading.value = true
    const response = await novelApi.getNovelChapters(novelId)
    chapters.value = response.data || []
    if (chapters.value.length > 0) {
      // 默认选择第一章和最后一章
      startChapter.value = chapters.value[0].id
      endChapter.value = chapters.value[chapters.value.length - 1].id
    }
  } catch (error) {
    console.error('获取章节列表失败:', error)
    throw error
  } finally {
    loading.value = false
  }
}

// 根据章节范围分析角色
async function analyzeCharactersByChapter() {
  if (!selectedNovel.value || !startChapter.value || !endChapter.value) {
    ElMessage.warning('请选择完整的章节范围')
    return
  }
  
  try {
    loading.value = true
    chapterDialogVisible.value = false
    
    // 使用新的API进行章节范围分析
    const data = await characterApi.analyzeCharactersByChapter(
      selectedNovel.value, 
      startChapter.value, 
      endChapter.value
    )
    
    if (data && Array.isArray(data)) {
      // 按重要性排序
      characters.value = [...data].sort((a, b) => 
        (b.importance || 0) - (a.importance || 0)
      )
      ElMessage.success(`章节角色分析完成，共发现${data.length}个角色`)
    } else {
      ElMessage.warning('获取到的角色列表为空')
      characters.value = []
    }
  } catch (error) {
    console.error('章节角色分析失败:', error)
    ElMessage.error('章节角色分析失败: ' + (error.message || '未知错误'))
  } finally {
    loading.value = false
  }
}

// 导航到小说列表
function navigateToNovelList() {
  router.push('/novels/list')
}

// 查看角色详情
function viewCharacterDetails(characterId) {
  ElMessage.info('角色详情功能开发中')
  // TODO: 实现角色详情页面
}

// 查看角色旅程
function viewCharacterJourney(characterId) {
  router.push({
    path: '/analysis/characters/journey',
    query: { 
      novelId: selectedNovel.value,
      characterId: characterId
    }
  })
}

// 获取随机头像（用于显示）
function getRandomAvatar(id) {
  return `https://avatars.dicebear.com/api/avataaars/${id || Math.random()}.svg`
}

// 截断文本
function truncateText(text, maxLength) {
  if (!text) return text
  if (text.length <= maxLength) return text
  return text.substring(0, maxLength) + '...'
}
</script>

<style scoped>
.character-list-container {
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
  margin-bottom: 15px;
  position: sticky;
  top: 0;
  background-color: white;
  z-index: 10;
  padding: 10px 0;
}

.page-header h2 {
  margin: 0;
}

.header-actions {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
  align-items: center;
}

.full-width-select {
  min-width: 180px;
}

.analyze-button {
  white-space: nowrap;
}

.loading-container {
  padding: 20px 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 200px;
}

.loading-text {
  text-align: center;
  margin-top: 20px;
  color: #909399;
}

.character-list {
  margin-top: 20px;
  overflow: visible;
  padding-bottom: 30px;
}

.character-col {
  margin-bottom: 20px;
}

.character-card {
  height: 100%;
  transition: transform 0.3s;
  display: flex;
  flex-direction: column;
}

.character-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 10px 20px rgba(0,0,0,0.1);
}

.character-avatar {
  display: flex;
  justify-content: center;
  margin-bottom: 10px;
  padding-top: 15px;
}

.character-info {
  text-align: center;
  flex: 1;
  display: flex;
  flex-direction: column;
  padding: 0 10px 10px;
}

.character-name {
  margin: 10px 0;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-wrap: wrap;
  gap: 8px;
}

.character-description {
  color: #606266;
  margin-bottom: 10px;
  min-height: 60px;
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
}

.character-aliases {
  margin-bottom: 15px;
  flex: 1;
}

.aliases-label {
  color: #909399;
  font-size: 12px;
  margin-bottom: 5px;
}

.alias-tags {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: 5px;
}

.alias-tag {
  margin-bottom: 5px;
}

.character-actions {
  display: flex;
  justify-content: center;
  gap: 10px;
  margin-top: 15px;
  flex-wrap: wrap;
}

/* 确保内容在所有设备上都可滚动 */
:deep(.el-card__body) {
  overflow-y: visible;
  height: auto;
}

:deep(.el-card) {
  overflow: visible;
}

/* 针对滚动条的样式 */
::-webkit-scrollbar {
  width: 6px;
  height: 6px;
}

::-webkit-scrollbar-track {
  background: #f1f1f1;
  border-radius: 3px;
}

::-webkit-scrollbar-thumb {
  background: #c0c4cc;
  border-radius: 3px;
}

::-webkit-scrollbar-thumb:hover {
  background: #909399;
}

@media (max-width: 768px) {
  .page-header {
    flex-direction: column;
    align-items: flex-start;
    width: 100%;
  }
  
  .header-actions {
    flex-direction: column;
    width: 100%;
    gap: 15px;
    margin-top: 10px;
  }
  
  .full-width-select {
    width: 100%;
  }
  
  .analyze-button {
    width: 100%;
    margin-left: 0 !important;
  }
  
  .character-actions {
    flex-direction: column;
    width: 100%;
  }
  
  .character-actions .el-button {
    margin-right: 0;
    margin-bottom: 8px;
    width: 100%;
  }
  
  .character-card {
    margin-bottom: 10px;
  }
  
  .character-avatar {
    padding-top: 10px;
  }
  
  :deep(.el-empty__image) {
    width: 120px !important;
    height: 120px !important;
  }
}

/* 触摸设备滚动优化 */
@media (pointer: coarse) {
  .character-list-container {
    -webkit-overflow-scrolling: touch;
  }
}
</style> 