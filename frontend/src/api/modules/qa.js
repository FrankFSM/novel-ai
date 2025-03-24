import request from '../request'

export default {
  // 向小说提问
  askQuestion(data) {
    return request({
      url: '/qa/ask',
      method: 'post',
      data
    })
  },
  
  // 提取文本中的实体
  extractEntities(data) {
    return request({
      url: '/qa/extract-entities',
      method: 'post',
      data
    })
  },
  
  // 分析文本
  analyzeText(data) {
    return request({
      url: '/qa/analyze-text',
      method: 'post',
      data
    })
  }
} 