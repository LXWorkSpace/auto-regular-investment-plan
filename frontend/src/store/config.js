import { defineStore } from 'pinia'
import api from '../api'

export const useConfigStore = defineStore('config', {
  state: () => ({
    config: {
      monthly_investment: 0,
      assets: [],
      buffer_amount: 500.0
    },
    loading: false,
    saving: false,
    exampleAssets: []
  }),

  getters: {
    totalWeight: (state) => {
      return state.config.assets.reduce((sum, asset) => sum + asset.weight, 0)
    },
    isValidConfig: (state) => {
      return (
        state.config.monthly_investment > 0 &&
        state.config.assets.length > 0
      )
    }
  },

  actions: {
    // 加载用户配置
    async loadConfig () {
      this.loading = true
      try {
        const data = await api.config.get()
        this.config = data
      } catch (error) {
        console.error('加载配置失败', error)
      } finally {
        this.loading = false
      }
    },

    // 保存用户配置
    async saveConfig () {
      this.saving = true
      try {
        await api.config.update(this.config)
      } catch (error) {
        console.error('保存配置失败', error)
      } finally {
        this.saving = false
      }
    },

    // 加载示例资产
    async loadExampleAssets () {
      try {
        const data = await api.assets.getExamples()
        this.exampleAssets = data
      } catch (error) {
        console.error('加载示例资产失败', error)
      }
    },

    // 添加资产
    addAsset (asset) {
      // 检查是否已存在相同代码的资产
      const exists = this.config.assets.some(a => a.code === asset.code)
      if (!exists) {
        this.config.assets.push({
          ...asset,
          weight: 0,
          id: Date.now().toString() // 简单的ID生成
        })
      }
    },

    // 移除资产
    removeAsset (assetId) {
      this.config.assets = this.config.assets.filter(a => a.id !== assetId)
    },

    // 更新资产权重
    updateAssetWeight (assetId, weight) {
      const asset = this.config.assets.find(a => a.id === assetId)
      if (asset) {
        asset.weight = weight
      }
    },

    // 自动平衡权重
    balanceWeights () {
      const count = this.config.assets.length
      if (count > 0) {
        const equalWeight = 1 / count
        this.config.assets.forEach(asset => {
          asset.weight = equalWeight
        })
      }
    }
  }
}) 