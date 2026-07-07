# MDR II 制造执行深化开发计划 v1.0

> 目标：将系统从 MRP II 计划层向 MES 执行层深化，打造面向中小离散制造业的"计划—执行—追溯"一体化解决方案。
>
> 技术栈：FastAPI + Vue 3 + Element Plus + MySQL 8.4

---

## 总体策略

不追金蝶用友的大而全（财务/HR/CRM），聚焦**制造执行**这条线做深——从工单下达那一刻起，每一颗物料、每一道工序、每一次质检、每一个工时都被记录、可追溯。

### 设计原则

1. **复用已有模型** — 不推翻重来，在现有 `work_order` / `routing` / `inspection_record` 上延伸
2. **每一期可独立交付** — 一个 phase 做完就能上线用，后续 phase 是增量叠加
3. **前后端同步推进** — 每个功能后端 API 先通，前端紧接着跟上
4. **MySQL 原生特性** — 本地和云端都跑 MySQL，充分利用 CTE、窗口函数、事务

---

## Phase 6 — 工序级工单执行

**目标**：将工单从"整单管理"下沉到"工序级管理"——每道工序可独立开工、报工、检验、流转

### 现状
- `work_order` 是一整张单子，开工→完工是单步操作
- `routing_header` + `routing_operation` 定义了工艺路线，但没有与工单实际执行绑定
- 报工是"按工单"而非"按工序"

### 改动

**6.1 工序执行表（新模型）**
```python
class WorkOrderOperation(Base):
    """工单工序执行记录"""
    work_order_id       # FK → work_order
    routing_operation_id # FK → routing_operation
    seq_no              # 工序序号
    work_center_id      # 实际执行工作中心
    status              # 待开工 / 进行中 / 待检验 / 已完成 / 跳过
    plan_start / plan_end
    actual_start / actual_end
    completed_qty       # 本工序完成数
    rejected_qty        # 本工序不合格数
    labor_hours         # 本工序工时
    setup_hours         # 换线工时
    operator            # 操作人
```

**6.2 API 端点**
| 方法 | 端点 | 说明 |
|------|------|------|
| POST | `/production/orders/{id}/operations/init` | 根据工艺路线生成工序执行计划 |
| GET | `/production/orders/{id}/operations` | 查看工单工序列表 |
| POST | `/production/orders/{id}/operations/{op_id}/start` | 开工 |
| POST | `/production/orders/{id}/operations/{op_id}/report` | 报工 |
| POST | `/production/orders/{id}/operations/{op_id}/complete` | 完成 |
| POST | `/production/orders/{id}/operations/{op_id}/skip` | 跳过 |

**6.3 前端**：工单详情页增加"工序视图"Tab，显示工艺路线→工序卡片流，支持拖拽调整顺序

**6.4 工艺路线绑定**
- 创建工单时如果物料有 `routing_header`，自动带出
- `start` 时根据 routing 展开工序执行计划
- 上游工序完成后，下游工序自动变为"待开工"

---

## Phase 7 — 质检体系完善（IQC → PQC → OQC）

**目标**：构建完整的来料→过程→出货三级检验体系，并与工单、采购单、销售单自然联动

### 现状
- `inspection_record` 只有一个表，且仅关联 `purchase_order_id`
- 缺少检验标准/抽样方案
- 不合格品处理流程缺失

### 改动

**7.1 检验标准表（新模型）**
```python
class InspectionStandard(Base):
    """检验标准"""
    item_id             # 物料
    standard_code       # 标准编码
    inspection_type     # IQC / PQC / OQC
    sampling_method     # 全检 / AQL / 百分比
    aql_level           # AQL 等级（可选）
    sample_size
    accept_level
    characteristics     # JSON: 检验特性列表 {name, spec, method, tool}
```

**7.2 检验记录重构**
- 扩展现有 `inspection_record`，增加 `inspection_type`（IQC/PQC/OQC）、`source_type`（采购单/工单/工单工序/销售出货单）、`standard_id`
- 新增 `inspection_defect` 表：不合格品明细（缺陷类型/严重度/处理方式/责任方）

