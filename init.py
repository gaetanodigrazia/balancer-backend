import asyncio
from app.database import engine
from app.models.orm_models import Base

async def init():
    async with engine.begin() as conn:
        # Sblocca questa riga se vuoi forzare la cancellazione delle tabelle (⚠️ attenzione ai dati!)
        # await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    print("✅ Tabelle create con successo.")

asyncio.run(init())
