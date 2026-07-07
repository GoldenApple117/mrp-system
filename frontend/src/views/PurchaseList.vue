<template>
  <div class="page-container">
    <div class="page-toolbar">
      <el-button type="primary" @click="showDialog(null)"
        ><el-icon><Plus /></el-icon> 新建采购单</el-button
      >
      <el-button type="success" :loading="syncing" @click="syncFromBom"
        ><el-icon><Refresh /></el-icon> 从BOM同步</el-button
      >
      <el-input
        v-model="keyword"
        placeholder="搜索型号/编码"
        class="w-[200px]"
        clearable
        @clear="onSearch"
        @keyup.enter="onSearch"
      >
        <template #prefix
          ><el-icon><Search /></el-icon
        ></template>
      </el-input>
      <el-select
        v-model="filterStatus"
        placeholder="状态"
        class="w-[130px]"
        clearable
        @change="onSearch"
      >
        <el-option label="已下单" value="已下单" /><el-option
          label="部分到货"
          value="部分到货"
        /><el-option label="全部到货" value="全部到货" />
      </el-select>
      <span class="flex-1" />
      <el-button :type="tab==='suppliers'?'':'default'" @click="tab='suppliers'"
        >供应商管理</el-button
      >
    </div>

    <el-tabs v-model="tab" @tab-change="onTabChange">
      <el-tab-pane label="采购订单" name="orders" />
      <el-tab-pane label="供应商" name="suppliers" />
    </el-tabs>

    <!-- 采购订单 — 折叠视图 -->
    <div v-if="tab==='orders'" v-loading="loading">
      <div v-for="p in projectModules" :key="p.product_code" class="proj-card">
        <div class="proj-header" @click="p._open=!p._open">
          <span class="text-[15px] font-semibold">{{ p.product_name }}</span>
          <el-tag size="small" type="danger" class="mx-2 my-0">{{ p.module_count }}模块</el-tag>
          <span class="text-xs text-[var(--color-text-disabled)]">{{ p.total_parts }}零件</span>
          <span class="ml-auto text-[#409eff] font-bold">¥{{ formatMoney(p.totalAmount) }}</span>
          <span class="ml-2 text-[var(--color-text-disabled)]">{{ p._open?'▲':'▼' }}</span>
        </div>
        <div v-show="p._open" class="px-3 pb-2">
          <div v-for="m in p.modules" :key="m.module_code" class="mod-card">
            <div class="mod-header" @click="m._open=!m._open">
              <span class="font-medium">{{ m.module_name }}</span>
              <el-tag size="small" class="mx-1.5 my-0">{{ m.rows.length }}笔</el-tag>
              <span class="text-[#e6a23c] ml-auto text-[13px]"
                >¥{{ formatMoney(m.totalAmount) }}</span
              >
              <span
                class="ml-1.5 text-[var(--color-text-disabled)] text-xs"
                >{{ m._open?'▲':'▼' }}</span
              >
            </div>
            <div v-show="m._open">
              <el-table :data="filterRows(m.rows)" size="small" stripe border>
                <el-table-column prop="material_code" label="编码" width="110" />
                <el-table-column
                  prop="material_name"
                  label="型号"
                  min-width="110"
                  show-overflow-tooltip
                />
                <el-table-column prop="brand" label="品牌" width="75" />
                <el-table-column label="供应商" width="170">
                  <template #default="{row}">
                    <div v-if="row.supplier_link" class="flex items-start gap-1">
                      <a
                        :href="row.supplier_link"
                        target="_blank"
                        class="text-[#409eff] text-[11px] break-all flex-1"
                        >{{ expandedLinks[row.id] ? row.supplier_link : row.supplier_link.slice(0,25)+'...' }}</a
                      >
                      <el-button
                        v-if="row.supplier_link.length>25"
                        link
                        size="small"
                        class="text-[10px] shrink-0"
                        @click="expandedLinks[row.id]=!expandedLinks[row.id]"
                        >{{ expandedLinks[row.id]?'收':'展' }}</el-button
                      >
                    </div>
                    <span v-else class="text-[#c0c4cc] text-[11px]">—</span>
                  </template>
                </el-table-column>
                <el-table-column label="订购" width="55" align="center"
                  ><template #default="{row}">{{ row.order_qty }}</template></el-table-column
                >
                <el-table-column label="需求日" width="90" align="center"
                  ><template #default="{row}"
                    ><span
                      v-if="row.due_date"
                      :style="{color: new Date(row.due_date)<new Date()?'#f56c6c':'#606266'}"
                      >{{ row.due_date }}</span
                    ><span v-else class="text-[#c0c4cc]">—</span></template
                  ></el-table-column
                >
                <el-table-column label="单价" width="65" align="right"
                  ><template #default="{row}"
                    ><span v-if="row.unit_price>0">¥{{ row.unit_price }}</span
                    ><span v-else class="text-[#c0c4cc]">—</span></template
                  ></el-table-column
                >
                <el-table-column label="金额" width="75" align="right"
                  ><template #default="{row}"
                    ><span v-if="row.total_amount>0" class="text-[#e6a23c] font-bold"
                      >¥{{ row.total_amount }}</span
                    ><span v-else class="text-[#c0c4cc]">—</span></template
                  ></el-table-column
                >
                <el-table-column label="提交人" width="55" prop="submitter" />
                <el-table-column label="到/未" width="60" align="center"
                  ><template #default="{row}"
                    ><span class="text-[#67c23a]">{{ row.received_qty||0 }}</span
                    >/<span
                      class="text-[#f56c6c]"
                      >{{ (row.order_qty-(row.received_qty||0)).toFixed(0) }}</span
                    ></template
                  ></el-table-column
                >
                <el-table-column label="状态" width="75"
                  ><template #default="{row}"
                    ><el-tag
                      :type="row.status==='已下单'?'danger':row.status==='部分到货'?'warning':'success'"
                      size="small"
                      >{{ row.status }}</el-tag
                    ></template
                  ></el-table-column
                >
                <el-table-column label="操作" width="190" fixed="right">
                  <template #default="{row}">
                    <el-button
                      v-if="['已下单','部分到货'].includes(row.status)"
                      link
                      type="success"
                      size="small"
                      @click="showReceiveDialog(row)"
                      >收货</el-button
                    >
                    <el-button link type="primary" size="small" @click="updateStatus(row)"
                      >更新到货</el-button
                    >
                    <el-button
                      v-if="row.status==='已下单'"
                      link
                      type="danger"
                      size="small"
                      @click="deletePo(row.id)"
                      >删除</el-button
                    >
                  </template>
                </el-table-column>
              </el-table>
            </div>
          </div>
        </div>
      </div>
      <el-empty v-if="!loading && !projectModules.length" description="暂无采购数据">
        <template #image>
          <el-icon :size="48" color="var(--color-text-disabled)"><Box /></el-icon>
        </template>
        <el-button type="primary" @click="showDialog()">新建采购单</el-button>
      </el-empty>
    </div>

    <!-- 供应商 -->
    <div v-if="tab==='suppliers'">
      <div class="mb-3">
        <el-button type="primary" size="small" @click="showSupplierDialog"
          ><el-icon><Plus /></el-icon> 新增</el-button
        >
      </div>
      <el-table :data="suppliers" stripe border>
        <el-table-column prop="supplier_code" label="编码" width="120" /><el-table-column
          prop="supplier_name"
          label="名称"
          width="100"
        />
        <el-table-column label="购买链接" min-width="180">
          <template #default="{row}"
            ><div v-if="row.purchase_link" class="flex items-start gap-1">
              <a
                :href="row.purchase_link"
                target="_blank"
                class="text-[#409eff] text-xs break-all flex-1"
                >{{ expandedSuppliers[row.id]?row.purchase_link:row.purchase_link.slice(0,35)+'...' }}</a
              ><el-button
                v-if="row.purchase_link.length>35"
                link
                size="small"
                class="text-[10px]"
                @click="expandedSuppliers[row.id]=!expandedSuppliers[row.id]"
                >{{ expandedSuppliers[row.id]?'收起':'展开' }}</el-button
              >
            </div>
            <span v-else class="text-[#c0c4cc]">—</span></template
          >
        </el-table-column>
        <el-table-column prop="contact_person" label="联系人" width="80" /><el-table-column
          prop="contact_phone"
          label="电话"
          width="120"
        /><el-table-column prop="lead_time_days" label="交期(天)" width="80" />
      </el-table>
      <el-dialog v-model="supplierDialogVisible" title="新增供应商" width="450px">
        <el-form :model="supplierForm" label-width="90px">
          <el-form-item label="编码" required
            ><el-input v-model="supplierForm.supplier_code"
          /></el-form-item>
          <el-form-item label="名称" required
            ><el-input v-model="supplierForm.supplier_name"
          /></el-form-item>
          <el-form-item label="联系人"
            ><el-input v-model="supplierForm.contact_person"
          /></el-form-item>
          <el-form-item label="电话"
            ><el-input v-model="supplierForm.contact_phone"
          /></el-form-item>
          <el-form-item label="地址"><el-input v-model="supplierForm.address" /></el-form-item>
          <el-form-item label="交期(天)"
            ><el-input-number v-model="supplierForm.lead_time_days" :min="0"
          /></el-form-item>
        </el-form>
        <template #footer
          ><el-button @click="supplierDialogVisible=false">取消</el-button
          ><el-button type="primary" @click="submitSupplier">保存</el-button></template
        >
      </el-dialog>
    </div>

    <!-- 弹窗 -->
    <el-dialog v-model="dialogVisible" title="新建采购单" width="500px">
      <el-form :model="form" :rules="rules" label-width="90px">
        <el-form-item label="物料" required
          ><el-select v-model="form.item_id" filterable placeholder="选择物料" class="w-full"
            ><el-option
              v-for="m in materialOptions"
              :key="m.id"
              :label="`${m.material_code} ${m.material_name}`"
              :value="m.id" /></el-select
        ></el-form-item>
        <el-form-item label="供应商" required
          ><el-select v-model="form.supplier_id" filterable placeholder="选择供应商" class="w-full"
            ><el-option
              v-for="s in suppliers"
              :key="s.id"
              :label="s.supplier_name"
              :value="s.id" /></el-select
        ></el-form-item>
        <el-row :gutter="16"
          ><el-col :span="12"
            ><el-form-item label="数量" required
              ><el-input-number
                v-model="form.order_qty"
                :min="1"
                class="w-full" /></el-form-item></el-col
          ><el-col :span="12"
            ><el-form-item label="到货日"
              ><el-date-picker
                v-model="form.due_date"
                type="date"
                value-format="YYYY-MM-DD"
                class="w-full" /></el-form-item></el-col
        ></el-row>
      </el-form>
      <template #footer
        ><el-button @click="dialogVisible=false">取消</el-button
        ><el-button type="primary" :loading="saving" @click="submitForm">保存</el-button></template
      >
    </el-dialog>

    <el-dialog v-model="statusDialogVisible" title="更新到货" width="480px">
      <el-form label-width="90px">
        <el-form-item label="物料"
          ><span class="font-bold">{{ statusForm.material_name }}</span></el-form-item
        >
        <el-form-item label="订购总数"
          ><el-tag type="info" size="large">{{ statusForm.order_qty }}</el-tag></el-form-item
        >
        <el-form-item label="本次到货"
          ><el-input-number
            v-model="statusForm.received_delta"
            :min="0"
            :max="statusForm.remain_qty"
            size="large"
            class="w-[180px]"
            @change="calcRemain"
          /><span class="ml-3 text-[var(--color-text-disabled)]"
            >(已到: {{ statusForm.existing_received }})</span
          ></el-form-item
        >
        <el-divider />
        <el-form-item label="累计到货"
          ><span
            class="text-lg text-[#67c23a] font-bold"
            >{{ statusForm.total_after }}</span
          ></el-form-item
        >
        <el-form-item label="剩余未到"
          ><span
            class="text-lg text-[#f56c6c] font-bold"
            >{{ statusForm.remain_after }}</span
          ></el-form-item
        >
      </el-form>
      <template #footer
        ><el-button @click="statusDialogVisible=false">取消</el-button
        ><el-button type="primary" :disabled="!statusForm.received_delta" @click="confirmStatus"
          >确认到货</el-button
        ></template
      >
    </el-dialog>

    <el-dialog v-model="bomSyncVisible" title="选择BOM同步" width="500px">
      <el-alert type="info" :closable="false" show-icon class="mb-4"
        >自动提取BOM中所有采购件生成采购单。</el-alert
      >
      <el-form label-width="100px"
        ><el-form-item label="选择BOM"
          ><el-select v-model="bomSyncBomId" placeholder="选择BOM" class="w-full"
            ><el-option
              v-for="b in bomOptions"
              :key="b.id"
              :label="`${b.bom_code} - ${b.product_name}`"
              :value="b.id" /></el-select></el-form-item
      ></el-form>
      <div
        v-if="syncResult"
        class="mt-3 whitespace-pre-wrap text-sm text-[#67c23a] bg-[#f0f9eb] p-3 rounded-md"
      >
        {{ syncResult }}
      </div>
      <template #footer
        ><el-button @click="bomSyncVisible=false">取消</el-button
        ><el-button type="primary" :loading="syncing" @click="doBomSync"
          >开始同步</el-button
        ></template
      >
    </el-dialog>

    <!-- 收货弹窗 -->
    <el-dialog v-model="receiveVisible" title="采购收货" width="460px">
      <el-form label-width="100px">
        <el-form-item label="物料"
          ><span class="font-bold">{{ receiveForm.material_name }}</span></el-form-item
        >
        <el-form-item label="供应商"
          ><span>{{ receiveForm.supplier_name }}</span></el-form-item
        >
        <el-form-item label="订购总数"
          ><el-tag type="info">{{ receiveForm.order_qty }}</el-tag></el-form-item
        >
        <el-form-item label="已收数量"
          ><el-tag type="success">{{ receiveForm.total_received }}</el-tag></el-form-item
        >
        <el-form-item label="本次收货" required>
          <el-input-number
            v-model="receiveForm.receive_qty"
            :min="1"
            :max="receiveForm.remaining"
            class="w-[150px]"
          />
          <span class="ml-2 text-[var(--color-text-disabled)]"
            >最多 {{ receiveForm.remaining }}</span
          >
        </el-form-item>
        <el-form-item label="不合格数">
          <el-input-number
            v-model="receiveForm.reject_qty"
            :min="0"
            :max="receiveForm.receive_qty"
            class="w-[150px]"
          />
          <span class="ml-2 text-[#f56c6c]">不合格退回供应商</span>
        </el-form-item>
        <el-form-item label="操作人"
          ><el-input v-model="receiveForm.operator" class="w-[200px]"
        /></el-form-item>
        <el-divider />
        <el-form-item label="合格入库"
          ><span
            class="text-base text-[#67c23a] font-bold"
            >{{ (receiveForm.receive_qty||0) - (receiveForm.reject_qty||0) }}</span
          ></el-form-item
        >
        <el-form-item label="累计已收"
          ><span
            class="text-base text-[#409eff] font-bold"
            >{{ (receiveForm.total_received||0) + (receiveForm.receive_qty||0) }}</span
          ></el-form-item
        >
      </el-form>
      <template #footer>
        <el-button @click="receiveVisible=false">取消</el-button>
        <el-button
          type="success"
          :disabled="!receiveForm.receive_qty"
          :loading="receiving"
          @click="confirmReceive"
          >确认收货入库</el-button
        >
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import api from '@/api'

