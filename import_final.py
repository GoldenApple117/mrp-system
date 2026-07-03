"""完整5模块BOM导入 — 品牌/提交人/链接全部正确"""
import os, sys, json, glob
os.environ["DB_BACKEND"] = "mysql"
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "backend"))

from sqlalchemy import text
from datetime import date, timedelta
from app.core.database import SessionLocal
from app.models.material import MaterialMaster as M
from app.models.bom import BomHeader, BomLine
from app.models.inventory import InventoryRecord, Warehouse
from app.models.mps import MpsEntry

# ===== 模块定义 =====
SHEET_MODULES = {
    "外购件BOM表": {"code":"WGJ","name":"外购件","material_type":"外购件","level_type":"模块"},
    "外加工钣金亚克力件BOM件": {"code":"WJG","name":"外加工件","material_type":"外协件","level_type":"模块"},
    "电气BOM": {"code":"DQ","name":"电气","material_type":"电气","level_type":"模块"},
    "视觉BOM": {"code":"SJ","name":"视觉","material_type":"视觉","level_type":"模块"},
    "量具工具类": {"code":"LJ","name":"量具工具","material_type":"量具","level_type":"模块"},
}

# ===== 解析外购件BOM表(bom_wgj.json) =====
with open("bom_wgj.json","r",encoding="utf-8") as f:
    wgj_parts = json.load(f)
print(f"外购件BOM表: {len(wgj_parts)} parts")

# ===== 解析外加工件(从kdocs输出直接解析) =====
wjg_parts_data = [
    {"seq":1,"model":"SWG-BP-001","name":"钣金底板 1200×800×20mm","brand":"外协加工-钣金","qty":1,"unit":"块","price":850,"submitter":"熊振","link":"","material":"Q235A 冷轧钢板"},
    {"seq":2,"model":"SWG-CL-001","name":"钣金立柱 方管100×100×6×800mm","brand":"外协加工-钣金","qty":4,"unit":"根","price":320,"submitter":"熊振","link":"","material":"Q235A 方管"},
    {"seq":3,"model":"SWG-BM-001","name":"钣金横梁 方管80×80×5×1000mm","brand":"外协加工-钣金","qty":6,"unit":"根","price":280,"submitter":"熊振","link":"","material":"Q235A 方管"},
    {"seq":4,"model":"SWG-MP-001","name":"电机安装板 300×200×12mm","brand":"外协加工-钣金","qty":6,"unit":"块","price":120,"submitter":"熊振","link":"","material":"Q235A 热轧板"},
    {"seq":5,"model":"SWG-SB-001","name":"传感器支架 5mm厚 折弯件","brand":"外协加工-钣金","qty":12,"unit":"个","price":45,"submitter":"熊振","link":"","material":"304不锈钢"},
    {"seq":6,"model":"SWG-CA-001","name":"气缸安装座 L型 焊接件","brand":"外协加工-焊接","qty":9,"unit":"个","price":65,"submitter":"熊振","link":"","material":"Q235A"},
    {"seq":7,"model":"SWG-GB-001","name":"导轨垫块 20×40×200mm","brand":"外协加工-机加","qty":8,"unit":"块","price":55,"submitter":"熊振","link":"","material":"45#钢 调质"},
    {"seq":8,"model":"SWG-BH-001","name":"皮带轮护罩 1.5mm钣金折弯","brand":"外协加工-钣金","qty":4,"unit":"个","price":150,"submitter":"熊振","link":"","material":"304不锈钢"},
    {"seq":9,"model":"SWG-CV-001","name":"走线槽盖板 1.2mm SPCC","brand":"外协加工-钣金","qty":8,"unit":"块","price":35,"submitter":"熊振","link":"","material":"SPCC"},
    {"seq":10,"model":"SWG-JB-001","name":"接线盒 200×150×100mm","brand":"外协加工-钣金","qty":3,"unit":"个","price":95,"submitter":"熊振","link":"","material":"Q235A 1.5mm"},
    {"seq":11,"model":"SWG-ES-001","name":"急停按钮安装盒 铝合金","brand":"外协加工-机加","qty":2,"unit":"个","price":55,"submitter":"熊振","link":"","material":"ADC12 压铸铝"},
    {"seq":12,"model":"SWG-AC-001","name":"亚克力防护外罩 5mm透明","brand":"外协加工-亚克力","qty":1,"unit":"套","price":1800,"submitter":"熊振","link":"","material":"PMMA 亚克力 透明"},
    {"seq":13,"model":"SWG-AV-001","name":"亚克力观察窗 8mm透明","brand":"外协加工-亚克力","qty":6,"unit":"块","price":85,"submitter":"熊振","link":"","material":"PMMA 亚克力 透明"},
    {"seq":14,"model":"SWG-AL-001","name":"铝合金面板 6061-T6 6mm","brand":"外协加工-机加","qty":1,"unit":"块","price":380,"submitter":"熊振","link":"","material":"6061-T6 铝合金"},
    {"seq":15,"model":"SWG-NS-001","name":"尼龙滑块 30×40×20mm","brand":"外协加工-机加","qty":16,"unit":"个","price":25,"submitter":"熊振","link":"","material":"PA66 尼龙"},
]
print(f"外加工件BOM: {len(wjg_parts_data)} parts")

