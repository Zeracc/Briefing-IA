from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from app.services.supabase_client import supabase

router = APIRouter()

class LoginRequest(BaseModel):
    email: str
    password: str

@router.post("/login")
async def login_account(payload: LoginRequest):
    try:
        response = supabase.auth.sign_in_with_password({
            "email": payload.email,
            "password": payload.password,
        })

        # Interpreta diferentes formatos de retorno do client
        error = None
        user_email = None

        if isinstance(response, dict):
            # supabase-py pode devolver {"data": {...}, "error": ...} ou {"user": ..., "error": ...}
            error = response.get("error") or (response.get("data") or {}).get("error")
            user = response.get("user") or response.get("data")
            if isinstance(user, dict):
                user_email = user.get("email")
        else:
            # objeto com atributos (algumas versões)
            error = getattr(response, "error", None)
            user_obj = getattr(response, "user", None)
            if user_obj:
                user_email = getattr(user_obj, "email", None)

        if error or not user_email:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(error or "Credenciais inválidas"))

        return {"status": "ok", "user": user_email}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))