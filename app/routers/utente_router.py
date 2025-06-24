from fastapi import APIRouter, Header, HTTPException, status
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import engine, SessionLocal
from app.models.orm_models import Utente
from app.models.schema_models import UtenteOut

router = APIRouter(prefix="/utenti", tags=["utenti"])
@router.get("/utente", response_model=UtenteOut)
async def leggi_utente_corrente(authorization: str = Header(...)):
    print(f"🧪 Authorization header ricevuto: '{authorization}'")

    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token mancante o formato errato"
        )

    token = authorization.removeprefix("Bearer ").strip()
    print(f"🔑 Token estratto: '{token}'")

    async with SessionLocal() as session:  # usa la sessione corretta
        result = await session.execute(select(Utente).where(Utente.keysession == token))
        utente = result.scalars().first()

        if not utente:
            raise HTTPException(status_code=401, detail="Token non valido")

        return UtenteOut.from_orm(utente)

@router.options("/utente")
async def options_utente():
    return Response(status_code=200)
