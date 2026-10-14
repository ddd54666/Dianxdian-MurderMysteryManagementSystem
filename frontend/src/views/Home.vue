<!-- 首页：展示店铺名称、系统简介和通用使用指南。 -->

<template>
  <div class="home-wrapper">
    <div class="home-card">
      <el-icon class="avatar" aria-hidden="true"><Reading /></el-icon>
      <h1>{{ shopName }}</h1>
      <p class="subtitle">点小点剧本杀店铺管理系统</p>
      <hr class="divider-line" />
      <p class="desc">记录开本场次、会员储值与 DM 薪资，便于查询和经营统计。</p>
    </div>
    <div class="home-intro">
      <p>项目开发者：<img src="/dd.png" class="dev-img" alt="开发者仓鼠头像" /></p>
    </div>
    <el-button class="guide-btn" @click="drawerVisible = true">查看使用指南</el-button>

    <!-- 使用指南抽屉 -->
    <el-drawer v-model="drawerVisible" title="使用指南" size="520px">
      <div class="guide-content">
        <div class="guide-section">
          <h3>场次记录</h3>
          <p class="guide-placeholder">在“场次管理”中选择“新增场次”，输入剧本或 DM 名称的关键词，再从搜索结果中选择对应档案。若档案不存在，可使用表单中的新增按钮，或先到剧本管理、DM 管理中建立档案。</p>
          <p class="guide-placeholder">剧本单价和营业额可根据折扣、活动或实际收费调整。单 DM 场次的薪资默认为剧本单价，且必须大于 0；多 DM 场次可分别填写薪资，未填写时默认为 0。</p>
        </div>
        <div class="guide-section">
          <h3>会员与经营统计</h3>
          <p class="guide-placeholder">新增储值会员时需要填写初始充值。后续充值、消费及交易记录的编辑或删除会同步更新余额。营业额、剧本场次和 DM 开本统计支持按年或按月查看。</p>
          <p class="guide-placeholder">会员管理和营业额统计页面使用二级密码解锁，解锁状态有效期为 3 分钟。请由店铺负责人管理密码，财务操作完成后及时关闭相关页面。</p>
        </div>
        <div class="guide-section">
          <h3>关于拼车管理</h3>
          <p class="guide-placeholder">拼车管理模块目前弃用，尚未完成正式使用所需的开发。</p>
        </div>
        <div class="guide-section">
          <h3>资料维护与反馈</h3>
          <p class="guide-placeholder">剧本价格、人数或其他档案信息有变化时可以在对应管理页面中修改。系统问题或功能建议可记录在留言板中，反馈时请说明具体场景。</p>
        </div>
      </div>
    </el-drawer>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { shopName } from '../utils/shop.js'

/* 使用指南抽屉可见性 */
const drawerVisible = ref(false)
</script>

<style scoped>
.home-wrapper {
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  min-height: calc(100vh - 120px);
  position: relative;
}

.home-card {
  text-align: center;
  max-width: 480px;
  margin-top: -150px; /* 调整首页卡片的垂直位置。 */
}

/* 通用系统图标样式。 */
.avatar {
  width: 80px;
  height: 80px;
  border-radius: 50%;
  font-size: 40px;
  color: #8B7355;
  border: 2px solid #E5DDD0;
  margin-bottom: 16px;
}

.home-card h1 {
  font-family: "STFangsong", "FZFS", "FangSong", "华文仿宋", "仿宋", serif;
  font-size: 32px;
  font-weight: normal;
  letter-spacing: 4px;
  color: #3D3226;
  overflow-wrap: anywhere;
}

.subtitle {
  font-family: "STFangsong", "FZFS", "FangSong", "华文仿宋", "仿宋", serif;
  font-size: 16px;
  letter-spacing: 2px;
  color: #8C7B6B;
  margin-top: 4px;
}

.desc {
  font-family: "SimSun", "STSong", "宋体", "Noto Serif SC", serif;
  color: #5C4F3E;
  line-height: 1.8;
  margin-bottom: 20px;
}

/* 左下角简介文本框 */
.home-intro {
  position: absolute;
  bottom: 100px;
  left: 50px;
  max-width: 800px;
  padding: 12px 16px;
  background: transparent;
  border: none;
  border-radius: 4px;
  font-family: "SimSun", "STSong", "宋体", "Noto Serif SC", serif;
  font-size: 14px;
  color: #5C4F3E;
  line-height: 1.8;
}

.home-intro p {
  margin: 0;
}

/* 开发者仓鼠头像保持原有尺寸和行内展示方式。 */
.dev-img {
  display: inline-block;
  width: 50px;
  height: 50px;
  margin-left: 6px;
  vertical-align: middle;
  border-radius: 40%;
}

/* 使用指南按钮 */
.guide-btn {
  position: absolute;
  bottom: 50px;
  left: 80px;
  font-family: "STFangsong","FangSong",serif;
  font-size: 15px;
  color: #8B7355;
  background: #FDFBF7;
  border: 1px solid #D9D0C1;
  border-radius: 4px;
  padding: 8px 20px;
  cursor: pointer;
  transition: all 0.2s;
}
.guide-btn:hover {
  background: #F0EBE2;
  border-color: #8B7355;
}

/* 抽屉内指南内容 */
.guide-content {
  font-family: "SimSun","STSong","宋体",serif;
  color: #5C4F3E;
  line-height: 2;
  padding: 0 8px;
}
.guide-section {
  margin-bottom: 28px;
}
.guide-section h3 {
  font-family: "STFangsong","FangSong",serif;
  font-size: 16px;
  font-weight: normal;
  color: #3D3226;
  margin: 0 0 10px 0;
  padding-bottom: 6px;
  border-bottom: 1px solid #E5DDD0;
}
.guide-placeholder {
  font-size: 14px;
  color: #8C7B6B;
  background: #FDFBF7;
  border: 1px dashed #D9D0C1;
  border-radius: 4px;
  padding: 14px 16px;
  margin: 0;
}
</style>