const loading = ref(false); const syncing = ref(false); const tab = ref('orders')
const keyword = ref(''); const filterStatus = ref('')
const suppliers = ref([]); const materialOptions = ref([]); const bomOptions = ref([])
const expandedLinks = reactive({}); const expandedSuppliers = reactive({})
const projectModules = ref([])

async function loadGrouped() {
  loading.value = true
  try {
    const [treeRes, poRes] = await Promise.all([
      api.get('/materials/tree'),
      api.get('/purchase/orders/all')
    ])
    const pos = poRes.items || []
    const projects = (treeRes.projects || []).map(p => {
      let pt = 0
      const modules = p.modules.map(m => {
        const partCodes = new Set(m.parts.map(pp => pp.material_code))
        let mt = 0; const rows = []
        pos.forEach(po => {
          if (partCodes.has(po.material_code)) { rows.push(po); mt += po.total_amount || 0 }
        })
        pt += mt
        return { ...m, rows, totalAmount: mt, _open: false }
      })
      return { ...p, modules, totalAmount: pt, _open: true }
    })
    projectModules.value = projects
  } finally { loading.value = false }
}

function filterRows(rows) {
  if (!rows) return []
  let r = rows
  if (filterStatus.value) r = r.filter(x => x.status === filterStatus.value)
  if (keyword.value) { const kw = keyword.value.toLowerCase(); r = r.filter(x => (x.material_code||'').toLowerCase().includes(kw) || (x.material_name||'').toLowerCase().includes(kw)) }
  return r
}
function onSearch() { loadGrouped() }
function formatMoney(v) { return Number(v||0).toLocaleString('zh-CN',{maximumFractionDigits:0}) }