**7.3 不合格品处理流程（NCR）**
```python
class NcrRecord(Base):
    """不合格品处理单"""
    ncr_no              # NCR 编号
    source_type         # 来源类型
    source_id           # 关联单号
    item_id / qty
    defect_type         # 缺陷分类
    severity            # 严重度：致命/严重/一般/轻微
    disposition         # 处理：退货/让步接收/返工/报废/降级
    disposition_qty
    reviewer / approver
    status              # 待处理/评审中/已处理/已关闭
```

**7.4 API 端点**
| 方法 | 端点 | 说明 |
|------|------|------|
| CRUD | `/quality/standards` | 检验标准管理 |
| POST | `/quality/inspect/{source_type}/{source_id}` | 发起检验 |
| POST | `/quality/ncr` | 开 NCR 单 |
| PUT | `/quality/ncr/{id}/dispose` | NCR 评审处理 |
| GET | `/quality/dashboard` | 质量看板（合格率趋势/缺陷分布/供应商质量） |

**7.5 联动逻辑**
- 采购收货 → 自动生成 IQC 检验任务（如果物料有 IQC 标准）
- 工单工序完成 → 自动生成 PQC 检验任务（如果 routing 标记了需要检验）
- 销售出货 → 自动生成 OQC 检验任务

---

## Phase 8 — 批次追溯与序列号

**目标**：实现物料从供应商到客户的完整追溯链路

### 现状
- `inventory_record.batch_no` 和 `inventory_transaction.batch_no` 字段存在但未使用
- 没有序列号（SN）管理

### 改动

**8.1 批次管理**
```python
class BatchRecord(Base):
    """批次主档"""
    batch_no            # 批次号（生成规则：YYYYMMDD-供应商-流水）
    item_id
    supplier_id         # 来源供应商
    po_id               # 来源采购单
    received_date
    expiry_date
    status              # 在库/已用尽/已冻结/已过期
```

**8.2 序列号管理**
```python
class SerialNumber(Base):
    """序列号追踪"""
    sn                  # 序列号
    item_id
    batch_no            # 关联批次
    status              # 在库/已出库/在制/已发货/已退货
    current_location    # 当前位置描述
    
class SerialNumberLog(Base):
    """序列号流转日志"""
    sn_id
    event_type          # 入库/领料/上机/完工/出货/退货
    reference_no        # 关联单号
    operator
    created_at
```

**8.3 追溯查询 API**

| 方法 | 端点 | 说明 |
|------|------|------|
| GET | `/trace/forward?batch_no=` | 正向追溯：批次→所有出库→客户 |
| GET | `/trace/backward?sn=` | 逆向追溯：序列号→所有历史→供应商 |
| GET | `/trace/batch-flow/{batch_no}` | 批次流转图（API 返回结构化数据，前端渲染 Sankey 图） |

**8.4 前端**
- 批次追溯页面：输入批次号/序列号，显示完整流转链路
- 物料卡片增加"批次详情"按钮

---

## Phase 9 — 现场执行与可视化

**目标**：生产现场可用的看板和操作界面，包括移动端扫码支持

### 9.1 生产看板

| 看板 | 内容 |
|------|------|
| 工序流转看板 | Kanban 视图：待开工/进行中/待检验/已完成 四列，可拖拽 |
| 产线状态看板 | 各工作中心当前负荷、正在生产的工单、预计完成时间 |
| OEE 看板 | 设备综合效率 = 时间利用率 × 性能效率 × 合格率 |
| 质量看板 | SPC 控制图、合格率趋势、TOP10 缺陷 |

**技术方案**：
- `el-table` + `el-card` + CSS Grid 实现看板布局
- 数据通过轮询刷新（5 秒间隔），后期可升级 WebSocket

### 9.2 OEE 计算
```
时间利用率 = (计划运行时间 - 停机时间) / 计划运行时间
性能效率   = (标准节拍 × 实际产量) / 实际运行时间
合格率     = 合格数 / 总产量
OEE        = 时间利用率 × 性能效率 × 合格率
```
- 数据来源：`WorkOrderReport`（产量）、`WorkOrderOperation`（时间）、`InspectionRecord`（合格数）
- `downtime_record` 表记录停机事件

