<template>
  <div class="home-container">
    <el-row :gutter="20">
      <!-- 欢迎卡片 -->
      <el-col :span="24">
        <el-card shadow="hover" class="welcome-card">
          <template #header>
            <div class="welcome-header">
              <h2>欢迎使用长篇小说智能分析系统</h2>
              <el-button type="primary" @click="navigateToUpload">上传新小说</el-button>
            </div>
          </template>
          <div class="welcome-content">
            <p>本系统提供全面的小说分析功能，帮助您深入理解小说内容与结构。</p>
            <p>通过AI技术，我们为小说提供智能问答、人物关系分析、情节时间线等功能。</p>
          </div>
        </el-card>
      </el-col>
      
      <!-- 统计数据卡片 -->
      <el-col :span="8" v-if="novelStore.novels.length > 0">
        <el-card shadow="hover" class="stat-card">
          <template #header>
            <h3>系统数据</h3>
          </template>
          <div class="stat-content">
            <div class="stat-item">
              <div class="stat-value">{{ novelStore.novels.length }}</div>
              <div class="stat-label">已分析小说</div>
            </div>
          </div>
        </el-card>
      </el-col>
      
      <!-- 小说列表 -->
      <el-col :span="16" v-if="novelStore.novels.length > 0">
        <el-card shadow="hover" class="novels-card">
          <template #header>
            <div class="novels-header">
              <h3>小说列表</h3>
              <el-button text @click="navigateToNovelList">查看全部</el-button>
            </div>
          </template>
          <div class="novels-content">
            <el-empty 
              v-if="novelStore.novels.length === 0" 
              description="暂无小说，请上传" 
            />
            <el-table v-else :data="recentNovels" style="width: 100%">
              <el-table-column label="封面" width="60">
                <template #default="scope">
                  <el-avatar 
                    :size="40" 
                    :src="scope.row.cover_url || 'https://cube.elemecdn.com/3/7c/3ea6beec64369c2642b92c6726f1epng.png'" 
                  />
                </template>
              </el-table-column>
              <el-table-column prop="title" label="标题" />
              <el-table-column prop="author" label="作者" width="120" />
              <el-table-column fixed="right" label="操作" width="120">
                <template #default="scope">
                  <el-button link type="primary" @click="navigateToNovelDetail(scope.row.id)">
                    查看详情
                  </el-button>
                </template>
              </el-table-column>
            </el-table>
          </div>
        </el-card>
      </el-col>
      
      <!-- 快速入口卡片 -->
      <el-col :span="24">
        <el-card shadow="hover" class="entry-card">
          <template #header>
            <h3>快速入口</h3>
          </template>
          <div class="entry-content">
            <el-row :gutter="20">
              <el-col :span="6">
                <div class="entry-item" @click="navigateToQA">
                  <el-icon :size="40"><ChatDotRound /></el-icon>
                  <span>智能问答</span>
                </div>
              </el-col>
              <el-col :span="6">
                <div class="entry-item" @click="navigateToRelationship">
                  <el-icon :size="40"><Connection /></el-icon>
                  <span>关系网络</span>
                </div>
              </el-col>
              <el-col :span="6">
                <div class="entry-item" @click="navigateToTimeline">
                  <el-icon :size="40"><DataLine /></el-icon>
                  <span>情节时间线</span>
                </div>
              </el-col>
              <el-col :span="6">
                <div class="entry-item" @click="navigateToCharacter">
                  <el-icon :size="40"><Avatar /></el-icon>
                  <span>角色分析</span>
                </div>
              </el-col>
            </el-row>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ChatDotRound, Connection, DataLine, Avatar } from '@element-plus/icons-vue'
import { useNovelStore } from '@/store/novel'

const router = useRouter()
const novelStore = useNovelStore()

// 计算属性：获取最近的3本小说
const recentNovels = computed(() => {
  return novelStore.novels.slice(0, 3)
})

// 页面加载时获取小说列表
onMounted(async () => {
  if (novelStore.novels.length === 0) {
    try {
      await novelStore.fetchNovels()
    } catch (error) {
      console.error('获取小说列表失败', error)
    }
  }
})

// 导航函数
function navigateToUpload() {
  router.push('/novels/upload')
}

function navigateToNovelList() {
  router.push('/novels/list')
}

function navigateToNovelDetail(id) {
  router.push(`/novels/detail/${id}`)
}

function navigateToQA() {
  router.push('/qa')
}

function navigateToRelationship() {
  router.push('/analysis/relationships')
}

function navigateToTimeline() {
  router.push('/analysis/timeline')
}

function navigateToCharacter() {
  router.push('/analysis/characters')
}
</script>

<style scoped>
.home-container {
  padding: 20px 0;
}

.welcome-card {
  margin-bottom: 20px;
}

.welcome-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.welcome-header h2 {
  margin: 0;
}

.welcome-content {
  font-size: 16px;
  line-height: 1.6;
  color: #606266;
}

.stat-card, .novels-card {
  height: 240px;
  margin-bottom: 20px;
}

.stat-content {
  display: flex;
  justify-content: space-around;
  align-items: center;
  height: 100%;
}

.stat-item {
  text-align: center;
}

.stat-value {
  font-size: 36px;
  font-weight: bold;
  color: #409EFF;
}

.stat-label {
  margin-top: 8px;
  color: #909399;
}

.novels-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.novels-header h3 {
  margin: 0;
}

.entry-card {
  margin-bottom: 20px;
}

.entry-content {
  padding: 20px 0;
}

.entry-item {
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  height: 120px;
  background-color: #f5f7fa;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.3s;
}

.entry-item:hover {
  background-color: #ecf5ff;
  transform: translateY(-5px);
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
}

.entry-item span {
  margin-top: 10px;
  font-size: 16px;
}
</style> 