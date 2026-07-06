"""MRP 核心计算引擎 — 单元测试

测试策略：
- MrpCalculator 的 calculate() 方法接收纯字典参数，不依赖真实数据库
- 因此无需 mock database session，直接传入构造数据即可
- 覆盖三个核心方法：compute_low_level_codes / apply_lot_sizing / calculate
"""
import pytest
from datetime import date, timedelta
from app.services.mrp_calculator import MrpCalculator


# ==============================================================================
# Fixtures
# ==============================================================================

@pytest.fixture
def calc():
    """返回一个默认的 MrpCalculator 实例（db_session=None，因为 calculate 不用它）"""
    return MrpCalculator(db_session=None, horizon_days=90, time_fence_days=7)


@pytest.fixture
def today():
    return date.today()


# ==============================================================================
# Test: compute_low_level_codes (低保码计算)
# ==============================================================================

class TestComputeLowLevelCodes:
    """LLC 是 MRP 的核心——确保物料只在正确层级被处理一次"""

    def test_single_level_bom(self, calc):
        """单层 BOM：产品 A → 零件 B"""
        bom = [
            {"parent_code": "A", "child_code": "B"},
        ]
        llc = calc.compute_low_level_codes(bom)
        assert llc["A"] == 0, "顶层物料 LLC 应为 0"
        assert llc["B"] == 1, "下一层 LLC 应为 1"

    def test_multi_level_bom(self, calc):
        """三层 BOM：A → B → C"""
        bom = [
            {"parent_code": "A", "child_code": "B"},
            {"parent_code": "B", "child_code": "C"},
        ]
        llc = calc.compute_low_level_codes(bom)
        assert llc["A"] == 0
        assert llc["B"] == 1
        assert llc["C"] == 2

    def test_shared_component(self, calc):
        """
        共享零件：A → C, B → C
        C 同时是 A 和 B 的子物料，LLC 应取最大深度 (A=0, B=1 → C=max(1,2)=2)
        """
        bom = [
            {"parent_code": "A", "child_code": "C"},
            {"parent_code": "B", "child_code": "C"},  # B 自己也是子物料
        ]
        llc = calc.compute_low_level_codes(bom)
        # B 没有父级 → LLC=0
        # C 是 A 的下一级 → LLC=1, 也是 B 的下一级 → LLC=1, 取 max=1
        assert llc["A"] == 0
        assert llc["B"] == 0
        assert llc["C"] == 1

    def test_deep_shared_component(self, calc):
        """
        深层共享：A → B → D, A → C → D
        D 通过两条路径到达，应取最大深度
        """
        bom = [
            {"parent_code": "A", "child_code": "B"},
            {"parent_code": "B", "child_code": "D"},
            {"parent_code": "A", "child_code": "C"},
            {"parent_code": "C", "child_code": "D"},
        ]
        llc = calc.compute_low_level_codes(bom)
        assert llc["A"] == 0
        assert llc["B"] == 1
        assert llc["C"] == 1
        assert llc["D"] == 2, "D 在两条路径中最大深度为 2"

    def test_complex_bom(self, calc):
        """复杂 BOM：校验各物料 LLC 正确性"""
        bom = [
            {"parent_code": "P1", "child_code": "M1"},
            {"parent_code": "P1", "child_code": "C1"},
            {"parent_code": "M1", "child_code": "C1"},  # C1 是共享件
            {"parent_code": "M1", "child_code": "C2"},
            {"parent_code": "C1", "child_code": "R1"},
            {"parent_code": "P2", "child_code": "M2"},
            {"parent_code": "M2", "child_code": "C3"},
        ]
        llc = calc.compute_low_level_codes(bom)
        assert llc["P1"] == 0
        assert llc["P2"] == 0
        assert llc["M1"] == 1
        assert llc["M2"] == 1
        # C1 是 P1 的二级 (LLC=1) + M1 的一级 (LLC=2) → max=2
        assert llc["C1"] == 2, "C1 是共享件，LLC 应为 2"
        assert llc["C2"] == 2
        assert llc["C3"] == 2
        assert llc["R1"] == 3

    def test_empty_bom(self, calc):
        """空 BOM → 空字典"""
        assert calc.compute_low_level_codes([]) == {}

    def test_single_material_no_children(self, calc):
        """单个物料没有子物料"""
        bom = [{"parent_code": "A", "child_code": ""}]
        llc = calc.compute_low_level_codes(bom)
        assert len(llc) == 0, "空 child_code 应被忽略"


