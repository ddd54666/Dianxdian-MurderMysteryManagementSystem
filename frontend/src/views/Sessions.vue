<!-- 场次管理：核心模块，含自动补全、嵌套新增、动态DM选择器、金额联动计算 -->

<template>
  <div>
    <div style="display: flex; justify-content: space-between; align-items: center;">
      <h2 class="page-title">场次管理</h2>
      <el-button type="primary" @click="openCreate">新增场次</el-button>
    </div>
    <hr class="divider-line" />

    <!-- 筛选栏 -->
    <div style="display: flex; gap: 12px; margin-bottom: 16px; flex-wrap: wrap; align-items: center;">
      <el-select v-model="filterYear" style="width: 80px;" @change="fetchData">
        <el-option v-for="y in yearOptions" :key="y" :label="y" :value="y" />
      </el-select>
      <span>年</span>
      <el-select v-model="filterMonth" style="width: 70px;" @change="fetchData">
        <el-option :value="null" label="全部" />
        <el-option v-for="m in 12" :key="m" :label="m" :value="m" />
      </el-select>
      <span>月</span>
      <el-select v-model="filterType" placeholder="类型" clearable style="width: 100px;" @change="fetchData">
        <el-option v-for="t in types" :key="t" :label="t" :value="t" />
      </el-select>
      <el-select v-model="filterDmId" placeholder="DM" clearable filterable remote :remote-method="searchDms" style="width: 140px;" @change="fetchData">
        <el-option v-for="d in dmOptions" :key="d.id" :label="d.name" :value="d.id" />
      </el-select>
    </div>

    <!-- 列表表格：同日期合并单元格，背景按日交替，日期旁显示当日场次数徽标 -->
    <el-table :data="sessions" :row-class-name="rowClassName" :span-method="spanMethod" :header-cell-style="{ background: '#F0EBE2' }" style="font-size: 14px;">
      <el-table-column label="日期" width="110">
        <template #default="{ row }">
          <span class="date-text">{{ row.session_date.slice(5) }}</span>
          <span class="day-badge">{{ countOf(row.session_date) }}场</span>
        </template>
      </el-table-column>
      <el-table-column prop="script_name" label="剧本" min-width="140" />
      <el-table-column prop="script_type" label="类型" width="70" />
      <el-table-column prop="script_category" label="种类" width="70" />
      <el-table-column label="DM" min-width="120">
        <template #default="{ row }">{{ row.dms?.map(d => d.name).join('、') || '-' }}</template>
      </el-table-column>
      <el-table-column prop="player_count" label="人数" width="60" />
      <el-table-column label="单价(元)" width="90">
        <template #default="{ row }"><span class="money-font">{{ toYuan(row.unit_price) }}</span></template>
      </el-table-column>
      <el-table-column label="营业额(元)" width="110">
        <template #default="{ row }"><span class="money-font">{{ toYuan(row.revenue) }}</span></template>
      </el-table-column>
      <el-table-column label="薪资(元)" width="90">
        <template #default="{ row }"><span class="money-font">{{ row.dm_salary > 0 ? toYuan(row.dm_salary) : '-' }}</span></template>
      </el-table-column>
      <el-table-column prop="notes" label="备注" min-width="100" />
      <el-table-column label="操作" width="140" fixed="right">
        <template #default="{ row }">
          <el-button link type="primary" size="small" @click="openEdit(row)">编辑</el-button>
          <el-button link type="danger" size="small" @click="handleDelete(row.id)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-pagination v-if="total > pageSize" v-model:current-page="page" :page-size="pageSize" :total="total"
      layout="prev, pager, next" @current-change="fetchData" style="margin-top: 20px; justify-content: center;" />

    <!-- 新增/编辑场次弹窗 -->
    <el-dialog v-model="dialogVisible" :title="editingId ? '编辑场次' : '新增场次'" width="900px" top="5vh" @close="resetForm">
      <div class="session-form-grid">
        <!-- 左列 -->
        <div>
          <div class="form-group">
            <label>剧本名称 <span class="required">*</span></label>
            <div style="display: flex; gap: 4px;">
              <el-select v-model="form.script_id" filterable remote :remote-method="searchScripts" clearable style="flex:1;" placeholder="搜索剧本" @change="onScriptSelected">
                <el-option v-for="s in scriptOptions" :key="s.id" :label="s.name" :value="s.id" />
              </el-select>
              <el-button @click="openQuickScript" :icon="Plus">新增</el-button>
            </div>
          </div>
          <div class="form-group">
            <label>剧本类型</label>
            <el-input :value="form.script_type" disabled />
          </div>
          <div class="form-group">
            <label>剧本种类</label>
            <el-input :value="form.script_category" disabled />
          </div>
          <div class="form-group">
            <label>DM人数 <span class="required">*</span></label>
            <el-input-number v-model="form.dm_count" :min="1" :max="6" @change="onDmCountChange" />
          </div>
          <div class="form-group" v-for="(_, idx) in form.dm_count" :key="'dm'+idx">
            <label>DM名-{{ idx + 1 }} <span class="required">*</span></label>
            <div style="display: flex; gap: 6px;">
              <el-select v-model="form.dm_ids[idx]" filterable remote :remote-method="(q) => searchDms(q)" clearable style="flex: 3;" placeholder="搜索DM">
                <el-option v-for="d in dmOptions" :key="d.id" :label="d.name" :value="d.id" />
              </el-select>
              <el-input v-model="form.dm_salaries[idx]" placeholder="薪资" style="flex: 1; min-width: 100px;" @input="v => form.dm_salaries[idx] = v.replace(/[^0-9]/g, '')">
                <template #append>元</template>
              </el-input>
              <el-button @click="openQuickDM" :icon="Plus" style="flex-shrink: 0;">新增</el-button>
            </div>
          </div>
        </div>
        <!-- 右列 -->
        <div>
          <div class="form-group">
            <label>剧本单价(元) <span class="required">*</span></label>
            <el-input v-model="form.unitPriceYuan" @input="recalcRevenue" placeholder="单价" />
          </div>
          <div class="form-group">
            <label>剧本人数 <span class="required">*</span></label>
            <el-input-number v-model="form.player_count" :min="1" :disabled="form.player_fixed" @change="recalcRevenue" />
          </div>
          <div class="form-group">
            <label>开本日期 <span class="required">*</span></label>
            <el-date-picker v-model="form.session_date" type="date" value-format="YYYY-MM-DD" style="width: 100%;" />
          </div>
          <div class="form-group">
            <label>场次营业额(元) <span class="required">*</span></label>
            <el-input v-model="form.revenueYuan" @input="onRevenueManual" placeholder="自动计算=单价×人数" />
          </div>
          <div class="form-group">
            <label>备注</label>
            <el-input v-model="form.notes" placeholder="自由文本" />
          </div>
        </div>
      </div>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSave" :loading="saving">确定</el-button>
      </template>
    </el-dialog>

    <!-- 嵌套：快速新增剧本 -->
    <el-dialog v-model="quickScriptVisible" title="新增剧本" width="400px" append-to-body>
      <el-form label-width="80px">
        <el-form-item label="名称"><el-input v-model="quickScriptForm.name" /></el-form-item>
        <el-form-item label="类型"><el-select v-model="quickScriptForm.type" style="width:100%;"><el-option v-for="t in types" :key="t" :label="t" :value="t" /></el-select></el-form-item>
        <el-form-item label="种类"><el-select v-model="quickScriptForm.category" style="width:100%;"><el-option v-for="c in ['盒装','城限']" :key="c" :label="c" :value="c" /></el-select></el-form-item>
        <el-form-item label="单价(元)"><el-input v-model="quickScriptForm.priceYuan" /></el-form-item>
        <el-form-item label="人数固定"><el-switch v-model="quickScriptForm.is_fixed" /></el-form-item>
        <el-form-item label="人数"><el-input-number v-model="quickScriptForm.player_count" :min="1" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="quickScriptVisible = false">取消</el-button>
        <el-button type="primary" @click="doQuickScript" :loading="quickSaving">确定</el-button>
      </template>
    </el-dialog>

    <!-- 嵌套：快速新增DM -->
    <el-dialog v-model="quickDMVisible" title="新增DM" width="350px" append-to-body>
      <el-form label-width="60px">
        <el-form-item label="姓名"><el-input v-model="quickDMForm.name" /></el-form-item>
        <el-form-item label="备注"><el-input v-model="quickDMForm.notes" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="quickDMVisible = false">取消</el-button>
        <el-button type="primary" @click="doQuickDM" :loading="quickSaving">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, nextTick } from 'vue'
