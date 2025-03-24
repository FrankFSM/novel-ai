<template>
  <div class="novel-list-container">
    <el-card shadow="never">
      <template #header>
        <div class="list-header">
          <h2>小说管理</h2>
          <div class="header-actions">
            <el-input
              v-model="searchQuery"
              placeholder="搜索小说标题或作者"
              prefix-icon="Search"
              clearable
              @clear="handleSearch"
              @input="handleSearch"
              style="width: 300px; margin-right: 16px;"
            />
            <el-button type="primary" @click="navigateToUpload">上传新小说</el-button>
          </div>
        </div>
      </template>
      
      <div class="list-content">
        <!-- 加载中状态 -->
        <div v-if="novelStore.loading" class="loading-container">
          <el-skeleton :rows="10" animated />
        </div>
        
        <!-- 空状态 -->
        <el-empty v-else-if="filteredNovels.length === 0" description="暂无小说，点击上方按钮上传">
          <el-button type="primary" @click="navigateToUpload">上传新小说</el-button>
        </el-empty>
        
        <!-- 小说列表 -->
        <el-table
          v-else
          :data="filteredNovels"
          style="width: 100%"
          row-key="id"
          border
          stripe
          @row-click="handleRowClick"
        >
          <el-table-column label="封面" width="80">
            <template #default="scope">
              <el-avatar 
                shape="square"
                :size="50" 
                :src="scope.row.cover_url || 'https://cube.elemecdn.com/3/7c/3ea6beec64369c2642b92c6726f1epng.png'" 
                fit="cover"
              />
            </template>
          </el-table-column>
          
          <el-table-column prop="title" label="标题" min-width="180" />
          <el-table-column prop="author" label="作者" min-width="120" />
          
          <el-table-column label="创建时间" min-width="180">
            <template #default="scope">
              {{ formatDate(scope.row.created_at) }}
            </template>
          </el-table-column>
          
          <el-table-column label="统计" min-width="120">
            <template #default="scope">
              <span v-if="scope.row.chapters_count !== undefined">
                {{ scope.row.chapters_count }} 章节 / 
                {{ scope.row.characters_count || 0 }} 角色
              </span>
              <el-button v-else link type="primary" @click.stop="loadNovelDetail(scope.row.id)">
                加载统计
              </el-button>
            </template>
          </el-table-column>
          
          <el-table-column fixed="right" label="操作" width="200">
            <template #default="scope">
              <el-button link type="primary" @click.stop="viewNovelDetail(scope.row.id)">
                查看详情
              </el-button>
              <el-button link type="primary" @click.stop="startQA(scope.row.id)">
                开始问答
              </el-button>
              <el-button link type="danger" @click.stop="confirmDelete(scope.row)">
                删除
              </el-button>
            </template>
          </el-table-column>
        </el-table>
      </div>
    </el-card>
    
    <!-- 删除确认对话框 -->
    <el-dialog
      v-model="deleteDialogVisible"
      title="确认删除"
      width="30%"
    >
      <span>确定要删除小说《{{ novelToDelete?.title }}》吗？此操作不可恢复！</span>
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
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useNovelStore } from '@/store/novel'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Search } from '@element-plus/icons-vue'

const router = useRouter()
const novelStore = useNovelStore()

// 本地状态
const searchQuery = ref('')
const deleteDialogVisible = ref(false)
const novelToDelete = ref(null)

// 计算属性：过滤后的小说列表
const filteredNovels = computed(() => {
  if (!searchQuery.value) {
    return novelStore.novels
  }
  
  const query = searchQuery.value.toLowerCase()
  return novelStore.novels.filter(novel => 
    novel.title.toLowerCase().includes(query) || 
    novel.author.toLowerCase().includes(query)
  )
})

// 页面加载时获取小说列表
onMounted(async () => {
  try {
    await novelStore.fetchNovels()
  } catch (error) {
    ElMessage.error('获取小说列表失败')
  }
})

// 搜索处理
const handleSearch = () => {
  // 搜索逻辑，这里通过计算属性自动完成
}

// 导航到上传页面
const navigateToUpload = () => {
  router.push('/novels/upload')
}

// 查看小说详情
const viewNovelDetail = (id) => {
  router.push(`/novels/detail/${id}`)
}

// 开始智能问答
const startQA = (id) => {
  // 设置当前小说
  novelStore.setCurrentNovel(id)
  // 导航到问答页面
  router.push('/qa')
}

// 加载小说详情
const loadNovelDetail = async (id) => {
  try {
    await novelStore.fetchNovelDetail(id)
    ElMessage.success('小说详情加载成功')
  } catch (error) {
    ElMessage.error('获取小说详情失败')
  }
}

// 确认删除小说
const confirmDelete = (novel) => {
  novelToDelete.value = novel
  deleteDialogVisible.value = true
}

// 删除小说
const deleteNovel = async () => {
  if (!novelToDelete.value) return
  
  try {
    await novelStore.deleteNovel(novelToDelete.value.id)
    deleteDialogVisible.value = false
    ElMessage.success(`小说《${novelToDelete.value.title}》删除成功`)
    novelToDelete.value = null
  } catch (error) {
    ElMessage.error('删除小说失败')
  }
}

// 行点击处理
const handleRowClick = (row) => {
  viewNovelDetail(row.id)
}

// 格式化日期
const formatDate = (dateString) => {
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
</script>

<style scoped>
.novel-list-container {
  height: 100%;
}

.list-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.list-header h2 {
  margin: 0;
}

.header-actions {
  display: flex;
  align-items: center;
}

.list-content {
  min-height: 400px;
}

.loading-container {
  padding: 20px 0;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}
</style> 