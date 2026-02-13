-- RLS policies and optional trigger for public.videos
-- Goal: allow safe insert by owner and enforce project ownership

alter table public.videos enable row level security;

-- Drop old/duplicate policies if they exist
drop policy if exists "Users can view their own videos" on public.videos;
drop policy if exists "Users can delete their own videos" on public.videos;
drop policy if exists "Users can update their own videos" on public.videos;
drop policy if exists "Users can insert their own videos" on public.videos;
drop policy if exists "videos_select_own" on public.videos;
drop policy if exists "videos_insert_own" on public.videos;
drop policy if exists "videos_update_own" on public.videos;
drop policy if exists "videos_delete_own" on public.videos;

-- SELECT: owner only
create policy "videos_select_own"
  on public.videos
  for select
  to authenticated
  using (auth.uid() = user_id);

-- INSERT: owner only + project must belong to same owner (if provided)
create policy "videos_insert_own"
  on public.videos
  for insert
  to authenticated
  with check (
    auth.uid() = user_id
    and (
      project_id is null
      or exists (
        select 1
        from public.projects p
        where p.id = project_id
          and p.user_id = auth.uid()
      )
    )
  );

-- UPDATE: owner only + keep ownership + project ownership constraint
create policy "videos_update_own"
  on public.videos
  for update
  to authenticated
  using (auth.uid() = user_id)
  with check (
    auth.uid() = user_id
    and (
      project_id is null
      or exists (
        select 1
        from public.projects p
        where p.id = project_id
          and p.user_id = auth.uid()
      )
    )
  );

-- DELETE: owner only
create policy "videos_delete_own"
  on public.videos
  for delete
  to authenticated
  using (auth.uid() = user_id);

-- Option B (recommended if you do NOT want frontend to send user_id):
-- Update enforce_video_project_owner() to also set user_id = auth.uid()
-- when project_id is null. This keeps ownership consistent without relying
-- on frontend-sent user_id.
create or replace function public.enforce_video_project_owner()
returns trigger
language plpgsql
as $$
declare
  v_owner uuid;
begin
  if new.user_id is null then
    new.user_id := auth.uid();
  end if;

  if new.project_id is null then
    return new;
  end if;

  select user_id into v_owner from public.projects where id = new.project_id;

  if v_owner is null then
    raise exception 'Project not found';
  end if;

  if new.user_id <> v_owner then
    raise exception 'Video owner mismatch with project owner';
  end if;

  return new;
end;
$$;

drop trigger if exists trg_enforce_video_project_owner on public.videos;
create trigger trg_enforce_video_project_owner
before insert or update on public.videos
for each row
execute function public.enforce_video_project_owner();
