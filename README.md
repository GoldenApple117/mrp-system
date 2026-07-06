# MRP II 物料需求计划管理系统

> 基于 Python FastAPI + Vue 3 的全栈 MRP II 系统，为"三工位测试台"项目提供物料需求计划、采购管理、生产管理和库存管理能力。

[![version](https://img.shields.io/badge/version-1.7.0-blue)](https://github.com/GoldenApple117/mrp-system)
[![Python](https://img.shields.io/badge/python-3.11-3776AB)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.111-009688)](https://fastapi.tiangolo.com/)
[![Vue](https://img.shields.io/badge/vue-3.4-42b883)](https://vuejs.org/)
[![MySQL](https://img.shields.io/badge/MySQL-8.0-4479A1)](https://www.mysql.com/)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)

---

## 📋 目录

- [在线地址](#-在线地址)
- [功能概览](#-功能概览)
- [技术栈](#-技术栈)
- [系统架构](#-系统架构)
- [快速开始](#-快速开始)
- [用户指南](#-用户指南)
- [API 接口](#-api-接口)
- [测试指南](#-测试指南)
- [部署与运维](#-部署与运维)
- [架构决策记录](#-架构决策记录)
- [常见问题](#-常见问题)
- [数据规模](#-数据规模)

---

## 🌐 在线地址

| 环境 | 地址 |
|------|------|
| **生产系统** | [https://mrp-system-production.up.railway.app](https://mrp-system-production.up.railway.app) |
| **API 文档** | [https://mrp-system-production.up.railway.app/docs](https://mrp-system-production.up.railway.app/docs) |
| **GitHub** | [https://github.com/GoldenApple117/mrp-system](https://github.com/GoldenApple117/mrp-system) |

---

## 🎯 功能概览

| 模块 | 说明 |
|------|------|
| 🔐 **JWT 认证** | `admin` / `normal` 双角色，密码 bcrypt 哈希，Token 24h 过期 |
| 👥 **权限管理** | 普通用户申请 + 管理员审批，未授权页面遮罩保护 |
| 📦 **物料管理** | 189 种物料，含编码/名称/规格/品牌/单价/采购链接 |
| 🏗️ **BOM 管理** | 6 大模块 177 行 BOM，支持 Excel 导入 + 金山文档在线导入 + 版本管理 |
| 📊 **MPS 主计划** | 成品级生产计划录入，支持批量添加 |
| 🧮 **MRP 运算** | LLC 低保码分层展开，净需求计算，批量规则（LFL/FOQ/EOQ/MULT），生成采购/生产建议 |
| 🛒 **采购管理** | PO 全生命周期（申请→审批→下单→收货），品牌/单价/链接自动同步 |
| 🏭 **生产管理** | 工单全流程（待下达→已下达→进行中→已完成），支持 CRP 产能计算 |
| 📈 **报表分析** | ECharts 可视化：库存按模块、工单状态分布、低库存预警、OTD 准时率 |
| 📬 **邮件通知** | 定时 MRP 后自动发送 HTML 报告（SMTP 可配置） |
| ⏰ **定时 MRP** | APScheduler 每日自动运算 + 转采购申请 |
| 💰 **费用合计** | 按模块统计 BOM 采购成本 |
| 📋 **例外看板** | MRP 运算异常集中展示，支持标记已处理/批量清理 |
| 🔍 **搜索面板** | 全局物料搜索，快捷键 `Ctrl+K` |
| 📥 **数据导入** | Excel 导入、金山文档在线导入、原始 JSON 导入 |

---

## 🛠️ 技术栈

| 层级 | 技术 |
|------|------|
| **后端框架** | FastAPI 0.111 + Uvicorn |
| **ORM** | SQLAlchemy 2.0（连接池 20 + pool_pre_ping） |
| **数据库** | MySQL 8.0（生产）/ SQLite（本地开发） |
| **认证** | JWT（python-jose）+ bcrypt 4.0.1 |
| **定时任务** | APScheduler 3.10（CronTrigger，默认 06:00） |
| **前端框架** | Vue 3.4 + Vite 5.4 |
| **UI 组件** | Element Plus 2.7 + Tailwind CSS 3.4 |
| **图表** | ECharts 5.5（库存概览/工单状态/低库存预警/OTD） |
| **状态管理** | Pinia 2.1 |
| **数据导入** | openpyxl + 金山文档 MCP 连接器 |
| **数据库迁移** | Alembic（自动执行） |
| **部署** | Docker 多阶段构建 + Railway |

---

## 🏗️ 系统架构

```
┌─────────────────────────────────────────────────────────────────────┐
│                    🖥️ 前端 (Vue 3 + Element Plus + Pinia)           │
│  Login(独立页)  Dashboard  Materials  BOM  Inventory  MPS  MRP     │
│  Purchase  Production  CRP  Reports  Cost  Finance  Exceptions     │
│  Permissions  Inspection  Routing  Suppliers                       │
│                    ↓ Axios (Bearer Token + 401拦截)                 │
├─────────────────────────────────────────────────────────────────────┤
│                     ⚙️ 后端 (Python FastAPI)                        │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │  API 路由层 (18 个模块，全部 require_approved)                │   │
│  │  auth / materials / bom / inventory / mps / mrp / purchase   │   │
│  │  production / crp / inspection / sales / cost / finance      │   │
│  │  exceptions / permissions / system / routing / suppliers     │   │
│  └─────────────────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │  安全层: get_current_user → require_approved → 业务逻辑      │   │
│  │  JWT Token (24h) + bcrypt 密码哈希 + CORS 白名单             │   │
│  └─────────────────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │  服务层: MRP Calculator / CRP Calculator / BOM Exploder     │   │
│  │          Scheduler (APScheduler) / Notifier (SMTP)          │   │
│  └─────────────────────────────────────────────────────────────┘   │
├─────────────────────────────────────────────────────────────────────┤
│                    🗄️ 数据库 (MySQL 8.0 / SQLite)                   │
│  15+ 个模型: User, MaterialMaster, BomHeader/Line, Inventory,      │
│  MpsEntry, PurchaseOrder, WorkOrder, WorkCenter, Routing,           │
│  Supplier, InspectionRecord, MrpException, MrpRunRecord, etc.       │
└─────────────────────────────────────────────────────────────────────┘
```

### 目录结构

```
mrp-system/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI 入口 + 路由注册 + CORS
│   │   ├── core/
│   │   │   ├── config.py        # 数据库配置(MYSQL_URL / .env)
│   │   │   ├── database.py      # SQLAlchemy + 连接池 + Alembic + 自动迁移
│   │   │   └── security.py      # JWT签发/验证 + bcrypt密码哈希
│   │   ├── models/              # 数据模型 (SQLAlchemy ORM)
│   │   ├── api/                 # API 路由 (18 个模块)
│   │   ├── services/            # 业务服务层
│   │   │   ├── mrp_calculator.py    # MRP 核心引擎 (LLC分层/净需求/批量规则)
│   │   │   ├── crp_calculator.py    # CRP 产能计算
│   │   │   ├── bom_exploder.py      # BOM 展开
│   │   │   ├── scheduler.py         # APScheduler 定时任务
│   │   │   ├── notifier.py          # SMTP 邮件通知
│   │   │   ├── excel_importer.py    # Excel 导入
│   │   │   └── kdocs_importer.py    # 金山文档导入
│   │   └── schemas/             # Pydantic 数据模式
│   ├── alembic/                 # 数据库迁移
│   ├── tests/                   # 单元测试 (30 个)
│   └── requirements.txt
├── frontend/
│   └── src/
│       ├── views/               # 18 个 Vue 页面
│       ├── components/          # 可复用组件 (NavGroup/KpiCard/StatusRow等)
│       ├── stores/              # Pinia 状态管理
│       └── router/              # 路由 + beforeEach 守卫
├── docs/
│   └── adr/                     # 架构决策记录 (ADR)
├── Dockerfile                   # 多阶段构建
├── railway.json                 # Railway 配置
├── start.sh                     # 容器启动脚本
├── init_db.py                   # 生产数据库初始化
└── README.md
```

---

## 🚀 快速开始

### 本地开发

```bash
# 1. 启动后端
cd backend
pip install -r requirements.txt
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload

# 2. 启动前端（可选，后端自带编译后的前端文件）
cd frontend
npm install && npm run dev
```

- **前端**：http://localhost:5173
- **后端**：http://localhost:8000
- **API 文档**：http://localhost:8000/docs
- **默认账号**：`admin` / `admin123`

### 数据库配置

| 模式 | 配置 |
|------|------|
| **本地开发** | 默认 SQLite（`backend/app.db`）；设置 `set DB_BACKEND=mysql` 切换 MySQL |
| **环境变量** | `DATABASE_URL` 或 `MYSQL_URL` 自动识别；MySQL 需 `mysql+pymysql://` 前缀 |

### 一键启动（开发环境）

项目根目录有 `start-dev.bat`，双击即可同时启动 MySQL + 后端 + 前端。

---

## 📖 用户指南

### 登录与权限

| 角色 | 默认账号 | 说明 |
|------|----------|------|
| **管理员** | `admin` / `admin123` | 全部功能 + 审批权限 |
| **普通用户** | `user1` / `123456`（未授权） | 需管理员审批后方可操作 |

**权限申请流程**：
1. 普通用户登录后，页面内容区显示半透明遮罩
2. 点击遮罩上的「申请权限」按钮
3. 管理员顶部导航栏出现红色角标
4. 管理员进入权限管理页 → 同意/拒绝
5. 审批通过后用户刷新页面即可正常使用

### 操作流程

```
MPS 录入（成品需求）
    ↓
BOM 展开（LLC 分层）
    ↓
MRP 运算（净需求 + 批量规则 + 提前期倒推）
    ↓
生成采购建议 / 生产建议
    ↓
一键转为采购申请 / 生产工单
    ↓
采购管理（申请→审批→下单→收货）
生产管理（下达→开工→完工）
库存管理（入库→出库→盘点）
```

### 各模块操作说明

| 模块 | 操作步骤 |
|------|----------|
| **仪表盘** | 登录后默认进入，显示 KPI 卡片、库存概览图、工单状态分布、低库存预警列表 |
| **物料管理** | 左侧菜单进入，支持搜索、新建、编辑、查看树状结构 |
| **BOM 管理** | 查看产品结构树，支持 Excel 导入、金山文档导入、版本管理 |
| **MPS 主计划** | 点击「添加计划」→ 选择成品 → 填写日期/数量 → 保存 |
| **MRP 运算** | 进入 MRP 页面 → 点「一键 MRP 运算」→ 查看结果 → 「一键转为采购申请」 |
| **采购管理** | 查看/管理采购订单，状态流转：申请→已审批→已下单→部分收货→已完成 |
| **生产管理** | 查看/管理工单，状态流转：待下达→已下达→进行中→已完成 |
| **库存管理** | 查看库存，执行入库/出库操作 |
| **例外看板** | 集中展示 MRP 运算产生的异常（缺料/逾期/安全库存），支持标记已处理 |
| **系统工具** | 配置定时 MRP、邮件通知、导出数据 |

### 邮件通知配置

| 字段 | QQ 邮箱示例 |
|------|-------------|
| 收件邮箱 | `your@qq.com` |
| SMTP 服务器 | `smtp.qq.com` |
| 端口 | `587` |
| 用户名 | `your@qq.com` |
| 密码 | QQ邮箱授权码（16位） |

> 授权码获取：QQ邮箱 → 设置 → 账户 → POP3/SMTP服务 → 开启 → 生成授权码

---

## 📡 API 接口

完整 API 文档请访问 `/docs`（Swagger UI）。

### 认证

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/auth/login` | 登录，返回 JWT Token |
| GET | `/api/auth/me` | 获取当前用户信息 |
| POST | `/api/auth/logout` | 登出 |

### 核心业务

| 模块 | 路径前缀 | 主要端点 |
|------|----------|----------|
| 物料 | `/api/materials` | CRUD + `/tree`（物料树）、`/all`（全量） |
| BOM | `/api/bom` | CRUD + `/tree/{id}` 展开、`/import/excel`、`/import/kdocs`、版本管理 |
| 库存 | `/api/inventory` | CRUD + `/summary`、`/low-stock` |
| MPS | `/api/mps` | CRUD + 批量添加 |
| MRP | `/api/mrp` | `POST /run`（运算）、`POST /convert-to-orders`（转单） |
| 采购 | `/api/purchase` | PO 全生命周期 CRUD |
| 生产 | `/api/production` | 工单 CRUD + 状态流转 |
| CRP | `/api/crp` | `POST /calculate` 产能计算 |
| 例外 | `/api/exceptions` | 查询/标记/批量清理 MRP 例外 |

### 系统管理

| 方法 | 路径 | 说明 |
|------|------|------|
| GET/PUT | `/api/system/schedule` | 定时 MRP 配置 |
| GET/PUT | `/api/system/email-config` | SMTP 邮件配置 |
| POST | `/api/system/schedule/run-now` | 立即执行定时 MRP |
| POST | `/api/system/email-test` | 发送测试邮件 |

### MRP 核心算法

````
MPS(成品需求)
  → BOM展开(递归/LLC分层)
  → 逐层计算低保码(LLC)
  → 毛需求汇总
  → 扣除库存(现有库存 - 已分配 - 已预留)
  → 净需求判断(低于安全库存 → 需要下达)
  → 替代料检查(若有替代料组，优先消耗替代料库存)
  → 批量规则应用:
      LFL(按需定量) / FOQ(固定批量) / EOQ(经济批量) / MULT(倍数批量)
  → 提前期倒推(下达日 = 需求日 - 提前期)
  → 例外识别(缺料/逾期/安全库存预警)
  → 输出采购建议(PURCHASE) + 生产建议(PRODUCTION)
````

---

## 🧪 测试指南

### 运行测试

```bash
cd backend
python -m pytest tests/ -v
# 30 个测试：23 个 MRP 引擎 + 7 个安全配置
```

### 快速验证 API

```bash
# 1. 登录
curl -s -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}'

# 2. 保存 Token
TOKEN="<上一步返回的 access_token>"

# 3. 测试各模块
curl -s http://localhost:8000/api/materials -H "Authorization: Bearer $TOKEN"
curl -s http://localhost:8000/api/bom -H "Authorization: Bearer $TOKEN"
curl -s http://localhost:8000/api/mps -H "Authorization: Bearer $TOKEN"
curl -s http://localhost:8000/api/inventory -H "Authorization: Bearer $TOKEN"

# 4. 执行 MRP
curl -s -X POST http://localhost:8000/api/mrp/run \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"horizon_days": 90}'

# 5. 健康检查
curl http://localhost:8000/api/health
```

### 权限测试

```bash
ADMIN_TOKEN=$(curl -s -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}' | python -c "import sys,json;print(json.load(sys.stdin)['access_token'])")

USER_TOKEN=$(curl -s -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"user1","password":"123456"}' | python -c "import sys,json;print(json.load(sys.stdin)['access_token'])")

# user1 访问业务 API → 403
curl -s http://localhost:8000/api/mps -H "Authorization: Bearer $USER_TOKEN"

# user1 申请权限
curl -s -X POST http://localhost:8000/api/permissions/request \
  -H "Authorization: Bearer $USER_TOKEN"

# admin 审批
curl -s http://localhost:8000/api/permissions/pending-count \
  -H "Authorization: Bearer $ADMIN_TOKEN"
curl -s -X PUT http://localhost:8000/api/permissions/approve/1 \
  -H "Authorization: Bearer $ADMIN_TOKEN"
```

---

## 🚢 部署与运维

### Docker 构建

```bash
docker build -t mrp-system .
```

多阶段构建流程：
1. **Stage 1** (`node:20-alpine`)：前端编译 → `frontend/dist/`
2. **Stage 2** (`python:3.11-slim`)：Python 依赖安装 → `uvicorn` 启动

### Railway 部署

项目已配置 `railway.json` 和 `Dockerfile`，推送到 GitHub 后 Railway 自动部署。

**生产环境必须设置的环境变量**：

| 变量名 | 用途 | 示例 |
|--------|------|------|
| `JWT_SECRET_KEY` | JWT Token 签名密钥 | `MRP-Prod-2026-S3cur3-K3y!` |
| `MYSQL_URL` | MySQL 连接串（使用 Railway MySQL 插件时自动注入） | `mysql://root:xxx@mysql.railway.internal:3306/railway` |

### 本地 MySQL 配置

| 项目 | 说明 |
|------|------|
| 版本 | MySQL 8.4.9 |
| 端口 | 3306 |
| root 密码 | `root` |
| 数据目录 | `D:\MySQL_Server_8.4\data` |
| 启动方式 | `start-mysql.bat`（免安装 standalone 模式） |

---

## 📐 架构决策记录

项目采用 ADR（Architecture Decision Record）记录关键技术决策：

| ADR | 标题 | 决策 |
|-----|------|------|
| [ADR-001](docs/adr/ADR-001-mrp-cache-to-database.md) | MRP 缓存从全局变量改为数据库持久化 | 用 `mrp_run_record` 表替代 Python 全局变量，支持多实例部署 |
| [ADR-002](docs/adr/ADR-002-mrp-engine-tests.md) | MRP 引擎单元测试策略 | 23 个 Pytest 测试覆盖核心算法，使用 SQLite 内存数据库 |
| [ADR-003](docs/adr/ADR-003-cors-and-jwt-security.md) | CORS 白名单和 JWT 安全加固 | CORS 从 `allow_origins=["*"]` 改为环境变量白名单；JWT 密钥生产环境必设 |
| [ADR-004](docs/adr/ADR-004-materials-tree-n-plus-one.md) | 物料树 N+1 查询优化 | 从 ~300 次 SQL 查询优化到 4 次批量查询，响应时间从秒级降到毫秒级 |

---

## ❓ 常见问题

### Q1：登录提示"用户名或密码错误"
确认用户名密码正确。默认管理员 `admin` / `admin123`。

### Q2：普通用户登录后看不到数据
普通用户默认无权限，需点击遮罩上的「申请权限」按钮，等待管理员审批。

### Q3：MRP 运算没有结果
需要先在「MPS 主计划」录入成品需求计划，MRP 才能基于 MPS 进行计算。

### Q4：MRP 运算返回 500
检查 `mrp_run_record` 表的 `planned_orders_json` 列是否为 `LONGTEXT` 类型。
MySQL TEXT 类型上限 65KB，生产环境约 135KB，需用 LONGTEXT（4GB）。

### Q5：授权码是什么？
授权码是邮箱服务商为第三方应用颁发的专用密码，不是邮箱登录密码。
QQ 邮箱在「设置 → 账户 → POP3/SMTP 服务」中生成。

### Q6：定时 MRP 怎么不执行？
检查系统工具的「启用」开关是否打开，时间设置是否正确。

### Q7：怎么备份数据？
点击系统工具 → 导出，下载 JSON 备份文件。数据库层面可备份 `backend/app.db`（SQLite）或导出 MySQL dump。

### Q8：本地开发如何切换数据库？
设置环境变量 `DB_BACKEND=sqlite` 或 `DB_BACKEND=mysql`，系统自动识别。

---

## 📊 数据规模

| 指标 | 数量 |
|------|:----:|
| 物料 | 189 |
| BOM 行 | 177 |
| 模块 | 6（外购件/外加工件/电气/视觉/量具/成品） |
| 库存记录 | 178（总库存 ~21,502） |
| MPS 计划 | 10 |
| 采购订单 | 按需生成 |
| 用户 | 2（admin + user1） |
| MRP 例外记录 | 按需生成 |

---

> **在线系统**：[https://mrp-system-production.up.railway.app](https://mrp-system-production.up.railway.app)  
> **源代码**：[https://github.com/GoldenApple117/mrp-system](https://github.com/GoldenApple117/mrp-system)  
> **作者**：GoldenApple117  
> **许可**：MIT
