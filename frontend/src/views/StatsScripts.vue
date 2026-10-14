<!-- 剧本场次统计：按年/按月切换 + 箭头导航、全宽单列图表、剧本方块网格 + 点击详情弹窗 -->
<template>
  <div>
    <h2 class="page-title">剧本场次统计</h2>
    <hr class="divider-line" />

    <!-- 筛选栏：按年统计/按月统计 + 箭头导航 + CSV导出 -->
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

    <!-- 图表区：全宽单列 -->
    <div v-if="viewMode === 'year'" class="chart-box">
      <div class="chart-title">剧本场次每月汇总</div>
      <div ref="chartTrend" class="chart-el chart-trend"></div>
    </div>

    <div class="chart-box">
      <div class="chart-title-row">
        <span class="chart-title" style="margin-bottom:0;">剧本开本排行</span>
        <el-select v-model="rankTypeFilter" placeholder="全部类型" clearable size="small" style="width:100px;">
          <el-option v-for="t in ['欢乐','推理','恐怖','情感','机制']" :key="t" :label="t" :value="t" />
        </el-select>
      </div>
      <div ref="chartRank" class="chart-el" :style="{ height: rankChartHeight }"></div>
    </div>

    <!-- 饼图并排 -->
    <div class="pie-row">
      <div class="chart-box"><div class="chart-title">按剧本类型</div><div ref="chartType" class="chart-el chart-pie"></div></div>
      <div class="chart-box"><div class="chart-title">按盒装/城限</div><div ref="chartCategory" class="chart-el chart-pie"></div></div>
    </div>

    <!-- 剧本方块网格 -->
    <div class="chart-box">
      <div class="block-title-row">
        <span class="chart-title" style="margin-bottom:0;">剧本速览</span>
        <div class="block-filters">
          <el-input v-model="blockSearch" placeholder="搜索剧本" clearable size="small" style="width: 140px;" />
          <el-select v-model="blockTypeFilter" placeholder="全部类型" clearable size="small" style="width: 100px;">
            <el-option v-for="t in ['欢乐','推理','恐怖','情感','机制']" :key="t" :label="t" :value="t" />
          </el-select>
        </div>
      </div>
      <p class="block-hint">点击剧本以查看开本详情</p>
      <div class="block-grid">
        <div
          v-for="s in filteredScripts" :key="s.script_id"
          class="script-block"
          @click="openScriptDetail(s)"
        >{{ s.script_name }}</div>
        <div v-if="filteredScripts.length === 0" style="grid-column: 1/-1; text-align: center; color: #BFB5A8;">
          暂无数据
        </div>
      </div>
    </div>

    <!-- 剧本详情弹窗 -->
    <el-dialog v-model="detailVisible" :title="`剧本统计 - ${detailScript?.script_name || ''}`" width="500px" top="8vh">
      <template v-if="detailScript">
        <div class="detail-stats">
          <div class="detail-stat-card">
            <div class="ds-label">本月开本</div>
            <div class="ds-value">{{ detailData.this_month_count }} 场</div>
          </div>
          <div class="detail-stat-card">
            <div class="ds-label">今年开本</div>
            <div class="ds-value">{{ detailData.this_year_count }} 场</div>
          </div>
        </div>
        <div class="chart-title" style="margin-top: 16px;">近13个月开本趋势</div>
        <div ref="chartDetailTrend" class="chart-el" style="height: 240px;"></div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, watch, computed, nextTick, onUnmounted } from 'vue'
import { ArrowLeft, ArrowRight, DArrowLeft, DArrowRight } from '@element-plus/icons-vue'
import { get } from '../utils/request.js'
import { COLORS, baseOption, createChart, disposeChart } from '../utils/chart-theme.js'

const viewMode = ref('month')
const filterYear = ref(new Date().getFullYear())
const filterMonth = ref(new Date().getMonth() + 1)
const ranking = ref([])
const rankTypeFilter = ref('')
const blockSearch = ref('')
const blockTypeFilter = ref('')

const rankData = computed(() => {
  let list = (ranking.value || []).filter(r => r.count > 0)
  if (rankTypeFilter.value) list = list.filter(r => r.script_type === rankTypeFilter.value)
  return list
})

const rankChartHeight = computed(() => `${Math.max(rankData.value.length * 45, 120)}px`)

