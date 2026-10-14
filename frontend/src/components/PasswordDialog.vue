<!-- 二级密码验证弹窗，成功后 sessionStorage 记录解锁时间，3分钟有效。 -->

<template>
  <el-dialog
    :model-value="visible"
    @update:model-value="$emit('update:visible', $event)"
    title="请输入二级密码"
    width="350px"
    :close-on-click-modal="false"
    :close-on-press-escape="false"
    center
  >
    <el-input
      v-model="password"
      type="password"
      placeholder="请输入二级密码"
      show-password
      @keyup.enter="handleVerify"
    />
    <p v-if="errorMsg" style="color: #C46B5A; margin-top: 8px; font-size: 12px;">
      {{ errorMsg }}
    </p>
    <template #footer>
      <el-button @click="handleCancel">取消</el-button>
      <el-button type="primary" @click="handleVerify" :loading="loading">确认</el-button>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref } from 'vue'
import { post } from '../utils/request.js'

const props = defineProps({
  visible: { type: Boolean, default: false }
})

const emit = defineEmits(['update:visible', 'unlocked', 'cancelled'])

const password = ref('')
const errorMsg = ref('')
const loading = ref(false)

/* 验证密码 */
async function handleVerify() {
  if (!password.value) {
    errorMsg.value = '请输入密码'
    return
  }
  loading.value = true
  errorMsg.value = ''
  try {
    const res = await post('/api/auth/verify-password', { password: password.value })
    if (res.valid) {
      /* 记录解锁时间到 sessionStorage */
      sessionStorage.setItem('pwd_unlocked_at', Date.now().toString())
      password.value = ''
      emit('update:visible', false)
      emit('unlocked')
    }
  } catch (e) {
    /* request.js 密码错误时抛出该消息，其余为网络或服务异常 */
    errorMsg.value = e.message === '密码错误' ? '密码错误' : '无法连接服务，请检查系统是否运行'
  } finally {
    loading.value = false
  }
}

function handleCancel() {
  password.value = ''
  errorMsg.value = ''
  emit('update:visible', false)
  emit('cancelled')
}
</script>
