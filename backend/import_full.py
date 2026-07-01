"""全量导入：按金山文档结构调整所有五模块数据并写入本地DB"""
import os, sys

sys.path.insert(0, r'C:\Users\20210817\WorkBuddy\2026-06-30-14-24-08\mrp-system\backend')
os.environ['DB_BACKEND'] = 'sqlite'

from app.core.database import init_db, SessionLocal
from app.models.material import MaterialMaster
from app.models.bom import BomHeader, BomLine
from app.models.supplier import Supplier

init_db()
db = SessionLocal()

# ====== 产品 ======
product = db.query(MaterialMaster).filter(MaterialMaster.material_code == 'PROJ-SWG-15').first()
if not product:
    product = MaterialMaster(material_code='PROJ-SWG-15', material_name='三工位-15台',
        material_type='成品', level_type='产品', unit='台', is_purchased=False,
        lead_time=30, safety_stock=0, lot_size_rule='LFL')
    db.add(product); db.flush()
n = 1  # 装机台数

# ====== 各模块数据 ======
modules = [
    ('MOD-PURCHASED-SWG', '外购件模块', 'MP', [
        # [型号, 名称规格, 品牌, 单台数量, 单位, 单价, 提交人]
        ['6204-2RS','深沟球轴承 6204-2RS 内径20mm','SKF',4,'个',35,'熊振'],
        ['6005-2RS','深沟球轴承 6005-2RS 内径25mm','NSK',4,'个',42,'熊振'],
        ['HGH20CA-1000','直线导轨 HGH20CA 长度1000mm 含滑块×2','上银HIWIN',2,'套',1280,'熊振'],
        ['SFU1605-1000','滚珠丝杆 SFU1605 导程5mm 长度1000mm','上银HIWIN',2,'套',980,'熊振'],
        ['DS40-AL','联轴器 DS40 梅花型 铝合金 夹紧式','米思米',4,'个',45,'熊振'],
        ['MDBB32-100Z','气缸 MDBB32-100Z 双作用 32mm×100mm','SMC',6,'个',320,'熊振'],
        ['MDBB40-150Z','气缸 MDBB40-150Z 双作用 40mm×150mm','SMC',3,'个',420,'熊振'],
        ['D-M9B','气缸传感器 D-M9B 无触点 固态开关','SMC',12,'个',55,'熊振'],
        ['AS2201F-01-08S','调速阀 AS2201F-01-08S 单向节流','SMC',15,'个',18,'熊振'],
        ['ZP3-T08BUN','真空吸盘 ZP3-T08BUN 丁腈橡胶 平型','SMC',12,'个',25,'熊振'],
        ['ZH05BS-02-02','真空发生器 ZH05BS 喷嘴直径0.5mm','SMC',4,'个',180,'熊振'],
        ['KQ2H06-01AS','气管直通接头 KQ2H06-01AS φ6-1/8','SMC',40,'个',3.5,'熊振'],
        ['KQ2L06-01AS','气管弯头 KQ2L06-01AS φ6-1/8','SMC',30,'个',4.5,'熊振'],
        ['2500.038.100.0','拖链 E2/000 25×38 桥式 内高25mm','易格斯IGUS',4,'根',380,'熊振'],
        ['RB1007S','油压缓冲器 RB1007S 行程7mm','SMC',8,'个',65,'熊振'],
        ['GB70-M6x20','内六角螺栓 M6×20 12.9级 发黑','国产',200,'个',0.15,'熊振'],
        ['GB70-M8x25','内六角螺栓 M8×25 12.9级 发黑','国产',150,'个',0.25,'熊振'],
        ['GB93-M6','弹簧垫圈 M6 65Mn 发黑','国产',200,'个',0.08,'熊振'],
        ['GB97-M6','平垫圈 M6 A2不锈钢','国产',200,'个',0.06,'熊振'],
        ['MSH8-30','定位销 D8×30 淬火钢 圆柱型','米思米',16,'个',3.5,'熊振'],
        ['NBR-O30','O型圈套装 NBR 丁腈橡胶 30种规格','国产',2,'盒',45,'熊振'],
        ['PTFE-2mm','密封垫片 PTFE 聚四氟乙烯 2mm厚','国产',4,'张',25,'熊振'],
        ['MOBIL-EP2','润滑脂 美孚EP2 复合锂基 2kg/桶','美孚',2,'桶',68,'熊振'],
        ['LOCTITE-242','螺纹胶 乐泰242 中强度 50ml','乐泰',3,'支',28,'熊振'],
        ['WD40-400ML','防锈清洁剂 WD-40 多用途 400ml','WD-40',5,'瓶',18,'熊振'],
    ]),
    ('MOD-FABRICATED-SWG', '外加工钣金模块', 'FP', [
        ['SWG-BP-001','钣金底板 1200×800×20mm','外协加工-钣金',1,'块',850,'熊振'],
        ['SWG-CL-001','钣金立柱 方管100×100×6×800mm','外协加工-钣金',4,'根',320,'熊振'],
        ['SWG-BM-001','钣金横梁 方管80×80×5×1000mm','外协加工-钣金',6,'根',280,'熊振'],
        ['SWG-MP-001','电机安装板 300×200×12mm','外协加工-钣金',6,'块',120,'熊振'],
        ['SWG-SB-001','传感器支架 5mm厚 折弯件','外协加工-钣金',12,'个',45,'熊振'],
        ['SWG-CA-001','气缸安装座 L型 焊接件','外协加工-焊接',9,'个',65,'熊振'],
        ['SWG-GB-001','导轨垫块 20×40×200mm','外协加工-机加',8,'块',55,'熊振'],
        ['SWG-BH-001','皮带轮护罩 1.5mm钣金折弯','外协加工-钣金',4,'个',150,'熊振'],
        ['SWG-CV-001','走线槽盖板 1.2mm SPCC','外协加工-钣金',8,'块',35,'熊振'],
        ['SWG-JB-001','接线盒 200×150×100mm','外协加工-钣金',3,'个',95,'熊振'],
        ['SWG-ES-001','急停按钮安装盒 铝合金','外协加工-机加',2,'个',55,'熊振'],
        ['SWG-AC-001','亚克力防护外罩 5mm透明','外协加工-亚克力',1,'套',1800,'熊振'],
        ['SWG-AV-001','亚克力观察窗 8mm透明','外协加工-亚克力',6,'块',85,'熊振'],
        ['SWG-AL-001','铝合金面板 6061-T6 6mm','外协加工-机加',1,'块',380,'熊振'],
        ['SWG-NS-001','尼龙滑块 30×40×20mm','外协加工-机加',16,'个',25,'熊振'],
    ]),
    ('MOD-ELEC-SWG', '电气模块', 'EL', [
        ['FX5U-80MT/ES','PLC主机 FX5U-80MT/ES 40入40出 晶体管','三菱',1,'台',3200,'熊振'],
        ['FX5-16EX/ES','PLC输入扩展模块 FX5-16EX/ES 16点DC24V','三菱',1,'台',980,'熊振'],
        ['FX5-16EYR/ES','PLC输出扩展模块 FX5-16EYR/ES 16点继电器','三菱',2,'台',850,'熊振'],
        ['FX5-4AD','模拟量输入模块 FX5-4AD 4通道','三菱',1,'台',1450,'熊振'],
        ['FX5-4DA','模拟量输出模块 FX5-4DA 4通道','三菱',1,'台',1380,'熊振'],
        ['GT2710-STBA','触摸屏 GOT2000 GT2710 10.4寸','三菱',1,'台',4200,'熊振'],
        ['S-350-24','开关电源 S-350-24 DC24V 14.6A','明纬',2,'台',185,'熊振'],
        ['S-150-12','开关电源 S-150-12 DC12V 12.5A','明纬',1,'台',95,'熊振'],
        ['MDR-60-24','导轨电源 MDR-60-24 DC24V 2.5A','明纬',2,'台',128,'熊振'],
        ['NXB-63-C32','小型断路器 NXB-63 C32 2P','正泰',2,'个',28,'熊振'],
        ['NXB-63-C16','小型断路器 NXB-63 C16 1P','正泰',4,'个',15,'熊振'],
        ['NXB-63-C10','小型断路器 NXB-63 C10 1P','正泰',3,'个',13,'熊振'],
        ['NXB-63-C6','小型断路器 NXB-63 C6 2P','正泰',2,'个',32,'熊振'],
        ['NXBLE-63-C32','漏电保护器 NXBLE-63 C32 2P 30mA','正泰',1,'个',55,'熊振'],
        ['CJX2-2510','交流接触器 CJX2-2510 AC220V 25A','正泰',3,'个',42,'熊振'],
        ['NR2-25','热继电器 NR2-25 7-10A','正泰',3,'个',28,'熊振'],
        ['JZX-22F/4Z','中间继电器 JZX-22F/4Z DC24V','正泰',8,'个',12,'熊振'],
        ['PYF08A-E','继电器插座 PYF08A-E 8脚','正泰',8,'个',5,'熊振'],
        ['JQX-13F-2Z','大功率继电器 JQX-13F 2组 10A DC24V','正泰',4,'个',15,'熊振'],
        ['UK2.5B-GRAY','接线端子 UK2.5B 灰色 2.5mm²','菲尼克斯',80,'个',1.5,'熊振'],
        ['UK2.5B-BLUE','接线端子 UK2.5B 蓝色 N线专用','菲尼克斯',40,'个',1.5,'熊振'],
        ['UK2.5B-PE','接地端子 UK2.5B-PE 黄绿色','菲尼克斯',30,'个',2.0,'熊振'],
        ['D-UK2.5','端子端板 D-UK2.5 灰色','菲尼克斯',20,'个',1.2,'熊振'],
        ['ZB6-LGS','端子标记条 ZB6 LGS:1-10','菲尼克斯',15,'条',3.5,'熊振'],
        ['UKH50','大电流端子 UKH50 50mm²','菲尼克斯',6,'个',8.5,'熊振'],
        ['E3Z-D61','光电传感器 E3Z-D61 漫反射 NPN 300mm','欧姆龙',3,'个',85,'熊振'],
        ['E3X-NA11','光纤放大器 E3X-NA11 NPN输出 2m','欧姆龙',3,'个',180,'熊振'],
        ['E32-DC200','光纤探头 E32-DC200 同轴型 M6','欧姆龙',3,'个',120,'熊振'],
        ['TL-Q5MC1','接近开关 TL-Q5MC1 NPN常开 5mm','欧姆龙',6,'个',35,'熊振'],
        ['E2E-X5MF1','接近开关 E2E-X5MF1 M12 NPN 5mm','欧姆龙',4,'个',48,'熊振'],
        ['D-M9B-CS1','磁性开关 D-M9B 固态无触点 1m','SMC',6,'个',55,'熊振'],
        ['WLCA12-2N','限位开关 WLCA12-2N 滚轮摆杆','欧姆龙',6,'个',42,'熊振'],
        ['SY5120-5LZD','电磁阀 SY5120 5通 单线圈 DC24V C6','SMC',3,'个',280,'熊振'],
        ['SY5220-5LZD','电磁阀 SY5220 5通 双线圈 DC24V C6','SMC',2,'个',310,'熊振'],
        ['SS5Y3-20-02','汇流板 SS5Y3-20 阀岛底座 4联','SMC',1,'个',380,'熊振'],
        ['AN103-KM5','消音器 AN103 快插型 M5 铜烧结','SMC',4,'个',8,'熊振'],
        ['AN203-02','消音器 AN203-02 R1/4 铜烧结','SMC',2,'个',12,'熊振'],
        ['XB2BS542C','急停按钮 XB2BS542C 红色 旋转复位 1NC','施耐德',2,'个',45,'熊振'],
        ['XB2BA31C','平头按钮 XB2BA31C 绿色 1NO','施耐德',3,'个',12,'熊振'],
        ['XB2BA42C','平头按钮 XB2BA42C 红色 1NC','施耐德',3,'个',12,'熊振'],
        ['XB2BA51C','平头按钮 XB2BA51C 黄色 1NO','施耐德',2,'个',12,'熊振'],
        ['XB2BVM3LC','指示灯 XB2BVM3LC 绿色 AC220V','施耐德',3,'个',18,'熊振'],
        ['XB2BVM4LC','指示灯 XB2BVM4LC 红色 AC220V','施耐德',3,'个',18,'熊振'],
        ['XB2BVM5LC','指示灯 XB2BVM5LC 黄色 AC220V','施耐德',1,'个',18,'熊振'],
        ['XB2BSB4LC','蜂鸣器 XB2BSB4LC 红色 90dB','施耐德',1,'个',55,'熊振'],
        ['XB2BD21C','选择开关 XB2BD21C 2位 自锁','施耐德',2,'个',22,'熊振'],
        ['XB2BD33C','选择开关 XB2BD33C 3位 自复位','施耐德',2,'个',25,'熊振'],
        ['SV630PS2R8I','伺服驱动器 SV630PS2R8I 750W','汇川技术',1,'台',1250,'熊振'],
        ['MS1H1-75B30','伺服电机 MS1H1 750W 3000rpm','汇川技术',1,'台',980,'熊振'],
        ['S6-L-P021','伺服动力线 S6-L-P021 3米','汇川技术',1,'根',120,'熊振'],
        ['S6-L-F021','伺服编码器线 S6-L-F021 3米','汇川技术',1,'根',135,'熊振'],
        ['DM542','步进驱动器 DM542 4.2A 128细分','雷赛智能',3,'台',185,'熊振'],
        ['57HS22-A','步进电机 57HS22 2.2N·m 4A','雷赛智能',3,'台',160,'熊振'],
        ['AE-1038.500','电气柜 AE 1800×800×500mm IP54','威图',1,'台',2800,'熊振'],
        ['SZ-2485.200','安装板 SZ 1750×750mm 2mm','威图',1,'块',320,'熊振'],
        ['VD-80-60','线槽 VD 80×60mm PVC 灰色','凯士士',15,'根',18,'熊振'],
        ['VD-60-40','线槽 VD 60×40mm PVC 灰色','凯士士',10,'根',12,'熊振'],
        ['TS35-7.5','DIN导轨 TS35 7.5mm 1m/根','国产',8,'根',8,'熊振'],
        ['PG-M20','电缆格兰头 M20×1.5 尼龙','国产',20,'个',1.5,'熊振'],
        ['PG-M25','电缆格兰头 M25×1.5 尼龙','国产',10,'个',2.0,'熊振'],
        ['LED-TL-10W','柜内照明灯 LED 10W AC220V','施耐德',1,'个',85,'熊振'],
        ['KA1238HA2','散热风扇 120×120×38mm AC220V','卡固',2,'个',55,'熊振'],
        ['KF-120','风扇过滤网 120×120mm','卡固',2,'个',12,'熊振'],
        ['RVV-4×2.5','动力电缆 RVV 4×2.5mm² 黑色','起帆',50,'米',8.5,'熊振'],
        ['RVV-10×0.5','控制电缆 RVV 10×0.5mm² 黑色','起帆',30,'米',6.5,'熊振'],
        ['RVVP-4×0.5','屏蔽电缆 RVVP 4×0.5mm²','起帆',40,'米',5.5,'熊振'],
        ['CAT5E-SFTP','超五类屏蔽网线 SFTP 305米/箱','安普AMP',1,'箱',580,'熊振'],
        ['RJ45-CAT5E','水晶头 RJ45 超五类 屏蔽 100个/盒','安普AMP',1,'盒',45,'熊振'],
        ['BVR-2.5-RED','单芯软线 BVR 2.5mm² 红色','起帆',2,'卷',95,'熊振'],
        ['BVR-2.5-BLUE','单芯软线 BVR 2.5mm² 蓝色','起帆',2,'卷',95,'熊振'],
        ['BVR-1.5-BLACK','单芯软线 BVR 1.5mm² 黑色','起帆',3,'卷',58,'熊振'],
    ]),
    ('MOD-VISION-SWG', '视觉模块', 'VS', [
        ['MER-503-20GM-P','工业相机 500万像素 黑白 GigE','大恒图像',3,'台',2850,'熊振'],
        ['MER-503-20GC-P','工业相机 500万像素 彩色 GigE','大恒图像',1,'台',3200,'熊振'],
        ['M1614-MP2','定焦镜头 16mm F1.4 C口 2/3"','Computar',3,'个',850,'熊振'],
        ['M2514-MP2','定焦镜头 25mm F1.4 C口 2/3"','Computar',1,'个',980,'熊振'],
        ['RL12090-W','环形光源 120mm 90° 白光','OPT奥普特',3,'个',680,'熊振'],
        ['BL18018-W','条形光源 180×18mm 白光','OPT奥普特',2,'个',850,'熊振'],
        ['DP1024-4CH','数字光源控制器 4通道 24V/1A','OPT奥普特',2,'台',1200,'熊振'],
        ['IPC-610L-I7','视觉工控机 i7-12700/32G/512G+2T','研华',1,'台',6800,'熊振'],
        ['U2422H','显示器 23.8英寸 IPS 1920×1080','戴尔',1,'台',1200,'熊振'],
        ['CA100-AL','相机安装支架 铝合金 可调角度','大恒图像',4,'个',180,'熊振'],
        ['I350-T4','千兆网卡 PCIe x4 4口 Intel I350','Intel',1,'个',580,'熊振'],
        ['NW102-SFTP','超六类屏蔽网线 2米 蓝色','绿联',6,'根',18,'熊振'],
        ['CG-100-100','棋盘格标定板 100×100mm 陶瓷','OPT奥普特',1,'块',350,'熊振'],
        ['BP660-25.4','带通滤光片 BP660nm Φ25.4mm','Edmund',3,'片',420,'熊振'],
        ['PRA-25.4-BK7','直角棱镜 BK7 25.4mm AR镀膜','Thorlabs',2,'个',680,'熊振'],
    ]),
    ('MOD-TOOLS-SWG', '量具工具类模块', 'TL', [
        # 参照金山文档量具工具类原始数据
        ['5X0.3-100M','普通多芯线 5芯 0.3mm² 100米/卷','淘宝纵凯',1,'卷',245,'熊振'],
        ['6X0.3-100M','普通多芯线 6芯 0.3mm² 100米/卷','淘宝纵凯',1,'卷',295,'熊振'],
        ['8X0.3-100M','普通多芯线 8芯 0.3mm² 100米/卷','淘宝纵凯',1,'卷',376,'熊振'],
        ['6X0.2-100M','高柔多芯线 6芯 0.2mm² 100米/卷','淘宝纵凯',1,'卷',268,'熊振'],
        ['SX-0.5-RED','单芯软线 0.5mm² 红色 100米/卷','蓝叶淘宝',2,'卷',52,'熊振'],
        ['SX-0.5-BLK','单芯软线 0.5mm² 黑色 100米/卷','蓝叶淘宝',2,'卷',52,'熊振'],
        ['SX-0.3-RED','单芯软线 0.3mm² 红色 100米/卷','蓝叶淘宝',2,'卷',35,'熊振'],
        ['SX-0.3-BLK','单芯软线 0.3mm² 黑色 100米/卷','蓝叶淘宝',2,'卷',35,'熊振'],
        ['SX-0.3-BLU','单芯软线 0.3mm² 蓝色 100米/卷','蓝叶淘宝',2,'卷',35,'熊振'],
        ['SX-0.3-YLW','单芯软线 0.3mm² 黄色 100米/卷','蓝叶淘宝',2,'卷',35,'熊振'],
        ['SX-0.3-WHT','单芯软线 0.3mm² 白色 100米/卷','蓝叶淘宝',2,'卷',35,'熊振'],
        ['SX-0.3-GRN','单芯软线 0.3mm² 绿色 100米/卷','蓝叶淘宝',2,'卷',35,'熊振'],
        ['SX-0.3-ORG','单芯软线 0.3mm² 橙色 100米/卷','蓝叶淘宝',1,'卷',35,'熊振'],
        ['SX-0.3-PUR','单芯软线 0.3mm² 紫色 100米/卷','蓝叶淘宝',1,'卷',35,'熊振'],
        ['SX-0.3-PNK','单芯软线 0.3mm² 粉色 100米/卷','蓝叶淘宝',1,'卷',35,'熊振'],
        ['SX-0.3-GRY','单芯软线 0.3mm² 灰色 100米/卷','蓝叶淘宝',1,'卷',35,'熊振'],
        ['SX-2.5-RED','单芯软线 2.5mm² 红色 100米/卷','民赞',1,'卷',85,'熊振'],
        ['SX-2.5-BLK','单芯软线 2.5mm² 黑色 100米/卷','民赞',1,'卷',85,'熊振'],
        ['SX-1.5-RED','单芯软线 1.5mm² 红色 100米/卷','民赞',2,'卷',58,'熊振'],
        ['SX-1.5-BLK','单芯软线 1.5mm² 黑色 100米/卷','民赞',2,'卷',58,'熊振'],
        ['DG-PIN-RED','冷压端子 E型 红色 1000个/包','淘宝纵凯',1,'包',28,'熊振'],
        ['DG-PIN-BLU','冷压端子 E型 蓝色 1000个/包','淘宝纵凯',1,'包',28,'熊振'],
        ['DG-PIN-YLW','冷压端子 E型 黄色 1000个/包','淘宝纵凯',1,'包',28,'熊振'],
        ['DG-TUB-RED','热缩管 红色 φ3mm 100米/卷','蓝叶淘宝',1,'卷',15,'熊振'],
        ['DG-TUB-BLK','热缩管 黑色 φ3mm 100米/卷','蓝叶淘宝',1,'卷',15,'熊振'],
        ['DG-TUB-WHT','热缩管 白色 φ3mm 100米/卷','蓝叶淘宝',1,'卷',15,'熊振'],
        ['DG-CAB-TIE-100','尼龙扎带 3×100mm 1000根/包','淘宝纵凯',2,'包',8.5,'熊振'],
        ['DG-CAB-TIE-150','尼龙扎带 3×150mm 1000根/包','淘宝纵凯',1,'包',10,'熊振'],
        ['DG-CAB-TIE-200','尼龙扎带 4×200mm 500根/包','淘宝纵凯',3,'包',12,'熊振'],
        ['DG-INSU-TAPE','电工绝缘胶带 黑色 10卷/筒','淘宝纵凯',2,'筒',22,'熊振'],
        ['DG-DUCT-TAPE','布基胶带 50mm×30m','淘宝纵凯',3,'卷',18,'熊振'],
        ['DG-DOUBLE-TAPE','双面胶带 3M 20mm×3m','3M',5,'卷',6,'熊振'],
        ['DG-TIN-WIRE','焊锡丝 0.8mm 500g/卷','淘宝纵凯',1,'卷',45,'熊振'],
        ['DG-MARKER-TUB','线号管 白色 4mm² 100米/卷','淘宝纵凯',2,'卷',25,'熊振'],
        ['DG-RES-100-1W','碳膜电阻 100Ω 1W 100个/包','淘宝纵凯',1,'包',5,'熊振'],
        ['DG-RES-1K-1W','碳膜电阻 1KΩ 1W 100个/包','淘宝纵凯',2,'包',5,'熊振'],
        ['DG-RES-10K-0.5W','碳膜电阻 10KΩ 0.5W 100个/包','淘宝纵凯',1,'包',3,'熊振'],
        ['DG-GAS-TUBE','气管 PU 6×4mm 透明 100米/卷','淘宝纵凯',2,'卷',55,'熊振'],
        ['DG-GAS-TUBE-8','气管 PU 8×5mm 透明 100米/卷','淘宝纵凯',1,'卷',68,'熊振'],
        ['DG-GAS-CONN-6','快插直通接头 PC6-M5','淘宝纵凯',30,'个',0.8,'熊振'],
        ['DG-GAS-CONN-8','快插直通接头 PC8-01','淘宝纵凯',15,'个',1.2,'熊振'],
        ['DG-GAS-TEE-6','快插三通接头 PE-6','淘宝纵凯',10,'个',1.5,'熊振'],
        ['DG-GAS-ELBOW-6','快插弯头 PL6-M5','淘宝纵凯',10,'个',1.8,'熊振'],
        ['DG-ALLEN-SET','内六角扳手套装 9件套 1.5-10mm','淘宝纵凯',1,'套',35,'熊振'],
        ['DG-SCREWDRIVER','十字螺丝刀套装 6件套','淘宝纵凯',1,'套',28,'熊振'],
        ['DG-WRENCH','开口扳手 8-10mm','淘宝纵凯',2,'把',12,'熊振'],
        ['DG-PLIERS','尖嘴钳 6寸','淘宝纵凯',1,'把',18,'熊振'],
        ['DG-WIRE-STRIP','剥线钳 自动剥线 0.5-6mm²','淘宝纵凯',1,'把',45,'熊振'],
        ['DG-CRIMP-TOOL','冷压端子钳 0.5-6mm²','淘宝纵凯',1,'把',55,'熊振'],
        ['DG-MULTIMETER','数字万用表 DT9205A','淘宝纵凯',1,'台',68,'熊振'],
        ['DG-LEVEL','水平尺 300mm 铝合金','淘宝纵凯',1,'把',22,'熊振'],
        ['DG-CALIPER','游标卡尺 150mm 电子数显','淘宝纵凯',1,'把',85,'熊振'],
        ['DG-SOLD-IRON','电烙铁 60W 恒温','淘宝纵凯',1,'把',35,'熊振'],
        ['DG-HEAT-GUN','热风枪 2000W 调温','淘宝纵凯',1,'把',120,'熊振'],
        ['DG-DRILL-BIT','麻花钻头套装 1-10mm 13件套','淘宝纵凯',1,'套',38,'熊振'],
        ['DG-TAP-SET','丝锥套装 M3-M8 手动','淘宝纵凯',1,'套',42,'熊振'],
        ['DG-DEBURR','倒角器 内孔去毛刺','淘宝纵凯',1,'把',8,'熊振'],
        ['DG-GLUE-GUN','热熔胶枪 100W','淘宝纵凯',1,'把',25,'熊振'],
        ['DG-GLUE-STICK','热熔胶棒 11mm 透明 100根','淘宝纵凯',1,'包',15,'熊振'],
        ['DG-ALCOHOL','无水乙醇 500ml','淘宝纵凯',2,'瓶',12,'熊振'],
        ['DG-CLOTH','无尘擦拭布 100片/包','淘宝纵凯',3,'包',8,'熊振'],
        ['DG-BRUSH','防静电毛刷 小号','淘宝纵凯',2,'把',5,'熊振'],
        ['DG-CLEAN-ROD','清洁棒 棉签 200支/盒','淘宝纵凯',2,'盒',8,'熊振'],
        ['DG-STOR-BOX','零件收纳盒 12格','淘宝纵凯',3,'个',15,'熊振'],
        ['DG-LABEL','设备标签 白底黑字 100张/卷','淘宝纵凯',5,'卷',12,'熊振'],
        ['DG-MARKER-PEN','油漆笔 白色 三菱','淘宝纵凯',3,'支',6,'熊振'],
        ['DG-SAFTY-GLASS','护目镜 防冲击','淘宝纵凯',3,'副',15,'熊振'],
        ['DG-GLOVES','防静电手套 100只/包','淘宝纵凯',5,'包',18,'熊振'],
        ['DG-WRISTBAND','防静电手环 有线','淘宝纵凯',2,'个',8,'熊振'],
        ['DG-MAT','防静电桌垫 600×1200mm','淘宝纵凯',2,'张',55,'熊振'],
        ['DG-POWER-STRIP','排插 6位 3米线','公牛',3,'个',35,'熊振'],
        ['DG-USB-HUB','USB扩展器 4口 USB3.0','淘宝纵凯',2,'个',25,'熊振'],
        ['DG-CABLE-TIE','魔术贴扎带 20mm×5m','淘宝纵凯',3,'卷',12,'熊振'],
        ['DG-STOR-CART','工具推车 三层 塑料','淘宝纵凯',1,'台',280,'熊振'],
        ['DG-LIGHT-LED','工作灯 LED 便携磁吸','淘宝纵凯',2,'台',45,'熊振'],
        ['DG-AIR-BLOW','气吹球 大号 橡胶','淘宝纵凯',1,'个',15,'熊振'],
        ['DG-TWEEZER','防静电镊子套装 6件套','淘宝纵凯',1,'套',22,'熊振'],
        ['DG-CUTTER','美工刀 18mm','淘宝纵凯',2,'把',8,'熊振'],
        ['DG-MEASURE','卷尺 5米','淘宝纵凯',2,'把',10,'熊振'],
        ['DG-CABLE-MARK','电缆标记牌 100片/包','淘宝纵凯',2,'包',18,'熊振'],
    ]),
]

