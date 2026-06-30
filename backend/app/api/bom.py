"""BOM管理 API — 层级BOM + Excel导入 + 版本管理 + ECN + 金山文档导入"""
import os, uuid, logging
from datetime import date, datetime
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import Optional

from app.core.database import get_db
from app.core.config import UPLOAD_DIR
from app.models.bom import BomHeader, BomLine, BomEcn
from app.models.material import MaterialMaster
from app.services.excel_importer import ExcelImporter
from app.services.bom_exploder import BomExploder
from app.services.kdocs_importer import parse_kdocs_link, parse_kdocs_sheet_data

router = APIRouter(prefix="/api/bom", tags=["BOM管理"])

logger = logging.getLogger(__name__)


@router.get("/headers")
def list_bom_headers(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    keyword: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    """获取BOM头列表"""
    query = db.query(BomHeader)
    if keyword:
        query = query.filter(
            BomHeader.bom_code.ilike(f"%{keyword}%")
        )
    if status:
        query = query.filter(BomHeader.status == status)

    total = query.count()
    headers = query.order_by(BomHeader.bom_code).offset(
        (page - 1) * page_size
    ).limit(page_size).all()

    return {
        "items": [
            {
                "id": h.id, "bom_code": h.bom_code,
                "product_id": h.product_id,
                "product_code": h.product.material_code if h.product else "",
                "product_name": h.product.material_name if h.product else "",
                "version": h.version, "revision": h.revision,
                "status": h.status,
                "effective_date": h.effective_date.isoformat() if h.effective_date else None,
                "expire_date": h.expire_date.isoformat() if h.expire_date else None,
                "change_reason": h.change_reason,
                "created_at": h.created_at.isoformat() if h.created_at else None,
            }
            for h in headers
        ],
        "total": total, "page": page, "page_size": page_size,
    }


@router.get("/headers/{header_id}")
def get_bom_detail(header_id: int, db: Session = Depends(get_db)):
    """获取BOM详情（含所有行）"""
    header = db.query(BomHeader).filter(BomHeader.id == header_id).first()
    if not header:
        raise HTTPException(status_code=404, detail="BOM不存在")

    return {
        "header": {
            "id": header.id, "bom_code": header.bom_code,
            "product_id": header.product_id,
            "product_code": header.product.material_code if header.product else "",
            "product_name": header.product.material_name if header.product else "",
            "version": header.version, "status": header.status,
            "effective_date": header.effective_date.isoformat() if header.effective_date else None,
        },
        "lines": [
            {
                "id": line.id,
                "parent_item_id": line.parent_item_id,
                "parent_code": line.parent_item.material_code if line.parent_item else "",
                "parent_name": line.parent_item.material_name if line.parent_item else "",
                "item_id": line.item_id,
                "item_code": line.item.material_code if line.item else "",
                "item_name": line.item.material_name if line.item else "",
                "quantity": line.quantity,
                "position": line.position,
                "is_substitute": line.is_substitute,
                "substitute_group": line.substitute_group,
                "scrap_rate": line.scrap_rate,
                "level": line.level,
                "sort_order": line.sort_order,
                "remark": line.remark,
            }
            for line in header.lines
        ],
    }


@router.post("/headers")
def create_bom_header(data: dict, db: Session = Depends(get_db)):
    """创建BOM头"""
    header = BomHeader(
        bom_code=data["bom_code"],
        product_id=data["product_id"],
        version=data.get("version", "A"),
        status=data.get("status", "草稿"),
        effective_date=data.get("effective_date", date.today()),
        created_by=data.get("created_by", ""),
    )
    db.add(header)
    db.flush()

    # 添加BOM行
    for i, line_data in enumerate(data.get("lines", [])):
        line = BomLine(
            bom_header_id=header.id,
            parent_item_id=line_data.get("parent_item_id"),
            item_id=line_data["item_id"],
            quantity=line_data.get("quantity", 1),
            position=line_data.get("position", ""),
            is_substitute=line_data.get("is_substitute", False),
            substitute_for_id=line_data.get("substitute_for_id"),
            substitute_group=line_data.get("substitute_group", ""),
            scrap_rate=line_data.get("scrap_rate", 0),
            level=line_data.get("level", 0),
            sort_order=line_data.get("sort_order", i + 1),
            remark=line_data.get("remark", ""),
        )
        db.add(line)

    db.commit()
    return {"success": True, "message": "BOM创建成功", "data": {"id": header.id}}


@router.put("/headers/{header_id}")
def update_bom_header(header_id: int, data: dict, db: Session = Depends(get_db)):
    """更新BOM(先删行再重建)"""
    header = db.query(BomHeader).filter(BomHeader.id == header_id).first()
    if not header:
        raise HTTPException(status_code=404, detail="BOM不存在")

    # 更新头
    for key in ["version", "status", "effective_date", "change_reason"]:
        if key in data:
            setattr(header, key, data[key])

    # 删除旧行
    db.query(BomLine).filter(BomLine.bom_header_id == header_id).delete()

    # 重建行
    for i, line_data in enumerate(data.get("lines", [])):
        line = BomLine(
            bom_header_id=header.id,
            parent_item_id=line_data.get("parent_item_id"),
            item_id=line_data["item_id"],
            quantity=line_data.get("quantity", 1),
            position=line_data.get("position", ""),
            is_substitute=line_data.get("is_substitute", False),
            substitute_for_id=line_data.get("substitute_for_id"),
            substitute_group=line_data.get("substitute_group", ""),
            scrap_rate=line_data.get("scrap_rate", 0),
            level=line_data.get("level", 0),
            sort_order=line_data.get("sort_order", i + 1),
            remark=line_data.get("remark", ""),
        )
        db.add(line)

    db.commit()
    return {"success": True, "message": "BOM更新成功"}


@router.get("/tree/{product_id}")
def get_bom_tree(product_id: int, db: Session = Depends(get_db)):
    """获取物料BOM树形结构"""
    # 获取该成品的生效BOM
    header = db.query(BomHeader).filter(
        BomHeader.product_id == product_id,
        BomHeader.status == "生效",
    ).first()

    if not header:
        # 尝试草稿状态
        header = db.query(BomHeader).filter(
            BomHeader.product_id == product_id
        ).order_by(BomHeader.id.desc()).first()

    if not header:
        return {"tree": None, "message": "该物料没有BOM"}

    # 用递归CTE展开层级
    result = db.execute(text("""
        WITH RECURSIVE bom_tree AS (
            SELECT
                bl.id, bl.bom_header_id, bl.parent_item_id, bl.item_id,
                bl.quantity, bl.position, bl.is_substitute, bl.substitute_group,
                bl.scrap_rate, bl.remark, bl.sort_order, 0 as depth
            FROM bom_line bl
            WHERE bl.bom_header_id = :header_id AND (bl.parent_item_id IS NULL OR bl.parent_item_id = :product_id)

            UNION ALL

            SELECT
                bl2.id, bl2.bom_header_id, bl2.parent_item_id, bl2.item_id,
                bl2.quantity, bl2.position, bl2.is_substitute, bl2.substitute_group,
                bl2.scrap_rate, bl2.remark, bl2.sort_order, bt.depth + 1
            FROM bom_line bl2
            INNER JOIN bom_tree bt ON bl2.parent_item_id = bt.item_id
            WHERE bl2.bom_header_id = :header_id
        )
        SELECT bt.*, mm.material_code, mm.material_name, mm.unit
        FROM bom_tree bt
        JOIN material_master mm ON bt.item_id = mm.id
        ORDER BY bt.depth, bt.sort_order
    """), {"header_id": header.id, "product_id": header.product_id})

    nodes = []
    for row in result:
        nodes.append({
            "id": row.id,
            "parent_item_id": row.parent_item_id,
            "item_id": row.item_id,
            "material_code": row.material_code,
            "material_name": row.material_name,
            "unit": row.unit,
            "quantity": row.quantity,
            "position": row.position,
            "depth": row.depth,
            "is_substitute": row.is_substitute,
            "scrap_rate": row.scrap_rate,
        })

    product = db.query(MaterialMaster).filter(MaterialMaster.id == product_id).first()
    return {
        "tree": {
            "header_id": header.id,
            "bom_code": header.bom_code,
            "product_code": product.material_code if product else "",
            "product_name": product.material_name if product else "",
            "version": header.version,
            "nodes": nodes,
        }
    }


@router.get("/where-used/{item_id}")
def where_used(item_id: int, db: Session = Depends(get_db)):
    """物料用途反查：哪些BOM使用了该物料"""
    lines = db.query(BomLine).filter(BomLine.item_id == item_id).all()
    result = []
    for line in lines:
        header = db.query(BomHeader).filter(BomHeader.id == line.bom_header_id).first()
        parent = db.query(MaterialMaster).filter(MaterialMaster.id == line.parent_item_id).first()
        result.append({
            "bom_code": header.bom_code if header else "",
            "parent_code": parent.material_code if parent else "",
            "parent_name": parent.material_name if parent else "",
            "quantity": line.quantity,
            "position": line.position,
        })
    return {"items": result}


@router.post("/import/excel")
async def import_bom_from_excel(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """从Excel导入BOM（自动创建物料）"""
    if not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(status_code=400, detail="仅支持 .xlsx / .xls 文件")

    file_path = os.path.join(UPLOAD_DIR, f"bom_import_{date.today().isoformat()}.xlsx")
    with open(file_path, "wb") as f:
        content = await file.read()
        f.write(content)

    importer = ExcelImporter(file_path)

    # Step 1: 先导入物料主数据（自动创建不存在的物料）
    materials, mat_errors = importer.import_materials()
    mat_created = 0
    for mat_data in materials:
        existing = db.query(MaterialMaster).filter(
            MaterialMaster.material_code == mat_data["material_code"]
        ).first()
        if not existing:
            mat = MaterialMaster(
                material_code=mat_data["material_code"],
                material_name=mat_data["material_name"],
                specification=mat_data.get("specification", ""),
                unit=mat_data.get("unit", "个"),
                material_type=mat_data.get("material_type", "原材料"),
                lead_time=mat_data.get("lead_time", 0),
                safety_stock=mat_data.get("safety_stock", 0),
                lot_size_rule=mat_data.get("lot_size_rule", "LFL"),
                lot_size_qty=mat_data.get("lot_size_qty", 1),
                min_order_qty=mat_data.get("min_order_qty", 0),
                max_order_qty=mat_data.get("max_order_qty", 0),
                scrap_rate=mat_data.get("scrap_rate", 0),
                is_purchased=mat_data.get("is_purchased", True),
            )
            db.add(mat)
            mat_created += 1
    if mat_created:
        db.commit()

    # Step 2: 读取BOM行
    bom_lines, errors = importer.import_bom()

    if errors:
        return {"success": False, "message": "导入验证失败", "errors": errors}

    if not bom_lines:
        return {"success": False, "message": "未读取到BOM数据", "errors": ["请检查Excel中的BOM工作表"]}

    # 获取所有涉及的物料编码，按成品分组
    all_parents = set(line["parent_code"] for line in bom_lines if line["parent_code"])
    all_children = set(line["child_code"] for line in bom_lines)

    # 顶层物料 = 出现在父物料中但不出现为子物料的
    top_level = all_parents - all_children

    imported_count = 0
    for top_code in top_level:
        # 查找成品物料
        product = db.query(MaterialMaster).filter(
            MaterialMaster.material_code == top_code
        ).first()
        if not product:
            continue

        # 跳过已存在的BOM（防止重复导入报错）
        if db.query(BomHeader).filter(BomHeader.bom_code == f"BOM-{top_code}").first():
            continue

        # 创建BOM头
        header = BomHeader(
            bom_code=f"BOM-{top_code}",
            product_id=product.id,
            version="A",
            status="草稿",
        )
        db.add(header)
        db.flush()

        # 递归添加BOM行
        def add_lines(parent_code, parent_item_id=None, level=0):
            count = 0
            for bl in bom_lines:
                if bl["parent_code"] == parent_code:
                    child_mat = db.query(MaterialMaster).filter(
                        MaterialMaster.material_code == bl["child_code"]
                    ).first()
                    if child_mat:
                        line = BomLine(
                            bom_header_id=header.id,
                            parent_item_id=parent_item_id,
                            item_id=child_mat.id,
                            quantity=bl["quantity_per"],
                            position=bl["position"],
                            is_substitute=bl.get("is_substitute", False),
                            scrap_rate=bl.get("scrap_rate", 0),
                            level=level,
                            sort_order=count + 1,
                            remark=bl.get("remark", ""),
                        )
                        db.add(line)
                        db.flush()
                        count += 1
                        # 递归子物料
                        add_lines(bl["child_code"], child_mat.id, level + 1)
            return count

        add_lines(top_code, product.id, 0)
        imported_count += 1

    db.commit()
    msg = f"成功导入 {imported_count} 个BOM，新建物料 {mat_created} 个"
    if mat_errors:
        msg += f"，物料错误 {len(mat_errors)} 条"
    return {"success": True, "message": msg, "imported_count": imported_count, "mat_created": mat_created}


@router.get("/template")
def download_bom_template():
    """生成并返回BOM导入模板"""
    template_path = os.path.join(UPLOAD_DIR, "BOM导入模板.xlsx")
    ExcelImporter.generate_bom_template(template_path)
    return {"success": True, "message": "模板已生成", "path": template_path}


# ====== BOM 版本管理 ======

@router.get("/versions/{product_id}")
def list_bom_versions(product_id: int, db: Session = Depends(get_db)):
    """获取某成品所有BOM版本历史"""
    headers = db.query(BomHeader).filter(
        BomHeader.product_id == product_id
    ).order_by(BomHeader.version.desc(), BomHeader.id.desc()).all()

    return {
        "items": [
            {
                "id": h.id, "bom_code": h.bom_code, "version": h.version,
                "revision": h.revision, "status": h.status,
                "effective_date": h.effective_date.isoformat() if h.effective_date else None,
                "expire_date": h.expire_date.isoformat() if h.expire_date else None,
                "change_reason": h.change_reason,
                "lines_count": len(h.lines),
                "created_at": h.created_at.isoformat() if h.created_at else None,
            }
            for h in headers
        ]
    }


@router.post("/activate/{header_id}")
def activate_bom(header_id: int, db: Session = Depends(get_db)):
    """激活BOM：将指定BOM设为生效，自动失效同成品的其他生效版本"""
    header = db.query(BomHeader).filter(BomHeader.id == header_id).first()
    if not header:
        raise HTTPException(status_code=404, detail="BOM不存在")

    if not header.lines:
        raise HTTPException(status_code=400, detail="BOM为空行，无法生效")

    # 失效该物料的其他生效版本
    db.query(BomHeader).filter(
        BomHeader.product_id == header.product_id,
        BomHeader.status == "生效",
        BomHeader.id != header_id,
    ).update({"status": "失效", "expire_date": date.today()})

    # 激活当前版本
    header.status = "生效"
    header.effective_date = date.today()
    header.expire_date = None
    db.commit()

    return {"success": True, "message": f"BOM {header.bom_code} 已生效 (版本 {header.version})"}


@router.post("/version-bump/{product_id}")
def create_new_bom_version(product_id: int, data: dict, db: Session = Depends(get_db)):
    """基于现有BOM创建新版本(复制行)"""
    # 查找当前生效版本或最新草稿
    current = db.query(BomHeader).filter(
        BomHeader.product_id == product_id,
        BomHeader.status.in_(["生效", "草稿"])
    ).order_by(BomHeader.id.desc()).first()

    if not current:
        raise HTTPException(status_code=404, detail="该物料没有BOM，请先创建")

    # 计算新版本号（A→B→C...）
    new_ver = chr(ord(current.version[0]) + 1) if current.version else "A"

    header = BomHeader(
        bom_code=f"{current.bom_code}-{new_ver}",
        product_id=product_id,
        version=new_ver,
        status="草稿",
        change_reason=data.get("change_reason", ""),
        created_by=data.get("created_by", ""),
    )
    db.add(header)
    db.flush()

    # 复制BOM行
    for line in current.lines:
        db.add(BomLine(
            bom_header_id=header.id,
            parent_item_id=line.parent_item_id,
            item_id=line.item_id,
            quantity=line.quantity,
            position=line.position,
            is_substitute=line.is_substitute,
            substitute_for_id=line.substitute_for_id,
            substitute_group=line.substitute_group,
            scrap_rate=line.scrap_rate,
            level=line.level,
            sort_order=line.sort_order,
        ))

    db.commit()
    return {
        "success": True, "message": f"新版本 {new_ver} 已创建",
        "data": {"id": header.id, "bom_code": header.bom_code, "version": new_ver}
    }


@router.post("/inactivate/{header_id}")
def inactivate_bom(header_id: int, data: dict, db: Session = Depends(get_db)):
    """失效BOM"""
    header = db.query(BomHeader).filter(BomHeader.id == header_id).first()
    if not header:
        raise HTTPException(status_code=404, detail="BOM不存在")
    header.status = "失效"
    header.expire_date = date.today()
    header.change_reason = data.get("change_reason", header.change_reason)
    db.commit()
    return {"success": True, "message": f"BOM {header.bom_code} 已失效"}


# ====== ECN 工程变更管理 ======

@router.get("/ecn")
def list_ecn(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: str = Query(None),
    db: Session = Depends(get_db),
):
    """ECN列表"""
    query = db.query(BomEcn)
    if status:
        query = query.filter(BomEcn.status == status)

    total = query.count()
    ecns = query.order_by(BomEcn.id.desc()).offset(
        (page - 1) * page_size
    ).limit(page_size).all()

    return {
        "items": [
            {
                "id": e.id, "ecn_number": e.ecn_number,
                "bom_header_id": e.bom_header_id,
                "change_type": e.change_type,
                "reason": e.reason,
                "status": e.status,
                "applicant": e.applicant,
                "created_at": e.created_at.isoformat() if e.created_at else None,
            }
            for e in ecns
        ],
        "total": total, "page": page, "page_size": page_size,
    }


@router.post("/ecn")
def create_ecn(data: dict, db: Session = Depends(get_db)):
    """创建ECN变更申请"""
    now = datetime.now()
    ecn_number = f"ECN-{now.strftime('%Y%m%d')}-{date.today().strftime('%d%H%M')}"

    ecn = BomEcn(
        ecn_number=ecn_number,
        bom_header_id=data["bom_header_id"],
        change_type=data.get("change_type", "修订"),
        reason=data.get("reason", ""),
        old_content=data.get("old_content", ""),
        new_content=data.get("new_content", ""),
        applicant=data.get("applicant", ""),
    )
    db.add(ecn)
    db.commit()

    return {
        "success": True, "message": f"ECN {ecn_number} 已提交",
        "data": {"id": ecn.id, "ecn_number": ecn_number},
    }


@router.put("/ecn/{ecn_id}/approve")
def approve_ecn(ecn_id: int, data: dict, db: Session = Depends(get_db)):
    """审批ECN"""
    ecn = db.query(BomEcn).filter(BomEcn.id == ecn_id).first()
    if not ecn:
        raise HTTPException(status_code=404, detail="ECN不存在")

    action = data.get("action", "通过")
    if action == "通过":
        ecn.status = "已审批"
        ecn.approver = data.get("approver", "")
        ecn.approved_at = datetime.now()
        # 自动激活关联BOM
        header = db.query(BomHeader).filter(BomHeader.id == ecn.bom_header_id).first()
        if header:
            header.status = "生效"
            header.effective_date = date.today()
            # 失效同物料其他版本
            db.query(BomHeader).filter(
                BomHeader.product_id == header.product_id,
                BomHeader.status == "生效",
                BomHeader.id != header.id,
            ).update({"status": "失效", "expire_date": date.today()})
    elif action == "驳回":
        ecn.status = "已驳回"

    db.commit()
    return {"success": True, "message": f"ECN {ecn.ecn_number} 已{action}"}


@router.post("/import/procurement")
async def import_procurement_bom(
    files: list[UploadFile] = File(...),
    product_name: str = "",
    db: Session = Depends(get_db),
):
    """导入采购BOM（支持多CSV文件一次性导入）"""
    if not files:
        raise HTTPException(status_code=400, detail="请至少选择一个文件")

    # 验证文件类型
    for f in files:
        if not f.filename.endswith(('.csv', '.xlsx', '.xls')):
            raise HTTPException(status_code=400, detail=f"不支持的文件格式: {f.filename}")

    # 如果没有提供产品名，从第一个文件名推断
    if not product_name:
        base = os.path.splitext(os.path.basename(files[0].filename))[0]
        # 尝试去掉模块后缀
        for suffix in ['BOM表', 'BOM', '表']:
            base = base.rstrip(suffix)
        product_name = base.strip()
        if not product_name:
            product_name = "未命名产品"

    # 读取所有文件内容
    file_data = []
    for f in files:
        content = await f.read()
        # 尝试解码
        try:
            text = content.decode("utf-8")
        except UnicodeDecodeError:
            try:
                text = content.decode("gbk")
            except UnicodeDecodeError:
                text = content.decode("utf-8", errors="replace")
        file_data.append((f.filename, text))

    try:
        from app.services.procurement_importer import run_multi
        result = run_multi(file_data, product_name, db)
        return result
    except Exception as e:
        return {"success": False, "message": f"导入失败: {str(e)}", "errors": [], "stats": {}}


# ====== 金山文档在线导入 + 原始数据导入 ======

@router.post("/import/raw")
def import_bom_from_raw(data: dict, db: Session = Depends(get_db)):
    """
    从原始JSON数据导入BOM（通用入口，支持金山文档/手工录入/API对接）

    请求体格式：
    {
        "materials": [
            {
                "material_code": "RM-001",
                "material_name": "PCB电路板",
                "material_type": "原材料",
                "level_type": "零件",
                "unit": "块",
                "lead_time": 5,
                "safety_stock": 100,
                "lot_size_rule": "EOQ",
                "lot_size_qty": 500,
                "is_purchased": true
            }
        ],
        "bom_lines": [
            {
                "parent_code": "FG-001",
                "child_code": "MOD-ELEC",
                "quantity_per": 1,
                "position": "A1"
            }
        ]
    }
    """
    materials = data.get("materials", [])
    bom_lines_data = data.get("bom_lines", [])

    if not bom_lines_data:
        return {"success": False, "message": "没有BOM数据", "errors": ["bom_lines 为空"]}

    # Step 1: 自动创建不存在的物料
    mat_created = 0
    mat_updated = 0
    for mat_data in materials:
        existing = db.query(MaterialMaster).filter(
            MaterialMaster.material_code == mat_data["material_code"]
        ).first()
        if not existing:
            mat = MaterialMaster(
                material_code=mat_data["material_code"],
                material_name=mat_data.get("material_name", mat_data["material_code"]),
                specification=mat_data.get("specification", ""),
                unit=mat_data.get("unit", "个"),
                material_type=mat_data.get("material_type", "原材料"),
                level_type=mat_data.get("level_type", "零件"),
                lead_time=mat_data.get("lead_time", 0),
                safety_stock=mat_data.get("safety_stock", 0),
                lot_size_rule=mat_data.get("lot_size_rule", "LFL"),
                lot_size_qty=mat_data.get("lot_size_qty", 1),
                min_order_qty=mat_data.get("min_order_qty", 0),
                max_order_qty=mat_data.get("max_order_qty", 0),
                scrap_rate=mat_data.get("scrap_rate", 0),
                is_purchased=mat_data.get("is_purchased", True),
            )
            db.add(mat)
            mat_created += 1
        else:
            # 更新物料名称（如果为空）
            if not existing.material_name and mat_data.get("material_name"):
                existing.material_name = mat_data["material_name"]
                mat_updated += 1

    if mat_created or mat_updated:
        db.commit()

    # Step 2: 获取所有涉及物料编码，找顶层物料
    all_parents = set(line["parent_code"] for line in bom_lines_data if line.get("parent_code"))
    all_children = set(line["child_code"] for line in bom_lines_data)
    top_level_codes = all_parents - all_children

    # 如果没有顶层物料（环形结构），全部视为顶层
    if not top_level_codes:
        top_level_codes = all_parents

    imported_count = 0
    errors = []

    for top_code in top_level_codes:
        product = db.query(MaterialMaster).filter(
            MaterialMaster.material_code == top_code
        ).first()
        if not product:
            errors.append(f"顶层物料 {top_code} 不存在")
            continue

        # 跳过已存在的BOM
        if db.query(BomHeader).filter(BomHeader.bom_code == f"BOM-{top_code}").first():
            continue

        header = BomHeader(
            bom_code=f"BOM-{top_code}",
            product_id=product.id,
            version="A",
            status="草稿",
        )
        db.add(header)
        db.flush()

        def add_lines(parent_code, parent_item_id=None, level=0):
            count = 0
            for bl in bom_lines_data:
                if bl.get("parent_code") == parent_code:
                    child_mat = db.query(MaterialMaster).filter(
                        MaterialMaster.material_code == bl["child_code"]
                    ).first()
                    if not child_mat:
                        # 尝试自动创建缺失的物料
                        child_mat = MaterialMaster(
                            material_code=bl["child_code"],
                            material_name=bl["child_code"],
                            level_type=bl.get("level_type", "零件"),
                        )
                        db.add(child_mat)
                        db.flush()
                    
                    line = BomLine(
                        bom_header_id=header.id,
                        parent_item_id=parent_item_id,
                        item_id=child_mat.id,
                        quantity=bl.get("quantity_per", 1),
                        position=bl.get("position", ""),
                        is_substitute=bl.get("is_substitute", False),
                        substitute_group=bl.get("substitute_group", ""),
                        scrap_rate=bl.get("scrap_rate", 0),
                        level=level,
                        sort_order=count + 1,
                        remark=bl.get("remark", ""),
                    )
                    db.add(line)
                    db.flush()
                    count += 1
                    add_lines(bl["child_code"], child_mat.id, level + 1)
            return count

        add_lines(top_code, product.id, 0)
        imported_count += 1

    db.commit()
    msg = f"成功导入 {imported_count} 个BOM，新建物料 {mat_created} 个"
    if errors:
        msg += f"，{len(errors)} 个警告"
    return {
        "success": True,
        "message": msg,
        "imported_count": imported_count,
        "mat_created": mat_created,
        "errors": errors,
    }


@router.post("/import/kdocs")
def import_bom_from_kdocs(data: dict, db: Session = Depends(get_db)):
    """
    从金山文档在线链接导入BOM数据

    请求体格式：
    {
        "url": "https://www.kdocs.cn/l/xxx",
        "raw_data": "[可选] 如果提供了raw_data则直接解析，否则通过url获取"
    }

    支持的表格格式：
    - 工作表1「物料主数据」：物料编码、名称、规格、单位...
    - 工作表2「BOM」：父物料编码、子物料编码、用量、位号...
    """
    url = data.get("url", "")
    raw_content = data.get("raw_data", "")

    # 如果提供了原始数据，直接解析
    if raw_content:
        parsed = parse_kdocs_sheet_data(raw_content)
    elif url:
        file_type, file_id = parse_kdocs_link(url)
        if not file_id:
            return {
                "success": False,
                "message": "无法解析金山文档链接",
                "hint": "支持的格式: https://www.kdocs.cn/l/xxx 或 https://www.kdocs.cn/s/xxx",
            }

        # 尝试通过kdocs API读取文件
        try:
            import requests
            # 金山文档开放API：尝试读取分享链接的内容
            api_url = f"https://www.kdocs.cn/api/v3/share/file/{file_id}"
            resp = requests.get(api_url, timeout=10, headers={
                "User-Agent": "MRP-System/1.3",
            })
            if resp.status_code == 200:
                raw_content = resp.text
                parsed = parse_kdocs_sheet_data(raw_content)
            else:
                return {
                    "success": False,
                    "message": f"无法读取金山文档 (HTTP {resp.status_code})",
                    "hint": "请确认链接可公开访问，或使用 raw_data 参数直接提供数据",
                    "file_id": file_id,
                }
        except Exception as e:
            logger.warning(f"Kdocs API读取失败: {e}")
            return {
                "success": False,
                "message": f"读取金山文档失败: {str(e)}",
                "hint": "请使用 raw_data 参数直接传入文档内容，或通过Excel导入",
                "file_id": file_id,
            }
    else:
        return {
            "success": False,
            "message": "请提供 url 或 raw_data 参数",
            "usage": {
                "url": "金山文档分享链接",
                "raw_data": "表格原始数据（JSON格式的行列数据）",
            },
        }

    if not parsed.get("bom_lines"):
        return {
            "success": False,
            "message": "解析失败：未找到BOM数据",
            "parsed_materials": len(parsed.get("materials", [])),
            "errors": parsed.get("errors", []),
        }

    # 调用 raw 导入端点
    return import_bom_from_raw(
        {"materials": parsed["materials"], "bom_lines": parsed["bom_lines"]},
        db,
    )
