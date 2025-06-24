from fastapi import Depends, HTTPException, Header
from sqlalchemy.future import select
from app.database import SessionLocal
from app.models.orm_models import Utente

async def get_current_user(authorization: str = Header(...)) -> Utente:
    print("🔐 get_current_user chiamato")

    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token mancante o formato errato")

    token = authorization.removeprefix("Bearer ").strip()

    async with SessionLocal() as session:
        result = await session.execute(
            select(Utente).where(Utente.keysession == token)
        )
        user = result.scalars().first()

        if not user:
            raise HTTPException(status_code=401, detail="Token non valido")

        return user
