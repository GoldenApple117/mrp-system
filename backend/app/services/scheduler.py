"""APScheduler MRP定时任务 + 邮件通知"""
import logging
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

logger = logging.getLogger(__name__)

# 全局单例
_scheduler: BackgroundScheduler = None
_config = {
    "enabled": False,
    "hour": 8,
    "minute": 0,
    "horizon_days": 90,
    "time_fence_days": 7,
    "last_run": None,
    "last_result": None,
}


def get_config():
    return dict(_config)


def update_config(**kwargs):
    """更新配置并即时生效"""
    global _config
    _config.update({k: v for k, v in kwargs.items() if k in _config})
    _apply_schedule()
    return dict(_config)


def _run_mrp_job():
    """定时任务执行体"""
    from app.core.database import SessionLocal
    from app.api.mrp import run_mrp_logic
    from app.services.notifier import send_mrp_notification

    db = SessionLocal()
    try:
        logger.info(f"[MRP定时] 开始执行...")
        result = run_mrp_logic(db, _config["horizon_days"], _config["time_fence_days"])
        _config["last_run"] = datetime.now().isoformat()
        _config["last_result"] = {
            "success": result.get("success", False),
            "total_orders": len(result.get("data", {}).get("planned_orders", [])),
            "exceptions": len(result.get("data", {}).get("exceptions", [])),
            "message": result.get("message", ""),
        }
        logger.info(f"[MRP定时] 完成: {_config['last_result']}")

        # 自动转换计划订单
        if result.get("success"):
            planned = result.get("data", {}).get("planned_orders", [])
            if planned:
                from app.models.material import MaterialMaster as M
                from app.models.order import PurchaseOrder, WorkOrder
                po_seq = wo_seq = 0
                today_str = datetime.now().strftime("%Y%m%d")
                time_part = datetime.now().strftime("%H%M%S")
                po_base = f"PR-{today_str}-{time_part}"
                wo_base = f"WO-{today_str}-{time_part}"
                created_po = created_wo = 0

                for order in planned:
                    try:
                        mat = db.query(M).filter(M.material_code == order["item_code"]).first()
                        if not mat: continue
                        if order["order_type"] == "PURCHASE":
                            po_seq += 1
                            unit_price = mat.reference_unit_price or 0
                            order_qty = order["quantity"]
                            brand = mat.specification.split(" / ")[-1] if " / " in (mat.specification or "") else (mat.specification or "")
                            po = PurchaseOrder(
                                po_number=f"{po_base}-{po_seq:04d}",
                                supplier_id=0,  # 定时任务自动生成，无指定供应商
                                item_id=mat.id, order_qty=order_qty,
                                unit_price=unit_price,
                                total_amount=round(unit_price * order_qty, 2),
                                due_date=order["required_date"],
                                status="申请", source_type="MRP定时",
                                brand=brand,
                                submitter=mat.reference_submitter or "",
                                supplier_link=mat.reference_link or "",
                            )
                            db.add(po); created_po += 1
                    except Exception as e:
                        logger.error(f"[MRP定时] PO创建失败: {e}")
                
                db.commit()
                _config["last_result"]["auto_po"] = created_po
                _config["last_result"]["auto_wo"] = created_wo

        # 邮件通知（notifier 从配置中自动读取收件地址）
        send_mrp_notification(_config["last_result"])

    except Exception as e:
        logger.error(f"[MRP定时] 执行失败: {e}", exc_info=True)
    finally:
        db.close()


def _apply_schedule():
    global _scheduler
    if _scheduler is None:
        return

    # 移除已有MRP任务
    for job in _scheduler.get_jobs():
        if job.id == "mrp_auto":
            job.remove()

    if _config["enabled"]:
        _scheduler.add_job(
            _run_mrp_job,
            CronTrigger(hour=_config["hour"], minute=_config["minute"]),
            id="mrp_auto",
            name="MRP自动运算",
            replace_existing=True,
        )
        logger.info(f"[MRP定时] 已启用: 每天 {_config['hour']:02d}:{_config['minute']:02d}")
    else:
        logger.info("[MRP定时] 已停用")


def start_scheduler():
    """启动调度器（应用启动时调用）"""
    global _scheduler
    if _scheduler is not None:
        return

    _scheduler = BackgroundScheduler(daemon=True)
    _scheduler.start()
    _apply_schedule()
    logger.info("[MRP定时] 调度器已启动")


def shutdown_scheduler():
    global _scheduler
    if _scheduler:
        _scheduler.shutdown(wait=False)
        _scheduler = None
