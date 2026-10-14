<!-- 剧本管理：列表、搜索筛选、新增/编辑弹窗 -->

<template>
  <div>
    <div style="display: flex; justify-content: space-between; align-items: center;">
      <h2 class="page-title">剧本管理</h2>
      <el-button type="primary" @click="openCreate">新增剧本</el-button>
    </div>
    <hr class="divider-line" />

    <!-- 搜索筛选 -->
    <div style="display: flex; gap: 12px; margin-bottom: 16px;">
      <el-input v-model="search" placeholder="搜索剧本名称" clearable style="width: 200px;" @change="fetchData" />
      <el-select v-model="filterType" placeholder="类型" clearable style="width: 120px;" @change="fetchData">
        <el-option v-for="t in types" :key="t" :label="t" :value="t" />
      </el-select>
      <el-select v-model="filterCategory" placeholder="种类" clearable style="width: 120px;" @change="fetchData">
        <el-option v-for="c in categories" :key="c" :label="c" :value="c" />
      </el-select>
    </div>

    <!-- 列表表格 -->
    <el-table :data="scripts" stripe :header-cell-style="{ background: '#F0EBE2' }">
      <el-table-column prop="name" label="名称" min-width="160" />
      <el-table-column prop="type" label="类型" width="80" />
      <el-table-column prop="category" label="种类" width="80" />
      <el-table-column label="单价(元)" width="100">
        <template #default="{ row }"><span class="money-font">{{ toYuan(row.unit_price) }}</span></template>
      </el-table-column>
      <el-table-column prop="player_count" label="人数" width="70" />
      <el-table-column label="固定" width="70">
        <template #default="{ row }">{{ row.is_player_count_fixed ? '是' : '否' }}</template>
      </el-table-column>
      <el-table-column label="操作" width="140">
        <template #default="{ row }">
          <el-button link type="primary" size="small" @click="openEdit(row)">编辑</el-button>
          <el-tooltip content="有关联场次，无法删除" :disabled="!row.hasSession" placement="top">
            <el-button link type="danger" size="small" :disabled="row.hasSession" @click="handleDelete(row.id)">删除</el-button>
          </el-tooltip>
        </template>
      </el-table-column>
    </el-table>

    <el-pagination v-if="total > pageSize" v-model:current-page="page" :page-size="pageSize" :total="total"
      layout="prev, pager, next" @current-change="fetchData" style="margin-top: 20px; justify-content: center;" />

    <!-- 新增/编辑弹窗 -->
    <el-dialog v-model="dialogVisible" :title="editingId ? '编辑剧本' : '新增剧本'" width="500px">
      <el-form label-width="80px">
        <el-form-item label="剧本名称">
          <el-input v-model="form.name" placeholder="剧本名称" />
        </el-form-item>
        <el-form-item label="剧本类型">
          <el-select v-model="form.type" style="width: 100%;">
            <el-option v-for="t in types" :key="t" :label="t" :value="t" />
          </el-select>
        </el-form-item>
        <el-form-item label="剧本种类">
          <el-select v-model="form.category" style="width: 100%;">
            <el-option v-for="c in categories" :key="c" :label="c" :value="c" />
          </el-select>
        </el-form-item>
        <el-form-item label="剧本单价(元)">
          <el-input v-model="form.unitPriceYuan" placeholder="单价" />
        </el-form-item>
        <el-form-item label="人数固定">
          <el-switch v-model="form.is_player_count_fixed" />
        </el-form-item>
        <el-form-item label="剧本人数">
          <el-input-number v-model="form.player_count" :min="1" />
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
import { ref, onMounted } from 'vue'
import { ElMessageBox, ElMessage } from 'element-plus'
import { get, post, put, del } from '../utils/request.js'
import { toYuan, toFen } from '../utils/money.js'

const types = ['欢乐', '推理', '恐怖', '情感', '机制']
const categories = ['盒装', '城限']

const scripts = ref([])
const total = ref(0)
const page = ref(1)
const pageSize = 20
const search = ref('')
const filterType = ref('')
const filterCategory = ref('')

const dialogVisible = ref(false)
const editingId = ref(null)
const saving = ref(false)
const form = ref({ name: '', type: '欢乐', category: '盒装', unitPriceYuan: '', is_player_count_fixed: true, player_count: 6 })

onMounted(() => fetchData())

async function fetchData() {
  const res = await get('/api/scripts', { search: search.value, type: filterType.value, category: filterCategory.value, page: page.value, page_size: pageSize })
  scripts.value = res.data
  total.value = res.total
}

function openCreate() { editingId.value = null; form.value = { name: '', type: '欢乐', category: '盒装', unitPriceYuan: '', is_player_count_fixed: true, player_count: 6 }; dialogVisible.value = true }
function openEdit(row) { editingId.value = row.id; form.value = { name: row.name, type: row.type, category: row.category, unitPriceYuan: toYuan(row.unit_price), is_player_count_fixed: !!row.is_player_count_fixed, player_count: row.player_count }; dialogVisible.value = true }

async function handleSave() {
  if (!form.value.name.trim()) { ElMessage.warning('请输入剧本名称'); return }
  saving.value = true
  const data = { name: form.value.name, type: form.value.type, category: form.value.category, unit_price: toFen(form.value.unitPriceYuan), player_count: form.value.player_count, is_player_count_fixed: form.value.is_player_count_fixed }
  try {
    if (editingId.value) { await put(`/api/scripts/${editingId.value}`, data); ElMessage.success('修改成功') }
    else { await post('/api/scripts', data); ElMessage.success('新增成功') }
    dialogVisible.value = false
    await fetchData()
  } catch (e) { ElMessage.error(e.message) } finally { saving.value = false }
}

async function handleDelete(id) { await ElMessageBox.confirm('确定删除该剧本？', '提示', { type: 'warning' }); await del(`/api/scripts/${id}`); ElMessage.success('删除成功'); await fetchData() }
</script>
