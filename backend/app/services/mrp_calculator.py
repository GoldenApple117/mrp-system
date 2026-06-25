"""MRP 核心计算引擎

MRP = Master Production Schedule + BOM + Inventory → Net Requirements

逐层展开逻辑：
1. 计算低保码(LLC)，确定物料的处理顺序
2. 从0层(成品)开始，逐层向下
3. 每层：毛需求 → 扣除库存 → 净需求 → 批量规则 → 提前期倒推
4. 上层计划下达量 → 下层毛需求（通过BOM展开）
"""
from datetime import datetime, date, timedelta
from collections import defaultdict
from typing import Dict, List, Tuple, Optional
from math import ceil
import logging

logger = logging.getLogger(__name__)


class MrpCalculator:
    """MRP核心计算器"""

    def __init__(self, db_session, horizon_days: int = 90, time_fence_days: int = 7):
        self.db = db_session
        self.horizon_days = horizon_days
        self.time_fence_days = time_fence_days
        self.today = date.today()

    def generate_time_buckets(self) -> List[date]:
        """生成每日时间桶"""
        return [self.today + timedelta(days=i) for i in range(self.horizon_days + 1)]

    def compute_low_level_codes(self, all_bom_lines) -> Dict[str, int]:
        """
        计算低保码 (Low-Level Code, LLC)
        每个物料取其出现的最大层级，确保只在其最低层级处理一次

        Returns:
            {material_code: llc_level}
        """
        # 构建父子关系图：{parent_code: [child_code, ...]}
        parent_to_children = defaultdict(list)
        child_to_parents = defaultdict(list)
        all_codes = set()

        for line in all_bom_lines:
            parent_code = line.get("parent_code", "")
            child_code = line.get("child_code", "")
            if parent_code and child_code:
                parent_to_children[parent_code].append(child_code)
                child_to_parents[child_code].append(parent_code)
                all_codes.add(parent_code)
                all_codes.add(child_code)

        llc = {}

        def traverse(code, current_level):
            llc[code] = max(llc.get(code, 0), current_level)
            for child in parent_to_children.get(code, []):
                traverse(child, current_level + 1)

        # 顶层物料(parent_code 为 NULL 或没有父级的)
        top_level = [c for c in all_codes if c not in child_to_parents]
        for top_code in top_level:
            traverse(top_code, 0)

        return llc

    def apply_lot_sizing(self, net_qty: float, rule: str, lot_size: float,
                         min_qty: float = 0, max_qty: float = 0) -> float:
        """应用批量规则"""
        if net_qty <= 0:
            return 0

        if rule == "LFL":
            result = net_qty
        elif rule == "FOQ":
            result = ceil(net_qty / lot_size) * lot_size if lot_size > 0 else net_qty
        elif rule == "EOQ":
            result = max(net_qty, lot_size)
        elif rule == "MULT":
            result = ceil(net_qty / lot_size) * lot_size if lot_size > 0 else net_qty
        else:
            result = net_qty

        if min_qty > 0:
            result = max(result, min_qty)
        if max_qty > 0:
            result = min(result, max_qty)

        return result

    def calculate(self, mps_entries: List[dict], material_masters: List[dict],
                  bom_lines: List[dict], inventory_snapshot: Dict[str, dict],
                  scheduled_receipts: Dict[str, List[dict]],
                  substitute_groups: Dict[str, List[dict]] = None) -> Tuple[List[dict], List[dict]]:
        """
        MRP核心计算

        Args:
            mps_entries: MPS计划 [{item_code, plan_date, quantity}, ...]
            material_masters: 物料主数据 [{code, lead_time, safety_stock, lot_size_rule, ...}, ...]
            bom_lines: BOM行 [{parent_code, child_code, quantity_per, is_substitute, substitute_group}, ...]
            inventory_snapshot: 库存快照 {item_code: {on_hand, allocated, reserved}}
            scheduled_receipts: 在途/在制 {item_code: [{date, quantity}, ...]}
            substitute_groups: 替代料组 {group_name: [{item_code, on_hand}, ...], ...}

        Returns:
            (planned_orders, exceptions):
                planned_orders: [{item_code, level, order_type, release_date,
                                  required_date, quantity, parent_code}, ...]
                exceptions: [{type, item_code, message, severity}, ...]
        """
        time_buckets = self.generate_time_buckets()
        planned_orders = []
        exceptions = []

        # 构建物料索引
        material_map = {m["code"]: m for m in material_masters}

        # 构建替代料组索引 {item_code: group_name}
        item_to_sub_group = {}
        for bl in bom_lines:
            if bl.get("is_substitute") and bl.get("substitute_group"):
                item_to_sub_group[bl["child_code"]] = bl["substitute_group"]

        # Step 1: 计算低保码
        llc = self.compute_low_level_codes(bom_lines)

        # 按LLC分组
        llc_groups = defaultdict(list)
        for code, level in llc.items():
            llc_groups[level].append(code)

        max_level = max(llc_groups.keys()) if llc_groups else 0

        # 存储每层每个物料在不同时间桶的毛需求
        # gross_requirements[code][date_str] = quantity
        gross_requirements: Dict[str, Dict[str, float]] = defaultdict(lambda: defaultdict(float))

        # 存储计划下达量（用于传递给下层）
        # planned_releases[code][date_str] = quantity
        planned_releases: Dict[str, Dict[str, float]] = defaultdict(lambda: defaultdict(float))

        # Step 2: 处理0层 — 毛需求来自MPS
        for mps in mps_entries:
            item_code = mps["item_code"]
            plan_date = mps["plan_date"]
            quantity = mps["quantity"]
            if isinstance(plan_date, str):
                plan_date = date.fromisoformat(plan_date)
            gross_requirements[item_code][plan_date.isoformat()] += quantity

        # Step 3: 逐层计算
        for level in range(max_level + 1):
            level_items = llc_groups.get(level, [])

            for item_code in level_items:
                mat = material_map.get(item_code)
                if not mat:
                    continue

                inv = inventory_snapshot.get(item_code, {
                    "on_hand": 0, "allocated": 0, "reserved": 0
                })
                sched_recv = scheduled_receipts.get(item_code, [])
                lead_time = mat.get("lead_time", 0)
                safety_stock = mat.get("safety_stock", 0)
                lot_rule = mat.get("lot_size_rule", "LFL")
                lot_size = mat.get("lot_size_qty", 1)
                min_qty = mat.get("min_order_qty", 0)
                max_qty = mat.get("max_order_qty", 0)
                is_purchased = mat.get("is_purchased", True)

                # 构建在途/在制按日期索引
                sched_map = defaultdict(float)
                for sr in sched_recv:
                    d = sr["date"]
                    if isinstance(d, str):
                        d = date.fromisoformat(d)
                    sched_map[d.isoformat()] += sr["quantity"]

                # 逐期计算净需求
                projected_available = inv.get("on_hand", 0) - inv.get("allocated", 0) - inv.get("reserved", 0)
                shortfall_dates = []

                for tb in time_buckets:
                    tb_str = tb.isoformat()

                    # 加入在途在制
                    projected_available += sched_map.get(tb_str, 0)

                    # 扣除毛需求
                    gross = gross_requirements.get(item_code, {}).get(tb_str, 0)
                    projected_available -= gross

                    # 低于安全库存 → 需要下达
                    if projected_available < safety_stock:
                        net_qty = safety_stock - projected_available

                        # ---- 替代料处理 ----
                        substituted_qty = 0
                        sub_group = item_to_sub_group.get(item_code)
                        if sub_group and substitute_groups and sub_group in substitute_groups:
                            for sub in substitute_groups[sub_group]:
                                sub_code = sub["item_code"]
                                if sub_code == item_code:
                                    continue
                                sub_avail = sub["on_hand"] - sub.get("allocated", 0) - sub.get("reserved", 0)
                                if sub_avail > 0:
                                    take = min(net_qty - substituted_qty, sub_avail)
                                    if take > 0:
                                        substituted_qty += take
                                        sub["on_hand"] -= take  # 从替代料扣减
                                        exceptions.append({
                                            "type": "SUBSTITUTE",
                                            "item_code": item_code,
                                            "message": f"物料 {item_code} 缺料 {net_qty:.0f}，由替代料 {sub_code} 提供 {take:.0f}",
                                            "severity": "INFO",
                                        })

                        net_qty_after_sub = net_qty - substituted_qty

                        # 应用批量规则
                        planned_qty = self.apply_lot_sizing(
                            net_qty_after_sub, lot_rule, lot_size, min_qty, max_qty
                        )

                        if planned_qty > 0:
                            release_date = tb - timedelta(days=lead_time)

                            order_type = "PURCHASE" if is_purchased else "PRODUCTION"

                            planned_orders.append({
                                "item_code": item_code,
                                "level": level,
                                "order_type": order_type,
                                "release_date": release_date.isoformat(),
                                "required_date": tb_str,
                                "quantity": planned_qty,
                                "parent_code": "",
                            })

                            # 记录下达量，用于传递给子物料
                            planned_releases[item_code][release_date.isoformat()] += planned_qty

                            projected_available += planned_qty
                            shortfall_dates.append(tb_str)

                # 例外信息
                if shortfall_dates:
                    exceptions.append({
                        "type": "SHORTAGE",
                        "item_code": item_code,
                        "message": f"物料 {item_code} 缺料，最早缺料日期 {shortfall_dates[0]}",
                        "severity": "ERROR",
                    })

                if inv.get("on_hand", 0) < safety_stock:
                    exceptions.append({
                        "type": "SAFETY_STOCK_ALERT",
                        "item_code": item_code,
                        "message": f"物料 {item_code} 当前库存({inv['on_hand']})低于安全库存({safety_stock})",
                        "severity": "WARNING",
                    })

            # Step 4: 将本层的计划下达量展开为下层的毛需求
            for item_code in level_items:
                releases = planned_releases.get(item_code, {})
                if not releases:
                    continue

                # 查找BOM中该物料的所有子物料
                for bl in bom_lines:
                    if bl.get("parent_code") == item_code:
                        child_code = bl["child_code"]
                        qty_per = bl.get("quantity_per", 1)
                        scrap = bl.get("scrap_rate", 0)

                        for rel_date_str, rel_qty in releases.items():
                            # 考虑损耗
                            demand = rel_qty * qty_per * (1 + scrap / 100)
                            gross_requirements[child_code][rel_date_str] += demand

        # 检查逾期采购单
        for item_code, receipts in scheduled_receipts.items():
            for sr in receipts:
                d = sr["date"]
                if isinstance(d, str):
                    d = date.fromisoformat(d)
                if d < self.today and sr["quantity"] > 0:
                    exceptions.append({
                        "type": "OVERDUE_ORDER",
                        "item_code": item_code,
                        "message": f"物料 {item_code} 在途单 {sr.get('ref_no', '')} 已逾期",
                        "severity": "ERROR",
                    })

        return planned_orders, exceptions
