from fastapi import APIRouter, HTTPException, Body, Depends, Header
from typing import List
import json
import logging
from app.auth.dependencies import get_current_user
from app.models.schema_models import SchemaNutrizionaleInput, SchemaNutrizionaleOut, DettagliPasto
from app.models.orm_models import SchemaNutrizionale, Utente
from app.database import SessionLocal
from sqlalchemy import text
from sqlalchemy.future import select

router = APIRouter(prefix="/schemi-nutrizionali", tags=["schemi-nutrizionali"])
logger = logging.getLogger("uvicorn.error")


def normalizza_dettagli(raw_dettagli: dict) -> dict:
    normalized = {}
    for key, val in raw_dettagli.items():
        if isinstance(val, dict) and "opzioni" in val and isinstance(val["opzioni"], list):
            try:
                normalized[key] = DettagliPasto.parse_obj(val)
            except Exception:
                normalized[key] = DettagliPasto(opzioni=[])
        else:
            normalized[key] = DettagliPasto(opzioni=[])
    return normalized

@router.get("", response_model=List[SchemaNutrizionaleOut])
async def get_schemi(current_user: Utente = Depends(get_current_user)):
    async with SessionLocal() as session:
        result = await session.execute(
            text("SELECT * FROM schemi_nutrizionali WHERE is_global = false AND utente_id = :uid ORDER BY id DESC"),
            {"uid": current_user.id}
        )
        rows = result.fetchall()
        schemi = []
        for row in rows:
            data = dict(row._mapping)
            if data.get('dettagli'):
                try:
                    dettagli_raw = json.loads(data['dettagli'])
                    data['dettagli'] = normalizza_dettagli(dettagli_raw)
                except Exception:
                    data['dettagli'] = {}
            else:
                data['dettagli'] = {}
            schemi.append(data)
        return schemi
    
@router.post("", response_model=List[SchemaNutrizionaleOut])
async def crea_schemi(schemi: List[SchemaNutrizionaleInput], current_user: Utente = Depends(get_current_user)):
    saved_schemi = []
    async with SessionLocal() as session:
        for schema in schemi:
            dettagli_dict = {k: v.dict() for k, v in schema.dettagli.items()}
            dettagli_json = json.dumps(dettagli_dict)

            if schema.id:
                db_schema = await session.get(SchemaNutrizionale, schema.id)
                if not db_schema or (db_schema.utente_id != current_user.id and not db_schema.is_global):
                    raise HTTPException(status_code=403, detail="Accesso non autorizzato allo schema")
                db_schema.nome = schema.nome
                db_schema.calorie = schema.calorie
                db_schema.carboidrati = schema.carboidrati
                db_schema.grassi = schema.grassi
                db_schema.proteine = schema.proteine
                db_schema.acqua = schema.acqua
                db_schema.dettagli = dettagli_json
                db_schema.is_modello = schema.is_modello
                db_schema.is_global = schema.is_global
            else:
                existing = await session.execute(
                    text("SELECT * FROM schemi_nutrizionali WHERE nome = :nome"),
                    {"nome": schema.nome}
                )
                if existing.first():
                    raise HTTPException(status_code=400, detail=f"Schema con nome '{schema.nome}' già esistente")

                db_schema = SchemaNutrizionale(
                    nome=schema.nome,
                    calorie=schema.calorie,
                    carboidrati=schema.carboidrati,
                    grassi=schema.grassi,
                    proteine=schema.proteine,
                    acqua=schema.acqua,
                    dettagli=dettagli_json,
                    is_modello=schema.is_modello,
                    is_global=schema.is_global,
                    utente_id=current_user.id
                )
                session.add(db_schema)

            saved_schemi.append(db_schema)

        await session.commit()
        for s in saved_schemi:
            await session.refresh(s)

    result = []
    for s in saved_schemi:
        try:
            dettagli_obj = {k: DettagliPasto.parse_obj(v) for k, v in json.loads(s.dettagli).items()}
        except Exception:
            dettagli_obj = None

        schema_out = SchemaNutrizionaleOut(
            id=s.id,
            nome=s.nome,
            calorie=s.calorie,
            carboidrati=s.carboidrati,
            grassi=s.grassi,
            proteine=s.proteine,
            acqua=s.acqua,
            is_modello=s.is_modello,
            is_global=s.is_global,
            dettagli=dettagli_obj
        )
        result.append(schema_out)

    return result



