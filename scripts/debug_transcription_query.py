from supabase import create_client
from dotenv import load_dotenv
import os

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

video_id = "b5897d11-1b37-473a-b5b5-17a71a8f6608"

resp = supabase.table("transcriptions") \
    .select("*") \
    .eq("video_id", video_id) \
    .maybe_single() \
    .execute()

print("data:", resp.data)
print("error:", resp.error)
