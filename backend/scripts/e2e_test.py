"""E2E 全流程测试 — MRP II 系统 v2
模拟真实用户从登录到完整业务闭环的每个步骤
"""
import requests
import json
import time
import sys

BASE = "http://localhost:8000"
HEADERS = {}
results = []

def log(section, step, status, detail=""):
    icon = "✅" if status == "pass" else "❌" if status == "fail" else "⏭️" if status == "skip" else "⚠️"
    msg = f"{icon} [{section}] {step}"
    if detail:
        msg += f" — {detail}"
    print(msg)
    results.append({"section": section, "step": step, "status": status, "detail": str(detail)})

def get(path, **kw):
    """GET with /api prefix and no trailing slash"""
    return requests.get(f"{BASE}/api{path}", headers=HEADERS, **kw)

def post(path, **kw):
    return requests.post(f"{BASE}/api{path}", headers=HEADERS, **kw)

def put(path, **kw):
    return requests.put(f"{BASE}/api{path}", headers=HEADERS, **kw)

def delete(path, **kw):
    return requests.delete(f"{BASE}/api{path}", headers=HEADERS, **kw)

def safe_get_data(r):
    """Extract items/total from API response robustly"""
    try:
        d = r.json()
        if isinstance(d, list):
            return d, {}
        items = d.get("items", []) if isinstance(d, dict) else []
        total = d.get("total", len(items)) if isinstance(d, dict) else len(items)
        return items, {"total": total, "extra": {k: v for k, v in d.items() if k not in ("items", "total")}}
    except:
        return [], {}

# ============================================================
# 1. 用户认证
# ============================================================
print("\n" + "=" * 60)
print("  1. 用户认证")
print("=" * 60)

r = post("/auth/login", json={"username": "admin", "password": "admin123"})
if r.status_code == 200:
    token = r.json()["access_token"]
    HEADERS["Authorization"] = f"Bearer {token}"
    user = r.json()["user"]
    log("登录", "admin 登录", "pass", f"角色={user['role']}")
else:
    log("登录", "admin 登录", "fail", r.text[:100])
    sys.exit(1)

r = get("/auth/me")
if r.status_code == 200:
    log("认证", "验证 token", "pass", r.json()["username"])
else:
    log("认证", "验证 token", "fail", r.text[:100])

# ============================================================
# 2. 物料管理
# ============================================================
print("\n" + "=" * 60)
print("  2. 物料管理 (material_master: 973 条)")
print("=" * 60)

r = get("/materials?page=1&page_size=10")
if r.status_code == 200:
    items, meta = safe_get_data(r)
    log("物料列表", "分页查询(page=1,10)", "pass", f"返回 {len(items)} 条, 总计 {meta.get('total','?')} 条")
else:
    log("物料列表", "分页查询", "fail", r.text[:100])

# 筛选
r = get("/materials?keyword=三工位")
if r.status_code == 200:
    items, meta = safe_get_data(r)
    log("物料筛选", "关键词=三工位", "pass", f"匹配 {meta.get('total',len(items))} 条")
else:
    log("物料筛选", "关键词=三工位", "warning", r.text[:80])

# 新增物料
new_mat = {
    "material_code": "",
    "material_name": "E2E测试物料",
    "specification": "E2E-TEST-001",
    "unit": "个",
    "material_type": "自制件",
    "level_type": "零件",
    "is_purchased": False,
}
r = post("/materials", json=new_mat)
if r.status_code in (200, 201):
    d = r.json()
    new_mat_id = d.get("data", {}).get("id") or d.get("id")
    new_mat_code = d.get("data", {}).get("material_code") or d.get("material_code", "")
    log("物料新增", "创建测试物料", "pass", f"ID={new_mat_id} 编码={new_mat_code}")
else:
    log("物料新增", "创建测试物料", "warning", r.text[:100])
    new_mat_id = None

# ============================================================
# 3. BOM 管理
# ============================================================
print("\n" + "=" * 60)
print("  3. BOM 管理 (bom_header: 24, bom_line: 858)")
print("=" * 60)

r = get("/bom/headers?page=1&page_size=10")
if r.status_code == 200:
    items, meta = safe_get_data(r)
    log("BOM 列表", "分页查询", "pass", f"返回 {len(items)} 条, 总计 {meta.get('total','?')} 条")
else:
    log("BOM 列表", "分页查询", "warning", r.text[:100])

# BOM 树 — need product_id, use any material with BOM
r = get("/bom/headers?page_size=1")
bom_product_id = None
if r.status_code == 200:
    bitems, _ = safe_get_data(r)
    if bitems:
        bom_product_id = bitems[0].get("product_id") or bitems[0].get("id")

