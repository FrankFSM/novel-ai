<template>
  <div class="home-container">
    <div class="welcome-section">
      <h1>欢迎使用小说人物分析系统</h1>
      <p>这是一个帮助作家和读者分析小说中人物角色的工具</p>
    </div>
    
    <div class="features-section">
      <el-row :gutter="20">
        <el-col :xs="24" :sm="12" :md="8" :lg="8" :xl="8" v-for="(feature, index) in features" :key="index">
          <el-card class="feature-card">
            <div class="feature-icon">
              <i :class="feature.icon"></i>
            </div>
            <h3>{{ feature.title }}</h3>
            <p>{{ feature.description }}</p>
          </el-card>
        </el-col>
      </el-row>
    </div>
    
    <div class="getting-started-section">
      <h2>如何开始</h2>
      <el-steps :active="1" align-center>
        <el-step v-for="(step, index) in steps" :key="index" :title="step.title" :description="step.description" />
      </el-steps>
      <div class="action-buttons">
        <el-button type="primary" @click="navigateTo('/upload')">上传小说文件</el-button>
        <el-button @click="navigateTo('/analysis/characters')">查看角色分析</el-button>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'Home',
  data() {
    return {
      features: [
        {
          title: '角色特征分析',
          description: '深入分析小说中每个角色的性格特征、行为模式和发展变化',
          icon: 'el-icon-user'
        },
        {
          title: '角色关系图谱',
          description: '可视化展示小说中角色之间的关系网络和互动',
          icon: 'el-icon-connection'
        },
        {
          title: '角色成长轨迹',
          description: '追踪角色在小说不同阶段的成长和变化，展示人物弧光',
          icon: 'el-icon-data-line'
        }
      ],
      steps: [
        {
          title: '上传小说',
          description: '上传您的小说文件（支持txt、doc、docx等格式）'
        },
        {
          title: '等待分析',
          description: '系统自动分析小说中的角色信息'
        },
        {
          title: '查看结果',
          description: '浏览角色分析报告、关系图谱和成长轨迹'
        }
      ]
    };
  },
  methods: {
    navigateTo(path) {
      this.$router.push(path);
    }
  }
};
</script>

<style scoped>
.home-container {
  padding: 20px;
  width: 100%;
  height: 100%;
  overflow-y: auto;
}

.welcome-section {
  text-align: center;
  margin-bottom: 40px;
  padding: 40px 20px;
  background: linear-gradient(135deg, #409eff 0%, #53a8ff 100%);
  color: white;
  border-radius: 8px;
}

.welcome-section h1 {
  font-size: 2.5rem;
  margin-bottom: 10px;
}

.features-section {
  margin-bottom: 40px;
}

.feature-card {
  height: 100%;
  text-align: center;
  transition: transform 0.3s;
  margin-bottom: 20px;
}

.feature-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 10px 20px rgba(0,0,0,0.1);
}

.feature-icon {
  font-size: 3rem;
  color: #409eff;
  margin-bottom: 20px;
}

.getting-started-section {
  text-align: center;
  padding: 20px;
  background-color: #f5f7fa;
  border-radius: 8px;
}

.action-buttons {
  margin-top: 30px;
  display: flex;
  justify-content: center;
  gap: 20px;
}

h2 {
  margin-bottom: 30px;
}

@media (max-width: 768px) {
  .welcome-section {
    padding: 20px 10px;
  }
  
  .welcome-section h1 {
    font-size: 1.8rem;
  }
  
  .feature-card {
    margin-bottom: 15px;
  }
  
  .action-buttons {
    flex-direction: column;
    gap: 10px;
  }
  
  .action-buttons .el-button {
    width: 100%;
    margin-left: 0 !important;
  }
}
</style> 