"""生成精简测试数据集 — 模仿三工位项目"""
import json
from datetime import datetime

now = datetime.now().isoformat()

test_data = {
    "exported_at": now,
    "tables": {
        "material_master": [
            {"id":100,"material_code":"MOD-WGJ","material_name":"外购件模块","unit":"个","material_type":"模块","level_type":"模块","lead_time":0,"safety_stock":0,"lot_size_rule":"LFL","lot_size_qty":0,"min_order_qty":0,"max_order_qty":0,"scrap_rate":0,"is_purchased":0,"is_active":1,"reference_unit_price":0,"reference_submitter":"","reference_link":"","remark":"","created_at":now,"updated_at":now},
            {"id":101,"material_code":"MOD-DQ","material_name":"电气模块","unit":"个","material_type":"模块","level_type":"模块","lead_time":0,"safety_stock":0,"lot_size_rule":"LFL","lot_size_qty":0,"min_order_qty":0,"max_order_qty":0,"scrap_rate":0,"is_purchased":0,"is_active":1,"reference_unit_price":0,"reference_submitter":"","reference_link":"","remark":"","created_at":now,"updated_at":now},
            {"id":102,"material_code":"MOD-SJ","material_name":"视觉模块","unit":"个","material_type":"模块","level_type":"模块","lead_time":0,"safety_stock":0,"lot_size_rule":"LFL","lot_size_qty":0,"min_order_qty":0,"max_order_qty":0,"scrap_rate":0,"is_purchased":0,"is_active":1,"reference_unit_price":0,"reference_submitter":"","reference_link":"","remark":"","created_at":now,"updated_at":now},
            {"id":200,"material_code":"FG-SGW001","material_name":"三工位测试台","unit":"台","material_type":"成品","level_type":"产品","lead_time":15,"safety_stock":5,"lot_size_rule":"LFL","lot_size_qty":0,"min_order_qty":0,"max_order_qty":0,"scrap_rate":0,"is_purchased":0,"is_active":1,"reference_unit_price":85000,"reference_submitter":"熊振","reference_link":"","remark":"","created_at":now,"updated_at":now},
            {"id":301,"material_code":"WGJ-001","material_name":"深沟球轴承 6204-2RS 内径20mm","unit":"个","material_type":"外购件","level_type":"零件","lead_time":21,"safety_stock":20,"lot_size_rule":"FOQ","lot_size_qty":10,"min_order_qty":4,"max_order_qty":100,"scrap_rate":0,"is_purchased":1,"is_active":1,"reference_unit_price":45,"reference_submitter":"熊振","reference_link":"","remark":"品牌:SKF","created_at":now,"updated_at":now},
            {"id":302,"material_code":"WGJ-002","material_name":"深沟球轴承 6005-2RS 内径25mm","unit":"个","material_type":"外购件","level_type":"零件","lead_time":14,"safety_stock":20,"lot_size_rule":"FOQ","lot_size_qty":10,"min_order_qty":4,"max_order_qty":100,"scrap_rate":0,"is_purchased":1,"is_active":1,"reference_unit_price":55,"reference_submitter":"熊振","reference_link":"","remark":"品牌:NSK","created_at":now,"updated_at":now},
            {"id":303,"material_code":"WGJ-003","material_name":"直线导轨 HGH15CA 上银HIWIN","unit":"根","material_type":"外购件","level_type":"零件","lead_time":30,"safety_stock":10,"lot_size_rule":"LFL","lot_size_qty":0,"min_order_qty":2,"max_order_qty":20,"scrap_rate":0,"is_purchased":1,"is_active":1,"reference_unit_price":680,"reference_submitter":"熊振","reference_link":"","remark":"品牌:上银HIWIN","created_at":now,"updated_at":now},
            {"id":304,"material_code":"WGJ-004","material_name":"联轴器 梅花型 外径40mm","unit":"个","material_type":"外购件","level_type":"零件","lead_time":7,"safety_stock":15,"lot_size_rule":"FOQ","lot_size_qty":5,"min_order_qty":3,"max_order_qty":50,"scrap_rate":0,"is_purchased":1,"is_active":1,"reference_unit_price":120,"reference_submitter":"熊振","reference_link":"","remark":"品牌:米思米","created_at":now,"updated_at":now},
            {"id":401,"material_code":"DQ-001","material_name":"PLC控制器 FX5U-32MT 三菱","unit":"台","material_type":"零件","level_type":"零件","lead_time":14,"safety_stock":5,"lot_size_rule":"LFL","lot_size_qty":0,"min_order_qty":1,"max_order_qty":10,"scrap_rate":0,"is_purchased":1,"is_active":1,"reference_unit_price":3200,"reference_submitter":"熊振","reference_link":"","remark":"品牌:三菱","created_at":now,"updated_at":now},
            {"id":402,"material_code":"DQ-002","material_name":"伺服电机 HG-KR43 三菱 400W","unit":"台","material_type":"零件","level_type":"零件","lead_time":21,"safety_stock":5,"lot_size_rule":"LFL","lot_size_qty":0,"min_order_qty":1,"max_order_qty":10,"scrap_rate":0,"is_purchased":1,"is_active":1,"reference_unit_price":2800,"reference_submitter":"熊振","reference_link":"","remark":"品牌:三菱","created_at":now,"updated_at":now},
            {"id":403,"material_code":"DQ-003","material_name":"开关电源 24V 10A 明纬","unit":"个","material_type":"零件","level_type":"零件","lead_time":7,"safety_stock":10,"lot_size_rule":"FOQ","lot_size_qty":5,"min_order_qty":2,"max_order_qty":30,"scrap_rate":0,"is_purchased":1,"is_active":1,"reference_unit_price":380,"reference_submitter":"熊振","reference_link":"","remark":"品牌:明纬","created_at":now,"updated_at":now},
            {"id":404,"material_code":"DQ-004","material_name":"断路器 3P 32A 施耐德","unit":"个","material_type":"零件","level_type":"零件","lead_time":5,"safety_stock":8,"lot_size_rule":"FOQ","lot_size_qty":4,"min_order_qty":1,"max_order_qty":20,"scrap_rate":0,"is_purchased":1,"is_active":1,"reference_unit_price":180,"reference_submitter":"熊振","reference_link":"","remark":"品牌:施耐德","created_at":now,"updated_at":now},
            {"id":501,"material_code":"SJ-001","material_name":"工业相机 500万像素 USB3.0","unit":"台","material_type":"零件","level_type":"零件","lead_time":14,"safety_stock":3,"lot_size_rule":"LFL","lot_size_qty":0,"min_order_qty":1,"max_order_qty":10,"scrap_rate":0,"is_purchased":1,"is_active":1,"reference_unit_price":4500,"reference_submitter":"熊振","reference_link":"","remark":"品牌:大恒图像","created_at":now,"updated_at":now},
            {"id":502,"material_code":"SJ-002","material_name":"镜头 25mm F1.4 C口","unit":"个","material_type":"零件","level_type":"零件","lead_time":7,"safety_stock":3,"lot_size_rule":"LFL","lot_size_qty":0,"min_order_qty":1,"max_order_qty":10,"scrap_rate":0,"is_purchased":1,"is_active":1,"reference_unit_price":1800,"reference_submitter":"熊振","reference_link":"","remark":"品牌:Computar","created_at":now,"updated_at":now},
            {"id":503,"material_code":"SJ-003","material_name":"LED环形光源 白色 内径60mm","unit":"个","material_type":"零件","level_type":"零件","lead_time":7,"safety_stock":3,"lot_size_rule":"LFL","lot_size_qty":0,"min_order_qty":1,"max_order_qty":10,"scrap_rate":0,"is_purchased":1,"is_active":1,"reference_unit_price":650,"reference_submitter":"熊振","reference_link":"","remark":"品牌:OPT","created_at":now,"updated_at":now},
            {"id":504,"material_code":"SJ-004","material_name":"千兆网卡 PCIe 4口 Intel I350","unit":"块","material_type":"零件","level_type":"零件","lead_time":5,"safety_stock":3,"lot_size_rule":"LFL","lot_size_qty":0,"min_order_qty":1,"max_order_qty":5,"scrap_rate":0,"is_purchased":1,"is_active":1,"reference_unit_price":850,"reference_submitter":"熊振","reference_link":"","remark":"品牌:Intel","created_at":now,"updated_at":now},
        ],
        "bom_header": [
            {"id":100,"bom_code":"BOM-SGW001","product_id":200,"version":"A","revision":"0","status":"生效","effective_date":"2026-07-01","expire_date":None,"change_reason":"","created_at":now,"updated_at":now},
        ],
        "bom_line": [
            {"id":1001,"bom_header_id":100,"parent_item_id":100,"item_id":301,"quantity":4,"level":0,"position":1,"scrap_rate":0,"is_substitute":0,"remark":"","substitute_for_id":None,"substitute_group":"","sort_order":1},
            {"id":1002,"bom_header_id":100,"parent_item_id":100,"item_id":302,"quantity":4,"level":0,"position":2,"scrap_rate":0,"is_substitute":0,"remark":"","substitute_for_id":None,"substitute_group":"","sort_order":2},
            {"id":1003,"bom_header_id":100,"parent_item_id":100,"item_id":303,"quantity":2,"level":0,"position":3,"scrap_rate":0,"is_substitute":0,"remark":"","substitute_for_id":None,"substitute_group":"","sort_order":3},
            {"id":1004,"bom_header_id":100,"parent_item_id":100,"item_id":304,"quantity":3,"level":0,"position":4,"scrap_rate":0,"is_substitute":0,"remark":"","substitute_for_id":None,"substitute_group":"","sort_order":4},
            {"id":2001,"bom_header_id":100,"parent_item_id":101,"item_id":401,"quantity":1,"level":0,"position":5,"scrap_rate":0,"is_substitute":0,"remark":"","substitute_for_id":None,"substitute_group":"","sort_order":5},
            {"id":2002,"bom_header_id":100,"parent_item_id":101,"item_id":402,"quantity":3,"level":0,"position":6,"scrap_rate":0,"is_substitute":0,"remark":"","substitute_for_id":None,"substitute_group":"","sort_order":6},
            {"id":2003,"bom_header_id":100,"parent_item_id":101,"item_id":403,"quantity":2,"level":0,"position":7,"scrap_rate":0,"is_substitute":0,"remark":"","substitute_for_id":None,"substitute_group":"","sort_order":7},
            {"id":2004,"bom_header_id":100,"parent_item_id":101,"item_id":404,"quantity":1,"level":0,"position":8,"scrap_rate":0,"is_substitute":0,"remark":"","substitute_for_id":None,"substitute_group":"","sort_order":8},
            {"id":3001,"bom_header_id":100,"parent_item_id":102,"item_id":501,"quantity":1,"level":0,"position":9,"scrap_rate":0,"is_substitute":0,"remark":"","substitute_for_id":None,"substitute_group":"","sort_order":9},
            {"id":3002,"bom_header_id":100,"parent_item_id":102,"item_id":502,"quantity":1,"level":0,"position":10,"scrap_rate":0,"is_substitute":0,"remark":"","substitute_for_id":None,"substitute_group":"","sort_order":10},
            {"id":3003,"bom_header_id":100,"parent_item_id":102,"item_id":503,"quantity":1,"level":0,"position":11,"scrap_rate":0,"is_substitute":0,"remark":"","substitute_for_id":None,"substitute_group":"","sort_order":11},
            {"id":3004,"bom_header_id":100,"parent_item_id":102,"item_id":504,"quantity":1,"level":0,"position":12,"scrap_rate":0,"is_substitute":0,"remark":"","substitute_for_id":None,"substitute_group":"","sort_order":12},
        ],
        "inventory_record": [
            {"id":1001,"item_id":301,"warehouse_id":1,"location_code":"A01","batch_no":"","on_hand_qty":100,"allocated_qty":0,"reserved_qty":0,"on_order_qty":0,"on_production_qty":0,"last_count_date":"2026-07-01","updated_at":now},
            {"id":1002,"item_id":302,"warehouse_id":1,"location_code":"A02","batch_no":"","on_hand_qty":100,"allocated_qty":0,"reserved_qty":0,"on_order_qty":0,"on_production_qty":0,"last_count_date":"2026-07-01","updated_at":now},
            {"id":1003,"item_id":303,"warehouse_id":1,"location_code":"A03","batch_no":"","on_hand_qty":50,"allocated_qty":0,"reserved_qty":0,"on_order_qty":0,"on_production_qty":0,"last_count_date":"2026-07-01","updated_at":now},
            {"id":1004,"item_id":304,"warehouse_id":1,"location_code":"A04","batch_no":"","on_hand_qty":60,"allocated_qty":0,"reserved_qty":0,"on_order_qty":0,"on_production_qty":0,"last_count_date":"2026-07-01","updated_at":now},
            {"id":2001,"item_id":401,"warehouse_id":1,"location_code":"B01","batch_no":"","on_hand_qty":20,"allocated_qty":0,"reserved_qty":0,"on_order_qty":0,"on_production_qty":0,"last_count_date":"2026-07-01","updated_at":now},
            {"id":2002,"item_id":402,"warehouse_id":1,"location_code":"B02","batch_no":"","on_hand_qty":15,"allocated_qty":0,"reserved_qty":0,"on_order_qty":0,"on_production_qty":0,"last_count_date":"2026-07-01","updated_at":now},
            {"id":2003,"item_id":403,"warehouse_id":1,"location_code":"B03","batch_no":"","on_hand_qty":30,"allocated_qty":0,"reserved_qty":0,"on_order_qty":0,"on_production_qty":0,"last_count_date":"2026-07-01","updated_at":now},
            {"id":2004,"item_id":404,"warehouse_id":1,"location_code":"B04","batch_no":"","on_hand_qty":25,"allocated_qty":0,"reserved_qty":0,"on_order_qty":0,"on_production_qty":0,"last_count_date":"2026-07-01","updated_at":now},
            {"id":3001,"item_id":501,"warehouse_id":1,"location_code":"C01","batch_no":"","on_hand_qty":8,"allocated_qty":0,"reserved_qty":0,"on_order_qty":0,"on_production_qty":0,"last_count_date":"2026-07-01","updated_at":now},
            {"id":3002,"item_id":502,"warehouse_id":1,"location_code":"C02","batch_no":"","on_hand_qty":8,"allocated_qty":0,"reserved_qty":0,"on_order_qty":0,"on_production_qty":0,"last_count_date":"2026-07-01","updated_at":now},
            {"id":3003,"item_id":503,"warehouse_id":1,"location_code":"C03","batch_no":"","on_hand_qty":8,"allocated_qty":0,"reserved_qty":0,"on_order_qty":0,"on_production_qty":0,"last_count_date":"2026-07-01","updated_at":now},
            {"id":3004,"item_id":504,"warehouse_id":1,"location_code":"C04","batch_no":"","on_hand_qty":8,"allocated_qty":0,"reserved_qty":0,"on_order_qty":0,"on_production_qty":0,"last_count_date":"2026-07-01","updated_at":now},
        ],
        "warehouse": [
            {"id":1,"warehouse_code":"WH-01","warehouse_name":"主仓库","location":"A区1楼","is_active":1,"created_at":now},
        ],
        "mps_entry": [
            {"id":1,"item_id":200,"plan_date":"2026-08-01","quantity":5,"source_type":"销售订单","source_id":"","is_frozen":0,"status":"进行中"},
            {"id":2,"item_id":200,"plan_date":"2026-09-01","quantity":10,"source_type":"预测","source_id":"","is_frozen":0,"status":"进行中"},
        ],
    }
}

with open("C:/Users/20210817/Desktop/三工位测试数据_演示版.json", "w", encoding="utf-8") as f:
    json.dump(test_data, f, ensure_ascii=False, indent=2)

size = len(json.dumps(test_data))
print(f"创建成功: {size} bytes")
for k, v in test_data["tables"].items():
    print(f"  {k}: {len(v)} 行")