const filteredScripts = computed(() => {
  let list = ranking.value.filter(r => r.count > 0)
  if (blockTypeFilter.value) list = list.filter(r => r.script_type === blockTypeFilter.value)
  if (blockSearch.value) {
    const q = blockSearch.value.toLowerCase()
    list = list.filter(r => r.script_name.toLowerCase().includes(q))
  }
  return list
})

const chartTrend = ref(null)
const chartRank = ref(null)
const chartType = ref(null)
const chartCategory = ref(null)
const chartDetailTrend = ref(null)

let chartInstances = []

/* 详情弹窗 */
const detailVisible = ref(false)
const detailScript = ref(null)
const detailData = ref({ this_month_count: 0, this_year_count: 0, trend_13months: [] })

const labelText = computed(() => {
  if (viewMode.value === 'year') return `${filterYear.value}年`
  return `${filterYear.value}年${filterMonth.value}月`
})

onUnmounted(() => chartInstances.forEach(disposeChart))

async function fetchData() {
  const params = { year: filterYear.value }
  if (viewMode.value === 'month') params.month = filterMonth.value
  const res = await get('/api/stats/scripts', params)
  const data = res.data
  ranking.value = data.ranking || []

  await nextTick()
  chartInstances.forEach(disposeChart)
  chartInstances = []

  /* 按年时画月趋势 */
  if (viewMode.value === 'year') buildTrendChart(data)
  buildTypeChart(data)
  buildCategoryChart(data)
}

/* 月趋势折线 */
function buildTrendChart(data) {
  const c = createChart(chartTrend)
  if (!c) return
  const trend = data.monthly_trend || []
  c.setOption(baseOption({
    tooltip: { trigger: 'axis', formatter: p => `${p[0].axisValue}<br/>场次：<b>${p[0].value}</b>` },
    xAxis: { type: 'category', data: trend.map(r => r.month), axisLine: { lineStyle: { color: COLORS.grid } }, axisLabel: { fontSize: 11, color: COLORS.text } },
    yAxis: { type: 'value', splitLine: { lineStyle: { color: COLORS.grid, type: 'dashed' } } },
    series: [{
      type: 'line', smooth: true, symbol: 'circle', symbolSize: 6,
      data: trend.map(r => r.count),
      itemStyle: { color: COLORS.accent1 },
      lineStyle: { color: COLORS.accent1, width: 2 },
      areaStyle: { color: { type: 'linear', x: 0, y: 0, x2: 0, y2: 1,
        colorStops: [{ offset: 0, color: 'rgba(196,163,90,0.2)' }, { offset: 1, color: 'rgba(196,163,90,0.02)' }] } }
    }]
  }))
  chartInstances.push(c)
}

/* 排行横向柱状图 */
/* 剧本开本排行（watch 响应，自动 resize） */
watch(rankData, async (list) => {
  await nextTick()
  const c = createChart(chartRank)
  if (!c) return
  c.resize()
  const top = [...list].reverse()
  c.setOption(baseOption({
    tooltip: { trigger: 'axis', formatter: p => `<b>${p[0].name}</b><br/>开本 ${p[0].value} 次` },
    xAxis: { type: 'value', splitLine: { lineStyle: { color: COLORS.grid, type: 'dashed' } } },
    yAxis: { type: 'category', data: top.map(r => r.script_name), axisLabel: { fontSize: 11, color: COLORS.text }, axisLine: { lineStyle: { color: COLORS.grid } } },
    series: [{
      type: 'bar', barWidth: '60%', data: top.map(r => r.count),
      itemStyle: { color: COLORS.primary, borderRadius: [0, 4, 4, 0] }
    }]
  }), true)
  chartInstances = chartInstances.filter(ci => ci !== c)
  chartInstances.push(c)
})

/* 类型饼图 */
function buildTypeChart(data) {
  const c = createChart(chartType)
  if (!c) return
  const colors = [COLORS.primary, COLORS.accent1, COLORS.accent2, COLORS.accent3, COLORS.accent5]
  c.setOption(baseOption({
    tooltip: { trigger: 'item', formatter: '{b}: {c} 场 ({d}%)' },
    grid: null,
    series: [{
      type: 'pie', radius: ['45%', '72%'], center: ['50%', '52%'],
      data: (data.by_type || []).map(r => ({ name: r.type, value: r.count })),
      label: { color: COLORS.text, fontSize: 12, formatter: '{b}\n{d}%' },
      itemStyle: { borderColor: COLORS.bg, borderWidth: 2 },
      color: colors, emphasis: { scaleSize: 6 }
    }]
  }))
  chartInstances.push(c)
}