@router.post("/dati-generali")
async def salva_dati_generali(payload: dict = Body(...), current_user: Utente = Depends(get_current_user)):
    nome = payload.get("nome")
    calorie = payload.get("calorie")
    carboidrati = payload.get("carboidrati")
    grassi = payload.get("grassi")
    proteine = payload.get("proteine")
    acqua = payload.get("acqua")
    is_modello = payload.get("is_modello", False)
    is_global = False  # sempre false come richiesto
    clona_da = payload.get("clona_da")

    if not all([nome, calorie, carboidrati, grassi, proteine, acqua]):
        raise HTTPException(status_code=400, detail="Tutti i campi sono obbligatori")

    async with SessionLocal() as session:
        result = await session.execute(select(Utente).where(Utente.keysession == current_user.keysession))
        user = result.scalars().first()
        if not user:
            raise HTTPException(status_code=401, detail="Token non valido")

        dettagli = "{}"
        if clona_da:
            modello = await session.get(SchemaNutrizionale, clona_da)
            if modello:
                dettagli = modello.dettagli or "{}"

        schema_id = payload.get("id")
        if schema_id:
            db_schema = await session.get(SchemaNutrizionale, schema_id)
            if not db_schema:
                raise HTTPException(status_code=404, detail="Schema non trovato")
            db_schema.nome = nome
            db_schema.calorie = calorie
            db_schema.carboidrati = carboidrati
            db_schema.grassi = grassi
            db_schema.proteine = proteine
            db_schema.acqua = acqua
            db_schema.is_modello = is_modello
            db_schema.is_global = is_global
            db_schema.utente_id = user.id
            if clona_da:
                db_schema.dettagli = dettagli
        else:
            db_schema = SchemaNutrizionale(
                nome=nome,
                calorie=calorie,
                carboidrati=carboidrati,
                grassi=grassi,
                proteine=proteine,
                acqua=acqua,
                is_modello=is_modello,
                is_global=is_global,
                dettagli=dettagli,
                utente_id=user.id
            )
            session.add(db_schema)

        await session.commit()
        await session.refresh(db_schema)

        logger.info(f"✅ Salvato schema '{nome}' (ID: {db_schema.id}) per utente {user.id}")

    return {"status": "ok", "message": "Dati generali salvati con successo"}



@router.post("/dinamico/completo")
async def salva_schema_completo(payload: dict = Body(...), current_user: Utente = Depends(get_current_user)):
    nome = payload.get("nome")
    tipo_schema = payload.get("tipoSchema")
    tipo_pasto = payload.get("tipoPasto")
    dettagli = payload.get("dettagli")

    if not all([nome, tipo_schema, tipo_pasto, dettagli]):
        raise HTTPException(status_code=400, detail="Tutti i campi sono obbligatori")

    async with SessionLocal() as session:
        result = await session.execute(
            text("SELECT * FROM schemi_nutrizionali WHERE nome = :nome"), {"nome": nome}
        )
        row = result.first()
        if not row:
            raise HTTPException(status_code=404, detail="Schema nutrizionale non trovato")

        db_schema = await session.get(SchemaNutrizionale, row.id)
        if db_schema.utente_id != current_user.id:
            raise HTTPException(status_code=403, detail="Accesso non autorizzato")

        dettagli_dict = json.loads(db_schema.dettagli or '{}')
        dettagli_dict[tipo_pasto] = dettagli
        db_schema.dettagli = json.dumps(dettagli_dict)

        await session.commit()
        await session.refresh(db_schema)

    return {"status": "ok", "message": "Schema completo salvato con successo"}





