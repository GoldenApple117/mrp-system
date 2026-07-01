<template>
  <div class="page-container">
    <div class="page-toolbar">
      <el-input v-model="keyword" placeholder="搜索型号/编码" style="width:240px" clearable @clear="onSearch" @keyup.enter="onSearch">
        <template #prefix><el-icon><Search /></el-icon></template>
      </el-input>
      <el-button type="primary" @click="onSearch">搜索</el-button>
      <span style="flex:1" />
      <el-button @click="tab='parts'" :type="tab==='parts'?'primary':'default'">零件管理</el-button>
      <el-button @click="tab='products'" :type="tab==='products'?'':'default'">产品管理</el-button>
      <el-button @click="tab='tx'">出入库流水</el-button>
    </div>

    <!-- 零件管理 -->
    <div v-if="tab==='parts'" v-loading="loading">
      <div v-if="selectedIds.length" class="batch-bar">
        <el-tag type="info">已选 {{ selectedIds.length }} 项</el-tag>
        <el-input-number v-model="batchSafetyStock" :min="0" size="small" style="width:130px" placeholder="新安全库存"/>
        <el-button size="small" type="primary" @click="batchUpdateSafetyStock" :disabled="batchSafetyStock===null">批量更新</el-button>
        <el-button size="small" @click="selectedIds=[]">取消</el-button>
      </div>
      <div v-for="p in projects" :key="p.product_code" class="proj-card">
        <div class="proj-header" @click="p._open=!p._open">
          <span style="font-weight:600;font-size:15px">{{ p.product_name }}</span>
          <el-tag size="small" type="danger" style="margin:0 8px">{{ p.module_count }}模块</el-tag>
          <span style="margin-left:auto;color:#999">{{ p._open?'▲':'▼' }}</span>
        </div>
        <div v-show="p._open" style="padding:0 12px 8px">
          <div v-for="m in p.modules" :key="m.module_code" class="mod-card">
            <div class="mod-header" @click="m._open=!m._open">
              <span style="font-weight:500">{{ m.module_name }}</span>
              <el-tag size="small" style="margin:0 6px">{{ m.parts.length }}项</el-tag>
              <span style="margin-left:auto;color:#999;font-size:12px">{{ m._open?'▲':'▼' }}</span>
            </div>
            <div v-show="m._open">
              <el-table :data="getParts(m.parts)" size="small" stripe border @selection-change="(rows)=>selectedIds=rows.map(r=>r.item_id)">
                <el-table-column type="selection" width="40" />
                <el-table-column prop="material_code" label="编码" width="110" />
                <el-table-column prop="material_name" label="型号" min-width="110" show-overflow-tooltip />
                <el-table-column prop="unit" label="单位" width="50" />
                <el-table-column label="库存" width="60" align="center"><template #default="{row}"><span :style="{color:row.on_hand>0?'#67c23a':'#c0c4cc',fontWeight:'bold'}">{{ row.on_hand||0 }}</span></template></el-table-column>
                <el-table-column prop="safety_stock" label="安全库存" width="70" align="center" />
                <el-table-column label="最近入库" width="140">
                  <template #default="{row}"><span v-if="row.last_received_date" style="font-size:11px;color:#67c23a">+{{ row.last_received_qty }} {{ row.unit }}<br/><span style="color:#999">{{ row.last_received_date?.slice(0,16) }}</span></span><span v-else style="color:#c0c4cc;font-size:11px">—</span></template>
                </el-table-column>
                <el-table-column label="操作" width="120" fixed="right">
                  <template #default="{row}"><el-button size="small" type="success" link @click="quickIn(row)">入库</el-button><el-button size="small" type="danger" link @click="quickOut(row)">出库</el-button></template>
                </el-table-column>
              </el-table>
            </div>
          </div>
        </div>
      </div>
      <el-empty v-if="!loading && !projects.length" description="暂无数据" />
    </div>

    <!-- 产品管理 -->
    <div v-if="tab==='products'" v-loading="loading">
      <el-table :data="productStock" size="small" stripe border>
        <el-table-column prop="material_code" label="编码" width="130" />
        <el-table-column prop="material_name" label="产品名称" min-width="150" />
        <el-table-column label="库存" width="80" align="center"><template #default="{row}"><span :style="{color:row.on_hand>0?'#67c23a':'#c0c4cc',fontWeight:'bold'}">{{ row.on_hand||0 }}</span></template></el-table-column>
        <el-table-column label="操作" width="120"><template #default="{row}"><el-button size="small" type="success" link @click="quickIn(row)">入库</el-button><el-button size="small" type="danger" link @click="quickOut(row)">出库</el-button></template></el-table-column>
      </el-table>
    </div>

    <!-- 流水 -->
    <div v-if="tab==='tx'">
      <el-table :data="txData" v-loading="loading" stripe border size="small">
        <el-table-column label="时间" width="145"><template #default="{row}"><span style="font-size:12px">{{ row.created_at?.slice(0,16)?.replace('T',' ') }}</span></template></el-table-column>
        <el-table-column prop="material_code" label="编码" width="110" />
        <el-table-column prop="material_name" label="型号" min-width="100" show-overflow-tooltip />
        <el-table-column label="类型" width="80"><template #default="{row}"><el-tag :type="row.transaction_type.includes('出')?'danger':'success'" size="small">{{ row.transaction_type }}</el-tag></template></el-table-column>
        <el-table-column label="数量" width="65" align="center"><template #default="{row}"><span :style="{color:row.quantity>0?'#67c23a':'#f56c6c',fontWeight:'bold'}">{{ row.quantity>0?'+'+row.quantity:row.quantity }}</span></template></el-table-column>
        <el-table-column label="单号" width="130"><template #default="{row}"><el-tag v-if="row.reference_no" type="info" size="small">{{ row.reference_no }}</el-tag></template></el-table-column>
        <el-table-column prop="operator" label="操作人" width="70" />
        <el-table-column prop="remark" label="备注" min-width="80" />
      </el-table>
    </div>

    <el-dialog v-model="quickDialogVisible" :title="quickType==='in'?'快速入库':'快速出库'" width="420px">
      <el-form label-width="90px">
        <el-form-item label="物料"><span style="font-weight:bold">{{ quickForm.material_code }} {{ quickForm.material_name }}</span></el-form-item>
        <el-form-item label="当前库存"><el-tag :type="quickForm.on_hand>0?'success':'danger'" size="large">{{ quickForm.on_hand }} {{ quickForm.unit }}</el-tag></el-form-item>
        <el-form-item :label="quickType==='in'?'入库数量':'出库数量'"><el-input-number v-model="quickForm.qty" :min="1" :max="quickType==='out'?quickForm.on_hand:99999" size="large" style="width:180px" /></el-form-item>
        <el-form-item label="操作人"><el-input v-model="quickForm.operator" /></el-form-item>
        <el-form-item v-if="quickForm.qty>0" :label="quickType==='in'?'入库后':'出库后'"><span :style="{color:'#67c23a',fontWeight:'bold',fontSize:'16px'}">{{ quickType==='in'?quickForm.on_hand+quickForm.qty:quickForm.on_hand-quickForm.qty }}</span></el-form-item>
      </el-form>
      <template #footer><el-button @click="quickDialogVisible=false">取消</el-button><el-button :type="quickType==='in'?'success':'danger'" @click="doQuickTx" :loading="quickSaving">确认</el-button></template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import api from '@/api'

