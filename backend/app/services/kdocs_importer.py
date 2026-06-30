"""金山文档在线导入器 — 从云文档链接读取BOM和物料数据"""
import json
import logging
from typing import List, Tuple, Optional

logger = logging.getLogger(__name__)


def parse_kdocs_link(url: str) -> Tuple[Optional[str], Optional[str]]:
    """
    解析金山文档分享链接，提取文件ID和文件类型

    支持的链接格式：
    - https://www.kdocs.cn/l/xxx          → 分享链接
    - https://www.kdocs.cn/w/xxx          → 文档链接
    - https://www.kdocs.cn/s/xxx          → 表格链接
    - https://www.kdocs.cn/p/xxx          → 演示文稿链接

    Returns:
        (file_type, file_id) 或 (None, None) 如果无法解析
    """
    import re
    
    # 匹配各种kdocs链接格式
    patterns = [
        r'kdocs\.cn/l/([a-zA-Z0-9_-]+)',           # 分享链接
        r'kdocs\.cn/([wsp])/([a-zA-Z0-9_-]+)',     # 直接链接 (w=文档, s=表格, p=演示)
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            groups = match.groups()
            if len(groups) == 1:
                return ("share", groups[0])
            elif len(groups) == 2:
                type_map = {"w": "doc", "s": "sheet", "p": "presentation"}
                return (type_map.get(groups[0], "unknown"), groups[1])
    
    return (None, None)


def parse_kdocs_sheet_data(raw_data: str, header_row: int = 1) -> dict:
    """
    解析金山文档表格数据为物料主数据和BOM行数据

    支持的表格格式：
    - 第一个工作表：物料主数据（物料编码、名称、规格、单位、类型、提前期...）
    - 第二个工作表：BOM数据（父物料编码、子物料编码、用量、位号...）

    Args:
        raw_data: 表格的原始数据（JSON格式的行列数据）
        header_row: 表头所在行号（默认第1行）

    Returns:
        {"materials": [...], "bom_lines": [...], "errors": [...]}
    """
    materials = []
    bom_lines = []
    errors = []

    try:
        # 尝试解析JSON数据
        data = json.loads(raw_data) if isinstance(raw_data, str) else raw_data
    except json.JSONDecodeError:
        # 如果不是JSON，尝试按CSV/TSV解析
        data = _parse_tsv_data(raw_data)

    if not data:
        return {"materials": [], "bom_lines": [], "errors": ["无法解析数据"]}

    # 处理多个工作表或数据块
    sheets = data if isinstance(data, list) else [data]
    
    for sheet_idx, sheet in enumerate(sheets):
        if not isinstance(sheet, (list, dict)):
            continue
            
        rows = sheet.get("rows", []) if isinstance(sheet, dict) else sheet
        
        if not rows or len(rows) < header_row + 1:
            continue

        # 提取表头
        headers = _extract_headers(rows, header_row)
        if not headers:
            continue

        # 判断是物料表还是BOM表
        is_material_sheet = any(h and ('物料编码' in str(h) or 'material_code' in str(h).lower() or '物料名称' in str(h) or 'material_name' in str(h).lower()) for h in headers)
        is_bom_sheet = any(h and ('父物料' in str(h) or 'parent' in str(h).lower() or '子物料' in str(h) or 'child' in str(h).lower()) for h in headers)

        # 跳过表头行
        for row_idx in range(header_row, len(rows)):
            row = rows[row_idx]
            if not row or all(not cell for cell in (row if isinstance(row, list) else [row])):
                continue

            row_data = _row_to_dict(headers, row)

            if is_material_sheet:
                mat = _parse_material_row(row_data)
                if mat:
                    materials.append(mat)
            elif is_bom_sheet:
                bl = _parse_bom_row(row_data)
                if bl:
                    bom_lines.append(bl)

    return {
        "materials": materials,
        "bom_lines": bom_lines,
        "errors": errors,
    }


def _extract_headers(rows, header_row: int) -> List[str]:
    """从行数据中提取表头"""
    if len(rows) < header_row:
        return []
    header = rows[header_row - 1]
    if isinstance(header, list):
        return [str(h).strip() if h else "" for h in header]
    elif isinstance(header, dict):
        return list(header.keys())
    return []


def _row_to_dict(headers: List[str], row) -> dict:
    """将行数据转为字典"""
    if isinstance(row, dict):
        return row
    if isinstance(row, list):
        return {headers[i] if i < len(headers) else f"col_{i}": str(v).strip() if v else ""
                for i, v in enumerate(row)}
    return {}


def _parse_material_row(data: dict) -> Optional[dict]:
    """解析物料主数据行"""
    code = data.get("物料编码") or data.get("material_code") or data.get("编码") or ""
    name = data.get("物料名称") or data.get("material_name") or data.get("名称") or ""
    
    if not code or not name:
        return None

    return {
        "material_code": str(code).strip(),
        "material_name": str(name).strip(),
        "specification": str(data.get("规格型号", data.get("specification", ""))).strip(),
        "unit": str(data.get("单位", data.get("unit", "个"))).strip(),
        "material_type": str(data.get("物料类型", data.get("material_type", "原材料"))).strip(),
        "level_type": str(data.get("层级类型", data.get("level_type", "零件"))).strip(),
        "lead_time": _safe_int(data.get("提前期(天)", data.get("lead_time", 0))),
        "safety_stock": _safe_float(data.get("安全库存", data.get("safety_stock", 0))),
        "lot_size_rule": str(data.get("批量规则", data.get("lot_size_rule", "LFL"))).strip().upper(),
        "lot_size_qty": _safe_float(data.get("批量数量", data.get("lot_size_qty", 1))),
        "min_order_qty": _safe_float(data.get("最小订货量", data.get("min_order_qty", 0))),
        "max_order_qty": _safe_float(data.get("最大订货量", data.get("max_order_qty", 0))),
        "is_purchased": str(data.get("外购件", data.get("is_purchased", "是"))).strip() in ("是", "1", "true", "True", "Y"),
    }


def _parse_bom_row(data: dict) -> Optional[dict]:
    """解析BOM行数据"""
    parent = data.get("父物料编码") or data.get("parent_code") or data.get("parent") or ""
    child = data.get("子物料编码") or data.get("child_code") or data.get("child") or data.get("物料编码") or ""
    
    if not parent or not child:
        return None

    return {
        "parent_code": str(parent).strip(),
        "child_code": str(child).strip(),
        "quantity_per": _safe_float(data.get("用量", data.get("quantity_per", data.get("quantity", 1))), 1),
        "position": str(data.get("位号", data.get("position", ""))).strip(),
        "level_type": str(data.get("层级类型", data.get("level_type", "零件"))).strip(),
        "is_substitute": str(data.get("替代料", data.get("is_substitute", "否"))).strip() in ("是", "1", "true"),
        "substitute_group": str(data.get("替代组", data.get("substitute_group", ""))).strip(),
        "scrap_rate": _safe_float(data.get("损耗率%", data.get("scrap_rate", 0)), 0),
        "remark": str(data.get("备注", data.get("remark", ""))).strip(),
    }


def _parse_tsv_data(text: str) -> list:
    """将TSV/CSV文本解析为表格数据"""
    lines = text.strip().split('\n')
    delimiter = '\t' if '\t' in lines[0] else ','
    return [[cell.strip() for cell in line.split(delimiter)] for line in lines]


def _safe_int(value, default=0):
    try:
        return int(float(str(value)))
    except (ValueError, TypeError):
        return default


def _safe_float(value, default=0.0):
    try:
        return float(str(value))
    except (ValueError, TypeError):
        return default
