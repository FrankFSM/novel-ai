<template>
  <el-config-provider :locale="zhCn">
    <div class="app-container">
      <el-container class="main-container">
        <el-aside width="auto" class="main-sidebar">
          <app-sidebar />
        </el-aside>
        <el-container class="content-container">
          <el-header height="auto" class="main-header">
            <app-header />
          </el-header>
          <el-main class="main-content">
            <router-view v-slot="{ Component }">
              <transition name="fade" mode="out-in">
                <keep-alive>
                  <component :is="Component" />
                </keep-alive>
              </transition>
            </router-view>
          </el-main>
          <el-footer height="auto" class="main-footer" v-if="showFooter">
            <app-footer />
          </el-footer>
        </el-container>
      </el-container>
    </div>
  </el-config-provider>
</template>

<script setup>
import { ElConfigProvider } from 'element-plus'
import zhCn from 'element-plus/dist/locale/zh-cn.mjs'
import AppSidebar from '@/components/layout/AppSidebar.vue'
import AppHeader from '@/components/layout/AppHeader.vue'
import AppFooter from '@/components/layout/AppFooter.vue'
import { ref, onMounted, onBeforeUnmount } from 'vue'

const showFooter = ref(true)

const setAppHeight = () => {
  document.documentElement.style.setProperty('--app-height', `${window.innerHeight}px`)
}

onMounted(() => {
  window.addEventListener('resize', setAppHeight)
  setAppHeight()
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', setAppHeight)
})
</script>

<style>
html, body {
  margin: 0;
  padding: 0;
  height: 100%;
  width: 100%;
  overflow: hidden;
}

.app-container {
  height: 100vh;
  height: var(--app-height, 100vh);
  width: 100vw;
  position: fixed;
  top: 0;
  left: 0;
  overflow: hidden;
}

.main-container {
  height: 100%;
  width: 100%;
}

.main-sidebar {
  background-color: #304156;
  color: #fff;
  overflow-y: auto;
  overflow-x: hidden;
  z-index: 1000;
  transition: width 0.3s;
}

.content-container {
  flex: 1;
  display: flex;
  flex-direction: column;
  height: 100%;
  overflow: hidden;
}

.main-header {
  padding: 0;
  background-color: #fff;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.08);
  z-index: 999;
}

.main-content {
  flex: 1;
  overflow-y: auto;
  overflow-x: hidden;
  padding: 20px;
  -webkit-overflow-scrolling: touch;
}

.main-footer {
  padding: 0;
  background-color: #f5f7fa;
  z-index: 998;
}

/* 强制所有卡片支持滚动 */
.el-card__body {
  overflow-y: auto;
}

/* 覆盖Element Plus的默认高度设置 */
.el-header, .el-footer, .el-main {
  height: auto !important;
}

/* 针对移动设备的优化 */
@media (max-width: 768px) {
  .main-content {
    padding: 10px;
    -webkit-overflow-scrolling: touch;
  }
  
  .el-aside {
    position: fixed;
    height: 100%;
    z-index: 2000;
    transform: translateX(-100%);
    transition: transform 0.3s;
  }
  
  .el-aside.is-opened {
    transform: translateX(0);
  }
}
</style> 