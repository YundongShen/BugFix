import os
import logging
from contextlib import asynccontextmanager
from typing import AsyncIterator, Optional, Type
from uuid import uuid4
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import text
from fastapi import HTTPException
from pydantic_settings import BaseSettings, SettingsConfigDict
from urllib.parse import quote_plus 

class DatabaseSettings(BaseSettings):
    mysql_host: str = os.getenv('mysql_host', 'localhost')
    mysql_port: int = int(os.getenv('mysql_port', '3306'))
    mysql_database: str = os.getenv('mysql_database', 'default_db')
    mysql_user: str = os.getenv('mysql_user', 'root')
    mysql_password: str = os.getenv('mysql_password', '123456')

    DB_POOL_SIZE: int = int(os.getenv('DB_POOL_SIZE', '5'))
    DB_MAX_OVERFLOW: int = int(os.getenv('DB_MAX_OVERFLOW', '10'))
    DB_POOL_RECYCLE: int = int(os.getenv('DB_POOL_RECYCLE', '3600'))
    DB_DEBUG: bool = os.getenv('DB_DEBUG', 'False').lower() == 'true'

    @property
    def DB_URL(self) -> str:
        escaped_user = quote_plus(self.mysql_user)
        escaped_password = quote_plus(self.mysql_password)
        escaped_host = quote_plus(self.mysql_host)
        escaped_database = quote_plus(self.mysql_database)
        return (
            f"mysql+asyncmy://{escaped_user}:{escaped_password}"
            f"@{escaped_host}:{self.mysql_port}/{escaped_database}"
            f"?charset=utf8mb4"
        )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


class DatabaseManager:
    _instance = None
    Base = declarative_base()

    def __new__(cls, settings: Optional[DatabaseSettings] = None):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._settings = settings or DatabaseSettings()
            try:
                cls._engine = create_async_engine(
                    cls._settings.DB_URL,
                    pool_pre_ping=True,
                    pool_size=cls._settings.DB_POOL_SIZE,
                    max_overflow=cls._settings.DB_MAX_OVERFLOW,
                    pool_recycle=cls._settings.DB_POOL_RECYCLE,
                    echo=cls._settings.DB_DEBUG,
                    connect_args={
                        "connect_timeout": 10,
                        "charset": "utf8mb4",
                    }
                )
                cls._session_factory = async_sessionmaker(
                    bind=cls._engine,
                    class_=AsyncSession,
                    expire_on_commit=False,
                    autoflush=False
                )
            except Exception as e:
                trace_id = str(uuid4())
                logging.error(f"数据库引擎初始化失败. Trace ID: {trace_id}")
                raise HTTPException(status_code=500, detail=f"数据库初始化失败. Trace ID: {trace_id}") from e
        return cls._instance

    @property
    def engine(self):
        return self._engine

    @asynccontextmanager
    async def session(self) -> AsyncIterator[AsyncSession]:
        async with self._session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception as e:
                await session.rollback()
                trace_id = str(uuid4())
                logging.error(f"数据库事务失败: {e}. Trace ID: {trace_id}")
                raise HTTPException(status_code=500, detail=f"数据库事务失败. Trace ID: {trace_id}") from e

    async def health_check(self) -> bool:
        try:
            async with self.engine.connect() as conn:
                result = await conn.execute(text("SELECT 1"))
                return result.scalar() == 1
        except Exception as e:
            trace_id = str(uuid4())
            logging.error(f"数据库健康检查失败: {e}. Trace ID: {trace_id}")
            return False

    async def initialize_database(self, drop_existing: bool = True):
        if not await self.health_check():
            raise ConnectionError("数据库连接失败，无法初始化")

        async with self.engine.begin() as conn:
            if drop_existing:
                logging.warning("开发模式：删除已有数据库表...")
                await conn.run_sync(self.Base.metadata.drop_all)

            logging.info("正在创建数据库表...")
            await conn.run_sync(self.Base.metadata.create_all)

            logging.info("数据库初始化完成")

    