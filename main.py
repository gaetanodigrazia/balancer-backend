from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response, JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

from app.routers import ricetta_router, schema_router, scontrino_router, auth

# ✅ Lista di origini ammesse
ALLOWED_ORIGINS = [
    "https://balancer-dashboard.onrender.com",
    "http://localhost:4200",
]

# ✅ Inizializza l'app
app = FastAPI(title="Schema Nutrizionale Backend")

# ✅ CORS middleware standard
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ Middleware custom per intercettare anche le eccezioni
class CORSErrorFixMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        try:
            response = await call_next(request)
        except Exception as exc:
            print("❌ Errore intercettato dal middleware:", exc)
            response = JSONResponse(content={"detail": str(exc)}, status_code=500)

        origin = request.headers.get("origin")
        if origin in ALLOWED_ORIGINS:
            response.headers["Access-Control-Allow-Origin"] = origin
            response.headers["Access-Control-Allow-Credentials"] = "true"
            response.headers["Access-Control-Allow-Methods"] = "POST, GET, OPTIONS, PUT, DELETE"
            response.headers["Access-Control-Allow-Headers"] = "Authorization, Content-Type"

        return response

app.add_middleware(CORSErrorFixMiddleware)

# ✅ Gestione preflight OPTIONS
@app.options("/{full_path:path}")
async def preflight_handler(request: Request, full_path: str):
    origin = request.headers.get("origin")
    if origin in ALLOWED_ORIGINS:
        headers = {
            "Access-Control-Allow-Origin": origin,
            "Access-Control-Allow-Methods": "POST, GET, OPTIONS, PUT, DELETE",
            "Access-Control-Allow-Headers": "Authorization, Content-Type",
            "Access-Control-Allow-Credentials": "true"
        }
        return Response(status_code=200, headers=headers)
    return Response(status_code=403)

# ✅ Configura OpenAI client
client = OpenAI(
    api_key=os.environ.get("OPENAI_API_KEY"),
    default_headers={"OpenAI-Client-Data-Retention": "none"},
)

ricetta_router.client = client
scontrino_router.client = client

# ✅ Registra router
app.include_router(ricetta_router.router)
app.include_router(schema_router.router)
app.include_router(scontrino_router.router)
app.include_router(auth.router)

# ✅ Health check
@app.get("/")
async def root():
    return {"message": "Balancer backend è attivo."}
