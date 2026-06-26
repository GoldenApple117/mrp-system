<template>
  <div class="page-container">
    <div class="page-toolbar">
      <el-button type="primary" @click="showDialog(null)"><el-icon><Plus /></el-icon> 新建工艺路线</el-button>
    </div>

    <el-table :data="tableData" v-loading="loading" stripe border @row-click="showDetail">
      <el-table-column prop="routing_code" label="工艺编码" width="150" />
      <el-table-column prop="material_code" label="物料编码" width="130" />
      <el-table-column prop="material_name" label="物料名称" min-width="160" />
      <el-table-column label="工序数量" width="100">
        <template #default="{row}">
          <el-tag size="small">{{ row.operations_count }} 道</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="120" fixed="right">
        <template #default="{row}">
          <el-button link type="primary" size="small" @click.stop="showDetail(row)">查看</el-button>
        </template>
      </el-table-column>
    </el-table>

    <!-- 新建弹窗 -->
    <el-dialog v-model="dialogVisible" title="新建工艺路线" width="750px">
      <el-form label-width="100px">
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="工艺编码" required>
              <el-input v-model="form.routing_code" placeholder="如 RT-P-A1" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="适用物料" required>
              <el-select v-model="form.item_id" filterable placeholder="选择物料" style="width:100%">
                <el-option v-for="m in matOptions" :key="m.id" :label="`${m.material_code} ${m.material_name}`" :value="m.id" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>

        <el-divider>工序列表</el-divider>

        <div v-for="(op, idx) in form.operations" :key="idx" style="background:#f9f9f9;padding:12px;margin-bottom:8px;border-radius:6px">
          <el-row :gutter="12">
            <el-col :span="2">
              <el-input v-model="op.seq_no" placeholder="序号" size="small" />
            </el-col>
            <el-col :span="5">
              <el-input v-model="op.operation_name" placeholder="工序名称" size="small" />
            </el-col>
            <el-col :span="5">
              <el-select v-model="op.work_center_id" filterable placeholder="工作中心" size="small" style="width:100%">
                <el-option v-for="wc in wcOptions" :key="wc.id" :label="wc.center_name" :value="wc.id" />
              </el-select>
            </el-col>
            <el-col :span="4">
              <el-input-number v-model="op.setup_time" :min="0" :precision="1" size="small" placeholder="准备(min)" style="width:100%" />
            </el-col>
            <el-col :span="4">
              <el-input-number v-model="op.run_time_per_unit" :min="0" :precision="2" size="small" placeholder="单件(min)" style="width:100%" />
            </el-col>
            <el-col :span="2">
              <el-button link type="danger" size="small" @click="form.operations.splice(idx,1)">×</el-button>
            </el-col>
          </el-row>
        </div>
        <el-button size="small" @click="form.operations.push({seq_no: form.operations.length+1, operation_name: '', work_center_id: null, setup_time: 5, run_time_per_unit: 0.5, queue_time: 0})">
          添加工序
        </el-button>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible=false">取消</el-button>
        <el-button type="primary" @click="submitForm" :loading="saving">保存</el-button>
      </template>
    </el-dialog>

    <!-- 详情弹窗 -->
    <el-dialog v-model="detailVisible" title="工艺路线详情" width="700px">
      <template v-if="detailData">
        <el-descriptions :column="2" border size="small">
          <el-descriptions-item label="工艺编码">{{ detailData.header.routing_code }}</el-descriptions-item>
          <el-descriptions-item label="物料">{{ detailData.header.material_code }}</el-descriptions-item>
        </el-descriptions>
        <el-table :data="detailData.operations" stripe border size="small" style="margin-top:12px">
          <el-table-column label="序号" prop="seq_no" width="60" />
          <el-table-column label="工序名称" prop="operation_name" min-width="140" />
          <el-table-column label="工作中心" prop="work_center_name" width="130" />
          <el-table-column label="准备(min)" prop="setup_time" width="100" />
          <el-table-column label="单件(min)" prop="run_time_per_unit" width="100" />
          <el-table-column label="排队(min)" prop="queue_time" width="100" />
        </el-table>
      </template>
      <div v-else style="text-align:center;padding:40px;color:#999">加载中...</div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import api from '@/api'

const loading = ref(false)
const saving = ref(false)
const tableData = ref([])
const dialogVisible = ref(false)
const detailVisible = ref(false)
const detailData = ref(null)
const matOptions = ref([])
const wcOptions = ref([])
const form = ref({
  routing_code: '', item_id: null,
  operations: [{ seq_no: 1, operation_name: '', work_center_id: null, setup_time: 5, run_time_per_unit: 0.5, queue_time: 0 }],
})

async function fetchData() {
  loading.value = true
  try {
    const res = await api.get('/production/routings')
    tableData.value = res.items
  } finally { loading.value = false }
}

async function showDialog() {
  const [matRes, wcRes] = await Promise.all([
    api.get('/materials/all', { params: { material_type: '成品' } }),
    api.get('/production/work-centers'),
  ])
  matOptions.value = matRes.items || []
  wcOptions.value = wcRes.items || []
  form.value = {
    routing_code: '', item_id: null,
    operations: [{ seq_no: 1, operation_name: '', work_center_id: null, setup_time: 5, run_time_per_unit: 0.5, queue_time: 0 }],
  }
  dialogVisible.value = true
}

async function submitForm() {
  if (!form.value.routing_code || !form.value.item_id) {
    return ElMessage.warning('请填写工艺编码和适用物料')
  }
  const validOps = form.value.operations.filter(o => o.operation_name && o.work_center_id)
  if (!validOps.length) return ElMessage.warning('请添加至少一道工序')
  saving.value = true
  try {
    await api.post('/production/routings', { ...form.value, operations: validOps })
    ElMessage.success('工艺路线创建成功')
    dialogVisible.value = false
    fetchData()
  } finally { saving.value = false }
}

async function showDetail(row) {
  detailData.value = null
  detailVisible.value = true
  const res = await api.get(`/production/routings/${row.id}`)
  detailData.value = res
}

onMounted(fetchData)
</script>

<style scoped>
.page-container { background:#fff; padding:20px; border-radius:8px; }
.page-toolbar { display:flex; gap:12px; margin-bottom:16px; align-items:center; }
</style>
