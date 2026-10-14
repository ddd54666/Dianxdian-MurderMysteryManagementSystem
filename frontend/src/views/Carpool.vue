<!-- 拼车管理：列表、过期标注、增删改、图片生成 -->

<template>
  <div>
    <div style="display: flex; justify-content: space-between; align-items: center;">
      <h2 class="page-title">拼车管理</h2>
      <div style="display: flex; gap: 8px;">
        <el-button type="primary" @click="openCreate">新增拼车</el-button>
        <el-button @click="generateImage">生成图片</el-button>
      </div>
    </div>
    <hr class="divider-line" />

    <!-- 图片预览区 -->
    <div v-if="showPreview" ref="previewRef" class="preview-area">
      <h3 style="text-align: center; margin-bottom: 16px; font-family: STFangsong,FangSong,serif;">
        拼车信息 - {{ new Date().toLocaleDateString('zh-CN') }}
      </h3>
      <div class="carpool-grid">
        <div v-for="c in allCarpools" :key="c.id" class="carpool-preview-card" :class="{ expired: c.is_expired }">
          <div class="card-date">{{ c.carpool_date }}</div>
          <div class="card-script">{{ c.script_name }}</div>
          <div v-if="c.notes" class="card-notes">{{ c.notes }}</div>
          <div v-if="c.is_expired" class="card-expired-tag">已过期</div>
        </div>
      </div>
      <div style="text-align: center; margin-top: 20px;">
        <el-button type="primary" @click="downloadImage">下载图片</el-button>
        <el-button @click="showPreview = false">关闭预览</el-button>
      </div>
    </div>

    <!-- 列表表格 -->
    <el-table :data="carpools" stripe :header-cell-style="{ background: '#F0EBE2' }">
      <el-table-column prop="carpool_date" label="日期" width="120" />
      <el-table-column prop="script_name" label="剧本名称" min-width="160" />
      <el-table-column prop="notes" label="备注" min-width="180" />
      <el-table-column label="状态" width="100">
        <template #default="{ row }">
          <el-tag :type="row.is_expired ? 'danger' : 'success'" size="small">
            {{ row.is_expired ? '已过期' : '进行中' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="140">
        <template #default="{ row }">
          <el-button link type="primary" size="small" @click="openEdit(row)">编辑</el-button>
          <el-button link type="danger" size="small" @click="handleDelete(row.id)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-pagination v-if="total > pageSize" v-model:current-page="page" :page-size="pageSize" :total="total"
      layout="prev, pager, next" @current-change="fetchData" style="margin-top: 20px; justify-content: center;" />

    <!-- 新增/编辑弹窗 -->
    <el-dialog v-model="dialogVisible" :title="editingId ? '编辑拼车' : '新增拼车'" width="500px">
      <el-form label-width="80px">
        <el-form-item label="拼车日期">
          <el-date-picker v-model="form.carpool_date" type="date" value-format="YYYY-MM-DD" style="width: 100%;" />
        </el-form-item>
        <el-form-item label="剧本名称">
          <el-select v-model="form.script_id" filterable remote :remote-method="searchScripts" clearable style="width: 100%;" placeholder="搜索剧本">
            <el-option v-for="s in scriptOptions" :key="s.id" :label="s.name" :value="s.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="form.notes" placeholder="如 3=4 差1男" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSave" :loading="saving">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick } from 'vue'
import { ElMessageBox, ElMessage } from 'element-plus'
import { get, post, put, del } from '../utils/request.js'

const carpools = ref([])
const total = ref(0)
const page = ref(1)
const pageSize = 20

const dialogVisible = ref(false)
const editingId = ref(null)
const saving = ref(false)
const form = ref({ carpool_date: '', script_id: null, notes: '' })
const scriptOptions = ref([])

const showPreview = ref(false)
const previewRef = ref(null)
const allCarpools = ref([])

onMounted(() => fetchData())

async function fetchData() {
  const res = await get('/api/carpools', { page: page.value, page_size: pageSize })
  carpools.value = res.data
  total.value = res.total
}

async function searchScripts(q) {
  if (!q) { scriptOptions.value = []; return }
  const res = await get('/api/scripts/search', { q, limit: 10 })
  scriptOptions.value = res.data
}

function openCreate() {
  editingId.value = null
  form.value = { carpool_date: '', script_id: null, notes: '' }
  dialogVisible.value = true
}

function openEdit(row) {
  editingId.value = row.id
  form.value = { carpool_date: row.carpool_date, script_id: row.script_id, notes: row.notes }
  dialogVisible.value = true
}

async function handleSave() {
  if (!form.value.carpool_date || !form.value.script_id) { ElMessage.warning('日期和剧本不能为空'); return }
  saving.value = true
  try {
    if (editingId.value) { await put(`/api/carpools/${editingId.value}`, form.value); ElMessage.success('修改成功') }
    else { await post('/api/carpools', form.value); ElMessage.success('新增成功') }
    dialogVisible.value = false
    await fetchData()
  } finally { saving.value = false }
}

async function handleDelete(id) { await ElMessageBox.confirm('确定删除该拼车？', '提示', { type: 'warning' }); await del(`/api/carpools/${id}`); ElMessage.success('删除成功'); await fetchData() }

/* 生成图片 */
async function generateImage() {
  const res = await get('/api/carpools', { page: 1, page_size: 200 })
  allCarpools.value = res.data
  showPreview.value = true
  await nextTick()
}

async function downloadImage() {
  const html2canvas = (await import('html2canvas')).default
  const canvas = await html2canvas(previewRef.value, { scale: 2, backgroundColor: '#FAF6F0' })
  const link = document.createElement('a')
  link.download = `拼车信息_${new Date().toISOString().slice(0,10)}.png`
  link.href = canvas.toDataURL()
  link.click()
  ElMessage.success('图片已下载')
}
</script>

<style scoped>
.preview-area { padding: 24px; background: #FAF6F0; margin-bottom: 20px; border: 1px solid #E5DDD0; }
.carpool-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(180px, 1fr)); gap: 12px; }
.carpool-preview-card { background: #FDFBF7; border: 1px solid #E5DDD0; border-radius: 4px; padding: 12px; position: relative; }
.carpool-preview-card.expired { border-color: #C46B5A; }
.card-date { font-size: 12px; color: #8C7B6B; }
.card-script { font-family: STFangsong,FangSong,serif; font-size: 15px; color: #3D3226; margin-top: 4px; }
.card-notes { font-size: 13px; color: #5C4F3E; margin-top: 4px; }
.card-expired-tag { position: absolute; top: 4px; right: 4px; font-size: 10px; color: #C46B5A; }
</style>
