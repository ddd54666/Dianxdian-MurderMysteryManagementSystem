<!-- 会员管理：列表、详情抽屉（含充值/消费Tabs）、增删改、二级密码保护 -->

<template>
  <div>
    <!-- 二级密码弹窗：置于锁定与解锁分支之外，锁定时与解锁后会话过期场景均可弹出 -->
    <PasswordDialog v-model:visible="showPwd" @unlocked="onUnlocked" @cancelled="onPwdCancelled" />
    <template v-if="!unlocked">
      <div style="text-align: center; padding: 60px 0;">
        <p style="color: #8C7B6B; margin-bottom: 16px;">此页面需要二级密码</p>
        <el-button type="primary" @click="showPwd = true">输入密码</el-button>
      </div>
    </template>

    <template v-else>
      <div style="display: flex; justify-content: space-between; align-items: center;">
        <h2 class="page-title">会员管理</h2>
        <el-button type="primary" @click="handleCreateMember">新增会员</el-button>
      </div>
      <hr class="divider-line" />

    <!-- 搜索 -->
    <el-input v-model="search" placeholder="搜索姓名或电话" clearable style="width: 240px; margin-bottom: 16px;" @change="fetchData" />

    <!-- 列表 -->
    <el-table :data="members" stripe style="width: 100%;" :header-cell-style="{ background: '#F0EBE2' }">
      <el-table-column prop="name" label="姓名" min-width="120" />
      <el-table-column prop="gender" label="性别" width="70" />
      <el-table-column prop="phone" label="电话" width="140" />
      <el-table-column label="余额(元)" width="120">
        <template #default="{ row }"><span class="money-font">{{ toYuan(row.balance) }}</span></template>
      </el-table-column>
      <el-table-column prop="created_at" label="创建时间" width="150">
        <template #default="{ row }">{{ formatTime(row.created_at) }}</template>
      </el-table-column>
      <el-table-column label="最后更新" width="150">
        <template #default="{ row }">{{ formatTime(row.updated_at) }}</template>
      </el-table-column>
      <el-table-column label="操作" width="100">
        <template #default="{ row }">
          <el-button link type="primary" size="small" @click="openDetail(row)">查看详情</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-pagination v-if="total > pageSize" v-model:current-page="page" :page-size="pageSize" :total="total"
      layout="prev, pager, next" @current-change="fetchData" style="margin-top: 20px; justify-content: center;" />

    <!-- 新增会员弹窗 -->
    <el-dialog v-model="createVisible" title="新增会员" width="500px">
      <el-form label-width="80px">
        <el-form-item label="顾客姓名"><el-input v-model="createForm.name" /></el-form-item>
        <el-form-item label="性别"><el-select v-model="createForm.gender" style="width: 100%;"><el-option label="男" value="男" /><el-option label="女" value="女" /></el-select></el-form-item>
        <el-form-item label="电话"><el-input v-model="createForm.phone" maxlength="11" /></el-form-item>
        <el-form-item label="实付金额(元)"><el-input v-model="createForm.payYuan" /></el-form-item>
        <el-form-item label="赠送金额(元)"><el-input v-model="createForm.bonusYuan" /></el-form-item>
        <el-form-item label="备注"><el-input v-model="createForm.notes" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="createVisible = false">取消</el-button>
        <el-button type="primary" @click="doCreateMember" :loading="creating">确定</el-button>
      </template>
    </el-dialog>

    <!-- 会员详情抽屉 -->
    <el-drawer v-model="drawerVisible" size="650px" :modal="true" :close-on-click-modal="true" destroy-on-close :before-close="handleDrawerClose">
      <template #header>
        <span style="font-family: STFangsong,FangSong,serif; font-size: 18px;">会员详情 - {{ detail.name }}</span>
      </template>

      <div class="detail-info">
        <p><strong>姓名：</strong>{{ detail.name }} &nbsp; <strong>性别：</strong>{{ detail.gender }} &nbsp; <strong>电话：</strong>{{ detail.phone }}</p>
        <p><strong>当前余额：</strong><span class="money-font" style="font-size: 18px; color: #8B7355;">{{ toYuan(detail.balance) }} 元</span></p>
        <p><strong>备注：</strong>{{ detail.notes || '无' }}</p>
        <el-button link type="primary" @click="openEditMember">编辑信息</el-button>
      </div>

      <el-tabs v-model="activeTab">
        <el-tab-pane label="消费记录" name="consumptions">
          <div style="margin-bottom: 12px;">
            <el-button type="primary" size="small" @click="openCreateConsumption">新增消费</el-button>
          </div>
          <el-table :data="consumptions" stripe size="small">
            <el-table-column label="时间" width="140"><template #default="{ row }">{{ formatTime(row.consumption_time) }}</template></el-table-column>
            <el-table-column label="金额(元)" width="100"><template #default="{ row }"><span class="money-font">{{ toYuan(row.amount) }}</span></template></el-table-column>
            <el-table-column prop="script_name" label="剧本" min-width="140" />
            <el-table-column label="操作" width="100">
              <template #default="{ row }">
                <el-button link size="small" @click="openEditConsumption(row)">编辑</el-button>
                <el-button link type="danger" size="small" @click="handleDeleteConsumption(row.id)">删除</el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-tab-pane>

        <el-tab-pane label="充值记录" name="recharges">
          <div style="margin-bottom: 12px;">
            <el-button type="primary" size="small" @click="openCreateRecharge">新增充值</el-button>
          </div>
          <el-table :data="recharges" stripe size="small">
            <el-table-column label="时间" width="140"><template #default="{ row }">{{ formatTime(row.recharge_time) }}</template></el-table-column>
            <el-table-column label="实付(元)" width="100"><template #default="{ row }"><span class="money-font">{{ toYuan(row.pay_amount) }}</span></template></el-table-column>
            <el-table-column label="赠送(元)" min-width="100"><template #default="{ row }"><span class="money-font">{{ toYuan(row.bonus_amount) }}</span></template></el-table-column>
            <el-table-column label="操作" width="100">
              <template #default="{ row }">
                <el-button link size="small" @click="openEditRecharge(row)">编辑</el-button>
                <el-button link type="danger" size="small" @click="handleDeleteRecharge(row.id)">删除</el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-tab-pane>
      </el-tabs>
    </el-drawer>

    <!-- 编辑会员信息弹窗 -->
    <el-dialog v-model="editMemberVisible" title="编辑会员信息" width="400px">
      <el-form label-width="80px">
        <el-form-item label="姓名"><el-input v-model="editMemberForm.name" /></el-form-item>
        <el-form-item label="性别"><el-select v-model="editMemberForm.gender" style="width: 100%;"><el-option label="男" value="男" /><el-option label="女" value="女" /></el-select></el-form-item>
        <el-form-item label="电话"><el-input v-model="editMemberForm.phone" maxlength="11" /></el-form-item>
        <el-form-item label="备注"><el-input v-model="editMemberForm.notes" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="editMemberVisible = false">取消</el-button>
        <el-button type="primary" @click="doEditMember" :loading="saving">确定</el-button>
      </template>
    </el-dialog>

    <!-- 消费弹窗 -->
    <el-dialog v-model="consumptionVisible" :title="editingConsumptionId ? '编辑消费' : '新增消费'" width="400px">
      <el-form label-width="80px">
        <el-form-item label="消费时间">
          <el-date-picker v-model="consumptionForm.time" type="datetime" value-format="YYYY-MM-DDTHH:mm:ss" style="width: 100%;" />
        </el-form-item>
        <el-form-item label="金额(元)"><el-input v-model="consumptionForm.amountYuan" /></el-form-item>
        <el-form-item label="游玩剧本"><el-input v-model="consumptionForm.script_name" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="consumptionVisible = false">取消</el-button>
        <el-button type="primary" @click="doSaveConsumption" :loading="saving">确定</el-button>
      </template>
    </el-dialog>

    <!-- 充值弹窗 -->
    <el-dialog v-model="rechargeVisible" :title="editingRechargeId ? '编辑充值' : '新增充值'" width="400px">
      <el-form label-width="80px">
        <el-form-item label="充值时间">
          <el-date-picker v-model="rechargeForm.time" type="datetime" value-format="YYYY-MM-DDTHH:mm:ss" style="width: 100%;" />
        </el-form-item>
        <el-form-item label="实付(元)"><el-input v-model="rechargeForm.payYuan" /></el-form-item>
        <el-form-item label="赠送(元)"><el-input v-model="rechargeForm.bonusYuan" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="rechargeVisible = false">取消</el-button>
        <el-button type="primary" @click="doSaveRecharge" :loading="saving">确定</el-button>
      </template>
    </el-dialog>

    </template>
  </div>
