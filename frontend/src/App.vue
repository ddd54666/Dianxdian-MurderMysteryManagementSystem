<!-- 全局布局：左侧侧边栏 + 右侧内容区 -->

<template>
  <div class="app-layout">
    <!-- 侧边栏 -->
    <el-menu
      :default-active="activeMenu"
      router
      class="sidebar-container"
      background-color="#F0EBE2"
      text-color="#5C4F3E"
      active-text-color="#8B7355"
    >
      <div class="sidebar-logo" :title="shopName">{{ shopName }}</div>
      <hr class="divider-line" style="margin: 0 16px 8px 16px;" />

      <el-menu-item index="/">
        <el-icon><HomeFilled /></el-icon>
        <span>首页</span>
      </el-menu-item>

      <el-menu-item index="/sessions">
        <el-icon><Tickets /></el-icon>
        <span>场次管理</span>
      </el-menu-item>

      <el-menu-item index="/carpools">
        <el-icon><Van /></el-icon>
        <span>拼车管理</span>
      </el-menu-item>

      <el-menu-item index="/dms">
        <el-icon><UserFilled /></el-icon>
        <span>DM管理</span>
      </el-menu-item>

      <el-menu-item index="/members">
        <el-icon><CreditCard /></el-icon>
        <span>会员管理</span>
      </el-menu-item>

      <el-menu-item index="/scripts">
        <el-icon><Reading /></el-icon>
        <span>剧本管理</span>
      </el-menu-item>

      <el-sub-menu index="stats">
        <template #title>
          <el-icon><DataAnalysis /></el-icon>
          <span>统计信息</span>
        </template>
        <el-menu-item index="/stats/revenue">
          <span>💰 营业额统计 🔒</span>
        </el-menu-item>
        <el-menu-item index="/stats/scripts">
          <span>📖 剧本场次统计</span>
        </el-menu-item>
        <el-menu-item index="/stats/dms">
          <span>👤 DM开本统计</span>
        </el-menu-item>
      </el-sub-menu>

      <el-menu-item index="/messages">
        <el-icon><ChatLineSquare /></el-icon>
        <span>留言板</span>
      </el-menu-item>
    </el-menu>

    <!-- 内容区 -->
    <div class="main-content">
      <router-view />
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, watch } from 'vue'
import { useRoute } from 'vue-router'
import { loadShopInfo, shopName } from './utils/shop.js'

const route = useRoute()

/* 页面启动时读取店铺名称，供侧边栏和首页共同展示。 */
onMounted(loadShopInfo)

/* 店铺名称更新时同步浏览器标题。 */
watch(shopName, name => {
  document.title = `${name} | 剧本杀店铺管理系统`
}, { immediate: true })

/* 计算当前激活菜单项 */
const activeMenu = computed(() => {
  const path = route.path
  if (path.startsWith('/stats')) return path
  return path
})
</script>

<style scoped>
.app-layout {
  display: flex;
  height: 100vh;
}

.sidebar-container {
  flex-shrink: 0;
  overflow-y: auto;
  overflow-x: hidden;
}

/* 店铺名称较长时省略显示，完整名称可通过悬停查看。 */
.sidebar-logo {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* Element Plus 菜单项左侧激活指示条 */
.sidebar-container :deep(.el-menu-item.is-active) {
  border-left: 3px solid #8B7355;
}

/* 子菜单样式 */
.sidebar-container :deep(.el-sub-menu .el-menu-item) {
  padding-left: 56px !important;
  min-width: 220px;
}
</style>
