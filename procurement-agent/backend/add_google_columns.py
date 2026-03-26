import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
import os
from dotenv import load_dotenv

load_dotenv()


# If the above doesn't work, hardcode it temporarily like this:
DATABASE_URL = "postgresql+asyncpg://procurement_user:procurement_pass@localhost:5432/procurement"

async def add_columns():
    if not DATABASE_URL:
        print(" DATABASE_URL not found in .env")
        return

    engine = create_async_engine(DATABASE_URL)
    
    async with engine.begin() as conn:
        await conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS google_id VARCHAR(255) UNIQUE;"))
        await conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS picture VARCHAR(500);"))
        await conn.execute(text("CREATE INDEX IF NOT EXISTS idx_users_google_id ON users(google_id);"))
    
    print("✅ Google columns (google_id and picture) added successfully!")
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(add_columns())