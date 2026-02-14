from sqlalchemy import create_engine, text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.pool import NullPool
import os
import ssl
from contextlib import asynccontextmanager

Base = declarative_base()

# Get MySQL connection details from environment
MYSQL_HOST = os.getenv('MYSQL_HOST', '127.0.0.1')
MYSQL_PORT = os.getenv('MYSQL_PORT', '3306')
MYSQL_USER = os.getenv('MYSQL_USER', 'root')
MYSQL_PASSWORD = os.getenv('MYSQL_PASSWORD', 'root')
MYSQL_DATABASE = os.getenv('MYSQL_DATABASE', 'fixed_income_db')
ENVIRONMENT = os.getenv('ENVIRONMENT', 'development')

# Create SSL context for Aiven
ssl_context = None
if ENVIRONMENT == 'production' or ENVIRONMENT == 'development':
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE

# Connection arguments
connect_args = {}
if ssl_context:
    connect_args = {'ssl': ssl_context}

# Async database URL for aiomysql
DATABASE_URL = f"mysql+aiomysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DATABASE}?charset=utf8mb4"

# Sync database URL for initial setup
SYNC_DATABASE_URL = f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DATABASE}?charset=utf8mb4"

# Create async engine with SSL
async_engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    pool_pre_ping=True,
    poolclass=NullPool,
    connect_args=connect_args
)

# Create async session factory
AsyncSessionLocal = async_sessionmaker(
    async_engine,
    class_=AsyncSession,
    expire_on_commit=False
)

# Dependency for getting DB session
async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

# Function to initialize database
def init_db():
    """Create all tables using sync engine"""
    try:
        # Create sync engine with SSL
        sync_engine = create_engine(
            SYNC_DATABASE_URL,
            connect_args=connect_args,
            pool_pre_ping=True
        )
        
        # Create tables
        Base.metadata.create_all(bind=sync_engine)
        sync_engine.dispose()
        print(f"✅ Database initialized: {MYSQL_DATABASE}")
    except Exception as e:
        print(f"⚠️ Database initialization warning: {e}")

# Initialize database on startup
try:
    init_db()
except Exception as e:
    print(f"⚠️ Could not initialize database: {e}")
