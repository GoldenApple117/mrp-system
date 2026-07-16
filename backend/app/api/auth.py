"""认证 API — 登录/登出/当前用户"""
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import create_access_token, verify_password
from app.models.user import User
from app.models.permission import UserModulePermission
from app.api.deps import get_current_user, MODULE_LABELS

router = APIRouter(prefix="/api/auth", tags=["认证"])


class LoginRequest(BaseModel):
    username: str
    password: str


class UserInfo(BaseModel):
    id: int
    username: str
    role: str
    is_approved: bool = True

    class Config:
        from_attributes = True


@router.post("/login")
def login(req: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == req.username).first()
    if not user or not verify_password(req.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="用户名或密码错误")

    token = create_access_token({"sub": user.username, "role": user.role, "approved": bool(user.is_approved)})

    # 查询用户的模块权限
    if user.role == "admin":
        module_perms = list(MODULE_LABELS.keys())
    else:
        perms = db.query(UserModulePermission).filter(
            UserModulePermission.user_id == user.id).all()
        module_perms = [p.module_name for p in perms]

    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {"id": user.id, "username": user.username, "role": user.role, "is_approved": bool(user.is_approved)},
        "module_permissions": module_perms,
    }


@router.get("/me")
def me(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    # 查询模块权限
    if current_user.role == "admin":
        module_perms = list(MODULE_LABELS.keys())
    else:
        perms = db.query(UserModulePermission).filter(
            UserModulePermission.user_id == current_user.id).all()
        module_perms = [p.module_name for p in perms]

    return {
        "id": current_user.id,
        "username": current_user.username,
        "role": current_user.role,
        "is_approved": bool(current_user.is_approved),
        "module_permissions": module_perms,
    }


@router.post("/logout")
def logout():
    return {"message": "已登出"}
