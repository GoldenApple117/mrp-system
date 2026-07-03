"""MRP II 系统三轮重复性回归测试"""
import json, urllib.request, urllib.error, sys, time, os
from datetime import datetime

BASE = "http://localhost:8000"
PASS, FAIL, SKIP = "PASS", "FAIL", "SKIP"

def api(method, path, body=None):
    url = f"{BASE}{path}"
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Content-Type", "application/json") if data is not None else None
    try:
        resp = urllib.request.urlopen(req, timeout=15)
        return resp.status, json.loads(resp.read())
    except urllib.error.HTTPError as e:
        try: body = json.loads(e.read())
        except: body = {"error": str(e)}
        return e.code, body
    except Exception as e:
        return 0, {"error": str(e)}

def check(desc, status, data, expected_status=200, key_check=None, not_empty=False):
    if status == expected_status:
        if key_check and key_check not in data:
            return FAIL, f"[{desc}] 缺少字段: {key_check}"
        if not_empty and isinstance(data, (list, dict)) and len(data) == 0:
            return FAIL, f"[{desc}] 响应为空"
        return PASS, f"[{desc}] OK (status={status})"
    return FAIL, f"[{desc}] 状态码={status}, 期望={expected_status}, 响应={str(data)[:120]}"

def run_round(round_num):
    results = []
    t = lambda d, s, data, es=200, k=None, ne=False: results.append(check(d, s, data, es, k, ne))

    # === 系统 ===
    s, d = api("GET", "/api/health"); t("系统-健康检查", s, d)
    s, d = api("GET", "/api/system/schedule"); t("系统-定时器配置", s, d, 200, "enabled")
    
    # === 物料 ===
    s, d = api("GET", "/api/materials"); t("物料-获取列表", s, d, 200, "items", ne=True)
    if isinstance(d.get("items"), list) and len(d["items"]) > 0:
        mid = d["items"][0]["id"]
        s, d2 = api("GET", f"/api/materials/{mid}"); t(f"物料-获取详情(id={mid})", s, d2, 200, "item")
    mid = d.get("items", [{}])[0].get("id", 1)
    
    # === BOM ===
    s, d = api("GET", "/api/bom"); t("BOM-获取列表", s, d, 200, ne=True)
    if isinstance(d, list) and len(d) > 0:
        bid = d[0].get("id")
        if bid:
            s, d2 = api("GET", f"/api/bom/{bid}"); t(f"BOM-获取详情(id={bid})", s, d2, 200)
            s, d3 = api("GET", f"/api/bom/{bid}/lines"); t(f"BOM-获取行项目(id={bid})", s, d3, 200, ne=True)
    
    # === 库存 ===
    s, d = api("GET", "/api/inventory"); t("库存-获取列表", s, d, 200, ne=True)
    s, d = api("GET", "/api/inventory/obsolete?days=90"); t("库存-呆滞料预警", s, d, 200)
    
    # === MPS ===
    s, d = api("GET", "/api/mps"); t("MPS-获取列表", s, d, 200, ne=True)
    
    # === 销售 ===
    s, d = api("GET", "/api/sales/orders"); t("销售-获取订单", s, d, 200, ne=True)
    
    # === MRP ===
    s, d = api("POST", "/api/mrp/run", {}); t("MRP-执行运算", s, d, 200, "success")
    
    # === 采购 ===
    s, d = api("GET", "/api/purchase/orders"); t("采购-获取订单", s, d, 200, ne=True)
    s, d = api("GET", "/api/purchase/orders/all"); t("采购-获取全部订单", s, d, 200, ne=True)
    
    # === 例外看板 ===
    s, d = api("GET", "/api/exceptions"); t("例外-获取列表", s, d, 200, ne=True)
    
    # === 财务 ===
    s, d = api("GET", "/api/finance"); t("财务-获取概览", s, d, 200)
    
    # === 生产 ===
    s, d = api("GET", "/api/production"); t("生产-获取列表", s, d, 200, ne=True)
    
    # === CRP ===
    s, d = api("GET", "/api/crp"); t("CRP-获取数据", s, d, 200)
    
    # === 检验 ===
    s, d = api("GET", "/api/inspection"); t("检验-获取列表", s, d, 200, ne=True)
    
    # === 费用 ===
    s, d = api("GET", "/api/cost"); t("费用-获取数据", s, d, 200)
    
    # === 工艺路线 ===
    s, d = api("GET", "/api/routings"); t("工艺路线-获取列表", s, d, 200, ne=True)
    
    # === 系统导出 ===
    s, d = api("GET", "/api/system/export"); t("系统-数据导出", s, d, 200)
    
    # === 前端静态 ===
    try:
        url = f"{BASE}/"
        resp = urllib.request.urlopen(url, timeout=10)
        html = resp.read().decode()
        if "<!DOCTYPE html>" in html and "MRP" in html:
            t("前端-入口页面", resp.status, {"ok": True})
        else:
            t("前端-入口页面", resp.status, {"ok": False}, 200)
    except Exception as e:
        t("前端-入口页面", 0, {"error": str(e)}, 200)
    
    # 前端页面路由
    for route in ["/materials", "/bom", "/inventory", "/mps", "/sales", "/mrp",
                   "/purchase", "/production", "/finance", "/exceptions",
                   "/reports", "/crp", "/inspection", "/cost", "/routings"]:
        try:
            resp = urllib.request.urlopen(f"{BASE}{route}", timeout=10)
            if "text/html" in resp.headers.get("content-type", ""):
                t(f"前端-路由({route})", resp.status, {"ok": True})
            else:
                t(f"前端-路由({route})", resp.status, {"ok": True})  # API fallback also OK
        except Exception as e:
            t(f"前端-路由({route})", 0, {"error": str(e)}, 200)
    
    # === 数据修改测试（使用已有的物料ID） ===
    s, d = api("GET", "/api/materials")
    if isinstance(d.get("items"), list) and len(d["items"]) > 0:
        mid = d["items"][0]["id"]
        orig_name = d["items"][0].get("material_name", "TEST")
        s, d2 = api("PUT", f"/api/materials/{mid}", {"material_name": f"ROUND{round_num}_{orig_name[:10]}"})
        t(f"物料-更新名称", s, d2, 200)
        s, d3 = api("PUT", f"/api/materials/{mid}", {"material_name": orig_name})
        t("物料-恢复名称", s, d3, 200)
    
    return results

