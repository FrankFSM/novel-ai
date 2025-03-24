<template>
  <div class="settings-container">
    <el-card shadow="never" class="settings-card">
      <template #header>
        <div class="settings-header">
          <h2>系统设置</h2>
        </div>
      </template>
      
      <el-form :model="settings" label-width="120px">
        <!-- 外观设置 -->
        <el-divider content-position="left">外观</el-divider>
        
        <el-form-item label="主题颜色">
          <el-color-picker v-model="settings.theme.primaryColor" show-alpha />
        </el-form-item>
        
        <el-form-item label="深色模式">
          <el-switch
            v-model="settings.theme.darkMode"
            active-text="开启"
            inactive-text="关闭"
          />
        </el-form-item>
        
        <!-- API设置 -->
        <el-divider content-position="left">API设置</el-divider>
        
        <el-form-item label="API地址">
          <el-input v-model="settings.api.baseUrl" placeholder="请输入API基础地址" />
        </el-form-item>
        
        <el-form-item label="API超时">
          <el-input-number 
            v-model="settings.api.timeout" 
            :min="1000" 
            :max="60000" 
            :step="1000" 
            controls-position="right"
          />
          <span class="form-item-hint">毫秒</span>
        </el-form-item>
        
        <!-- 智能问答设置 -->
        <el-divider content-position="left">智能问答</el-divider>
        
        <el-form-item label="默认使用RAG">
          <el-switch
            v-model="settings.qa.useRag"
            active-text="开启"
            inactive-text="关闭"
          />
          <div class="form-item-help">
            <el-tooltip 
              content="启用RAG（检索增强生成）可以让AI根据检索到的小说内容回答问题，提高答案准确性" 
              placement="top"
            >
              <el-icon><InfoFilled /></el-icon>
            </el-tooltip>
          </div>
        </el-form-item>
        
        <el-form-item label="最大上下文数量">
          <el-input-number 
            v-model="settings.qa.maxContexts" 
            :min="1" 
            :max="10" 
            :step="1" 
            controls-position="right"
          />
          <div class="form-item-help">
            <el-tooltip 
              content="检索的小说段落数量，数量越多，回答越全面，但速度会变慢" 
              placement="top"
            >
              <el-icon><InfoFilled /></el-icon>
            </el-tooltip>
          </div>
        </el-form-item>
        
        <!-- 分析设置 -->
        <el-divider content-position="left">分析设置</el-divider>
        
        <el-form-item label="关系图深度">
          <el-input-number 
            v-model="settings.analysis.relationshipDepth" 
            :min="1" 
            :max="5" 
            :step="1" 
            controls-position="right"
          />
          <div class="form-item-help">
            <el-tooltip 
              content="关系网络图的展示深度，深度越大，展示的关系越多" 
              placement="top"
            >
              <el-icon><InfoFilled /></el-icon>
            </el-tooltip>
          </div>
        </el-form-item>
        
        <!-- 操作按钮 -->
        <el-divider></el-divider>
        
        <div class="settings-actions">
          <el-button type="primary" @click="saveSettings">保存设置</el-button>
          <el-button @click="resetSettings">恢复默认</el-button>
        </div>
      </el-form>
    </el-card>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import { InfoFilled } from '@element-plus/icons-vue'

// 系统默认设置
const defaultSettings = {
  theme: {
    primaryColor: '#409EFF',
    darkMode: false
  },
  api: {
    baseUrl: '/api/v1',
    timeout: 1000 * 60 * 5
  },
  qa: {
    useRag: true,
    maxContexts: 5
  },
  analysis: {
    relationshipDepth: 2
  }
}

// 从本地存储加载设置
const loadSettings = () => {
  try {
    const savedSettings = localStorage.getItem('novel-ai-settings')
    if (savedSettings) {
      return JSON.parse(savedSettings)
    }
  } catch (error) {
    console.error('加载设置失败', error)
  }
  return { ...defaultSettings }
}

// 设置状态
const settings = ref(loadSettings())

// 保存设置
const saveSettings = () => {
  try {
    localStorage.setItem('novel-ai-settings', JSON.stringify(settings.value))
    ElMessage.success('设置保存成功')
    
    // 应用设置逻辑
    applySettings()
  } catch (error) {
    console.error('保存设置失败', error)
    ElMessage.error('设置保存失败')
  }
}

// 重置设置
const resetSettings = () => {
  settings.value = { ...defaultSettings }
  ElMessage.success('已恢复默认设置')
}

// 应用设置到系统
const applySettings = () => {
  // 应用深色模式
  if (settings.value.theme.darkMode) {
    document.documentElement.classList.add('dark')
  } else {
    document.documentElement.classList.remove('dark')
  }
  
  // 应用主题色
  const style = document.createElement('style')
  style.innerHTML = `
    :root {
      --el-color-primary: ${settings.value.theme.primaryColor};
    }
  `
  document.head.appendChild(style)
}

// 初始应用设置
applySettings()
</script>

<style scoped>
.settings-container {
  max-width: 800px;
  margin: 0 auto;
}

.settings-card {
  margin-bottom: 20px;
}

.settings-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.settings-header h2 {
  margin: 0;
}

.form-item-hint {
  margin-left: 10px;
  color: #909399;
}

.form-item-help {
  display: inline-block;
  margin-left: 10px;
  color: #909399;
  cursor: pointer;
}

.settings-actions {
  display: flex;
  justify-content: center;
  margin-top: 20px;
  gap: 20px;
}
</style> 