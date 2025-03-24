<template>
  <div class="qa-container">
    <el-card class="qa-card">
      <template #header>
        <div class="qa-header">
          <h2>小说智能问答</h2>
          <div class="qa-actions">
            <el-tooltip content="清空对话">
              <el-button type="danger" :icon="Delete" circle @click="handleClearHistory" />
            </el-tooltip>
            <el-switch
              v-model="useRag"
              active-text="基于小说内容"
              inactive-text="通用回答"
              inline-prompt
            />
          </div>
        </div>
      </template>
      
      <!-- 对话历史 -->
      <div class="qa-history" ref="historyRef">
        <div v-if="history.length === 0" class="empty-history">
          <el-empty description="暂无对话，在下方输入您的问题" />
        </div>
        
        <div v-else class="message-list">
          <div
            v-for="item in history"
            :key="item.id"
            :class="['message-item', `message-${item.type}`]"
          >
            <div class="message-avatar">
              <el-avatar :size="40" :src="item.type === 'question' ? userAvatar : aiAvatar" />
            </div>
            <div class="message-content">
              <div class="message-text" v-html="formatMessage(item.content)"></div>
              
              <!-- 如果是回答且有引用来源 -->
              <div v-if="item.type === 'answer' && item.sources && item.sources.length > 0" class="message-sources">
                <div class="sources-header">
                  <span>引用来源：</span>
                  <el-rate
                    v-model="item.confidence"
                    disabled
                    show-score
                    text-color="#ff9900"
                    score-template="{value}"
                  />
                </div>
                <el-collapse>
                  <el-collapse-item v-for="(source, index) in item.sources" :key="index" :title="`${source.chapter_title}`">
                    <div class="source-content">{{ source.content }}</div>
                  </el-collapse-item>
                </el-collapse>
              </div>
              
              <!-- 如果是错误消息 -->
              <div v-if="item.type === 'error'" class="message-error">
                <el-alert type="error" :title="item.content" :closable="false" />
              </div>
            </div>
          </div>
        </div>
      </div>
      
      <!-- 输入区域 -->
      <div class="qa-input">
        <el-input
          v-model="question"
          type="textarea"
          :rows="3"
          placeholder="请输入您对小说的问题..."
          resize="none"
          :disabled="loading"
          @keyup.ctrl.enter="handleAskQuestion"
        />
        <el-button
          type="primary"
          :icon="QuestionFilled"
          :loading="loading"
          @click="handleAskQuestion"
        >提问</el-button>
      </div>
      
      <div class="qa-tip">
        提示：您可以询问关于情节、人物关系、物品传承等各种问题。按Ctrl+Enter快速发送。
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, computed, nextTick, onMounted, watch } from 'vue'
import { useQAStore } from '@/store/qa'
import { useNovelStore } from '@/store/novel'
import { Delete, QuestionFilled } from '@element-plus/icons-vue'
import { ElMessageBox } from 'element-plus'
import markdownit from 'markdown-it'

const md = markdownit()

// 引入状态
const qaStore = useQAStore()
const novelStore = useNovelStore()

// 本地状态
const question = ref('')
const useRag = ref(true)
const historyRef = ref(null)
const userAvatar = 'https://cube.elemecdn.com/0/88/03b0d39583f48206768a7534e55bcpng.png'
const aiAvatar = 'https://cube.elemecdn.com/3/7c/3ea6beec64369c2642b92c6726f1epng.png'

// 计算属性
const history = computed(() => qaStore.history)
const loading = computed(() => qaStore.loading)
const currentNovel = computed(() => novelStore.currentNovel)

// 获取小说列表
onMounted(async () => {
  if (novelStore.novels.length === 0) {
    try {
      await novelStore.fetchNovels()
    } catch (error) {
      console.error('获取小说列表失败', error)
    }
  }
})

// 监听历史记录变化，自动滚动到底部
watch(history, () => {
  nextTick(() => {
    if (historyRef.value) {
      historyRef.value.scrollTop = historyRef.value.scrollHeight
    }
  })
}, { deep: true })

// 处理提问
async function handleAskQuestion() {
  if (!question.value.trim()) {
    return
  }
  
  if (!currentNovel.value) {
    ElMessageBox.alert('请先选择一本小说', '提示', {
      confirmButtonText: '确定',
      type: 'warning'
    })
    return
  }
  
  try {
    await qaStore.askQuestion(question.value, currentNovel.value.id, useRag.value)
    question.value = ''
  } catch (error) {
    console.error('提问失败', error)
  }
}

// 清空历史记录
function handleClearHistory() {
  ElMessageBox.confirm('确定要清空所有对话历史吗？', '提示', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning'
  }).then(() => {
    qaStore.clearHistory()
  }).catch(() => {})
}

// 格式化消息内容（支持markdown）
function formatMessage(content) {
  return md.render(content)
}
</script>

<style scoped>
.qa-container {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.qa-card {
  flex: 1;
  display: flex;
  flex-direction: column;
  height: 100%;
}

.qa-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.qa-header h2 {
  margin: 0;
}

.qa-actions {
  display: flex;
  gap: 16px;
  align-items: center;
}

.qa-history {
  flex: 1;
  overflow-y: auto;
  padding: 10px 0;
  margin-bottom: 20px;
  max-height: calc(100vh - 280px);
}

.empty-history {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 200px;
}

.message-list {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.message-item {
  display: flex;
  margin-bottom: 10px;
}

.message-question {
  align-self: flex-end;
}

.message-answer {
  align-self: flex-start;
}

.message-error {
  align-self: flex-start;
  width: 100%;
}

.message-avatar {
  margin-right: 10px;
}

.message-content {
  max-width: 80%;
  padding: 10px 16px;
  border-radius: 6px;
  position: relative;
}

.message-question .message-content {
  background-color: #ecf5ff;
  color: #303133;
}

.message-answer .message-content {
  background-color: #f5f7fa;
  color: #303133;
}

.message-error .message-content {
  background-color: #fef0f0;
  color: #f56c6c;
}

.message-text {
  line-height: 1.6;
  white-space: pre-wrap;
  word-break: break-word;
}

.message-sources {
  margin-top: 10px;
  font-size: 13px;
  border-top: 1px solid #ebeef5;
  padding-top: 10px;
}

.sources-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.source-content {
  font-size: 12px;
  background-color: #f5f7fa;
  padding: 8px;
  border-radius: 4px;
  color: #606266;
}

.qa-input {
  display: flex;
  gap: 10px;
  margin-top: auto;
}

.qa-tip {
  margin-top: 8px;
  font-size: 12px;
  color: #909399;
  text-align: center;
}

:deep(.el-textarea__inner) {
  resize: none;
}

:deep(.el-card__body) {
  display: flex;
  flex-direction: column;
  height: calc(100% - 60px);
  padding-bottom: 20px;
}
</style> 