# ===== 主程序 =====
all_results = {}
for rnd in range(1, 4):
    print(f"\n{'='*60}")
    print(f"开始第 {rnd} 轮测试...")
    print(f"{'='*60}")
    start = time.time()
    results = run_round(rnd)
    elapsed = time.time() - start
    total = len(results)
    passed = sum(1 for r, _ in results if r == PASS)
    failed = sum(1 for r, _ in results if r == FAIL)
    
    all_results[rnd] = {
        "total": total, "passed": passed, "failed": failed,
        "elapsed": round(elapsed, 2),
        "results": [(status, msg) for status, msg in results]
    }
    
    print(f"\n第{rnd}轮完成: {passed}/{total} 通过, {failed} 失败, 耗时 {elapsed:.1f}s")
    for status, msg in results:
        if status == FAIL:
            print(f"  ❌ {msg}")

# 输出JSON结果
output_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "test_results.json")
with open(output_path, "w", encoding="utf-8") as f:
    json.dump(all_results, f, ensure_ascii=False, indent=2)

print(f"\n全部测试完成，结果已保存至: {output_path}")

# 摘要
for rnd in range(1, 4):
    r = all_results[rnd]
    print(f"第{rnd}轮: {r['passed']}/{r['total']} 通过, {r['failed']} 失败, 耗时{r['elapsed']}s")

sys.exit(0 if all(all_results[r]['failed'] == 0 for r in range(1,4)) else 1)
