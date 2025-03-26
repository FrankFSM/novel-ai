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
    redirect: '/analysis/characters/list',
    meta: { title: '小说分析' },
    children: [
      {
        path: 'characters',
        name: 'CharacterAnalysis',
        redirect: '/analysis/characters/list',
        meta: { title: '角色分析' },
        children: [
          {
            path: 'list',
            name: 'CharacterList',
            component: () => import('@/views/analysis/CharacterList.vue'),
            meta: { title: '角色列表' }
          },
          {
            path: 'journey',
            name: 'CharacterJourney',
            component: () => import('@/views/analysis/CharacterJourney.vue'),
            meta: { title: '角色旅程' }
          }
        ]
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
        redirect: '/analysis/locations/list',
        meta: { title: '地点分析' },
        children: [
          {
            path: 'list',
            name: 'LocationList',
            component: () => import('@/views/analysis/LocationList.vue'),
            meta: { title: '地点列表' }
          },
          {
            path: 'detail/:locationId',
            name: 'LocationDetail',
            component: () => import('@/views/analysis/LocationDetail.vue'),
            meta: { title: '地点详情' },
            props: route => ({ locationId: Number(route.params.locationId), novelId: Number(route.query.novelId) })
          },
          {
            path: 'events/:locationId',
            name: 'LocationEvents',
            component: () => import('@/views/analysis/LocationEvents.vue'),
            meta: { title: '地点事件' },
            props: route => ({ locationId: Number(route.params.locationId), novelId: Number(route.query.novelId) })
          }
        ]
      },
      {
        path: 'events',
        name: 'EventAnalysis',
        redirect: '/analysis/events/list',
        meta: { title: '事件分析' },
        children: [
          {
            path: 'list',
            name: 'EventList',
            component: () => import('@/views/analysis/EventList.vue'),
            meta: { title: '事件列表' }
          },
          {
            path: 'detail/:eventId',
            name: 'EventDetail',
            component: () => import('@/views/analysis/EventDetail.vue'),
            meta: { title: '事件详情' },
            props: route => ({ eventId: Number(route.params.eventId), novelId: Number(route.query.novelId) })
          }
        ]
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