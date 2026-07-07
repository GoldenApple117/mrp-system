"""完整BOM设置：产品→5模块→158零件，三层结构"""
import sys, os, json
from datetime import date
from collections import defaultdict

os.environ['DB_BACKEND'] = 'mysql'
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'backend'))

from app.core.database import SessionLocal
from app.core.config import DATABASE_URL
from app.models.material import MaterialMaster
from app.models.bom import BomHeader, BomLine

print(f'DB: {DATABASE_URL}')
db = SessionLocal()

PRODUCT_CODE = "SG-3ST-15"

# 5个模块（使用生产环境已有的模块编码）
MODULES = {
    "MOD-WGJ":  ("外购件", "外购件模块"),
    "MOD-WJG":  ("机加件", "外加工钣金亚克力件模块"),
    "MOD-DQ":   ("电气", "电气模块"),
    "MOD-SJ":   ("视觉", "视觉模块"),
    "MOD-LJ":   ("量具", "量具工具模块"),
}

# Sheet → Module mapping
SHEET_MODULE = {
    1: "MOD-WGJ",   # 外购件BOM表
    2: "MOD-WJG",   # 外加工钣金亚克力件BOM件
    3: "MOD-DQ",    # 电气BOM
    4: "MOD-SJ",    # 视觉BOM
    5: "MOD-LJ",    # 量具工具类
}

# Read kdocs data
with open(r'C:\Users\Admin\.workbuddy\projects\c-Users-Admin-WorkBuddy-2026-07-06-09-50-26\6995c34d-d7fd-4eb3-9b25-2bba972f5984\tool-results\mcp-connector-proxy-kdocs_read_file_sync-1783330935269-b7abd8.txt', 'r', encoding='utf-8') as f:
    kd = json.load(f)

sheets = kd['data']['content']['sheets']

# Get product
prod = db.query(MaterialMaster).filter(MaterialMaster.material_code == PRODUCT_CODE).first()
if not prod:
    print(f'❌ Product {PRODUCT_CODE} not found')
    sys.exit(1)
print(f'Product: {PRODUCT_CODE} (id={prod.id})')

# Ensure modules exist with correct level_type
module_ids = {}
for mc, (short_name, full_name) in MODULES.items():
    mod = db.query(MaterialMaster).filter(MaterialMaster.material_code == mc).first()
    if not mod:
        # Create new module material
        mod = MaterialMaster(
            material_code=mc, material_name=full_name,
            material_type='半成品', level_type='模块', unit='套',
            is_purchased=False,
        )
        db.add(mod)
        db.flush()
        print(f'  Created module: {mc} ({full_name})')
    else:
        # Update level_type
        mod.level_type = '模块'
        print(f'  Existing module: {mc} ({full_name}) - id={mod.id}')
    module_ids[mc] = mod.id

# Create BOM header for product
bom_header = BomHeader(
    product_id=prod.id,
    bom_code=f"BOM-{PRODUCT_CODE}",
    version="A",
    status="生效",
    effective_date=date.today(),
)
db.add(bom_header)
db.flush()
print(f'\nCreated BOM header #{bom_header.id}')

# Parse each sheet and create materials + BOM lines
bom_line_count = 0

for sheet_idx, mod_code in SHEET_MODULE.items():
    sheet = sheets[sheet_idx]
    rows = sheet.get('data', [])
    module_part_count = 0
    
    for entry in rows:
        idx = entry.get('index', 0)
        if idx < 4:
            continue
        
        cells = entry.get('cells', [])
        col_map = {}
        for cell in cells:
            ci = cell.get('index', -1)
            if 'display_text' in cell:
                col_map[ci] = cell['display_text'].strip()
        
        model = col_map.get(1, '')
        name = col_map.get(2, '')
        qty_str = col_map.get(4, '')
        unit = col_map.get(7, '')
        
        if not model and not name:
            continue
        
        code = model if model else f"AUTO-{mod_code}-{idx}"
        
        try:
            qty = float(qty_str.replace(',','').replace('，','')) if qty_str else 1
        except:
            qty = 1
        
        # Check/create part material
        part = db.query(MaterialMaster).filter(MaterialMaster.material_code == code).first()
        if not part:
            part = MaterialMaster(
                material_code=code,
                material_name=name if name else model,
                specification=model,
                material_type='原材料',
                level_type='零件',
                unit=unit if unit else '个',
                lead_time=7,
                safety_stock=0,
                lot_size_rule='LFL',
                is_purchased=True,
            )
            db.add(part)
            db.flush()
            module_part_count += 1
        
        # Create BOM line: Module → Part
        bl = BomLine(
            bom_header_id=bom_header.id,
            parent_item_id=module_ids[mod_code],
            item_id=part.id,
            quantity=qty,
        )
        db.add(bl)
        bom_line_count += 1
    
    # Create BOM line: Product → Module
    bl = BomLine(
        bom_header_id=bom_header.id,
        parent_item_id=prod.id,
        item_id=module_ids[mod_code],
        quantity=1,
    )
    db.add(bl)
    bom_line_count += 1
    print(f'  {mod_code}: product→module + {module_part_count} new parts')

db.commit()
db.close()

print(f'\n✅ Done!')
print(f'  BOM header: #{bom_header.id}')
print(f'  Total BOM lines: {bom_line_count}')
print(f'  Structure: Product({PRODUCT_CODE}) → 5 Modules → Parts')

# Verify
print('\n=== Verification ===')
db = SessionLocal()
mods = db.query(MaterialMaster).filter(MaterialMaster.level_type == '模块').all()
parts = db.query(MaterialMaster).filter(MaterialMaster.level_type == '零件').all()
prods = db.query(MaterialMaster).filter(MaterialMaster.level_type == '产品').all()
lines = db.query(BomLine).filter(BomLine.bom_header_id == bom_header.id).count()
print(f'  Products: {len(prods)} ({prods[0].material_code})')
print(f'  Modules: {len(mods)}')
for m in mods:
    child_count = db.query(BomLine).filter(BomLine.parent_item_id == m.id, BomLine.bom_header_id == bom_header.id).count()
    print(f'    {m.material_code} ({m.material_name}) → {child_count} parts')
print(f'  Parts: {len(parts)}')
print(f'  BOM lines total: {lines}')
db.close()
