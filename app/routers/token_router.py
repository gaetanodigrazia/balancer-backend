from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from datetime import datetime
import hmac
import hashlib
import base64
import os

router = APIRouter(prefix="/token", tags=["token"])

# Segreto per firmare i timestamp
SECRET = os.getenv("DATABASE_URL")

def sign_timestamp(ts: str) -> str:
    """Genera la firma HMAC del timestamp."""
    mac = hmac.new(SECRET.encode(), ts.encode(), hashlib.sha256)
    return base64.urlsafe_b64encode(mac.digest()).decode()

class TimestampToken(BaseModel):
    ts: str  # ISO format datetime string
    sig: str  # Firma HMAC base64

@router.get("/genera")
async def genera_token():
    """Genera un timestamp firmato."""
    ts = datetime.utcnow().replace(microsecond=0).isoformat() + "Z"
    sig = sign_timestamp(ts)
    return {"ts": ts, "sig": sig}

@router.post("/verifica")
async def verifica_token(token: TimestampToken):
    """Verifica che il timestamp firmato sia valido."""
    expected_sig = sign_timestamp(token.ts)
    if not hmac.compare_digest(token.sig, expected_sig):
        raise HTTPException(status_code=400, detail="Firma non valida")
    return {"valid": True}
