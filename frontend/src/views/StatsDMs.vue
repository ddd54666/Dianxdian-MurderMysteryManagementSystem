<!-- DM开本统计：按年/按月切换 + 排行柱状图 + DM总览方块网格 + 点击详情弹窗 -->
<template>
  <div>
    <h2 class="page-title">DM开本统计</h2>
    <hr class="divider-line" />

    <!-- 筛选栏 -->
    <div class="filter-bar">
      <div class="toggle-btns">
        <button :class="['toggle-btn', { active: viewMode === 'year' }]" @click="setViewMode('year')">按年统计</button>
        <button :class="['toggle-btn', { active: viewMode === 'month' }]" @click="setViewMode('month')">按月统计</button>
      </div>

      <div class="nav-arrows">
        <el-button :icon="DArrowLeft" circle size="small" @click="prevYear" title="上一年" />
        <el-button v-if="viewMode === 'month'" :icon="ArrowLeft" circle size="small" @click="prevMonth" title="上一月" />
        <span class="nav-label">{{ labelText }}</span>
        <el-button v-if="viewMode === 'month'" :icon="ArrowRight" circle size="small" @click="nextMonth" title="下一月" />
        <el-button :icon="DArrowRight" circle size="small" @click="nextYear" title="下一年" />
      </div>

      <div style="flex:1;"></div>
      <el-button @click="exportSummary">导出汇总CSV</el-button>
      <el-button @click="exportDetail">导出明细CSV</el-button>
    </div>

    <!-- 排行竖柱状图 -->
    <div class="chart-box">
      <div class="chart-title">DM开本排行</div>
      <div ref="chartRank" class="chart-el" :style="{ height: rankChartHeight }"></div>
    </div>

    <!-- DM总览方块网格 -->
    <div class="chart-box">
      <div class="block-title-row">
        <span class="chart-title" style="margin-bottom:0;">DM总览</span>
        <el-input v-model="dmSearch" placeholder="搜索DM" clearable size="small" style="width: 140px;" />
      </div>
      <p class="block-hint">点击DM以查看详细统计</p>
      <div class="block-grid">
        <div
          v-for="d in filteredDms" :key="d.dm_id"
          class="dm-block"
          @click="openDmDetail(d)"
        >
          <div class="dm-block-name">{{ d.dm_name }}</div>
          <div class="dm-block-count">{{ d.session_count }} 场</div>
        </div>
        <div v-if="filteredDms.length === 0" style="grid-column: 1/-1; text-align: center; color: #BFB5A8;">
          暂无数据
        </div>
      </div>
    </div>

    <!-- DM详情弹窗 -->
    <el-dialog v-model="detailVisible" :title="`DM统计 - ${detailDm?.dm_name || ''}`" width="520px" top="8vh">
      <template v-if="detailDm">
        <div class="detail-stats">
          <div class="detail-stat-card">
            <div class="ds-label">本月开本</div>
            <div class="ds-value">{{ detailData.this_month_count }} 场</div>
          </div>
          <div class="detail-stat-card">
            <div class="ds-label">今年开本</div>
            <div class="ds-value">{{ detailData.this_year_count }} 场</div>
          </div>
          <div class="detail-stat-card">
            <div class="ds-label">本月薪资</div>
            <div class="ds-value">{{ toYuan(detailData.this_month_salary) }} 元</div>
          </div>
          <div class="detail-stat-card">
            <div class="ds-label">今年薪资</div>
            <div class="ds-value">{{ toYuan(detailData.this_year_salary) }} 元</div>
          </div>
        </div>
        <div class="chart-title" style="margin-top: 16px;">近13个月统计</div>
        <div ref="chartDetailTrend" class="chart-el" style="height: 260px;"></div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, watch, computed, nextTick, onUnmounted } from 'vue'
import { ArrowLeft, ArrowRight, DArrowLeft, DArrowRight } from '@element-plus/icons-vue'
import { get } from '../utils/request.js'
import { toYuan } from '../utils/money.js'
import { COLORS, baseOption, createChart, disposeChart } from '../utils/chart-theme.js'

const viewMode = ref('month')
const filterYear = ref(new Date().getFullYear())
const filterMonth = ref(new Date().getMonth() + 1)
const ranking = ref([])
const dmSearch = ref('')

