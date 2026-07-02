"""生成电气BOM测试数据并导入数据库"""
import json, sys, os
sys.path.insert(0, '.')

# 电气BOM物料清单 —— 三工位-15台 电气模块
electrical_items = [
    # 编码, 名称, 规格, 品牌, 单台数量, 单位, 单价
    # ---- PLC & 控制器 ----
    ("EL-PLC-001", "PLC主机", "FX5U-80MT/ES", "三菱", 1, "台"),
    ("EL-PLC-002", "PLC输入模块", "FX5-16EX/ES", "三菱", 1, "台"),
    ("EL-PLC-003", "PLC输出模块", "FX5-16EYR/ES", "三菱", 2, "台"),
    ("EL-PLC-004", "模拟量模块", "FX5-4AD 4通道", "三菱", 1, "台"),
    # ---- 电源配电 ----
    ("EL-PWR-001", "开关电源24V", "S-350-24 14.6A", "明纬", 2, "台"),
    ("EL-PWR-002", "开关电源12V", "S-150-12 12.5A", "明纬", 1, "台"),
    ("EL-PWR-003", "断路器", "NXB-63 C32 2P", "正泰", 2, "个"),
    ("EL-PWR-004", "断路器", "NXB-63 C16 1P", "正泰", 4, "个"),
    ("EL-PWR-005", "断路器", "NXB-63 C6 2P", "正泰", 1, "个"),
    ("EL-PWR-006", "漏电保护器", "NXBLE-63 C32 30mA", "正泰", 1, "个"),
    ("EL-PWR-007", "交流接触器", "CJX2-2510 220V", "正泰", 3, "个"),
    ("EL-PWR-008", "热继电器", "NR2-25 7-10A", "正泰", 3, "个"),
    ("EL-PWR-009", "中间继电器", "JZX-22F/4Z DC24V", "正泰", 8, "个"),
    ("EL-PWR-010", "继电器底座", "PYF08A-E 8脚", "正泰", 8, "个"),
    ("EL-PWR-011", "接线端子(灰)", "UK2.5B 灰色", "菲尼克斯", 80, "个"),
    ("EL-PWR-012", "接线端子(蓝)", "UK2.5B 蓝色", "菲尼克斯", 40, "个"),
    ("EL-PWR-013", "接线端子(PE)", "UK2.5B-PE 黄绿", "菲尼克斯", 30, "个"),
    ("EL-PWR-014", "端板", "D-UK2.5", "菲尼克斯", 20, "个"),
    ("EL-PWR-015", "标记条", "ZB6 1-10", "菲尼克斯", 15, "条"),
    # ---- 传感器 ----
    ("EL-SEN-001", "光电传感器", "E3Z-D61 NPN", "欧姆龙", 3, "个"),
    ("EL-SEN-002", "光纤放大器", "E3X-NA11 2M", "欧姆龙", 3, "个"),
    ("EL-SEN-003", "光纤探头", "E32-DC200 同轴", "欧姆龙", 3, "个"),
    ("EL-SEN-004", "接近开关", "TL-Q5MC1 NPN", "欧姆龙", 6, "个"),
    ("EL-SEN-005", "磁性开关", "D-M9B 无触点", "SMC", 6, "个"),
    ("EL-SEN-006", "限位开关", "WLCA12-2N 滚轮", "欧姆龙", 6, "个"),
    # ---- 气动电磁阀 ----
    ("EL-VLV-001", "电磁阀", "SY5120-5LZD-C6", "SMC", 3, "个"),
    ("EL-VLV-002", "电磁阀", "SY5220-5LZD-C6", "SMC", 2, "个"),
    ("EL-VLV-003", "汇流板", "SS5Y3-20-02 4联", "SMC", 1, "个"),
    ("EL-VLV-004", "消音器", "AN103-KM5", "SMC", 4, "个"),
    # ---- 按钮指示灯 ----
    ("EL-BTN-001", "急停按钮", "XB2BS542C 旋转复位", "施耐德", 2, "个"),
    ("EL-BTN-002", "按钮(绿)", "XB2BA31C 常开", "施耐德", 3, "个"),
    ("EL-BTN-003", "按钮(红)", "XB2BA42C 常闭", "施耐德", 3, "个"),
    ("EL-BTN-004", "按钮(黄)", "XB2BA51C 常开", "施耐德", 1, "个"),
    ("EL-BTN-005", "指示灯(绿)", "XB2BVM3LC AC220V", "施耐德", 3, "个"),
    ("EL-BTN-006", "指示灯(红)", "XB2BVM4LC AC220V", "施耐德", 3, "个"),
    ("EL-BTN-007", "指示灯(黄)", "XB2BVM5LC AC220V", "施耐德", 1, "个"),
    ("EL-BTN-008", "蜂鸣器", "XB2BSB4LC 90dB", "施耐德", 1, "个"),
    ("EL-BTN-009", "选择开关", "XB2BD21C 2位", "施耐德", 2, "个"),
    # ---- 触摸屏HMI ----
    ("EL-HMI-001", "触摸屏", "MT8106iQ 10寸", "威纶通", 1, "台"),
    ("EL-HMI-002", "编程电缆", "USB-MINI 3米", "威纶通", 1, "根"),
    # ---- 伺服/步进电机 ----
    ("EL-MTR-001", "伺服驱动器", "SV630PS2R8I 750W", "汇川", 1, "台"),
    ("EL-MTR-002", "伺服电机", "MS1H1-75B30CB 750W", "汇川", 1, "台"),
    ("EL-MTR-003", "伺服动力线", "S6-L-P021-3.0 3m", "汇川", 1, "根"),
    ("EL-MTR-004", "编码器线", "S6-L-F021-3.0 3m", "汇川", 1, "根"),
    ("EL-MTR-005", "步进驱动器", "DM542 4.2A", "雷赛", 3, "台"),
    ("EL-MTR-006", "步进电机", "57HS22 2.2Nm", "雷赛", 3, "台"),
    # ---- 电气柜附件 ----
    ("EL-CAB-001", "电气柜", "1800x800x500 前单门", "威图", 1, "台"),
    ("EL-CAB-002", "安装板", "1750x750 镀锌2mm", "定制", 1, "块"),
    ("EL-CAB-003", "线槽80x60", "PVC 灰色 2m/根", "凯士士", 15, "根"),
    ("EL-CAB-004", "线槽60x40", "PVC 灰色 2m/根", "凯士士", 10, "根"),
    ("EL-CAB-005", "DIN导轨", "TH35-7.5 1m/根", "国产", 8, "根"),
    ("EL-CAB-006", "电缆格兰头", "M20x1.5 尼龙", "国产", 20, "个"),
    ("EL-CAB-007", "电缆格兰头", "M25x1.5 尼龙", "国产", 10, "个"),
    ("EL-CAB-008", "柜内照明灯", "LED 10W AC220V", "施耐德", 1, "个"),
    ("EL-CAB-009", "散热风扇", "120x120x38 AC220V", "卡固", 2, "个"),
    ("EL-CAB-010", "风扇过滤网", "120x120 黑色", "卡固", 2, "个"),
    # ---- 线缆 ----
    ("EL-CBL-001", "动力电缆", "RVV 4x2.5mm2 黑", "起帆", 50, "米"),
    ("EL-CBL-002", "控制电缆", "RVV 10x0.5mm2 黑", "起帆", 30, "米"),
    ("EL-CBL-003", "屏蔽电缆", "RVVP 4x0.3mm2 黑", "起帆", 40, "米"),
    ("EL-CBL-004", "超五类网线", "屏蔽 305m/箱", "安普", 1, "箱"),
    ("EL-CBL-005", "RJ45水晶头", "超五类 100个/盒", "安普", 1, "盒"),
]

