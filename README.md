# MRP II 物料需求计划管理系统

> 基于 Python FastAPI + Vue 3 的全栈 MRP II 系统，为"三工位测试台"项目提供物料需求计划、采购管理、生产管理和库存管理能力。

![版本](https://img.shields.io/badge/version-1.7.0-blue)
![Python](https://img.shields.io/badge/python-3.13-3776AB)
![Vue](https://img.shields.io/badge/vue-3.4-42b883)
![License](https://img.shields.io/badge/license-MIT-green)

**在线地址**：[https://mrp-system-production.up.railway.app](https://mrp-system-production.up.railway.app)

---

## 功能概览

| 模块 | 说明 |
|------|------|
| 🔐 JWT 登录 | admin/normal 双角色，密码 bcrypt 哈希 |
| 👥 权限管理 | 普通用户申请 + 管理员审批，未授权页面遮罩 |
| 📦 物料管理 | 179 种物料的编码/名称/规格/品牌/价格/采购链接 |
| 🏗️ BOM 管理 | 5 大模块 177 行 BOM，支持 Excel 导入 + 金山文档导入 |
| 📊 MPS 主计划 | 成品级生产计划，支持批量添加 |
| 🧮 MRP 运算 | LLC 分层净需求计算，自动生成采购/生产建议 |
| 🛒 采购管理 | PO 全生命周期 + 品牌/价格/链接自动同步 |
| 🏭 生产管理 | 工单下达/开工/完工全流程 |
| 📈 报表分析 | ECharts 可视化：库存按模块、工单状态、低库存预警 |
| 📬 邮件通知 | 定时 MRP 后自动发送结果报告（SMTP 可配） |
| ⏰ 定时 MRP | APScheduler 每日自动运算 + 转 PO |
| 💰 费用合计 | 按模块统计 BOM 采购成本 |

---

## 技术栈

| 层级 | 技术 |
|------|------|
| 后端框架 | FastAPI 0.111 + Uvicorn |
| ORM | SQLAlchemy 2.0 |
| 数据库 | MySQL 8.0 (默认) / SQLite |
| 认证 | JWT (python-jose) + bcrypt |
| 定时任务 | APScheduler 3.10 |
| 前端框架 | Vue 3.4 + Vite |
| UI 组件 | Element Plus 2.7 + Tailwind CSS |
| 图表 | ECharts 5.5 |
| 状态管理 | Pinia 2.1 |
| 数据导入 | openpyxl + 金山文档 MCP 连接器 |

---

## 快速开始

```bash
# 后端
cd backend
pip install -r requirements.txt
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# 前端
cd frontend
npm install && npm run dev
```

访问 `http://localhost:5173`，默认账号 **admin / admin123**

---

## 项目结构

```
mrp-system/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI 入口 + 路由注册
│   │   ├── core/                 # 配置 / 数据库 / JWT安全
│   │   ├── models/               # 14 个数据模型
│   │   ├── api/                  # 17 个 API 模块
│   │   └── services/             # MRP 调度器 / 邮件通知
│   └── requirements.txt
├── frontend/
│   └── src/
│       ├── views/                # 18 个 Vue 页面
│       ├── components/           # 可复用组件
│       ├── stores/               # Pinia 状态管理
│       └── router/               # 路由 + 守卫
├── docs/                         # 开发文档 / 用户手册 / 测试指南
├── Dockerfile
└── railway.json
```

---

## 部署

```bash
# Docker 多阶段构建（Railway 支持）
docker build -t mrp-system .

# 环境变量
DB_BACKEND=sqlite          # Railway 用 sqlite
JWT_SECRET_KEY=xxx         # 生产环境必设
```

---

## 当前数据规模

| 指标 | 数量 |
|------|------|
| 物料 | 179 |
| BOM 行 | 177 |
| 模块 | 6（外购件/外加工件/电气/视觉/量具/成品）|
| 库存记录 | 178（总库存 21,502）|
| MPS 计划 | 3 |

---

> **GitHub**: [GoldenApple117/mrp-system](https://github.com/GoldenApple117/mrp-system)
