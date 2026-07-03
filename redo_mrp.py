import urllib.request, json, os, sys
os.environ['DB_BACKEND']='mysql'
sys.path.insert(0,'c:/Users/20210817/WorkBuddy/2026-06-30-14-24-08/mrp-system/backend')
from app.core.database import SessionLocal
from app.models.order import PurchaseOrder
from sqlalchemy import text

# Clear
print("1. 清空...")
db=SessionLocal()
db.execute(text('SET FOREIGN_KEY_CHECKS=0'))
for t in ['purchase_order','mrp_exception']: db.execute(text(f'DELETE FROM {t}')); db.commit()
db.execute(text('SET FOREIGN_KEY_CHECKS=1')); db.commit()
db.close()

# MRP
print("2. MRP...")
req=urllib.request.Request('http://localhost:8000/api/mrp/run',
    data=json.dumps({'horizon_days':90,'time_fence_days':7}).encode(),method='POST')
req.add_header('Content-Type','application/json')
plans=json.loads(urllib.request.urlopen(req).read())['data']['planned_orders']
print(f"   计划订单: {len(plans)}条")

# Convert
print("3. 转换...")
req2=urllib.request.Request('http://localhost:8000/api/mrp/convert-to-orders',
    data=json.dumps({'planned_orders':plans}).encode(),method='POST')
req2.add_header('Content-Type','application/json')
r2=json.loads(urllib.request.urlopen(req2).read())
print(f"   {r2['message']}")

# Verify
print("\n4. 验证:")
db=SessionLocal()
pos=db.query(PurchaseOrder).order_by(PurchaseOrder.id).limit(5).all()
print(f"   PO总数: {db.query(PurchaseOrder).count()}")
for po in pos:
    mn=(po.item.material_name if po.item else '?')[:20]
    print(f"   {mn}: qty={po.order_qty} | 单价={po.unit_price:.0f} | 金额={po.total_amount:.0f}")
    print(f"      品牌={str(po.brand)[:25]} | 提交人={po.submitter} | 链接={str(po.supplier_link)[:50]}")
db.close()
print("\n✅ 完成！刷新采购页面")
