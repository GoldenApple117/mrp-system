# ADR-002: MRP 核心引擎单元测试

## Status
Accepted

## Context
MRP 计算引擎 `MrpCalculator` 是系统的核心——它负责低保码计算、净需求计算、批量规则应用、BOM 多层展开、替代料处理、损耗率计算等关键逻辑。任何一处边界条件错误都可能导致采购建议偏差，造成真金白银的损失。

原项目零测试覆盖，重构或新增功能时只能靠手动点页面验证，不可重复且容易遗漏。

## Decision
新建 `backend/tests/test_mrp_calculator.py`，用 pytest 编写 23 个测试用例，覆盖三个核心方法：

- **`compute_low_level_codes`**（7 个用例）：单层/多层 BOM、共享零件（取最大深度）、复杂 BOM、空 BOM、无效输入
- **`apply_lot_sizing`**（7 个用例）：LFL/FOQ/EOQ/MULT 四种批量规则、最小/最大订单量限制、0 批量退化、未知规则退化
- **`calculate`**（9 个用例）：无 MPS 空结果、简单生产、库存扣减、批量规则集成、在途订单抵扣、安全库存告警、三层 BOM 幻影穿透、损耗率放大、逾期订单检测

`MrpCalculator` 的 `calculate()` 方法接收纯字典参数，不依赖数据库 session，天然可测试。

## Consequences
**更容易：**
- 任何 MRP 引擎修改后运行 `pytest tests/ -v` 即可验证，防止回归
- 测试用例本身就是算法行为的活文档
- 新增特性时先写测试再实现（TDD 循环可逐步引入）

**更困难：**
- 需要维护测试数据与生产数据模型的一致性
- 当前测试覆盖了核心算法，但未覆盖 MRP API 端点的集成测试（依赖真实数据库）
