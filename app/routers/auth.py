from fastapi import APIRouter, Request
from app.services.supabase_client import supabase

router = APIRouter()


@router.post("/signup")
async def criar_conta(request: Request):
    data = await request.json()
    email = data.get("email")
    password = data.get("password")  # 👈 alteração aqui
    full_name = data.get("full_name")  # opcional, se quiser salvar no metadata

    try:
        response = supabase.auth.sign_up(
            {
                "email": email,
                "password": password,
                "data": {"full_name": full_name}  # salva no user_metadata
            }
        )
        return {
            "status": "ok",
            "user": response.user.email if response.user else None
        }
    except Exception as e:
        return {"status": "error", "detail": str(e)}