# ====== 批量导入 ======
total_parts = 0
module_bom_lines = {}

for mod_code, mod_name, prefix, items in modules:
    # 创建模块
    mod = db.query(MaterialMaster).filter(MaterialMaster.material_code == mod_code).first()
    if not mod:
        mod = MaterialMaster(material_code=mod_code, material_name=mod_name,
            material_type='模块', level_type='模块', unit='套',
            is_purchased=False, lead_time=0, safety_stock=0, lot_size_rule='LFL')
        db.add(mod); db.flush()
    
    # 创建零件
    lines = []
    for i, (model, name, brand, qty, unit, price, submitter) in enumerate(items):
        item_code = f'{prefix}-{i+1:04d}'
        full_name = f'{model} {name}'[:200]
        
        existing = db.query(MaterialMaster).filter(MaterialMaster.material_code == item_code).first()
        if existing:
            mat = existing
            # Update existing with price data
            mat.reference_unit_price = price
            mat.reference_submitter = submitter
        else:
            mat = MaterialMaster(
                material_code=item_code, material_name=full_name,
                specification=brand, material_type='原材料', level_type='零件',
                unit=unit, is_purchased=True,
                lead_time=5, safety_stock=0, lot_size_rule='LFL',
                reference_unit_price=price,
                reference_submitter=submitter,
            )
            db.add(mat); db.flush()
        
        lines.append({'child_code': item_code, 'qty': qty, 'position': f'{prefix}{i+1}'})
    
    db.commit()
    module_bom_lines[mod_code] = lines
    total_parts += len(items)
    print(f'  {mod_name}: {len(items)} 项')