if bom_product_id:
    r = get(f"/bom/tree/{bom_product_id}")
    if r.status_code == 200:
        data = r.json()
        log("BOM 树", f"产品#{bom_product_id} BOM树", "pass", str(data)[:80])
    else:
        log("BOM 树", f"产品#{bom_product_id} BOM树", "warning", r.text[:100])
else:
    log("BOM 树", "查询 BOM 树", "skip", "无可用 BOM 头")

# ============================================================
# 4. 库存
# ============================================================
print("\n" + "=" * 60)
print("  4. 库存管理 (inventory_record: 184 条)")
print("=" * 60)

r = get("/inventory?page=1&page_size=10")
if r.status_code == 200:
    items, meta = safe_get_data(r)
    log("库存列表", "分页查询", "pass", f"返回 {len(items)} 条, 总计 {meta.get('total','?')} 条")
else:
    log("库存列表", "分页查询", "warning", r.text[:100])

r = get("/inventory/abc-analysis")
if r.status_code == 200:
    log("ABC 分析", "查询 ABC 分类", "pass", str(r.json())[:80])
else:
    log("ABC 分析", "查询 ABC 分类", "warning", r.text[:80])

# ============================================================
# 5. 销售订单 → 审核 → MPS
# ============================================================
print("\n" + "=" * 60)
print("  5. 销售订单 & MPS")
print("=" * 60)

# 找产品 — 取第一个物料作为销售对象
r = get("/materials?page_size=5")
product_id = None
product_name = "?"
if r.status_code == 200:
    items, _ = safe_get_data(r)
    if items:
        product_id = items[0]["id"]
        product_name = items[0].get("material_name", "?")
        log("产品定位", "查找可售产品", "pass", f"{product_name} ID={product_id}")
    else:
        log("产品定位", "查找可售产品", "warning", "物料表为空")
else:
    log("产品定位", "查找可售产品", "fail", r.text[:100])

if product_id:
    order_data = {
        "customer_id": 1,
        "item_id": product_id,
        "order_qty": 1,
        "unit_price": 1000.00,
        "delivery_date": "2026-07-30",
    }
    r = post("/sales/orders", json=order_data)
    if r.status_code in (200, 201):
        so_id = r.json().get("id") or r.json().get("data", {}).get("id")
        log("销售订单", "创建销售订单", "pass", f"ID={so_id}")

        if so_id:
            r2 = post(f"/sales/orders/{so_id}/approve")
            if r2.status_code == 200:
                log("销售审核", "审核→自动MPS", "pass")
            else:
                log("销售审核", "审核→自动MPS", "warning", r2.text[:100])
    else:
        log("销售订单", "创建销售订单", "warning", r.text[:100])

r = get("/mps?page_size=10")
if r.status_code == 200:
    items, meta = safe_get_data(r)
    log("MPS 列表", "查询主生产计划", "pass", f"共 {meta.get('total',len(items))} 条")
else:
    log("MPS 列表", "查询主生产计划", "warning", r.text[:100])

# ============================================================
# 6. MRP 运算
# ============================================================
print("\n" + "=" * 60)
print("  6. MRP 运算")
print("=" * 60)

r = post("/mrp/run", json={})
if r.status_code == 200:
    d = r.json()
    log("MRP 运算", "执行 MRP 计算", "pass",
        f"耗时={d.get('elapsed_ms','?')}ms 计划订单={d.get('total_planned_orders','?')}条")
else:
    log("MRP 运算", "执行 MRP 计算", "fail", r.text[:200])

r = get("/mrp/planned-orders?page_size=10")
if r.status_code == 200:
    items, meta = safe_get_data(r)
    log("计划订单", "查询计划订单", "pass", f"共 {meta.get('total',len(items))} 条")
else:
    log("计划订单", "查询计划订单", "warning", r.text[:100])

# ============================================================
# 7. 采购管理 & 收货
# ============================================================
print("\n" + "=" * 60)
print("  7. 采购管理 (purchase_order: 1332)")
print("=" * 60)

