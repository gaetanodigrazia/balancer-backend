from fastapi import APIRouter, HTTPException
from typing import Dict
import json
import logging
import re

from sqlalchemy import text
from app.models.schema_models import RicettaOutput, DettagliPasto
from app.models.orm_models import SchemaNutrizionale
from app.database import SessionLocal

router = APIRouter(prefix="/ricette", tags=["ricette"])
logger = logging.getLogger("uvicorn.error")

client = None  # Assicurati che venga inizializzato nel main


def normalizza_dettagli(raw_dettagli: dict) -> dict:
    normalized = {}
    if not isinstance(raw_dettagli, dict):
        logger.warning("⚠️ 'dettagli' non è un dizionario valido")
        return {}

    for key, val in raw_dettagli.items():
        if isinstance(val, dict) and "opzioni" in val and isinstance(val["opzioni"], list):
            try:
                normalized[key] = DettagliPasto.parse_obj(val)
            except Exception as e:
                logger.warning(f"❌ Errore parsing per '{key}': {e}")
                logger.debug(f"Contenuto non valido:\n{json.dumps(val, indent=2)}")
                normalized[key] = DettagliPasto(opzioni=[])
        else:
            normalized[key] = DettagliPasto(opzioni=[])
    return normalized


@router.post("/genera/{schema_id}/{tipo_pasto}", response_model=RicettaOutput)
async def genera_ricetta(schema_id: int, tipo_pasto: str):
    logger.info(f"🟡 [MOCK] Generazione ricetta per schema ID={schema_id}, tipo_pasto='{tipo_pasto}'")

    async with SessionLocal() as session:
        result = await session.execute(
            text("SELECT * FROM schemi_nutrizionali WHERE id = :id"),
            {"id": schema_id}
        )
        row = result.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Schema non trovato")

        schema_data = dict(row._mapping)
        raw_json = schema_data.get("dettagli", "{}")
        try:
            dettagli_raw = json.loads(raw_json)
            dettagli = normalizza_dettagli(dettagli_raw)
        except Exception:
            dettagli = {}

        if tipo_pasto not in dettagli or not dettagli[tipo_pasto].opzioni:
            raise HTTPException(status_code=400, detail=f"Nessuna opzione per il pasto '{tipo_pasto}'")

        logger.info("ℹ️ [MOCK] Restituzione ricetta simulata")

        # Ricette mock diverse per tipo pasto
        ricette_mock = {
            "colazione": RicettaOutput(
                titolo="Smoothie proteico",
                ingredienti=[
                    {"nome": "Banana", "quantita": "1"},
                    {"nome": "Latte di mandorla", "quantita": "200ml"},
                    {"nome": "Proteine in polvere", "quantita": "30g"},
                    {"nome": "Avena", "quantita": "40g"},
                ],
                procedimento="1. Inserisci tutti gli ingredienti nel frullatore.\n2. Frulla fino a ottenere un composto omogeneo.\n3. Servi fresco.",
                presentazione="Versa in un bicchiere alto con cubetti di ghiaccio.",
                nota_nutrizionale="Perfetto per iniziare la giornata con energia."
            ),
            "spuntino_1": RicettaOutput(
                titolo="Yogurt con frutta secca",
                ingredienti=[
                    {"nome": "Yogurt greco", "quantita": "150g"},
                    {"nome": "Noci", "quantita": "15g"},
                    {"nome": "Miele", "quantita": "1 cucchiaino"},
                ],
                procedimento="1. Versa lo yogurt in una ciotola.\n2. Aggiungi le noci spezzettate e un filo di miele.\n3. Mescola e gusta.",
                presentazione="Servi in una coppetta con qualche frutto fresco.",
                nota_nutrizionale="Spuntino proteico e saziante."
            ),
            "pranzo": RicettaOutput(
                titolo="Insalata di riso integrale e pollo",
                ingredienti=[
                    {"nome": "Riso integrale", "quantita": "60g"},
                    {"nome": "Petto di pollo", "quantita": "150g"},
                    {"nome": "Pomodorini", "quantita": "50g"},
                    {"nome": "Zucchine", "quantita": "50g"},
                ],
                procedimento="1. Cuoci il riso.\n2. Griglia il pollo e le zucchine.\n3. Unisci tutto in una ciotola con i pomodorini.\n4. Condisci a piacere.\n5. Mescola bene e servi.",
                presentazione="In una bowl con foglie di basilico fresco.",
                nota_nutrizionale="Pasto equilibrato per il pranzo."
            ),
            "spuntino_2": RicettaOutput(
                titolo="Barretta energetica casalinga",
                ingredienti=[
                    {"nome": "Fiocchi d'avena", "quantita": "50g"},
                    {"nome": "Burro di arachidi", "quantita": "1 cucchiaio"},
                    {"nome": "Miele", "quantita": "1 cucchiaino"},
                    {"nome": "Mandorle", "quantita": "10g"},
                ],
                procedimento="1. Mescola tutti gli ingredienti.\n2. Compatta su carta da forno.\n3. Lascia riposare in frigo 2 ore.\n4. Taglia a barrette.\n5. Servi.",
                presentazione="Avvolgi in carta da forno per uno snack pratico.",
                nota_nutrizionale="Fonte di energia prima dello sport."
            ),
            "pre_intra_post_workout": RicettaOutput(
                titolo="Frullato pre-workout",
                ingredienti=[
                    {"nome": "Banana", "quantita": "1"},
                    {"nome": "Latte", "quantita": "200ml"},
                    {"nome": "Miele", "quantita": "1 cucchiaino"},
                    {"nome": "Proteine in polvere", "quantita": "20g"},
                ],
                procedimento="1. Frulla tutti gli ingredienti.\n2. Servi subito.\n3. Consumare 30 minuti prima dell’allenamento.",
                presentazione="In uno shaker portatile.",
                nota_nutrizionale="Ideale per fornire energia e amminoacidi."
            ),
            "cena": RicettaOutput(
                titolo="Zuppa di legumi e verdure",
                ingredienti=[
                    {"nome": "Lenticchie", "quantita": "80g"},
                    {"nome": "Carote", "quantita": "50g"},
                    {"nome": "Sedano", "quantita": "30g"},
                    {"nome": "Olio extravergine", "quantita": "1 cucchiaino"},
                ],
                procedimento="1. Fai un soffritto leggero con olio, carote e sedano.\n2. Aggiungi le lenticchie e acqua.\n3. Cuoci a fuoco lento per 30 minuti.\n4. Regola di sale.\n5. Servi calda.",
                presentazione="In un piatto fondo con crostini integrali.",
                nota_nutrizionale="Ricca di fibre e proteine vegetali."
            ),
        }

        if tipo_pasto not in ricette_mock:
            raise HTTPException(status_code=400, detail="Tipo pasto non supportato per esempio fittizio.")

        return ricette_mock[tipo_pasto]
