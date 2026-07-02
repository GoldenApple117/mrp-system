import os;os.environ['DB_BACKEND']='sqlite'
from app.core.database import init_db, engine
from sqlalchemy import text
init_db()
with engine.connect() as conn:
    for col, typ in [
        ('unit_price','FLOAT DEFAULT 0'),('total_amount','FLOAT DEFAULT 0'),('paid_amount','FLOAT DEFAULT 0'),
        ('ship_status','VARCHAR(20) DEFAULT "待出货"'),('pay_status','VARCHAR(20) DEFAULT "未收款"')
    ]:
        try:
            conn.execute(text(f'ALTER TABLE sales_order ADD COLUMN {col} {typ}'))
            conn.commit()
            print(f'Added {col}')
        except Exception as e:
            print(f'{col}: {e}')
    try:
        conn.execute(text("UPDATE sales_order SET ship_status=status WHERE ship_status IS NULL OR ship_status=''"))
        conn.execute(text("UPDATE sales_order SET pay_status='未收款' WHERE pay_status IS NULL OR pay_status=''"))
        conn.commit()
        print('Migrated existing orders')
    except Exception as e:
        print(f'Migration: {e}')
