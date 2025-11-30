import json  # <--- Garanta que isso está importado no topo
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

# ... (Seus imports e configurações do client OpenAI continuam iguais)


def transcribe_audio(audio_path: str):
    """
    Usa o Whisper-1 para transcrever o áudio.
    """
    # Debug: Tamanho do arquivo
    tamanho_mb = os.path.getsize(audio_path) / (1024 * 1024)
    print(f"📡 [IA] Iniciando upload para OpenAI... ({tamanho_mb:.2f} MB)")
    print("⏳ [IA] Aguarde, isso depende da sua internet...")

    try:
        with open(audio_path, "rb") as audio_file:
            transcript = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                response_format="verbose_json"
            )
        print("✅ [IA] Resposta recebida da OpenAI!")
        return transcript

    except Exception as e:
        print(f"❌ [IA] Erro na conexão com OpenAI: {e}")
        raise e

# ... (Sua função gerar_recomendacoes continua igual)


def gerar_recomendacoes(transcricao: str):
    """
    Recebe o texto da transcrição e retorna uma lista de recomendações.
    """

    # ... (seu prompt continua igual) ...
    prompt = f"""
TAREFA PRINCIPAL:
Com base na transcrição e no vídeo enviado, gere um roteiro completo e estruturado de edição. Você deve produzir ações de edição ultra claras, com timestamps exatos, B-roll sugerido, cortes, trilhas sonoras, recortes e marcadores. Não invente conteúdo que não exista no vídeo.

Você é um Editor IA profissional, especializado em análise de vídeo. Sua tarefa é transformar a transcrição em um conjunto de instruções objetivas que possam ser executadas diretamente por um editor humano ou automático.

A transcrição é:
---
{transcricao}
---

RETORNO (FORMATO OBRIGATÓRIO):
Retorne exclusivamente uma LISTA JSON onde cada item representa uma ação de edição do vídeo.

Cada item deve seguir rigorosamente este formato:

[
  {{
    "timestamp_seconds": 12.4,
    "tag": "curto título da ação (ex: Inserir B-roll, Cortar pausa, Início do Hook...)",
    "description": "descrição completa da ação, incluindo: identificação da parte (Hook, Intro, Desenvolvimento, Conclusão); ação detalhada de edição; timestamps de entrada e saída; sugestões de B-roll (até 3 links); sugestão de música (se aplicável); emoção detectada (se aplicável); instruções de thumbnail quando aplicável; instruções de recorte para redes sociais (se aplicável).",
    "confidence": 0.85
  }}
]

TODOS os comandos de edição devem aparecer como itens separados na lista, em ordem cronológica.

NÃO INCLUA:
- explicações
- texto fora do JSON
- comentários
- formatação markdown

Somente retorne o JSON puro.
"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",  # Confirmando o modelo correto
        messages=[{"role": "user", "content": prompt}]
    )

    # Conteúdo retornado pelo modelo
    content = response.choices[0].message.content

    # --- CORREÇÃO: LIMPEZA DO MARKDOWN ---
    # A IA às vezes responde com ```json [dados] ```. Vamos remover isso.
    if "```json" in content:
        content = content.replace("```json", "").replace("```", "")
    elif "```" in content:
        content = content.replace("```", "")

    content = content.strip()  # Remove espaços em branco do começo e fim
    # -------------------------------------

    # Converte JSON string → Python
    import json
    try:
        parsed = json.loads(content)
        return parsed
    except Exception as e:
        print("❌ Erro ao converter resposta da IA em JSON:")
        print(content)  # Mostra o que chegou para debug
        raise e
