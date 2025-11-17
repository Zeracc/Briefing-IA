from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.services.supabase_client import supabase

router = APIRouter()


class LoginRequest(BaseModel):
    email: str
    password: str


@router.post("/loged")
async def login_account(data: LoginRequest):

    try:
        response = supabase.auth.sign_in_with_password({
            "email": data.email,
            "password": data.password,
        })

        if not response.user:
            raise HTTPException(
                status_code=401, detail="Credenciais inválidas")

        return {
            "status": "ok",
            "user": response.user.email
        }

    except Exception:
        raise HTTPException(status_code=401, detail="Credenciais inválidas")