</template>

<script setup>
import { ref, watch, onMounted } from 'vue'
import { ElMessageBox, ElMessage } from 'element-plus'
import { get, post, put, del } from '../utils/request.js'
import { toYuan, toFen } from '../utils/money.js'
import { isUnlocked } from '../utils/password.js'
import PasswordDialog from '../components/PasswordDialog.vue'

const members = ref([])
const total = ref(0)
const page = ref(1)
const pageSize = 20
const search = ref('')

const createVisible = ref(false)
const creating = ref(false)
const createForm = ref({ name: '', gender: '男', phone: '', payYuan: '', bonusYuan: '0', notes: '' })

const drawerVisible = ref(false)
const detail = ref({})
const activeTab = ref('consumptions')
const consumptions = ref([])
const recharges = ref([])

const editMemberVisible = ref(false)
const editMemberForm = ref({ name: '', gender: '', phone: '', notes: '' })

const consumptionVisible = ref(false)
const editingConsumptionId = ref(null)
const consumptionForm = ref({ time: '', amountYuan: '', script_name: '' })

const rechargeVisible = ref(false)
const editingRechargeId = ref(null)
const rechargeForm = ref({ time: '', payYuan: '', bonusYuan: '0' })

const unlocked = ref(isUnlocked())
const saving = ref(false)
const showPwd = ref(false)

