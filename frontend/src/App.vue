<template>
  <el-config-provider :locale="zhCn">
    <div class="app-container">
      <el-container>
        <el-header height="60px">
          <div class="header-container">
            <h1>自动定投策略提醒系统</h1>
          </div>
        </el-header>
        <el-container>
          <el-aside width="200px">
            <el-menu
              :router="true"
              default-active="/"
              class="el-menu-vertical"
              background-color="#001529"
              text-color="#fff"
              active-text-color="#ffd04b"
            >
              <el-menu-item index="/">
                <el-icon><el-icon-menu /></el-icon>
                <span>首页</span>
              </el-menu-item>
              <el-menu-item index="/config">
                <el-icon><el-icon-setting /></el-icon>
                <span>投资配置</span>
              </el-menu-item>
              <el-menu-item index="/market">
                <el-icon><el-icon-data-line /></el-icon>
                <span>市场数据</span>
              </el-menu-item>
              <el-menu-item index="/plans">
                <el-icon><el-icon-document /></el-icon>
                <span>投资计划</span>
              </el-menu-item>
              <el-menu-item index="/historical-test">
                <el-icon><el-icon-time /></el-icon>
                <span>历史数据测试</span>
              </el-menu-item>
              <el-divider
                style="margin: 10px 0; border-color: rgba(255, 255, 255, 0.1)"
              />
              <el-menu-item index="/api-test">
                <el-icon><el-icon-connection /></el-icon>
                <span>接口测试</span>
              </el-menu-item>
            </el-menu>
          </el-aside>
          <el-main>
            <router-view />
          </el-main>
        </el-container>
      </el-container>
    </div>
  </el-config-provider>
</template>

<script setup>
import { ElConfigProvider } from "element-plus";
import zhCn from "element-plus/es/locale/lang/zh-cn";
import {
  Menu as ElIconMenu,
  Setting as ElIconSetting,
  DataLine as ElIconDataLine,
  Document as ElIconDocument,
  Connection as ElIconConnection,
  Time as ElIconTime,
} from "@element-plus/icons-vue";
</script>

<style scoped>
.app-container {
  height: 100vh;
  width: 100%;
}

.header-container {
  display: flex;
  align-items: center;
  height: 100%;
}

.el-header {
  background-color: #001529;
  color: #fff;
  padding: 0 20px;
}

.el-aside {
  background-color: #001529;
}

.el-menu-vertical {
  height: calc(100vh - 60px);
  border-right: none;
}
</style>
