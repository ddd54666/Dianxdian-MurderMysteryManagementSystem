<!-- DM管理：列表、搜索、详情、新增/编辑弹窗 -->

<template>
  <div>
    <div style="display: flex; justify-content: space-between; align-items: center;">
      <h2 class="page-title">DM管理</h2>
      <el-button type="primary" @click="openCreate">新增DM</el-button>
    </div>
    <hr class="divider-line" />

    <!-- 搜索栏 -->
    <el-input v-model="search" placeholder="搜索DM姓名" clearable style="width: 200px; margin-bottom: 16px;" @change="fetchData" />

    <!-- 列表表格 -->
    <el-table :data="dms" stripe style="width: 100%;" :header-cell-style="{ background: '#F0EBE2' }">
      <el-table-column prop="name" label="姓名" width="120" />
      <el-table-column prop="notes" label="备注" />
      <el-table-column prop="session_count_this_month" label="本月开本次数" width="140" sortable />
      <el-table-column label="操作" width="220" fixed="right">
        <template #default="{ row }">
          <el-button link type="primary" size="small" @click="openDetail(row)">查看详情</el-button>
          <el-button link type="primary" size="small" @click="openEdit(row)">编辑</el-button>
          <el-button link type="danger" size="small" @click="handleDelete(row.id)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-pagination v-if="total > pageSize" v-model:current-page="page" :page-size="pageSize" :total="total"
      layout="prev, pager, next" @current-change="fetchData" style="margin-top: 20px; justify-content: center;" />

    <!-- 详情抽屉 -->
    <el-drawer v-model="drawerVisible" title="DM详情" size="600px">
      <template #header>
        <span style="font-family: STFangsong,FangSong,serif; font-size: 18px;">DM详情 - {{ detailDM.name }}</span>
      </template>
      <div style="margin-bottom: 16px; color: #5C4F3E;">
        <p><strong>姓名：</strong>{{ detailDM.name }}</p>
        <p><strong>备注：</strong>{{ detailDM.notes || '无' }}</p>
      </div>
      <el-table :data="dmSessions" stripe :header-cell-style="{ background: '#F0EBE2' }">
        <el-table-column prop="session_date" label="日期" width="120" />
        <el-table-column prop="script_name" label="剧本名称" min-width="160" />
        <el-table-column prop="dm_count" label="本场DM人数" width="110" />
        <el-table-column label="DM薪资(元)" width="120">
          <template #default="{ row }">
            <span class="money-font">{{ row.dm_salary > 0 ? toYuan(row.dm_salary) : '-' }}</span>
          </template>
        </el-table-column>
      </el-table>
      <el-pagination v-if="sessionTotal > pageSize" v-model:current-page="sessionPage" :page-size="pageSize"
        :total="sessionTotal" layout="prev, pager, next" @current-change="fetchDmSessions" style="margin-top: 16px;" />
    </el-drawer>

    <!-- 新增/编辑弹窗 -->
    <el-dialog v-model="dialogVisible" :title="editingId ? '编辑DM' : '新增DM'" width="400px">
      <el-form label-width="60px">
        <el-form-item label="姓名"><el-input v-model="form.name" /></el-form-item>
        <el-form-item label="备注"><el-input v-model="form.notes" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSave" :loading="saving">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessageBox, ElMessage } from 'element-plus'
import { get, post, put, del } from '../utils/request.js'
import { toYuan } from '../utils/money.js'

const dms = ref([])
const total = ref(0)
const page = ref(1)
const pageSize = 20
const search = ref('')

const dialogVisible = ref(false)
const editingId = ref(null)
const saving = ref(false)
const form = ref({ name: '', notes: '' })

const drawerVisible = ref(false)
const detailDM = ref({})
const dmSessions = ref([])
const sessionTotal = ref(0)
const sessionPage = ref(1)

onMounted(() => fetchData())

async function fetchData() {
  const res = await get('/api/dms', { search: search.value, page: page.value, page_size: pageSize })
  dms.value = res.data
  total.value = res.total
}

function openCreate() { editingId.value = null; form.value = { name: '', notes: '' }; dialogVisible.value = true }
function openEdit(row) { editingId.value = row.id; form.value = { name: row.name, notes: row.notes }; dialogVisible.value = true }

async function handleSave() {
  if (!form.value.name.trim()) { ElMessage.warning('请输入DM姓名'); return }
  saving.value = true
  try {
    if (editingId.value) { await put(`/api/dms/${editingId.value}`, form.value); ElMessage.success('修改成功') }
    else { await post('/api/dms', form.value); ElMessage.success('新增成功') }
    dialogVisible.value = false
    await fetchData()
  } finally { saving.value = false }
}

async function handleDelete(id) { await ElMessageBox.confirm('确定删除该DM？', '提示', { type: 'warning' }); await del(`/api/dms/${id}`); ElMessage.success('删除成功'); await fetchData() }

async function openDetail(row) {
  detailDM.value = row
  sessionPage.value = 1
  drawerVisible.value = true
  await fetchDmSessions()
}

async function fetchDmSessions() {
  const res = await get(`/api/dms/${detailDM.value.id}/sessions`, { page: sessionPage.value, page_size: pageSize })
  dmSessions.value = res.data
  sessionTotal.value = res.total
}
</script>
