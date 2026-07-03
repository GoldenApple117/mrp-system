"""P0-2: 初始化库存数据 — 为所有物料设置安全库存 + 现有库存"""
from app.core.database import SessionLocal
from app.models.material import MaterialMaster
from app.models.inventory import InventoryRecord

db = SessionLocal()
try:
    # 默认仓库 ID
    DEFAULT_WH = 14

    # 按物料级别设置安全库存策略
    safety_rules = {
        "成品": 5,         # 成品备5台
        "模块": 8,         # 模块备8套
        "零件": 50,        # 零件备50个
        "原材料": 200,     # 原材料备200
    }

    mats = db.query(MaterialMaster).filter(MaterialMaster.is_active == True).all()
    updated = 0
    inv_updated = 0

    for mat in mats:
        # 设置安全库存
        lvl = mat.level_type or "零件"
        if mat.material_type == "成品":
            lvl = "成品"
        elif mat.material_type in ("模块",):
            lvl = "模块"

        default_safety = safety_rules.get(lvl, 30)
        
        if mat.safety_stock == 0 or mat.safety_stock is None:
            mat.safety_stock = default_safety
            updated += 1

        # 设置初始库存（安全库存的 2-3 倍，模拟正常库存水平）
        inv = db.query(InventoryRecord).filter(
            InventoryRecord.item_id == mat.id,
            InventoryRecord.warehouse_id == DEFAULT_WH,
        ).first()

        if inv:
            if inv.on_hand_qty == 0 or inv.on_hand_qty is None:
                inv.on_hand_qty = default_safety * 2.5
                inv_updated += 1
        else:
            # 创建新库存记录
            inv = InventoryRecord(
                item_id=mat.id,
                warehouse_id=DEFAULT_WH,
                on_hand_qty=default_safety * 2.5,
            )
            db.add(inv)
            inv_updated += 1

    db.commit()
    print(f"安全库存更新: {updated} 条")
    print(f"库存数量更新: {inv_updated} 条")

    # 汇总
    from sqlalchemy import func
    total_on_hand = db.query(func.sum(InventoryRecord.on_hand_qty)).scalar() or 0
    total_safety = db.query(func.sum(MaterialMaster.safety_stock)).filter(
        MaterialMaster.is_active == True
    ).scalar() or 0
    print(f"现有库存总量: {total_on_hand:.0f}")
    print(f"安全库存总量: {total_safety:.0f}")

finally:
    db.close()
