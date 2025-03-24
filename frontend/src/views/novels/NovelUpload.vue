<template>
  <div class="upload-container">
    <el-card shadow="never">
      <template #header>
        <div class="upload-header">
          <h2>上传小说</h2>
        </div>
      </template>
      
      <el-steps :active="activeStep" finish-status="success" align-center>
        <el-step title="基本信息" />
        <el-step title="上传文件" />
        <el-step title="处理完成" />
      </el-steps>
      
      <div class="step-content">
        <!-- 步骤1：基本信息 -->
        <div v-if="activeStep === 0" class="form-container">
          <el-form 
            ref="formRef" 
            :model="novelForm" 
            :rules="formRules" 
            label-width="100px"
            status-icon
          >
            <el-form-item label="小说标题" prop="title">
              <el-input v-model="novelForm.title" placeholder="请输入小说标题" />
            </el-form-item>
            
            <el-form-item label="作者" prop="author">
              <el-input v-model="novelForm.author" placeholder="请输入作者姓名" />
            </el-form-item>
            
            <el-form-item label="简介" prop="description">
              <el-input 
                v-model="novelForm.description" 
                type="textarea" 
                :rows="5" 
                placeholder="请输入小说简介" 
              />
            </el-form-item>
            
            <el-form-item label="封面" prop="cover">
              <el-upload
                class="cover-uploader"
                action="#"
                :show-file-list="false"
                :auto-upload="false"
                :on-change="handleCoverChange"
              >
                <img v-if="coverUrl" :src="coverUrl" class="cover-image" />
                <el-icon v-else class="cover-uploader-icon"><Plus /></el-icon>
              </el-upload>
              <div class="upload-tip">
                支持JPG、PNG格式，建议尺寸：300x400
              </div>
            </el-form-item>
            
            <el-form-item>
              <el-button type="primary" @click="nextStep">下一步</el-button>
            </el-form-item>
          </el-form>
        </div>
        
        <!-- 步骤2：上传文件 -->
        <div v-else-if="activeStep === 1" class="upload-file-container">
          <el-upload
            class="file-uploader"
            drag
            action="#"
            :auto-upload="false"
            :on-change="handleFileChange"
            :limit="1"
          >
            <el-icon class="el-icon--upload"><upload-filled /></el-icon>
            <div class="el-upload__text">
              拖拽文件到此处，或 <em>点击选择文件</em>
            </div>
            <template #tip>
              <div class="el-upload__tip">
                支持TXT文件格式，建议使用UTF-8编码。文件大小不超过10MB。
              </div>
            </template>
          </el-upload>
          
          <div v-if="selectedFile" class="file-info">
            <p><strong>文件名：</strong>{{ selectedFile.name }}</p>
            <p><strong>大小：</strong>{{ formatFileSize(selectedFile.size) }}</p>
          </div>
          
          <div class="step-actions">
            <el-button @click="prevStep">上一步</el-button>
            <el-button type="primary" :loading="uploading" @click="uploadNovel">
              {{ uploading ? '上传中...' : '开始上传' }}
            </el-button>
          </div>
        </div>
        
        <!-- 步骤3：处理完成 -->
        <div v-else class="result-container">
          <el-result 
            v-if="uploadSuccess" 
            icon="success" 
            title="上传成功" 
            sub-title="小说文件已上传，系统正在后台处理中..."
          >
            <template #extra>
              <el-button type="primary" @click="viewNovelDetail">查看小说详情</el-button>
              <el-button @click="uploadAnother">再次上传</el-button>
            </template>
          </el-result>
          
          <el-result 
            v-else 
            icon="error" 
            title="上传失败" 
            :sub-title="errorMessage || '小说上传过程中发生错误'"
          >
            <template #extra>
              <el-button @click="prevStep">返回重试</el-button>
              <el-button type="primary" @click="navigateToList">返回列表</el-button>
            </template>
          </el-result>
        </div>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Plus, UploadFilled } from '@element-plus/icons-vue'
import { useNovelStore } from '@/store/novel'

const router = useRouter()
const novelStore = useNovelStore()

// 表单与验证规则
const formRef = ref(null)
const novelForm = ref({
  title: '',
  author: '',
  description: ''
})
const formRules = {
  title: [
    { required: true, message: '请输入小说标题', trigger: 'blur' },
    { min: 1, max: 100, message: '长度在 1 到 100 个字符', trigger: 'blur' }
  ],
  author: [
    { required: true, message: '请输入作者姓名', trigger: 'blur' },
    { min: 1, max: 50, message: '长度在 1 到 50 个字符', trigger: 'blur' }
  ],
  description: [
    { max: 500, message: '长度不超过 500 个字符', trigger: 'blur' }
  ]
}

