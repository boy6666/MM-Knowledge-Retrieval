"""
数据库连接管理
统一管理SQLAlchemy引擎、会话、Base类
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from config import settings

engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False},
    echo=False,
)

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
    """初始化所有表结构"""
    from models.user import User
    from models.knowledge import Knowledge
    from models.task import Guidance, CommunityPost
    Base.metadata.create_all(bind=engine)
