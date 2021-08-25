import asyncpg


async def init_connection_pool(dsn: str):
    async with asyncpg.create_pool(dsn=dsn) as pool:
        yield pool