const statusDialogVisible = ref(false)
const statusForm = reactive({ id: null, material_name: '', order_qty: 0, oldStatus: '', existing_received: 0, received_delta: 0, remain_qty: 0, total_after: 0, remain_after: 0 })
function updateStatus(row) {
  const rec = row.received_qty || 0; const remain = row.order_qty - rec
  Object.assign(statusForm, { id: row.id, material_name: row.material_name, order_qty: row.order_qty, oldStatus: row.status, existing_received: rec, received_delta: 0, remain_qty: remain, total_after: rec, remain_after: remain })
  statusDialogVisible.value = true
}
function calcRemain() { const d = statusForm.received_delta||0; statusForm.total_after = statusForm.existing_received + d; statusForm.remain_after = Math.max(0, statusForm.order_qty - statusForm.total_after) }
async function confirmStatus() {
  const d = statusForm.received_delta||0; if (d<=0) return ElMessage.warning('请输入到货数量')
  const total = statusForm.existing_received + d; const ns = total >= statusForm.order_qty ? '全部到货' : '部分到货'
  await api.put(`/purchase/orders/${statusForm.id}/status`, { status: ns, received_qty: total })
  ElMessage.success(`收货 ${d} 件`); statusDialogVisible.value = false; loadGrouped()
}

// ====== 收货弹窗 ======
const receiveVisible = ref(false)
const receiving = ref(false)
const receiveForm = reactive({
  id: null, material_name: '', supplier_name: '', order_qty: 0, total_received: 0,
  remaining: 0, receive_qty: 1, reject_qty: 0, operator: '系统',
})
function showReceiveDialog(row) {
  const rec = row.received_qty || 0
  Object.assign(receiveForm, {
    id: row.id, material_name: row.material_name, supplier_name: row.supplier_name || '',
    order_qty: row.order_qty, total_received: rec,
    remaining: row.order_qty - rec, receive_qty: Math.min(1, row.order_qty - rec),
    reject_qty: 0, operator: '系统',
  })
  receiveVisible.value = true
}
async function confirmReceive() {
  if (!receiveForm.receive_qty || receiveForm.receive_qty <= 0) return ElMessage.warning('请输入收货数量')
  receiving.value = true
  try {
    const res = await api.post(`/purchase/orders/${receiveForm.id}/receive`, {
      receive_qty: receiveForm.receive_qty,
      reject_qty: receiveForm.reject_qty || 0,
      operator: receiveForm.operator || '系统',
    })
    ElMessage.success(res.message)
    receiveVisible.value = false
    loadGrouped()
  } catch (e) { ElMessage.error(e.message || '收货失败') } finally { receiving.value = false }
}
async function deletePo(id) { await ElMessageBox.confirm('确定删除？', '提示', { type: 'warning' }); await api.delete(`/purchase/orders/${id}`); loadGrouped() }

