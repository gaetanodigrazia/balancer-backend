import json
from typing import List, Optional, Dict
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.orm_models import SchemaNutrizionale
from app.models.schema_models import SchemaNutrizionaleInput, DettagliPasto
from fastapi import HTTPException

async def get_all_schemi(session: AsyncSession) -> List[Dict]:
    result = await session.execute(text("SELECT * FROM schemi_nutrizionali ORDER BY id DESC"))
    rows = result.fetchall()
    schemi = []
    for row in rows:
        data = dict(row._mapping)
        if data.get('dettagli'):
            try:
                dettagli_dict = json.loads(data['dettagli'])
                data['dettagli'] = dettagli_dict
            except Exception:
                data['dettagli'] = {}
        else:
            data['dettagli'] = {}
        schemi.append(data)
    return schemi

async def crea_o_aggiorna_schemi(session: AsyncSession, schemi_input: List[SchemaNutrizionaleInput]) -> List[SchemaNutrizionale]:
    saved_schemi = []
    for schema in schemi_input:
        dettagli_dict = {k: v.dict() for k, v in schema.dettagli.items()}
        dettagli_json = json.dumps(dettagli_dict)

        existing = await session.execute(
            text("SELECT * FROM schemi_nutrizionali WHERE nome = :nome"),
            {"nome": schema.nome}
        )
        existing_row = existing.first()

        if existing_row:
            db_schema = await session.get(SchemaNutrizionale, existing_row.id)
            db_schema.calorie = schema.calorie
            db_schema.carboidrati = schema.carboidrati
            db_schema.grassi = schema.grassi
            db_schema.proteine = schema.proteine
            db_schema.acqua = schema.acqua
            db_schema.dettagli = dettagli_json
        else:
            db_schema = SchemaNutrizionale(
                nome=schema.nome,
                calorie=schema.calorie,
                carboidrati=schema.carboidrati,
                grassi=schema.grassi,
                proteine=schema.proteine,
                acqua=schema.acqua,
                dettagli=dettagli_json
            )
            session.add(db_schema)

        saved_schemi.append(db_schema)

    await session.commit()
    for s in saved_schemi:
        await session.refresh(s)
    return saved_schemi

async def aggiorna_dati_generali(session: AsyncSession, nome: str, calorie: float, carboidrati: float,
                                 grassi: float, proteine: float, acqua: float) -> SchemaNutrizionale:
    existing = await session.execute(
        text("SELECT * FROM schemi_nutrizionali WHERE nome = :nome"),
        {"nome": nome}
    )
    existing_row = existing.first()

    if existing_row:
        db_schema = await session.get(SchemaNutrizionale, existing_row.id)
        db_schema.calorie = calorie
        db_schema.carboidrati = carboidrati
        db_schema.grassi = grassi
        db_schema.proteine = proteine
        db_schema.acqua = acqua
    else:
        db_schema = SchemaNutrizionale(
            nome=nome,
            calorie=calorie,
            carboidrati=carboidrati,
            grassi=grassi,
            proteine=proteine,
            acqua=acqua,
            dettagli="{}"
        )
        session.add(db_schema)

    await session.commit()
    await session.refresh(db_schema)
    return db_schema

async def salva_singolo_pasto(session: AsyncSession, nome: str, tipo_pasto: str, dettagli: dict) -> SchemaNutrizionale:
    existing = await session.execute(
        text("SELECT * FROM schemi_nutrizionali WHERE nome = :nome"),
        {"nome": nome}
    )
    existing_row = existing.first()

    if not existing_row:
        raise HTTPException(status_code=404, detail="Schema nutrizionale non trovato")

    db_schema = await session.get(SchemaNutrizionale, existing_row.id)

    dettagli_dict = json.loads(db_schema.dettagli) if db_schema.dettagli else {}

    dettagli_dict[tipo_pasto] = dettagli

    db_schema.dettagli = json.dumps(dettagli_dict)

    await session.commit()
    await session.refresh(db_schema)
    return db_schema

async def elimina_schema(session: AsyncSession, schema_id: int):
    db_schema = await session.get(SchemaNutrizionale, schema_id)
    if not db_schema:
        raise HTTPException(status_code=404, detail="Schema non trovato")
    await session.delete(db_schema)
    await session.commit()



