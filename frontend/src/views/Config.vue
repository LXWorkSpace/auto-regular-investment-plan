<template>
  <div class="config-container">
    <el-card shadow="hover" class="config-card">
      <template #header>
        <div class="card-header">
          <h2>投资配置</h2>
          <div>
            <el-button
              type="success"
              @click="saveConfig"
              :loading="configStore.saving"
              :disabled="!configStore.isValidConfig"
            >
              保存配置
            </el-button>
          </div>
        </div>
      </template>

      <el-form
        :model="configStore.config"
        label-position="top"
        :rules="rules"
        ref="configForm"
        v-loading="configStore.loading"
      >
        <el-form-item label="月度投资金额(¥)" prop="monthly_investment">
          <el-input-number
            v-model="configStore.config.monthly_investment"
            :min="100"
            :step="100"
            :precision="0"
            style="width: 200px"
          />
        </el-form-item>

        <el-form-item label="资金池金额(¥)" prop="buffer_amount">
          <el-tooltip
            content="设置额外的资金池金额，作为月度投资额之外的资金，在特殊市场条件下（如极度超跌）启用"
          >
            <el-input-number
              v-model="configStore.config.buffer_amount"
              :min="0"
              :max="10000"
              :step="100"
              :precision="0"
              style="width: 200px"
            />
          </el-tooltip>
        </el-form-item>

        <el-divider content-position="left">投资标的配置</el-divider>

        <div class="assets-config">
          <div class="assets-header">
            <h3>
              已添加资产
              <el-tag type="info"
                >总权重:
                {{ percentageFormatter(configStore.totalWeight) }}</el-tag
              >
            </h3>
            <div>
              <el-button
                type="primary"
                size="small"
                @click="showAssetDialog"
                plain
              >
                添加资产
              </el-button>
              <el-button
                type="success"
                size="small"
                @click="configStore.balanceWeights"
                :disabled="configStore.config.assets.length === 0"
                plain
              >
                自动平衡权重
              </el-button>
            </div>
          </div>

          <el-table :data="configStore.config.assets" style="width: 100%">
            <el-table-column label="资产名称" prop="name" />
            <el-table-column label="代码" prop="code" width="100" />
            <el-table-column label="类型" prop="type" width="120" />
            <el-table-column label="权重" width="220">
              <template #default="scope">
                <el-slider
                  v-model="scope.row.weight"
                  :min="0"
                  :max="1"
                  :step="0.01"
                  :format-tooltip="percentageFormatter"
                  style="width: 180px"
                />
              </template>
            </el-table-column>
            <el-table-column label="权重%" width="80">
              <template #default="scope">
                {{ percentageFormatter(scope.row.weight) }}
              </template>
            </el-table-column>
            <el-table-column label="操作" width="80">
              <template #default="scope">
                <el-button
                  type="danger"
                  size="small"
                  circle
                  @click="configStore.removeAsset(scope.row.id)"
                  :icon="Delete"
                />
              </template>
            </el-table-column>
          </el-table>

          <el-empty
            v-if="configStore.config.assets.length === 0"
            description="请添加投资资产"
            :image-size="100"
          />
        </div>
      </el-form>
    </el-card>

    <!-- 添加资产对话框 -->
    <el-dialog v-model="assetDialogVisible" title="添加投资资产" width="500px">
      <el-tabs v-model="assetDialogTab">
        <el-tab-pane label="示例资产" name="examples">
          <el-table
            :data="configStore.exampleAssets"
            style="width: 100%"
            height="300px"
            @row-click="handleExampleClick"
          >
            <el-table-column label="资产名称" prop="name" />
            <el-table-column label="代码" prop="code" width="120" />
            <el-table-column label="类型" prop="type" width="120" />
          </el-table>
        </el-tab-pane>
        <el-tab-pane label="自定义资产" name="custom">
          <el-form :model="newAsset" label-position="top">
            <el-form-item label="资产名称" required>
              <el-input v-model="newAsset.name" />
            </el-form-item>
            <el-form-item label="资产代码" required>
              <el-input v-model="newAsset.code" />
            </el-form-item>
            <el-form-item label="资产类型" required>
              <el-select v-model="newAsset.type" style="width: 100%">
                <el-option label="中国指数" value="中国指数" />
                <el-option label="美国指数" value="美国指数" />
                <el-option label="黄金" value="黄金" />
                <el-option label="债券" value="债券" />
                <el-option label="现金" value="现金" />
                <el-option label="其他" value="其他" />
              </el-select>
            </el-form-item>
            <el-form-item label="描述">
              <el-input
                v-model="newAsset.description"
                type="textarea"
                rows="2"
              />
            </el-form-item>
          </el-form>
        </el-tab-pane>
      </el-tabs>
      <template #footer>
        <div class="dialog-footer">
          <el-button @click="assetDialogVisible = false">取消</el-button>
          <el-button
            type="primary"
            @click="addAsset"
            :disabled="
              assetDialogTab === 'custom' &&
              (!newAsset.name || !newAsset.code || !newAsset.type)
            "
          >
            添加
          </el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from "vue";
