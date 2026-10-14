<!-- 营业额统计：总览卡片、复合趋势图、饼图、剧本排行、CSV导出 -->
<template>
  <div>
    <h2 class="page-title">营业额统计</h2>
    <hr class="divider-line" />

    <template v-if="!unlocked">
      <div style="text-align: center; padding: 60px 0;">
        <p style="color: #8C7B6B; margin-bottom: 16px;">此页面需要二级密码</p>
        <el-button type="primary" @click="showPwd = true">输入密码</el-button>
      </div>
      <PasswordDialog v-model:visible="showPwd" @unlocked="unlocked = true" />
    </template>

    <template v-else>
      <!-- 总览卡片 -->
      <div class="overview-row">
        <div class="overview-card card-today">
          <div class="ov-label">今日</div>
          <div class="ov-value">{{ toYuan(overview.today.revenue) }}</div>
          <div class="ov-sub">{{ overview.today.session_count }} 场</div>
        </div>
        <div class="overview-card card-week">
          <div class="ov-label">本周</div>
          <div class="ov-value">{{ toYuan(overview.this_week.revenue) }}</div>
          <div class="ov-sub">{{ overview.this_week.session_count }} 场</div>
        </div>
        <div class="overview-card card-month">
          <div class="ov-label">本月</div>
          <div class="ov-value">{{ toYuan(overview.this_month.revenue) }}</div>
          <div class="ov-sub">{{ overview.this_month.session_count }} 场</div>
        </div>
        <div class="overview-card card-year">
          <div class="ov-label">本年度</div>
          <div class="ov-value">{{ toYuan(overview.this_year.revenue) }}</div>
          <div class="ov-sub">{{ overview.this_year.session_count }} 场</div>
        </div>
      </div>

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

      <!-- 趋势图（全宽） -->
      <div class="chart-box"><div class="chart-title">{{ viewMode === 'year' ? '营业额每月汇总' : '营业额每日汇总' }}</div><div ref="chartTrend" class="chart-el chart-trend"></div></div>

      <!-- 按年：年度对比柱状图 -->
      <div v-if="viewMode === 'year'" class="chart-box"><div class="chart-title">年度对比</div><div ref="chartYear" class="chart-el chart-bar"></div></div>

      <!-- 饼图并排 -->
      <div class="pie-row">
        <div class="chart-box"><div class="chart-title">按剧本类型</div><div ref="chartType" class="chart-el chart-pie"></div></div>
        <div class="chart-box"><div class="chart-title">按盒装/城限</div><div ref="chartCategory" class="chart-el chart-pie"></div></div>
      </div>

      <!-- 剧本营业额排行柱状图 -->
      <div class="chart-box">
        <div class="chart-title-row">
          <span class="chart-title" style="margin-bottom:0;">剧本营业额排行</span>
          <el-select v-model="revenueRankTypeFilter" placeholder="全部类型" clearable size="small" style="width:100px;">
            <el-option v-for="t in ['欢乐','推理','恐怖','情感','机制']" :key="t" :label="t" :value="t" />
          </el-select>
        </div>
        <div ref="chartScriptRank" class="chart-el" :style="{ height: rankChartHeight }"></div>
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref, watch, computed, nextTick, onUnmounted } from 'vue'
import { ArrowLeft, ArrowRight, DArrowLeft, DArrowRight } from '@element-plus/icons-vue'
import { get } from '../utils/request.js'
import { toYuan } from '../utils/money.js'
import { isUnlocked } from '../utils/password.js'
import PasswordDialog from '../components/PasswordDialog.vue'
import { COLORS, baseOption, createChart, disposeChart } from '../utils/chart-theme.js'

const unlocked = ref(isUnlocked())
const showPwd = ref(false)

const viewMode = ref('month')
const filterYear = ref(new Date().getFullYear())
const filterMonth = ref(new Date().getMonth() + 1)
const overview = ref({
  today: { revenue: 0, session_count: 0 },
  this_week: { revenue: 0, session_count: 0 },
  this_month: { revenue: 0, session_count: 0 },
  this_year: { revenue: 0, session_count: 0 }
})

const chartTrend = ref(null)
const chartYear = ref(null)
const chartType = ref(null)
const chartCategory = ref(null)
const chartScriptRank = ref(null)
const revenueRankTypeFilter = ref('')
const _allRevenueData = ref(null)

