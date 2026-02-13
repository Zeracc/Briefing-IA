-- Storage policies for videos bucket
-- Enforce user isolation by folder: {auth.uid()}/...

alter table storage.objects enable row level security;

create policy "Videos objects are readable by owner"
    on storage.objects
    for select
    using (
        bucket_id = 'videos'
        and auth.uid()::text = (storage.foldername(name))[1]
    );

create policy "Videos objects are insertable by owner"
    on storage.objects
    for insert
    with check (
        bucket_id = 'videos'
        and auth.uid()::text = (storage.foldername(name))[1]
    );

create policy "Videos objects are deletable by owner"
    on storage.objects
    for delete
    using (
        bucket_id = 'videos'
        and auth.uid()::text = (storage.foldername(name))[1]
    );

create policy "Videos objects are updatable by owner"
    on storage.objects
    for update
    using (
        bucket_id = 'videos'
        and auth.uid()::text = (storage.foldername(name))[1]
    )
    with check (
        bucket_id = 'videos'
        and auth.uid()::text = (storage.foldername(name))[1]
    );