import asyncio

from app.workers.memory_worker import run_memory_worker


if __name__ == "__main__":
    asyncio.run(run_memory_worker())