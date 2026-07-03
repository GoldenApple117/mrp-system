"""完整导入：解析所有kdocs输出文件，创建物料+BOM"""
import os, sys, json, glob, re
os.environ["DB_BACKEND"] = "mysql"
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "backend"))

from sqlalchemy import text
from datetime import date, timedelta
from app.core.database import SessionLocal
from app.models.material import MaterialMaster as M
from app.models.bom import BomHeader, BomLine
from app.models.inventory import InventoryRecord, Warehouse
from app.models.mps import MpsEntry

def parse_file(filepath):
    """Return (sheet_name, {seq_num: {col_idx: value}}) for data rows"""
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.loads(f.read())
    
    content = data["data"]["content"]
    cells = content["range_data"]["detail"]["rangeData"]
    
    # Identify sheet by first cell's text (title at row 0)
    title_cell = [c for c in cells if c.get('originRow',0) == 0]
    title = title_cell[0].get('cellText','') if title_cell else ''
    
    SHEET_TITLES = {
        "外购件BOM": "外购件BOM表",
        "外加工件BOM表": "外加工钣金亚克力件BOM件",
        "外加工件BOM": "外加工钣金亚克力件BOM件",
        "电气BOM": "电气BOM",
        "视觉BOM": "视觉BOM",
        "量具工具耗材": "量具工具类",
        "量具工具": "量具工具类",
    }
    sheet_name = title  # Default to title
    for keyword, name in SHEET_TITLES.items():
        if keyword in title:
            sheet_name = name
            break
    
    rows = {}
    for cell in cells:
        r = cell.get("originRow", 0)
        c = cell.get("originCol", 0)
        v = cell.get("cellText", "") or cell.get("originalCellValue", "")
        ut = cell.get("understandableType", {})
        if ut.get("value") is not None:
            v = ut["value"]
        if v is None or (isinstance(v, float) and str(v) == 'nan'):
            v = ""
        rows.setdefault(r, {})[c] = v
    
    # Extract data rows (where col 0 is a valid number)
    data_rows = {}
    for r, vals in rows.items():
        col0 = str(vals.get(0, "")).strip()
        if col0 and re.match(r'^\d+$', col0):
            seq = int(col0)
            data_rows[seq] = vals
    
    return sheet_name, data_rows

# ===== 1. Parse all files =====
base = r"C:\Users\20210817\.workbuddy\projects\c-Users-20210817-WorkBuddy-2026-06-30-14-24-08\018cf496-e7d6-4538-88f0-65691b7ba022\tool-results"
files = glob.glob(os.path.join(base, "mcp-connector-proxy-kdocs_read_file-*.txt"))
files.sort(key=os.path.getmtime)

# Collect data by sheet
sheet_data = {}
for f in files:
    try:
        name, rows = parse_file(f)
        if rows:
            if name not in sheet_data:
                sheet_data[name] = {}
            sheet_data[name] = {**sheet_data[name], **rows}
    except Exception as e:
        print(f"  Skip {os.path.basename(f)[:50]}: {e}")

print(f"Parsed {len(sheet_data)} sheets:")
for name, rows in sheet_data.items():
    seqs = sorted(rows.keys())
    print(f"  {name}: {len(seqs)} parts (seq {seqs[0]}-{seqs[-1]})")

# ===== 2. Extract BOM modules =====
# Sheet name mapping
SHEET_MODULES = {
    "外购件BOM表": {"code": "WGJ", "label": "外购件"},
    "外加工钣金亚克力件BOM件": {"code": "BJG", "label": "外加工件"},
    "电气BOM": {"code": "DQ", "label": "电气"},
    "视觉BOM": {"code": "SJ", "label": "视觉"},
    "量具工具类": {"code": "LJ", "label": "量具工具"},
}

BOM_PARTS = {}
for sheet_name, mod_info in SHEET_MODULES.items():
    if sheet_name in sheet_data:
        parts = []
        for seq in sorted(sheet_data[sheet_name].keys()):
            row = sheet_data[sheet_name][seq]
            # Extract fields based on common column layout
            # Col 0: seq, Col 1: model/code, Col 2: name/spec, Col 3: brand/supplier
            # Col 4/6: qty_per, Col 7: unit, Col 8/9: lead_time, price varies
            model = str(row.get(1, "")).strip()
            name = str(row.get(2, "")).strip()
            brand = str(row.get(3, "")).strip()
            
            # Find qty column - varies by sheet
            qty = 1
            for c in [4, 6]:
                v = row.get(c)
                if v and str(v).replace('.','',1).isdigit():
                    qty = float(v)
                    break
            
            unit = str(row.get(7, "")).strip() or str(row.get(5, "")).strip()
            
            # Lead time
            lead = 7
            for c in [8, 9]:
                v = row.get(c)
                if v and str(v).replace('.','',1).isdigit():
                    lead = int(float(v))
                    break
            
            # Price
            price = 0
            for c in [9, 10, 11]:
                v = row.get(c)
                if v and str(v).replace('.','',1).isdigit():
                    price = float(v)
                    break
            
            if not model and not name:
                continue  # Empty row
            
            parts.append({
                "seq": seq, "model": model, "name": name,
                "brand": brand, "qty": qty, "unit": unit,
                "lead_time": lead, "price": price
            })
        
        if parts:
            BOM_PARTS[sheet_name] = parts
            print(f"  {sheet_name}: {len(parts)} valid parts")
            for p in parts[:3]:
                print(f"    {p['seq']}: {p['model']} | {p['name'][:40]} | qty={p['qty']} {p['unit']} | ¥{p['price']}")

