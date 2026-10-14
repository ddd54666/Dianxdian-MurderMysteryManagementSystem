<!-- 留言板：卡片列表，按时间倒序，增删功能 -->

<template>
  <div>
    <div style="display: flex; justify-content: space-between; align-items: center;">
      <h2 class="page-title">留言板</h2>
      <el-button type="primary" @click="openCreateDialog">新增留言</el-button>
    </div>
    <p class="intro-text">可在此记录店铺运营建议、系统问题或功能需求。</p>
    <hr class="divider-line" />

    <!-- 留言卡片列表 -->
    <div v-if="messages.length === 0" style="text-align: center; padding: 60px 0;">
      <el-empty description="暂无留言" />
    </div>

    <div v-for="msg in messages" :key="msg.id" class="message-card">
      <div class="msg-header">
        <span class="author-text">{{ msg.author }}：</span>
        <span class="time-text">{{ formatTime(msg.created_at) }}</span>
        <el-button type="danger" link size="small" @click="handleDelete(msg.id)">删除</el-button>
      </div>
      <div class="msg-divider"></div>
      <div class="content-text">{{ msg.content }}</div>
    </div>

    <!-- 分页 -->
    <el-pagination
      v-if="total > pageSize"
      v-model:current-page="page"
      :page-size="pageSize"
      :total="total"
      layout="prev, pager, next"
      @current-change="fetchMessages"
      style="margin-top: 20px; justify-content: center;"
    />

    <!-- 新增留言弹窗 -->
    <el-dialog v-model="dialogVisible" title="新增留言" width="400px">
      <el-form label-position="top">
        <el-form-item label="留言者">
          <el-input v-model="form.author" placeholder="请输入姓名或称呼" />
        </el-form-item>
        <el-form-item label="内容">
          <el-input v-model="form.content" type="textarea" :rows="3" placeholder="请输入留言内容" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleCreate" :loading="submitting">发布</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessageBox, ElMessage } from 'element-plus'
import { get, post, del } from '../utils/request.js'

const messages = ref([])
const total = ref(0)
const page = ref(1)
const pageSize = 20

const dialogVisible = ref(false)
const submitting = ref(false)
const form = ref({ author: '', content: '' })

onMounted(() => fetchMessages())

/* 加载留言列表 */
async function fetchMessages() {
  const res = await get('/api/messages', { page: page.value, page_size: pageSize })
  messages.value = res.data
  total.value = res.total
}

/* 新增留言 */
async function handleCreate() {
  if (!form.value.author.trim() || !form.value.content.trim()) {
    ElMessage.warning('留言者和内容不能为空')
    return
  }
  submitting.value = true
  try {
    await post('/api/messages', { author: form.value.author.trim(), content: form.value.content.trim() })
    ElMessage.success('发布成功')
    dialogVisible.value = false
    form.value = { author: '', content: '' }
    page.value = 1
    await fetchMessages()
  } finally {
    submitting.value = false
  }
}

/* 删除留言 */
async function handleDelete(id) {
  await ElMessageBox.confirm('确定删除该留言？', '提示', { type: 'warning' })
  await del(`/api/messages/${id}`)
  ElMessage.success('删除成功')
  await fetchMessages()
}

/* 格式化时间 */
function formatTime(iso) {
  if (!iso) return ''
  return iso.replace('T', ' ').substring(0, 16)
}

/* 打开新增留言弹窗并清空表单。 */
function openCreateDialog() {
  form.value = { author: '', content: '' }
  dialogVisible.value = true
}
</script>

<style scoped>
.msg-header {
  display: flex;
  align-items: center;
  gap: 8px;
}

.author-text {
  font-family: "STFangsong", "FZFS", "FangSong", "华文仿宋", "仿宋", serif;
  font-size: 15px;
  color: #3D3226;
  font-weight: normal;
  flex: 1;
}

.time-text {
  font-size: 12px;
  color: #BFB5A8;
  flex-shrink: 0;
}

.msg-divider {
  height: 1px;
  background: #E5DDD0;
  margin: 8px 0;
}

.content-text {
  color: #5C4F3E;
  line-height: 1.8;
  white-space: pre-wrap;
  font-size: 14px;
}

/* 留言板简介文字，与首页 desc 同字体 */
.intro-text {
  font-family: "SimSun", "STSong", "宋体", "Noto Serif SC", serif;
  color: #8C7B6B;
  font-size: 14px;
  margin-bottom: 12px;
}
</style>
