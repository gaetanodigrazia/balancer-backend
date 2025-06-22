from fastapi import APIRouter, HTTPException, Body
from sqlalchemy import text
from sqlalchemy.future import select
from sqlalchemy.orm import Session
from app.models.orm_models import Utente
from app.database import SessionLocal
import uuid
from datetime import datetime, timedelta
import traceback
import logging
logger = logging.getLogger("uvicorn.error")

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/login")
async def login(payload: dict = Body(...)):
    try:
        username = payload.get("username")
        password = payload.get("password")

        if not username or not password:
            raise HTTPException(status_code=400, detail="Username e password sono obbligatori")

        async with SessionLocal() as session:
            result = await session.execute(
                select(Utente).where(Utente.username == username, Utente.password == password)
            )
            user = result.scalars().first()

            if not user:
                raise HTTPException(status_code=401, detail="Credenziali non valide")
            print(f"[DEBUG] Utente trovato: {user.username} (ID: {user.id})")

            
            keysession = str(uuid.uuid4())
            now = datetime.utcnow()
            expired = now + timedelta(hours=1)

            user.keysession = keysession
            user.createdAt = now
            user.expiredAt = expired

            await session.commit()
            await session.refresh(user)

            return {
                "token": keysession,
                "expires_at": user.expiredAt.isoformat(),
                "user_id": user.id
            }

    except Exception as e:
        logger.error("[LOGIN ERROR] Eccezione catturata:")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail="Errore interno al server durante il login")


        
@router.post("/logout")
async def logout(payload: dict = Body(...)):
    token = payload.get("token")
    if not token:
        raise HTTPException(status_code=400, detail="Token mancante")

    async with SessionLocal() as session:
        result = await session.execute(
            select(Utente).where(Utente.keysession == token)
        )
        user = result.scalars().first()

        if not user:
            raise HTTPException(status_code=401, detail="Sessione non valida")

        user.keysession = None
        user.createdAt = None
        user.expiredAt = None

        await session.commit()
        return {"status": "ok", "message": "Logout effettuato con successo"}

@router.post("/debug-crea-utente")
async def crea_utente(payload: dict = Body(...)):
    async with SessionLocal() as session:
        user = Utente(
            username=payload["username"],
            password=payload["password"]
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)
        return {"id": user.id, "username": user.username}
