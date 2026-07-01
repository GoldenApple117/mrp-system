"""生成三工位-15台 各模块测试数据并导入系统"""
import json, sys, os
sys.path.insert(0, '.')
os.environ['DB_BACKEND'] = 'sqlite'

# ===== 外购件BOM表 =====
purchased_items = [
    ("MP-001", "深沟球轴承", "6204-2RS 20×47×14", "SKF", 4, "个"),
    ("MP-002", "深沟球轴承", "6005-2RS 25×47×12", "NSK", 4, "个"),
    ("MP-003", "直线导轨", "HGH20CA 2R 1000mm+滑块", "上银HIWIN", 2, "套"),
    ("MP-004", "滚珠丝杆", "SFU1605-1000mm C5级+螺母", "上银HIWIN", 2, "套"),
    ("MP-005", "联轴器", "DS40-12-14 梅花型", "米思米", 4, "个"),
    ("MP-006", "气缸", "MDBB32-100Z 32×100mm", "SMC", 6, "个"),
    ("MP-007", "气缸", "MDBB40-150Z 40×150mm", "SMC", 3, "个"),
    ("MP-008", "气缸传感器", "D-M9B 无触点", "SMC", 12, "个"),
    ("MP-009", "调速阀", "AS2201F-01-08S", "SMC", 15, "个"),
    ("MP-010", "调速阀", "AS2201F-02-10S", "SMC", 6, "个"),
    ("MP-011", "油压缓冲器", "RB1007S 行程7mm", "SMC", 8, "个"),
    ("MP-012", "真空吸盘", "ZP3-T08BUN-A5 8mm", "SMC", 12, "个"),
    ("MP-013", "真空发生器", "ZH05BS-02-02", "SMC", 4, "个"),
    ("MP-014", "气管接头", "KQ2H06-01AS 直通6mm", "SMC", 40, "个"),
    ("MP-015", "气管接头", "KQ2L06-01AS 弯头6mm", "SMC", 30, "个"),
    ("MP-016", "气管接头", "KQ2T06-00A 三通6mm", "SMC", 20, "个"),
    ("MP-017", "拖链", "25×38 桥式 R75 2m", "易格斯IGUS", 4, "根"),
    ("MP-018", "拖链", "18×25 桥式 R55 1.5m", "易格斯IGUS", 4, "根"),
    ("MP-019", "压缩弹簧", "TWS 25×40 黄色", "米思米", 20, "个"),
    ("MP-020", "压缩弹簧", "TWS 20×30 蓝色", "米思米", 20, "个"),
    ("MP-021", "内六角螺栓", "M6×20 12.9级 发黑", "国产", 200, "个"),
    ("MP-022", "内六角螺栓", "M8×25 12.9级 发黑", "国产", 150, "个"),
    ("MP-023", "内六角螺栓", "M4×12 12.9级 发黑", "国产", 200, "个"),
    ("MP-024", "弹垫", "M6 不锈钢", "国产", 200, "个"),
    ("MP-025", "弹垫", "M8 不锈钢", "国产", 150, "个"),
    ("MP-026", "平垫", "M6 不锈钢", "国产", 200, "个"),
    ("MP-027", "平垫", "M8 不锈钢", "国产", 150, "个"),
    ("MP-028", "定位销", "D8×30 淬火钢", "米思米", 16, "个"),
    ("MP-029", "定位销", "D6×20 淬火钢", "米思米", 16, "个"),
    ("MP-030", "O型圈套装", "NBR 30种规格盒装", "国产", 2, "盒"),
    ("MP-031", "密封垫片", "PTFE 2mm×200×200", "国产", 4, "张"),
    ("MP-032", "油封", "TC 35×50×8 丁腈", "NOK", 8, "个"),
    ("MP-033", "润滑油", "美孚EP2 锂基脂 2kg", "美孚", 2, "桶"),
    ("MP-034", "螺纹胶", "乐泰242 50ml 蓝色", "乐泰", 3, "支"),
    ("MP-035", "清洁剂", "WD-40 除锈润滑 400ml", "WD-40", 5, "瓶"),
]

