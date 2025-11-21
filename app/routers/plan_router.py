from fastapi import APIRouter, Depends
from app.services.supabase_client import supabase
from app.services.auth import get_current_user

router = APIRouter(prefix="/plans")

@router.get("/")
def list_plans():
    return supabase.table("plans").select("*").execute().data

@router.post("/change")
def change_plan(data: dict, user=Depends(get_current_user)):
    plan_id = data["plan_id"]

    supabase.table("profiles").update({"plan_id": plan_id}).eq("id", user.id).execute()

    return {"status": "ok", "message": "Plano atualizado"}
