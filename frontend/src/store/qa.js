import { defineStore } from 'pinia'
import { ref } from 'vue'
import { qaApi } from '@/api'

export const useQAStore = defineStore('qa', () => {
  // 状态
  const history = ref([])  // 问答历史记录
  const loading = ref(false)
  const error = ref(null)
  
  // 发送问题
  async function askQuestion(question, novelId, useRag = true) {
    loading.value = true
    error.value = null
    
    try {
      // 将问题添加到历史记录
      const questionItem = {
        id: Date.now(),
        type: 'question',
        content: question,
        timestamp: new Date().toISOString()
      }
      history.value.push(questionItem)
      
      // 调用API
      const response = await qaApi.askQuestion({
        novel_id: novelId,
        question,
        use_rag: useRag
      })
      
      // 将回答添加到历史记录
      const answerItem = {
        id: Date.now() + 1,
        type: 'answer',
        content: response.data.answer,
        sources: response.data.sources,
        confidence: response.data.confidence,
        timestamp: new Date().toISOString()
      }
      history.value.push(answerItem)
      
      return response.data
    } catch (err) {
      error.value = err.message || '问答失败'
      
      // 添加错误消息到历史记录
      history.value.push({
        id: Date.now() + 1,
        type: 'error',
        content: error.value,
        timestamp: new Date().toISOString()
      })
      
      throw err
    } finally {
      loading.value = false
    }
  }
  
  // 提取实体
  async function extractEntities(text, novelId = null) {
    loading.value = true
    error.value = null
    
    try {
      const response = await qaApi.extractEntities({
        text,
        novel_id: novelId
      })
      
      return response.data
    } catch (err) {
      error.value = err.message || '实体提取失败'
      throw err
    } finally {
      loading.value = false
    }
  }
  
  // 分析文本
  async function analyzeText(text, novelId = null) {
    loading.value = true
    error.value = null
    
    try {
      const response = await qaApi.analyzeText({
        text,
        novel_id: novelId
      })
      
      return response.data
    } catch (err) {
      error.value = err.message || '文本分析失败'
      throw err
    } finally {
      loading.value = false
    }
  }
  
  // 清空历史记录
  function clearHistory() {
    history.value = []
  }
  
  return {
    history,
    loading,
    error,
    askQuestion,
    extractEntities,
    analyzeText,
    clearHistory
  }
}) 