const loading = ref(false); const tab = ref('parts'); const keyword = ref('')
const projects = ref([])
const selectedIds = ref([]); const batchSafetyStock = ref(null)
const productStock = ref([])
const inventoryMap = ref({})

async function loadData() {
  loading.value = true
  try {
    const [treeRes, invRes] = await Promise.all([api.get('/materials/tree'), api.get('/inventory/summary')])
    const invMap = {}; (invRes.items||[]).forEach(i => { invMap[i.material_code] = i })
    inventoryMap.value = invMap
    productStock.value = (invRes.items||[]).filter(i => i.material_type==='成品')
    projects.value = (treeRes.projects||[]).map(p => ({
      ...p, _open: true,
      modules: p.modules.map(m => ({ ...m, _open: false }))
    }))
  } finally { loading.value = false }
}

function getParts(parts) {
  let r = parts.map(p => { const inv = inventoryMap.value[p.material_code]||{}; return { ...p, on_hand: inv.on_hand||0, last_received_qty:inv.last_received_qty||0, last_received_date:inv.last_received_date } })
  if (keyword.value) { const kw = keyword.value.toLowerCase(); r = r.filter(p => (p.material_code||'').toLowerCase().includes(kw) || (p.material_name||'').toLowerCase().includes(kw)) }
  return r
}
function onSearch() { loadData() }