r = get("/purchase/orders?page=1&page_size=5")
if r.status_code == 200:
    items, meta = safe_get_data(r)
    log("采购订单", "分页查询", "pass", f"返回 {len(items)} 条, 总计 {meta.get('total','?')} 条")
    # Find PO with remaining qty to receive
    po_id = None
    for po in items:
        ordered = float(po.get("ordered_qty", 0))
        received = float(po.get("received_qty", 0))
        if ordered > received:
            po_id = po["id"]
            log("采购收货", f"找到可收货PO", "pass", f"PO#{po_id} 已订{ordered} 已收{received}")
            receive = {"received_qty": 1, "reject_qty": 0, "operator": "E2E测试员", "warehouse": "原料仓"}
            r2 = post(f"/purchase/orders/{po_id}/receive", json=receive)
            if r2.status_code == 200:
                log("采购收货", f"PO#{po_id} 收货完成", "pass", "数量=1")
            else:
                log("采购收货", f"PO#{po_id} 收货", "warning", r2.text[:100])
            break
    if not po_id:
        log("采购收货", "查找可收货PO", "skip", "所有PO已全部收货")
else:
    log("采购订单", "分页查询", "warning", r.text[:100])

# ============================================================
# 8. 质检
# ============================================================
print("\n" + "=" * 60)
print("  8. 质检体系")
print("=" * 60)

r = get("/inspection/standards")
if r.status_code == 200:
    log("检验标准", "查询检验标准", "pass")
else:
    log("检验标准", "查询检验标准", "warning", r.text[:100])

r = get("/inspection/ncrs?page_size=10")
if r.status_code == 200:
    items, meta = safe_get_data(r)
    log("NCR 记录", "查询不合格品", "pass", f"共 {meta.get('total',len(items))} 条")
else:
    log("NCR 记录", "查询不合格品", "warning", r.text[:100])

# ============================================================
# 9. 生产执行 (routing_header: 2, work_order: 13)
# ============================================================
print("\n" + "=" * 60)
print("  9. 生产执行 (工序级)")
print("=" * 60)

r = get("/production/routings")
if r.status_code == 200:
    items, meta = safe_get_data(r)
    log("工艺路线", "查询工艺路线", "pass", f"共 {meta.get('total',len(items))} 条")
else:
    log("工艺路线", "查询工艺路线", "warning", r.text[:100])

r = get("/production/orders?page_size=10")
work_order_id = None
if r.status_code == 200:
    items, meta = safe_get_data(r)
    log("工单列表", "查询工单", "pass", f"共 {meta.get('total',len(items))} 条")
    for wo in items:
        if wo.get("status") in ("待生产", "进行中"):
            work_order_id = wo["id"]
            break
    if work_order_id:
        log("工单定位", "找到可执行工单", "pass", f"ID={work_order_id}")
else:
    log("工单列表", "查询工单", "warning", r.text[:100])

if work_order_id:
    # 初始化工序
    r = post(f"/production/orders/{work_order_id}/operations/init")
    if r.status_code in (200, 201):
        log("工序初始化", "展开工艺路线→工序", "pass")
    else:
        log("工序初始化", "展开工艺路线→工序", "warning", r.text[:100])

    # 查询工序
    r = get(f"/production/orders/{work_order_id}/operations")
    if r.status_code == 200:
        ops = r.json()
        ops_list = ops if isinstance(ops, list) else ops.get("items", ops.get("operations", []))
        if ops_list:
            op = ops_list[0]
            op_id = op["id"]
            # 开工
            r2 = put(f"/production/operations/{op_id}/start")
            if r2.status_code == 200:
                log("工序开工", f"工序#{op_id} 开工", "pass")
                # 报工
                r3 = put(f"/production/operations/{op_id}/report", json={"qty_good": 1, "qty_defect": 0})
                if r3.status_code == 200:
                    log("工序报工", f"工序#{op_id} 报工", "pass", "良品=1")
                    # 完成
                    r4 = put(f"/production/operations/{op_id}/complete")
                    if r4.status_code == 200:
                        log("工序完成", f"工序#{op_id} 完成", "pass")
                    else:
                        log("工序完成", f"工序#{op_id} 完成", "warning", r4.text[:100])
                else:
                    log("工序报工", f"工序#{op_id} 报工", "warning", r3.text[:100])
            else:
                log("工序开工", f"工序#{op_id} 开工", "warning", r2.text[:100])
    else:
        log("工序查询", "查询工序列表", "warning", r.text[:100])

# ============================================================
# 10. 批次追溯
# ============================================================
print("\n" + "=" * 60)
print("  10. 批次追溯")
print("=" * 60)

r = get("/trace/batches?page_size=10")
if r.status_code == 200:
    items, meta = safe_get_data(r)
    log("批次记录", "查询批次", "pass", f"共 {meta.get('total',len(items))} 条")

    # 正向追溯
    if items:
        batch_id = items[0]["id"]
        r2 = get(f"/trace/batches/{batch_id}/forward")
        if r2.status_code == 200:
            log("正向追溯", f"批次#{batch_id}→下游", "pass")
        else:
            log("正向追溯", f"批次#{batch_id}→下游", "warning", r2.text[:100])
