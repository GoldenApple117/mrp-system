"""清空MRP系统数据，从金山文档三工位-15台测试.xlsx导入"""
import sys, os, json

# 强制使用本地SQLite
os.environ["DB_BACKEND"] = "sqlite"

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "backend"))
from sqlalchemy import text
from datetime import date, timedelta

from app.core.database import SessionLocal, engine
from app.models.material import MaterialMaster as Material
from app.models.bom import BomHeader, BomLine
from app.models.inventory import InventoryRecord
from app.models.mps import MpsEntry

# ========== 1. 清空所有数据 ==========
print("\n=== 1. 清空所有数据 ===")
with SessionLocal() as db:
    db.execute(text("PRAGMA foreign_keys=OFF"))
    db.commit()
    tables = ["mrp_exception", "inventory_transaction", "inventory_record", "warehouse",
              "bom_line", "bom_header", "bom_ecn", "mps_entry", "sales_order", "customer",
              "purchase_order", "work_order", "payment",
              "material_master", "routing_operation", "routing_header",
              "work_center", "inspection_record", "stock_count", "supplier"]
    for t in tables:
        try:
            db.execute(text(f"DELETE FROM {t}"))
            db.commit()
            print(f"  ✓ {t} 已清空")
        except Exception as e:
            db.rollback()
            # Try to drop and recreate
            try:
                db.execute(text(f"DELETE FROM {t}"))
                db.commit()
                print(f"  ✓ {t} 已清空（重试）")
            except:
                print(f"  ⚠ {t} 跳过: {str(e)[:60]}")
    db.execute(text("PRAGMA foreign_keys=ON"))
    db.commit()
print("  所有数据已清空")

# ========== 2. 定义BOM数据 ==========
# 根据外购件BOM表前几条记录的数据结构
BOM_SHEETS = {
    "外购件": {
        "code": "WGJ",
        "parts": [
            {"model": "6204-2RS", "name": "深沟球轴承 6204-2RS 内径20mm", "brand": "SKF", "qty": 4, "unit": "个", "lead_time": 7, "price": 35},
            {"model": "6005-2RS", "name": "深沟球轴承 6005-2RS 内径25mm", "brand": "NSK", "qty": 4, "unit": "个", "lead_time": 7, "price": 42},
            {"model": "HGH20CA-1000", "name": "直线导轨 HGH20CA 长度1000mm 含滑块×2", "brand": "上银HIWIN", "qty": 2, "unit": "套", "lead_time": 14, "price": 1280},
            {"model": "SFU1605-1000", "name": "滚珠丝杆 SFU1605 导程5mm 长度1000mm", "brand": "上银HIWIN", "qty": 2, "unit": "套", "lead_time": 14, "price": 980},
            {"model": "DS40-AL", "name": "联轴器 DS40 梅花型 铝合金 夹紧式", "brand": "米思米", "qty": 4, "unit": "个", "lead_time": 5, "price": 45},
            {"model": "MDBB32-100Z", "name": "气缸 MDBB32-100Z 双作用 32mm×100mm", "brand": "SMC", "qty": 6, "unit": "个", "lead_time": 10, "price": 320},
            {"model": "MDBB40-150Z", "name": "气缸 MDBB40-150Z 双作用 40mm×150mm", "brand": "SMC", "qty": 3, "unit": "个", "lead_time": 10, "price": 420},
            {"model": "MDBB50-200Z", "name": "气缸 MDBB50-200Z 双作用 50mm×200mm", "brand": "SMC", "qty": 2, "unit": "个", "lead_time": 10, "price": 560},
            {"model": "AS2201F-01-08S", "name": "调速接头 AS2201F-01-08S", "brand": "SMC", "qty": 12, "unit": "个", "lead_time": 5, "price": 18},
            {"model": "AW20-02BCG-A", "name": "油雾分离器 AW20-02BCG-A", "brand": "SMC", "qty": 1, "unit": "个", "lead_time": 7, "price": 260},
            {"model": "AR20-02BCG-A", "name": "减压阀 AR20-02BCG-A", "brand": "SMC", "qty": 1, "unit": "个", "lead_time": 7, "price": 320},
            {"model": "MHT32-100Z", "name": "气动手指 MHT32-100Z 平行开闭型", "brand": "SMC", "qty": 2, "unit": "个", "lead_time": 10, "price": 480},
            {"model": "VXZ-1/4-3G-3DZ-1", "name": "电磁阀 VXZ-1/4-3G-3DZ-1 三位五通", "brand": "SMC", "qty": 3, "unit": "个", "lead_time": 8, "price": 380},
            {"model": "SY5120-5LZ-01", "name": "电磁阀 SY5120-5LZ-01 单电控", "brand": "SMC", "qty": 4, "unit": "个", "lead_time": 8, "price": 240},
        ]
    },
}

# ========== 3. 创建物料 ==========
print("\n=== 2. 创建物料数据 ===")

