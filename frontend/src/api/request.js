import axios from 'axios'
import { ElMessage } from 'element-plus'

// 创建axios实例
const request = axios.create({
  baseURL: '/api/v1',
  timeout: 1000 * 60 * 5,
  headers: {
    'Content-Type': 'application/json'
  }
})

// 请求拦截器
request.interceptors.request.use(
  config => {
    // 可以在这里添加token等逻辑
    return config
  },
  error => {
    return Promise.reject(error)
  }
)

// 响应拦截器
request.interceptors.response.use(
  response => {
    return response
  },
  error => {
    const { response } = error

    // 处理错误响应
    if (response) {
      const { status, data } = response
      
      let message = '请求失败'
      
      if (data && data.detail) {
        message = data.detail
      } else if (status === 404) {
        message = '请求资源不存在'
      } else if (status === 401) {
        message = '未授权访问'
      } else if (status === 403) {
        message = '禁止访问'
      } else if (status === 500) {
        message = '服务器内部错误'
      }
      
      ElMessage.error(message)
    } else {
      // 网络错误等
      ElMessage.error('网络连接失败，请检查网络')
    }
    
    return Promise.reject(error)
  }
)

export default request 