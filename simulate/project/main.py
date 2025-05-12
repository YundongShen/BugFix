"""
main.py
"""
import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from backend.database.connection import DatabaseManager, DatabaseSettings
from backend.modules.tasks.api import router as tasks_router
from sqlalchemy import text
from uuid import uuid4
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Task Management API",
    version="1.0.0",
    description="Backend API for managing tasks in a to-do list application."
)

origins = [
    "http://localhost",
    "http://localhost:3000",  # Example frontend origin
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Retrieve database configuration from environment variables
mysql_host = os.getenv('mysql_host', 'localhost')
mysql_port = int(os.getenv('mysql_port', 3306))
mysql_database = os.getenv('mysql_database', 'default_db')
mysql_user = os.getenv('mysql_user', 'root')
mysql_password = os.getenv('mysql_password', '123456')

# Database connection URL
DATABASE_URL = f"mysql+asyncmy://{mysql_user}:{mysql_password}@{mysql_host}:{mysql_port}/{mysql_database}"

db_settings = DatabaseSettings()
db_manager = DatabaseManager(settings=db_settings)

@app.on_event("startup")
async def startup_event():
    """Initialize database and ensure tables exist."""
    logger.info("Starting up the application...")
    try:
        await db_manager.initialize_database(drop_existing=False)
        logger.info("Database initialized successfully.")
        
        # Ensure the 'tasks' table exists and contains the 'description' column
        async with db_manager.engine.begin() as conn:
            result = await conn.execute(text("SHOW COLUMNS FROM tasks LIKE 'description';"))
            if not result.fetchone():
                logger.error("The 'description' column is missing in the 'tasks' table. Fixing schema...")
                await conn.execute(text("ALTER TABLE tasks ADD COLUMN description VARCHAR(255) NOT NULL;"))
                logger.info("'description' column added to the 'tasks' table.")
    except ConnectionError as e:
        trace_id = str(uuid4())
        logger.error(f"Failed to initialize database: {e}. Trace ID: {trace_id}")
        raise RuntimeError("Database initialization failed.") from e

@app.on_event("shutdown")
async def shutdown_event():
    """Gracefully close database connections."""
    logger.info("Shutting down the application...")
    await db_manager.engine.dispose()

app.include_router(tasks_router, prefix="/api")

@app.get("/health", tags=["Health Check"])
async def health_check():
    """Check the health of the application and database."""
    db_healthy = await db_manager.health_check()
    if not db_healthy:
        trace_id = str(uuid4())
        logger.error(f"Database health check failed. Trace ID: {trace_id}")
        return {"status": "error", "message": "Database connection failed."}
    return {"status": "ok", "message": "Application is healthy."}