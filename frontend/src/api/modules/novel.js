import request from '../request'

export default {
  // 获取小说列表
  getNovels(params = {}) {
    return request({
      url: '/novels',
      method: 'get',
      params
    })
  },
  
  // 获取小说详情
  getNovelDetail(id) {
    return request({
      url: `/novels/${id}`,
      method: 'get'
    })
  },
  
  // 创建小说
  createNovel(data) {
    return request({
      url: '/novels',
      method: 'post',
      data
    })
  },
  
  // 更新小说
  updateNovel(id, data) {
    return request({
      url: `/novels/${id}`,
      method: 'put',
      data
    })
  },
  
  // 删除小说
  deleteNovel(id) {
    return request({
      url: `/novels/${id}`,
      method: 'delete'
    })
  },
  
  // 上传小说文件
  uploadNovelFile(formData) {
    return request({
      url: '/novels/upload-file',
      method: 'post',
      data: formData,
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
  },
  
  // 获取小说统计数据
  getNovelStatistics(id) {
    return request({
      url: `/novels/${id}/statistics`,
      method: 'get'
    })
  },
  
  // 提取小说实体
  extractNovelEntities(id) {
    return request({
      url: `/novels/${id}/extract-entities`,
      method: 'post'
    })
  }
} 