import { ElMessageBox, ElMessage } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import { get, post, put, del } from '../utils/request.js'
import { toYuan, toFen } from '../utils/money.js'

const types = ['欢乐', '推理', '恐怖', '情感', '机制']

/* 日期分组：后端按日期倒序返回，同一天连续排列，按页内数据计算各日期的行区间 */
const dateGroups = computed(() => {
  const groups = []
  let start = 0
  for (let i = 1; i <= sessions.value.length; i++) {
    if (i === sessions.value.length || sessions.value[i].session_date !== sessions.value[start].session_date) {
      groups.push({ date: sessions.value[start].session_date, start, count: i - start })
      start = i
    }
  }
  return groups
})

/* 合并日期列：组首行向下跨 count 行，其余行隐藏 */
function spanMethod({ rowIndex, columnIndex }) {
  if (columnIndex !== 0) return
  const g = dateGroups.value.find(g => rowIndex >= g.start && rowIndex < g.start + g.count)
  if (!g) return
  return rowIndex === g.start ? { rowspan: g.count, colspan: 1 } : { rowspan: 0, colspan: 0 }
}

/* 行背景按日交替，组内同色 */
function rowClassName({ row }) {
  const idx = dateGroups.value.findIndex(g => g.date === row.session_date)
  return idx % 2 === 0 ? 'date-group-a' : 'date-group-b'
}

