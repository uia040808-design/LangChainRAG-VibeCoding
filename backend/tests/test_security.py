"""
安全模块单元测试
---------------
测试范围：密码加密/验证、JWT令牌创建/解析
"""
import sys
import os
import pytest

# 确保 backend 目录在 sys.path 中
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.core.security import hash_password, verify_password, create_access_token, decode_access_token


class TestPasswordHashing:
    """测试 bcrypt 密码加密和验证"""

    def test_hash_password_returns_string(self):
        """测试：加密后返回字符串，且不同于原始密码"""
        hashed = hash_password("123456")
        assert isinstance(hashed, str), "应该返回字符串"
        assert hashed != "123456", "加密后不应等于原始密码"

    def test_hash_password_starts_with_bcrypt_prefix(self):
        """测试：bcrypt 哈希值以 $2b$ 或 $2a$ 开头"""
        hashed = hash_password("mypassword")
        assert hashed.startswith("$2"), f"bcrypt 哈希应该以 $2 开头，实际: {hashed[:10]}"

    def test_same_password_generates_different_hash(self):
        """测试：相同密码两次加密结果不同（因为盐值随机）"""
        h1 = hash_password("same_password")
        h2 = hash_password("same_password")
        assert h1 != h2, "两次加密结果应该不同（因为随机盐值）"

    def test_verify_correct_password(self):
        """测试：正确密码验证通过"""
        hashed = hash_password("correct_password")
        assert verify_password("correct_password", hashed) is True

    def test_verify_wrong_password(self):
        """测试：错误密码验证不通过"""
        hashed = hash_password("correct_password")
        assert verify_password("wrong_password", hashed) is False

    def test_verify_empty_password(self):
        """测试：空密码验证不通过（除非原始密码也是空）"""
        hashed = hash_password("real_password")
        assert verify_password("", hashed) is False

    def test_hash_long_password_truncated(self):
        """测试：超过72字节的密码会被截断"""
        long_password = "a" * 100  # 超过72字节限制
        hashed = hash_password(long_password)
        # 截断后依然能验证前72字节
        assert verify_password("a" * 72, hashed) is True

    def test_special_characters_password(self):
        """测试：包含特殊字符的密码"""
        special = "密码!@#$%^&*()_+-=[]{}|;':\",./<>?"
        hashed = hash_password(special)
        assert verify_password(special, hashed) is True


class TestJWTToken:
    """测试 JWT 令牌的创建和解析"""

    def test_create_token_returns_string(self):
        """测试：create_access_token 返回字符串"""
        token = create_access_token(data={"sub": "user123"})
        assert isinstance(token, str), "JWT token 应该是一个字符串"
        assert len(token) > 20, "JWT token 应该足够长"

    def test_create_token_contains_three_parts(self):
        """测试：JWT 由3部分组成（header.payload.signature）"""
        token = create_access_token(data={"sub": "user123"})
        parts = token.split(".")
        assert len(parts) == 3, f"JWT 应该有3个部分，实际有 {len(parts)} 个"

    def test_decode_valid_token(self):
        """测试：有效token可以正确解码"""
        token = create_access_token(data={"sub": "user123"})
        payload = decode_access_token(token)
        assert payload is not None, "有效token解码不应返回None"
        assert payload["sub"] == "user123", "解码后的sub应与原始数据一致"

    def test_decode_returns_dict(self):
        """测试：解码后返回字典"""
        token = create_access_token(data={"sub": "user_abc", "role": "admin"})
        payload = decode_access_token(token)
        assert isinstance(payload, dict), "解码结果应为字典"
        assert "sub" in payload, "应包含 sub 字段"
        assert "exp" in payload, "应包含过期时间 exp 字段"

    def test_decode_invalid_token_returns_none(self):
        """测试：无效token解码返回None"""
        result = decode_access_token("this_is_not_a_valid_jwt_token")
        assert result is None, "无效token应该返回None"

    def test_decode_empty_token_returns_none(self):
        """测试：空token解码返回None"""
        result = decode_access_token("")
        assert result is None, "空token应该返回None"

    def test_decode_tampered_token_returns_none(self):
        """测试：被篡改的token解码返回None"""
        token = create_access_token(data={"sub": "user123"})
        # 修改token中间部分
        parts = token.split(".")
        tampered = parts[0] + "." + "tampered" + "." + parts[2]
        result = decode_access_token(tampered)
        assert result is None, "被篡改的token应该返回None"

    def test_create_token_with_custom_expiry(self):
        """测试：自定义过期时间"""
        from datetime import timedelta
        # 过期时间为1秒
        token = create_access_token(
            data={"sub": "user123"},
            expires_delta=timedelta(seconds=1)
        )
        # 立即解码应该成功
        payload = decode_access_token(token)
        assert payload is not None, "刚创建的token应该有效"

    def test_create_token_without_data(self):
        """测试：空data也能创建token"""
        token = create_access_token(data={})
        payload = decode_access_token(token)
        assert payload is not None, "空data的token应该有效"
        assert "exp" in payload, "至少应包含过期时间"
