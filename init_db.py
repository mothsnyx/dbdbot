
import sqlite3
import aiosqlite
import asyncio

async def initialize_db():
    async with aiosqlite.connect('profiles.db') as db:
        await db.execute('''
        CREATE TABLE IF NOT EXISTS profiles (
            user_id INTEGER,
            name TEXT,
            role TEXT,
            stats TEXT,
            inventory TEXT,
            PRIMARY KEY (user_id, name, role)
        )
        ''')
        await db.commit()

if __name__ == "__main__":
    asyncio.run(initialize_db())
