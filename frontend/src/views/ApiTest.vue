<template>
  <div class="api-test-container">
    <el-card shadow="hover" class="api-test-card">
      <template #header>
        <div class="card-header">
          <h2>API接口测试</h2>
        </div>
      </template>
      
      <div class="test-content">
        <p>此页面用于测试前端API与后端接口的连接状态。点击下面的按钮开始测试所有接口。</p>
        <p>测试结果将显示在下面的面板中和浏览器控制台。</p>
        
        <div class="button-container">
          <el-button 
            type="primary" 
            @click="runApiTest" 
            :loading="testing"
            :disabled="testing"
          >
            开始测试所有接口
          </el-button>
        </div>
        
        <div v-if="testCompleted" class="result-summary">
          <el-alert
            :type="testResults.failed > 0 ? 'error' : 'success'"
            :title="testResults.failed > 0 ? '接口测试发现问题' : '所有测试的接口都可以访问'"
            :closable="false"
            show-icon
          />
          
          <el-descriptions title="测试结果摘要" :column="3" border>
            <el-descriptions-item label="总测试数">
              {{ testResults.total }}
            </el-descriptions-item>
            <el-descriptions-item label="成功">
              <span class="success-text">{{ testResults.success }}</span>
            </el-descriptions-item>
            <el-descriptions-item label="失败">
              <span class="fail-text">{{ testResults.failed }}</span>
            </el-descriptions-item>
          </el-descriptions>
        </div>
        
        <div v-if="testCompleted" class="debug-tips">
          <el-divider content-position="left">详细测试结果</el-divider>
          <p>测试详情已输出到浏览器控制台，请按F12或右键检查并选择Console标签查看。</p>
          
          <div class="debug-instructions">
            <h3>如果测试失败，请检查：</h3>
            <ol>
              <li>后端服务是否已启动并运行在 <code>http://localhost:8000</code></li>
              <li>CORS设置是否正确，允许前端域名的请求</li>
              <li>网络连接是否正常</li>
              <li>API路径是否匹配</li>
            </ol>
            
            <h3>后端启动命令：</h3>
            <div class="code-block">
              <pre>cd backend
python main.py</pre>
            </div>
            
            <h3>运行后端API测试脚本：</h3>
            <div class="code-block">
              <pre>cd backend
python test_api.py</pre>
            </div>
          </div>
        </div>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import { testApi } from '../utils/api-tester'

const testing = ref(false)
const testCompleted = ref(false)
const testResults = ref({
  success: 0,
  failed: 0,
  total: 0
})

const runApiTest = async () => {
  testing.value = true
  testCompleted.value = false
  
  try {
    console.clear() // 清除之前的控制台输出
    
    ElMessage.info('API测试开始，请查看浏览器控制台了解详情')
    
    // 运行API测试
    const results = await testApi()
    
    // 更新测试结果
    testResults.value = results
    testCompleted.value = true
    
    if (results.failed > 0) {
      ElMessage.warning(`测试完成，有 ${results.failed} 个接口测试失败`)
    } else {
      ElMessage.success('所有接口测试成功')
    }
  } catch (error) {
    console.error('测试过程中出错:', error)
    ElMessage.error('测试过程中出错，请查看控制台')
  } finally {
    testing.value = false
  }
}
</script>

<style scoped>
.api-test-container {
  padding: 20px;
}

.api-test-card {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.card-header h2 {
  margin: 0;
}

.test-content {
  line-height: 1.6;
}

.button-container {
  margin: 20px 0;
  display: flex;
  justify-content: center;
}

.result-summary {
  margin: 20px 0;
}

.success-text {
  color: #67C23A;
  font-weight: bold;
}

.fail-text {
  color: #F56C6C;
  font-weight: bold;
}

.debug-tips {
  margin-top: 30px;
}

.debug-instructions {
  background-color: #f8f8f8;
  padding: 15px;
  border-radius: 4px;
  margin-top: 15px;
}

.debug-instructions h3 {
  margin-top: 20px;
  margin-bottom: 10px;
  font-size: 16px;
}

.debug-instructions ol, .debug-instructions ul {
  padding-left: 20px;
  margin-bottom: 15px;
}

.code-block {
  background-color: #2d2d2d;
  color: #eee;
  padding: 10px 15px;
  border-radius: 4px;
  margin: 10px 0;
}

.code-block pre {
  margin: 0;
  white-space: pre-wrap;
}
</style> 