const rankData = computed(() => {
  if (!_allRevenueData.value) return []
  let list = _allRevenueData.value.by_script || []
  if (revenueRankTypeFilter.value) list = list.filter(r => r.script_type === revenueRankTypeFilter.value)
  return list
})

const rankChartHeight = computed(() => `${Math.max(rankData.value.length * 45, 120)}px`)

let chartInstances = []

const labelText = computed(() => {
  if (viewMode.value === 'year') return `${filterYear.value}年`
  return `${filterYear.value}年${filterMonth.value}月`
})

onUnmounted(() => chartInstances.forEach(disposeChart))

async function fetchOverview() {
  try {
    const res = await get('/api/stats/revenue/overview')
    overview.value = res.data
  } catch { /* 静默失败 */ }
}

async function fetchData() {
  const params = { year: filterYear.value }
  if (viewMode.value === 'month') params.month = filterMonth.value
  const res = await get('/api/stats/revenue', params)
  _allRevenueData.value = res.data

  await nextTick()
  chartInstances.forEach(disposeChart)
  chartInstances = []

  buildTrendChart(res.data)
  if (viewMode.value === 'year') buildYearChart(res.data)
  buildTypeChart(res.data)
  buildCategoryChart(res.data)
}

/* 复合趋势：柱状=营业额，折线=场次 */
function buildTrendChart(data) {
  const c = createChart(chartTrend)
  if (!c) return
  const isYear = viewMode.value === 'year'
  const source = isYear ? data.monthly_trend : data.daily_trend
  const labels = source.map(r => isYear ? r.month : r.date)
  const counts = source.map(r => r.session_count)
  const totals = source.map(r => r.revenue / 100)

  c.setOption(baseOption({
    tooltip: { trigger: 'axis', formatter: p => {
      const bar = p.find(q => q.seriesName === '营业额')
      const line = p.find(q => q.seriesName === '场次')
      return `${p[0].axisValue}<br/>营业额：<b>${(bar?.value ?? 0).toFixed(0)}</b> 元<br/>场次：<b>${line?.value ?? 0}</b> 场`
    }},
    legend: { bottom: 0, textStyle: { fontSize: 12, color: COLORS.textDim }, data: ['营业额', '场次'] },
    xAxis: { type: 'category', data: labels, axisLine: { lineStyle: { color: COLORS.grid } }, axisLabel: { fontSize: 11, color: COLORS.text } },
    yAxis: [
      { type: 'value', name: '元', nameTextStyle: { fontSize: 11, color: COLORS.textDim }, splitLine: { lineStyle: { color: COLORS.grid, type: 'dashed' } } },
      { type: 'value', name: '场', nameTextStyle: { fontSize: 11, color: COLORS.textDim }, splitLine: { show: false }, minInterval: 1 }
    ],
    series: [
      { name: '营业额', type: 'bar', barWidth: isYear ? '40%' : '60%', data: totals, itemStyle: { color: COLORS.primaryLight, borderRadius: [4, 4, 0, 0] } },
      { name: '场次', type: 'line', yAxisIndex: 1, smooth: true, symbol: 'circle', symbolSize: 6, data: counts, itemStyle: { color: COLORS.accent1 }, lineStyle: { color: COLORS.accent1, width: 2 } }
    ]
  }))
  chartInstances.push(c)
}

/* 年度对比柱状图 */
function buildYearChart(data) {
  const c = createChart(chartYear)
  if (!c) return
  c.setOption(baseOption({
    tooltip: { trigger: 'axis', formatter: p => `${p[0].axisValue}年<br/>营业额：<b>${(p[0].value).toFixed(0)}</b> 元` },
    xAxis: { type: 'category', data: data.yearly_comparison.map(r => r.year), axisLine: { lineStyle: { color: COLORS.grid } } },
    yAxis: { type: 'value', splitLine: { lineStyle: { color: COLORS.grid, type: 'dashed' } } },
    series: [{
      type: 'bar', barWidth: '50%', data: data.yearly_comparison.map(r => r.revenue / 100),
      itemStyle: { color: COLORS.primary, borderRadius: [4, 4, 0, 0] }
    }]
  }))
  chartInstances.push(c)
}

