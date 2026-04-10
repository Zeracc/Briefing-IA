from pydantic import BaseModel, Field
from typing import List, Literal, Optional

class RecommendedStructureItem(BaseModel):
    section: str = Field(description="Ex: Hook, Problem, Solution, CTA")
    objective: str = Field(description="O objetivo emocional ou lógico dessa seção")
    recommended_time_range: str = Field(description="Faixa de tempo em segundos. Ex: '0-15s'")
    editing_guidance: str = Field(description="Instruções práticas de edição de imagem e áudio")
    suggested_script_adjustment: str = Field(description="Adaptação ou melhoria sugerida no roteiro para aumentar impacto")

class HighlightMoment(BaseModel):
    start: float = Field(description="Tempo inicial em segundos")
    end: float = Field(description="Tempo final em segundos")
    reason: str = Field(description="Por que esse momento é um destaque (força comercial, emocional, etc.)")
    impact_score: int = Field(description="Score de impacto de 1 a 10")

class CutRecommendation(BaseModel):
    start: float
    end: float
    reason: str = Field(description="Motivo do corte (ex: silêncio, erro, divagação, repetição)")
    priority: Literal["low", "medium", "high"] = Field(description="Prioridade do corte. High significa que prejudica a retenção imediatamente")

class BRollRecommendation(BaseModel):
    time_range: str = Field(description="Ex: '10s a 15s'")
    start: float = Field(description="Tempo inicial EXATO em segundos do b-roll. Ex: 10.0")
    end: float = Field(description="Tempo final EXATO em segundos. Ex: 15.0")
    suggestion: str = Field(description="Sugestão visual extremamente detalhada")
    reason: str = Field(description="Por que usar esse B-roll")

class CaptionRecommendation(BaseModel):
    time_range: str = Field(description="Ex: '10s a 15s'")
    start: float = Field(description="Tempo inicial EXATO em segundos")
    end: float = Field(description="Tempo final EXATO em segundos")
    text_style: str = Field(description="Estilo da legenda")
    reason: str

class VideoBriefingResult(BaseModel):
    summary: str = Field(description="Resumo do vídeo")
    video_goal: str = Field(description="Objetivo principal (ex: venda, autoridade, entretenimento, explicação, depoimento)")
    target_audience: str = Field(description="Público-alvo estimado bem específico")
    tone_analysis: str = Field(description="Tom da fala predominante: emocional, técnico, comercial, urgente, natural, etc")
    content_strengths: List[str] = Field(description="Pontos fortes do vídeo (Mínimo 2)")
    content_weaknesses: List[str] = Field(description="Pontos fracos ou oportunidades de melhoria (Mínimo 2)")
    recommended_structure: List[RecommendedStructureItem] = Field(description="Estruturação em blocos do vídeo reeditado.")
    highlight_moments: List[HighlightMoment] = Field(description="Momentos de ouro do vídeo, ideais para shorts ou anúncios")
    cut_recommendations: List[CutRecommendation] = Field(description="Cortes sugeridos para melhorar retenção")
    broll_recommendations: List[BRollRecommendation] = Field(description="Imagens de cobertura recomendadas")
    caption_recommendations: List[CaptionRecommendation] = Field(description="Sugestões dinâmicas de legenda/lettering")
    cta_recommendation: str = Field(description="Uma sugestão extra ou melhoria da Chamada Para Ação")
    title_suggestions: List[str] = Field(description="Sugestões de títulos virais")
    thumbnail_suggestions: List[str] = Field(description="Sugestões de arte e hook visual para thumbnail")
    editor_notes: List[str] = Field(description="Conselhos gerais práticos da perspectiva de um master editor de redes sociais")
