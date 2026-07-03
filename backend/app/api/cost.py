"""费用合计 API"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.material import MaterialMaster
from app.models.bom import BomHeader, BomLine

router = APIRouter(prefix="/api/cost", tags=["费用合计"])


@router.get("/summary")
def cost_summary(db: Session = Depends(get_db)):
    """获取所有项目的费用合计（按项目→模块→零件 汇总）"""
    # 1. 找到所有产品
    products = db.query(MaterialMaster).filter(
        MaterialMaster.level_type == "产品",
        MaterialMaster.is_active == True,
    ).all()

    projects = []
    grand_total = 0

    for product in products:
        # 找到产品的 BOM
        bom = db.query(BomHeader).filter(
            BomHeader.product_id == product.id
        ).order_by(BomHeader.id.desc()).first()
        if not bom:
            continue

        # 获取产品BOM的直接子行（即模块）
        module_lines = db.query(BomLine).filter(
            BomLine.bom_header_id == bom.id
        ).order_by(BomLine.sort_order).all()

        modules_detail = []
        project_total = 0

        for ml in module_lines:
            module_mat = db.query(MaterialMaster).filter(
                MaterialMaster.id == ml.item_id
            ).first()
            if not module_mat or module_mat.level_type != "模块":
                continue

            # 找到零件：优先独立模块BOM，其次当前产品BOM下的模块子行
            parts_detail = []
            module_total = 0
            mod_bom = db.query(BomHeader).filter(
                BomHeader.product_id == module_mat.id
            ).order_by(BomHeader.id.desc()).first()
            if mod_bom:
                part_lines = db.query(BomLine).filter(
                    BomLine.bom_header_id == mod_bom.id
                ).order_by(BomLine.sort_order).all()
            else:
                part_lines = db.query(BomLine).filter(
                    BomLine.bom_header_id == bom.id,
                    BomLine.parent_item_id == module_mat.id
                ).order_by(BomLine.sort_order).all()

            for pl in part_lines:
                part_mat = db.query(MaterialMaster).filter(
                    MaterialMaster.id == pl.item_id
                ).first()
                if not part_mat:
                    continue
                price = part_mat.reference_unit_price or 0
                qty = pl.quantity or 0
                cost = price * qty
                if cost > 0:
                    module_total += cost
                    parts_detail.append({
                        "material_code": part_mat.material_code,
                        "material_name": part_mat.material_name,
                        "brand": part_mat.specification or "",
                        "unit_price": price,
                        "quantity": qty,
                        "cost": round(cost, 2),
                    })

            modules_detail.append({
                "module_code": module_mat.material_code,
                "module_name": module_mat.material_name,
                "part_count": len(parts_detail),
                "total": round(module_total, 2),
                "parts": parts_detail,
            })
            project_total += module_total

        projects.append({
            "product_id": product.id,
            "product_code": product.material_code,
            "product_name": product.material_name,
            "module_count": len(modules_detail),
            "part_count": sum(m["part_count"] for m in modules_detail),
            "project_total": round(project_total, 2),
            "modules": modules_detail,
        })
        grand_total += project_total

    return {
        "projects": projects,
        "grand_total": round(grand_total, 2),
    }
