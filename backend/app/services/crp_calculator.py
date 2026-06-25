"""CRP 产能需求计划计算器

CRP = Capacity Requirements Planning
校验 MPS/MRP 工单在设备/人力产能范围内，识别瓶颈工作中心。

计算公式（每个工作中心 × 每个时间桶）：
    Load = Σ(工单数量 × 单件工时 / 效率) + 准备时间
    Utilization = Load / Capacity × 100%
"""
from datetime import date, timedelta
from collections import defaultdict
from typing import List, Dict, Tuple
import logging

logger = logging.getLogger(__name__)


class CrpCalculator:
    """CRP产能计算器"""

    def __init__(self, horizon_days: int = 60):
        self.horizon_days = horizon_days
        self.today = date.today()

    def generate_time_buckets(self) -> List[date]:
        """生成每日/每周时间桶"""
        # 以周为单位
        weeks = []
        for w in range(self.horizon_days // 7 + 1):
            weeks.append(self.today + timedelta(days=w * 7))
        return weeks

    def calculate(self, work_orders: List[dict], work_centers: List[dict],
                  routings: List[dict], operations: List[dict]) -> dict:
        """
        产能计算

        Args:
            work_orders: 工单列表 [{item_id, plan_qty, start_date, end_date, work_center_id, routing_id}, ...]
            work_centers: 工作中心 [{id, center_code, center_name, capacity_per_day, efficiency}, ...]
            routings: 工艺路线 [{id, item_id, routing_code}, ...]
            operations: 工序 [{routing_header_id, seq_no, work_center_id, operation_name, setup_time, run_time_per_unit}, ...]

        Returns:
            {
                "load_analysis": [...],
                "bottlenecks": [...],
                "summary": {...}
            }
        """
        time_buckets = self.generate_time_buckets()

        # 构建索引
        wc_map = {wc["id"]: wc for wc in work_centers}
        routing_map = {r["id"]: r for r in routings}

        # {work_center_id: {week_start: load_hours}}
        wc_load: Dict[int, Dict[str, float]] = defaultdict(lambda: defaultdict(float))
        # {work_center_id: {week_start: [order_details]}}
        wc_details: Dict[int, Dict[str, list]] = defaultdict(lambda: defaultdict(list))

        for wo in work_orders:
            routing_id = wo.get("routing_id")
            if not routing_id:
                continue

            # 获取该工艺路线的工序
            wo_ops = [op for op in operations if op["routing_header_id"] == routing_id]
            if not wo_ops:
                continue

            qty = wo.get("plan_qty", 0)
            start = wo.get("start_date")
            end = wo.get("end_date")
            if isinstance(start, str):
                start = date.fromisoformat(start)
            if isinstance(end, str):
                end = date.fromisoformat(end)

            # 确定工单落在哪些时间桶
            affected_weeks = [tb for tb in time_buckets if start <= tb + timedelta(days=7) and end >= tb]

            for op in sorted(wo_ops, key=lambda o: o.get("seq_no", 0)):
                wc_id = op.get("work_center_id")
                if not wc_id:
                    continue

                setup = op.get("setup_time", 0)
                run_time = op.get("run_time_per_unit", 0)
                wc = wc_map.get(wc_id, {})

                # 总负荷 = 准备时间 + 数量 × 单件工时 / 效率
                eff = wc.get("efficiency", 100) / 100
                total_load = setup + (qty * run_time / eff) if eff > 0 else setup + qty * run_time

                # 分摊到各个受影响的时间桶
                load_per_week = total_load / len(affected_weeks) if affected_weeks else total_load

                for tb in affected_weeks:
                    tb_str = tb.isoformat()
                    wc_load[wc_id][tb_str] += load_per_week
                    wc_details[wc_id][tb_str].append({
                        "wo_number": wo.get("wo_number", ""),
                        "operation_name": op.get("operation_name", ""),
                        "load_hours": round(load_per_week, 2),
                        "setup_time": setup,
                        "run_time_total": round(qty * run_time, 2),
                    })

        # 生成分析结果
        load_analysis = []
        bottlenecks = []

        for wc in work_centers:
            wc_id = wc["id"]
            total_capacity_hours = 0
            total_load_hours = 0

            for tb in time_buckets:
                tb_str = tb.isoformat()
                # 周产能 = 日产能 × 效率 × 1周(5天)
                capacity = wc.get("capacity_per_day", 8) * (wc.get("efficiency", 100) / 100) * 5
                load = wc_load[wc_id].get(tb_str, 0)

                total_capacity_hours += capacity
                total_load_hours += load

                utilization = round(load / capacity * 100, 1) if capacity > 0 else 0.0

                period = {
                    "work_center_id": wc_id,
                    "center_name": wc.get("center_name", ""),
                    "week_start": tb_str,
                    "capacity_hours": round(capacity, 1),
                    "load_hours": round(load, 1),
                    "utilization_pct": utilization,
                    "is_overloaded": utilization > 100,
                    "details": wc_details[wc_id].get(tb_str, []),
                }
                load_analysis.append(period)

                if utilization > 100:
                    bottlenecks.append({
                        "work_center_id": wc_id,
                        "center_name": wc.get("center_name", ""),
                        "week_start": tb_str,
                        "utilization_pct": utilization,
                        "overload_hours": round(load - capacity, 1),
                        "severity": "CRITICAL" if utilization > 130 else "WARNING",
                    })

        overall_util = round(
            total_load_hours / total_capacity_hours * 100, 1
        ) if total_capacity_hours > 0 else 0.0

        return {
            "success": True,
            "message": "CRP计算完成",
            "data": {
                "load_analysis": load_analysis,
                "bottlenecks": bottlenecks,
                "summary": {
                    "total_work_centers": len(work_centers),
                    "total_orders_analyzed": len(work_orders),
                    "total_load_hours": round(total_load_hours, 1),
                    "total_capacity_hours": round(total_capacity_hours, 1),
                    "overall_utilization_pct": overall_util,
                    "bottleneck_count": len(bottlenecks),
                    "horizon_days": self.horizon_days,
                },
            },
        }