const chartRank = ref(null)
const chartDetailTrend = ref(null)

const rankData = computed(() => {
  return (ranking.value || []).filter(d => d.session_count > 0)
})

const rankChartHeight = computed(() => `${Math.max(rankData.value.length * 30, 120)}px`)
let chartInstances = []

const detailVisible = ref(false)
const detailDm = ref(null)
const detailData = ref({ this_month_count: 0, this_year_count: 0, this_month_salary: 0, this_year_salary: 0, trend_13months: [] })

const labelText = computed(() => viewMode.value === 'year' ? `${filterYear.value}年` : `${filterYear.value}年${filterMonth.value}月`)

const filteredDms = computed(() => {
  let list = ranking.value.filter(d => d.session_count > 0)
  if (dmSearch.value) {
    const q = dmSearch.value.toLowerCase()
    list = list.filter(d => d.dm_name.toLowerCase().includes(q))
  }
  return list
})

onUnmounted(() => chartInstances.forEach(disposeChart))

async function fetchData() {
  const params = { year: filterYear.value }
  if (viewMode.value === 'month') params.month = filterMonth.value
  const res = await get('/api/stats/dms', params)
  ranking.value = res.data.ranking || []

  await nextTick()
  chartInstances.forEach(disposeChart)
  chartInstances = []
}

/* 排行竖柱状图（watch 响应，自动 resize） */
watch(rankData, async (list) => {
  await nextTick()
  const c = createChart(chartRank)
  if (!c) return
  c.resize()
  c.setOption(baseOption({
    tooltip: { trigger: 'axis', formatter: p => `<b>${p[0].name}</b><br/>开本 ${p[0].value} 次` },
    xAxis: { type: 'category', data: list.map(r => r.dm_name), axisLabel: { fontSize: 12, color: COLORS.text }, axisLine: { lineStyle: { color: COLORS.grid } } },
    yAxis: { type: 'value', splitLine: { lineStyle: { color: COLORS.grid, type: 'dashed' } }, minInterval: 1 },
    series: [{
      type: 'bar', barWidth: '50%', data: list.map(r => r.session_count),
      itemStyle: { color: COLORS.primary, borderRadius: [4, 4, 0, 0] }
    }]
  }), true)
  chartInstances = chartInstances.filter(ci => ci !== c)
  chartInstances.push(c)
})

/* DM详情弹窗 */
async function openDmDetail(dm) {
  detailDm.value = dm
  detailVisible.value = true
  detailData.value = { this_month_count: 0, this_year_count: 0, this_month_salary: 0, this_year_salary: 0, trend_13months: [] }
  try {
    const res = await get(`/api/stats/dms/${dm.dm_id}/detail`)
    detailData.value = res.data
    await nextTick()
    buildDetailTrendChart()
  } catch { /* 静默失败 */ }
}

function buildDetailTrendChart() {
  const c = createChart(chartDetailTrend)
  if (!c) return
  const trend = detailData.value.trend_13months || []
  c.setOption(baseOption({
    tooltip: { trigger: 'axis', formatter: p => {
      const bar = p.find(q => q.seriesName === '薪资')
      const line = p.find(q => q.seriesName === '开本次数')
      return `${p[0].axisValue}<br/>薪资：<b>${Number(bar?.value ?? 0).toFixed(0)}</b> 元<br/>开本：<b>${line?.value ?? 0}</b> 场`
    }},
    legend: { bottom: 0, textStyle: { fontSize: 12, color: COLORS.textDim }, data: ['薪资', '开本次数'] },
    xAxis: { type: 'category', data: trend.map(r => r.month), axisLine: { lineStyle: { color: COLORS.grid } }, axisLabel: { fontSize: 11, color: COLORS.text } },
    yAxis: [
      { type: 'value', name: '元', nameTextStyle: { fontSize: 11, color: COLORS.textDim }, splitLine: { lineStyle: { color: COLORS.grid, type: 'dashed' } } },
      { type: 'value', name: '场', nameTextStyle: { fontSize: 11, color: COLORS.textDim }, splitLine: { show: false }, minInterval: 1 }
    ],
    series: [
      { name: '薪资', type: 'bar', barWidth: '50%', data: trend.map(r => r.salary / 100), itemStyle: { color: COLORS.primaryLight, borderRadius: [4, 4, 0, 0] } },
      { name: '开本次数', type: 'line', yAxisIndex: 1, smooth: true, symbol: 'circle', symbolSize: 6, data: trend.map(r => r.count), itemStyle: { color: COLORS.accent1 }, lineStyle: { color: COLORS.accent1, width: 2 } }
    ]
  }))
}

