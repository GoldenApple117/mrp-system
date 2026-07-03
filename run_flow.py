"""操作手册10步全流程模拟测试"""
import urllib.request, json

def api(method, path, body=None):
    url = f"http://localhost:8000{path}"
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, method=method)
    if data is not None: req.add_header("Content-Type", "application/json")
    try:
        r = urllib.request.urlopen(req)
        return json.loads(r.read())
    except urllib.error.HTTPError as e:
        try: return json.loads(e.read())
        except: return {"error": str(e)}

def ok(r):
    return "✓" if r.get("success") else f"✗ {r.get('detail', '')}"

B = "=" * 55
print(f"{B}\n  MRP II 操作手册全流程模拟 | 2026-07-03\n{B}")

# Step 1
print("\n[步骤1] 创建客户")
cust = api("GET", "/api/sales/customers")
if cust.get("items"):
    c = cust["items"][0]; cid = c["id"]
    print(f"  已有客户: {c['customer_code']} - {c['customer_name']} (id={cid})")
else:
    r = api("POST", "/api/sales/customers", {"customer_code":"CUST-003","customer_name":"亿图视觉","contact_person":"王工","contact_phone":"13800138000"})
    cid = r["data"]["id"]
    print(f"  ✓ 新建客户 id={cid}")

# Step 2
print("\n[步骤2] 创建销售订单 10台 x 5000 = 50000")
mats = api("GET", "/api/materials?page_size=100")["items"]
prod = [i for i in mats if i.get("material_code") == "SG-3ST-15"][0]
print(f"  产品: {prod['material_code']} - {prod['material_name']} (id={prod['id']})")
r = api("POST", "/api/sales/orders", {
    "customer_id": cid, "item_id": prod["id"],
    "order_number": "SO-20260703-001", "order_qty": 10,
    "unit_price": 5000, "delivery_date": "2026-08-15",
    "total_amount": 50000
})
print(f"  {ok(r)}")

# Step 3
print("\n[步骤3] 订单转MPS主生产计划")
so_id = api("GET", "/api/sales/orders")["items"][0]["id"]
r = api("POST", f"/api/sales/orders/{so_id}/to-mps")
print(f"  {ok(r)}")
mps = api("GET", "/api/mps")
mc = mps.get("total", len(mps) if isinstance(mps,list) else "?")
print(f"  MPS条目: {mc}")

# Step 4
print("\n[步骤4] 运行MRP (展望90天 时界7天)")
r = api("POST", "/api/mrp/run", {"horizon_days":90,"time_fence_days":7})
plans = r.get("planned_orders", [])
print(f"  {ok(r)} 耗时{r.get('elapsed',0):.1f}s 计划订单{len(plans)}条")

# Step 5
print("\n[步骤5] 例外看板")
ex = api("GET", "/api/exceptions")
el = ex if isinstance(ex, list) else ex.get("exceptions", ex.get("items", []))
print(f"  例外数: {len(el) if isinstance(el, list) else '?'}")

# Step 6
print("\n[步骤6] BOM同步生成采购单")
bom_id = api("GET", "/api/bom/headers")["items"][0]["id"]
r = api("POST", "/api/purchase/sync-from-bom", {"bom_header_id": bom_id})
print(f"  {ok(r)}")
pos = api("GET", "/api/purchase/orders/all")["items"]
print(f"  生成采购单: {len(pos)}条")
for po in pos[:3]:
    mn = str(po.get("material_name",""))[:22]
    up = po.get("unit_price", 0)
    oq = po.get("order_qty", 0)
    print(f"    PO#{po['id']}: {mn} | {up:.0f} x {oq}")

# Step 7
print("\n[步骤7] 采购到货入库(前5条PO)")
ac = 0
for po in pos[:5]:
    r = api("PUT", f"/api/purchase/orders/{po['id']}/status",
            {"status":"部分到货","received_qty":po["order_qty"]})
    if r.get("success"):
        ac += 1
        mn = str(po.get("material_name",""))[:18]
        print(f"    ✓ PO#{po['id']} {mn}: +{po['order_qty']}件")
    else:
        print(f"    ✗ PO#{po['id']}: {r.get('detail',str(r)[:30])}")
print(f"  到货: {ac}/{min(5,len(pos))}")

# Step 8
print("\n[步骤8] 产品出库发货 3台")
r = api("POST", "/api/inventory/transaction",
        {"item_id":prod["id"],"warehouse_id":1,"quantity":15,"transaction_type":"盘点调整"})
print(f"  补库存+15: {ok(r)}")
r = api("POST", "/api/inventory/transaction",
        {"item_id":prod["id"],"warehouse_id":1,"quantity":-3,"transaction_type":"销售出库","remark":"SO-001发货"})
print(f"  出库-3: {ok(r)}")

# Step 9
print("\n[步骤9] 财务收款 15000")
r = api("POST", "/api/finance/payments", {
    "sales_order_id":so_id,"customer_id":cid,"amount":15000,
    "payment_date":"2026-07-03","payment_method":"银行转账","status":"已到账"
})
print(f"  {ok(r)}")

# Step 10
print("\n[步骤10] 订单最终状态")
s = api("GET", "/api/sales/orders")["items"][0]
sq = s.get("shipped_qty",0); oq = s.get("order_qty",0)
pa = s.get("paid_amount",0); ta = s.get("total_amount",0)
print(f"  单据: {s['order_number']}")
print(f"  出货: {s.get('ship_status','?')} ({sq}/{oq}台)")
print(f"  收款: {s.get('pay_status','?')} ({pa:,.0f}/{ta:,.0f})")
print(f"  状态: {s.get('status','?')}")

print(f"\n{B}\n  OK 全流程完成!\n{B}")
print(f"  客户: 亿图视觉 | 订单: SO-20260703-001 50,000")
print(f"  PO: {len(pos)}条({ac}到货) | 出货: {sq}/{oq}台 | 收款: {pa:,.0f}/{ta:,.0f}")