async function batchUpdateSafetyStock() {
  if (batchSafetyStock.value===null) return
  await ElMessageBox.confirm(`将 ${selectedIds.value.length} 个物料安全库存设为 ${batchSafetyStock.value}？`,'批量更新',{type:'info'})
  await api.put('/materials/batch/safety-stock',{item_ids:selectedIds.value,safety_stock:batchSafetyStock.value})
  ElMessage.success('已更新'); selectedIds.value=[]; batchSafetyStock.value=null; loadData()
}

const quickDialogVisible = ref(false); const quickType = ref('in'); const quickSaving = ref(false)
const quickForm = reactive({ item_id:null, material_code:'', material_name:'', unit:'', on_hand:0, qty:1, operator:'' })
function quickIn(row) { quickType.value='in'; Object.assign(quickForm,{item_id:row.id||row.item_id,material_code:row.material_code,material_name:row.material_name,unit:row.unit||'个',on_hand:row.on_hand||0,qty:1,operator:''}); quickDialogVisible.value=true }
function quickOut(row) { quickType.value='out'; Object.assign(quickForm,{item_id:row.id||row.item_id,material_code:row.material_code,material_name:row.material_name,unit:row.unit||'个',on_hand:row.on_hand||0,qty:1,operator:''}); quickDialogVisible.value=true }
async function doQuickTx() {
  if (!quickForm.qty||quickForm.qty<=0) return
  if (quickType.value==='out' && quickForm.qty>quickForm.on_hand) return ElMessage.error('出库数量不能超过现有库存')
  quickSaving.value=true
  try { const whRes=await api.get('/inventory/warehouses'); const whId=whRes.items[0]?.id||1; const qty=quickType.value==='in'?quickForm.qty:-quickForm.qty; await api.post('/inventory/transaction',{item_id:quickForm.item_id,warehouse_id:whId,transaction_type:quickType.value==='in'?'入库':'出库',quantity:qty,operator:quickForm.operator,remark:quickType.value==='in'?'手动入库':'手动出库'}); ElMessage.success(`${quickType.value==='in'?'入库':'出库'} ${quickForm.qty}`); quickDialogVisible.value=false; loadData() }
  catch(e) { ElMessage.error('操作失败: '+(e.message||'')) }
  finally { quickSaving.value=false }
}

const txData = ref([])
async function fetchTx() { loading.value=true; try { const r=await api.get('/inventory/transactions',{params:{page_size:200}}); txData.value=r.items||[] } finally { loading.value=false } }
onMounted(() => { loadData(); fetchTx() })
</script>

<style scoped>
.page-container { background:#fff; padding:20px; border-radius:8px }
.page-toolbar { display:flex; gap:12px; margin-bottom:16px; align-items:center; flex-wrap:wrap }
.batch-bar { display:flex; align-items:center; gap:8px; background:#f0f9eb; border:1px solid #b3e19d; padding:8px 14px; border-radius:6px; margin-bottom:12px }
.proj-card { border:1px solid #e4e7ed; border-radius:8px; margin-bottom:12px; overflow:hidden }
.proj-header { display:flex; align-items:center; padding:12px 16px; background:#fafbfc; cursor:pointer; user-select:none; border-bottom:1px solid #ebeef5 }
.proj-header:hover { background:#f0f5ff }
.mod-card { border:1px solid #f0f0f0; border-radius:6px; margin:8px 0; overflow:hidden }
.mod-header { display:flex; align-items:center; padding:8px 12px; background:#fafbfc; cursor:pointer; user-select:none }
.mod-header:hover { background:#f5f7fa }
</style>
