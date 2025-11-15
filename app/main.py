from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import auth, videos, login

app = FastAPI(title="Backend Supabase + FFmpeg")

# Permitir o front (Vite) acessar o backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inclui as rotas
app.include_router(auth.router, prefix="/api/auth", tags=["Auth"])
app.include_router(videos.router, prefix="/api/videos", tags=["Videos"])
app.include_router(login.router, prefix="/api/login", tags=["Login"])


@app.get("/")
def root():
    return {"message": "🚀 API rodando!"}