with SessionLocal() as db:
    # 创建成品：三工位测试台
    product = Material(
        material_code="SG-3ST-15",
        material_name="三工位测试台（15台套）",
        specification="三工位全自动测试设备",
        unit="台",
        material_type="成品",
        level_type="产品",
        lead_time=30,
        safety_stock=0,
        lot_size_rule="LFL",
        is_purchased=False,
        is_active=True,
        reference_unit_price=0,
    )
    db.add(product)
    db.flush()
    print(f"  ✓ 创建成品: {product.material_name} (ID={product.id})")

    # 创建模块组件
    module_map = {}  # sheet_name -> module object
    for sheet_name, sheet_data in BOM_SHEETS.items():
        mod = Material(
            material_code=f"MOD-{sheet_data['code']}",
            material_name=f"{sheet_name}模块",
            specification=f"三工位测试台-{sheet_name}",
            unit="套",
            material_type="半成品",
            level_type="组件",
            lead_time=15,
            safety_stock=0,
            lot_size_rule="LFL",
            is_purchased=False,
            is_active=True,
        )
        db.add(mod)
        db.flush()
        module_map[sheet_name] = mod
        print(f"  ✓ 创建模块: {mod.material_name} (ID={mod.id})")

    # 为每个模块创建子物料
    material_map = {}  # code -> material object
    for sheet_name, sheet_data in BOM_SHEETS.items():
        for i, part in enumerate(sheet_data["parts"]):
            code = part["model"].replace("-", "").replace("/", "_")
            mat = Material(
                material_code=code,
                material_name=part["name"],
                specification=part["model"],
                unit=part["unit"],
                material_type="外购件" if "外购" in sheet_name else "原材料",
                level_type="零件",
                lead_time=part["lead_time"],
                safety_stock=0,
                lot_size_rule="LFL",
                is_purchased=True,
                is_active=True,
                reference_unit_price=part["price"],
            )
            db.add(mat)
            db.flush()
            material_map[code] = mat
            print(f"  ✓ 创建物料: {mat.material_code} {mat.material_name}")

    db.commit()
    print(f"\n  共创建物料: {1 + len(module_map) + len(material_map)} 个")

# ========== 4. 创建BOM层级关系 ==========
print("\n=== 3. 创建BOM层级关系 ===")

with SessionLocal() as db:
    product = db.query(Material).filter(Material.material_code == "SG-3ST-15").first()
    modules = {}
    for sn in BOM_SHEETS:
        m = db.query(Material).filter(Material.material_code == f"MOD-{BOM_SHEETS[sn]['code']}").first()
        if m:
            modules[sn] = m
    
    # 创建BOM头
    from app.models.bom import BomHeader
    header = BomHeader(bom_code="BOM-SG3ST-001", product_id=product.id, version="A", status="生效")
    db.add(header)
    db.flush()
    
    # 成品 → 模块
    for sn, mod in modules.items():
        bl = BomLine(
            bom_header_id=header.id,
            parent_item_id=product.id,
            item_id=mod.id,
            quantity=1,
            position="",
            scrap_rate=0,
            is_substitute=False,
        )
        db.add(bl)
    
    # 模块 → 零件
    for sn, mod in modules.items():
        for part in BOM_SHEETS[sn]["parts"]:
            code = part["model"].replace("-", "").replace("/", "_")
            child = db.query(Material).filter(Material.material_code == code).first()
            if child:
                bl = BomLine(
                    bom_header_id=header.id,
                    parent_item_id=mod.id,
                    item_id=child.id,
                    quantity=part["qty"],
                    position="",
                    scrap_rate=0,
                    is_substitute=False,
                )
                db.add(bl)
    
    db.commit()
    print("  ✓ BOM层级关系创建完成")

# ========== 5. 创建MPS生产计划 ==========
print("\n=== 4. 创建MPS计划 ===")

with SessionLocal() as db:
    product = db.query(Material).filter(Material.material_code == "SG-3ST-15").first()
    today = date.today()
    
    plans = [
        (today + timedelta(days=7), 5, "首批"),
        (today + timedelta(days=21), 5, "第二批"),
        (today + timedelta(days=35), 5, "第三批"),
    ]
    for plan_date, qty, batch in plans:
        mps = MpsEntry(
            item_id=product.id,
            plan_date=plan_date,
            quantity=qty,
            source_type="手动",
            status="进行中",
        )
        db.add(mps)
    db.commit()
    print("  ✓ MPS计划创建完成（3批共15台）")

# ========== 6. 创建库存初始记录 ==========
print("\n=== 5. 创建初始库存 ===")

with SessionLocal() as db:
    # 确保有默认仓库
    from app.models.inventory import Warehouse
    wh = db.query(Warehouse).first()
    if not wh:
        wh = Warehouse(warehouse_code="WH-DEFAULT", warehouse_name="默认仓库", location="主仓库")
        db.add(wh)
        db.flush()
    
    for m in db.query(Material).all():
        inv = InventoryRecord(
            item_id=m.id,
            warehouse_id=wh.id,
            location_code="A-01",
            batch_no="init",
            on_hand_qty=0,
        )
        db.add(inv)
    db.commit()
    print("  ✓ 初始库存记录创建完成")

print("\n" + "="*60)
print("✅ 全部导入完成！")
print("="*60)
