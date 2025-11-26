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
        try:
            response = supabase.auth.sign_up(
                {
                    "email": sign.email,
                    "password": sign.password,
                    "data": {"full_name": sign.full_name},
                }
            )
        except Exception as inner_exc:
            # log the exception locally for debugging and raise a clear HTTP error
            print("Signup failed - supabase.auth.sign_up exception:", repr(inner_exc))
            # print more diagnostic info if available
            try:
                print("inner_exc.args:", inner_exc.args)
            except Exception:
                pass
            # some exceptions from underlying http clients may expose a response
            for attr in ("response", "httpx_response", "res", "resp"):
                try:
                    val = getattr(inner_exc, attr, None)
                    if val is not None:
                        print(f"inner_exc.{attr}:", repr(val))
                        # try to print text/body if available
                        body = getattr(val, "text", None) or getattr(val, "content", None)
                        if body:
                            print(f"inner_exc.{attr}.body:", body)
                except Exception:
                    pass

            # If the client provided a message, include it concisely
            msg = str(inner_exc)
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=(msg or "Database error saving new user"))

        # suporto diferentes formatos de retorno do client
        user_email = None
        user_id = None
        if hasattr(response, "user") and getattr(response, "user"):
            user_obj = getattr(response, "user")
            user_email = getattr(user_obj, "email", None)
            user_id = getattr(user_obj, "id", None)
        elif isinstance(response, dict):
            user = response.get("user")
            if isinstance(user, dict):
                user_email = user.get("email")
                user_id = user.get("id")

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

        # tenta criar/atualizar um profile no servidor (idempotente, não bloqueia o signup se falhar)
        try:
            if user_id:
                # tenta obter o plan_id do plano básico (slug = 'basic') para atribuir ao novo usuário
                default_plan_id = None
                try:
                    plan_resp = supabase.table("plans").select("id").eq("slug", "basic").maybe_single().execute()
                    plan_data = None
                    if isinstance(plan_resp, dict):
                        plan_data = plan_resp.get("data")
                    else:
                        plan_data = getattr(plan_resp, "data", None)
                    if plan_data:
                        if isinstance(plan_data, dict):
                            default_plan_id = plan_data.get("id")
                        else:
                            default_plan_id = getattr(plan_data, "id", None)
                except Exception as e:
                    print("Failed to fetch default plan id (non-fatal):", repr(e))

                profile_payload = {"id": user_id, "username": None, "full_name": sign.full_name}
                if default_plan_id:
                    profile_payload["plan_id"] = default_plan_id
                # usar upsert para ser idempotente (se já existir, atualiza; senão, insere)
                try:
                    res = supabase.table("profiles").upsert(profile_payload).execute()
                except AttributeError:
                    # fallback caso a versão do client não exponha `upsert`
                    res = supabase.table("profiles").insert(profile_payload).execute()

                # log resumido para debugging
                data = None
                err = None
                if isinstance(res, dict):
                    data = res.get("data")
                    err = res.get("error")
                else:
                    data = getattr(res, "data", None)
                    err = getattr(res, "error", None)

                print("Profile upsert response (short):", data)
                if err:
                    print("Profile upsert error (non-fatal):", err)
        except Exception as e:
            # log e segue em frente — não aborta o signup
            print("Profile upsert failed (non-fatal):", repr(e))

        return JSONResponse(status_code=status.HTTP_201_CREATED, content={"status": "ok", "user": user_email, "user_id": user_id})

    except HTTPException:
        raise
    except Exception as e:
        # Log unexpected errors and return uma mensagem concisa
        print("Unhandled exception in signup handler:", repr(e))
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database error saving new user")