// 步骤控制
const activeStep = ref(0)
const nextStep = () => {
  formRef.value.validate((valid) => {
    if (valid) {
      activeStep.value++
    }
  })
}
const prevStep = () => {
  activeStep.value--
}

// 封面处理
const coverUrl = ref('')
const handleCoverChange = (file) => {
  // 读取并显示封面预览
  const reader = new FileReader()
  reader.onload = (e) => {
    coverUrl.value = e.target.result
  }
  reader.readAsDataURL(file.raw)
}

// 文件处理
const selectedFile = ref(null)
const handleFileChange = (file) => {
  selectedFile.value = file.raw
}

// 上传状态
const uploading = ref(false)
const uploadSuccess = ref(false)
const createdNovelId = ref(null)
const errorMessage = ref('')

// 上传小说
const uploadNovel = async () => {
  if (!selectedFile.value) {
    ElMessage.warning('请选择要上传的小说文件')
    return
  }
  
  uploading.value = true
  errorMessage.value = ''
  
  try {
    // 准备表单数据
    const formData = new FormData()
    formData.append('title', novelForm.value.title)
    formData.append('author', novelForm.value.author)
    
    if (novelForm.value.description) {
      formData.append('description', novelForm.value.description)
    }
    
    formData.append('file', selectedFile.value)
    
    // 调用API上传
    const response = await novelStore.uploadNovelFile(formData)
    
    // 上传成功
    uploadSuccess.value = true
    createdNovelId.value = response.novel_id
    
    // 刷新小说列表
    await novelStore.fetchNovels()
    
    // 前进到结果页
    activeStep.value++
  } catch (error) {
    uploadSuccess.value = false
    errorMessage.value = error.message || '上传失败，请稍后重试'
    ElMessage.error(errorMessage.value)
  } finally {
    uploading.value = false
  }
}

// 结果页操作
const viewNovelDetail = () => {
  if (createdNovelId.value) {
    router.push(`/novels/detail/${createdNovelId.value}`)
  }
}

const uploadAnother = () => {
  // 重置表单和状态
  formRef.value.resetFields()
  coverUrl.value = ''
  selectedFile.value = null
  uploadSuccess.value = false
  createdNovelId.value = null
  errorMessage.value = ''
  activeStep.value = 0
}

const navigateToList = () => {
  router.push('/novels/list')
}

// 工具函数
const formatFileSize = (size) => {
  if (size < 1024) {
    return size + ' B'
  } else if (size < 1024 * 1024) {
    return (size / 1024).toFixed(2) + ' KB'
  } else {
    return (size / (1024 * 1024)).toFixed(2) + ' MB'
  }
}
</script>

<style scoped>
.upload-container {
  max-width: 800px;
  margin: 0 auto;
}

.upload-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.upload-header h2 {
  margin: 0;
}

.step-content {
  margin-top: 30px;
  min-height: 300px;
}

.form-container {
  max-width: 600px;
  margin: 0 auto;
}

.cover-uploader {
  width: 200px;
  height: 270px;
  border: 1px dashed #d9d9d9;
  border-radius: 6px;
  cursor: pointer;
  position: relative;
  overflow: hidden;
  display: flex;
  justify-content: center;
  align-items: center;
  background-color: #fbfdff;
}

.cover-uploader:hover {
  border-color: #409EFF;
}

.cover-uploader-icon {
  font-size: 28px;
  color: #8c939d;
  width: 32px;
  height: 32px;
}

.cover-image {
  max-width: 100%;
  max-height: 100%;
  object-fit: contain;
}

.upload-tip {
  font-size: 12px;
  color: #606266;
  margin-top: 5px;
}

.upload-file-container {
  max-width: 600px;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  align-items: center;
}

.file-uploader {
  width: 100%;
}

.file-info {
  margin-top: 20px;
  padding: 10px;
  width: 100%;
  border: 1px solid #ebeef5;
  border-radius: 4px;
  background-color: #f5f7fa;
}

.step-actions {
  margin-top: 30px;
  display: flex;
  justify-content: center;
  gap: 20px;
}

.result-container {
  margin-top: 20px;
}
</style> 