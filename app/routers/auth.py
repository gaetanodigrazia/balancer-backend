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
from app.database import engine
from sqlalchemy import inspect
from app.database import engine
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

@router.get("/utenti")
async def lista_utenti():
    async with SessionLocal() as session:
        result = await session.execute(select(Utente))
        utenti = result.scalars().all()
        return [ {
                "username": u.username,
                "password": u.password,
                "token": u.keysession,
                "expires_at": u.expiredAt.isoformat(),
                "user_id": u.id
            } for u in utenti]

@router.post("/demo-login")
async def demo_login():
    try:
        # Genera credenziali demo
        unique_id = uuid.uuid4().hex[:8]
        username = f"demo_{unique_id}"
        password = username
        keysession = str(uuid.uuid4())
        now = datetime.utcnow()
        expires_at = now + timedelta(hours=12)

        async with SessionLocal() as session:
            utente = Utente(
                username=username,
                password=password,
                keysession=keysession,
                createdAt=now,
                expiredAt=expires_at,
                is_demo=True
            )

            session.add(utente)
            await session.commit()
            await session.refresh(utente)

            print(f"[DEBUG] Utente demo creato: {username}")

            return {
                "username": utente.username,
                "password": utente.password,
                "token": utente.keysession,
                "expires_at": utente.expiredAt.isoformat(),
                "user_id": utente.id
            }

    except Exception as e:
        print(f"[ERRORE] demo_login: {e}")
        raise HTTPException(status_code=500, detail="Errore nella creazione utente demo")


@router.get("/utenti-columns")
async def get_utenti_columns():
    try:
        async with engine.begin() as conn:
            def fetch_columns(sync_conn):
                insp = inspect(sync_conn)
                columns = []
                for col in insp.get_columns("utenti"):
                    columns.append({
                        "name": col["name"],
                        "type": str(col["type"]),
                        "nullable": col.get("nullable", None),
                        "default": col.get("default", None)
                    })
                return columns

            columns = await conn.run_sync(fetch_columns)

        return {"columns": columns}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Errore durante l'ispezione: {str(e)}")