/* 当日场次数 */
function countOf(date) {
  const g = dateGroups.value.find(g => g.date === date)
  return g ? g.count : 1
}

const sessions = ref([])
const total = ref(0)
const page = ref(1)
const pageSize = 20
const filterYear = ref(new Date().getFullYear())
const filterMonth = ref(new Date().getMonth() + 1)
const filterType = ref('')
const filterDmId = ref(null)
const dmOptions = ref([])
const scriptOptions = ref([])
const yearOptions = Array.from({ length: 10 }, (_, i) => new Date().getFullYear() - 5 + i)

const dialogVisible = ref(false)
const editingId = ref(null)
const saving = ref(false)
const revenueManual = ref(false)

/* 表单数据 */
function defaultForm() {
  return {
    script_id: null, script_type: '', script_category: '',
    dm_count: 1, dm_ids: [null], dm_salaries: [''],
    unitPriceYuan: '', player_count: 6, player_fixed: false,
    session_date: new Date().toISOString().slice(0, 10),
    revenueYuan: '', notes: ''
  }
}
const form = ref(defaultForm())

/* 快速新增剧本 */
const quickScriptVisible = ref(false)
const quickSaving = ref(false)
const quickScriptForm = ref({ name: '', type: '推理', category: '盒装', priceYuan: '', is_fixed: true, player_count: 6 })

/* 快速新增DM */
const quickDMVisible = ref(false)
const quickDMForm = ref({ name: '', notes: '' })

onMounted(() => fetchData())

async function fetchData() {
  const res = await get('/api/sessions', {
    year: filterYear.value, month: filterMonth.value,
    type: filterType.value, dm_id: filterDmId.value,
    page: page.value, page_size: pageSize
  })
  sessions.value = res.data
  total.value = res.total
}

async function searchScripts(q) {
  if (!q) { scriptOptions.value = []; return }
  const res = await get('/api/scripts/search', { q, limit: 10 })
  scriptOptions.value = res.data
}

async function searchDms(q) {
  if (!q) { dmOptions.value = []; return }
  const res = await get('/api/dms/search', { q, limit: 10 })
  dmOptions.value = res.data
}

function onScriptSelected(scriptId) {
  if (!scriptId) return
  const script = scriptOptions.value.find(s => s.id === scriptId)
  if (!script) return
  form.value.script_type = script.type
  form.value.script_category = script.category
  form.value.unitPriceYuan = toYuan(script.unit_price)
  form.value.player_fixed = script.is_player_count_fixed
  if (script.is_player_count_fixed) form.value.player_count = script.player_count
  /* 默认DM薪资 = 剧本单价 */
  const priceYuan = toYuan(script.unit_price)
  if (form.value.dm_count === 1) form.value.dm_salaries[0] = parseInt(priceYuan)
  recalcRevenue()
}

function onDmCountChange(val) {
  /* 调整 dm_ids 和 dm_salaries 数组长度 */
  while (form.value.dm_ids.length < val) { form.value.dm_ids.push(null); form.value.dm_salaries.push('') }
  while (form.value.dm_ids.length > val) { form.value.dm_ids.pop(); form.value.dm_salaries.pop() }
}

function recalcRevenue() {
  if (revenueManual.value) return
  const price = parseFloat(form.value.unitPriceYuan) || 0
  const count = form.value.player_count || 0
  form.value.revenueYuan = (price * count).toFixed(2)
}

function onRevenueManual() { revenueManual.value = true }

function openCreate() {
  editingId.value = null
  form.value = defaultForm()
  revenueManual.value = false
  dialogVisible.value = true
}