const dialogVisible = ref(false); const saving = ref(false)
const form = reactive({ item_id: null, supplier_id: null, order_qty: 1, due_date: '' })
const rules = { item_id: [{ required: true }], supplier_id: [{ required: true }], order_qty: [{ required: true }] }
async function showDialog() { const r = await api.get('/materials/all'); materialOptions.value = r.items||[]; dialogVisible.value = true }
async function submitForm() { if (!form.item_id||!form.supplier_id) return ElMessage.warning('请填写完整'); saving.value=true; try { await api.post('/purchase/orders',{...form}); ElMessage.success('创建成功'); dialogVisible.value=false; loadGrouped() } finally { saving.value=false } }

const supplierDialogVisible = ref(false)
const supplierForm = reactive({ supplier_code:'', supplier_name:'', contact_person:'', contact_phone:'', address:'', lead_time_days:0 })
async function fetchSuppliers() { const r = await api.get('/purchase/suppliers'); suppliers.value = r.items||[] }
function showSupplierDialog() { Object.assign(supplierForm,{supplier_code:'',supplier_name:'',contact_person:'',contact_phone:'',address:'',lead_time_days:0}); supplierDialogVisible.value=true }
async function submitSupplier() { await api.post('/purchase/suppliers',{...supplierForm}); ElMessage.success('已添加'); supplierDialogVisible.value=false; fetchSuppliers() }
function onTabChange(v) { if (v==='suppliers') fetchSuppliers() }

