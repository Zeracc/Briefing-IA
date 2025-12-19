from fastapi import APIRouter, Depends
from app.services.dependencies import get_supabase_user
from app.services.auth import get_current_user

router = APIRouter(prefix="/plans")

@router.get("/")
def list_plans(supabase=Depends(get_supabase_user)):
    return supabase.table("plans").select("*").execute().data

@router.post("/change")
def change_plan(
    data: dict,
    user=Depends(get_current_user),
    supabase=Depends(get_supabase_user)
):
    supabase.table("profiles") \
        .update({"plan_id": data["plan_id"]}) \
        .eq("id", user.id) \
        .execute()

    return {"status": "ok"}