function openEdit(row) {
  editingId.value = row.id
  form.value = {
    script_id: row.script_id,
    script_type: row.script_type,
    script_category: row.script_category,
    dm_count: row.dm_count,
    dm_ids: row.dms?.map(d => d.id) || [],
    dm_salaries: row.dms?.map(d => parseInt(toYuan(d.dm_salary || 0))) || [],
    unitPriceYuan: toYuan(row.unit_price),
    player_count: row.player_count,
    player_fixed: false,
    session_date: row.session_date,
    revenueYuan: toYuan(row.revenue),
    notes: row.notes || ''
  }
  revenueManual.value = true
  dialogVisible.value = true
}

function resetForm() { revenueManual.value = false }

async function handleSave() {
  if (!form.value.script_id) { ElMessage.warning('请选择剧本'); return }
  if (form.value.dm_ids.some(id => !id)) { ElMessage.warning('请填写所有DM'); return }
  if (!form.value.session_date) { ElMessage.warning('请选择日期'); return }
  saving.value = true
  const data = {
    script_id: form.value.script_id,
    dm_count: form.value.dm_count,
    dm_ids: form.value.dm_ids.filter(Boolean),
    dm_salaries: form.value.dm_salaries.map(s => toFen(s || 0)),
    unit_price: toFen(form.value.unitPriceYuan),
    player_count: form.value.player_count,
    session_date: form.value.session_date,
    revenue: toFen(form.value.revenueYuan),
    notes: form.value.notes
  }
  try {
    if (editingId.value) { await put(`/api/sessions/${editingId.value}`, data); ElMessage.success('修改成功') }
    else { await post('/api/sessions', data); ElMessage.success('新增成功') }
    dialogVisible.value = false
    await fetchData()
  } finally { saving.value = false }
}

async function handleDelete(id) {
  await ElMessageBox.confirm('确定删除该场次记录？删除后不可恢复。', '提示', { type: 'warning' })
  await del(`/api/sessions/${id}`)
  ElMessage.success('删除成功')
  await fetchData()
}

/* 快速新增剧本 */
function openQuickScript() { quickScriptForm.value = { name: '', type: '推理', category: '盒装', priceYuan: '', is_fixed: true, player_count: 6 }; quickScriptVisible.value = true }

async function doQuickScript() {
  if (!quickScriptForm.value.name) { ElMessage.warning('请输入剧本名称'); return }
  quickSaving.value = true
  try {
    await post('/api/scripts', {
      name: quickScriptForm.value.name, type: quickScriptForm.value.type, category: quickScriptForm.value.category,
      unit_price: toFen(quickScriptForm.value.priceYuan), is_player_count_fixed: quickScriptForm.value.is_fixed,
      player_count: quickScriptForm.value.player_count
    })
    ElMessage.success('剧本新增成功')
    quickScriptVisible.value = false
    /* 重新搜索并选中新剧本 */
    await searchScripts(quickScriptForm.value.name)
    await nextTick()
    if (scriptOptions.value.length > 0) {
      const s = scriptOptions.value[0]
      form.value.script_id = s.id
      onScriptSelected(s.id)
    }
  } finally { quickSaving.value = false }
}

/* 快速新增DM */
function openQuickDM() { quickDMForm.value = { name: '', notes: '' }; quickDMVisible.value = true }

async function doQuickDM() {
  if (!quickDMForm.value.name) { ElMessage.warning('请输入DM姓名'); return }
  quickSaving.value = true
  try {
    const res = await post('/api/dms', quickDMForm.value)
    ElMessage.success('DM新增成功')
    quickDMVisible.value = false
    /* 加入 dmOptions 并选中到第一个空位 */
    dmOptions.value.unshift({ id: res.data.id, name: quickDMForm.value.name })
    const emptyIdx = form.value.dm_ids.findIndex(id => !id)
    if (emptyIdx >= 0) form.value.dm_ids[emptyIdx] = res.data.id
  } finally { quickSaving.value = false }
}
</script>

<style scoped>
.session-form-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 0 24px; }
.form-group { margin-bottom: 14px; }
.form-group label { display: block; font-size: 13px; color: #5C4F3E; margin-bottom: 4px; }
.required { color: #C46B5A; }

/* 日期组背景交替：两种接近白色的浅色，色差柔和 */
.date-group-a td.el-table__cell { background-color: #FDFBF7; }
.date-group-b td.el-table__cell { background-color: #F6F1E7; }
.date-group-a:hover td.el-table__cell { background-color: #F2EDE3; }
.date-group-b:hover td.el-table__cell { background-color: #EFE9DD; }

/* 日期文字与场次徽标 */
.date-text { font-weight: 600; }
.day-badge {
  display: inline-block;
  background: #8B7355;
  color: #fff;
  border-radius: 3px;
  font-size: 11px;
  line-height: 1;
  padding: 3px 5px;
  margin-left: 6px;
}
</style>
