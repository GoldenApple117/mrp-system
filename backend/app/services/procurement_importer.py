"""采购BOM导入器 — 支持多CSV文件一次性导入
文件命名规则：CSV文件名决定模块归属（与xlsx工作表名一致）
"""
import os, re, csv, io
from datetime import datetime
from sqlalchemy.orm import Session

from app.models.material import MaterialMaster
from app.models.bom import BomHeader, BomLine

SHEET_MAP = [
    (r"外购", "外购件模块"),
    (r"加工|机加|钣金", "机加件模块"),
    (r"电气", "电气模块"),
    (r"视觉", "视觉模块"),
    (r"量具|工具", "量具模块"),
]


def _module_name(filename: str) -> str | None:
    """从CSV文件名识别模块名"""
    base = os.path.splitext(os.path.basename(filename))[0]
    for pat, mod in SHEET_MAP:
        if re.search(pat, base):
            return mod
    return None


def _gen_code(db: Session) -> str:
    now = datetime.now().strftime("%Y%m%d")
    pre = f"MAT-{now}-"
    last = db.query(MaterialMaster).filter(
        MaterialMaster.material_code.like(f"{pre}%")
    ).order_by(MaterialMaster.material_code.desc()).first()
    n = int(last.material_code.split("-")[-1]) + 1 if last else 1
    return f"{pre}{n:05d}"


def _parse_csv(content: str) -> list[dict]:
    """解析CSV内容，返回 [{"code":...,"name":...,"qty":...,"unit":...}]"""
    reader = csv.reader(io.StringIO(content))
    rows = list(reader)
    if not rows or len(rows) < 2:
        return []

    header = [h.strip() if h else "" for h in rows[0]]

    # 找各列的索引
    def find_col(*aliases):
        for a in aliases:
            for i, h in enumerate(header):
                if a in h:
                    return i
        return -1

    code_col = find_col("型号", "物料编码", "编码")
    name_col = find_col("名称规格", "名称", "物料名称", "零件名称")
    qty_col = find_col("单台数量", "用量", "数量", "每台数量")
    unit_col = find_col("单位")

    if name_col < 0:
        return []

    results = []
    for row in rows[1:]:
        if len(row) <= name_col:
            continue
        name = row[name_col].strip() if name_col < len(row) else ""
        if not name or "合计" in name or "总计" in name:
            continue
        code = row[code_col].strip() if code_col >= 0 and code_col < len(row) else ""
        qty = 1
        if qty_col >= 0 and qty_col < len(row):
            try:
                qty = max(1, float(row[qty_col].strip() or 1))
            except (ValueError, TypeError):
                pass
        unit = row[unit_col].strip() if unit_col >= 0 and unit_col < len(row) else "个"
        results.append({"code": code, "name": name, "qty": qty, "unit": unit})
    return results


def run_multi(files: list[tuple[str, str]], product_name: str, db: Session) -> dict:
    """
    多文件导入入口
    files: [(filename, content_str), ...]
    product_name: 用户输入的产品名
    """
    stats = {"product": 0, "modules": 0, "parts": 0, "bom_lines": 0}
    errors = []
    warnings = []

    # 产品
    prod = db.query(MaterialMaster).filter(
        MaterialMaster.material_code == f"PROD-{product_name}",
        MaterialMaster.level_type == "产品",
    ).first()
    if not prod:
        prod = MaterialMaster(
            material_code=f"PROD-{product_name}", material_name=product_name,
            unit="台", material_type="成品", level_type="产品",
            lead_time=0, safety_stock=0, lot_size_rule="LFL", is_purchased=False,
        )
        db.add(prod); db.flush()
        stats["product"] = 1

    # BOM头
    bom = db.query(BomHeader).filter(BomHeader.product_id == prod.id).first()
    if not bom:
        bom = BomHeader(bom_code=f"BOM-{product_name}", product_id=prod.id, version="A", status="生效")
        db.add(bom); db.flush()

    mod_map = {}
    seen = set()

    for fname, content in files:
        mn = _module_name(fname)
        if not mn:
            warnings.append(f"跳过: {os.path.basename(fname)}（未识别模块类型）")
            continue

        rows = _parse_csv(content)
        if not rows:
            warnings.append(f"{os.path.basename(fname)}: 未解析到数据，请确认表头包含'名称规格'或'名称'列")
            continue

        # 模块
        if mn not in mod_map:
            mod = db.query(MaterialMaster).filter(
                MaterialMaster.material_code == f"MOD-{mn}",
                MaterialMaster.level_type == "模块",
            ).first()
            if not mod:
                mod = MaterialMaster(
                    material_code=f"MOD-{mn}", material_name=mn,
                    unit="个", material_type="模块", level_type="模块",
                    lead_time=0, safety_stock=0, lot_size_rule="LFL", is_purchased=False,
                )
                db.add(mod); db.flush()
                stats["modules"] += 1
            mod_map[mn] = mod
        else:
            mod = mod_map[mn]

        for row in rows:
            code = re.sub(r'[\\/:*?"<>|]', '_', row["code"])[:50] if row["code"] else _gen_code(db)
            key = f"{mn}:{code}"
            if key in seen:
                continue
            seen.add(key)

            part = db.query(MaterialMaster).filter(MaterialMaster.material_code == code).first()
            if not part:
                part = MaterialMaster(
                    material_code=code, material_name=row["name"][:200],
                    specification=row["name"][:500] if row["name"] != code else "",
                    unit=row["unit"], material_type="原材料", level_type="零件",
                    lead_time=0, safety_stock=0, lot_size_rule="LFL", is_purchased=True,
                )
                db.add(part); db.flush()
                stats["parts"] += 1

            if not db.query(BomLine).filter(
                BomLine.bom_header_id == bom.id,
                BomLine.parent_item_id == mod.id,
                BomLine.item_id == part.id,
            ).first():
                stats["bom_lines"] += 1
                db.add(BomLine(
                    bom_header_id=bom.id, parent_item_id=mod.id,
                    item_id=part.id, quantity=row["qty"], level=2,
                    sort_order=stats["bom_lines"],
                ))

    # 产品→模块
    so = 0
    for mn, mod in mod_map.items():
        so += 1
        if not db.query(BomLine).filter(
            BomLine.bom_header_id == bom.id,
            BomLine.parent_item_id == prod.id,
            BomLine.item_id == mod.id,
        ).first():
            db.add(BomLine(
                bom_header_id=bom.id, parent_item_id=prod.id,
                item_id=mod.id, quantity=1, level=1, sort_order=so,
            ))

    db.commit()

    msg = f"导入完成：{stats['product']}个产品，{stats['modules']}个模块，{stats['parts']}个零件，{stats['bom_lines']}条BOM行"
    if warnings:
        msg += f"，{len(warnings)}个警告"
    
    return {
        "success": stats["parts"] > 0,
        "message": msg,
        "stats": stats,
        "errors": errors[:10],
        "warnings": warnings[:10],
    }
