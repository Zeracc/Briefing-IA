import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()  # carrega .env


SUPABASE_URL = "https://ylugeisisejxkhxawzlh.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InlsdWdlaXNpc2VqeGtoeGF3emxoIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2MjE3MzQ5NywiZXhwIjoyMDc3NzQ5NDk3fQ.zOf53I2QPtsw5HF5o81vEo5rQHDwXEYYNk13atRLDSM"

if not SUPABASE_URL or not SUPABASE_KEY:
    raise RuntimeError("Defina SUPABASE_URL e SUPABASE_KEY no .env")


supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

