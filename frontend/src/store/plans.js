import { defineStore } from 'pinia'
import api from '../api'

export const usePlansStore = defineStore('plans', {
  state: () => ({
    plans: [],
    currentPlan: null,
    loading: false,
    generating: false
  }),

  getters: {
    // 获取最新计划
    latestPlan: (state) => {
      return state.plans.length > 0 ? state.plans[0] : null
    },

    // 格式化计划生成时间
    formattedGeneratedAt: () => (plan) => {
      if (!plan || !plan.generated_at) return '未知时间'
      return new Date(plan.generated_at).toLocaleString('zh-CN')
    },

    // 计算特定计划的总投资金额
    totalAmount: () => (plan) => {
      if (!plan || !plan.recommendations) return 0
      return plan.recommendations.reduce((sum, rec) => sum + rec.single_amount, 0)
    },

    // 获取计划中的资产类型分布
    assetTypeDistribution: () => (plan) => {
      if (!plan || !plan.recommendations) return {}

      const distribution = {}

      plan.recommendations.forEach(rec => {
        const type = rec.asset.type
        if (!distribution[type]) {
          distribution[type] = 0
        }
        distribution[type] += rec.monthly_amount
      })

      return distribution
    }
  },

  actions: {
    // 加载所有投资计划
    async loadPlans () {
      this.loading = true
      try {
        const data = await api.plans.getAll()
        this.plans = data
      } catch (error) {
        console.error('加载投资计划失败', error)
      } finally {
        this.loading = false
      }
    },

    // 加载最新投资计划
    async loadLatestPlan () {
      this.loading = true
      try {
        const data = await api.plans.getLatest()
        this.currentPlan = data

        // 如果plans为空，则添加当前计划
        if (this.plans.length === 0) {
          this.plans = [data]
        }
      } catch (error) {
        if (error.response && error.response.status === 404) {
          this.currentPlan = null
        } else {
          console.error('加载最新投资计划失败', error)
        }
      } finally {
        this.loading = false
      }
    },

    // 生成新的投资计划
    async generatePlan () {
      this.generating = true
      try {
        const data = await api.plans.generate()
        this.currentPlan = data

        // 更新计划列表
        await this.loadPlans()
      } catch (error) {
        console.error('生成投资计划失败', error)
      } finally {
        this.generating = false
      }
    },

    // 通过ID加载特定计划
    async loadPlanById (id) {
      // 首先尝试从已加载的计划中查找
      const existingPlan = this.plans.find(p => p.id === id)
      if (existingPlan) {
        this.currentPlan = existingPlan
        return
      }

      // 如果没有找到，可能需要加载所有计划
      this.loading = true
      try {
        await this.loadPlans()
        this.currentPlan = this.plans.find(p => p.id === id) || null
      } catch (error) {
        console.error('加载计划失败', error)
        this.currentPlan = null
      } finally {
        this.loading = false
      }
    },

    // 清空计划
    clearPlans () {
      this.plans = []
      this.currentPlan = null
    }
  }
}) 