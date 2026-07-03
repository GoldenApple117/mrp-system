"""完整5模块BOM导入"""
import os, sys
os.environ["DB_BACKEND"] = "mysql"
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "backend"))
from sqlalchemy import text
from datetime import date, timedelta
from app.core.database import SessionLocal
from app.models.material import MaterialMaster as M
from app.models.bom import BomHeader, BomLine
from app.models.inventory import InventoryRecord, Warehouse
from app.models.mps import MpsEntry

MODULES = {
    "外购件": [
        ("6204-2RS","深沟球轴承 6204-2RS 内径20mm","SKF",4,"个",7,35),
        ("6005-2RS","深沟球轴承 6005-2RS 内径25mm","NSK",4,"个",7,42),
        ("HGH20CA-1000","直线导轨 HGH20CA 长度1000mm 含滑块×2","上银HIWIN",2,"套",14,1280),
        ("SFU1605-1000","滚珠丝杆 SFU1605 导程5mm 长度1000mm","上银HIWIN",2,"套",14,980),
        ("DS40-AL","联轴器 DS40 梅花型 铝合金 夹紧式","米思米",4,"个",5,45),
        ("MDBB32-100Z","气缸 MDBB32-100Z 双作用 32mm×100mm","SMC",6,"个",10,320),
        ("MDBB40-150Z","气缸 MDBB40-150Z 双作用 40mm×150mm","SMC",3,"个",10,420),
        ("D-M9B","气缸传感器 D-M9B 无触点 固态开关","SMC",12,"个",5,55),
        ("AS2201F-01-08S","调速阀 AS2201F-01-08S 单向节流","SMC",15,"个",3,18),
        ("ZP3-T08BUN-J6-B5","真空吸盘 ZP3-T08BUN 丁腈橡胶 平型","SMC",12,"个",5,25),
        ("ZH05BS-02-02","真空发生器 ZH05BS 喷嘴直径0.5mm","SMC",4,"个",7,180),
        ("KQ2H06-01AS","气管直通接头 KQ2H06-01AS φ6-1/8","SMC",40,"个",3,3.5),
        ("KQ2L06-01AS","气管弯头 KQ2L06-01AS φ6-1/8","SMC",30,"个",3,4),
        ("2500.038.100.0","拖链 E2/000 25×38 桥式 内高25mm","易格斯",4,"根",10,320),
        ("RB1007S","油压缓冲器 RB1007S 行程7mm","SMC",8,"个",7,85),
        ("GB70-M6×20-12.9","内六角圆柱头螺栓 M6×20 12.9级","晋亿",200,"个",3,0.15),
        ("GB70-M8×25-12.9","内六角圆柱头螺栓 M8×25 12.9级","晋亿",150,"个",3,0.25),
        ("GB93-M6","弹簧垫圈 M6 65Mn","晋亿",200,"个",3,0.05),
        ("GB97-M6","平垫圈 M6 A2不锈钢","晋亿",200,"个",3,0.08),
        ("MSH8-30","定位销 D8×30 淬火钢 圆柱型","MISUMI",16,"个",5,3),
        ("NBR-O30","O型圈套装 NBR 丁腈橡胶 30种规格","NOK",2,"盒",5,45),
        ("PTFE-2mm","密封垫片 PTFE 聚四氟乙烯 2mm厚","国产",4,"张",5,12),
        ("MOBIL-EP2-2KG","润滑脂 美孚EP2 复合锂基 2kg/桶","美孚",2,"桶",3,85),
        ("LOCTITE-242-50ML","螺纹胶 乐泰242 中强度 50ml","乐泰",3,"支",3,25),
        ("WD40-400ML","防锈清洁剂 WD-40 多用途 400ml","WD-40",5,"瓶",3,35),
    ],
    "外加工件": [
        ("SWG-BP-001","钣金底板 1200×800×20mm","外协-钣金",1,"块",10,850),
        ("SWG-CL-001","钣金立柱 方管100×100×6×800mm","外协-钣金",4,"根",10,320),
        ("SWG-BM-001","钣金横梁 方管80×80×5×1000mm","外协-钣金",6,"根",10,280),
        ("SWG-MP-001","电机安装板 300×200×12mm","外协-钣金",6,"块",7,120),
        ("SWG-SB-001","传感器支架 5mm厚 折弯件","外协-钣金",12,"个",7,45),
        ("SWG-CA-001","气缸安装座 L型 焊接件","外协-焊接",9,"个",10,85),
        ("SWG-GB-001","导轨垫块 20×40×200mm","外协-机加",8,"块",7,55),
        ("SWG-BH-001","皮带轮护罩 1.5mm钣金折弯","外协-钣金",4,"个",10,95),
        ("SWG-CV-001","走线槽盖板 1.2mm SPCC","外协-钣金",8,"块",7,35),
        ("SWG-JB-001","接线盒 200×150×100mm","外协-钣金",3,"个",7,65),
        ("SWG-ES-001","急停按钮安装盒 铝合金","外协-机加",2,"个",7,40),
        ("SWG-AC-001","亚克力防护外罩 5mm透明","外协-亚克力",1,"套",14,650),
        ("SWG-AV-001","亚克力观察窗 8mm透明","外协-亚克力",6,"块",7,85),
        ("SWG-AL-001","铝合金面板 6061-T6 6mm","外协-机加",1,"块",10,280),
        ("SWG-NS-001","尼龙滑块 30×40×20mm","外协-机加",16,"个",7,15),
    ],
    "电气": [
        ("FX5U-80MT/ES","PLC主机 FX5U-80MT/ES 40入40出 晶体管","三菱",1,"台",14,3200),
        ("FX5-16EX/ES","PLC输入扩展模块 FX5-16EX/ES 16点DC24V","三菱",1,"台",7,980),
        ("FX5-16EYR/ES","PLC输出扩展模块 FX5-16EYR/ES 16点继电器","三菱",2,"台",7,1700),
        ("FX5-4AD","模拟量输入模块 FX5-4AD 4通道 电压/电流","三菱",1,"台",7,1450),
        ("FX5-4DA","模拟量输出模块 FX5-4DA 4通道","三菱",1,"台",7,1380),
        ("DKM-3U-05D-24","开关电源 DKM-3U-05D-24 24V 5A 120W","明纬",1,"台",5,180),
        ("DKM-3U-24D-24","开关电源 DKM-3U-24D-24 24V 24A 576W","明纬",1,"台",5,580),
        ("XS5F-D421-E80-F","Ethernet网线 M12 RJ45 8m","欧姆龙",1,"根",3,120),
        ("DRT2-OD16","远程IO模块 DRT2-OD16 16点晶体管输出","欧姆龙",2,"台",7,850),
        ("DRT2-ID16","远程IO模块 DRT2-ID16 16点输入","欧姆龙",2,"台",7,780),
        ("E3Z-LS86","光电传感器 E3Z-LS86 输送线检测","欧姆龙",6,"个",5,68),
    ],
    "视觉": [
        ("MER-503-20GM-P","工业相机 500万像素 黑白 GigE接口 2/3\" CMOS","大恒",3,"台",10,8550),
        ("MER-503-20GC-P","工业相机 500万像素 彩色 GigE接口 2/3\" CMOS","大恒",1,"台",10,3200),
        ("M1614-MP2","定焦镜头 16mm F1.4 C口 2/3\"","computar",3,"个",5,2550),
        ("M2514-MP2","定焦镜头 25mm F1.4 C口 2/3\"","computar",1,"个",5,980),
        ("RL12090-W","环形光源 120mm外径 90°照射角 白光","CCS",3,"个",7,2040),
        ("WLDR2-100SW2","条形光源 100mm 白光","CCS",2,"个",7,680),
        ("DH-VT120","光源控制器 数字式 2通道","大恒",2,"台",5,450),
        ("M0814-MP2","定焦镜头 8mm F1.4 C口","computar",1,"个",5,1280),
        ("FL-HC0614-2M","定焦镜头 6mm F1.4 2MP C口","RICOH",1,"个",7,1850),
    ],
    "量具工具": [
        ("K3GLS3100","数显卡尺 0-150mm 0.01mm","三丰",3,"把",5,680),
        ("F-008-030","千分表 0-1mm 0.001mm 带表架","三丰",2,"套",7,850),
        ("K070180","塞尺 0.02-1.0mm 20片","三丰",3,"把",3,45),
        ("6132-20-K","扭矩扳手 5-25Nm 1/4\"","东日",2,"把",7,580),
        ("ST1-600-20-23","千分尺 0-25mm 0.01mm","三丰",2,"把",5,320),
        ("TR12000","万用表 真有效值 自动量程","Fluke",1,"台",7,850),
        ("T6-1000","电压测试仪 非接触式","Fluke",1,"台",3,420),
        ("FL-01","酒精灯 玻璃 250ml","国产",3,"个",3,15),
        ("01-01-01","无尘布 9寸 100片/包","国产",5,"包",3,25),
        ("TC-01","热电偶测温仪 K型 -50~1300℃","国产",2,"台",5,120),
    ],
}

