import { defineStore } from 'pinia'
import api from '../api'

export const useMarketStore = defineStore('market', {
  state: () => ({
    marketData: {},
    loading: false,
    refreshing: false,
    lastUpdated: null,
    investmentDetails: null,
    loadingDetails: false,
    marketTrends: {},  // 存储资产的市场趋势分析结果
    loadingTrends: false  // 加载趋势分析的状态
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
    },
    
    // 获取特定资产的投资系数详情
    getAssetInvestmentDetails: (state) => (assetCode) => {
      if (!state.investmentDetails) return null
      return {
        marketDataStatus: state.investmentDetails.market_data_status?.[assetCode] || null,
        coefficients: state.investmentDetails.coefficients?.[assetCode] || null,
        frequency: state.investmentDetails.frequency?.[assetCode] || null,
        specialConditions: state.investmentDetails.special_conditions?.[assetCode] || null,
        marketScores: state.investmentDetails.market_scores?.[assetCode] || null
      }
    },
    
    // 获取特定资产的市场趋势分析
    getAssetMarketTrend: (state) => (assetCode) => {
      return state.marketTrends[assetCode] || null
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
    },
    
    // 获取投资系数计算详情
    async loadInvestmentDetails () {
      this.loadingDetails = true
      try {
        const data = await api.plans.getDetails()
        this.investmentDetails = data
        return data
      } catch (error) {
        console.error('获取投资系数计算详情失败', error)
        return null
      } finally {
        this.loadingDetails = false
      }
    },
    
    // 获取特定资产的市场趋势分析
    async loadAssetMarketTrend (code) {
      this.loadingTrends = true
      try {
        const data = await api.market.getTrendByCode(code)
        // 更新趋势分析结果
        this.marketTrends = {
          ...this.marketTrends,
          [code]: data
        }
        return data
      } catch (error) {
        console.error(`获取资产 ${code} 市场趋势分析失败`, error)
        return null
      } finally {
        this.loadingTrends = false
      }
    },
    
    // 批量加载资产的市场趋势分析
    async loadAllAssetMarketTrends (assetCodes) {
      this.loadingTrends = true
      try {
        const promises = assetCodes.map(code => api.market.getTrendByCode(code))
        const results = await Promise.all(promises)
        
        // 更新趋势分析结果
        const trendsData = {}
        assetCodes.forEach((code, index) => {
          trendsData[code] = results[index]
        })
        
        this.marketTrends = {
          ...this.marketTrends,
          ...trendsData
        }
        
        return trendsData
      } catch (error) {
        console.error('批量加载市场趋势分析失败', error)
        return {}
      } finally {
        this.loadingTrends = false
      }
    }
  }
}) 