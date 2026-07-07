"""从生产环境导出的JSON数据导入本地 MySQL 数据库"""
import sys, os, json
from datetime import date, datetime
from collections import defaultdict

os.environ['DB_BACKEND'] = 'mysql'
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# 提前加载环境
from app.core.config import DATABASE_URL
from app.core.database import engine, Base, SessionLocal
from app.core.security import hash_password

# 导入所有模型以注册到Base
from app.models import *
from app.models.material import MaterialMaster
from app.models.supplier import Supplier
from app.models.sales import Customer
from app.models.mps import MpsEntry
from app.models.inventory import InventoryRecord, Warehouse
from app.models.order import PurchaseOrder
from app.models.routing import WorkCenter
from app.models.user import User

# 创建表
Base.metadata.create_all(bind=engine)

# 模型
from app.models.material import MaterialMaster
from app.models.supplier import Supplier
from app.models.sales import Customer
from app.models.mps import MpsEntry
from app.models.inventory import InventoryRecord, Warehouse
from app.models.order import PurchaseOrder
from app.models.routing import WorkCenter
from app.models.user import User

# 读取导出数据
backup_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'production_data_export.json')
if not os.path.exists(backup_path):
    backup_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'production_data_export.json')
with open(backup_path, 'r', encoding='utf-8') as f:
    data = json.load(f)

db = SessionLocal()
counts = {}