# ====== 创建模块BOM ======
total_bom_lines = 0
for mod_code, lines in module_bom_lines.items():
    mod = db.query(MaterialMaster).filter(MaterialMaster.material_code == mod_code).first()
    bom = db.query(BomHeader).filter(BomHeader.bom_code == f'BOM-{mod_code}').first()
    if bom:
        db.query(BomLine).filter(BomLine.bom_header_id == bom.id).delete()
    else:
        bom = BomHeader(bom_code=f'BOM-{mod_code}', product_id=mod.id, version='A', status='草稿')
        db.add(bom); db.flush()
    for i, line in enumerate(lines):
        child = db.query(MaterialMaster).filter(MaterialMaster.material_code == line['child_code']).first()
        if child:
            db.add(BomLine(bom_header_id=bom.id, parent_item_id=mod.id, item_id=child.id,
                           quantity=line['qty'], position=line['position'], level=2, sort_order=i+1))
    db.commit()
    total_bom_lines += len(lines)

# ====== 创建产品BOM ======
proj_bom = db.query(BomHeader).filter(BomHeader.bom_code == 'BOM-PROJ-SWG-15').first()
if proj_bom:
    db.query(BomLine).filter(BomLine.bom_header_id == proj_bom.id).delete()
else:
    proj_bom = BomHeader(bom_code='BOM-PROJ-SWG-15', product_id=product.id, version='A', status='草稿')
    db.add(proj_bom); db.flush()

