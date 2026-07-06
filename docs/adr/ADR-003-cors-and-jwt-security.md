# ADR-003: CORS 白名单与安全加固

## Status
Accepted

## Context
原项目在生产环境（Railway）和本地开发环境中均使用 `allow_origins=["*"]`，允许任意跨域来源访问 API。虽然在 Railway 部署时前端由后端同源代理可缓解风险，但本地开发时前端运行在 `localhost:5173`，后端在 `localhost:8000`，跨域请求是开放的。

同时，JWT 密钥使用了 `os.getenv("JWT_SECRET_KEY") or secrets.token_hex(32)` 作为 fallback，每次进程启动生成新密钥，导致：
1. 服务重启后所有已签发 token 失效（用户需要重新登录）
2. 多 worker 环境各 worker 密钥不一致，token 验证失败

## Decision
**CORS**：将 `["*"]` 改为从 `CORS_ORIGINS` 环境变量读取，默认值为 `http://localhost:5173,http://localhost:8000`。本地开发无需额外配置，生产环境通过 Railway 环境变量或 Nginx 白名单控制。

**JWT Secret**：去掉随机 fallback，改用固定开发密钥 `mrp-system-dev-secret-key-do-not-use-in-production`，并输出日志警告。生产环境通过 `JWT_SECRET_KEY` 环境变量覆盖。

**参数校验**：为 `horizon_days` 增加 `[1, 365]` 范围限制，`time_fence_days` 增加 `[0, 30]` 范围限制。

## Consequences
**更容易：**
- 本地开发重启后端不再踢出已登录用户
- 多 worker 行为一致
- CORS 策略可通过环境变量自定义，无需改代码

**更困难：**
- 开发人员需要意识到 `CORS_ORIGINS` 环境变量的存在（默认值覆盖 90% 场景）
- 开发密钥日志警告可能被忽视（已用 `WARNING` 级别日志）