import { useConfigStore } from "../store/config";
import { ElMessage } from "element-plus";
import { Delete } from "@element-plus/icons-vue";

const configStore = useConfigStore();
const configForm = ref(null);
const assetDialogVisible = ref(false);
const assetDialogTab = ref("examples");
const newAsset = reactive({
  name: "",
  code: "",
  type: "",
  description: "",
});

// 表单验证规则
const rules = {
  monthly_investment: [
    { required: true, message: "请设置每月投资金额", trigger: "blur" },
    {
      type: "number",
      min: 100,
      message: "金额必须大于等于100",
      trigger: "blur",
    },
  ],
  buffer_amount: [
    { required: true, message: "请设置资金池金额", trigger: "blur" },
    {
      type: "number",
      min: 0,
      message: "资金池金额必须大于等于0",
      trigger: "blur",
    },
  ],
};

// 百分比格式化
const percentageFormatter = (val) => {
  return `${(val * 100).toFixed(0)}%`;
};

// 显示添加资产对话框
const showAssetDialog = () => {
  assetDialogVisible.value = true;
  assetDialogTab.value = "examples";
  Object.keys(newAsset).forEach((key) => {
    newAsset[key] = "";
  });
};

// 处理示例资产点击
const handleExampleClick = (row) => {
  assetDialogTab.value = "custom";
  Object.keys(newAsset).forEach((key) => {
    newAsset[key] = row[key] || "";
  });
};

// 添加资产
const addAsset = () => {
  if (assetDialogTab.value === "custom") {
    if (!newAsset.name || !newAsset.code || !newAsset.type) {
      ElMessage.warning("请完善资产信息");
      return;
    }
    configStore.addAsset({ ...newAsset });
  } else {
    const selectedAsset = configStore.exampleAssets.find(
      (a) => a.code === newAsset.code
    );
    if (selectedAsset) {
      configStore.addAsset(selectedAsset);
    } else {
      ElMessage.warning("请选择一个示例资产");
      return;
    }
  }
  assetDialogVisible.value = false;
};

// 保存配置
const saveConfig = async () => {
  if (!configStore.config.monthly_investment) {
    ElMessage.warning("请确保月度投资金额已设置");
    return;
  }

  try {
    await configStore.saveConfig();
    ElMessage.success("配置保存成功");
  } catch (error) {
    ElMessage.error("配置保存失败");
  }
};

// 生命周期钩子
onMounted(async () => {
  await configStore.loadConfig();
  await configStore.loadExampleAssets();
});
</script>

<style scoped>
.config-container {
  padding: 20px;
}

.config-card {
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

.assets-config {
  margin-top: 20px;
}

.assets-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px;
}

.assets-header h3 {
  margin: 0;
}

.mt-10 {
  margin-top: 10px;
}
</style>