try:
    # 1. 默认管理员
    if not db.query(User).filter(User.username == 'admin').first():
        db.add(User(username='admin', password_hash=hash_password('admin123'), role='admin', is_approved=True))
        db.flush()
    if not db.query(User).filter(User.username == 'user1').first():
        db.add(User(username='user1', password_hash=hash_password('123456'), role='normal', is_approved=False))
        db.flush()
    counts['users'] = 2

    # 2. 物料
    materials = data.get('materials', [])
    for m in materials:
        existing = db.query(MaterialMaster).filter(MaterialMaster.material_code == m.get('material_code', '')).first()
        if not existing:
            db.add(MaterialMaster(
                material_code=m.get('material_code', ''),
                material_name=m.get('material_name', ''),
                specification=m.get('specification', ''),
                material_type=m.get('material_type', '零件'),
                unit=m.get('unit', '个'),
                lead_time=m.get('lead_time', 0) or 0,
                safety_stock=m.get('safety_stock', 0) or 0,
                lot_size_rule=m.get('lot_size_rule', 'LFL'),
                level_type=m.get('level_type', '零件'),
                is_purchased=m.get('is_purchased', True),
                reference_unit_price=m.get('reference_unit_price', 0) or 0,
                reference_submitter=m.get('reference_submitter', '') or '',
                reference_link=m.get('reference_link', '') or '',
                is_active=True,
            ))
    db.flush()
    counts['materials'] = len(materials)

    # 3. 客户
    for c in data.get('customers', []):
        existing = db.query(Customer).filter(Customer.customer_code == c.get('customer_code', '')).first()
        if not existing:
            db.add(Customer(
                customer_code=c.get('customer_code', ''),
                customer_name=c.get('customer_name', ''),
                contact_person=c.get('contact_person', ''),
                contact_phone=c.get('contact_phone', ''),
                address=c.get('address', ''),
                is_active=True,
            ))
    db.flush()
    counts['customers'] = len(data.get('customers', []))

    # 4. 供应商
    for s in data.get('suppliers', []):
        existing = db.query(Supplier).filter(Supplier.supplier_code == s.get('supplier_code', '')).first()
        if not existing:
            db.add(Supplier(
                supplier_code=s.get('supplier_code', ''),
                supplier_name=s.get('supplier_name', ''),
                contact_person=s.get('contact_person', ''),
                contact_phone=s.get('contact_phone', ''),
                purchase_link=s.get('purchase_link', '') or '',
                is_active=True,
            ))
    db.flush()
    counts['suppliers'] = len(data.get('suppliers', []))

    # 5. 工作中心
    for wc in data.get('work_centers', []):
        existing = db.query(WorkCenter).filter(WorkCenter.center_code == wc.get('center_code', '')).first()
        if not existing:
            db.add(WorkCenter(
                center_code=wc.get('center_code', ''),
                center_name=wc.get('center_name', ''),
                capacity_per_day=wc.get('capacity_per_day', 8) or 8,
                efficiency=wc.get('efficiency', 85) or 85,
                is_active=True,
            ))
    db.flush()
    counts['work_centers'] = len(data.get('work_centers', []))

    # 6. 仓库
    wh = db.query(Warehouse).filter(Warehouse.warehouse_code == 'WH01').first()
    if not wh:
        db.add(Warehouse(warehouse_code='WH01', warehouse_name='主仓库'))
        db.flush()
    wh = db.query(Warehouse).filter(Warehouse.warehouse_code == 'WH01').first()

    # 7. 库存
    inv_items = data.get('inventory', [])
    if isinstance(inv_items, dict):
        inv_items = inv_items.get('items', [])
    inv_count = 0
    for inv in inv_items:
        code = inv.get('material_code', inv.get('item_code', ''))
        mat = db.query(MaterialMaster).filter(MaterialMaster.material_code == code).first()
        if mat and wh:
            existing = db.query(InventoryRecord).filter(
                InventoryRecord.item_id == mat.id,
                InventoryRecord.warehouse_id == wh.id,
            ).first()
            if not existing:
                db.add(InventoryRecord(
                    item_id=mat.id,
                    warehouse_id=wh.id,
                    on_hand_qty=inv.get('on_hand_qty', inv.get('on_hand', 0)) or 0,
                    allocated_qty=inv.get('allocated_qty', inv.get('allocated', 0)) or 0,
                    reserved_qty=inv.get('reserved_qty', inv.get('reserved', 0)) or 0,
                ))
                inv_count += 1
    db.flush()
    counts['inventory'] = inv_count

    # 8. MPS
    mps_count = 0
    for m in data.get('mps', []):
        code = m.get('material_code', m.get('product_code', ''))
        mat = db.query(MaterialMaster).filter(MaterialMaster.material_code == code).first()
        if mat:
            plan_date_str = m.get('plan_date', m.get('start_date', ''))
            try:
                plan_date = date.fromisoformat(plan_date_str) if isinstance(plan_date_str, str) else date.today()
            except:
                plan_date = date.today()
            existing_mps = db.query(MpsEntry).filter(
                MpsEntry.item_id == mat.id,
                MpsEntry.plan_date == plan_date,
            ).first()
            if not existing_mps:
                db.add(MpsEntry(
                    item_id=mat.id,
                    plan_date=plan_date,
                    quantity=m.get('quantity', 0) or 0,
                    source_type=m.get('source_type', '手动'),
                    source_id=str(m.get('source_id', '')),
                    status=m.get('status', '进行中'),
                ))
                mps_count += 1
    db.flush()
    counts['mps'] = mps_count

    # 9. 采购订单（仅导入部分最近的）
    po_count = 0
    for po in (data.get('purchase_orders', []) or [])[-50:]:  # 最近50条
        code = po.get('material_code', '')
        mat = db.query(MaterialMaster).filter(MaterialMaster.material_code == code).first()
        sup = db.query(Supplier).first()
        if mat and sup:
            due_str = po.get('due_date', '')
            try:
                due_date = date.fromisoformat(due_str) if isinstance(due_str, str) else date.today()
            except:
                due_date = date.today()
            db.add(PurchaseOrder(
                po_number=po.get('po_number', f'PO-IMPORT-{po_count:04d}'),
                supplier_id=sup.id,
                item_id=mat.id,
                order_qty=po.get('order_qty', 0) or 0,
                received_qty=po.get('received_qty', 0) or 0,
                due_date=due_date,
                status=po.get('status', '已下单'),
                unit_price=po.get('unit_price', 0) or 0,
                total_amount=po.get('total_amount', 0) or 0,
                brand=po.get('brand', '') or '',
                supplier_link=po.get('supplier_link', '') or '',
                source_type='导入',
            ))
            po_count += 1
    db.flush()
    counts['purchase_orders'] = po_count

    db.commit()
    print(f'✅ 数据导入完成！')
    for k, v in counts.items():
        print(f'   {k}: {v}')

except Exception as e:
    db.rollback()
    print(f'❌ 导入失败: {e}')
    import traceback
    traceback.print_exc()
finally:
    db.close()
