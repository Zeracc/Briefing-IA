import os
from dotenv import load_dotenv
from openai import OpenAI

# carrega variáveis do .env (se existir)
load_dotenv()

_OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not _OPENAI_API_KEY:
    raise RuntimeError(
        "OPENAI_API_KEY não definido. Defina a variável de ambiente OPENAI_API_KEY ou adicione-a ao arquivo .env"
    )

client = OpenAI(api_key=_OPENAI_API_KEY)

def gerar_recomendacoes(transcricao: str):
    """
    Recebe o texto da transcrição e retorna uma lista de recomendações
    para serem inseridas na tabela 'recommendations'.
    """

    prompt = f"""
    Você é um sistema de análise de vídeos. 
    Leia a transcrição abaixo e gere recomendações estruturadas.

    A transcrição é:
    ---
    {transcricao}
    ---

    Gere uma lista JSON com recomendações no formato:
    [
        {{
            "timestamp_seconds": número,
            "tag": "curto título da ação",
            "description": "descrição completa da ação recomendada",
            "confidence": número entre 0 e 1
        }}
    ]

    Não inclua explicações, apenas o JSON puro.
    """

    response = client.chat.completions.create(
        model="gpt-4.1-mini",  # pode trocar
        messages=[{"role": "user", "content": prompt}]
    )

    # Conteúdo retornado pelo modelo
    content = response.choices[0].message.content

    # Converte JSON string → Python
    import json
    try:
        parsed = json.loads(content)
    except:
        print("❌ Erro ao converter resposta da IA em JSON:")
        print(content)
        raise

    return parsed
