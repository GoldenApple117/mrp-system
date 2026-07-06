"""JWT token 签发/验证 + 密码哈希"""
import os
from datetime import datetime, timedelta, timezone
from jose import JWTError, jwt
from passlib.context import CryptContext

# JWT 密钥：优先从环境变量读取；本地开发用固定 dev 密钥（保证重启不踢人）
import logging
logger = logging.getLogger(__name__)
_DEV_SECRET = "mrp-system-dev-secret-key-do-not-use-in-production"
SECRET_KEY = os.getenv("JWT_SECRET_KEY", _DEV_SECRET)
if SECRET_KEY == _DEV_SECRET:
    logger.warning("⚠️ JWT_SECRET_KEY 未设置，使用开发密钥。生产环境务必通过环境变量设置。")
ALGORITHM = "HS256"
TOKEN_EXPIRE_HOURS = 24

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(hours=TOKEN_EXPIRE_HOURS)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def verify_access_token(token: str) -> dict | None:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None