for idx, mod_code in enumerate(module_bom_lines.keys()):
    mod = db.query(MaterialMaster).filter(MaterialMaster.material_code == mod_code).first()
    if mod:
        db.add(BomLine(bom_header_id=proj_bom.id, parent_item_id=product.id, item_id=mod.id,
                       quantity=1, position=f'M{idx+1}', level=1, sort_order=idx+1))
db.commit()

# ====== 汇总 ======
mat_count = db.query(MaterialMaster).count()
bom_count = db.query(BomHeader).count()
bl_count = db.query(BomLine).count()

# Count by type
products = db.query(MaterialMaster).filter(MaterialMaster.level_type=='产品').count()
modules = db.query(MaterialMaster).filter(MaterialMaster.level_type=='模块').count()
parts = db.query(MaterialMaster).filter(MaterialMaster.level_type=='零件').count()

print(f'\n====== 导入完成 ======')
print(f'物料: {mat_count} (产品{products} + 模块{modules} + 零件{parts})')
print(f'BOM: {bom_count} 个, {bl_count} 行')
print(f'结构: 三工位-15台 → {modules}个模块 → {parts}个零件')

# Show BOM tree
print(f'\nBOM 结构:')
for h in db.query(BomHeader).order_by(BomHeader.id).all():
    lc = db.query(BomLine).filter(BomLine.bom_header_id == h.id).count()
    pn = h.product.material_name if h.product else '?'
    print(f'  [{h.status}] {h.bom_code} ({pn}) — {lc}行')

db.close()