/* 年月导航 */
function prevYear() { filterYear.value--; fetchData() }
function nextYear() { filterYear.value++; fetchData() }
function prevMonth() {
  if (filterMonth.value === 1) { filterMonth.value = 12; filterYear.value-- }
  else filterMonth.value--
  fetchData()
}
function nextMonth() {
  if (filterMonth.value === 12) { filterMonth.value = 1; filterYear.value++ }
  else filterMonth.value++
  fetchData()
}
function setViewMode(mode) {
  if (viewMode.value === mode) return
  viewMode.value = mode
  if (mode === 'year') filterMonth.value = new Date().getMonth() + 1
  fetchData()
}

fetchData()

function exportSummary() { window.open(`/api/stats/export/summary?type=dms&year=${filterYear.value}${viewMode.value === 'month' ? '&month=' + filterMonth.value : ''}`) }
function exportDetail() { window.open(`/api/stats/export/detail?year=${filterYear.value}${viewMode.value === 'month' ? '&month=' + filterMonth.value : ''}`) }
</script>

<style scoped>
/* 筛选栏 */
.filter-bar { display: flex; gap: 12px; margin-bottom: 20px; align-items: center; flex-wrap: wrap; }
.toggle-btns { display: flex; }
.toggle-btn {
  font-family: "STFangsong","FangSong",serif; font-size: 14px;
  padding: 6px 16px; border: 1px solid #D9D0C1; background: #FDFBF7; color: #5C4F3E;
  cursor: pointer; transition: all 0.2s;
}
.toggle-btn:first-child { border-radius: 4px 0 0 4px; }
.toggle-btn:last-child { border-radius: 0 4px 4px 0; border-left: none; }
.toggle-btn.active { background: #8B7355; color: #fff; border-color: #8B7355; }
.toggle-btn:not(.active):hover { background: #F0EBE2; }

.nav-arrows { display: flex; align-items: center; gap: 6px; }
.nav-label { font-family: "STFangsong","FangSong",serif; font-size: 15px; color: #3D3226; min-width: 90px; text-align: center; }

/* 图表 */
.chart-box { background: #FDFBF7; border: 1px solid #E5DDD0; border-radius: 4px; padding: 16px; margin-bottom: 16px; }
.chart-title { font-family: "STFangsong","FangSong",serif; font-size: 14px; color: #5C4F3E; text-align: center; margin-bottom: 8px; }
.chart-el { width: 100%; }
.chart-bar { height: 350px; }

/* DM方块网格 */
.block-title-row { display: flex; align-items: center; justify-content: space-between; margin-bottom: 4px; }
.block-hint { text-align: center; font-size: 12px; color: #8C7B6B; margin-bottom: 12px; }
.block-grid { display: grid; grid-template-columns: repeat(8, 1fr); gap: 10px; }
.dm-block {
  background: #F0EBE2; border: 1px solid #E0D7C8; border-radius: 4px;
  padding: 10px 6px; text-align: center; cursor: pointer;
  transition: background 0.2s, border-color 0.2s;
}
.dm-block:hover { background: #EBE3D6; border-color: #8B7355; }
.dm-block-name { font-family: "STFangsong","FangSong",serif; font-size: 15px; color: #3D3226; }
.dm-block-count { font-size: 12px; color: #8C7B6B; margin-top: 2px; }

/* 详情弹窗 */
.detail-stats { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }
.detail-stat-card { background: #F0EBE2; border: 1px solid #E0D7C8; border-radius: 4px; padding: 12px; text-align: center; }
.ds-label { font-size: 12px; color: #8C7B6B; }
.ds-value { font-family: "SimSun","STSong","宋体",serif; font-size: 18px; color: #8B7355; margin-top: 4px; }
</style>
