from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from app.services.supabase_client import supabase

router = APIRouter(prefix="/login")

class LoginRequest(BaseModel):
    email: str
    password: str

@router.post("/")
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

        # tenta extrair token de sessão (access_token) e id do usuário para retornar ao cliente
        access_token = None
        user_id = None
        # vários formatos possíveis do client/supabase-py
        if isinstance(response, dict):
            # forma comum: {'data': {'user': {...}, 'session': {...}}, 'error': None}
            data = response.get("data") or {}
            session = response.get("session") or data.get("session") or data.get("session")
            if isinstance(session, dict):
                access_token = session.get("access_token") or session.get("accessToken")

            # fallbacks: alguns clientes colocam token em data direto
            # tenta extrair user id de vários lugares onde pode aparecer
            user = response.get("user") or data.get("user") or data.get("session") and data.get("session").get("user")
            if isinstance(user, dict):
                user_id = user.get("id") or user.get("user_id")

            if not access_token:
                access_token = data.get("access_token") or response.get("access_token")
                # ou em data['session']['access_token']
                if not access_token and isinstance(data.get("session"), dict):
                    access_token = data["session"].get("access_token") or data["session"].get("accessToken")
                # como fallback, user id também pode estar em data['session']['user']
                if not user_id and isinstance(data.get("session"), dict):
                    user_id = data["session"].get("user", {}).get("id")
        else:
            # objeto com atributos (algumas versões do client)
            session = getattr(response, "session", None)
            if session:
                access_token = getattr(session, "access_token", None) or getattr(session, "accessToken", None)
                # objeto session.user
                user_obj = getattr(session, "user", None)
                if user_obj:
                    user_id = getattr(user_obj, "id", None) or getattr(user_obj, "user_id", None)

            # também pode haver response.user direto
            if not user_id:
                user_obj = getattr(response, "user", None)
                if user_obj:
                    user_id = getattr(user_obj, "id", None) or getattr(user_obj, "user_id", None)

        return {"status": "ok", "user": user_email, "user_id": user_id, "access_token": access_token}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
