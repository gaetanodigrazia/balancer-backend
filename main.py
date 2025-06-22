from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

from app.routers import ricetta_router, schema_router, scontrino_router, auth

app = FastAPI(title="Schema Nutrizionale Backend")

# ✅ Middleware CORS (valido per la maggior parte dei casi)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://balancer-dashboard.onrender.com",
        "http://localhost:4200",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ Fix specifico per risposte OPTIONS (necessario su Render/Cloudflare)
@app.options("/{full_path:path}")
async def preflight_handler(request: Request, full_path: str):
    origin = request.headers.get("origin")
    if origin in ["https://balancer-dashboard.onrender.com", "http://localhost:4200"]:
        headers = {
            "Access-Control-Allow-Origin": origin,
            "Access-Control-Allow-Methods": "POST, GET, OPTIONS, PUT, DELETE",
            "Access-Control-Allow-Headers": "Authorization, Content-Type",
            "Access-Control-Allow-Credentials": "true"
        }
        return Response(status_code=200, headers=headers)
    return Response(status_code=403)

# ✅ Client OpenAI
client = OpenAI(
    api_key=os.environ.get("OPENAI_API_KEY"),
    default_headers={"OpenAI-Client-Data-Retention": "none"},
)

ricetta_router.client = client
scontrino_router.client = client

# ✅ Router
app.include_router(ricetta_router.router)
app.include_router(schema_router.router)
app.include_router(scontrino_router.router)
app.include_router(auth.router)

@app.get("/")
async def root():
    return {"message": "Balancer backend è attivo."}
