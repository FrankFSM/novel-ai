import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { novelApi } from '@/api'

export const useNovelStore = defineStore('novel', () => {
  // 状态
  const novels = ref([])
  const currentNovelId = ref(null)
  const loading = ref(false)
  const error = ref(null)
  
  // 计算属性
  const currentNovel = computed(() => {
    if (!currentNovelId.value) return null
    return novels.value.find(novel => novel.id === currentNovelId.value) || null
  })
  
  // 获取所有小说
  async function fetchNovels() {
    loading.value = true
    error.value = null
    
    try {
      const response = await novelApi.getNovels()
      novels.value = response.data
      
      // 如果有小说且没有选择当前小说，则选择第一本
      if (novels.value.length > 0 && !currentNovelId.value) {
        currentNovelId.value = novels.value[0].id
      }
      
      return response.data
    } catch (err) {
      error.value = err.message || '获取小说列表失败'
      throw err
    } finally {
      loading.value = false
    }
  }
  
  // 获取小说详情
  async function fetchNovelDetail(id) {
    loading.value = true
    error.value = null
    
    try {
      const response = await novelApi.getNovelDetail(id)
      
      // 更新小说列表中的详情
      const index = novels.value.findIndex(novel => novel.id === id)
      if (index !== -1) {
        novels.value[index] = { ...novels.value[index], ...response.data }
      } else {
        novels.value.push(response.data)
      }
      
      return response.data
    } catch (err) {
      error.value = err.message || '获取小说详情失败'
      throw err
    } finally {
      loading.value = false
    }
  }
  
  // 创建新小说
  async function createNovel(novelData) {
    loading.value = true
    error.value = null
    
    try {
      const response = await novelApi.createNovel(novelData)
      novels.value.push(response.data)
      return response.data
    } catch (err) {
      error.value = err.message || '创建小说失败'
      throw err
    } finally {
      loading.value = false
    }
  }
  
  // 上传小说文件
  async function uploadNovelFile(formData) {
    loading.value = true
    error.value = null
    
    try {
      const response = await novelApi.uploadNovelFile(formData)
      return response.data
    } catch (err) {
      error.value = err.message || '上传小说失败'
      throw err
    } finally {
      loading.value = false
    }
  }
  
  // 删除小说
  async function deleteNovel(id) {
    loading.value = true
    error.value = null
    
    try {
      await novelApi.deleteNovel(id)
      
      // 从列表中删除
      novels.value = novels.value.filter(novel => novel.id !== id)
      
      // 如果删除的是当前选中的小说，重置当前小说
      if (currentNovelId.value === id) {
        currentNovelId.value = novels.value.length > 0 ? novels.value[0].id : null
      }
    } catch (err) {
      error.value = err.message || '删除小说失败'
      throw err
    } finally {
      loading.value = false
    }
  }
  
  // 设置当前小说
  function setCurrentNovel(id) {
    currentNovelId.value = id
  }
  
  return { 
    novels, 
    currentNovelId,
    currentNovel,
    loading,
    error,
    fetchNovels,
    fetchNovelDetail,
    createNovel,
    uploadNovelFile,
    deleteNovel,
    setCurrentNovel
  }
}) 