# ===== 外加工钣金亚克力件BOM =====
fabricated_items = [
    ("SP-001", "钣金底板", "平板 1200×800×20mm 45钢 发黑", "外协加工", 1, "块"),
    ("SP-002", "钣金立柱", "方管 100×100×800mm 焊接件", "外协加工", 4, "根"),
    ("SP-003", "钣金横梁", "方管 80×80×1000mm 焊接件", "外协加工", 6, "根"),
    ("SP-004", "电机安装板", "12mm Q235 激光切割 镀锌", "外协加工", 6, "块"),
    ("SP-005", "传感器支架", "5mm 不锈钢304 激光切割", "外协加工", 12, "个"),
    ("SP-006", "气缸安装座", "L型焊接件 10mm Q235 发黑", "外协加工", 9, "个"),
    ("SP-007", "导轨垫块", "20×40×200mm 45钢 磨削", "外协加工", 8, "块"),
    ("SP-008", "皮带轮护罩", "1.5mm不锈钢304 折弯成型", "外协加工", 4, "个"),
    ("SP-009", "接线盒", "200×150×100mm 1.5mm钢板 喷塑", "外协加工", 3, "个"),
    ("SP-010", "亚克力防护罩", "透明 5mm 1200×800×600mm", "外协加工", 1, "套"),
    ("SP-011", "亚克力观察窗", "透明 8mm 300×200mm", "外协加工", 6, "块"),
    ("SP-012", "尼龙滑块", "PA66 40×30×20mm CNC加工", "外协加工", 16, "个"),
    ("SP-013", "铝合金面板", "6061-T6 6mm 600×400mm 拉丝", "外协加工", 1, "块"),
    ("SP-014", "急停按钮盒", "铝合金压铸 黄色 RAL1021", "外协加工", 2, "个"),
    ("SP-015", "走线槽盖板", "1.2mm SPCC 静电喷塑 灰色", "外协加工", 8, "块"),
]

# ===== 视觉BOM =====
vision_items = [
    ("VS-CAM-001", "工业相机", "MER-503-20GM-P 500万像素 黑白", "大恒图像", 3, "台"),
    ("VS-CAM-002", "工业相机", "MER-503-20GC-P 500万像素 彩色", "大恒图像", 1, "台"),
    ("VS-CAM-003", "镜头", "M1614-MP2 16mm F1.4", "Computar", 3, "个"),
    ("VS-CAM-004", "镜头", "M2514-MP2 25mm F1.4", "Computar", 1, "个"),
    ("VS-CAM-005", "环形光源", "RL12090-W 白色 120mm", "OPT奥普特", 3, "个"),
    ("VS-CAM-006", "条形光源", "BL18018-W 白色 180mm", "OPT奥普特", 2, "个"),
    ("VS-CAM-007", "光源控制器", "DP1024-4CH 4通道", "OPT奥普特", 2, "台"),
    ("VS-CAM-008", "视觉工控机", "i7-12700/32G/512G SSD", "研华", 1, "台"),
    ("VS-CAM-009", "显示器", "23.8寸 1920×1080", "戴尔", 1, "台"),
    ("VS-CAM-010", "相机支架", "CA100 铝合金万向", "大恒图像", 4, "个"),
    ("VS-CAM-011", "千兆网卡", "PCIe 4口 Intel I350", "Intel", 1, "个"),
    ("VS-CAM-012", "网线", "超六类屏蔽 2米", "绿联", 6, "根"),
    ("VS-CAM-013", "标定板", "棋盘格 100×100mm 陶瓷", "OPT奥普特", 1, "块"),
    ("VS-CAM-014", "棱镜", "直角棱镜 25.4mm BK7", "Thorlabs", 2, "个"),
    ("VS-CAM-015", "滤光片", "BP660 带通 直径25.4mm", "Edmund", 3, "片"),
]

