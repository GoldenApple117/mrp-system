"""MRP例外看板 API"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.core.database import get_db
from app.models.mrp_exception import MrpException

router = APIRouter(prefix="/api/exceptions", tags=["例外看板"])


@router.get("")
def list_exceptions(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=1000),
    severity: str = Query(None),
    exception_type: str = Query(None),
    resolved: bool = Query(None),
    run_id: str = Query(None),
    db: Session = Depends(get_db),
):
    """例外列表（支持筛选）"""
    query = db.query(MrpException)

    if severity:
        query = query.filter(MrpException.severity == severity)
    if exception_type:
        query = query.filter(MrpException.exception_type == exception_type)
    if resolved is not None:
        query = query.filter(MrpException.is_resolved == resolved)
    if run_id:
        query = query.filter(MrpException.run_id == run_id)

    total = query.count()
    items = query.order_by(
        MrpException.severity.desc(),
        MrpException.is_resolved.asc(),
        MrpException.created_at.desc()
    ).offset((page-1)*page_size).limit(page_size).all()

    return {
        "items": [
            {
                "id": e.id, "run_id": e.run_id,
                "exception_type": e.exception_type,
                "item_code": e.item_code, "material_name": e.material_name,
                "message": e.message, "severity": e.severity,
                "is_resolved": e.is_resolved,
                "created_at": e.created_at.isoformat() if e.created_at else None,
                "resolved_at": e.resolved_at.isoformat() if e.resolved_at else None,
            }
            for e in items
        ],
        "total": total, "page": page, "page_size": page_size,
    }


@router.get("/summary")
def exception_summary(db: Session = Depends(get_db)):
    """例外汇总统计"""
    # 最新运行批次
    latest_run = db.query(MrpException.run_id).filter(
        MrpException.run_id != ""
    ).order_by(MrpException.created_at.desc()).first()
    latest_run_id = latest_run[0] if latest_run else None

    # 统计
    total = db.query(MrpException).count()
    unresolved = db.query(MrpException).filter(MrpException.is_resolved == False).count()
    errors = db.query(MrpException).filter(MrpException.severity == "ERROR", MrpException.is_resolved == False).count()
    warnings = db.query(MrpException).filter(MrpException.severity == "WARNING", MrpException.is_resolved == False).count()

    # 按类型统计
    type_counts = db.query(
        MrpException.exception_type,
        func.count()
    ).filter(MrpException.is_resolved == False).group_by(MrpException.exception_type).all()

    return {
        "total": total,
        "unresolved": unresolved,
        "errors": errors,
        "warnings": warnings,
        "latest_run": latest_run_id,
        "by_type": [{"type": t, "count": c} for t, c in type_counts],
        "type_labels": {
            "SHORTAGE": "缺料",
            "OVERDUE_ORDER": "逾期订单",
            "SAFETY_STOCK_ALERT": "安全库存预警",
            "SUBSTITUTE": "替代料使用",
        },
    }


@router.post("/resolve/{exception_id}")
def resolve_exception(exception_id: int, db: Session = Depends(get_db)):
    """标记例外为已处理"""
    from datetime import datetime
    ex = db.query(MrpException).filter(MrpException.id == exception_id).first()
    if not ex:
        return {"success": False, "message": "不存在"}
    ex.is_resolved = True
    ex.resolved_at = datetime.now()
    db.commit()
    return {"success": True, "message": "已标记处理"}


@router.post("/resolve/batch")
def batch_resolve(data: dict, db: Session = Depends(get_db)):
    """批量标记已处理"""
    from datetime import datetime
    ids = data.get("ids", [])
    if not ids:
        return {"success": False, "message": "请提供ID列表"}
    count = 0
    for eid in ids:
        ex = db.query(MrpException).filter(MrpException.id == eid).first()
        if ex and not ex.is_resolved:
            ex.is_resolved = True
            ex.resolved_at = datetime.now()
            count += 1
    db.commit()
    return {"success": True, "message": f"已处理 {count} 条"}


@router.delete("/clear")
def clear_exceptions(db: Session = Depends(get_db)):
    """清空所有例外记录"""
    db.query(MrpException).delete()
    db.commit()
    return {"success": True, "message": "已清空"}
