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
  
  // 获取小说章节列表
  getNovelChapters(novelId) {
    return request({
      url: `/chapters`,
      method: 'get',
      params: { novel_id: novelId }
    })
  },
  
  // 获取小说角色列表
  getNovelCharacters(novelId) {
    return request({
      url: `/characters`,
      method: 'get',
      params: { novel_id: novelId }
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
  
  // 上传小说内容
  uploadNovelContent(novelId, formData) {
    return request({
      url: `/novels/${novelId}/upload-content`,
      method: 'post',
      data: formData,
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
  },
  
  // 上传单个章节文件
  uploadChapterFile(novelId, formData) {
    return request({
      url: `/novels/${novelId}/upload-chapter`,
      method: 'post',
      data: formData,
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
  },
  
  // 创建章节
  createChapter(novelId, data) {
    return request({
      url: `/novels/${novelId}/chapters`,
      method: 'post',
      data
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