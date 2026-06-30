"""采购BOM导入器 — 使用pandas解析固定模板Excel
模板：产品→模块→零件 三层级
每个工作表对应一个模块，每个工作表的行对应零件
"""
import os, re
from datetime import datetime
import pandas as pd
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
SKIP_PATTERNS = [r"费用", r"售后", r"Sheet", r"维护", r"合计"]

SHEET_SPECIAL = {
    "机加件模块": {"model_col": "图号", "name_col": "零件名称", "qty_col": "每台数量", "unit_col": "单位"},
}


def _module_name(sn: str) -> str | None:
    for pat, mod in SHEET_MAP:
        if re.search(pat, sn):
            return mod
    return None


def _skip(sn: str) -> bool:
    return any(re.search(p, sn) for p in SKIP_PATTERNS)


def _product_name(fn: str) -> str:
    return os.path.splitext(os.path.basename(fn))[0].strip()


def _gen_code(db: Session) -> str:
    now = datetime.now().strftime("%Y%m%d")
    pre = f"MAT-{now}-"
    last = db.query(MaterialMaster).filter(
        MaterialMaster.material_code.like(f"{pre}%")
    ).order_by(MaterialMaster.material_code.desc()).first()
    n = int(last.material_code.split("-")[-1]) + 1 if last else 1
    return f"{pre}{n:05d}"


def run(file_path: str, db: Session, original_name: str = "") -> dict:
    name = _product_name(original_name or file_path)
    if not name:
        return {"success": False, "message": "无法提取产品名", "stats": {}, "errors": []}

    xls = pd.ExcelFile(file_path)
    stats = {"product": 0, "modules": 0, "parts": 0, "bom_lines": 0, "skipped": 0}
    errors = []

    # 收集需要导入的工作表
    sheets = []
    for sn in xls.sheet_names:
        if _skip(sn):
            stats["skipped"] += 1
            continue
        mod = _module_name(sn)
        if not mod:
            stats["skipped"] += 1
            continue
        sheets.append((sn, mod))

    if not sheets:
        return {"success": False, "message": "无符合模板的工作表", "stats": stats, "errors": errors}

    # 产品
    prod = db.query(MaterialMaster).filter(
        MaterialMaster.material_code == f"PROD-{name}",
        MaterialMaster.level_type == "产品",
    ).first()
    if not prod:
        prod = MaterialMaster(
            material_code=f"PROD-{name}", material_name=name,
            unit="台", material_type="成品", level_type="产品",
            lead_time=0, safety_stock=0, lot_size_rule="LFL", is_purchased=False,
        )
        db.add(prod); db.flush()
        stats["product"] = 1

    # BOM头
    bom = db.query(BomHeader).filter(BomHeader.product_id == prod.id).first()
    if not bom:
        bom = BomHeader(bom_code=f"BOM-{name}", product_id=prod.id, version="A", status="生效")
        db.add(bom); db.flush()

    # 遍历工作表
    mod_map = {}
    seen = set()

    for sn, mn in sheets:
        try:
            df = pd.read_excel(file_path, sheet_name=sn, header=2)
        except Exception as e:
            errors.append(f"{sn}: 读取失败 - {e}")
            continue
        if df.empty:
            errors.append(f"{sn}: 无数据")
            continue

        # 创建模块
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

        # 列名
        if mn in SHEET_SPECIAL:
            model_c = SHEET_SPECIAL[mn]["model_col"]
            name_c = SHEET_SPECIAL[mn]["name_col"]
            qty_c = SHEET_SPECIAL[mn]["qty_col"]
            unit_c = SHEET_SPECIAL[mn]["unit_col"]
        else:
            model_c, name_c, qty_c, unit_c = "型号", "名称规格", "单台数量", "单位"

        has_model = model_c in df.columns
        has_name = name_c in df.columns
        has_qty = qty_c in df.columns
        has_unit = unit_c in df.columns

        if not has_name:
            errors.append(f"{sn}: 缺少 '{name_c}' 列")
            continue

        cnt = 0
        for _, row in df.iterrows():
            nm = row[name_c]
            if nm is None or str(nm) == "nan" or not str(nm).strip():
                continue
            ns = str(nm).strip()
            if "合计" in ns or "总计" in ns:
                continue

            mo = str(row[model_c]).strip() if has_model and row[model_c] is not None and str(row[model_c]) != "nan" else ""
            code = re.sub(r'[\\/:*?"<>|]', '_', mo)[:50] if mo else _gen_code(db)
            unit = str(row[unit_c]).strip()[:20] if has_unit and row[unit_c] is not None else "个"

            qty = 1
            if has_qty:
                qv = row[qty_c]
                if qv is not None and str(qv) != "nan":
                    try:
                        qty = max(1, float(qv))
                    except (ValueError, TypeError):
                        pass

            key = f"{mn}:{code}"
            if key in seen:
                continue
            seen.add(key)

            part = db.query(MaterialMaster).filter(MaterialMaster.material_code == code).first()
            if not part:
                part = MaterialMaster(
                    material_code=code, material_name=ns[:200],
                    specification=ns[:500] if ns != mo else "",
                    unit=unit, material_type="原材料", level_type="零件",
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
                    item_id=part.id, quantity=qty, level=2,
                    sort_order=stats["bom_lines"],
                ))
            cnt += 1
        if cnt == 0:
            errors.append(f"{sn}: 未检测到有效物料数据。可能原因：Excel中数据为公式填充，请用WPS/Excel打开后复制粘贴为纯值再保存，或使用\"粘贴数据\"方式导入。")
        # else:  # 不另加，因为errors中已反馈
        #     pass

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
    return {
        "success": stats["parts"] > 0,
        "message": f"导入完成：{stats['product']}个产品，{stats['modules']}个模块，{stats['parts']}个零件，{stats['bom_lines']}条BOM行",
        "stats": stats,
        "errors": errors[:20],
    }