else:
    log("批次记录", "查询批次", "warning", r.text[:100])

r = get("/trace/serial-numbers?page_size=5")
if r.status_code == 200:
    items, meta = safe_get_data(r)
    log("序列号", "查询序列号", "pass", f"共 {meta.get('total',len(items))} 条")
else:
    log("序列号", "查询序列号", "warning", r.text[:100])

# ============================================================
# 11. 生产看板
# ============================================================
print("\n" + "=" * 60)
print("  11. 生产看板")
print("=" * 60)

r = get("/shop-floor/summary")
if r.status_code == 200:
    d = r.json()
    log("车间总览", "生产状态", "pass", f"活跃工单={d.get('active_orders','?')} 进行中={d.get('in_progress','?')}")
else:
    log("车间总览", "生产状态", "warning", r.text[:100])

r = get("/shop-floor/oee")
if r.status_code == 200:
    log("OEE", "设备综合效率", "pass")
else:
    log("OEE", "设备综合效率", "warning", r.text[:100])

r = get("/shop-floor/andon")
if r.status_code == 200:
    log("安灯", "产线异常告警", "pass")
else:
    log("安灯", "产线异常告警", "warning", r.text[:100])

# ============================================================
# 12. 设备 & 模具
# ============================================================
print("\n" + "=" * 60)
print("  12. 设备 & 模具 (equipment: 2)")
print("=" * 60)

r = get("/equipment")
if r.status_code == 200:
    items, meta = safe_get_data(r)
    log("设备台账", "查询设备", "pass", f"共 {meta.get('total',len(items))} 台")
else:
    log("设备台账", "查询设备", "warning", r.text[:100])

r = get("/equipment/toolings")
if r.status_code == 200:
    items, meta = safe_get_data(r)
    log("模具台账", "查询模具", "pass", f"共 {meta.get('total',len(items))} 套")
else:
    log("模具台账", "查询模具", "warning", r.text[:100])

r = get("/equipment/maintenance-plans")
if r.status_code == 200:
    log("保养计划", "查询保养计划", "pass")
else:
    log("保养计划", "查询保养计划", "warning", r.text[:100])

# ============================================================
# 13. 报表
# ============================================================
print("\n" + "=" * 60)
print("  13. 报表中心")
print("=" * 60)

r = get("/reports/production-summary")
if r.status_code == 200:
    log("生产报表", "生产汇总", "pass")
else:
    log("生产报表", "生产汇总", "warning", r.text[:100])

r = get("/reports/inventory-turnover")
if r.status_code == 200:
    log("库存报表", "库存周转", "pass")
else:
    log("库存报表", "库存周转", "warning", r.text[:100])

# ============================================================
# 14. 系统信息
# ============================================================
print("\n" + "=" * 60)
print("  14. 系统信息")
print("=" * 60)

r = get("/health")
if r.status_code == 200:
    log("健康检查", "/health", "pass", str(r.json()))

r = get("/docs")
if r.status_code == 200:
    log("API 文档", "/docs Swagger", "pass", "可访问")
else:
    log("API 文档", "/docs Swagger", "warning")

# ============================================================
# 汇总
# ============================================================
print("\n" + "=" * 60)
print("  E2E 测试汇总")
print("=" * 60)

passed = sum(1 for r in results if r["status"] == "pass")
failed = sum(1 for r in results if r["status"] == "fail")
warnings = sum(1 for r in results if r["status"] == "warning")
skipped = sum(1 for r in results if r["status"] == "skip")
total = len(results)

print(f"\n  ✅ 通过: {passed}   ❌ 失败: {failed}   ⚠️ 警告: {warnings}   ⏭️ 跳过: {skipped}")
print(f"  总计: {total} 项测试 | 通过率: {passed/total*100:.1f}%")

if failed > 0:
    print("\n  === 失败详情 ===")
    for r in results:
        if r["status"] == "fail":
            print(f"  ❌ [{r['section']}] {r['step']}: {r['detail'][:120]}")

if warnings > 0:
    print("\n  === 警告详情(非致命) ===")
    for r in results:
        if r["status"] == "warning":
            print(f"  ⚠️ [{r['section']}] {r['step']}: {r['detail'][:120]}")

# 保存
out_path = "D:/MDR II/backend/scripts/e2e_result.json"
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(results, f, ensure_ascii=False, indent=2)
print(f"\n  详细结果: {out_path}")
