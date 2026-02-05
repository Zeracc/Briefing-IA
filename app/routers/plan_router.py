from fastapi import APIRouter, Depends, HTTPException
from app.services.supabase_client import supabase, get_supabase_client
from app.services.auth import get_current_user, get_access_token, get_user_id

router = APIRouter(prefix="/plans")


@router.get("/")
def list_plans():
    return supabase.table("plans").select("*").execute().data


@router.post("/change")
def change_plan(data: dict, user=Depends(get_current_user), token=Depends(get_access_token)):
    plan_id = data["plan_id"]
    user_id = get_user_id(user)
    if not user_id:
        raise HTTPException(status_code=401, detail="Token invalido")

    client = get_supabase_client(token)
    client.table("profiles").update({"plan_id": plan_id}).eq("id", user_id).execute()

    return {"status": "ok", "message": "Plano atualizado"}
