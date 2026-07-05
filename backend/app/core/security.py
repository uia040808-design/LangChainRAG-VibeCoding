"""
安全模块 - JWT令牌和密码加密
-------------------------------
JWT (JSON Web Token)：用户登录后服务端签发的"电子票"，
之后每次请求带上这个票，服务端就知道是谁在操作，无需重复登录。

密码使用 bcrypt 加密，这是一种单向加密（只能加密不能解密），
即使数据库泄露，黑客也无法知道用户的原始密码。
"""
from datetime import datetime, timedelta, timezone
from typing import Optional
from jose import JWTError, jwt
import bcrypt

from app.core.config import settings

# ========== 密码加密 ==========


def hash_password(password: str) -> str:
    """
    将明文密码加密为哈希值
    解释：加密后的结果是一串乱码，无法逆向还原，但可以验证
    """
    # bcrypt 要求密码不超过72字节
    password_bytes = password.encode("utf-8")[:72]
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    验证密码是否正确
    解释：将用户输入的密码用同样算法加密后，与数据库中存储的哈希值比对
    """
    password_bytes = plain_password.encode("utf-8")[:72]
    hashed_bytes = hashed_password.encode("utf-8")
    return bcrypt.checkpw(password_bytes, hashed_bytes)


# ========== JWT令牌 ==========

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    创建JWT访问令牌
    参数：
        data: 要存储在令牌中的数据，通常包含 {"sub": user_id}
        expires_delta: 有效期，如果不指定则使用配置的默认值
    返回：加密后的JWT字符串
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=settings.access_token_expire_minutes
        )
    # 在令牌中设置过期时间
    to_encode.update({"exp": expire})
    # 用密钥签名生成JWT字符串
    encoded_jwt = jwt.encode(
        to_encode, settings.secret_key, algorithm="HS256"
    )
    return encoded_jwt


def decode_access_token(token: str) -> Optional[dict]:
    """
    解密并验证JWT令牌
    参数：token - JWT字符串
    返回：令牌中的数据字典，如果令牌无效或过期则返回None
    """
    try:
        payload = jwt.decode(
            token, settings.secret_key, algorithms=["HS256"]
        )
        return payload
    except JWTError:
        # 令牌过期、伪造、或签名不匹配都会触发JWTError
        return None
