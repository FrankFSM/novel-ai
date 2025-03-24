import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/',
    name: 'Home',
    component: () => import('@/views/Home.vue'),
    meta: { title: '首页' }
  },
  {
    path: '/novels',
    name: 'Novels',
    redirect: '/novels/list',
    meta: { title: '小说管理' },
    children: [
      {
        path: 'list',
        name: 'NovelList',
        component: () => import('@/views/novels/NovelList.vue'),
        meta: { title: '小说列表' }
      },
      {
        path: 'upload',
        name: 'NovelUpload',
        component: () => import('@/views/novels/NovelUpload.vue'),
        meta: { title: '上传小说' }
      },
      {
        path: 'detail/:id',
        name: 'NovelDetail',
        component: () => import('@/views/novels/NovelDetail.vue'),
        meta: { title: '小说详情' }
      }
    ]
  },
  {
    path: '/analysis',
    name: 'Analysis',
    redirect: '/analysis/characters',
    meta: { title: '小说分析' },
    children: [
      {
        path: 'characters',
        name: 'CharacterAnalysis',
        component: () => import('@/views/analysis/CharacterJourney.vue'),
        meta: { title: '角色分析' }
      },
      {
        path: 'relationships',
        name: 'RelationshipAnalysis',
        component: () => import('@/views/analysis/RelationshipAnalysis.vue'),
        meta: { title: '关系网络' }
      },
      {
        path: 'timeline',
        name: 'Timeline',
        component: () => import('@/views/analysis/Timeline.vue'),
        meta: { title: '时间线' }
      },
      {
        path: 'locations',
        name: 'LocationAnalysis',
        component: () => import('@/views/analysis/LocationEvents.vue'),
        meta: { title: '地理空间' }
      }
    ]
  },
  {
    path: '/qa',
    name: 'QA',
    component: () => import('@/views/QA.vue'),
    meta: { title: '智能问答' }
  },
  {
    path: '/settings',
    name: 'Settings',
    component: () => import('@/views/Settings.vue'),
    meta: { title: '系统设置' }
  },
  {
    path: '/:pathMatch(.*)*',
    name: 'NotFound',
    component: () => import('@/views/NotFound.vue')
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// 全局前置守卫
router.beforeEach((to, from, next) => {
  // 设置页面标题
  document.title = to.meta.title 
    ? `${to.meta.title} - 长篇小说智能分析系统` 
    : '长篇小说智能分析系统'
    
  next()
})

export default router 