### 9.3 移动端 PWA

不开发原生 App，用 PWA（Progressive Web App）覆盖核心场景：

| 场景 | 功能 | 交互 |
|------|------|------|
| 工序报工 | 扫描工单二维码 + 输入产量 | 两步操作 |
| 物料领用 | 扫描物料二维码 + 输入数量 | 两步操作 |
| 质检登记 | 扫描物料 + 勾选检验项 | 表单化 |
| 异常上报 | 扫工单码 + 选择异常类型 + 拍照 | 三步操作 |

**技术方案**：
- Vue 3 + Vite PWA 插件（`vite-plugin-pwa`）
- 移动端组件库 `vant`（与 Element Plus 共存，按路由加载）
- 二维码扫描用浏览器原生 `BarcodeDetector API`

### 9.4 异常安灯（Andon）
```python
class AndonEvent(Base):
    """安灯事件"""
    work_order_id / operation_id
    event_type          # 缺料/设备故障/质量问题/其他
    severity            # 红色（停线）/ 黄色（预警）/ 蓝色（请求）
    description
    handler             # 响应人
    response_time       # 响应时间
    resolve_time        # 解决时间
    status              # 待响应/处理中/已解决
```

---

## Phase 10 — 设备与模具管理

**目标**：设备台账、保养计划、模具寿命管理

### 现状
- `work_center` 表有 `machines_count` 字段，但没有设备级别的管理

### 改动

**10.1 设备台账**
```python
class Equipment(Base):
    """设备台账"""
    equipment_code      # 设备编码
    equipment_name
    model_spec          # 型号规格
    work_center_id      # 所属工作中心
    manufacturer
    purchase_date
    warranty_expiry
    status              # 运行中/停机/维修中/报废
```

**10.2 模具管理**
```python
class Tooling(Base):
    """模具/工装"""
    tooling_code
    tooling_name
    item_id             # 对应物料
    max_life            # 额定寿命（冲压次数等）
    current_life        # 当前已用寿命
    last_maintenance_date
    next_maintenance_date
    status
```

**10.3 保养计划**
```python
class MaintenancePlan(Base):
    """保养计划"""
    equipment_id / tooling_id
    plan_type           # 日保/周保/月保/年保
    description
    next_date
    status
```

---

## 各 Phase 预计工作量

| Phase | 主题 | 后端 | 前端 | 新表 | 说明 |
|:-----:|:-----|:---:|:---:|:---:|:-----|
| 6 | 工序级执行 | 新增 1 model, 6 endpoints | 工单详情页重构 | 1 | 对现有工单流程改动最大 |
| 7 | 质检体系 | 新增 3 models, 8 endpoints | 质检中心页 + NCR 弹窗 | 3 | 检验标准是基础建设 |
| 8 | 批次追溯 | 新增 3 models, 4 endpoints | 追溯查询页 + Sankey 图 | 3 | 追溯链路一打通，价值立刻体现 |
| 9 | 现场可视化 | 新增 2 models, 6 endpoints | 4 个看板 + PWA | 2 | 看板是"面子"，移动端是实用 |
| 10 | 设备模具 | 新增 4 models, 8 endpoints | 设备台账页 + 保养日历 | 4 | 并行性强，可独立开发 |
| **合计** | | **~13 新表, 32+ API** | | **13** | |

---

## 技术决策备忘

1. **工序执行用新表，不改原 work_order 流程** — 老的 `start`/`complete` 保留作为"快速模式"，工序模式通过 routing 触发
2. **PWA 不用独立项目** — 和主前端共享代码，`vite-plugin-pwa` + 路由级 `vant` 组件加载
3. **看板用 HTTP 轮询而非 WebSocket** — 单机部署不需要 WebSocket 的复杂度，5 秒轮询完全够
4. **序列号存储用独立表** — 不用 JSON 字段，保证查询和追溯效率
5. **每做完一个 Phase 本地测试 → 推 GitHub → Railway 部署** — 迭代节奏不变

---

> 下一步：请确认从 Phase 6（工序级工单执行）开始，还是调整优先级？
