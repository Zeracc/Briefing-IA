-- Migration: Create video_briefings table
-- This table stores the unified structured JSON from the Briefing AI, providing advanced analytics per video.

CREATE TABLE IF NOT EXISTS public.video_briefings (
    id uuid DEFAULT gen_random_uuid() PRIMARY KEY,
    video_id uuid NOT NULL REFERENCES public.videos(id) ON DELETE CASCADE,
    content jsonb NOT NULL,
    created_at timestamp with time zone DEFAULT now()
);

-- Habilitar RLS (Row Level Security)
ALTER TABLE public.video_briefings ENABLE ROW LEVEL SECURITY;

-- Politica: Usuarios só podem ver os briefings de seus vídeos
CREATE POLICY "Users can view their own video briefings"
    ON public.video_briefings FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM public.videos
            WHERE videos.id = video_briefings.video_id
            AND videos.user_id = auth.uid()
        )
    );

-- Politica: Usuarios podem inserir briefings ref a vídeos que eles possuem
CREATE POLICY "Users can insert their own video briefings"
    ON public.video_briefings FOR INSERT
    WITH CHECK (
        EXISTS (
            SELECT 1 FROM public.videos
            WHERE videos.id = video_briefings.video_id
            AND videos.user_id = auth.uid()
        )
    );

-- Politica: Usuarios podem atualizar briefings ref a vídeos que eles possuem
CREATE POLICY "Users can update their own video briefings"
    ON public.video_briefings FOR UPDATE
    USING (
        EXISTS (
            SELECT 1 FROM public.videos
            WHERE videos.id = video_briefings.video_id
            AND videos.user_id = auth.uid()
        )
    );

-- Politica: Usuarios podem deletar briefings ref a vídeos que eles possuem
CREATE POLICY "Users can delete their own video briefings"
    ON public.video_briefings FOR DELETE
    USING (
        EXISTS (
            SELECT 1 FROM public.videos
            WHERE videos.id = video_briefings.video_id
            AND videos.user_id = auth.uid()
        )
    );
