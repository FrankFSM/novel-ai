<template>
  <div class="upload-container">
    <el-card shadow="never">
      <template #header>
        <div class="upload-header">
          <h2>创建小说</h2>
        </div>
      </template>
      
      <el-steps :active="activeStep" finish-status="success" align-center>
        <el-step title="基本信息" />
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
              <el-button type="primary" @click="createNovel" :loading="creating">
                {{ creating ? '创建中...' : '创建小说' }}
              </el-button>
            </el-form-item>
          </el-form>
        </div>
        
        <!-- 步骤2：处理完成 -->
        <div v-else class="result-container">
          <el-result 
            v-if="createSuccess" 
            icon="success" 
            title="创建成功" 
            sub-title="小说基本信息已创建，您可以前往详情页上传内容"
          >
            <template #extra>
              <el-button type="primary" @click="viewNovelDetail">查看小说详情</el-button>
              <el-button @click="createAnother">继续创建</el-button>
            </template>
          </el-result>
          
          <el-result 
            v-else 
            icon="error" 
            title="创建失败" 
            :sub-title="errorMessage || '小说创建过程中发生错误'"
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
import { Plus } from '@element-plus/icons-vue'
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
  activeStep.value++
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

// 创建状态
const creating = ref(false)
const createSuccess = ref(false)
const createdNovelId = ref(null)
const errorMessage = ref('')

// 创建小说
const createNovel = async () => {
  formRef.value.validate(async (valid) => {
    if (!valid) return
    
    creating.value = true
    errorMessage.value = ''
    
    try {
      // 创建小说基本信息
      const novelData = {
        title: novelForm.value.title,
        author: novelForm.value.author,
        description: novelForm.value.description
      }
      
      // 调用API创建
      const response = await novelStore.createNovel(novelData)
      createdNovelId.value = response.id
      
      // 创建成功
      createSuccess.value = true
      
      // 刷新小说列表
      await novelStore.fetchNovels()
      
      // 前进到结果页
      nextStep()
    } catch (error) {
      createSuccess.value = false
      errorMessage.value = error.message || '创建失败，请稍后重试'
      ElMessage.error(errorMessage.value)
    } finally {
      creating.value = false
    }
  })
}

// 结果页操作
const viewNovelDetail = () => {
  if (createdNovelId.value) {
    router.push(`/novels/detail/${createdNovelId.value}`)
  }
}

const createAnother = () => {
  // 重置表单和状态
  formRef.value.resetFields()
  coverUrl.value = ''
  createSuccess.value = false
  createdNovelId.value = null
  activeStep.value = 0
}

const navigateToList = () => {
  router.push('/novels/list')
}
</script>

<style scoped>
.upload-container {
  max-width: 800px;
  margin: 0 auto;
  padding: 20px 0;
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
}

.form-container {
  max-width: 600px;
  margin: 0 auto;
}

.cover-uploader {
  width: 200px;
  height: 280px;
  border: 1px dashed #d9d9d9;
  border-radius: 6px;
  cursor: pointer;
  position: relative;
  overflow: hidden;
  display: flex;
  justify-content: center;
  align-items: center;
}

.cover-uploader:hover {
  border-color: #409EFF;
}

.cover-uploader-icon {
  font-size: 28px;
  color: #8c939d;
  width: 28px;
  height: 28px;
}

.cover-image {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.upload-tip {
  font-size: 12px;
  color: #606266;
  margin-top: 7px;
}

.step-actions {
  display: flex;
  justify-content: space-between;
  margin-top: 20px;
}

.result-container {
  padding: 20px 0;
}
</style> 