from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

from app.routers import ricetta_router, schema_router, scontrino_router, auth

app = FastAPI(title="Schema Nutrizionale Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://balancer-dashboard.onrender.com",
        "http://localhost:4200"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



client = OpenAI(
    api_key=os.environ.get("OPENAI_API_KEY"),
    default_headers={"OpenAI-Client-Data-Retention": "none"},
)

ricetta_router.client = client
scontrino_router.client = client

app.include_router(ricetta_router.router)
app.include_router(schema_router.router)
app.include_router(scontrino_router.router)
app.include_router(auth.router)

@app.get("/")
async def root():
    return {"message": "Balancer backend è attivo."}
