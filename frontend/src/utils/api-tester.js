/**
 * 自动定投策略提醒系统 - 前端API接口测试工具
 * 
 * 用于验证前端API调用是否与后端接口匹配
 */
import api from '../api'

export const testApi = async () => {
  const startTime = new Date()
  console.log(
    '%c自动定投策略提醒系统 - API接口测试',
    'color: #fff; background: #409EFF; padding: 4px 8px; border-radius: 4px; font-weight: bold;'
  )
  console.log(`测试开始时间: ${startTime.toLocaleString()}`)

  // 测试结果统计
  const results = {
    success: 0,
    failed: 0,
    total: 0
  }

  /**
   * 测试单个API调用
   * @param {string} name - API名称 
   * @param {Function} apiCall - API调用函数
   * @param {any} params - API调用参数 
   */
  const testApiCall = async (name, apiCall, params = null) => {
    results.total++
    console.log(`\n%c测试接口: ${name}`, 'color: #409EFF; font-weight: bold;')

    try {
      console.log('请求参数:', params || '无')
      const startCallTime = performance.now()
      const response = await (params !== null ? apiCall(params) : apiCall())
      const endCallTime = performance.now()

      console.log(
        `%c✓ 请求成功 (${(endCallTime - startCallTime).toFixed(2)}ms)`,
        'color: #67C23A; font-weight: bold;'
      )
      console.log('响应数据:', response)
      results.success++
      return response
    } catch (error) {
      console.log(
        `%c✗ 请求失败`,
        'color: #F56C6C; font-weight: bold;'
      )
      console.error('错误信息:', error)
      results.failed++
      return null
    }
  }

  // 测试配置相关API
  await testApiCall('获取用户配置', api.config.get)

  // 仅测试配置更新API的可用性，不修改数据
  try {
    const currentConfig = await api.config.get()
    if (currentConfig) {
      await testApiCall('更新用户配置(不修改数据)', api.config.update, currentConfig)
    }
  } catch (e) {
    console.log('跳过配置更新测试，因为无法获取当前配置')
  }

  // 测试示例资产API
  await testApiCall('获取示例资产', api.assets.getExamples)

  // 测试市场数据API
  const marketData = await testApiCall('获取所有市场数据', api.market.getAll)

  // 如果有市场数据，测试获取单个资产数据
  if (marketData && Object.keys(marketData).length > 0) {
    const firstAssetCode = Object.keys(marketData)[0]
    await testApiCall(
      `获取特定资产数据 (${firstAssetCode})`,
      api.market.getByCode,
      firstAssetCode
    )
  }

  await testApiCall('刷新市场数据', api.market.refresh)

  // 测试投资计划API
  await testApiCall('获取所有投资计划', api.plans.getAll)

  // 测试获取最新计划API (可能成功也可能失败，取决于是否有数据)
  try {
    await testApiCall('获取最新投资计划', api.plans.getLatest)
  } catch (e) {
    console.log('最新计划可能不存在，这是预期的可能结果')
  }

  // 测试获取投资系数计算详情API
  try {
    await testApiCall('获取投资系数计算详情', api.plans.getDetails)
  } catch (e) {
    console.log('获取投资系数计算详情失败', e)
  }

  // 输出测试结果摘要
  console.log('\n%c测试结果摘要', 'color: #409EFF; font-weight: bold;')
  console.log(`总测试数: ${results.total}`)
  console.log(`成功: ${results.success}`)
  console.log(`失败: ${results.failed}`)

  const endTime = new Date()
  const duration = (endTime - startTime) / 1000
  console.log(`\n测试完成时间: ${endTime.toLocaleString()}`)
  console.log(`总耗时: ${duration.toFixed(2)}秒`)

  return results
}

export default {
  testApi
} 