/* 密码回调 */
let pwdCallback = null
function onUnlocked() {
  unlocked.value = true
  if (pwdCallback) { pwdCallback(); pwdCallback = null }
}
function onPwdCancelled() { pwdCallback = null }

/* 需要二级密码的操作包装（页面解锁后 session 过期时使用） */
function requirePassword(callback) {
  if (isUnlocked()) { callback(); return }
  pwdCallback = callback
  showPwd.value = true
}

watch(unlocked, (val) => { if (val) fetchData() })
if (unlocked.value) fetchData()

async function fetchData() {
  const res = await get('/api/members', { search: search.value, page: page.value, page_size: pageSize })
  members.value = res.data
  total.value = res.total
}

/* 新增会员 */
async function handleCreateMember() {
  if (!isUnlocked()) { showPwd.value = true; pwdCallback = () => { createVisible.value = true }; return }
  createForm.value = { name: '', gender: '男', phone: '', payYuan: '', bonusYuan: '0', notes: '' }
  createVisible.value = true
}

async function doCreateMember() {
  if (!createForm.value.name || !createForm.value.phone || !createForm.value.payYuan) {
    ElMessage.warning('姓名、电话、实付金额不能为空'); return
  }
  creating.value = true
  try {
    await post('/api/members', { name: createForm.value.name, gender: createForm.value.gender, phone: createForm.value.phone, pay_amount: toFen(createForm.value.payYuan), bonus_amount: toFen(createForm.value.bonusYuan || '0'), notes: createForm.value.notes })
    ElMessage.success('新增成功')
    createVisible.value = false
    await fetchData()
  } finally { creating.value = false }
}

/* 打开详情 */
async function openDetail(row) {
  const res = await get(`/api/members/${row.id}`)
  detail.value = res.data
  consumptions.value = res.data.consumptions || []
  recharges.value = res.data.recharges || []
  activeTab.value = 'consumptions'
  drawerVisible.value = true
}

/* 抽屉关闭时清理状态 */
function handleDrawerClose() {
  detail.value = {}
  consumptions.value = []
  recharges.value = []
  activeTab.value = 'consumptions'
  drawerVisible.value = false
  fetchData()
}

/* 编辑会员信息（需密码） */
function openEditMember() { requirePassword(_openEditMember) }
function _openEditMember() {
  editMemberForm.value = { name: detail.value.name, gender: detail.value.gender, phone: detail.value.phone, notes: detail.value.notes || '' }
  editMemberVisible.value = true
}

async function doEditMember() {
  saving.value = true
  try {
    await put(`/api/members/${detail.value.id}`, editMemberForm.value)
    ElMessage.success('修改成功')
    editMemberVisible.value = false
    const res = await get(`/api/members/${detail.value.id}`)
    detail.value = res.data
  } finally { saving.value = false }
}

