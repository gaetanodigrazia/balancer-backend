from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.responses import FileResponse
import os
from dotenv import load_dotenv
from openai import OpenAI

from app.routers import ricetta_router, schema_router, scontrino_router, auth

load_dotenv()

app = FastAPI(title="Schema Nutrizionale Backend")

# CORS
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

@app.middleware("http")
async def custom_cors_headers(request, call_next):
    response = await call_next(request)
    origin = request.headers.get("origin")
    if origin in ["https://balancer-dashboard.onrender.com", "http://localhost:4200"]:
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Access-Control-Allow-Credentials"] = "true"
        response.headers["Access-Control-Allow-Methods"] = "*"
        response.headers["Access-Control-Allow-Headers"] = "*"
    return response

# Routers
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
ricetta_router.client = client
scontrino_router.client = client

app.include_router(ricetta_router.router)
app.include_router(schema_router.router)
app.include_router(scontrino_router.router)
app.include_router(auth.router)

# ✅ Serve la build Angular da /dist/balancer
frontend_dist = os.path.join(os.path.dirname(__file__), "..", "dist", "balancer")
frontend_dist = os.path.abspath(frontend_dist)

# Static files
app.mount("/static", StaticFiles(directory=os.path.join(frontend_dist, "assets")), name="static")

# ✅ Fallback per Angular SPA
@app.get("/{full_path:path}")
async def serve_angular_app(full_path: str):
    index_file = os.path.join(frontend_dist, "index.html")
    if os.path.exists(index_file):
        return FileResponse(index_file)
    return {"error": "index.html not found"}

# API test
@app.get("/")
async def root():
    return {"message": "Balancer backend è attivo."}
