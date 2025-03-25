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
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useNovelStore } from '@/store/novel'
import { ElMessage } from 'element-plus'
import { characterApi } from '@/api'

const router = useRouter()
const route = useRoute()
const novelStore = useNovelStore()

// 本地状态
const selectedNovel = ref(null)
const characters = ref([])
const loading = ref(false)

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
    
    // 调用API获取角色列表
    const data = await characterApi.analyzeCharacters(novelId, forceRefresh)
    console.log('角色分析API响应:', data)
    
    if (data && Array.isArray(data)) {
      // 按重要性排序
      characters.value = [...data].sort((a, b) => 
        (b.importance || 0) - (a.importance || 0)
      )
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
  await loadCharacters(novelId)
  
  // 更新URL参数
  router.replace({
    query: { ...route.query, novelId }
  })
}

// 手动分析角色按钮处理
async function analyzeCharacters() {
  if (!selectedNovel.value) return
  
  try {
    await loadCharacters(selectedNovel.value, true) // 强制刷新
  } catch (error) {
    ElMessage.error('分析角色失败')
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

.loading-text {
  text-align: center;
  margin-top: 10px;
  color: #909399;
}

.character-list {
  margin-top: 20px;
}

.character-col {
  margin-bottom: 20px;
}

.character-card {
  height: 100%;
  transition: transform 0.3s;
}

.character-card:hover {
  transform: translateY(-5px);
}

.character-avatar {
  display: flex;
  justify-content: center;
  margin-bottom: 10px;
}

.character-info {
  text-align: center;
}

.character-name {
  margin: 10px 0;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
}

.character-description {
  color: #606266;
  margin-bottom: 10px;
  height: 60px;
  overflow: hidden;
  text-overflow: ellipsis;
}

.character-aliases {
  margin-bottom: 15px;
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
}
</style> 