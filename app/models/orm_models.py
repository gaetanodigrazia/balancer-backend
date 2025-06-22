from sqlalchemy import Column, Integer, Float, Boolean, String, ForeignKey, Text, DateTime
from sqlalchemy.orm import relationship
from app.database import Base

class Scontrino(Base):
    __tablename__ = "scontrini"
    id = Column(Integer, primary_key=True, index=True)
    data = Column(String, index=True)
    totale = Column(Float)
    prodotti = relationship("Prodotto", back_populates="scontrino", cascade="all, delete")

class Prodotto(Base):
    __tablename__ = "prodotti"
    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String)
    quantita = Column(Integer)
    quantita_grammi = Column(Float, nullable=True)
    prezzo_unitario = Column(Float)
    scontrino_id = Column(Integer, ForeignKey("scontrini.id"), nullable=True)
    scontrino = relationship("Scontrino", back_populates="prodotti")

class SchemaNutrizionale(Base):
    __tablename__ = "schemi_nutrizionali"
    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String, unique=True, nullable=False, index=True)
    calorie = Column(Float, nullable=False)
    carboidrati = Column(Float, nullable=False)
    grassi = Column(Float, nullable=False)
    proteine = Column(Float, nullable=False)
    acqua = Column(Float, nullable=False)
    dettagli = Column(Text, nullable=False)
    is_modello = Column(Boolean, default=False)
    utente_id = Column(Integer, ForeignKey("utenti.id"), nullable=True)
    utente = relationship("Utente")
    is_global = Column(Boolean, default=False)

class Utente(Base):
    __tablename__ = "utenti"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, nullable=False)
    password = Column(String, nullable=False)
    keysession = Column(String)
    createdAt = Column(DateTime, name="createdat")
    expiredAt = Column(DateTime, name="expiredat")