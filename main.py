from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
from dotenv import load_dotenv
from openai import OpenAI

# Carica variabili ambiente
load_dotenv()

# Importa router
from app.routers import ricetta_router, schema_router, scontrino_router

app = FastAPI(title="Schema Nutrizionale Backend")

# Middleware CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://balancer-dashboard.onrender.com/"],
    allow_origins=["http://localhost:4200/"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inizializza client OpenAI
client = OpenAI(
    api_key=os.environ.get("OPENAI_API_KEY"),
    default_headers={"OpenAI-Client-Data-Retention": "none"},
)

# Assegna il client OpenAI ai router che ne hanno bisogno
ricetta_router.client = client
scontrino_router.client = client

# Includi i router
app.include_router(ricetta_router.router)
app.include_router(schema_router.router)
app.include_router(scontrino_router.router)

# Endpoint di health check semplice
@app.get("/")
async def root():
    return {"message": "Schema Nutrizionale Backend è attivo."}
