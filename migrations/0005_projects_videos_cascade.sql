-- Cascade de exclusao entre projetos/videos/transcriptions/recommendations.
-- Objetivo:
-- 1) ao excluir project, remover videos vinculados;
-- 2) ao excluir video, remover transcriptions/recommendations vinculadas.

begin;

alter table if exists public.videos
  drop constraint if exists videos_project_id_fkey;

alter table if exists public.videos
  add constraint videos_project_id_fkey
  foreign key (project_id)
  references public.projects(id)
  on delete cascade;

alter table if exists public.transcriptions
  drop constraint if exists transcriptions_video_id_fkey;

alter table if exists public.transcriptions
  add constraint transcriptions_video_id_fkey
  foreign key (video_id)
  references public.videos(id)
  on delete cascade;

alter table if exists public.recommendations
  drop constraint if exists recommendations_video_id_fkey;

alter table if exists public.recommendations
  add constraint recommendations_video_id_fkey
  foreign key (video_id)
  references public.videos(id)
  on delete cascade;

create index if not exists idx_videos_project_id
  on public.videos(project_id);

create index if not exists idx_transcriptions_video_id
  on public.transcriptions(video_id);

create index if not exists idx_recommendations_video_id
  on public.recommendations(video_id);

commit;
