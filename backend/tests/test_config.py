"""
配置模块单元测试
---------------
测试范围：Settings 配置类的属性和默认值
"""
import sys
import os
import pytest
import tempfile
import shutil

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


class TestSettingsDefaults:
    """测试 Settings 默认值"""

    def test_default_app_name(self):
        """测试：默认应用名称"""
        from app.core.config import Settings
        settings = Settings()
        assert settings.app_name == "LangChainRAG"

    def test_default_app_version(self):
        """测试：默认版本号"""
        from app.core.config import Settings
        settings = Settings()
        assert settings.app_version == "1.0.0"

    def test_default_debug_true(self):
        """测试：默认开启debug模式"""
        from app.core.config import Settings
        settings = Settings()
        assert settings.debug is True

    def test_default_database_url(self):
        """测试：默认数据库URL"""
        from app.core.config import Settings
        settings = Settings()
        assert "sqlite" in settings.database_url
        assert "aiosqlite" in settings.database_url

    def test_default_secret_key_is_dev(self):
        """测试：默认密钥是开发环境密钥"""
        from app.core.config import Settings
        settings = Settings()
        assert "dev-secret-key" in settings.secret_key

    def test_default_token_expire_minutes(self):
        """测试：默认Token有效期为7天"""
        from app.core.config import Settings
        settings = Settings()
        assert settings.access_token_expire_minutes == 60 * 24 * 7

    def test_default_backend_port(self):
        """测试：默认后端端口"""
        from app.core.config import Settings
        settings = Settings()
        assert settings.backend_port == 8000

    def test_default_frontend_port(self):
        """测试：默认前端端口"""
        from app.core.config import Settings
        settings = Settings()
        assert settings.frontend_port == 5173

    def test_default_max_upload_size(self):
        """测试：默认最大上传大小为50MB"""
        from app.core.config import Settings
        settings = Settings()
        assert settings.max_upload_size == 50 * 1024 * 1024

    def test_default_allowed_file_types(self):
        """测试：默认允许的文件类型"""
        from app.core.config import Settings
        settings = Settings()
        assert "pdf" in settings.allowed_file_types
        assert "txt" in settings.allowed_file_types
        assert "csv" in settings.allowed_file_types
        assert "docx" in settings.allowed_file_types
        assert "md" in settings.allowed_file_types

    def test_dashscope_api_key_has_default(self):
        """测试：API Key有默认值（占位符）"""
        from app.core.config import Settings
        settings = Settings()
        assert isinstance(settings.dashscope_api_key, str)
        assert len(settings.dashscope_api_key) > 0


class TestSettingsProperties:
    """测试 Settings 的计算属性"""

    def test_base_dir_is_path(self):
        """测试：base_dir 返回 Path 对象"""
        from app.core.config import Settings
        from pathlib import Path
        settings = Settings()
        assert isinstance(settings.base_dir, Path)

    def test_base_dir_exists(self):
        """测试：base_dir 指向一个存在的目录"""
        from app.core.config import Settings
        settings = Settings()
        # base_dir 由 Path(__file__).parent.parent.parent 计算得出
        # 它应该指向 backend 目录（一个存在的路径）
        assert settings.base_dir.exists(), "base_dir 应该指向一个存在的目录"
        assert settings.base_dir.is_dir(), "base_dir 应该是一个目录"

    def test_upload_dir_created(self):
        """测试：upload_dir 属性会创建目录"""
        from app.core.config import Settings
        import tempfile
        import shutil

        # 使用上下文临时覆盖 base_dir 太复杂，只验证类型
        settings = Settings()
        assert settings.upload_dir is not None
        assert settings.upload_dir.exists(), "uploads目录应该被自动创建"

    def test_chroma_dir_created(self):
        """测试：chroma_dir 属性会创建目录"""
        from app.core.config import Settings
        settings = Settings()
        assert settings.chroma_dir is not None
        assert settings.chroma_dir.exists(), "chroma_data目录应该被自动创建"

    def test_model_config_has_env_file(self):
        """测试：model_config 配置了 .env 文件读取"""
        from app.core.config import Settings
        config = Settings.model_config
        assert "env_file" in config, "应配置了env_file"
        assert config["env_file"] == ".env"


class TestGlobalSettings:
    """测试全局 settings 实例"""

    def test_global_settings_is_singleton(self):
        """测试：全局settings实例可以访问"""
        from app.core.config import settings
        assert settings is not None
        assert settings.app_name == "LangChainRAG"
