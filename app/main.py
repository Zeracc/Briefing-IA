from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import auth_router, login_router, videos_router, recomendations_router
from app.routers.upload import router as upload_router

app = FastAPI(title="Backend Supabase + FFmpeg")

# Permitir o front (Vite) acessar o backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000"
    ],
    allow_credentials=True,   # 🔥 ESSENCIAL PARA LOGIN / COOKIES
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inclui as rotas
app.include_router(auth_router.router, prefix="/api/auth", tags=["Auth"])
app.include_router(videos_router.router, prefix="/api/videos", tags=["Videos"])
app.include_router(login_router.router, prefix="/api/login", tags=["Login"])
app.include_router(recomendations_router.router,
                   prefix="/api", tags=["Recommendations"])
app.include_router(upload_router)


@app.get("/")
def root():
    return {"message": "🚀 API rodando!"}