@router.post("/dinamico/pasto")
async def salva_singolo_pasto(payload: dict = Body(...), current_user: Utente = Depends(get_current_user)):
    nome = payload.get("nome")
    tipo_schema = payload.get("tipoSchema")
    tipo_pasto = payload.get("tipoPasto")
    dettagli = payload.get("dettagli")

    if not all([nome, tipo_schema, tipo_pasto, dettagli]):
        raise HTTPException(status_code=400, detail="Tutti i campi sono obbligatori")

    for opzione in dettagli.get("opzioni", []):
        opzione["salvata"] = True

    async with SessionLocal() as session:
        result = await session.execute(
            text("SELECT * FROM schemi_nutrizionali WHERE nome = :nome"), {"nome": nome}
        )
        row = result.first()
        if not row:
            raise HTTPException(status_code=404, detail="Schema nutrizionale non trovato")

        db_schema = await session.get(SchemaNutrizionale, row.id)
        if db_schema.utente_id != current_user.id:
            raise HTTPException(status_code=403, detail="Accesso non autorizzato")

        dettagli_dict = json.loads(db_schema.dettagli or '{}')
        dettagli_dict[tipo_pasto] = dettagli
        db_schema.dettagli = json.dumps(dettagli_dict)

        await session.commit()
        await session.refresh(db_schema)

    return {"status": "ok", "message": "Dettagli pasto aggiornati con successo"}




@router.delete("/{id}")
async def elimina_schema(id: int, current_user: Utente = Depends(get_current_user)):
    async with SessionLocal() as session:
        schema = await session.get(SchemaNutrizionale, id)
        if not schema or schema.utente_id != current_user.id:
            raise HTTPException(status_code=403, detail="Accesso non autorizzato o schema non trovato")
        await session.delete(schema)
        await session.commit()
    return {"status": "ok", "message": f"Schema con id {id} eliminato."}


@router.get("/{schema_id}")
async def get_schema(schema_id: int, current_user: Utente = Depends(get_current_user)):
    async with SessionLocal() as session:
        db_schema = await session.get(SchemaNutrizionale, schema_id)
        if not db_schema or (db_schema.utente_id != current_user.id and not db_schema.is_global):
            raise HTTPException(status_code=403, detail="Accesso non autorizzato o schema non trovato")

        data = db_schema.__dict__.copy()
        if data.get("dettagli"):
            try:
                data["dettagli"] = json.loads(data["dettagli"])
            except Exception:
                data["dettagli"] = {}
        else:
            data["dettagli"] = {}

        return data


@router.delete("/{schema_id}/opzione/{tipo_pasto}/{opzione_id}/")
async def elimina_opzione_per_id(schema_id: int, tipo_pasto: str, opzione_id: str):
    async with SessionLocal() as session:
        db_schema = await session.get(SchemaNutrizionale, schema_id)
        if not db_schema:
            raise HTTPException(status_code=404, detail="Schema non trovato")

        dettagli_dict = json.loads(db_schema.dettagli or '{}')

        if tipo_pasto not in dettagli_dict:
            raise HTTPException(status_code=404, detail="Tipo pasto non trovato")

        opzioni = dettagli_dict[tipo_pasto].get("opzioni", [])
        nuove_opzioni = [op for op in opzioni if op.get("id") != opzione_id]

        if len(opzioni) == len(nuove_opzioni):
            raise HTTPException(status_code=404, detail="Opzione non trovata")

        dettagli_dict[tipo_pasto]["opzioni"] = nuove_opzioni
        db_schema.dettagli = json.dumps(dettagli_dict)

        await session.commit()
        return {"status": "ok", "message": "Opzione rimossa"}



