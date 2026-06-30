"""初始化演示数据 — 通过 ORM 写入 MySQL/SQLite"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from datetime import date, timedelta, datetime
from app.core.database import init_db, SessionLocal
from app.models.material import MaterialMaster
from app.models.bom import BomHeader, BomLine
from app.models.inventory import Warehouse, InventoryRecord, InventoryTransaction
from app.models.mps import MpsEntry
from app.models.order import PurchaseOrder, WorkOrder
from app.models.supplier import Supplier
from app.models.routing import WorkCenter, RoutingHeader, RoutingOperation
from app.models.inspection import InspectionRecord, StockCount


def seed_demo_data():
    # 初始化表
    init_db()
    db = SessionLocal()

    # 清空旧数据（按外键依赖倒序：先删有外键引用的子表）
    db.query(StockCount).delete()
    db.query(InspectionRecord).delete()
    db.query(InventoryTransaction).delete()
    db.query(PurchaseOrder).delete()
    db.query(WorkOrder).delete()
    db.query(RoutingOperation).delete()
    db.query(RoutingHeader).delete()
    db.query(BomLine).delete()
    db.query(BomHeader).delete()
    db.query(MpsEntry).delete()
    db.query(InventoryRecord).delete()
    db.query(MaterialMaster).delete()
    db.query(WorkCenter).delete()
    db.query(Warehouse).delete()
    db.query(Supplier).delete()
    db.commit()

    print("正在初始化演示数据...")

    # ===== 1. 仓库 =====
    wh = Warehouse(warehouse_code="WH01", warehouse_name="主仓库")
    db.add(wh)
    db.flush()
    print(f"  仓库: WH01")

    # ===== 2. 供应商 =====
    db.add(Supplier(supplier_code="SUP001", supplier_name="优质原材料供应商", lead_time_days=3))
    db.flush()

    # ===== 3. 工作中心（5个） =====
    wc_list = [
        WorkCenter(center_code="WC01", center_name="SMT贴片线", capacity_per_day=16, efficiency=95, machines_count=2, workers_count=2),
        WorkCenter(center_code="WC02", center_name="插件线", capacity_per_day=8, efficiency=90, machines_count=1, workers_count=3),
        WorkCenter(center_code="WC03", center_name="组装线1号", capacity_per_day=8, efficiency=95, machines_count=1, workers_count=4),
        WorkCenter(center_code="WC04", center_name="组装线2号", capacity_per_day=8, efficiency=90, machines_count=1, workers_count=3),
        WorkCenter(center_code="WC05", center_name="测试包装线", capacity_per_day=8, efficiency=98, machines_count=1, workers_count=2),
    ]
    db.add_all(wc_list)
    db.flush()
    wc_map = {wc.center_code: wc.id for wc in wc_list}
    print(f"  工作中心: 5 个")

    # ===== 4. 物料（16个） =====
    materials = [
        # 产品层（level_type='产品'）
        MaterialMaster(material_code="FG-001", material_name="智能温控器", unit="台", material_type="成品",
                       level_type="产品", lead_time=5, safety_stock=20, lot_size_rule="LFL", is_purchased=False, scrap_rate=1),
        MaterialMaster(material_code="FG-002", material_name="电动阀门", unit="台", material_type="成品",
                       level_type="产品", lead_time=7, safety_stock=15, lot_size_rule="FOQ", lot_size_qty=30, is_purchased=False),
        MaterialMaster(material_code="FG-003", material_name="工业传感器模组", unit="套", material_type="成品",
                       level_type="产品", lead_time=10, safety_stock=10, lot_size_rule="LFL", is_purchased=False),
        # 模块层（level_type='模块'，仅用于零件分类，不参与MRP运算）
        MaterialMaster(material_code="MOD-ELEC", material_name="电子电气模块", unit="个", material_type="模块",
                       level_type="模块", lead_time=0, safety_stock=0, lot_size_rule="LFL", is_purchased=False),
        MaterialMaster(material_code="MOD-MECH", material_name="机械结构模块", unit="个", material_type="模块",
                       level_type="模块", lead_time=0, safety_stock=0, lot_size_rule="LFL", is_purchased=False),
        MaterialMaster(material_code="MOD-SENSOR", material_name="传感器模块", unit="个", material_type="模块",
                       level_type="模块", lead_time=0, safety_stock=0, lot_size_rule="LFL", is_purchased=False),
        MaterialMaster(material_code="MOD-POWER", material_name="电源模块", unit="个", material_type="模块",
                       level_type="模块", lead_time=0, safety_stock=0, lot_size_rule="LFL", is_purchased=False),
        MaterialMaster(material_code="MOD-ENCLOSURE", material_name="外壳包材模块", unit="个", material_type="模块",
                       level_type="模块", lead_time=0, safety_stock=0, lot_size_rule="LFL", is_purchased=False),
        MaterialMaster(material_code="MOD-OTHER", material_name="其他模块", unit="个", material_type="模块",
                       level_type="模块", lead_time=0, safety_stock=0, lot_size_rule="LFL", is_purchased=False),
        # 零件层（level_type='零件'）
        MaterialMaster(material_code="SA-001", material_name="温控主板组件", unit="个", material_type="半成品",
                       level_type="零件", lead_time=3, safety_stock=30, lot_size_rule="FOQ", lot_size_qty=50, is_purchased=False),
        MaterialMaster(material_code="SA-002", material_name="显示面板组件", unit="个", material_type="半成品",
                       level_type="零件", lead_time=2, safety_stock=25, lot_size_rule="LFL", is_purchased=False),
        MaterialMaster(material_code="SA-003", material_name="阀门执行器组件", unit="个", material_type="半成品",
                       level_type="零件", lead_time=4, safety_stock=20, lot_size_rule="FOQ", lot_size_qty=40, is_purchased=False),
        MaterialMaster(material_code="SA-004", material_name="传感器核心模块", unit="个", material_type="半成品",
                       level_type="零件", lead_time=5, safety_stock=15, lot_size_rule="FOQ", lot_size_qty=30, is_purchased=False),
        MaterialMaster(material_code="RM-001", material_name="PCB电路板", unit="块", material_type="原材料",
                       level_type="零件", lead_time=5, safety_stock=100, lot_size_rule="EOQ", lot_size_qty=500, is_purchased=True),
        MaterialMaster(material_code="RM-002", material_name="温度传感器芯片", unit="个", material_type="原材料",
                       level_type="零件", lead_time=7, safety_stock=200, lot_size_rule="EOQ", lot_size_qty=1000, is_purchased=True),
        MaterialMaster(material_code="RM-003", material_name="LCD显示屏", unit="块", material_type="原材料",
                       level_type="零件", lead_time=10, safety_stock=80, lot_size_rule="FOQ", lot_size_qty=100, is_purchased=True),
        MaterialMaster(material_code="RM-004", material_name="微型步进电机", unit="个", material_type="原材料",
                       level_type="零件", lead_time=4, safety_stock=50, lot_size_rule="FOQ", lot_size_qty=200, is_purchased=True),
        MaterialMaster(material_code="RM-005", material_name="铝合金外壳", unit="个", material_type="原材料",
                       level_type="零件", lead_time=3, safety_stock=60, lot_size_rule="MULT", lot_size_qty=100, is_purchased=True),
        MaterialMaster(material_code="RM-006", material_name="电源模块12V", unit="个", material_type="原材料",
                       level_type="零件", lead_time=6, safety_stock=150, lot_size_rule="EOQ", lot_size_qty=300, is_purchased=True),
        MaterialMaster(material_code="RM-007", material_name="不锈钢阀体", unit="个", material_type="原材料",
                       level_type="零件", lead_time=8, safety_stock=40, lot_size_rule="FOQ", lot_size_qty=50, is_purchased=True),
        MaterialMaster(material_code="RM-008", material_name="密封圈套件", unit="套", material_type="原材料",
                       level_type="零件", lead_time=2, safety_stock=200, lot_size_rule="MULT", lot_size_qty=500, is_purchased=True),
        MaterialMaster(material_code="RM-009", material_name="工业级传感器探头", unit="个", material_type="原材料",
                       level_type="零件", lead_time=12, safety_stock=50, lot_size_rule="FOQ", lot_size_qty=80, is_purchased=True),
    ]
    print(f"  物料: {len(materials)} 个（含{len([m for m in materials if m.level_type=='产品'])}个产品, {len([m for m in materials if m.level_type=='模块'])}个模块, {len([m for m in materials if m.level_type=='零件'])}个零件）")
    db.add_all(materials)
    db.flush()
    mid = {m.material_code: m.id for m in materials}

    # ===== 5. BOM（7 个） =====
    # FG-001 智能温控器
    b1 = BomHeader(bom_code="BOM-FG-001", product_id=mid["FG-001"], version="A", status="生效")
    db.add(b1); db.flush()
    db.add_all([
        BomLine(bom_header_id=b1.id, parent_item_id=mid["FG-001"], item_id=mid["SA-001"], quantity=1, position="A1", level=1, sort_order=1),
        BomLine(bom_header_id=b1.id, parent_item_id=mid["FG-001"], item_id=mid["SA-002"], quantity=1, position="A2", level=1, sort_order=2),
        BomLine(bom_header_id=b1.id, parent_item_id=mid["FG-001"], item_id=mid["RM-005"], quantity=1, position="A3", level=1, sort_order=3),
    ])

    # SA-001 温控主板组件
    b2 = BomHeader(bom_code="BOM-SA-001", product_id=mid["SA-001"], version="A", status="生效")
    db.add(b2); db.flush()
    db.add_all([
        BomLine(bom_header_id=b2.id, parent_item_id=mid["SA-001"], item_id=mid["RM-001"], quantity=1, level=2, sort_order=1),
        BomLine(bom_header_id=b2.id, parent_item_id=mid["SA-001"], item_id=mid["RM-002"], quantity=3, level=2, sort_order=2),
        BomLine(bom_header_id=b2.id, parent_item_id=mid["SA-001"], item_id=mid["RM-006"], quantity=1, level=2, sort_order=3),
    ])

    # SA-002 显示面板组件
    b3 = BomHeader(bom_code="BOM-SA-002", product_id=mid["SA-002"], version="A", status="生效")
    db.add(b3); db.flush()
    db.add_all([
        BomLine(bom_header_id=b3.id, parent_item_id=mid["SA-002"], item_id=mid["RM-003"], quantity=1, level=2, sort_order=1),
        BomLine(bom_header_id=b3.id, parent_item_id=mid["SA-002"], item_id=mid["RM-001"], quantity=1, level=2, sort_order=2),
    ])

    # FG-002 电动阀门
    b4 = BomHeader(bom_code="BOM-FG-002", product_id=mid["FG-002"], version="A", status="生效")
    db.add(b4); db.flush()
    db.add_all([
        BomLine(bom_header_id=b4.id, parent_item_id=mid["FG-002"], item_id=mid["SA-003"], quantity=1, position="B1", level=1, sort_order=1),
        BomLine(bom_header_id=b4.id, parent_item_id=mid["FG-002"], item_id=mid["RM-005"], quantity=1, position="B2", level=1, sort_order=2),
    ])

    # SA-003 阀门执行器组件
    b5 = BomHeader(bom_code="BOM-SA-003", product_id=mid["SA-003"], version="A", status="生效")
    db.add(b5); db.flush()
    db.add_all([
        BomLine(bom_header_id=b5.id, parent_item_id=mid["SA-003"], item_id=mid["RM-004"], quantity=1, level=2, sort_order=1),
        BomLine(bom_header_id=b5.id, parent_item_id=mid["SA-003"], item_id=mid["RM-007"], quantity=1, level=2, sort_order=2),
        BomLine(bom_header_id=b5.id, parent_item_id=mid["SA-003"], item_id=mid["RM-008"], quantity=2, level=2, sort_order=3),
        BomLine(bom_header_id=b5.id, parent_item_id=mid["SA-003"], item_id=mid["RM-006"], quantity=1, level=2, sort_order=4),
    ])

    # FG-003 工业传感器模组
    b6 = BomHeader(bom_code="BOM-FG-003", product_id=mid["FG-003"], version="A", status="生效")
    db.add(b6); db.flush()
    db.add_all([
        BomLine(bom_header_id=b6.id, parent_item_id=mid["FG-003"], item_id=mid["SA-004"], quantity=1, position="C1", level=1, sort_order=1),
        BomLine(bom_header_id=b6.id, parent_item_id=mid["FG-003"], item_id=mid["RM-005"], quantity=1, position="C2", level=1, sort_order=2),
        BomLine(bom_header_id=b6.id, parent_item_id=mid["FG-003"], item_id=mid["RM-009"], quantity=2, position="C3", level=1, sort_order=3),
    ])

    # SA-004 传感器核心模块
    b7 = BomHeader(bom_code="BOM-SA-004", product_id=mid["SA-004"], version="A", status="生效")
    db.add(b7); db.flush()
    db.add_all([
        BomLine(bom_header_id=b7.id, parent_item_id=mid["SA-004"], item_id=mid["RM-001"], quantity=1, level=2, sort_order=1),
        BomLine(bom_header_id=b7.id, parent_item_id=mid["SA-004"], item_id=mid["RM-002"], quantity=2, level=2, sort_order=2),
        BomLine(bom_header_id=b7.id, parent_item_id=mid["SA-004"], item_id=mid["RM-009"], quantity=1, level=2, sort_order=3),
    ])
    print(f"  BOM: 7 个")

    # ===== 6. 工艺路线（3 条） =====
    rt1 = RoutingHeader(routing_code="RT-FG-001", item_id=mid["FG-001"])
    db.add(rt1); db.flush()
    db.add_all([
        RoutingOperation(routing_header_id=rt1.id, seq_no=10, work_center_id=wc_map["WC01"], operation_name="SMT贴片", setup_time=0.5, run_time_per_unit=0.08, queue_time=0.5),
        RoutingOperation(routing_header_id=rt1.id, seq_no=20, work_center_id=wc_map["WC02"], operation_name="插件焊接", setup_time=0.3, run_time_per_unit=0.12, queue_time=1.0),
        RoutingOperation(routing_header_id=rt1.id, seq_no=30, work_center_id=wc_map["WC03"], operation_name="整机组装", setup_time=0.5, run_time_per_unit=0.15, queue_time=0.5),
        RoutingOperation(routing_header_id=rt1.id, seq_no=40, work_center_id=wc_map["WC05"], operation_name="功能测试与包装", setup_time=0.3, run_time_per_unit=0.06, queue_time=0.3),
    ])

    rt2 = RoutingHeader(routing_code="RT-FG-002", item_id=mid["FG-002"])
    db.add(rt2); db.flush()
    db.add_all([
        RoutingOperation(routing_header_id=rt2.id, seq_no=10, work_center_id=wc_map["WC01"], operation_name="SMT贴片", setup_time=0.4, run_time_per_unit=0.06, queue_time=0.5),
        RoutingOperation(routing_header_id=rt2.id, seq_no=20, work_center_id=wc_map["WC04"], operation_name="阀体组装", setup_time=0.6, run_time_per_unit=0.20, queue_time=1.0),
        RoutingOperation(routing_header_id=rt2.id, seq_no=30, work_center_id=wc_map["WC05"], operation_name="密封测试与包装", setup_time=0.4, run_time_per_unit=0.08, queue_time=0.5),
    ])

    rt3 = RoutingHeader(routing_code="RT-FG-003", item_id=mid["FG-003"])
    db.add(rt3); db.flush()
    db.add_all([
        RoutingOperation(routing_header_id=rt3.id, seq_no=10, work_center_id=wc_map["WC01"], operation_name="SMT精密贴片", setup_time=0.8, run_time_per_unit=0.10, queue_time=1.0),
        RoutingOperation(routing_header_id=rt3.id, seq_no=20, work_center_id=wc_map["WC03"], operation_name="精密组装", setup_time=0.6, run_time_per_unit=0.25, queue_time=0.5),
        RoutingOperation(routing_header_id=rt3.id, seq_no=30, work_center_id=wc_map["WC05"], operation_name="校准测试与包装", setup_time=0.5, run_time_per_unit=0.15, queue_time=0.5),
    ])
    print(f"  工艺路线: 3 条")

    # ===== 7. MPS =====
    today_d = date.today()
    for i in range(1, 9):
        d = today_d + timedelta(days=7*i)
        src = "销售订单" if i <= 3 else "预测"
        db.add(MpsEntry(item_id=mid["FG-001"], plan_date=d, quantity=100+(20 if i%2==0 else 0), source_type=src))
    for i in range(1, 5):
        d = today_d + timedelta(days=14*i)
        src = "销售订单" if i <= 2 else "预测"
        db.add(MpsEntry(item_id=mid["FG-002"], plan_date=d, quantity=50+(i%3)*10, source_type=src))
    for i in range(1, 3):
        d = today_d + timedelta(days=30*i)
        db.add(MpsEntry(item_id=mid["FG-003"], plan_date=d, quantity=30, source_type="预测"))
    print(f"  MPS: 14 条计划")

    # ===== 8. 库存 =====
    inv_data = {
        "SA-001": 45, "SA-002": 20, "SA-003": 15, "SA-004": 10,
        "RM-001": 200, "RM-002": 350, "RM-003": 60,
        "RM-004": 45, "RM-005": 70, "RM-006": 180,
        "RM-007": 30, "RM-008": 300, "RM-009": 40,
        "FG-001": 15, "FG-002": 10, "FG-003": 5,
    }
    for code, qty in inv_data.items():
        db.add(InventoryRecord(item_id=mid[code], warehouse_id=wh.id, on_hand_qty=qty))
    print(f"  库存: {len(inv_data)} 条")

    db.commit()
    db.close()

    print(f"\n✅ 演示数据初始化完成！")
    print(f"   物料 16 个 | BOM 7 个 | 工作中心 5 个 | 工艺路线 3 条")
    print(f"   MPS 14 条 | 库存 16 条")


if __name__ == "__main__":
    seed_demo_data()
