"""
应用配置管理
-----------
使用 pydantic-settings 从 .env 文件和环境变量中读取配置。
所有配置项集中管理，方便修改。
"""
from pydantic_settings import BaseSettings
from pathlib import Path


class Settings(BaseSettings):
    """应用配置类"""
    # --- 阿里云百炼 API ---
    # 解释：DashScope是阿里云百炼的API品牌名，兼容OpenAI接口格式
    dashscope_api_key: str = "sk-your-api-key-here"
    # 解释：API地址。工作空间Key（sk-ws-开头）必须用工作空间专属地址，
    #       地址在阿里云百炼控制台 → 模型调用 → SDK示例中可以看到
    dashscope_base_url: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"

    # --- 应用基础信息 ---
    app_name: str = "LangChainRAG"
    app_version: str = "1.0.0"
    debug: bool = True

    # --- 数据库 ---
    # 解释：SQLite文件路径，aiosqlite是异步驱动，sqlite+aiosqlite是SQLAlchemy的连接协议
    database_url: str = "sqlite+aiosqlite:///./app.db"

    # --- JWT认证 ---
    # 解释：SECRET_KEY是JWT签名的密钥，密钥越复杂JWT越安全
    secret_key: str = "dev-secret-key-change-in-production"
    # 解释：Token有效期，单位分钟，默认7天
    access_token_expire_minutes: int = 60 * 24 * 7

    # --- 服务端口 ---
    backend_port: int = 8000
    frontend_port: int = 5173

    # --- 文件上传 ---
    # 解释：上传文件最大大小，50MB
    max_upload_size: int = 50 * 1024 * 1024
    # 解释：允许上传的文件类型
    allowed_file_types: list[str] = ["pdf", "txt", "csv", "docx", "md"]

    # --- 项目路径 ---
    # 解释：BASE_DIR是backend文件夹的绝对路径，所有其他路径基于此计算
    @property
    def base_dir(self) -> Path:
        return Path(__file__).parent.parent.parent

    @property
    def upload_dir(self) -> Path:
        path = self.base_dir / "uploads"
        path.mkdir(exist_ok=True)
        return path

    @property
    def chroma_dir(self) -> Path:
        path = self.base_dir / "chroma_data"
        path.mkdir(exist_ok=True)
        return path

    # 解释：model_config告诉pydantic从.env文件读取配置
    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


# 创建全局配置实例，其他模块通过 import settings 来使用
settings = Settings()
