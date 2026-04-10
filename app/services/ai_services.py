import base64
import json
import os

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise RuntimeError(
        "OPENAI_API_KEY nao definido. Configure OPENAI_API_KEY no ambiente."
    )

RECOMMENDATION_MODEL = os.getenv("OPENAI_RECOMMENDATION_MODEL", "gpt-4o-mini")
MAX_VISUAL_FRAMES = max(0, int(os.getenv("OPENAI_MAX_VISUAL_FRAMES", "6")))
MAX_VISUAL_FRAME_BYTES = max(
    200_000,
    int(os.getenv("OPENAI_MAX_VISUAL_FRAME_BYTES", str(2 * 1024 * 1024))),
)
VISUAL_IMAGE_DETAIL = os.getenv("OPENAI_VISUAL_IMAGE_DETAIL", "low")

client = OpenAI(api_key=OPENAI_API_KEY)


def transcribe_audio(audio_path: str):
    tamanho_mb = os.path.getsize(audio_path) / (1024 * 1024)
    print(f"[IA] transcription.start size_mb={tamanho_mb:.2f}")

    with open(audio_path, "rb") as audio_file:
        transcript = client.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file,
            response_format="verbose_json",
        )
    print("[IA] transcription.done")
    return transcript


def _image_to_data_url(path: str) -> str | None:
    if not path or not os.path.exists(path):
        return None
    with open(path, "rb") as handle:
        raw = handle.read()
    if not raw:
        return None
    if len(raw) > MAX_VISUAL_FRAME_BYTES:
        print(
            "[IA] frame.skip_too_large "
            f"path={path} bytes={len(raw)} max={MAX_VISUAL_FRAME_BYTES}"
        )
        return None
    extension = os.path.splitext(path)[1].lower()
    mime = "image/png" if extension == ".png" else "image/jpeg"
    encoded = base64.b64encode(raw).decode("utf-8")
    return f"data:{mime};base64,{encoded}"


def _build_visual_inputs(frame_paths: list[str] | None) -> list[dict]:
    if not frame_paths:
        return []
    visual_inputs: list[dict] = []
    for path in frame_paths[:MAX_VISUAL_FRAMES]:
        data_url = _image_to_data_url(path)
        if not data_url:
            continue
        visual_inputs.append(
            {
                "type": "image_url",
                "image_url": {
                    "url": data_url,
                    "detail": VISUAL_IMAGE_DETAIL,
                },
            }
        )
    return visual_inputs


def gerar_recomendacoes(transcricao: str, frame_paths: list[str] | None = None):
    prompt = f"""
TAREFA PRINCIPAL:
Com base na transcricao e nos snapshots do video, gere um roteiro completo e estruturado de edicao.
A intencao principal e criar um "briefing" rico e detalhado para a edicao de videos, melhorando significativamente a recomendacao de insercoes de "B-rolls" (imagens de cobertura) com base no contexto falado e visual.
Em vez de um B-roll "seco" e generico, forneca recomendacoes criativas e hiperdescritivas que guiem o editor em relacao a atmosfera visual, tipo de cena e acoes (ex: "B-roll de um cafe quente soltando vapor", em vez de apenas "B-roll de cafe").
Enriqueca o campo 'description' incluindo as sugestoes detalhadas do B-roll e a ambientacao de audio apropriada.

CONTEXTO:
- A transcricao vem do audio real do video.
- Os snapshots sao frames extraidos em intervalos maiores para dar contexto visual.

TRANSCRICAO:
---
{transcricao}
---

RETORNO OBRIGATORIO:
Retorne exclusivamente um array JSON.
Nao adicione chaves fora das estipuladas abaixo.
Cada item deve ter a exata estrutura:
[
  {{
    "timestamp_seconds": 12.4,
    "tag": "Corte/B-roll/Transicao/Efeito",
    "description": "Instrucao executavel e MUITO detalhada, incluindo movimento de camera sugerido, elementos da cena para o B-roll, e sugestoes sonoras (SFX/Trilha) que valorizam a marcacao.",
    "confidence": 0.85
  }}
]

Sem markdown. Sem texto fora do JSON.
"""

    content: list[dict] = [{"type": "text", "text": prompt}]
    visual_inputs = _build_visual_inputs(frame_paths)
    content.extend(visual_inputs)

    print(
        "[IA] recommendations.start "
        f"transcription_chars={len(transcricao or '')} snapshots={len(visual_inputs)} model={RECOMMENDATION_MODEL}"
    )

    response = client.chat.completions.create(
        model=RECOMMENDATION_MODEL,
        messages=[{"role": "user", "content": content}],
    )

    raw_content = response.choices[0].message.content or ""
    normalized = raw_content.strip()
    if normalized.startswith("```json"):
        normalized = normalized.replace("```json", "", 1).strip()
    if normalized.startswith("```"):
        normalized = normalized.replace("```", "", 1).strip()
    if normalized.endswith("```"):
        normalized = normalized[:-3].strip()

    try:
        parsed = json.loads(normalized)
    except Exception as exc:
        print("[IA] recommendations.parse_error", normalized)
        raise RuntimeError(f"Falha ao converter resposta da IA para JSON: {exc}") from exc

    print("[IA] recommendations.done")
    return parsed
