from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from typing import List
import base64
import json
import re
import logging

from app.models.schema_models import OCRResponse, ScontrinoOut, ProdottoOut
from app.models.orm_models import Scontrino, Prodotto
from app.database import SessionLocal
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

router = APIRouter(prefix="/scontrini", tags=["scontrini"])
logger = logging.getLogger("uvicorn.error")

# Serve istanza OpenAI client esterna
client = None

def extract_json(text: str) -> dict:
    match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    cleaned = match.group(1) if match else text.strip()
    return json.loads(cleaned)

@router.post("/ocr")
async def ocr_scontrino(file: UploadFile = File(...)):
    if client is None:
        raise HTTPException(status_code=500, detail="OpenAI client non configurato")

    img_bytes = await file.read()
    img_b64 = base64.b64encode(img_bytes).decode("utf-8")
    image_url = f"data:{file.content_type};base64,{img_b64}"

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": (
                                "Estrai i prodotti con quantità e prezzo da questo scontrino "
                                "e restituisci solo il JSON nel seguente formato:\n"
                                "{\n"
                                "  \"prodotti\": [{\"nome\": ..., \"quantita\": ..., \"prezzo_unitario\": ...}],\n"
                                "  \"totale\": ...,\n"
                                "  \"data\": \"YYYY-MM-DD\"\n"
                                "}\n"
                                "Rispondi solo con un oggetto JSON valido, senza spiegazioni."
                            ),
                        },
                        {
                            "type": "image_url",
                            "image_url": {"url": image_url}
                        }
                    ]
                }
            ],
            max_tokens=400
        )
        raw_content = response.choices[0].message.content.strip()
        parsed = extract_json(raw_content)
        validated = OCRResponse(**parsed)

        async with SessionLocal() as session:
            scontrino = Scontrino(data=validated.data, totale=validated.totale)
            session.add(scontrino)
            await session.flush()

            for p in validated.prodotti:
                prodotto = Prodotto(
                    nome=p.nome,
                    quantita=p.quantita,
                    prezzo_unitario=p.prezzo_unitario,
                    scontrino_id=scontrino.id
                )
                session.add(prodotto)

            await session.commit()

        return JSONResponse(content={"status": "ok", "data": validated.dict()})

    except (json.JSONDecodeError, Exception) as e:
        logger.error(f"Errore OCR scontrino: {str(e)}")
        return JSONResponse(status_code=422, content={"status": "error", "error": str(e)})

@router.get("", response_model=List[ScontrinoOut])
async def get_scontrini():
    async with SessionLocal() as session:
        result = await session.execute(text("SELECT id, data, totale FROM scontrini ORDER BY id DESC"))
        rows = result.fetchall()
        return [dict(row._mapping) for row in rows]

@router.get("/prodotti", response_model=List[ProdottoOut])
async def get_prodotti():
    async with SessionLocal() as session:
        result = await session.execute(text("SELECT id, nome, quantita, prezzo_unitario, scontrino_id FROM prodotti ORDER BY id DESC"))
        rows = result.fetchall()
        return [dict(row._mapping) for row in rows]
