from fastapi import APIRouter, status, HTTPException
from fastapi.responses import JSONResponse
from app.services.supabase_client import supabase
from pydantic import BaseModel

router = APIRouter()


class SignRequest(BaseModel):
    email: str
    password: str
    full_name: str | None = None


@router.post("/signup")
async def criar_conta(sign: SignRequest):
    """Cria uma nova conta no Supabase.

    Retornos:
    - 201 Created: conta criada com sucesso
    - 400 Bad Request: erro de validação/registro (ex.: email já existente)
    - 500 Internal Server Error: erro inesperado
    """
    try:
        response = supabase.auth.sign_up(
            {
                "email": sign.email,
                "password": sign.password,
                "data": {"full_name": sign.full_name},
            }
        )

        # suporto diferentes formatos de retorno do client
        user_email = None
        if hasattr(response, "user") and getattr(response, "user"):
            user_obj = getattr(response, "user")
            user_email = getattr(user_obj, "email", None)
        elif isinstance(response, dict):
            user = response.get("user")
            if isinstance(user, dict):
                user_email = user.get("email")

        # checar se há erro retornado
        error = None
        if hasattr(response, "error"):
            error = getattr(response, "error")
        elif isinstance(response, dict):
            error = response.get("error")

        if error:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error))

        if not user_email:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Sign up failed")

        return JSONResponse(status_code=status.HTTP_201_CREATED, content={"status": "ok", "user": user_email})

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))