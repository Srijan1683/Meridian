import asyncio
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from pathlib import Path

import asyncpg
from dotenv import load_dotenv

load_dotenv()

MIGRATION_PATH = os.path.join(
    os.path.dirname(__file__), "../app/db/migrations/001_initial_schema.sql"
)


async def init_db():
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("ERROR: DATABASE_URL not set")
        sys.exit(1)

    print("Connecting to database...")
    try:
        conn = await asyncpg.connect(database_url)
    except (OSError, asyncpg.PostgresError) as exc:
        print(f"ERROR connecting: {exc}")
        sys.exit(1)

    print("Reading migration file...")
    sql = await asyncio.to_thread(Path(MIGRATION_PATH).read_text, encoding="utf-8")

    print("Running migrations...")
    statements = [s.strip() for s in sql.split(";") if s.strip()]
    for statement in statements:
        try:
            await conn.execute(statement)
        except asyncpg.DuplicateTableError:
            print("Table already exists, skipping...")
        except asyncpg.DuplicateObjectError:
            print("Object already exists, skipping...")
        except asyncpg.PostgresError as exc:
            print(f"ERROR running migration statement: {exc}")

    await conn.close()
    print("Done.")


if __name__ == "__main__":
    asyncio.run(init_db())