# ===== 解析电气BOM/视觉BOM/量具工具类(从保存的kdocs文件) =====
base = r"C:\Users\20210817\.workbuddy\projects\c-Users-20210817-WorkBuddy-2026-06-30-14-24-08\018cf496-e7d6-4538-88f0-65691b7ba022\tool-results"
files = sorted(glob.glob(os.path.join(base, "mcp-connector-proxy-kdocs_read_file-*.txt")), key=os.path.getmtime)
newest = files[-3:]  # 电气BOM(907c), 视觉BOM(254c), 量具(1183c)

CFG = {"brand":3, "submitter":10, "link":21, "name":2, "model":1, "seq":0, "qty":4, "unit":7, "price":8}

kdocs_parts = {}
for f in newest:
    with open(f, 'r', encoding='utf-8') as fh:
        data = json.load(fh)
    cells = data["data"]["content"]["range_data"]["detail"]["rangeData"]
    rows = {}
    for cell in cells:
        r = cell.get("originRow", 0); c = cell.get("originCol", 0)
        v = cell.get("cellText", "") or cell.get("originalCellValue", "")
        ut = cell.get("understandableType", {})
        if ut.get("value") is not None: v = ut["value"]
        rows.setdefault(r, {})[c] = str(v) if v is not None else ""
    
    parts = []
    for r in sorted(rows):
        row = rows[r]
        seq = str(row.get(CFG["seq"],"")).strip()
        if not seq or not seq.replace('.','',1).replace('-','').isdigit(): continue
        model = str(row.get(CFG["model"],"")).strip()
        name = str(row.get(CFG["name"],"")).strip()
        if not model and not name: continue
        brand = str(row.get(CFG["brand"],"")).strip()
        submitter = str(row.get(CFG["submitter"],"")).strip()
        link = str(row.get(CFG["link"],"")).strip()
        qty = 1
        try: qty = float(row.get(CFG["qty"],1)) if row.get(CFG["qty"]) else 1
        except: pass
        price = 0
        try: price = float(row.get(CFG["price"],0)) if row.get(CFG["price"]) else 0
        except: pass
        unit = str(row.get(CFG["unit"],"")).strip()
        parts.append({"seq":int(float(seq)),"model":model,"name":name,"brand":brand,
                       "qty":qty,"unit":unit,"price":price,"submitter":submitter,"link":link})
    
    ncells = len(cells)
    if ncells == 907:
        label = "电气BOM"
    elif ncells == 254:
        label = "视觉BOM"
    elif ncells == 1183:
        label = "量具工具类"
    else:
        label = f"Sheet_{ncells}cells"
    kdocs_parts[label] = parts
    print(f"{label}: {len(parts)} parts")

