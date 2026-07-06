# MRP II 物料需求计划系统 — 技术改进方案

> 撰写日期：2026-07-06
> 作者：Software Architect
> 版本：v1.0

---

## 一、系统现状概述

### 1.1 项目定位
MRP II 物料需求计划系统，覆盖制造业核心业务闭环——从销售订单、MPS 主生产计划、BOM 物料清单、MRP 物料需求运算，到采购管理、生产工单、库存管理、品质检验、成本核算、财务管理，共 **14 个数据模型、19 个前端页面、7 个业务服务**。

### 1.2 技术栈
| 层 | 技术 | 版本 |
|----|------|------|
| 前端框架 | Vue 3 + Pinia + Vue Router 4 | 3.4 |
| UI 库 | Element Plus + Tailwind CSS | 2.7 / 3.4 |
| 可视化 | ECharts | 5.5 |
| 后端框架 | FastAPI | 0.111 |
| ORM | SQLAlchemy 2.0 | 2.0 |
| 数据库 | MySQL 8.4 + pymysql | 8.4 |
| 认证 | JWT (python-jose) + bcrypt | — |
| 部署 | Docker + Railway | — |

### 1.3 成熟度评估

| 维度 | 评分 | 说明 |
|------|------|------|
| 领域覆盖 | ★★★★★★★★☆☆ 8/10 | MRP II 核心模块齐全，但缺少供应商管理、质量追溯 |
| 架构设计 | ★★★★★★★☆☆☆ 7/10 | 分层清晰，但存在全局变量、安全配置缺陷 |
| 代码质量 | ★★★★★★☆☆☆☆ 6/10 | 算法正确，但缺少测试、存在 N+1 查询、Python 版本兼容问题 |
| 测试覆盖 | ★☆☆☆☆☆☆☆☆☆ 1/10 | 改进前零测试，改进后核心引擎 23 个用例 |
| 安全合规 | ★★★★★☆☆☆☆☆ 5/10 | CORS 全开、JWT 密钥随机、无速率限制、无 SQL 注入审计 |
| 前端体验 | ★★★★★★★☆☆☆ 7/10 | 完成度高，但空 catch 较多、无 TypeScript |
| **综合** | ★★★★★★☆☆☆☆ **5.7/10** | 优秀的个人项目，距生产级尚有差距 |

---

## 二、已完成的改进（Phase 1）

### 2.1 P0 — 阻塞性缺陷

| 问题 | 严重度 | 方案 | 状态 |
|------|--------|------|------|
| `_last_mrp_result` 全局变量缓存 MRP 结果 | **P0** | 新建 `mrp_run_record` 表持久化到数据库 | ✅ 已完成 |
| 零测试覆盖 | **P0** | pytest 23 个用例覆盖 MRP 核心引擎 | ✅ 已完成 |

### 2.2 P1 — 重要缺陷

| 问题 | 严重度 | 方案 | 状态 |
|------|--------|------|------|
| CORS `allow_origins=["*"]` | **P1** | 改为白名单，通过 `CORS_ORIGINS` 环境变量配置 | ✅ 已完成 |
| JWT Secret 每次重启随机生成 | **P1** | 固定开发密钥 + 环境变量覆盖 + 日志警告 | ✅ 已完成 |
| `/api/materials/tree` N+1 查询（~300 次 SQL） | **P1** | 批量预加载（4 次 SQL）+ 内存组装 | ✅ 已完成 |
| 前端 `catch {}` 静默吞异常 | **P1** | 13 处空 catch 改为 `console.error('[MRP]', e)` | ✅ 已完成 |
| `horizon_days` 无范围校验 | **P1** | 限制 1~365 天 | ✅ 已完成 |
| `datetime.utcnow()` 已废弃 | **P1** | 替换为 `datetime.now(timezone.utc)` | ✅ 已完成 |
| 架构决策无记录 | **P1** | 4 份 ADR 文档记录关键决策上下文 | ✅ 已完成 |

---

## 三、待改进项（Phase 2 建议）

### 3.1 P2 — 应做项