/* 消费（需密码） */
function openCreateConsumption() { requirePassword(_openCreateConsumption) }
function _openCreateConsumption() {
  editingConsumptionId.value = null
  consumptionForm.value = { time: new Date().toISOString().slice(0, 16), amountYuan: '', script_name: '' }
  consumptionVisible.value = true
}

function openEditConsumption(row) { requirePassword(() => _openEditConsumption(row)) }
function _openEditConsumption(row) {
  editingConsumptionId.value = row.id
  consumptionForm.value = { time: row.consumption_time, amountYuan: toYuan(row.amount), script_name: row.script_name }
  consumptionVisible.value = true
}

async function doSaveConsumption() {
  saving.value = true
  try {
    const data = { consumption_time: consumptionForm.value.time, amount: toFen(consumptionForm.value.amountYuan), script_name: consumptionForm.value.script_name }
    if (editingConsumptionId.value) { await put(`/api/consumptions/${editingConsumptionId.value}`, data) }
    else { await post(`/api/members/${detail.value.id}/consumptions`, data) }
    ElMessage.success(editingConsumptionId.value ? '修改成功' : '新增成功')
    consumptionVisible.value = false
    const res = await get(`/api/members/${detail.value.id}`)
    consumptions.value = res.data.consumptions || []
    detail.value.balance = res.data.balance
  } finally { saving.value = false }
}

async function handleDeleteConsumption(id) { requirePassword(() => _handleDeleteConsumption(id)) }
async function _handleDeleteConsumption(id) {
  await ElMessageBox.confirm('确定删除该消费记录？将同步更新余额。', '提示', { type: 'warning' })
  await del(`/api/consumptions/${id}`)
  ElMessage.success('删除成功')
  const res = await get(`/api/members/${detail.value.id}`)
  consumptions.value = res.data.consumptions || []
  detail.value.balance = res.data.balance
}

/* 充值（需密码） */
function openCreateRecharge() { requirePassword(_openCreateRecharge) }
function _openCreateRecharge() {
  editingRechargeId.value = null
  rechargeForm.value = { time: new Date().toISOString().slice(0, 16), payYuan: '', bonusYuan: '0' }
  rechargeVisible.value = true
}

function openEditRecharge(row) { requirePassword(() => _openEditRecharge(row)) }
function _openEditRecharge(row) {
  editingRechargeId.value = row.id
  rechargeForm.value = { time: row.recharge_time, payYuan: toYuan(row.pay_amount), bonusYuan: toYuan(row.bonus_amount) }
  rechargeVisible.value = true
}

async function doSaveRecharge() {
  saving.value = true
  try {
    const data = { recharge_time: rechargeForm.value.time, pay_amount: toFen(rechargeForm.value.payYuan), bonus_amount: toFen(rechargeForm.value.bonusYuan) }
    if (editingRechargeId.value) { await put(`/api/recharges/${editingRechargeId.value}`, data) }
    else { await post(`/api/members/${detail.value.id}/recharges`, data) }
    ElMessage.success(editingRechargeId.value ? '修改成功' : '新增成功')
    rechargeVisible.value = false
    const res = await get(`/api/members/${detail.value.id}`)
    recharges.value = res.data.recharges || []
    detail.value.balance = res.data.balance
  } finally { saving.value = false }
}

async function handleDeleteRecharge(id) { requirePassword(() => _handleDeleteRecharge(id)) }
async function _handleDeleteRecharge(id) {
  await ElMessageBox.confirm('确定删除该充值记录？将同步更新余额。', '提示', { type: 'warning' })
  await del(`/api/recharges/${id}`)
  ElMessage.success('删除成功')
  const res = await get(`/api/members/${detail.value.id}`)
  recharges.value = res.data.recharges || []
  detail.value.balance = res.data.balance
}

function formatTime(iso) {
  if (!iso) return ''
  return iso.replace('T', ' ').substring(0, 16)
}
</script>

<style scoped>
.detail-info { margin-bottom: 20px; padding-bottom: 12px; border-bottom: 1px solid #E5DDD0; }
.detail-info p { margin: 6px 0; color: #5C4F3E; }
</style>
