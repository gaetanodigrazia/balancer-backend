from pydantic import BaseModel
from typing import Optional, List, Dict, Union


# --- Ricetta ---

class Ingrediente(BaseModel):
    nome: str
    quantita: str

class RicettaOutput(BaseModel):
    titolo: str
    ingredienti: List[Ingrediente]
    procedimento: str
    presentazione: str
    nota_nutrizionale: Optional[str] = None

class RicettaRequest(BaseModel):
    tipo_pasto: str
    tipo_schema: str


# --- Alimenti e opzioni schema nutrizionale ---

class Alimento(BaseModel):
    nome: str
    macronutriente: str
    grammi: Optional[float] = None
    gruppoAlimenti: Optional[List["Alimento"]] = None  # supporta combo

Alimento.update_forward_refs()

class OpzionePasto(BaseModel):
    id: Optional[str]
    nome: Optional[str]
    alimenti: List[Alimento]
    salvata: Optional[bool] = False
    inModifica: Optional[bool] = False

class DettagliPasto(BaseModel):
    opzioni: List[OpzionePasto]


# --- Schema Nutrizionale ---

class SchemaNutrizionaleInput(BaseModel):
    id: Optional[int] = None
    nome: str
    calorie: float
    carboidrati: float
    grassi: float
    proteine: float
    acqua: float
    dettagli: Dict[str, DettagliPasto]
    is_modello: bool = False
    is_global: bool = False  # ✅ aggiunto


class SchemaNutrizionaleOut(SchemaNutrizionaleInput):
    id: int

    class Config:
        from_attributes = True


# --- Modelli OCR / Scontrino ---

class ProdottoModel(BaseModel):
    nome: str
    quantita: int
    quantita_grammi: Optional[float] = None
    prezzo_unitario: float

class OCRResponse(BaseModel):
    prodotti: List[ProdottoModel]
    totale: float
    data: str

class ScontrinoOut(BaseModel):
    id: int
    data: str
    totale: float

    class Config:
        from_attributes = True

class ProdottoOut(BaseModel):
    id: int
    nome: str
    quantita: int
    prezzo_unitario: float
    scontrino_id: Optional[int]

    class Config:
        from_attributes = True


# --- Aggiornamento ingrediente (se serve) ---

class IngredienteUpdate(BaseModel):
    nome: str
    quantita: str
