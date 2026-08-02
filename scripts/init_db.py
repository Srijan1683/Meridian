import asyncio
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import asyncpg
from dotenv import load_dotenv

load_dotenv()

MIGRATION_PATH = os.path.join(os.path.dirname(__file__), "../app/db/migrations/001_initial_schema.sql")


async def init_db():
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("ERROR: DATABASE_URL not set")
        sys.exit(1)

    print("Connecting to database...")
    conn = await asyncpg.connect(database_url)

    print("Reading migration file...")
    with open(MIGRATION_PATH, "r") as f:
        sql = f.read()

    print("Running migrations...")
    try:
        await conn.execute(sql)
        print("Done — all tables created successfully.")
    except asyncpg.DuplicateTableError:
        print("Tables already exist — nothing to do.")
    finally:
        await conn.close()