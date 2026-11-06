import asyncio
from app.core.db import engine
from sqlalchemy import inspect

async def main():
    async with engine.begin() as conn:
        insp = inspect(conn)
        print('Tables:', insp.get_table_names())

asyncio.run(main())
