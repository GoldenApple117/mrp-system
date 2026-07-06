# ADR-001: MRP 运算结果缓存改用数据库存储

## Status
Accepted

## Context
MRP 运算结果通过 `POST /api/mrp/run` 生成，然后由 `POST /api/mrp/convert-to-orders` 消费，将计划建议转为实际采购单和工单。

原实现使用模块级全局变量 `_last_mrp_result` 作为两个端点之间的桥梁。这个方案存在三个问题：

1. **多 worker 下各自为政**：Uvicorn 启动多个 worker 时，每个进程持有独立的 `_last_mrp_result`，`convert-to-orders` 可能落在没有缓存的 worker 上
2. **重启丢失**：服务重启后缓存清空，需要用户重新跑 MRP
3. **不可观测**：运维无法通过数据库或 API 查看历史 MRP 运算结果

## Decision
新建 `MrpRunRecord` 模型和 `mrp_run_record` 表，将每次 MRP 运算的 `planned_orders` 以 JSON 格式持久化到数据库。

- `run_mrp` 端点在运算完成后将结果写入 `mrp_run_record` 表
- `convert-to-orders` 端点不再依赖全局变量，改为按 `id DESC` 查询最近一条记录
- 保留前端显式传入 `planned_orders` 的能力（覆盖自动模式）

## Consequences
**更容易：**
- 多 worker 下行为一致，任意 worker 都能正确转换
- 服务重启后不丢失上一条 MRP 结果
- 可通过数据库直接查看历史的 `planned_orders` 快照
- 为后续 MRP 运行历史页面打下基础

**更困难：**
- MRP 运算结果现在占用数据库存储（每个运行记录约数 KB 到数十 KB）
- 未引入自动清理机制，长期运行会累积历史记录
