<template>
  <el-config-provider :locale="zhCn">
    <div class="app-container">
      <el-container>
        <el-aside width="220px">
          <app-sidebar />
        </el-aside>
        <el-container>
          <el-header>
            <app-header />
          </el-header>
          <el-main>
            <router-view />
          </el-main>
          <el-footer height="40px">
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
</script>

<style scoped>
.app-container {
  height: 100vh;
  width: 100vw;
  overflow: hidden;
}

.el-header {
  background-color: #fff;
  border-bottom: 1px solid #eee;
  padding: 0;
  line-height: 60px;
}

.el-aside {
  background-color: #304156;
  color: #fff;
}

.el-main {
  background-color: #f5f7f9;
  padding: 20px;
  overflow-y: auto;
  width: 100%;
}

.el-footer {
  background-color: #fff;
  color: #666;
  text-align: center;
  line-height: 40px;
  font-size: 12px;
  border-top: 1px solid #eee;
}
</style> 