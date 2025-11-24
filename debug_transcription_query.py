from app.services.supabase_client import supabase

video_id = "b5897d11-1b37-473a-b5b5-17a71a8f6608"  # ajuste aqui se quiser

resp = supabase.table("transcriptions").select("*").eq("video_id", video_id).maybe_single().execute()

print("RESPONSE OBJECT repr:", repr(resp))
print("type(resp):", type(resp))
print("data:", getattr(resp, "data", None))
print("error:", getattr(resp, "error", None))
print("status_code:", getattr(resp, "status_code", None))
try:
    print("as dict (if possible):", dict(resp))
except Exception:
    pass
