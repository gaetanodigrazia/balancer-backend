from fastapi import APIRouter, HTTPException, Body
from sqlalchemy import text
from sqlalchemy.future import select
from sqlalchemy.orm import Session
from app.models.orm_models import Utente
from app.database import SessionLocal
import uuid
from datetime import datetime, timedelta

router = APIRouter(prefix="/auth", tags=["auth"])

from fastapi import APIRouter, HTTPException, Body
from sqlalchemy.future import select
from app.database import SessionLocal
from app.models.orm_models import Utente
from datetime import datetime, timedelta
import uuid

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

            # ✅ Genera token temporaneo
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
        # 🔴 logga l'errore, ma non lo esporre in produzione
        print(f"[LOGIN ERROR] {e}")
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
