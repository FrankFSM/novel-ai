<template>
  <div class="header-container">
    <div class="left">
      <el-breadcrumb separator="/">
        <el-breadcrumb-item v-for="(item, index) in breadcrumbs" :key="index" :to="item.path">
          {{ item.title }}
        </el-breadcrumb-item>
      </el-breadcrumb>
    </div>
    <div class="right">
      <div class="novel-selector" v-if="currentNovel">
        <span>当前小说：</span>
        <el-dropdown>
          <span class="el-dropdown-link">
            {{ currentNovel.title }}
            <el-icon class="el-icon--right"><arrow-down /></el-icon>
          </span>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item v-for="novel in novels" :key="novel.id" @click="selectNovel(novel)">
                {{ novel.title }}
              </el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </div>
      <el-tooltip content="切换主题">
        <el-button :icon="Sunny" circle @click="toggleTheme" />
      </el-tooltip>
      <el-tooltip content="用户中心">
        <el-avatar :size="32" src="https://cube.elemecdn.com/0/88/03b0d39583f48206768a7534e55bcpng.png" />
      </el-tooltip>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRoute } from 'vue-router'
import { ArrowDown, Sunny } from '@element-plus/icons-vue'
import { useNovelStore } from '@/store/novel'

const route = useRoute()
const novelStore = useNovelStore()

// 模拟数据，实际应从store获取
const novels = ref([
  { id: 1, title: '《诡秘之主》' },
  { id: 2, title: '《雪中悍刀行》' },
  { id: 3, title: '《赘婿》' }
])

const currentNovel = ref(novels.value[0])

const selectNovel = (novel) => {
  currentNovel.value = novel
  // 实际应调用store方法切换当前小说
  // novelStore.setCurrentNovel(novel.id)
}

// 动态生成面包屑
const breadcrumbs = computed(() => {
  const { path, meta } = route
  const pathArray = path.split('/').filter(Boolean)
  
  const result = [{ path: '/', title: '首页' }]
  
  let currentPath = ''
  pathArray.forEach(segment => {
    currentPath += `/${segment}`
    const title = meta.title || segment.charAt(0).toUpperCase() + segment.slice(1)
    result.push({ path: currentPath, title })
  })
  
  return result
})

const toggleTheme = () => {
  // 实现暗黑模式切换逻辑
  document.documentElement.classList.toggle('dark')
}
</script>

<style scoped>
.header-container {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 20px;
  flex-wrap: wrap;
  width: 100%;
  overflow: visible;
  position: relative;
  min-height: 60px;
}

.left {
  display: flex;
  align-items: center;
  min-width: 150px;
  overflow-x: auto;
  white-space: nowrap;
  padding: 10px 0;
  margin-right: 10px;
}

.right {
  display: flex;
  align-items: center;
  gap: 16px;
  flex-wrap: wrap;
  padding: 10px 0;
}

.novel-selector {
  display: flex;
  align-items: center;
  margin-right: 20px;
  flex-wrap: nowrap;
  white-space: nowrap;
}

.novel-selector span {
  margin-right: 8px;
  color: #606266;
}

.el-dropdown-link {
  cursor: pointer;
  color: #409EFF;
  display: flex;
  align-items: center;
  max-width: 150px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

@media (max-width: 768px) {
  .header-container {
    flex-direction: column;
    padding: 10px;
    height: auto;
    min-height: 80px;
  }

  .left, .right {
    width: 100%;
    justify-content: center;
    margin-bottom: 10px;
  }

  .left {
    order: 2;
  }

  .right {
    order: 1;
  }

  .novel-selector {
    margin-right: 0;
    width: 100%;
    justify-content: center;
    margin-bottom: 10px;
  }
}
</style> 