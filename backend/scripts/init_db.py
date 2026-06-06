"""
Database migration helper.

Usage (from backend/ directory):
    python scripts/init_db.py

This creates all tables via SQLAlchemy metadata.
For production use Alembic migrations instead.
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.db.session import Base, engine
# Import all models so they register with Base.metadata
from app.db.models.models import User, Prediction, EmotionStat, ModelRegistry  # noqa: F401


async def init_db() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("✅  All tables created (or already exist).")


if __name__ == "__main__":
    asyncio.run(init_db())
