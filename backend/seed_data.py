"""初始化演示数据 — 通过 ORM 写入 MySQL/SQLite"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from datetime import date, timedelta, datetime
from app.core.database import init_db, SessionLocal
from app.models.material import MaterialMaster
from app.models.bom import BomHeader, BomLine
from app.models.inventory import Warehouse, InventoryRecord
from app.models.mps import MpsEntry
from app.models.supplier import Supplier
from app.models.routing import WorkCenter


def seed_demo_data():
    # 初始化表
    init_db()
    db = SessionLocal()

    # 检查已有数据，避免重复插入
    if db.query(MaterialMaster).count() > 0:
        print("数据已存在，清理旧数据...")
        db.query(BomLine).delete()
        db.query(BomHeader).delete()
        db.query(MpsEntry).delete()
        db.query(InventoryRecord).delete()
        db.query(MaterialMaster).delete()
        db.query(Warehouse).delete()
        db.query(Supplier).delete()
        db.query(WorkCenter).delete()
        db.commit()
        print("旧数据已清理")

    print("正在初始化演示数据...")

    # 1. 仓库
    wh = Warehouse(warehouse_code="WH01", warehouse_name="主仓库")
    db.add(wh)
    db.flush()
    print(f"  仓库: WH01 (id={wh.id})")

    # 2. 供应商
    s1 = Supplier(supplier_code="SUP001", supplier_name="优质原材料供应商", lead_time_days=3)
    db.add(s1)
    db.flush()

    # 3. 工作中心
    db.add(WorkCenter(center_code="WC01", center_name="装配线1号", capacity_per_day=8, efficiency=95))
    db.add(WorkCenter(center_code="WC02", center_name="加工中心", capacity_per_day=16, efficiency=90))
    db.flush()

    # 4. 物料
    now = datetime.now()
    materials = [
        MaterialMaster(material_code="FG-001", material_name="智能温控器", unit="台", material_type="成品",
                       lead_time=5, safety_stock=20, lot_size_rule="LFL", is_purchased=False, scrap_rate=1),
        MaterialMaster(material_code="FG-002", material_name="电动阀门", unit="台", material_type="成品",
                       lead_time=7, safety_stock=15, lot_size_rule="FOQ", lot_size_qty=30, is_purchased=False),
        MaterialMaster(material_code="SA-001", material_name="温控主板组件", unit="个", material_type="半成品",
                       lead_time=3, safety_stock=30, lot_size_rule="FOQ", lot_size_qty=50, is_purchased=False),
        MaterialMaster(material_code="SA-002", material_name="显示面板组件", unit="个", material_type="半成品",
                       lead_time=2, safety_stock=25, lot_size_rule="LFL", is_purchased=False),
        MaterialMaster(material_code="SA-003", material_name="阀门执行器组件", unit="个", material_type="半成品",
                       lead_time=4, safety_stock=20, lot_size_rule="FOQ", lot_size_qty=40, is_purchased=False),
        MaterialMaster(material_code="RM-001", material_name="PCB电路板", unit="块", material_type="原材料",
                       lead_time=5, safety_stock=100, lot_size_rule="EOQ", lot_size_qty=500, is_purchased=True),
        MaterialMaster(material_code="RM-002", material_name="温度传感器芯片", unit="个", material_type="原材料",
                       lead_time=7, safety_stock=200, lot_size_rule="EOQ", lot_size_qty=1000, is_purchased=True),
        MaterialMaster(material_code="RM-003", material_name="LCD显示屏", unit="块", material_type="原材料",
                       lead_time=10, safety_stock=80, lot_size_rule="FOQ", lot_size_qty=100, is_purchased=True),
        MaterialMaster(material_code="RM-004", material_name="微型步进电机", unit="个", material_type="原材料",
                       lead_time=4, safety_stock=50, lot_size_rule="FOQ", lot_size_qty=200, is_purchased=True),
        MaterialMaster(material_code="RM-005", material_name="铝合金外壳", unit="个", material_type="原材料",
                       lead_time=3, safety_stock=60, lot_size_rule="MULT", lot_size_qty=100, is_purchased=True),
        MaterialMaster(material_code="RM-006", material_name="电源模块12V", unit="个", material_type="原材料",
                       lead_time=6, safety_stock=150, lot_size_rule="EOQ", lot_size_qty=300, is_purchased=True),
        MaterialMaster(material_code="RM-007", material_name="不锈钢阀体", unit="个", material_type="原材料",
                       lead_time=8, safety_stock=40, lot_size_rule="FOQ", lot_size_qty=50, is_purchased=True),
        MaterialMaster(material_code="RM-008", material_name="密封圈套件", unit="套", material_type="原材料",
                       lead_time=2, safety_stock=200, lot_size_rule="MULT", lot_size_qty=500, is_purchased=True),
    ]
    db.add_all(materials)
    db.flush()

    code_to_id = {}
    for m in materials:
        code_to_id[m.material_code] = m.id
    print(f"  物料: {len(materials)} 个")

    # 5. BOM: FG-001 智能温控器
    bom1 = BomHeader(bom_code="BOM-FG-001", product_id=code_to_id["FG-001"], version="A", status="生效")
    db.add(bom1)
    db.flush()
    db.add_all([
        BomLine(bom_header_id=bom1.id, parent_item_id=code_to_id["FG-001"], item_id=code_to_id["SA-001"], quantity=1, position="A1", level=1, sort_order=1),
        BomLine(bom_header_id=bom1.id, parent_item_id=code_to_id["FG-001"], item_id=code_to_id["SA-002"], quantity=1, position="A2", level=1, sort_order=2),
        BomLine(bom_header_id=bom1.id, parent_item_id=code_to_id["FG-001"], item_id=code_to_id["RM-005"], quantity=1, position="A3", level=1, sort_order=3),
        BomLine(bom_header_id=bom1.id, parent_item_id=code_to_id["SA-001"], item_id=code_to_id["RM-001"], quantity=1, level=2, sort_order=4),
        BomLine(bom_header_id=bom1.id, parent_item_id=code_to_id["SA-001"], item_id=code_to_id["RM-002"], quantity=3, level=2, sort_order=5),
        BomLine(bom_header_id=bom1.id, parent_item_id=code_to_id["SA-001"], item_id=code_to_id["RM-006"], quantity=1, level=2, sort_order=6),
        BomLine(bom_header_id=bom1.id, parent_item_id=code_to_id["SA-002"], item_id=code_to_id["RM-003"], quantity=1, level=2, sort_order=7),
        BomLine(bom_header_id=bom1.id, parent_item_id=code_to_id["SA-002"], item_id=code_to_id["RM-001"], quantity=1, level=2, sort_order=8),
    ])

    # BOM: FG-002 电动阀门
    bom2 = BomHeader(bom_code="BOM-FG-002", product_id=code_to_id["FG-002"], version="A", status="生效")
    db.add(bom2)
    db.flush()
    db.add_all([
        BomLine(bom_header_id=bom2.id, parent_item_id=code_to_id["FG-002"], item_id=code_to_id["SA-003"], quantity=1, position="B1", level=1, sort_order=1),
        BomLine(bom_header_id=bom2.id, parent_item_id=code_to_id["FG-002"], item_id=code_to_id["RM-005"], quantity=1, position="B2", level=1, sort_order=2),
        BomLine(bom_header_id=bom2.id, parent_item_id=code_to_id["SA-003"], item_id=code_to_id["RM-004"], quantity=1, level=2, sort_order=3),
        BomLine(bom_header_id=bom2.id, parent_item_id=code_to_id["SA-003"], item_id=code_to_id["RM-007"], quantity=1, level=2, sort_order=4),
        BomLine(bom_header_id=bom2.id, parent_item_id=code_to_id["SA-003"], item_id=code_to_id["RM-008"], quantity=2, level=2, sort_order=5),
        BomLine(bom_header_id=bom2.id, parent_item_id=code_to_id["SA-003"], item_id=code_to_id["RM-006"], quantity=1, level=2, sort_order=6),
    ])
    print(f"  BOM: 2 个")

    # 6. MPS
    today_d = date.today()
    for i in range(1, 13):
        d = today_d + timedelta(days=7*i)
        qty = 100 if i % 4 != 0 else (120 if i % 2 == 0 else 150)
        src = "销售订单" if i <= 3 else "预测"
        db.add(MpsEntry(item_id=code_to_id["FG-001"], plan_date=d, quantity=qty, source_type=src))
    for i in range(1, 7):
        d = today_d + timedelta(days=14*i)
        src = "销售订单" if i <= 2 else "预测"
        db.add(MpsEntry(item_id=code_to_id["FG-002"], plan_date=d, quantity=50+(i%3)*10, source_type=src))
    print(f"  MPS: 18 条计划")

    # 7. 库存
    inv_data = {
        "SA-001": 45, "SA-002": 20, "SA-003": 15,
        "RM-001": 200, "RM-002": 350, "RM-003": 60,
        "RM-004": 45, "RM-005": 70, "RM-006": 180,
        "RM-007": 30, "RM-008": 300,
        "FG-001": 15, "FG-002": 10,
    }
    for code, qty in inv_data.items():
        db.add(InventoryRecord(item_id=code_to_id[code], warehouse_id=wh.id, on_hand_qty=qty))
    print(f"  库存: {len(inv_data)} 条")

    db.commit()
    db.close()

    print(f"\n✅ 演示数据初始化完成 (MySQL)")
    print(f"\n启动后端: cd backend && python -m uvicorn app.main:app --host 0.0.0.0 --port 8000")


if __name__ == "__main__":
    seed_demo_data()