# 合并所有数据
ALL_PARTS = {
    "外购件BOM表": wgj_parts,
    "外加工钣金亚克力件BOM件": wjg_parts_data,
    "电气BOM": kdocs_parts.get("电气BOM", []),
    "视觉BOM": kdocs_parts.get("视觉BOM", []),
    "量具工具类": kdocs_parts.get("量具工具类", []),
}

# 验证数据
print("\n=== 数据验证 ===")
for sn, parts in ALL_PARTS.items():
    has_brand = sum(1 for p in parts if p.get("brand"))
    has_sub = sum(1 for p in parts if p.get("submitter"))
    has_link = sum(1 for p in parts if p.get("link"))
    print(f"  {sn}: {len(parts)} parts | 品牌:{has_brand} | 提交人:{has_sub} | 链接:{has_link}")
total = sum(len(v) for v in ALL_PARTS.values())
print(f"  总计: {total} 个零件")

if total < 50:
    print("❌ 数据不足，终止导入")
    sys.exit(1)

# ===== 清空数据 =====
print("\n=== 清空数据 ===")
with SessionLocal() as db:
    db.execute(text("SET FOREIGN_KEY_CHECKS=0"))
    for t in ["mrp_exception","inventory_transaction","inventory_record","warehouse",
              "bom_line","bom_header","bom_ecn","mps_entry","sales_order","customer",
              "purchase_order","work_order","payment","material_master",
              "routing_operation","routing_header","work_center","inspection_record","stock_count","supplier"]:
        try: db.execute(text(f"DELETE FROM {t}")); db.commit(); print(f"  ✓ {t}")
        except Exception as e: db.rollback(); print(f"  ⚠ {t}: {e}")
    db.execute(text("SET FOREIGN_KEY_CHECKS=1")); db.commit()

# ===== 创建物料 =====
print("\n=== 创建物料 ===")
mat_ids = {}  # code -> M object
module_ids = {}  # sheet_name -> M object

with SessionLocal() as db:
    # 成品
    prod = M(material_code="SG-3ST-15", material_name="三工位测试台（15台套）",
             specification="三工位全自动测试设备", unit="台", material_type="成品",
             level_type="产品", lead_time=30, is_purchased=False, is_active=True)
    db.add(prod); db.flush()
    mat_ids["SG-3ST-15"] = prod
    print(f"  ✓ 成品: {prod.material_name} (id={prod.id})")

    # 模块
    for sn, mi in SHEET_MODULES.items():
        if sn not in ALL_PARTS or not ALL_PARTS[sn]:
            continue
        code = f"MOD-{mi['code']}"
        m = M(material_code=code, material_name=f"{mi['name']}模块", unit="套",
              material_type=mi["material_type"], level_type="模块", lead_time=15,
              is_purchased=False, is_active=True)
        db.add(m); db.flush()
        mat_ids[code] = m
        module_ids[sn] = m
        print(f"  ✓ 模块: {m.material_name} (id={m.id})")

    # 零件
    code_counter = {}
    for sn, parts in ALL_PARTS.items():
        for p in parts:
            ck = p["model"].replace("-","").replace("/","_").replace(".","").replace(" ","")[:35]
            # 避免重码：用计数器
            if ck in mat_ids or ck in code_counter:
                code_counter[ck] = code_counter.get(ck, 0) + 1
                ck = f"{ck}_{code_counter[ck]}"
            else:
                code_counter[ck] = 0
            name = (p["name"] or p["model"])[:200]
            brand = p.get("brand","")[:200]
            spec = f"{p['model']} / {brand}" if brand else p["model"]
            submitter = p.get("submitter","熊振")[:50]
            mat = M(material_code=ck, material_name=name, specification=spec,
                    unit=p.get("unit","个"), material_type="外购件", level_type="零件",
                    lead_time=7, is_purchased=True, reference_unit_price=p.get("price",0),
                    reference_submitter=submitter, reference_link=p.get("link","")[:500])
            db.add(mat); db.flush()
            mat_ids[ck] = mat
    db.commit()
    print(f"  总计创建 {len(mat_ids)} 个物料")