const bomSyncVisible = ref(false); const bomSyncBomId = ref(null); const syncResult = ref('')
async function syncFromBom() { syncResult.value=''; bomSyncBomId.value=null; const r=await api.get('/bom/headers'); bomOptions.value=r.items||[]; bomSyncVisible.value=true }
async function doBomSync() { if(!bomSyncBomId.value) return ElMessage.warning('请选择BOM'); syncing.value=true; syncResult.value=''; try { const r=await api.post('/purchase/sync-from-bom',{bom_header_id:bomSyncBomId.value}); syncResult.value=r.message; loadGrouped(); fetchSuppliers() } catch(e) { syncResult.value='同步失败: '+(e.message||e) } finally { syncing.value=false } }

onMounted(() => { loadGrouped(); fetchSuppliers() })
</script>

<style scoped>
.page-container { padding: 0; }
.page-toolbar { display:flex; gap:12px; margin-bottom:16px; align-items:center; flex-wrap:wrap }
.proj-card { border:1px solid var(--color-border-light); border-radius:var(--radius-md); margin-bottom:12px; overflow:hidden }
.proj-header { display:flex; align-items:center; padding:12px 16px; background:var(--color-bg-overlay); cursor:pointer; user-select:none; border-bottom:1px solid var(--color-border-subtle) }
.proj-header:hover { background:var(--color-bg-hover) }
.mod-card { border:1px solid var(--color-border-light); border-radius:var(--radius-sm); margin:8px 0; overflow:hidden }
.mod-header { display:flex; align-items:center; padding:8px 12px; background:var(--color-bg-raised); cursor:pointer; user-select:none }
.mod-header:hover { background:var(--color-bg-hover) }
</style>
