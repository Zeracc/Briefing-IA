from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from supabase import create_client
import os

router = APIRouter()

# =====================
# Schemas
# =====================
class SignupSchema(BaseModel):
    email: str
    password: str
    full_name: str | None = None


@router.post("/signup")
def signup(data: SignupSchema):
    supabase = create_client(
        os.getenv("SUPABASE_URL"),
        os.getenv("SUPABASE_ANON_KEY")
    )

    result = supabase.auth.sign_up({
        "email": data.email,
        "password": data.password,
        "options": {
            "data": {
                "full_name": data.full_name
            }
        }
    })

    if not result.user:
        raise HTTPException(status_code=400, detail="Erro ao criar usuário")

    return {
        "id": result.user.id,
        "email": result.user.email
    }
