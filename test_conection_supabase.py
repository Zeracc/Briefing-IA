from supabase import create_client, Client
from dotenv import load_dotenv
import os

load_dotenv()  # carrega .env

# --- CONFIGURAÇÕES DO SEU PROJETO ---
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

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