#### 3.1.1 数据库迁移：SQLite → MySQL（生产环境）
- **现状**：Railway 部署使用 SQLite，不支持并发写入，MRP 定时任务与用户操作冲突时出现 `database is locked`
- **建议**：切换 Railway MySQL 插件，配置 `DATABASE_URL` 环境变量即可（代码已支持）
- **工作量**：极小（环境变量 + `init_db.py` 重跑）
- **收益**：高——消除并发写入瓶颈

#### 3.1.2 数据库迁移：裸 SQL → Alembic
- **现状**：`database.py` 中用 `init_db()` 执行裸 ALTER TABLE 做迁移，失败时 try/except 静默忽略
- **建议**：初始化 Alembic，将迁移脚本从 `init_db()` 迁移到 Alembic revision 中
- **工作量**：中（1-2 天，需要为每张表创建初始 migration + 后续增量 migration）
- **收益**：高——可逆迁移、团队协作、生产环境安全

#### 3.1.3 加入 CORS 和 `horizon_days` 校验后更新测试
- **现状**：P1 改动中 CORS、参数校验等边界逻辑无测试覆盖
- **建议**：为 `security.py` 和 `mrp.py` 的校验逻辑补测试
- **工作量**：小
- **收益**：中——防止回归

### 3.2 P3 — 建议做项

#### 3.2.1 物料树接口缓存
- **现状**：`/api/materials/tree` 每次请求都查数据库（虽然已从 ~300 次降到 4 次）
- **建议**：加 30 秒内存缓存（物料树不会秒级变化），或使用 ETag 实现条件请求
- **工作量**：小
- **收益**：中——减少数据库压力

#### 3.2.2 前端迁移到 TypeScript
- **现状**：19 个页面全部使用 JavaScript，无类型检查
- **建议**：从 `api/` 层开始逐步迁移到 `.ts`，定义 API 响应类型
- **工作量**：大（2-3 天渐进式迁移）
- **收益**：高——编译期捕获接口变更、更好的 IDE 支持

#### 3.2.3 API 响应统一格式
- **现状**：部分端点返回 `{success, message, data}`，部分直接返回 `{items, total}`，部分返回 `{item}`
- **建议**：统一为 `{success: bool, message: string, data: any}` 格式
- **工作量**：中
- **收益**：中——前端错误处理逻辑可简化

#### 3.2.4 全局错误边界（Frontend）
- **现状**：Vue 3 无全局 error handler，组件渲染错误会导致白屏
- **建议**：在 `main.js` 中配置 `app.config.errorHandler` + 增加 `<ErrorBoundary>` wrapper 组件
- **工作量**：小
- **收益**：高——避免白屏，提升用户体验

#### 3.2.5 分页参数硬编码
- **现状**：`InventoryList.vue` 中 `loadInventory` 使用 `page_size=1000`，实为无分页
- **建议**：改为真分页，后端可考虑游标分页（cursor-based pagination）
- **工作量**：中
- **收益**：中——数据量大时防 OOM

### 3.3 P4 — 可以考虑

| 建议 | 预期收益 | 工作量 |
|------|---------|--------|
| 前端 API 层错误集中处理（axios 拦截器已有点，可扩展自动 token 刷新） | 中 | 小 |
| 引入 Ruff 或 Pylint 做 Python 代码风格检查 | 低 | 小 |
| Docker Compose 本地开发环境（MySQL + 后端 + 前端一键启动） | 中 | 中 |
| MRP 运算历史记录管理页面（基于 `mrp_run_record` 表） | 中 | 中 |
| 物料主数据导入校验（Excel 导入增加数据完整性检查） | 中 | 中 |
| 操作日志 Audit Log（谁在什么时间改了什么） | 中 | 大 |
| CI/CD 加入自动化测试（GitHub Actions → pytest） | 高 | 小 |
| 前端 i18n 国际化 | 低 | 大 |

---

## 四、架构质量属性评估

### 4.1 可维护性
```
当前 → 6/10
```
**优势**：项目结构清晰（models/api/services 三层分离），Vue 3 composition API 使用正确，Pinia store 管理状态合理。

**短板**：无测试覆盖（已部分修复）、无 TypeScript、数据库迁移方式脆弱。

### 4.2 可扩展性
```
当前 → 7/10
```
**优势**：模块化单体架构适合当前团队规模，MRP 引擎的字典入参设计使其可独立测试和扩展。

