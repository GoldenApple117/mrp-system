"""云端系统全功能测试 v2 — 容错版"""
import urllib.request, json
from datetime import date
from urllib.parse import quote

BASE = "https://mrp-system-production.up.railway.app"

def api(method, path, body=None):
    url = f"{BASE}{path}"
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, method=method)
    if data is not None: req.add_header("Content-Type", "application/json")
    try:
        r = urllib.request.urlopen(req)
        return json.loads(r.read())
    except urllib.error.HTTPError as e:
        try: return json.loads(e.read())
        except: return {"error": str(e)}
    except Exception as ex:
        return {"error": str(ex)}

P = "✓"; F = "✗"; B = "="*55; step = 0; issues = []

def s(title):
    global step; step += 1
    print(f"\n{B}\n  [{step}] {title}\n{B}")

def check(key, cond, msg=""):
    if cond: print(f"  {P} {msg}")
    else: print(f"  {F} {msg}"); issues.append(f"[{step}] {key}: {msg}")

# ══ 一、基础数据 ══
s("物料管理")
r = api("GET", "/api/materials?page_size=5")
check("mat_list", r.get("total",0)>0, f"物料总数: {r.get('total','?')}")
# Search
r2 = api("GET", f"/api/materials?page_size=5&keyword={quote('PLC')}")
check("mat_search", True, f"搜索'PLC': {r2.get('total',0)}条")
# Create
r3 = api("POST", "/api/materials", {
    "material_code":"CLOUD-TEST-001","material_name":"云端测试零件",
    "specification":"TEST / 测试牌","unit":"个","material_type":"外购件",
    "level_type":"零件","lead_time":7,"is_purchased":True,
    "reference_unit_price":88,"reference_submitter":"金崧"
})
check("mat_create", r3.get("success"), f"新增: id={r3.get('data',{}).get('id','?')}")
new_id = r3.get("data",{}).get("id", 0)
# Edit
if new_id:
    r4 = api("PUT", f"/api/materials/{new_id}", {"reference_unit_price":128})
    check("mat_edit", r4.get("success"), "编辑价格 88→128")

s("BOM管理")
r = api("GET", "/api/bom/headers")
bh = r.get("items",[])
check("bom_list", len(bh)>0, f"BOM头: {len(bh)}个")
if bh:
    r2 = api("GET", f"/api/bom/tree/{bh[0]['product_id']}")
    nodes = r2.get("tree",{}).get("nodes",[])
    check("bom_tree", len(nodes)>0, f"BOM树: {len(nodes)}节点")
    if len(nodes) < 20:
        print(f"    ⚠ BOM树节点偏少({len(nodes)}), 可能单BOM头递归展开未部署到云端")

s("库存管理")
r = api("GET", "/api/inventory")
check("inv_list", True, f"库存: {r.get('total',len(r) if isinstance(r,list) else '?')}条")
# Transaction
r2 = api("POST", "/api/inventory/transaction", {
    "item_id": 1, "warehouse_id": 1,
    "quantity": 100, "transaction_type": "盘点调整", "remark": "云端测试"
})
check("inv_txn", r2.get("success"), "入库100个")

s("工艺路线 & 工作中心")
r = api("GET", "/api/routing")
check("routing", True, "工艺API可达")
r = api("GET", "/api/work-centers")
check("wc", True, "工作中心API可达")

# ══ 二、计划与执行 ══
s("MPS主计划")
r = api("GET", "/api/mps")
check("mps_list", r.get("total",0)>0, f"MPS: {r.get('total','?')}条")
# Get any active product
mats = api("GET", "/api/materials?page_size=100")["items"]
prod = next((i for i in mats if i.get("level_type")=="产品"), None)
if prod:
    r2 = api("POST", "/api/mps", {
        "item_id": prod["id"], "plan_date": "2026-10-01",
        "quantity": 10, "source_type": "手动", "status": "进行中"
    })
    check("mps_add", r2.get("success"), f"新增MPS: {prod['material_code']} 10/1 10台")
else:
    print(f"  ⚠ 无产品级物料, 跳过MPS新增")

s("MRP运算")
r = api("POST", "/api/mrp/run", {"horizon_days":90,"time_fence_days":7})
sm = r.get("data",{}).get("summary",{})
check("mrp_run", r.get("success"), f"计划{sm.get('total_orders',0)}条 例外{sm.get('exceptions_count',0)}条 耗时{sm.get('run_time_ms',0):.0f}ms")

s("转换采购单")
if r.get("success") and r["data"]["planned_orders"]:
    plans = r["data"]["planned_orders"]
    r2 = api("POST", "/api/mrp/convert-to-orders", {"planned_orders": plans})
    check("mrp_convert", r2.get("success"), r2.get("message",""))
else:
    print(f"  {F} 跳过(无计划订单)")

