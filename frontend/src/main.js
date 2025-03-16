import { createApp } from 'vue'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import { createPinia } from 'pinia'
import App from './App.vue'
import router from './router'
import zhCn from 'element-plus/es/locale/lang/zh-cn'

// 创建应用实例
const app = createApp(App)

// 使用插件
app.use(ElementPlus, {
  locale: zhCn,
  size: 'default'
})
app.use(createPinia())
app.use(router)

// 挂载应用
app.mount('#app') 