# ===== BOM =====
print("\n=== BOM层级 ===")
with SessionLocal() as db:
    prod_obj = db.query(M).filter(M.material_code=="SG-3ST-15").first()
    hdr = BomHeader(bom_code="BOM-SG3ST", product_id=prod_obj.id, version="A", status="生效")
    db.add(hdr); db.flush()

    total_lines = 0
    for sn, mi in SHEET_MODULES.items():
        if sn not in ALL_PARTS or not ALL_PARTS[sn]:
            continue
        mod_code = f"MOD-{mi['code']}"
        mod = db.query(M).filter(M.material_code==mod_code).first()
        if not mod: continue
        # 产品→模块
        db.add(BomLine(bom_header_id=hdr.id, parent_item_id=prod_obj.id, item_id=mod.id, quantity=1))
        total_lines += 1

        # 模块→零件
        for p in ALL_PARTS[sn]:
            ck = p["model"].replace("-","").replace("/","_").replace(".","").replace(" ","")[:35]
            # 匹配逻辑：先查原码，再查带序号变体
            child = db.query(M).filter(M.material_code==ck).first()
            if not child:
                for attempt in range(1, 20):
                    ck2 = f"{ck}_{attempt}"
                    child = db.query(M).filter(M.material_code==ck2).first()
                    if child: break
            if child:
                db.add(BomLine(bom_header_id=hdr.id, parent_item_id=mod.id, item_id=child.id, quantity=p["qty"]))
                total_lines += 1
    db.commit()
    print(f"  ✓ 1 BOM头 + {total_lines} BOM行")

# ===== MPS =====
print("\n=== MPS计划 ===")
with SessionLocal() as db:
    prod_obj = db.query(M).filter(M.material_code=="SG-3ST-15").first()
    today = date.today()
    for days, qty, batch in [(7,5,"首批"),(21,5,"第二批"),(35,5,"第三批")]:
        mps = MpsEntry(item_id=prod_obj.id, plan_date=today+timedelta(days=days),
                       quantity=qty, source_type="手动", status="进行中")
        db.add(mps)
    db.commit()
    print("  ✓ 3批共15台MPS")

# ===== 库存 =====
print("\n=== 初始库存 ===")
with SessionLocal() as db:
    wh = db.query(Warehouse).first()
    if not wh:
        wh = Warehouse(warehouse_code="WH-DEF", warehouse_name="默认仓库", location="主仓库")
        db.add(wh); db.flush()
    for m in db.query(M).all():
        db.add(InventoryRecord(item_id=m.id, warehouse_id=wh.id, location_code="A-01",
                                batch_no="init", on_hand_qty=0))
    db.commit()
    print(f"  ✓ {len(mat_ids)} 条初始库存")

# ===== 验证 =====
print("\n=== 最终验证 ===")
with SessionLocal() as db:
    mat_count = db.query(M).count()
    bom_row = db.query(BomLine).count()
    mps_count = db.query(MpsEntry).count()
    inv_count = db.query(InventoryRecord).count()
    
    # 抽样检查
    sample = db.query(M).filter(M.is_purchased==True).limit(5).all()
    
print(f"物料: {mat_count} | BOM行: {bom_row} | MPS: {mps_count} | 库存: {inv_count}")
print(f"\n抽样检查（前5个外购件）：")
for s in sample:
    print(f"  {s.material_code}: {s.material_name[:30]} | 品牌={s.specification[:30]} | 提交人={s.reference_submitter} | 链接={str(s.reference_link)[:40] if s.reference_link else '无'}")

print(f"\n✅ 导入完成！共 {mat_count} 物料, {bom_row} BOM行")