def build_import_all():
    """构建完整的导入数据"""
    all_modules = [
        ("MOD-PURCHASED", "外购件模块", purchased_items, "P"),
        ("MOD-FABRICATED", "外加工钣金模块", fabricated_items, "S"),
        ("MOD-VISION", "视觉模块", vision_items, "V"),
    ]
    
    materials = []
    bom_lines = []
    
    # 产品
    materials.append({
        "material_code": "PROJ-SWG-15", "material_name": "三工位-15台",
        "material_type": "成品", "level_type": "产品", "unit": "台",
        "lead_time": 30, "safety_stock": 0, "lot_size_rule": "LFL", "is_purchased": False,
    })
    
    for mod_code, mod_name, items, prefix in all_modules:
        # 模块
        materials.append({
            "material_code": mod_code, "material_name": mod_name,
            "material_type": "模块", "level_type": "模块", "unit": "套",
            "lead_time": 0, "safety_stock": 0, "lot_size_rule": "LFL", "is_purchased": False,
        })
        bom_lines.append({
            "parent_code": "PROJ-SWG-15", "child_code": mod_code,
            "quantity_per": 1, "position": f"模块-{mod_name[:2]}",
        })
        
        # 零件
        for i, (code, name, spec, brand, qty, unit) in enumerate(items, 1):
            materials.append({
                "material_code": code, "material_name": name,
                "specification": f"{spec} [{brand}]",
                "material_type": "原材料", "level_type": "零件",
                "unit": unit, "lead_time": 5, "safety_stock": max(1, qty//3),
                "lot_size_rule": "LFL", "is_purchased": True,
            })
            bom_lines.append({
                "parent_code": mod_code, "child_code": code,
                "quantity_per": qty, "position": f"{prefix}{i}",
            })
    
    return {"materials": materials, "bom_lines": bom_lines}


def import_to_local():
    from app.core.database import init_db, SessionLocal
    from app.models.material import MaterialMaster
    from app.models.bom import BomHeader, BomLine
    
    init_db()
    db = SessionLocal()
    data = build_import_all()
    
    # Create materials
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
    
    # Create BOMs (one per module)
    for mod_info in [
        ("MOD-PURCHASED", "外购件模块", purchased_items, "MP-"),
        ("MOD-FABRICATED", "外加工钣金模块", fabricated_items, "SP-"),
        ("MOD-VISION", "视觉模块", vision_items, "VS-"),
    ]:
        mod_code, mod_name, items, prefix = mod_info
        mod_mat = db.query(MaterialMaster).filter(MaterialMaster.material_code == mod_code).first()
        if not mod_mat:
            continue
        
        exists = db.query(BomHeader).filter(BomHeader.bom_code == f"BOM-{mod_code}").first()
        if exists:
            continue
        
        header = BomHeader(bom_code=f"BOM-{mod_code}", product_id=mod_mat.id, version="A", status="草稿")
        db.add(header)
        db.flush()
        
        count = 0
        for item in items:
            code = item[0]
            child = db.query(MaterialMaster).filter(MaterialMaster.material_code == code).first()
            if child:
                db.add(BomLine(
                    bom_header_id=header.id, parent_item_id=mod_mat.id, item_id=child.id,
                    quantity=item[4], level=2, sort_order=count+1, position=f"{prefix[:1]}{count+1}",
                ))
                count += 1
        print(f"  BOM-{mod_code}: {count} 行 ({mod_name})")
    
    # Add module lines to product BOM
    proj = db.query(MaterialMaster).filter(MaterialMaster.material_code == "PROJ-SWG-15").first()
    proj_bom = db.query(BomHeader).filter(BomHeader.bom_code == "BOM-PROJ-SWG-15").first()
    if proj and proj_bom:
        for mod_code in ["MOD-PURCHASED", "MOD-FABRICATED", "MOD-VISION"]:
            mod_mat = db.query(MaterialMaster).filter(MaterialMaster.material_code == mod_code).first()
            if not mod_mat: continue
            exists_line = db.query(BomLine).filter(
                BomLine.bom_header_id == proj_bom.id, BomLine.item_id == mod_mat.id,
            ).first()
            if not exists_line:
                max_sort = db.query(BomLine).filter(BomLine.bom_header_id == proj_bom.id).count()
                db.add(BomLine(
                    bom_header_id=proj_bom.id, parent_item_id=proj.id, item_id=mod_mat.id,
                    quantity=1, level=1, sort_order=max_sort+1,
                ))
        db.commit()
    
    # Stats
    from sqlalchemy import func
    mat_count = db.query(MaterialMaster).count()
    bom_count = db.query(BomHeader).count()
    line_count = db.query(BomLine).count()
    print(f"\n数据库现状: {mat_count} 物料, {bom_count} BOM, {line_count} 行")
    for lt, cnt in db.query(MaterialMaster.level_type, func.count()).group_by(MaterialMaster.level_type).all():
        print(f"  {lt}: {cnt}")
    db.close()


if __name__ == "__main__":
    print(f"生成测试数据: 外购件{purchased_items.__len__()}项 + 外加工{fabricated_items.__len__()}项 + 视觉{vision_items.__len__()}项")
    print(f"总计: {len(build_import_all()['materials'])} 物料, {len(build_import_all()['bom_lines'])} BOM行")
    print()
    import_to_local()
