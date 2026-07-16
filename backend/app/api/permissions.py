"""权限管理 API — 申请/审批 + 模块权限管理"""
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.user import User
from app.models.permission import PermissionRequest, UserModulePermission
from app.api.deps import get_current_user, MODULE_LABELS

router = APIRouter(prefix="/api/permissions", tags=["权限管理"])


def require_admin(user: User):
    if user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="仅管理员可操作")


@router.post("/request")
def request_permission(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """普通用户申请权限"""
    if current_user.role == "admin":
        return {"message": "管理员无需申请", "status": "already_admin"}

    # 检查是否已有待审批的申请
    pending = db.query(PermissionRequest).filter(
        PermissionRequest.user_id == current_user.id,
        PermissionRequest.status == "pending"
    ).first()
    if pending:
        return {"message": "已有待审批的申请", "status": "pending"}

    req = PermissionRequest(user_id=current_user.id)
    db.add(req)
    db.commit()
    return {"message": "申请已提交，等待管理员审批", "status": "pending"}


@router.get("/my-status")
def my_status(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """查询当前用户的权限状态"""
    if current_user.role == "admin":
        return {"status": "approved", "message": "管理员"}
    latest = db.query(PermissionRequest).filter(
        PermissionRequest.user_id == current_user.id
    ).order_by(PermissionRequest.created_at.desc()).first()
    if not latest:
        return {"status": "none", "message": "未申请"}
    return {"status": latest.status, "message": {"pending": "审批中", "approved": "已授权", "rejected": "已拒绝"}.get(latest.status, "")}


@router.get("/list")
def list_requests(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """管理员查看所有申请列表"""
    require_admin(current_user)
    reqs = db.query(PermissionRequest).order_by(PermissionRequest.created_at.desc()).all()
    result = []
    for r in reqs:
        user = db.query(User).filter(User.id == r.user_id).first()
        result.append({
            "id": r.id,
            "user_id": r.user_id,
            "username": user.username if user else "未知",
            "status": r.status,
            "created_at": r.created_at.isoformat() if r.created_at else None,
            "reviewed_at": r.reviewed_at.isoformat() if r.reviewed_at else None,
        })
    return result


@router.put("/approve/{req_id}")
def approve_request(
    req_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """管理员同意权限申请"""
    require_admin(current_user)
    req = db.query(PermissionRequest).filter(PermissionRequest.id == req_id).first()
    if not req:
        raise HTTPException(status_code=404, detail="申请不存在")
    if req.status != "pending":
        raise HTTPException(status_code=400, detail="该申请已处理")

    req.status = "approved"
    req.reviewed_at = datetime.utcnow()
    req.reviewed_by = current_user.id
    db.commit()

    # 更新用户的 is_approved 状态
    user = db.query(User).filter(User.id == req.user_id).first()
    if user:
        user.is_approved = 1
        db.commit()

    return {"message": f"已授权用户 {user.username if user else '未知'}", "status": "approved"}


@router.put("/reject/{req_id}")
def reject_request(
    req_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """管理员拒绝权限申请"""
    require_admin(current_user)
    req = db.query(PermissionRequest).filter(PermissionRequest.id == req_id).first()
    if not req:
        raise HTTPException(status_code=404, detail="申请不存在")
    if req.status != "pending":
        raise HTTPException(status_code=400, detail="该申请已处理")

    req.status = "rejected"
    req.reviewed_at = datetime.utcnow()
    req.reviewed_by = current_user.id
    db.commit()

    user = db.query(User).filter(User.id == req.user_id).first()
    return {"message": f"已拒绝用户 {user.username if user else '未知'}", "status": "rejected"}


@router.get("/pending-count")
def pending_count(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """获取待审批数量（仅管理员）"""
    if current_user.role != "admin":
        return {"count": 0}
    count = db.query(PermissionRequest).filter(PermissionRequest.status == "pending").count()
    return {"count": count}


# ====== 模块权限管理 ======


@router.get("/users")
def list_users(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """返回全部用户列表（管理员用）"""
    require_admin(current_user)
    users = db.query(User).order_by(User.id).all()
    return [{"id": u.id, "username": u.username, "role": u.role} for u in users]


@router.get("/modules")
def list_modules():
    """返回全部模块清单（前端渲染权限勾选框用）"""
    return {"modules": [{"key": k, "label": v} for k, v in MODULE_LABELS.items()]}


@router.get("/users/{uid}/modules")
def get_user_modules(
    uid: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """查询指定用户的模块权限列表"""
    require_admin(current_user)
    user = db.query(User).filter(User.id == uid).first()
    if not user:
        raise HTTPException(404, "用户不存在")

    if user.role == "admin":
        return {"user_id": uid, "username": user.username, "module_permissions": list(MODULE_LABELS.keys())}

    perms = db.query(UserModulePermission).filter(
        UserModulePermission.user_id == uid).all()
    return {
        "user_id": uid,
        "username": user.username,
        "module_permissions": [p.module_name for p in perms],
    }


@router.put("/users/{uid}/modules")
def set_user_modules(
    uid: int,
    data: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """管理员设置用户的模块权限"""
    require_admin(current_user)
    user = db.query(User).filter(User.id == uid).first()
    if not user:
        raise HTTPException(404, "用户不存在")
    if user.role == "admin":
        raise HTTPException(400, "管理员拥有全部权限，无需设置")

    modules = data.get("modules", [])
    # 校验模块名
    valid_modules = set(MODULE_LABELS.keys())
    for m in modules:
        if m not in valid_modules:
            raise HTTPException(400, f"无效的模块名: {m}")

    # 全删重建
    db.query(UserModulePermission).filter(UserModulePermission.user_id == uid).delete()
    for m in modules:
        db.add(UserModulePermission(
            user_id=uid,
            module_name=m,
            granted_by=current_user.username,
        ))
    db.commit()
    return {"message": f"已更新用户 {user.username} 的模块权限", "modules": modules}