**短板**：`scheduler.py` 耦合在单体中，未来若需独立部署 MRP 定时任务需抽取为独立服务。

### 4.3 可靠性
```
当前 → 5/10
```
**风险点**：
- 全局变量缓存（已修复 ✅）
- SQLite 并发写入（在生产环境中存在，已记录计划）
- 无熔断/重试策略（MRP 定时任务中数据库连接失败可能导致任务丢失）
- 前端无 error boundary

### 4.4 安全性
```
当前 → 5/10
```
**风险点**：
- CORS 全开（已修复 ✅）
- JWT 密钥随机（已修复 ✅）
- 无速率限制（API 可被暴力调用）
- 无 SQL 注入审计（SQLAlchemy ORM 基本安全，但 `init_db.py` 中的裸 SQL 有风险）
- 无 HTTPS 强制（Railway 默认提供，但应用层未做检查）

---

## 五、团队能力成长建议

从你的代码可以看出的成长方向：

| 当前能力 | 下阶段目标 | 建议路径 |
|----------|-----------|---------|
| 能实现功能 | 能设计可测试的功能 | 写测试 → 感受测试带来的安全感 → TDD |
| 用 Python 写后端 | 理解 Python 版本差异 | 阅读 Python 3.11/3.12 changelog，理解为什么 `utcnow()` 废弃 |
| 用 Vue 写页面 | 理解前端的错误管理 | 全局 error handler → 错误监控（Sentry） |
| 知道 N+1 问题 | 能从架构层面预防 | 学习 SQLAlchemy eager loading（joined/selectin/subquery） |
| 单人开发 | 多人协作思维 | 写 ADR、写测试、格式化代码、统一 API 规范 |

---

## 六、推荐的下一阶段工作顺序

```
优先          Phase 2A（1-2 天）
  ├── ① 生产环境切 MySQL → 消除并发瓶颈
  ├── ② Alembic 初始化 → 迁移可追溯
  └── ③ CORS/JWT/参数校验补测试 → 防止回归

建议          Phase 2B（3-5 天）
  ├── ④ API 响应格式统一
  ├── ⑤ 前端全局 error boundary
  ├── ⑥ 前端 TypeScript 渐进式迁移（从 api/ 开始）
  └── ⑦ GitHub Actions CI（自动跑测试）

考虑          Phase 2C（按需）
  ├── ⑧ Docker Compose 本地开发环境
  ├── ⑨ MRP 运行历史页面
  ├── ⑩ Audit Log 操作日志
  └── ⑪ 物料树缓存 + ETag
```

---

## 附录：改进后目录变更

```diff
  backend/app/
    ├── api/
    │   ├── mrp.py                   # [修改] 去掉 global 变量，改用数据库
    │   └── materials.py             # [修改] tree 端点 N+1 → 4 次查询
    ├── core/
    │   ├── security.py              # [修改] JWT 密钥 + utcnow 修复
    │   └── database.py              # [修改] 新增 mrp_run_record 迁移
    ├── models/
    │   ├── mrp_run_record.py        # [新增] MRP 运行记录模型
    │   └── __init__.py              # [修改] 导入 MrpRunRecord
+   tests/
+       └── test_mrp_calculator.py   # [新增] 23 个测试用例
+ docs/
+   └── adr/
+       ├── ADR-001-*.md
+       ├── ADR-002-*.md
+       ├── ADR-003-*.md
+       └── ADR-004-*.md

  frontend/src/
    ├── api/index.js                 # [未改] 已自动处理非401错误弹窗
    ├── App.vue                      # [修改] 3 处空 catch 修复
    ├── views/
    │   ├── Dashboard.vue            # [修改] 1 处空 catch
    │   ├── InventoryList.vue        # [修改] 1 处空 catch
    │   ├── Login.vue                # [修改] 1 处空 catch
    │   ├── MaterialList.vue         # [修改] 1 处空 catch
    │   ├── MpsList.vue              # [修改] 1 处空 catch
    │   ├── PermissionList.vue       # [修改] 3 处空 catch
    │   └── SalesList.vue            # [修改] 2 处空 catch
    └── components/
        └── PermissionOverlay.vue    # [修改] 1 处空 catch
```
