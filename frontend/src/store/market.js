import { defineStore } from 'pinia'
import api from '../api'

export const useMarketStore = defineStore('market', {
  state: () => ({
    marketData: {},
    loading: false,
    refreshing: false,
    lastUpdated: null
  }),

  getters: {
    // 获取所有市场数据列表
    marketDataList: (state) => {
      return Object.values(state.marketData)
    },

    // 格式化最后更新时间
    formattedLastUpdated: (state) => {
      if (!state.lastUpdated) return '暂无数据'
      return new Date(state.lastUpdated).toLocaleString('zh-CN')
    }
  },

  actions: {
    // 加载所有市场数据
    async loadMarketData () {
      this.loading = true
      try {
        const data = await api.market.getAll()
        this.marketData = data

        // 更新最后更新时间
        const timestamps = Object.values(data)
          .map(item => item.updated_at ? new Date(item.updated_at).getTime() : 0)
          .filter(time => time > 0)

        if (timestamps.length > 0) {
          this.lastUpdated = new Date(Math.max(...timestamps)).toISOString()
        }
      } catch (error) {
        console.error('加载市场数据失败', error)
      } finally {
        this.loading = false
      }
    },

    // 刷新市场数据
    async refreshMarketData () {
      this.refreshing = true
      try {
        await api.market.refresh()
        // 等待一段时间给后端处理数据的时间
        await new Promise(resolve => setTimeout(resolve, 2000))
        // 重新加载市场数据
        await this.loadMarketData()
      } catch (error) {
        console.error('刷新市场数据失败', error)
      } finally {
        this.refreshing = false
      }
    },

    // 获取特定资产的市场数据
    getAssetMarketData (code) {
      return this.marketData[code] || null
    },

    // 清空市场数据
    clearMarketData () {
      this.marketData = {}
      this.lastUpdated = null
    }
  }
}) 