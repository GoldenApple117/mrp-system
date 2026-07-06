"""extend mrp_run_record text fields to LONGTEXT

Revision ID: a6a25d3c9b2f
Revises: b440565041fb
Create Date: 2026-07-06 14:55:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.mysql import LONGTEXT

# revision identifiers, used by Alembic.
revision: str = "a6a25d3c9b2f"
down_revision: Union[str, None] = "b440565041fb"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 将 planned_orders_json 和 summary_json 改为 LONGTEXT
    # 生产环境 MRP 结果 (526 个计划订单) 的 JSON 长度约 135KB，超出 TEXT(65KB) 限制
    op.alter_column("mrp_run_record", "planned_orders_json",
        existing_type=sa.Text(),
        type_=LONGTEXT,
        existing_comment="计划订单列表(JSON)",
        existing_nullable=True,
    )
    op.alter_column("mrp_run_record", "summary_json",
        existing_type=sa.Text(),
        type_=LONGTEXT,
        existing_comment="运算摘要(JSON)",
        existing_nullable=True,
    )


def downgrade() -> None:
    # 回退到 TEXT
    op.alter_column("mrp_run_record", "planned_orders_json",
        existing_type=LONGTEXT,
        type_=sa.Text(),
        existing_comment="计划订单列表(JSON)",
        existing_nullable=True,
    )
    op.alter_column("mrp_run_record", "summary_json",
        existing_type=LONGTEXT,
        type_=sa.Text(),
        existing_comment="运算摘要(JSON)",
        existing_nullable=True,
    )
