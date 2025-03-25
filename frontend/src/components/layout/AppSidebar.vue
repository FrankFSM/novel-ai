<template>
  <div class="sidebar-container">
    <div class="logo-container">
      <el-icon class="logo-icon"><Reading /></el-icon>
      <h1 class="title">长篇小说智能分析</h1>
    </div>
    <el-menu
      :default-active="activeMenu"
      class="el-menu-vertical"
      background-color="#304156"
      text-color="#bfcbd9"
      active-text-color="#409EFF"
      :router="true"
      :collapse="isCollapse"
    >
      <el-menu-item index="/">
        <el-icon><HomeFilled /></el-icon>
        <template #title>首页</template>
      </el-menu-item>
      
      <el-sub-menu index="/novels">
        <template #title>
          <el-icon><Reading /></el-icon>
          <span>小说管理</span>
        </template>
        <el-menu-item index="/novels/list">小说列表</el-menu-item>
        <el-menu-item index="/novels/upload">上传小说</el-menu-item>
      </el-sub-menu>
      
      <el-sub-menu index="/analysis">
        <template #title>
          <el-icon><DataAnalysis /></el-icon>
          <span>小说分析</span>
        </template>
        <el-sub-menu index="/analysis/characters">
          <template #title>
            <el-icon><Avatar /></el-icon>
            <span>角色分析</span>
          </template>
          <el-menu-item index="/analysis/characters/list">角色列表</el-menu-item>
          <el-menu-item index="/analysis/characters/journey">角色旅程</el-menu-item>
        </el-sub-menu>
        <el-menu-item index="/analysis/relationships">关系网络</el-menu-item>
        <el-menu-item index="/analysis/timeline">时间线</el-menu-item>
        <el-menu-item index="/analysis/locations">地理空间</el-menu-item>
      </el-sub-menu>
      
      <el-menu-item index="/qa">
        <el-icon><ChatDotRound /></el-icon>
        <template #title>智能问答</template>
      </el-menu-item>
      
      <el-menu-item index="/settings">
        <el-icon><Setting /></el-icon>
        <template #title>系统设置</template>
      </el-menu-item>
    </el-menu>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRoute } from 'vue-router'
import { 
  HomeFilled, 
  Reading, 
  DataAnalysis, 
  ChatDotRound, 
  Setting,
  Avatar
} from '@element-plus/icons-vue'

const route = useRoute()
const isCollapse = ref(false)

const activeMenu = computed(() => {
  const { path } = route
  return path
})
</script>

<style scoped>
.sidebar-container {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.logo-container {
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 10px 0;
  margin-bottom: 20px;
}

.logo-icon {
  font-size: 24px;
  color: #fff;
  margin-right: 10px;
}

.title {
  color: #fff;
  font-size: 16px;
  margin: 0;
  font-weight: 600;
}

.el-menu-vertical {
  border-right: none;
  height: calc(100% - 80px);
}
</style> 