@router.get("/schema/modelli", response_model=List[SchemaNutrizionaleOut])
async def getModelli(current_user: Utente = Depends(get_current_user)):
    async with SessionLocal() as session:
        result = await session.execute(
            text("""
                SELECT * 
                FROM schemi_nutrizionali 
                WHERE is_modello = true AND is_global = false AND utente_id = :uid 
                ORDER BY id DESC
            """),
            {"uid": current_user.id}
        )
        rows = result.fetchall()
        schemi = []
        for row in rows:
            data = dict(row._mapping)
            if data.get('dettagli'):
                try:
                    dettagli_raw = json.loads(data['dettagli'])
                    data['dettagli'] = normalizza_dettagli(dettagli_raw)
                except Exception:
                    data['dettagli'] = {}
            else:
                data['dettagli'] = {}
            schemi.append(data)

        return schemi



@router.post("/clona/{schema_id}", response_model=SchemaNutrizionaleOut)
async def clona_schema(schema_id: int):
    async with SessionLocal() as session:
        db_schema = await session.get(SchemaNutrizionale, schema_id)
        if not db_schema:
            raise HTTPException(status_code=404, detail="Schema non trovato")

        # Genera un nuovo nome (assicurati che non esista già)
        nuovo_nome_base = f"Copia di {db_schema.nome}"
        nuovo_nome = nuovo_nome_base
        count = 1

        while True:
            existing = await session.execute(
                text("SELECT 1 FROM schemi_nutrizionali WHERE nome = :nome"),
                {"nome": nuovo_nome}
            )
            if existing.first():
                count += 1
                nuovo_nome = f"{nuovo_nome_base} ({count})"
            else:
                break

        # Crea una nuova istanza
        nuovo_schema = SchemaNutrizionale(
            nome=nuovo_nome,
            calorie=db_schema.calorie,
            carboidrati=db_schema.carboidrati,
            grassi=db_schema.grassi,
            proteine=db_schema.proteine,
            acqua=db_schema.acqua,
            is_modello=db_schema.is_modello,
            dettagli=db_schema.dettagli
        )
        session.add(nuovo_schema)
        await session.commit()
        await session.refresh(nuovo_schema)

        # Parsing dettagli
        try:
            dettagli_dict = json.loads(nuovo_schema.dettagli)
            dettagli_parsed = {
                k: DettagliPasto.parse_obj(v) for k, v in dettagli_dict.items()
            }
        except Exception:
            dettagli_parsed = {}

        return SchemaNutrizionaleOut(
            id=nuovo_schema.id,
            nome=nuovo_schema.nome,
            calorie=nuovo_schema.calorie,
            carboidrati=nuovo_schema.carboidrati,
            grassi=nuovo_schema.grassi,
            proteine=nuovo_schema.proteine,
            acqua=nuovo_schema.acqua,
            is_modello=nuovo_schema.is_modello,
            dettagli=dettagli_parsed
        )


@router.get("/globali", response_model=List[SchemaNutrizionaleOut])
async def get_globali():
    async with SessionLocal() as session:
        result = await session.execute(
            text("SELECT * FROM schemi_nutrizionali WHERE is_global = true ORDER BY id DESC")
        )
        rows = result.fetchall()
        schemi = []
        for row in rows:
            data = dict(row._mapping)
            if data.get('dettagli'):
                try:
                    dettagli_raw = json.loads(data['dettagli'])
                    data['dettagli'] = normalizza_dettagli(dettagli_raw)
                except Exception:
                    data['dettagli'] = {}
            else:
                data['dettagli'] = {}
            schemi.append(data)
        return schemi
    
    
@router.get("/globali", response_model=List[SchemaNutrizionaleOut])
async def get_schemi_globali():
    async with SessionLocal() as session:
        result = await session.execute(
            text("SELECT * FROM schemi_nutrizionali WHERE is_global = true ORDER BY id DESC")
        )
        rows = result.fetchall()
        schemi = []
        for row in rows:
            data = dict(row._mapping)
            if data.get('dettagli'):
                try:
                    dettagli_raw = json.loads(data['dettagli'])
                    data['dettagli'] = normalizza_dettagli(dettagli_raw)
                except Exception:
                    data['dettagli'] = {}
            else:
                data['dettagli'] = {}
            schemi.append(data)
        return schemi