from fastapi import APIRouter, Depends
from app.services.dependencies import get_supabase_user

router = APIRouter(prefix="/plans", tags=["Plans"])

# =====================
# LIST PLANS (PUBLIC)
# =====================
@router.get("/")
def list_plans(
    supabase=Depends(get_supabase_user),
):
    return (
        supabase
        .table("plans")
        .select("*")
        .execute()
        .data
    )

# =====================
# CHANGE PLAN (RLS SAFE)
# =====================
@router.post("/change")
def change_plan(
    data: dict,
    supabase=Depends(get_supabase_user),
):
    response = (
        supabase
        .table("profiles")
        .update({"plan_id": data["plan_id"]})
        .execute()
    )

    return {
        "status": "ok",
        "updated": response.data
    }


@router.post("/plans/upgrade")
def upgrade_plan(
    data: dict,
    supabase=Depends(get_supabase_user)
):
    supabase.table("profiles") \
        .update({"plan_id": data["plan_id"]}) \
        .execute()

    return {"status": "ok"}


