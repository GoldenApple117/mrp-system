"""认证依赖注入 — get_current_user, require_approved, require_module"""
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import verify_access_token
from app.models.user import User
from app.models.permission import UserModulePermission

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=False)


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    """从请求头 Bearer token 中解析当前登录用户"""
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="请先登录")
    payload = verify_access_token(token)
    if not payload:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="登录已过期，请重新登录")
    username = payload.get("sub")
    if not username:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="无效的凭证")
    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="用户不存在")
    return user


def require_approved(current_user: User = Depends(get_current_user)):
    """权限检查：管理员直接通过，普通用户需已授权"""
    if current_user.role == "admin":
        return current_user
    if not current_user.is_approved:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="您的权限尚未通过审批，请联系管理员"
        )
    return current_user


MODULE_LABELS = {
    "materials": "物料管理", "bom": "BOM管理",
    "inventory": "库存管理", "routings": "工艺路线",
    "mps": "MPS主计划", "mrp": "MRP运算", "crp": "CRP计划",
    "sales": "销售管理", "purchase": "采购管理",
    "production": "生产管理", "inspection": "检验盘点",
    "cost": "成本管理", "finance": "财务管理",
    "exceptions": "异常看板",
}


def require_module(module_name: str):
    """工厂函数：返回一个 Depends，检查用户是否有指定模块的访问权限。
    - admin 角色不做限制
    - normal 用户必须已在 user_module_permission 表中被授予该模块
    """
    def checker(
        current_user: User = Depends(require_approved),
        db: Session = Depends(get_db),
    ):
        if current_user.role == "admin":
            return current_user
        perm = db.query(UserModulePermission).filter(
            UserModulePermission.user_id == current_user.id,
            UserModulePermission.module_name == module_name
        ).first()
        if not perm:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"无【{MODULE_LABELS.get(module_name, module_name)}】模块的访问权限，请联系管理员"
            )
        return current_user
    return checker
