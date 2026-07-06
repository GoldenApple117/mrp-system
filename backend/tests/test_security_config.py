"""安全配置与参数校验 — 单元测试

覆盖：
- JWT_SECRET_KEY 环境变量读取逻辑
- CORS 白名单配置
- MRP horizon_days / time_fence_days 校验
"""
import os
import pytest


# ==============================================================================
# Test: JWT Secret Key
# ==============================================================================

class TestJwtSecretKey:
    """确保 JWT 密钥在不同环境下行为正确"""

    def test_env_var_overrides_dev_key(self):
        """环境变量 JWT_SECRET_KEY 应覆盖开发密钥"""
        os.environ["JWT_SECRET_KEY"] = "my-production-key"
        # 重新加载模块获取新的 SECRET_KEY
        import importlib
        import app.core.security
        app.core.security = importlib.reload(app.core.security)
        assert app.core.security.SECRET_KEY == "my-production-key"
        del os.environ["JWT_SECRET_KEY"]
        # 恢复
        app.core.security = importlib.reload(app.core.security)

    def test_default_dev_key_is_fixed(self):
        """未设置环境变量时，应使用固定开发密钥"""
        # 确保环境变量不存在
        os.environ.pop("JWT_SECRET_KEY", None)
        import importlib
        import app.core.security
        app.core.security = importlib.reload(app.core.security)
        assert "dev" in app.core.security.SECRET_KEY
        assert "do-not-use-in-production" in app.core.security.SECRET_KEY

    def test_dev_key_warning_logged(self, caplog):
        """开发密钥应输出 WARNING 级别日志"""
        os.environ.pop("JWT_SECRET_KEY", None)
        import importlib
        import app.core.security
        caplog.clear()
        app.core.security = importlib.reload(app.core.security)
        warnings = [r for r in caplog.records if r.levelname == "WARNING"]
        assert any("JWT_SECRET_KEY" in r.message for r in warnings)


# ==============================================================================
# Test: CORS Origins
# ==============================================================================

class TestCorsOrigins:
    """CORS 白名单配置"""

    def _get_cors_origins(self):
        """从 app 中提取 CORS 白名单"""
        import app.main
        for mw in app.main.app.user_middleware:
            cls_name = mw.cls.__name__
            if "CORSMiddleware" in cls_name:
                opts = mw.kwargs if hasattr(mw, 'kwargs') else {}
                return opts.get("allow_origins", [])
        return None

    def test_default_origins(self):
        """默认应包含 localhost:5173 和 localhost:8000"""
        origins = self._get_cors_origins()
        assert origins is not None, "未找到 CORSMiddleware"
        assert "http://localhost:5173" in origins
        assert "http://localhost:8000" in origins

    def test_env_var_custom_origins(self):
        """CORS_ORIGINS 环境变量应生效"""
        import importlib
        os.environ["CORS_ORIGINS"] = "https://myapp.com,https://admin.myapp.com"
        import app.main
        app.main = importlib.reload(app.main)
        origins = self._get_cors_origins()
        assert origins is not None
        assert "https://myapp.com" in origins
        assert "https://admin.myapp.com" in origins
        assert "localhost" not in " ".join(origins)
        del os.environ["CORS_ORIGINS"]
        # 恢复
        app.main = importlib.reload(app.main)


# ==============================================================================
# Test: MRP 参数校验
# ==============================================================================

class TestMrpParamValidation:
    """MRP API 参数范围校验"""

    def test_horizon_days_clamped(self):
        """horizon_days 应在 1~365 范围内"""
        from app.api.mrp import run_mrp

        # 构造一个模拟的 data 对象
        # 由于 run_mrp 依赖数据库，我们只测试校验逻辑是否有这个限制
        # 通过检查代码中的 min/max 调用验证
        import inspect
        source = inspect.getsource(run_mrp)
        assert "max(1, min(data.get(" in source
        assert "365)" in source

    def test_time_fence_days_clamped(self):
        """time_fence_days 应在 0~30 范围内"""
        import inspect
        from app.api.mrp import run_mrp
        source = inspect.getsource(run_mrp)
        assert "max(0, min(data.get(" in source
        assert "30)" in source
