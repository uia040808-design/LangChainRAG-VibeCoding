"""
数据模型/Schema 单元测试
-----------------------
测试范围：Pydantic 请求/响应模型的验证逻辑
"""
import sys
import os
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


class TestRegisterRequest:
    """测试注册请求验证"""

    def test_valid_register_data(self):
        """测试：有效的注册数据"""
        from app.schemas.auth import RegisterRequest
        req = RegisterRequest(username="testuser", password="123456", email="test@test.com")
        assert req.username == "testuser"
        assert req.password == "123456"
        assert req.email == "test@test.com"

    def test_username_too_short(self):
        """测试：用户名少于2个字符"""
        from app.schemas.auth import RegisterRequest
        from pydantic import ValidationError
        with pytest.raises(ValidationError):
            RegisterRequest(username="a", password="123456")

    def test_username_too_long(self):
        """测试：用户名超过50个字符"""
        from app.schemas.auth import RegisterRequest
        from pydantic import ValidationError
        with pytest.raises(ValidationError):
            RegisterRequest(username="a" * 51, password="123456")

    def test_password_too_short(self):
        """测试：密码少于6个字符"""
        from app.schemas.auth import RegisterRequest
        from pydantic import ValidationError
        with pytest.raises(ValidationError):
            RegisterRequest(username="validuser", password="12345")

    def test_email_default_empty(self):
        """测试：邮箱默认为空字符串"""
        from app.schemas.auth import RegisterRequest
        req = RegisterRequest(username="user", password="123456")
        assert req.email == ""

    def test_chinese_username(self):
        """测试：支持中文用户名"""
        from app.schemas.auth import RegisterRequest
        req = RegisterRequest(username="张三", password="123456")
        assert req.username == "张三"


class TestLoginRequest:
    """测试登录请求验证"""

    def test_valid_login_data(self):
        """测试：有效的登录数据"""
        from app.schemas.auth import LoginRequest
        req = LoginRequest(username="admin", password="123456")
        assert req.username == "admin"
        assert req.password == "123456"

    def test_missing_username(self):
        """测试：缺少用户名"""
        from app.schemas.auth import LoginRequest
        from pydantic import ValidationError
        with pytest.raises(ValidationError):
            LoginRequest(password="123456")

    def test_missing_password(self):
        """测试：缺少密码"""
        from app.schemas.auth import LoginRequest
        from pydantic import ValidationError
        with pytest.raises(ValidationError):
            LoginRequest(username="admin")


class TestChangePasswordRequest:
    """测试修改密码请求验证"""

    def test_valid_change_password(self):
        """测试：有效的修改密码请求"""
        from app.schemas.auth import ChangePasswordRequest
        req = ChangePasswordRequest(old_password="old123", new_password="new456")
        assert req.old_password == "old123"
        assert req.new_password == "new456"

    def test_new_password_too_short(self):
        """测试：新密码少于6个字符"""
        from app.schemas.auth import ChangePasswordRequest
        from pydantic import ValidationError
        with pytest.raises(ValidationError):
            ChangePasswordRequest(old_password="old123", new_password="12345")


class TestChatRequest:
    """测试聊天请求验证"""

    def test_valid_chat_message(self):
        """测试：有效的聊天消息"""
        from app.schemas.chat import ChatRequest
        req = ChatRequest(message="你好，请介绍一下这款手机")
        assert req.message == "你好，请介绍一下这款手机"

    def test_empty_message(self):
        """测试：空消息被拒绝"""
        from app.schemas.chat import ChatRequest
        from pydantic import ValidationError
        with pytest.raises(ValidationError):
            ChatRequest(message="")


class TestFeedbackRequest:
    """测试反馈请求验证"""

    def test_like_feedback(self):
        """测试：点赞反馈"""
        from app.schemas.chat import FeedbackRequest
        req = FeedbackRequest(feedback="like")
        assert req.feedback == "like"

    def test_dislike_feedback(self):
        """测试：点踩反馈"""
        from app.schemas.chat import FeedbackRequest
        req = FeedbackRequest(feedback="dislike")
        assert req.feedback == "dislike"


class TestRenameSessionRequest:
    """测试重命名会话请求验证"""

    def test_valid_rename(self):
        """测试：有效的重命名"""
        from app.schemas.chat import RenameSessionRequest
        req = RenameSessionRequest(title="手机相关咨询")
        assert req.title == "手机相关咨询"

    def test_empty_title(self):
        """测试：空标题被拒绝"""
        from app.schemas.chat import RenameSessionRequest
        from pydantic import ValidationError
        with pytest.raises(ValidationError):
            RenameSessionRequest(title="")

    def test_title_too_long(self):
        """测试：标题超过200字符"""
        from app.schemas.chat import RenameSessionRequest
        from pydantic import ValidationError
        with pytest.raises(ValidationError):
            RenameSessionRequest(title="a" * 201)


class TestSourceInfoSchema:
    """测试来源信息模型"""

    def test_valid_source_info(self):
        """测试：有效的来源信息"""
        from app.schemas.chat import SourceInfo
        source = SourceInfo(
            document_title="手机参数.pdf",
            chunk_id="chunk_00001",
            content="电池容量5000mAh",
            similarity_score=0.92
        )
        assert source.document_title == "手机参数.pdf"
        assert source.similarity_score == 0.92

    def test_default_values(self):
        """测试：默认值"""
        from app.schemas.chat import SourceInfo
        source = SourceInfo(
            document_title="test.pdf",
            content="test content",
        )
        assert source.chunk_id == ""
        assert source.similarity_score == 0.0