/* 种类饼图（盒装/城限） */
function buildCategoryChart(data) {
  const c = createChart(chartCategory)
  if (!c) return
  c.setOption(baseOption({
    tooltip: { trigger: 'item', formatter: '{b}: {c} 场 ({d}%)' },
    grid: null,
    series: [{
      type: 'pie', radius: ['45%', '72%'], center: ['50%', '52%'],
      data: (data.by_category || []).map(r => ({ name: r.category, value: r.count })),
      label: { color: COLORS.text, fontSize: 12, formatter: '{b}\n{d}%' },
      itemStyle: { borderColor: COLORS.bg, borderWidth: 2 },
      color: [COLORS.primary, COLORS.accent1], emphasis: { scaleSize: 6 }
    }]
  }))
  chartInstances.push(c)
}

/* 剧本详情弹窗 */
async function openScriptDetail(script) {
  detailScript.value = script
  detailVisible.value = true
  detailData.value = { this_month_count: 0, this_year_count: 0, trend_13months: [] }

  try {
    const res = await get(`/api/stats/scripts/${script.script_id}/detail`)
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
    tooltip: { trigger: 'axis', formatter: p => `${p[0].axisValue}<br/>开本：<b>${p[0].value}</b> 场` },
    xAxis: { type: 'category', data: trend.map(r => r.month), axisLine: { lineStyle: { color: COLORS.grid } }, axisLabel: { fontSize: 11, color: COLORS.text } },
    yAxis: { type: 'value', splitLine: { lineStyle: { color: COLORS.grid, type: 'dashed' } }, minInterval: 1 },
    series: [{
      type: 'line', smooth: true, symbol: 'circle', symbolSize: 6,
      data: trend.map(r => r.count),
      itemStyle: { color: COLORS.primary },
      lineStyle: { color: COLORS.primary, width: 2 },
      areaStyle: { color: { type: 'linear', x: 0, y: 0, x2: 0, y2: 1,
        colorStops: [{ offset: 0, color: 'rgba(139,115,85,0.2)' }, { offset: 1, color: 'rgba(139,115,85,0.02)' }] } }
    }]
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

function exportSummary() { window.open(`/api/stats/export/summary?type=scripts&year=${filterYear.value}${viewMode.value === 'month' ? '&month=' + filterMonth.value : ''}`) }
function exportDetail() { window.open(`/api/stats/export/detail?year=${filterYear.value}${viewMode.value === 'month' ? '&month=' + filterMonth.value : ''}`) }
</script>

<style scoped>
/* 筛选栏 */
.filter-bar { display: flex; gap: 12px; margin-bottom: 20px; align-items: center; flex-wrap: wrap; }
/* 点击切换按钮组 */
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
.chart-title-row { display: flex; align-items: center; justify-content: space-between; margin-bottom: 8px; }
.chart-title { font-family: "STFangsong","FangSong",serif; font-size: 14px; color: #5C4F3E; text-align: center; margin-bottom: 8px; }
.chart-el { width: 100%; }
.chart-trend { height: 400px; }
.chart-bar { height: 350px; }
.chart-pie { height: 260px; }

/* 饼图并排 */
.pie-row { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-bottom: 0; }
.pie-row .chart-box { margin-bottom: 16px; }

/* 剧本方块网格 */
.block-title-row { display: flex; align-items: center; justify-content: space-between; margin-bottom: 4px; }
.block-filters { display: flex; gap: 8px; align-items: center; }
.block-hint { text-align: center; font-size: 12px; color: #8C7B6B; margin-bottom: 12px; }
.block-grid { display: grid; grid-template-columns: repeat(5, 1fr); gap: 10px; }
.script-block {
  background: #F0EBE2; border: 1px solid #E0D7C8; border-radius: 4px;
  padding: 10px 6px; text-align: center; font-size: 13px; color: #3D3226;
  cursor: pointer; transition: background 0.2s, border-color 0.2s;
  overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
}
.script-block:hover { background: #EBE3D6; border-color: #8B7355; }

/* 详情弹窗 */
.detail-stats { display: flex; gap: 16px; justify-content: center; }
.detail-stat-card { flex: 1; background: #F0EBE2; border: 1px solid #E0D7C8; border-radius: 4px; padding: 12px; text-align: center; }
.ds-label { font-size: 12px; color: #8C7B6B; }
.ds-value { font-family: "SimSun","STSong","宋体",serif; font-size: 18px; color: #8B7355; margin-top: 4px; }
</style>
