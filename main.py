import logging
from datetime import datetime

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response, JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

from app.routers import ricetta_router, schema_router, scontrino_router, auth

# ✅ Logging setup
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

ALLOWED_ORIGINS = [
    "https://balancer-dashboard.onrender.com",
    "http://localhost:4200",
]

app = FastAPI(title="Schema Nutrizionale Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ Middleware custom con logging
class LoggingAndCORSMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = datetime.utcnow()
        try:
            response = await call_next(request)
        except Exception as exc:
            logging.error("❌ Eccezione: %s", str(exc), exc_info=True)
            response = JSONResponse(content={"detail": "Errore interno"}, status_code=500)

        duration = (datetime.utcnow() - start_time).total_seconds()
        user_agent = request.headers.get("user-agent", "-")
        ip = request.client.host
        logging.info(
            "➡️ %s %s → %s [%.3fs] | IP: %s | UA: %s",
            request.method, request.url.path, response.status_code, duration, ip, user_agent
        )

        origin = request.headers.get("origin")
        if origin in ALLOWED_ORIGINS:
            response.headers["Access-Control-Allow-Origin"] = origin
            response.headers["Access-Control-Allow-Credentials"] = "true"
            response.headers["Access-Control-Allow-Methods"] = "POST, GET, OPTIONS, PUT, DELETE"
            response.headers["Access-Control-Allow-Headers"] = "Authorization, Content-Type"

        return response

app.add_middleware(LoggingAndCORSMiddleware)

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

# ✅ OpenAI client
client = OpenAI(
    api_key=os.environ.get("OPENAI_API_KEY"),
    default_headers={"OpenAI-Client-Data-Retention": "none"},
)

ricetta_router.client = client
scontrino_router.client = client

# ✅ Routers
app.include_router(ricetta_router.router)
app.include_router(schema_router.router)
app.include_router(scontrino_router.router)
app.include_router(auth.router)

@app.get("/")
async def root():
    return {"message": "Balancer backend è attivo."}
