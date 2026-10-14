/* 全局初始化：创建 Vue 应用，注册插件，挂载 DOM。 */

import { createApp } from 'vue'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import zhCn from 'element-plus/dist/locale/zh-cn.mjs'
import * as ElementPlusIconsVue from '@element-plus/icons-vue'
import App from './App.vue'
import router from './router/index.js'
import './styles/global.css'

const app = createApp(App)

app.use(router)
app.use(ElementPlus, { locale: zhCn })

/* 全局注册 Element Plus 图标 */
for (const [key, component] of Object.entries(ElementPlusIconsVue)) {
  app.component(key, component)
}

app.mount('#app')
