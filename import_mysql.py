"""导入三工位-15台测试数据到MySQL"""
import os, sys
os.environ["DB_BACKEND"] = "mysql"
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "backend"))
from sqlalchemy import text
from datetime import date, timedelta
from app.core.database import SessionLocal
from app.models.material import MaterialMaster as M
from app.models.bom import BomHeader, BomLine
from app.models.inventory import InventoryRecord, Warehouse
from app.models.mps import MpsEntry

PARTS = [
    ("6204-2RS", "深沟球轴承 6204-2RS 内径20mm", "SKF", 4, "个", 7, 35),
    ("6005-2RS", "深沟球轴承 6005-2RS 内径25mm", "NSK", 4, "个", 7, 42),
    ("HGH20CA-1000", "直线导轨 HGH20CA 长度1000mm 含滑块×2", "上银HIWIN", 2, "套", 14, 1280),
    ("SFU1605-1000", "滚珠丝杆 SFU1605 导程5mm 长度1000mm", "上银HIWIN", 2, "套", 14, 980),
    ("DS40-AL", "联轴器 DS40 梅花型 铝合金 夹紧式", "米思米", 4, "个", 5, 45),
    ("MDBB32-100Z", "气缸 MDBB32-100Z 双作用 32mm×100mm", "SMC", 6, "个", 10, 320),
    ("MDBB40-150Z", "气缸 MDBB40-150Z 双作用 40mm×150mm", "SMC", 3, "个", 10, 420),
    ("D-M9B", "气缸传感器 D-M9B 无触点 固态开关", "SMC", 12, "个", 5, 55),
    ("AS2201F-01-08S", "调速阀 AS2201F-01-08S 单向节流", "SMC", 15, "个", 3, 18),
    ("ZP3-T08BUN-J6-B5", "真空吸盘 ZP3-T08BUN 丁腈橡胶 平型", "SMC", 12, "个", 5, 25),
    ("ZH05BS-02-02", "真空发生器 ZH05BS 喷嘴直径0.5mm", "SMC", 4, "个", 7, 180),
    ("KQ2H06-01AS", "气管直通接头 KQ2H06-01AS φ6-1/8", "SMC", 40, "个", 3, 3.5),
]

BOM_SHEETS = {
    "外购件": {"code": "WGJ", "parts": PARTS},
}

# 1. 清空
print("=== 清空数据 ===")
with SessionLocal() as db:
    db.execute(text("SET FOREIGN_KEY_CHECKS=0"))
    for t in ["mrp_exception","inventory_transaction","inventory_record","warehouse",
              "bom_line","bom_header","bom_ecn","mps_entry","sales_order","customer",
              "purchase_order","work_order","payment","material_master",
              "routing_operation","routing_header","work_center","inspection_record",
              "stock_count","supplier"]:
        try:
            r = db.execute(text(f"DELETE FROM {t}"))
            db.commit()
            print(f"  ✓ {t} ({r.rowcount} rows)")
        except:
            db.rollback()
    db.execute(text("SET FOREIGN_KEY_CHECKS=1")); db.commit()

# 2. 物料
print("\n=== 创建物料 ===")
with SessionLocal() as db:
    prod = M(material_code="SG-3ST-15", material_name="三工位测试台（15台套）",
             specification="三工位全自动测试设备", unit="台", material_type="成品",
             level_type="产品", lead_time=30, is_purchased=False, is_active=True)
    db.add(prod); db.flush()
    print(f"  成品: {prod.material_name} (id={prod.id})")

    mod = M(material_code="MOD-WGJ", material_name="外购件模块",
            specification="三工位测试台-外购件", unit="套", material_type="半成品",
            level_type="组件", lead_time=15, is_purchased=False, is_active=True)
    db.add(mod); db.flush()
    print(f"  模块: {mod.material_name} (id={mod.id})")

    mat_map = {}
    for code, name, brand, qty, unit, lead, price in PARTS:
        code_key = code.replace("-","").replace("/","_")
        mat = M(material_code=code_key, material_name=name,
                specification=code, unit=unit, material_type="外购件",
                level_type="零件", lead_time=lead, lot_size_rule="LFL",
                is_purchased=True, is_active=True, reference_unit_price=price,
                reference_submitter="熊振", reference_link=brand)
        db.add(mat); db.flush()
        mat_map[code_key] = mat
        print(f"  {mat.material_code}: {name}")
    db.commit()
    print(f"  共 {1 + 1 + len(mat_map)} 个物料")

# 3. BOM
print("\n=== 创建BOM ===")
with SessionLocal() as db:
    prod = db.query(M).filter(M.material_code=="SG-3ST-15").first()
    mod = db.query(M).filter(M.material_code=="MOD-WGJ").first()
    hdr = BomHeader(bom_code="BOM-SG3ST-001", product_id=prod.id, version="A", status="生效")
    db.add(hdr); db.flush()
    db.add(BomLine(bom_header_id=hdr.id, parent_item_id=prod.id, item_id=mod.id, quantity=1))
    for code, name, brand, qty, unit, lead, price in PARTS:
        ck = code.replace("-","").replace("/","_")
        child = db.query(M).filter(M.material_code==ck).first()
        if child:
            db.add(BomLine(bom_header_id=hdr.id, parent_item_id=mod.id, item_id=child.id, quantity=qty))
    db.commit()
    print(f"  1个BOM头 + {1 + len(PARTS)}条BOM行")

# 4. MPS
print("\n=== 创建MPS ===")
with SessionLocal() as db:
    prod = db.query(M).filter(M.material_code=="SG-3ST-15").first()
    for i, (d, q) in enumerate([(7,5),(21,5),(35,5)]):
        db.add(MpsEntry(item_id=prod.id, plan_date=date.today()+timedelta(days=d),
                        quantity=q, source_type="手动", status="进行中"))
    db.commit()
    print("  3批共15台")

# 5. 库存 + 仓库
print("\n=== 创建库存 ===")
with SessionLocal() as db:
    wh = Warehouse(warehouse_code="WH-DEFAULT", warehouse_name="默认仓库", location="主仓库")
    db.add(wh); db.flush()
    for m in db.query(M).all():
        db.add(InventoryRecord(item_id=m.id, warehouse_id=wh.id, on_hand_qty=0, batch_no="init"))
    db.commit()
    print(f"  {db.query(M).count()} 条库存记录")

print("\n✅ 全部完成！")