# ===== 3. Import to MySQL =====
print("\n=== Importing to MySQL ===")

# Clear
with SessionLocal() as db:
    db.execute(text("SET FOREIGN_KEY_CHECKS=0"))
    for t in ["mrp_exception","inventory_transaction","inventory_record","warehouse",
              "bom_line","bom_header","bom_ecn","mps_entry","sales_order","customer",
              "purchase_order","work_order","payment","material_master",
              "routing_operation","routing_header","work_center","inspection_record",
              "stock_count","supplier"]:
        try: db.execute(text(f"DELETE FROM {t}")); db.commit()
        except: db.rollback()
    db.execute(text("SET FOREIGN_KEY_CHECKS=1")); db.commit()
print("  Cleared")

# Create materials
total_mats = 0
with SessionLocal() as db:
    # Product
    prod = M(material_code="SG-3ST-15", material_name="三工位测试台", unit="台",
             material_type="成品", level_type="产品", lead_time=30, is_purchased=False)
    db.add(prod); db.flush()
    total_mats += 1

    # Modules
    module_ids = {}
    for sheet_name, mod_info in SHEET_MODULES.items():
        if sheet_name in BOM_PARTS:
            m = M(material_code=f"MOD-{mod_info['code']}", material_name=f"{mod_info['label']}模块",
                  unit="套", material_type="半成品", level_type="组件")
            db.add(m); db.flush()
            module_ids[sheet_name] = m
            total_mats += 1

    # Parts - one material per unique model
    mat_ids = {}
    for sheet_name, parts in BOM_PARTS.items():
        for p in parts:
            code = p["model"].replace("-","").replace("/","_").replace(".","").replace(" ","")[:40]
            if code not in mat_ids:
                mat = M(material_code=code, material_name=p["name"][:200],
                        specification=p["model"], unit=p["unit"] or "个",
                        material_type="外购件", level_type="零件",
                        lead_time=p["lead_time"], is_purchased=True,
                        reference_unit_price=p["price"],
                        reference_submitter=p.get("brand",""))
                db.add(mat); db.flush()
                mat_ids[code] = mat
                total_mats += 1
    db.commit()
print(f"  Created {total_mats} materials")

# BOM
total_lines = 0
with SessionLocal() as db:
    prod = db.query(M).filter(M.material_code=="SG-3ST-15").first()
    hdr = BomHeader(bom_code="BOM-SG3ST-FULL", product_id=prod.id, version="A", status="生效")
    db.add(hdr); db.flush()

    for sheet_name, mod_info in SHEET_MODULES.items():
        if sheet_name not in module_ids:
            continue
        mod = module_ids[sheet_name]
        db.add(BomLine(bom_header_id=hdr.id, parent_item_id=prod.id, item_id=mod.id, quantity=1))
        total_lines += 1

        for p in BOM_PARTS.get(sheet_name, []):
            code = p["model"].replace("-","").replace("/","_").replace(".","").replace(" ","")[:40]
            if code in mat_ids:
                db.add(BomLine(bom_header_id=hdr.id, parent_item_id=mod.id,
                               item_id=mat_ids[code].id, quantity=p["qty"]))
                total_lines += 1
    db.commit()
print(f"  Created {1} BOM header + {total_lines} lines")

# MPS
with SessionLocal() as db:
    prod = db.query(M).filter(M.material_code=="SG-3ST-15").first()
    for d, q in [(7,5),(21,5),(35,5)]:
        db.add(MpsEntry(item_id=prod.id, plan_date=date.today()+timedelta(days=d), quantity=q))
    db.commit()
print("  Created MPS: 3 batches")

# Inventory
with SessionLocal() as db:
    wh = Warehouse(warehouse_code="WH-DEFAULT", warehouse_name="默认仓库", location="主仓库")
    db.add(wh); db.flush()
    for m in db.query(M).all():
        db.add(InventoryRecord(item_id=m.id, warehouse_id=wh.id, on_hand_qty=0, batch_no="init"))
    db.commit()
print(f"  Created {db.query(M).count()} inventory records")

print("\n✅ Complete!")