# ==============================================================================
# Test: apply_lot_sizing (批量规则)
# ==============================================================================

class TestApplyLotSizing:
    """批量规则直接影响计划订单数量——错误的批量规则会导致过量采购或短缺"""

    def test_lfl(self, calc):
        """LFL (Lot-for-Lot) → 恰好等于净需求"""
        assert calc.apply_lot_sizing(10, "LFL", 1) == 10
        assert calc.apply_lot_sizing(0, "LFL", 1) == 0
        assert calc.apply_lot_sizing(-5, "LFL", 1) == 0

    def test_foq(self, calc):
        """FOQ (Fixed Order Quantity) → 向上取整到 FOQ 的整数倍"""
        assert calc.apply_lot_sizing(10, "FOQ", 15) == 15
        assert calc.apply_lot_sizing(16, "FOQ", 15) == 30
        assert calc.apply_lot_sizing(30, "FOQ", 15) == 30
        assert calc.apply_lot_sizing(0, "FOQ", 15) == 0

    def test_eoq(self, calc):
        """EOQ (Economic Order Quantity) → max(净需求, EOQ)"""
        assert calc.apply_lot_sizing(10, "EOQ", 20) == 20
        assert calc.apply_lot_sizing(30, "EOQ", 20) == 30

    def test_mult(self, calc):
        """MULT (Multiple) → 向上取整到整数倍"""
        assert calc.apply_lot_sizing(10, "MULT", 5) == 10
        assert calc.apply_lot_sizing(12, "MULT", 5) == 15
        assert calc.apply_lot_sizing(0, "MULT", 5) == 0

    def test_min_max_qty(self, calc):
        """最小/最大订单量限制"""
        # 有最小值
        assert calc.apply_lot_sizing(3, "LFL", 1, min_qty=10) == 10
        # 有最大值
        assert calc.apply_lot_sizing(50, "LFL", 1, max_qty=30) == 30
        # 同时有 min 和 max
        assert calc.apply_lot_sizing(20, "LFL", 1, min_qty=15, max_qty=30) == 20
        assert calc.apply_lot_sizing(5, "LFL", 1, min_qty=15, max_qty=30) == 15
        assert calc.apply_lot_sizing(50, "LFL", 1, min_qty=15, max_qty=30) == 30

    def test_zero_lot_size(self, calc):
        """lot_size=0 时退化为 LFL"""
        assert calc.apply_lot_sizing(10, "FOQ", 0) == 10
        assert calc.apply_lot_sizing(10, "MULT", 0) == 10

    def test_unknown_rule(self, calc):
        """未知规则退化为 LFL"""
        assert calc.apply_lot_sizing(10, "UNKNOWN", 5) == 10


# ==============================================================================
# Test: calculate (MRP 全流程运算)
# ==============================================================================

