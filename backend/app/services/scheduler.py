"""定时任务 — MRP自动运算"""
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


def auto_run_mrp():
    """定时执行MRP运算（由APScheduler调用）"""
    from app.core.database import SessionLocal, init_db
    from app.api.mrp import run_mrp_logic

    try:
        init_db()
        db = SessionLocal()
        logger.info("🔄 定时MRP运算开始...")
        result = run_mrp_logic(db, horizon_days=90, time_fence_days=7)
        plan_count = len(result.get("planned_orders", []))
        logger.info(f"✅ 定时MRP完成，生成 {plan_count} 条建议订单")
        db.close()
    except Exception as e:
        logger.error(f"❌ 定时MRP失败: {e}")