MODULE_CODES = {"外购件":"MOD-WGJ","外加工件":"MOD-BJG","电气":"MOD-DQ","视觉":"MOD-SJ","量具工具":"MOD-LJ"}

# ===== Import =====
with SessionLocal() as db:
    db.execute(text("PRAGMA foreign_keys=OFF"))
    for t in ["mrp_exception","inventory_transaction","inventory_record","warehouse",
              "bom_line","bom_header","bom_ecn","mps_entry","sales_order","customer",
              "purchase_order","work_order","payment","material_master",
              "routing_operation","routing_header","work_center","inspection_record","stock_count","supplier"]:
        try: db.execute(text(f"DELETE FROM {t}")); db.commit()
        except: db.rollback()
    db.execute(text("PRAGMA foreign_keys=ON")); db.commit()

with SessionLocal() as db:
    prod = M(material_code="SG-3ST-15",material_name="三工位测试台（15台套）",unit="台",material_type="成品",level_type="产品",lead_time=30,is_purchased=False)
    db.add(prod); db.flush()

    modules = {}
    for mod_name, code in MODULE_CODES.items():
        m = M(material_code=code,material_name=f"{mod_name}模块",unit="套",material_type="半成品",level_type="模块")
        db.add(m); db.flush()
        modules[mod_name] = m

    mats = {}
    for mod_name, parts in MODULES.items():
        for model, name, brand, qty, unit, lead, price in parts:
            ck = model.replace("-","").replace("/","_").replace(".","").replace(" ","")[:40]
            if ck not in mats:
                mat = M(material_code=ck,material_name=name[:200],specification=model,unit=unit,material_type="外购件",level_type="零件",lead_time=lead,is_purchased=True,reference_unit_price=price,reference_submitter="熊振")
                db.add(mat); db.flush()
                mats[ck] = mat

    hdr = BomHeader(bom_code="BOM-SG3ST",product_id=prod.id,version="A",status="生效")
    db.add(hdr); db.flush()
    total_parts = 0
    total_lines = 0
    for mod_name in modules:
        db.add(BomLine(bom_header_id=hdr.id,parent_item_id=prod.id,item_id=modules[mod_name].id,quantity=1))
        total_lines += 1
        for model, name, brand, qty, unit, lead, price in MODULES[mod_name]:
            ck = model.replace("-","").replace("/","_").replace(".","").replace(" ","")[:40]
            if ck in mats:
                db.add(BomLine(bom_header_id=hdr.id,parent_item_id=modules[mod_name].id,item_id=mats[ck].id,quantity=qty))
                total_lines += 1
                total_parts += 1

    for d,q in [(7,5),(21,5),(35,5)]:
        db.add(MpsEntry(item_id=prod.id,plan_date=date.today()+timedelta(days=d),quantity=q))

    wh = Warehouse(warehouse_code="WH-DEF",warehouse_name="默认仓库",location="主仓库")
    db.add(wh); db.flush()
    inv_count = 0
    for m in db.query(M).all():
        db.add(InventoryRecord(item_id=m.id,warehouse_id=wh.id,on_hand_qty=0,batch_no="init"))
        inv_count += 1
    db.commit()

    print(f"✅ 完整导入完成！")
    print(f"   物料: 1成品 + {len(modules)}模块 + {total_parts}零件 = {1+len(modules)+total_parts} 个")
    print(f"   BOM: 三级结构 (成品→{len(modules)}模块→{total_parts}零件), {total_lines}行")
    print(f"   MPS: 3批共15台 | 库存: {inv_count}条")
    for mn, parts in MODULES.items():
        print(f"   [{mn}] {len(parts)} 项")
