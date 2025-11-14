from supabase import create_client, Client

# --- CONFIGURAÇÕES DO SEU PROJETO ---
SUPABASE_URL = "https://ylugeisisejxkhxawzlh.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InlsdWdlaXNpc2VqeGtoeGF3emxoIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2MjE3MzQ5NywiZXhwIjoyMDc3NzQ5NDk3fQ.zOf53I2QPtsw5HF5o81vEo5rQHDwXEYYNk13atRLDSM"

# --- CONEXÃO ---
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
print("✅ Conectado ao Supabase com sucesso!")

# --- TESTE DE INSERÇÃO ---
video_data = {
    "user_id": "63b970c6-3a2f-4105-82da-2fd6b38b94d5",
    "title": "Vídeo para deletar 3 rsrs",
    "original_url": "teste de deleção somente de usuário autenticado 3"
}

try:
    response = supabase.table("videos").insert(video_data).execute()

    # A nova versão da lib retorna um objeto APIResponse com .data e .error
    if response.data:
        print("✅ Inserção realizada com sucesso!")
        print("📦 Dados retornados:", response.data)
    elif response.error:
        print("⚠️ Erro retornado pelo Supabase:", response.error)
    else:
        print("⚠️ Nenhuma resposta de dados recebida.")

except Exception as e:
    print("❌ Erro ao inserir:", e)