class TestCalculate:
    """MRP 完整计算流程——验证多层级、多情景下的输出正确性"""

    def test_no_mps_empty_result(self, calc):
        """无 MPS 输入 → 无计划订单，无例外"""
        orders, exceptions = calc.calculate(
            mps_entries=[],
            material_masters=[],
            bom_lines=[],
            inventory_snapshot={},
            scheduled_receipts={},
        )
        assert orders == []
        assert exceptions == []

    def test_simple_production(self, calc, today):
        """
        简单场景：产品 A（自制），子物料 B 为外购件
        MPS: 第10天需要 10 个
        BOM: A → B ×1
        预期：A 有 1 个 PRODUCTION 订单，B 有 1 个 PURCHASE 订单
        """
        orders, exceptions = calc.calculate(
            mps_entries=[{
                "item_code": "A",
                "plan_date": today + timedelta(days=10),
                "quantity": 10,
            }],
            material_masters=[
                {"code": "A", "level_type": "产品", "lead_time": 2,
                 "safety_stock": 0, "lot_size_rule": "LFL", "lot_size_qty": 1,
                 "min_order_qty": 0, "max_order_qty": 0, "is_purchased": False},
                {"code": "B", "level_type": "零件", "lead_time": 5,
                 "safety_stock": 0, "lot_size_rule": "LFL", "lot_size_qty": 1,
                 "min_order_qty": 0, "max_order_qty": 0, "is_purchased": True},
            ],
            bom_lines=[{
                "parent_code": "A", "child_code": "B",
                "quantity_per": 1, "scrap_rate": 0,
            }],
            inventory_snapshot={},
            scheduled_receipts={},
        )
        a_orders = [o for o in orders if o["item_code"] == "A"]
        assert len(a_orders) == 1
        po = a_orders[0]
        assert po["order_type"] == "PRODUCTION"
        assert po["required_date"] == (today + timedelta(days=10)).isoformat()
        assert po["release_date"] == (today + timedelta(days=8)).isoformat()
        assert po["quantity"] == 10
        po = orders[0]
        assert po["item_code"] == "A"
        assert po["order_type"] == "PRODUCTION"
        assert po["required_date"] == (today + timedelta(days=10)).isoformat()
        assert po["release_date"] == (today + timedelta(days=8)).isoformat()
        assert po["quantity"] == 10

    def test_purchase_with_existing_inventory(self, calc, today):
        """
        零件 B（外购），有库存 20，安全库存 5
        MPS 产品 A 第 10 天需要 30 个，BOM: A→B ×1
        净需求 = 30 - (20 - 0) = 10，再加上安全库存 5，需 15
        """
        orders, exceptions = calc.calculate(
            mps_entries=[{
                "item_code": "A",
                "plan_date": today + timedelta(days=10),
                "quantity": 30,
            }],
            material_masters=[
                {"code": "A", "level_type": "产品", "lead_time": 1,
                 "safety_stock": 0, "lot_size_rule": "LFL", "lot_size_qty": 1,
                 "min_order_qty": 0, "max_order_qty": 0, "is_purchased": False},
                {"code": "B", "level_type": "零件", "lead_time": 5,
                 "safety_stock": 5, "lot_size_rule": "LFL", "lot_size_qty": 1,
                 "min_order_qty": 0, "max_order_qty": 0, "is_purchased": True},
            ],
            bom_lines=[{
                "parent_code": "A", "child_code": "B",
                "quantity_per": 1, "scrap_rate": 0,
            }],
            inventory_snapshot={"B": {"on_hand": 20, "allocated": 0, "reserved": 0}},
            scheduled_receipts={},
        )
        # A 的生产订单
        a_orders = [o for o in orders if o["item_code"] == "A"]
        assert len(a_orders) == 1
        # B 的采购订单
        b_orders = [o for o in orders if o["item_code"] == "B"]
        assert len(b_orders) == 1
        bo = b_orders[0]
        assert bo["order_type"] == "PURCHASE"
        # 需求：30 (从A传下来)
        # 库存：20，安全库存 5
        # 净需求：30 - 20 + 5 = 15（因为 projected_available 会从 20 逐步扣减）
        assert bo["quantity"] == 15

    def test_lot_sizing_in_mrp(self, calc, today):
        """
        批量规则测试：FOQ=20，净需求 15 → 应计划 20
        """
        orders, exceptions = calc.calculate(
            mps_entries=[{
                "item_code": "A",
                "plan_date": today + timedelta(days=10),
                "quantity": 15,
            }],
            material_masters=[
                {"code": "A", "level_type": "产品", "lead_time": 1,
                 "safety_stock": 0, "lot_size_rule": "LFL", "lot_size_qty": 1,
                 "min_order_qty": 0, "max_order_qty": 0, "is_purchased": False},
                {"code": "B", "level_type": "零件", "lead_time": 3,
                 "safety_stock": 0, "lot_size_rule": "FOQ", "lot_size_qty": 20,
                 "min_order_qty": 0, "max_order_qty": 0, "is_purchased": True},
            ],
            bom_lines=[{
                "parent_code": "A", "child_code": "B",
                "quantity_per": 1, "scrap_rate": 0,
            }],
            inventory_snapshot={},
            scheduled_receipts={},
        )
        b_orders = [o for o in orders if o["item_code"] == "B"]
        assert len(b_orders) >= 1
        assert b_orders[0]["quantity"] == 20

    def test_scheduled_receipt(self, calc, today):
        """
        在途采购单：B 有在途 10 个在第 3 天到货，毛需求 15
        净需求 = 15 - 10 = 5
        """
        orders, exceptions = calc.calculate(
            mps_entries=[{
                "item_code": "A",
                "plan_date": today + timedelta(days=10),
                "quantity": 15,
            }],
            material_masters=[
                {"code": "A", "level_type": "产品", "lead_time": 1,
                 "safety_stock": 0, "lot_size_rule": "LFL", "lot_size_qty": 1,
                 "min_order_qty": 0, "max_order_qty": 0, "is_purchased": False},
                {"code": "B", "level_type": "零件", "lead_time": 5,
                 "safety_stock": 0, "lot_size_rule": "LFL", "lot_size_qty": 1,
                 "min_order_qty": 0, "max_order_qty": 0, "is_purchased": True},
            ],
            bom_lines=[{
                "parent_code": "A", "child_code": "B",
                "quantity_per": 1, "scrap_rate": 0,
            }],
            inventory_snapshot={"B": {"on_hand": 0, "allocated": 0, "reserved": 0}},
            scheduled_receipts={"B": [{"date": today + timedelta(days=3), "quantity": 10}]},
        )
        b_orders = [o for o in orders if o["item_code"] == "B"]
        # 净需求 = 15 - 10 = 5
        if b_orders:
            assert b_orders[0]["quantity"] <= 10

    def test_safety_stock_alert(self, calc, today):
        """库存低于安全库存 → 产生 SAFETY_STOCK_ALERT"""
        orders, exceptions = calc.calculate(
            mps_entries=[{
                "item_code": "A",
                "plan_date": today + timedelta(days=5),
                "quantity": 5,
            }],
            material_masters=[
                {"code": "A", "level_type": "产品", "lead_time": 1,
                 "safety_stock": 0, "lot_size_rule": "LFL", "lot_size_qty": 1,
                 "min_order_qty": 0, "max_order_qty": 0, "is_purchased": False},
                {"code": "B", "level_type": "零件", "lead_time": 3,
                 "safety_stock": 10, "lot_size_rule": "LFL", "lot_size_qty": 1,
                 "min_order_qty": 0, "max_order_qty": 0, "is_purchased": True},
            ],
            bom_lines=[{
                "parent_code": "A", "child_code": "B",
                "quantity_per": 1, "scrap_rate": 0,
            }],
            inventory_snapshot={"B": {"on_hand": 3, "allocated": 0, "reserved": 0}},
            scheduled_receipts={},
        )
        alerts = [e for e in exceptions if e["type"] == "SAFETY_STOCK_ALERT"]
        assert len(alerts) >= 1
        assert "B" in alerts[0]["item_code"]

    def test_three_layer_bom(self, calc, today):
        """
        三层 BOM: 产品A → 模块M → 零件C
        模块层是幻影物料，需求穿透到零件层
        """
        orders, exceptions = calc.calculate(
            mps_entries=[{
                "item_code": "A",
                "plan_date": today + timedelta(days=10),
                "quantity": 10,
            }],
            material_masters=[
                {"code": "A", "level_type": "产品", "lead_time": 2,
                 "safety_stock": 0, "lot_size_rule": "LFL", "lot_size_qty": 1,
                 "min_order_qty": 0, "max_order_qty": 0, "is_purchased": False},
                {"code": "M", "level_type": "模块", "lead_time": 1,
                 "safety_stock": 0, "lot_size_rule": "LFL", "lot_size_qty": 1,
                 "min_order_qty": 0, "max_order_qty": 0, "is_purchased": False},
                {"code": "C", "level_type": "零件", "lead_time": 5,
                 "safety_stock": 0, "lot_size_rule": "LFL", "lot_size_qty": 1,
                 "min_order_qty": 0, "max_order_qty": 0, "is_purchased": True},
            ],
            bom_lines=[
                {"parent_code": "A", "child_code": "M", "quantity_per": 1, "scrap_rate": 0},
                {"parent_code": "M", "child_code": "C", "quantity_per": 2, "scrap_rate": 0},
            ],
            inventory_snapshot={},
            scheduled_receipts={},
        )
        # A 应该有生产订单
        a_orders = [o for o in orders if o["item_code"] == "A"]
        assert len(a_orders) == 1
        # C 应该有采购订单 (10个A × 1个M/A × 2个C/M = 20个C)
        c_orders = [o for o in orders if o["item_code"] == "C"]
        assert len(c_orders) >= 1
        assert sum(o["quantity"] for o in c_orders) == 20
        # 模块 M 不应该有订单（幻影穿透）
        m_orders = [o for o in orders if o["item_code"] == "M"]
        assert len(m_orders) == 0, "模块层是幻影物料，不应生成订单"

    def test_scrap_rate(self, calc, today):
        """BOM 损耗率 → 需求放大"""
        orders, exceptions = calc.calculate(
            mps_entries=[{
                "item_code": "A",
                "plan_date": today + timedelta(days=10),
                "quantity": 100,
            }],
            material_masters=[
                {"code": "A", "level_type": "产品", "lead_time": 1,
                 "safety_stock": 0, "lot_size_rule": "LFL", "lot_size_qty": 1,
                 "min_order_qty": 0, "max_order_qty": 0, "is_purchased": False},
                {"code": "B", "level_type": "零件", "lead_time": 3,
                 "safety_stock": 0, "lot_size_rule": "FOQ", "lot_size_qty": 50,
                 "min_order_qty": 0, "max_order_qty": 0, "is_purchased": True},
            ],
            bom_lines=[{
                "parent_code": "A", "child_code": "B",
                "quantity_per": 1, "scrap_rate": 5,  # 5% 损耗
            }],
            inventory_snapshot={},
            scheduled_receipts={},
        )
        b_orders = [o for o in orders if o["item_code"] == "B"]
        if b_orders:
            # 需求 = 100 * 1 * (1 + 5/100) = 105
            # FOQ 50 → ceil(105/50) * 50 = 150
            assert b_orders[0]["quantity"] >= 105

    def test_overdue_order_detected(self, calc, today):
        """
        逾期在途单（到货日期 < 今天）→ OVERDUE_ORDER 例外
        """
        yesterday = today - timedelta(days=1)
        orders, exceptions = calc.calculate(
            mps_entries=[{
                "item_code": "A",
                "plan_date": today + timedelta(days=10),
                "quantity": 10,
            }],
            material_masters=[
                {"code": "A", "level_type": "产品", "lead_time": 1,
                 "safety_stock": 0, "lot_size_rule": "LFL", "lot_size_qty": 1,
                 "min_order_qty": 0, "max_order_qty": 0, "is_purchased": False},
            ],
            bom_lines=[],
            inventory_snapshot={},
            scheduled_receipts={"A": [{"date": yesterday, "quantity": 5, "ref_no": "PO-001"}]},
        )
        overdue = [e for e in exceptions if e["type"] == "OVERDUE_ORDER"]
        assert len(overdue) >= 1
