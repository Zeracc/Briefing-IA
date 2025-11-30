-- Migration: 0002_add_slug_to_plans.sql
-- Adds a `slug` column to public.plans, populates it from name for existing rows,
-- ensures uniqueness by appending a short id fragment to duplicates, and creates
-- a unique index on slug.

BEGIN;

-- 1) add column if missing
ALTER TABLE public.plans
  ADD COLUMN IF NOT EXISTS slug text;

-- 2) populate slug for rows where it's null: slugify the name (lowercase, non-alnum -> '-')
UPDATE public.plans
SET slug = lower(regexp_replace(coalesce(name, ''), '[^a-z0-9]+', '-', 'gi'))
WHERE slug IS NULL;

-- 3) fix duplicates, if any, by appending a short id fragment to make slugs unique
WITH dup AS (
  SELECT slug FROM public.plans GROUP BY slug HAVING COUNT(*) > 1
)
UPDATE public.plans p
SET slug = p.slug || '-' || substring(p.id::text, 1, 8)
FROM dup
WHERE p.slug = dup.slug;

-- 4) create a unique index on slug if it doesn't already exist
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace
    WHERE c.relkind = 'i' AND c.relname = 'idx_plans_slug_unique'
  ) THEN
    EXECUTE 'CREATE UNIQUE INDEX idx_plans_slug_unique ON public.plans (slug)';
  END IF;
END$$;

COMMIT;

-- Notes:
-- - Run this migration in Supabase SQL editor or via your normal migration tooling.
-- - If you prefer a NOT NULL constraint on slug, add it after verifying there are no NULL slugs:
--     ALTER TABLE public.plans ALTER COLUMN slug SET NOT NULL;
-- - The migration intentionally avoids failing if duplicates exist by appending a short id fragment.
-- - After this migration you can safely query plans by `slug` (e.g. WHERE slug = 'basic').
