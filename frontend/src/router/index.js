import { createRouter, createWebHistory } from 'vue-router'

// 懒加载路由组件
const Home = () => import('../views/Home.vue')
const Config = () => import('../views/Config.vue')
const Market = () => import('../views/Market.vue')
const Plans = () => import('../views/Plans.vue')
const PlanDetail = () => import('../views/PlanDetail.vue')
const ApiTest = () => import('../views/ApiTest.vue')
const HistoricalTest = () => import('../views/HistoricalTest.vue')

const routes = [
  {
    path: '/',
    name: 'Home',
    component: Home,
    meta: { title: '首页' }
  },
  {
    path: '/config',
    name: 'Config',
    component: Config,
    meta: { title: '投资配置' }
  },
  {
    path: '/market',
    name: 'Market',
    component: Market,
    meta: { title: '市场数据' }
  },
  {
    path: '/plans',
    name: 'Plans',
    component: Plans,
    meta: { title: '投资计划' }
  },
  {
    path: '/plans/:id',
    name: 'PlanDetail',
    component: PlanDetail,
    meta: { title: '计划详情' }
  },
  {
    path: '/api-test',
    name: 'ApiTest',
    component: ApiTest,
    meta: { title: 'API接口测试' }
  },
  {
    path: '/historical-test',
    name: 'HistoricalTest',
    component: HistoricalTest,
    meta: { title: '历史数据测试' }
  }
]

const router = createRouter({
  history: createWebHistory(process.env.BASE_URL),
  routes
})

// 全局前置守卫 - 设置页面标题
router.beforeEach((to, from, next) => {
  document.title = to.meta.title ? `${to.meta.title} - 自动定投策略提醒系统` : '自动定投策略提醒系统'
  next()
})

export default router 