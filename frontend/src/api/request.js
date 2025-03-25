import axios from 'axios'
import { ElMessage } from 'element-plus'

// 是否启用详细日志
const ENABLE_DETAILED_LOGGING = true

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
    // 详细日志记录请求
    if (ENABLE_DETAILED_LOGGING) {
      const isCharacterApi = config.url && config.url.includes('character');
      const logLevel = isCharacterApi ? console.info : console.debug;
      
      logLevel(`[API请求] ${config.method.toUpperCase()} ${config.url}`);
      
      if (config.params && Object.keys(config.params).length > 0) {
        logLevel('[API请求参数]', config.params);
      }
      
      if (config.data) {
        logLevel('[API请求数据]', config.data);
      }
    }
    
    return config
  },
  error => {
    console.error('[API请求错误]', error);
    return Promise.reject(error)
  }
)

// 响应拦截器
request.interceptors.response.use(
  response => {
    // 详细日志记录响应
    if (ENABLE_DETAILED_LOGGING) {
      const isCharacterApi = response.config.url && response.config.url.includes('character');
      const logLevel = isCharacterApi ? console.info : console.debug;
      
      logLevel(`[API响应] ${response.config.method.toUpperCase()} ${response.config.url}`);
      logLevel(`[API响应状态] ${response.status}`);
      
      if (response.data) {
        if (isCharacterApi) {
          if (Array.isArray(response.data)) {
            logLevel(`[角色API] 收到${response.data.length}个角色数据`);
          } else {
            logLevel('[角色API] 收到数据:', response.data);
          }
        } else {
          logLevel('[API响应数据]', response.data);
        }
      }
    }
    
    return response
  },
  error => {
    const { response } = error
    console.error('[API响应错误]', error);

    // 处理错误响应
    if (response) {
      const { status, data, config } = response
      
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
      
      console.error(`[API错误] ${config?.method?.toUpperCase() || 'UNKNOWN'} ${config?.url || 'UNKNOWN'} - ${status} ${message}`);
      ElMessage.error(message)
    } else {
      // 网络错误等
      console.error('[API网络错误] 网络连接失败');
      ElMessage.error('网络连接失败，请检查网络')
    }
    
    return Promise.reject(error)
  }
)

export default request 