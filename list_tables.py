import sys, asyncio
sys.path.append('backend')
from app.core.database import engine
from sqlalchemy import inspect

async def main():
    async with engine.begin() as conn:
        insp = inspect(conn)
        print('Tables:', insp.get_table_names())

if __name__ == '__main__':
    asyncio.run(main())
