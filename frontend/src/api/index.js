import axios from 'axios'

// 创建axios实例
const service = axios.create({
  baseURL: 'http://localhost:8000/api',
  timeout: 10000 // 请求超时时间
})

// 响应拦截器
service.interceptors.response.use(
  response => {
    return response.data
  },
  error => {
    console.error('API错误', error)
    return Promise.reject(error)
  }
)

// API函数
export default {
  // 配置相关API
  config: {
    // 获取用户配置
    get () {
      return service.get('/config')
    },
    // 更新用户配置
    update (data) {
      return service.post('/config', data)
    }
  },

  // 市场数据相关API
  market: {
    // 获取所有市场数据
    getAll () {
      return service.get('/market-data')
    },
    // 获取特定资产的市场数据
    getByCode (code) {
      return service.get(`/market-data/${code}`)
    },
    // 获取特定资产的市场趋势分析
    getTrendByCode (code) {
      return service.get(`/market-trend/${code}`)
    },
    // 刷新市场数据
    refresh () {
      return service.post('/market-data/refresh')
    }
  },

  // 投资计划相关API
  plans: {
    // 获取所有投资计划
    getAll () {
      return service.get('/investment-plans')
    },
    // 获取最新投资计划
    getLatest () {
      return service.get('/investment-plans/latest')
    },
    // 生成新的投资计划
    generate () {
      return service.post('/investment-plans/generate')
    },
    // 获取投资系数计算详情
    getDetails () {
      return service.get('/investment-details')
    },
    // 删除投资计划
    delete (planId) {
      return service.delete(`/investment-plans/${planId}`)
    },
    // 生成历史日期的投资计划
    generateHistorical (date) {
      return service.post('/historical-test', { historical_date: date })
    }
  },

  // 示例资产API
  assets: {
    // 获取示例资产列表
    getExamples () {
      return service.get('/assets/examples')
    }
  }
} 