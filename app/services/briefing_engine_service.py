import os
import json
from openai import OpenAI
from dotenv import load_dotenv

from app.services.ai_services import _build_visual_inputs
from app.models.video_briefing_model import VideoBriefingResult

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise RuntimeError("OPENAI_API_KEY nao definido no ambiente.")

# Usa modelo o1/gpt-4o se existir para maior capacidade analítica
RECOMMENDATION_MODEL = os.getenv("OPENAI_RECOMMENDATION_MODEL", "gpt-4o-mini")

client = OpenAI(api_key=OPENAI_API_KEY)

def generate_video_briefing(transcricao: str, frame_paths: list[str] | None = None) -> VideoBriefingResult:
    schema_json = VideoBriefingResult.model_json_schema()
    
    prompt = f"""
Você é um MASTER EDITOR e PRODUTOR DE CONTEÚDO para redes sociais (TikTok, Reels, Shorts).
Sua missão é atuar como um "assistente de análise e recomendação de edição".

O objetivo do produto NÃO É editar o vídeo, mas sim entregar um BRIEFING INTELIGENTE de edição
que orientará a montagem final em ferramentas como CapCut ou Premiere.

Sua saída deve ser uma análise de alta performance com recomendações estratégicas de retenção, narrativa, cortes e ritmo.

ENTRADAS DO VÍDEO:
TRANSCRICAO:
---
{transcricao}
---

INSTRUÇÕES ESTRATÉGICAS:
1. Analise o contexto geral (público alvo, objetivo do vídeo, tom).
2. Identifique momentos de alta retenção (momentos de ouro, ganchos).
3. Seja EXTREMAMENTE criterioso com cortes: identifique silêncios aparentes ou partes desconexas para cortar.
4. Sugira B-Rolls dinâmicos baseados no contexto da fala (detalhados, guiando o editor sobre "o que mostrar").
5. OBRIGATÓRIO: Cobre extrema precisão nos tempos ('start' e 'end' em formatos numéricos/float, baseando-se nas chaves de tempo que enviei). NÃO REPITA TIMESTAMP '0.0' PARA TUDO! Use os segundos REAIS correspondentes à fala!
6. Não repita a transcrição como resumo. Faça algo analítico e acionável.
7. Aja como especialista. Não devolva ideias genéricas como "ponha musiquinha". Diga "Trilha rápida com batidas fortes para enfatizar urgência".

OBRIGATÓRIO:
Você deve retornar ESTRITAMENTE um objeto JSON válido, aderente ao esquema JSON a seguir.
Não retorne nada além do JSON (sem formatação markdown fora de controle).

SCHEMA JSON OBRIGATÓRIO:
{json.dumps(schema_json, indent=2)}
"""

    content: list[dict] = [{"type": "text", "text": prompt}]
    
    # Anexar as imagens como contexto
    visual_inputs = _build_visual_inputs(frame_paths) if frame_paths else []
    content.extend(visual_inputs)

    print(f"[BriefingEngine] Iniciando geracao. Transcricao: {len(transcricao)} chars, Frames: {len(visual_inputs)}, Model: {RECOMMENDATION_MODEL}")

    response = client.chat.completions.create(
        model=RECOMMENDATION_MODEL,
        messages=[{"role": "user", "content": content}],
        response_format={"type": "json_object"}
    )

    raw_content = response.choices[0].message.content or ""
    
    try:
        parsed_dict = json.loads(raw_content)
        result = VideoBriefingResult(**parsed_dict)
        print("[BriefingEngine] Geracao bem-sucedida e Pydantic validado.")
        return result
    except Exception as exc:
        print("[BriefingEngine] Falha ao parsear JSON no Pydantic:", exc, "Raw Content:", raw_content[:500])
        raise RuntimeError(f"Erro ao processar JSON da OpenAI no Pydantic: {exc}") from exc
