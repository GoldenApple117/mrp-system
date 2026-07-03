"""数据库连接与会话管理"""
from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import sessionmaker, declarative_base
from app.core.config import DATABASE_URL, DB_BACKEND

engine_kwargs = {
    "echo": False,
    "pool_size": 20,
    "max_overflow": 20,
    "pool_recycle": 1800,
    "pool_pre_ping": True,
    "pool_timeout": 10,
}

if "sqlite" in DATABASE_URL:
    engine_kwargs["connect_args"] = {"check_same_thread": False}

engine = create_engine(DATABASE_URL, **engine_kwargs)

if "sqlite" in DATABASE_URL:
    @event.listens_for(engine, "connect")
    def _set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.close()

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    """FastAPI 依赖注入：获取数据库会话"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """初始化数据库表（含迁移：新增列自动补齐）"""
    Base.metadata.create_all(bind=engine)

    # 迁移：补齐新增的列（不破坏已有数据）
    # 每条 ALTER TABLE 单独 try/except，避免一条失败阻塞后续
    with engine.connect() as conn:
        migration_stmts = [
            # v1.3 — 物料层级
            "ALTER TABLE material_master ADD COLUMN classification_code VARCHAR(100) DEFAULT ''",
            "ALTER TABLE material_master ADD COLUMN level_type VARCHAR(20) DEFAULT '零件'",
            # v1.5 — 物料参考价格/提交人/链接
            "ALTER TABLE material_master ADD COLUMN reference_unit_price FLOAT DEFAULT 0",
            "ALTER TABLE material_master ADD COLUMN reference_submitter VARCHAR(50) DEFAULT ''",
            "ALTER TABLE material_master ADD COLUMN reference_link VARCHAR(1000) DEFAULT ''",
            # v1.5 — 采购单品牌/提交人/链接
            "ALTER TABLE purchase_order ADD COLUMN brand VARCHAR(100) DEFAULT ''",
            "ALTER TABLE purchase_order ADD COLUMN submitter VARCHAR(50) DEFAULT ''",
            "ALTER TABLE purchase_order ADD COLUMN supplier_link VARCHAR(1000) DEFAULT ''",
            # v1.5 — 销售订单出货/收款状态
            "ALTER TABLE sales_order ADD COLUMN shipped_qty FLOAT DEFAULT 0",
            "ALTER TABLE sales_order ADD COLUMN unit_price FLOAT DEFAULT 0",
            "ALTER TABLE sales_order ADD COLUMN total_amount FLOAT DEFAULT 0",
            "ALTER TABLE sales_order ADD COLUMN paid_amount FLOAT DEFAULT 0",
            "ALTER TABLE sales_order ADD COLUMN ship_status VARCHAR(20) DEFAULT '待出货'",
            "ALTER TABLE sales_order ADD COLUMN pay_status VARCHAR(20) DEFAULT '未收款'",
            # v1.5 — MPS 状态
            "ALTER TABLE mps_entry ADD COLUMN status VARCHAR(20) DEFAULT '进行中'",
            # v1.5 — 供应商购买链接
            "ALTER TABLE supplier ADD COLUMN purchase_link VARCHAR(1000) DEFAULT ''",
            # v1.7 — 权限系统
            "ALTER TABLE users ADD COLUMN is_approved INTEGER DEFAULT 1",
        ]
        for stmt in migration_stmts:
            try:
                conn.execute(text(stmt))
                conn.commit()
            except Exception:
                conn.rollback()  # 列已存在时忽略

        # v1.7 — 确保admin用户被标记为已授权
        conn.execute(text("UPDATE users SET is_approved=1, role='admin' WHERE username='admin'"))
        conn.commit()

        # v1.6 — 创建默认管理员用户（含 is_approved）
        from app.core.security import hash_password
        result = conn.execute(text("SELECT id FROM users WHERE username='admin'"))
        if not result.fetchone():
            conn.execute(text(
                "INSERT INTO users (username, password_hash, role, is_approved) "
                "VALUES ('admin', :pw, 'admin', 1)"
            ), {"pw": hash_password("admin123")})
            conn.commit()

        # v1.7 — 创建默认普通用户 user1（未授权，需申请权限）
        result2 = conn.execute(text("SELECT id FROM users WHERE username='user1'"))
        if not result2.fetchone():
            conn.execute(text(
                "INSERT INTO users (username, password_hash, role, is_approved) "
                "VALUES ('user1', :pw, 'normal', 0)"
            ), {"pw": hash_password("123456")})
            conn.commit()