def build_import_data():
    materials = []
    bom_lines = []

    # 产品层
    materials.append({
        "material_code": "PROJ-SWG-15",
        "material_name": "三工位-15台",
        "material_type": "成品", "level_type": "产品", "unit": "台",
        "lead_time": 30, "safety_stock": 0, "lot_size_rule": "LFL",
        "is_purchased": False,
    })

    # 电气模块层（MRP跳过此层）
    materials.append({
        "material_code": "MOD-ELEC-SWG",
        "material_name": "电气模块",
        "material_type": "模块", "level_type": "模块", "unit": "套",
        "lead_time": 0, "safety_stock": 0, "lot_size_rule": "LFL",
        "is_purchased": False,
    })
    bom_lines.append({
        "parent_code": "PROJ-SWG-15", "child_code": "MOD-ELEC-SWG",
        "quantity_per": 1, "position": "模块1",
    })

    # 电气零件
    for i, (code, name, spec, brand, qty, unit) in enumerate(electrical_items, 1):
        materials.append({
            "material_code": code,
            "material_name": name,
            "specification": f"{spec} [{brand}]",
            "material_type": "原材料",
            "level_type": "零件",
            "unit": unit,
            "lead_time": 5 if "线" in name or "缆" in name else 3,
            "safety_stock": max(1, qty // 3),
            "lot_size_rule": "LFL",
            "is_purchased": True,
        })
        bom_lines.append({
            "parent_code": "MOD-ELEC-SWG",
            "child_code": code,
            "quantity_per": qty,
            "position": f"位号{i}",
        })

    return {"materials": materials, "bom_lines": bom_lines}


def import_to_db():
    os.environ["DB_BACKEND"] = "sqlite"
    from app.core.database import init_db, SessionLocal
    from app.models.material import MaterialMaster
    from app.models.bom import BomHeader, BomLine

    init_db()
    db = SessionLocal()

    data = build_import_data()

    # 导入物料
    created = 0
    for m in data["materials"]:
        exists = db.query(MaterialMaster).filter(
            MaterialMaster.material_code == m["material_code"]
        ).first()
        if not exists:
            db.add(MaterialMaster(**m))
            created += 1
    if created:
        db.commit()
        print(f"  新建物料: {created} 个")

    # 识别顶层
    all_parents = set(l["parent_code"] for l in data["bom_lines"])
    all_children = set(l["child_code"] for l in data["bom_lines"])
    top_levels = all_parents - all_children

    for top in sorted(top_levels):
        product = db.query(MaterialMaster).filter(
            MaterialMaster.material_code == top
        ).first()
        if not product:
            continue

        exists = db.query(BomHeader).filter(
            BomHeader.bom_code == f"BOM-{top}"
        ).first()
        if exists:
            continue

        header = BomHeader(
            bom_code=f"BOM-{top}",
            product_id=product.id,
            version="A",
            status="草稿",
        )
        db.add(header)
        db.flush()

        count = 0
        for bl in data["bom_lines"]:
            if bl["parent_code"] == top:
                child = db.query(MaterialMaster).filter(
                    MaterialMaster.material_code == bl["child_code"]
                ).first()
                if child:
                    db.add(BomLine(
                        bom_header_id=header.id,
                        parent_item_id=product.id,
                        item_id=child.id,
                        quantity=bl.get("quantity_per", 1),
                        position=bl.get("position", ""),
                        level=1 if product.level_type in ("模块","产品") else 2,
                        sort_order=count + 1,
                    ))
                    count += 1

        print(f"  BOM-{top}: {count} 行 ({product.material_name}, {product.level_type})")

    db.commit()

    # 统计
    mat_count = db.query(MaterialMaster).count()
    bom_count = db.query(BomHeader).count()
    line_count = db.query(BomLine).count()

    # 分类统计
    from sqlalchemy import func
    level_stats = db.query(
        MaterialMaster.level_type, func.count(MaterialMaster.id)
    ).group_by(MaterialMaster.level_type).all()
    
    print(f"\n导入完成! 数据库概况:")
    print(f"  物料: {mat_count} 个")
    for lt, cnt in level_stats:
        print(f"    {lt}: {cnt}")
    print(f"  BOM: {bom_count} 个")
    print(f"  BOM行: {line_count} 行")

    db.close()

if __name__ == "__main__":
    # 也保存JSON供API使用
    data = build_import_data()
    with open("kdocs_electrical_import.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"JSON已保存: kdocs_electrical_import.json")
    print(f"  产品: 1, 模块: 1, 零件: {len(electrical_items)}")

    print("\n开始导入数据库...")
    import_to_db()