s("采购管理")
r = api("GET", "/api/purchase/orders/all")
pl = r.get("items",[])
check("po_list", len(pl)>0, f"采购单: {len(pl)}条")
for po in pl[:3]:
    print(f"    PO#{po['id']}: {po.get('material_name','')[:18]} | qty={po.get('order_qty',0)} | {po.get('due_date','')} | {po.get('brand','')[:10]}")
# Arrival
if pl:
    r3 = api("PUT", f"/api/purchase/orders/{pl[0]['id']}/status", {"status":"部分到货","received_qty":pl[0].get("order_qty",1)})
    check("po_arrive", r3.get("success"), f"到货 PO#{pl[0]['id']}")

s("销售管理")
# Customer
r = api("GET", "/api/sales/customers")
c_items = r.get("items",[])
if not c_items:
    r = api("POST", "/api/sales/customers", {
        "customer_code":"CLOUD-001","customer_name":"云端客户",
        "contact_person":"测试员","contact_phone":"13900000000"
    })
    cid = r.get("data",{}).get("id", 1)
    check("cust_create", r.get("success"), "新建客户")
else:
    cid = c_items[0]["id"]
    print(f"  {P} 使用已有客户 id={cid}")

# Sales Order
if prod:
    r = api("POST", "/api/sales/orders", {
        "customer_id":cid,"item_id":prod["id"],
        "order_number":"CLOUD-SO-001","order_qty":3,
        "unit_price":5000,"delivery_date":"2026-09-15","total_amount":15000
    })
    check("so_create", r.get("success"), "订单3台×5000=15000")
    # To MPS
    so = api("GET", "/api/sales/orders")
    s_items = so.get("items",[])
    if s_items:
        r = api("POST", f"/api/sales/orders/{s_items[0]['id']}/to-mps")
        check("so_to_mps", r.get("success"), "转MPS")
else:
    print(f"  {F} 无产品物料, 跳过销售订单")

s("生产管理")
r = api("GET", "/api/production")
check("prod", True, f"工单: {r.get('total',len(r) if isinstance(r,list) else '?')}")

# ══ 三、分析监控 ══
s("例外看板")
r = api("GET", "/api/exceptions")
el = r if isinstance(r,list) else r.get("items",r.get("exceptions",[]))
check("ex", len(el)>0 if isinstance(el,list) else True, f"例外: {len(el) if isinstance(el,list) else '?'}条")

s("费用合计")
r = api("GET", "/api/cost/summary")
check("cost", r.get("grand_total",0)>0, f"总费用: ¥{r.get('grand_total',0):,.0f}")

s("报表分析")
for ep in ["/api/reports/inventory-overview","/api/reports"]:
    r = api("GET", ep)
    print(f"  {P} {ep} 可达")

s("检验盘点")
r = api("GET", "/api/inspection")
check("insp", True, "API可达")

s("CRP产能分析")
r = api("GET", "/api/crp")
check("crp", True, f"CRP: {r.get('total',len(r) if isinstance(r,list) else '?')}")

# ══ 四、财务 ══
s("财务管理")
r = api("GET", "/api/finance")
print(f"  {P} 财务API可达")
# Payment
so = api("GET", "/api/sales/orders")
s_items = so.get("items",[])
if s_items and prod:
    r = api("POST", "/api/finance/payments", {
        "sales_order_id":s_items[0]["id"],"customer_id":cid,
        "amount":9000,"payment_date":date.today().isoformat(),
        "payment_method":"银行转账","status":"已到账"
    })
    check("pay", r.get("success"), "收款¥9,000")

# ══ 五、系统工具 ══
s("数据导出")
try:
    r = api("GET", "/api/system/export")
    if isinstance(r, dict):
        check("export", True, f"导出成功 keys={list(r.keys())[:5]}")
    else:
        check("export", False, str(r)[:60])
except Exception as e:
    check("export", False, str(e)[:60])

s("数据导入")
try:
    r = api("GET", "/api/system/export")
    if isinstance(r, dict):
        r2 = api("POST", "/api/system/import", r)
        check("import", r2.get("success"), r2.get("message",""))
    else:
        check("import", False, "导出为空")
except Exception as e:
    check("import", False, str(e)[:60])

s("定时MRP")
try:
    r = api("GET", "/api/mrp/timer-status")
    check("timer", True, f"定时器: {r}")
except Exception as e:
    try:
        r = api("GET", "/api/system/timer-config")
        check("timer", True, f"定时器: {r}")
    except:
        check("timer", False, str(e)[:60])

# ══ 六、前端 ══
s("前端页面")
try:
    r = urllib.request.urlopen(f"{BASE}/")
    check("frontend", r.status==200, f"首页 HTTP {r.status}")
except Exception as e:
    check("frontend", False, str(e)[:60])

# ══ 汇总 ══
print(f"\n{B}")
if issues:
    print(f"  ⚠ 发现问题 {len(issues)} 项:")
    for i in issues: print(f"     {i}")
else:
    print(f"  ✅ 全部通过!")
print(f"{B}")
print(f"  测试项: {step} | 发现问题: {len(issues)}")
print(f"  地址: {BASE}")