/* 类型饼图 */
function buildTypeChart(data) {
  const c = createChart(chartType)
  if (!c) return
  const colors = [COLORS.primary, COLORS.accent1, COLORS.accent2, COLORS.accent3, COLORS.accent5]
  c.setOption(baseOption({
    tooltip: { trigger: 'item', formatter: '{b}: {c} 元 ({d}%)' },
    grid: null,
    series: [{
      type: 'pie', radius: ['45%', '72%'], center: ['50%', '52%'],
      data: data.by_type.map(r => ({ name: r.type, value: Math.round(r.revenue / 100) })),
      label: { color: COLORS.text, fontSize: 12, formatter: '{b}\n{d}%' },
      itemStyle: { borderColor: COLORS.bg, borderWidth: 2 },
      color: colors, emphasis: { scaleSize: 6 }
    }]
  }))
  chartInstances.push(c)
}

/* 种类饼图 */
function buildCategoryChart(data) {
  const c = createChart(chartCategory)
  if (!c) return
  c.setOption(baseOption({
    tooltip: { trigger: 'item', formatter: '{b}: {c} 元 ({d}%)' },
    grid: null,
    series: [{
      type: 'pie', radius: ['45%', '72%'], center: ['50%', '52%'],
      data: data.by_category.map(r => ({ name: r.category, value: (r.revenue / 100).toFixed(0) })),
      label: { color: COLORS.text, fontSize: 12, formatter: '{b}\n{d}%' },
      itemStyle: { borderColor: COLORS.bg, borderWidth: 2 },
      color: [COLORS.primary, COLORS.accent1], emphasis: { scaleSize: 6 }
    }]
  }))
  chartInstances.push(c)
}

/* 剧本营业额排行（watch 响应，自动 resize） */
watch(rankData, async (list) => {
  await nextTick()
  const c = createChart(chartScriptRank)
  if (!c) return
  c.resize()
  const top = [...list].reverse()
  c.setOption(baseOption({
    tooltip: { trigger: 'axis', formatter: p => `<b>${p[0].name}</b><br/>营业额：<b>${Number(p[0].value).toFixed(0)}</b> 元` },
    xAxis: { type: 'value', axisLabel: { formatter: v => v.toFixed(0) }, splitLine: { lineStyle: { color: COLORS.grid, type: 'dashed' } } },
    yAxis: { type: 'category', data: top.map(r => r.script_name), axisLabel: { fontSize: 11, color: COLORS.text }, axisLine: { lineStyle: { color: COLORS.grid } } },
    series: [{
      type: 'bar', barWidth: '60%', data: top.map(r => r.revenue / 100),
      itemStyle: { color: COLORS.primary, borderRadius: [0, 4, 4, 0] }
    }]
  }))
  // 替换旧实例，避免 chartInstances 堆积
  chartInstances = chartInstances.filter(ci => ci !== c)
  chartInstances.push(c)
})

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

watch(unlocked, (val) => { if (val) { fetchOverview(); fetchData() } })
if (unlocked.value) { fetchOverview(); fetchData() }

function exportSummary() { window.open(`/api/stats/export/summary?type=revenue&year=${filterYear.value}${viewMode.value === 'month' ? '&month=' + filterMonth.value : ''}`) }
function exportDetail() { window.open(`/api/stats/export/detail?year=${filterYear.value}${viewMode.value === 'month' ? '&month=' + filterMonth.value : ''}`) }
</script>

<style scoped>
/* 总览卡片 */
.overview-row { display: flex; gap: 16px; margin-bottom: 20px; }
.overview-card {
  flex: 1; background: #FDFBF7; border: 1px solid #E5DDD0; border-radius: 4px;
  padding: 14px 16px; text-align: center; position: relative; overflow: hidden;
}
/* 各卡片顶部色条 */
.overview-card::before {
  content: ''; position: absolute; top: 0; left: 0; right: 0; height: 3px;
}
.card-today::before  { background: #C4A35A; }  /* 金麦——今日 */
.card-week::before  { background: #8B7355; }  /* 茶棕——本周 */
.card-month::before { background: #6B8E6B; }  /* 青灰——本月 */
.card-year::before  { background: #7B8EA3; }  /* 雾蓝——本年度 */
.ov-label { font-size: 12px; color: #8C7B6B; margin-bottom: 4px; }
.ov-value { font-family: "SimSun","STSong","宋体",serif; font-size: 20px; color: #8B7355; font-weight: normal; }
.ov-sub { font-size: 12px; color: #BFB5A8; margin-top: 2px; }

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
</style>
