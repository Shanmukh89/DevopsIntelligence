BEGIN;

-- -----------------------------------------------------------------------------
-- EXTENSIONS
-- -----------------------------------------------------------------------------
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- -----------------------------------------------------------------------------
-- CLEAN SLATE: DROP POLICIES
-- -----------------------------------------------------------------------------
DO $$
DECLARE
  pol RECORD;
BEGIN
  FOR pol IN
    SELECT schemaname, tablename, policyname
    FROM pg_policies
    WHERE schemaname = 'public'
      AND tablename IN (
        'profiles',
        'github_installations',
        'repositories',
        'pull_requests',
        'pr_reviews',
        'builds',
        'vulnerabilities',
        'cloud_costs'
      )
  LOOP
    EXECUTE format('DROP POLICY IF EXISTS %I ON %I.%I', pol.policyname, pol.schemaname, pol.tablename);
  END LOOP;
END $$;

-- -----------------------------------------------------------------------------
-- CLEAN SLATE: DROP TRIGGER + FUNCTION
-- -----------------------------------------------------------------------------
DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
DROP FUNCTION IF EXISTS public.handle_new_user();

-- -----------------------------------------------------------------------------
-- CLEAN SLATE: DROP TABLES
-- -----------------------------------------------------------------------------
DROP TABLE IF EXISTS public.pr_reviews CASCADE;
DROP TABLE IF EXISTS public.pull_requests CASCADE;
DROP TABLE IF EXISTS public.builds CASCADE;
DROP TABLE IF EXISTS public.vulnerabilities CASCADE;
DROP TABLE IF EXISTS public.repositories CASCADE;
DROP TABLE IF EXISTS public.github_installations CASCADE;
DROP TABLE IF EXISTS public.cloud_costs CASCADE;
DROP TABLE IF EXISTS public.profiles CASCADE;

-- -----------------------------------------------------------------------------
-- CLEAN SLATE: DROP TYPES
-- -----------------------------------------------------------------------------
DROP TYPE IF EXISTS public.build_status CASCADE;
DROP TYPE IF EXISTS public.severity_level CASCADE;
DROP TYPE IF EXISTS public.audit_status CASCADE;

-- -----------------------------------------------------------------------------
-- TYPES
-- -----------------------------------------------------------------------------
CREATE TYPE public.build_status AS ENUM ('success', 'failure', 'running', 'cancelled');
CREATE TYPE public.severity_level AS ENUM ('critical', 'high', 'medium', 'low', 'info');
CREATE TYPE public.audit_status AS ENUM ('open', 'resolved', 'ignored');

-- -----------------------------------------------------------------------------
-- PROFILES
-- -----------------------------------------------------------------------------
CREATE TABLE public.profiles (
  id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
  first_name TEXT,
  last_name TEXT,
  email TEXT UNIQUE NOT NULL,
  avatar_url TEXT,
  github_username TEXT,
  auth_provider TEXT,
  provider_id TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc', now()),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc', now())
);

-- -----------------------------------------------------------------------------
-- GITHUB INSTALLATIONS
-- -----------------------------------------------------------------------------
CREATE TABLE public.github_installations (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  profile_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
  github_installation_id BIGINT NOT NULL UNIQUE,
  github_account_id BIGINT,
  github_account_login TEXT,
  github_account_type TEXT,
  target_type TEXT,
  app_slug TEXT,
  installed_by_github_user_id BIGINT,
  repository_selection TEXT DEFAULT 'selected',
  is_active BOOLEAN NOT NULL DEFAULT TRUE,
  created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc', now()),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc', now())
);

CREATE UNIQUE INDEX github_installations_profile_active_idx
ON public.github_installations(profile_id, github_installation_id);

-- -----------------------------------------------------------------------------
-- REPOSITORIES
-- -----------------------------------------------------------------------------
CREATE TABLE public.repositories (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  profile_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
  installation_id UUID REFERENCES public.github_installations(id) ON DELETE SET NULL,
  github_repo_id BIGINT UNIQUE,
  owner_login TEXT,
  name TEXT NOT NULL,
  full_name TEXT UNIQUE,
  url TEXT,
  provider TEXT NOT NULL DEFAULT 'github',
  default_branch TEXT DEFAULT 'main',
  language TEXT,
  is_private BOOLEAN DEFAULT FALSE,
  is_active BOOLEAN DEFAULT TRUE,
  last_synced_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc', now()),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc', now())
);

CREATE INDEX repositories_profile_id_idx ON public.repositories(profile_id);
CREATE INDEX repositories_installation_id_idx ON public.repositories(installation_id);

-- -----------------------------------------------------------------------------
-- BUILDS
-- -----------------------------------------------------------------------------
CREATE TABLE public.builds (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  repository_id UUID NOT NULL REFERENCES public.repositories(id) ON DELETE CASCADE,
  branch TEXT NOT NULL,
  commit_sha TEXT NOT NULL,
  commit_msg TEXT,
  status public.build_status NOT NULL DEFAULT 'running',
  duration_ms INTEGER,
  provider TEXT NOT NULL DEFAULT 'github_actions',
  created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc', now()),
  completed_at TIMESTAMPTZ
);

-- -----------------------------------------------------------------------------
-- VULNERABILITIES
-- -----------------------------------------------------------------------------
CREATE TABLE public.vulnerabilities (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  repository_id UUID NOT NULL REFERENCES public.repositories(id) ON DELETE CASCADE,
  package_name TEXT NOT NULL,
  cve_id TEXT,
  description TEXT,
  severity public.severity_level NOT NULL DEFAULT 'medium',
  installed_version TEXT,
  patched_version TEXT,
  status public.audit_status NOT NULL DEFAULT 'open',
  created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc', now()),
  resolved_at TIMESTAMPTZ
);

-- -----------------------------------------------------------------------------
-- PULL REQUESTS
-- -----------------------------------------------------------------------------
CREATE TABLE public.pull_requests (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  repository_id UUID NOT NULL REFERENCES public.repositories(id) ON DELETE CASCADE,
  github_pr_id BIGINT UNIQUE,
  pr_number INTEGER NOT NULL,
  title TEXT NOT NULL,
  author TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'open',
  created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc', now()),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc', now())
);

CREATE INDEX pull_requests_repository_id_idx ON public.pull_requests(repository_id);

-- -----------------------------------------------------------------------------
-- PR REVIEWS
-- -----------------------------------------------------------------------------
CREATE TABLE public.pr_reviews (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  pull_request_id UUID NOT NULL REFERENCES public.pull_requests(id) ON DELETE CASCADE,
  issues_found INTEGER DEFAULT 0,
  severity public.severity_level NOT NULL DEFAULT 'low',
  summary_text TEXT,
  reviewed_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc', now())
);

-- -----------------------------------------------------------------------------
-- CLOUD COSTS
-- -----------------------------------------------------------------------------
CREATE TABLE public.cloud_costs (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  profile_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
  resource_id TEXT NOT NULL,
  resource_type TEXT NOT NULL,
  provider TEXT NOT NULL DEFAULT 'aws',
  potential_saving_monthly NUMERIC(10, 2) NOT NULL DEFAULT 0.00,
  recommendation TEXT NOT NULL,
  status public.audit_status NOT NULL DEFAULT 'open',
  created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc', now())
);

-- -----------------------------------------------------------------------------
-- UPDATED_AT TRIGGER FUNCTION
-- -----------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION public.set_updated_at()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
  NEW.updated_at = timezone('utc', now());
  RETURN NEW;
END;
$$;

CREATE TRIGGER set_profiles_updated_at
BEFORE UPDATE ON public.profiles
FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();

CREATE TRIGGER set_github_installations_updated_at
BEFORE UPDATE ON public.github_installations
FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();

CREATE TRIGGER set_repositories_updated_at
BEFORE UPDATE ON public.repositories
FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();

CREATE TRIGGER set_pull_requests_updated_at
BEFORE UPDATE ON public.pull_requests
FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();

-- -----------------------------------------------------------------------------
-- AUTO-CREATE PROFILE ON AUTH SIGNUP
-- -----------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
DECLARE
  _provider TEXT;
  _provider_id TEXT;
  _full_name TEXT;
  _first TEXT;
  _last TEXT;
BEGIN
  -- Extract the provider from app metadata (google, github, email)
  _provider := COALESCE(NEW.raw_app_meta_data->>'provider', 'email');
  _provider_id := NEW.raw_user_meta_data->>'provider_id';

  -- Extract name: handle "full_name" (Google/GitHub) and "first_name/last_name" (email signup)
  _full_name := COALESCE(
    NEW.raw_user_meta_data->>'full_name',
    NEW.raw_user_meta_data->>'name',
    ''
  );
  _first := COALESCE(
    NULLIF(NEW.raw_user_meta_data->>'first_name', ''),
    NULLIF(split_part(_full_name, ' ', 1), '')
  );
  _last := COALESCE(
    NULLIF(NEW.raw_user_meta_data->>'last_name', ''),
    NULLIF(substring(_full_name from position(' ' in _full_name) + 1), '')
  );

  INSERT INTO public.profiles (
    id,
    first_name,
    last_name,
    email,
    avatar_url,
    github_username,
    auth_provider,
    provider_id
  )
  VALUES (
    NEW.id,
    _first,
    _last,
    COALESCE(NEW.email, ''),
    NEW.raw_user_meta_data->>'avatar_url',
    COALESCE(
      NEW.raw_user_meta_data->>'user_name',
      NEW.raw_user_meta_data->>'preferred_username'
    ),
    _provider,
    _provider_id
  )
  ON CONFLICT (id) DO UPDATE SET
    email = EXCLUDED.email,
    first_name = COALESCE(NULLIF(EXCLUDED.first_name, ''), public.profiles.first_name),
    last_name = COALESCE(NULLIF(EXCLUDED.last_name, ''), public.profiles.last_name),
    avatar_url = COALESCE(EXCLUDED.avatar_url, public.profiles.avatar_url),
    github_username = COALESCE(EXCLUDED.github_username, public.profiles.github_username),
    auth_provider = COALESCE(EXCLUDED.auth_provider, public.profiles.auth_provider),
    provider_id = COALESCE(EXCLUDED.provider_id, public.profiles.provider_id),
    updated_at = timezone('utc', now());

  RETURN NEW;
END;
$$;

CREATE TRIGGER on_auth_user_created
AFTER INSERT ON auth.users
FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();

-- -----------------------------------------------------------------------------
-- RLS
-- -----------------------------------------------------------------------------
ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.github_installations ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.repositories ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.builds ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.vulnerabilities ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.pull_requests ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.pr_reviews ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.cloud_costs ENABLE ROW LEVEL SECURITY;

-- -----------------------------------------------------------------------------
-- PROFILES POLICIES
-- -----------------------------------------------------------------------------
CREATE POLICY "profiles_select_own"
ON public.profiles
FOR SELECT
TO authenticated
USING (auth.uid() = id);

CREATE POLICY "profiles_insert_own"
ON public.profiles
FOR INSERT
TO authenticated
WITH CHECK (auth.uid() = id);

CREATE POLICY "profiles_update_own"
ON public.profiles
FOR UPDATE
TO authenticated
USING (auth.uid() = id)
WITH CHECK (auth.uid() = id);

-- -----------------------------------------------------------------------------
-- GITHUB INSTALLATIONS POLICIES
-- -----------------------------------------------------------------------------
CREATE POLICY "github_installations_select_own"
ON public.github_installations
FOR SELECT
TO authenticated
USING (auth.uid() = profile_id);

CREATE POLICY "github_installations_insert_own"
ON public.github_installations
FOR INSERT
TO authenticated
WITH CHECK (auth.uid() = profile_id);

CREATE POLICY "github_installations_update_own"
ON public.github_installations
FOR UPDATE
TO authenticated
USING (auth.uid() = profile_id)
WITH CHECK (auth.uid() = profile_id);

CREATE POLICY "github_installations_delete_own"
ON public.github_installations
FOR DELETE
TO authenticated
USING (auth.uid() = profile_id);

-- -----------------------------------------------------------------------------
-- REPOSITORIES POLICIES
-- -----------------------------------------------------------------------------
CREATE POLICY "repositories_select_own"
ON public.repositories
FOR SELECT
TO authenticated
USING (auth.uid() = profile_id);

CREATE POLICY "repositories_insert_own"
ON public.repositories
FOR INSERT
TO authenticated
WITH CHECK (auth.uid() = profile_id);

CREATE POLICY "repositories_update_own"
ON public.repositories
FOR UPDATE
TO authenticated
USING (auth.uid() = profile_id)
WITH CHECK (auth.uid() = profile_id);

CREATE POLICY "repositories_delete_own"
ON public.repositories
FOR DELETE
TO authenticated
USING (auth.uid() = profile_id);

-- -----------------------------------------------------------------------------
-- BUILDS POLICIES
-- -----------------------------------------------------------------------------
CREATE POLICY "builds_select_own"
ON public.builds
FOR SELECT
TO authenticated
USING (
  EXISTS (
    SELECT 1
    FROM public.repositories r
    WHERE r.id = builds.repository_id
      AND r.profile_id = auth.uid()
  )
);

-- -----------------------------------------------------------------------------
-- VULNERABILITIES POLICIES
-- -----------------------------------------------------------------------------
CREATE POLICY "vulnerabilities_select_own"
ON public.vulnerabilities
FOR SELECT
TO authenticated
USING (
  EXISTS (
    SELECT 1
    FROM public.repositories r
    WHERE r.id = vulnerabilities.repository_id
      AND r.profile_id = auth.uid()
  )
);

-- -----------------------------------------------------------------------------
-- PULL REQUESTS POLICIES
-- -----------------------------------------------------------------------------
CREATE POLICY "pull_requests_select_own"
ON public.pull_requests
FOR SELECT
TO authenticated
USING (
  EXISTS (
    SELECT 1
    FROM public.repositories r
    WHERE r.id = pull_requests.repository_id
      AND r.profile_id = auth.uid()
  )
);

CREATE POLICY "pull_requests_insert_own"
ON public.pull_requests
FOR INSERT
TO authenticated
WITH CHECK (
  EXISTS (
    SELECT 1
    FROM public.repositories r
    WHERE r.id = pull_requests.repository_id
      AND r.profile_id = auth.uid()
  )
);

CREATE POLICY "pull_requests_update_own"
ON public.pull_requests
FOR UPDATE
TO authenticated
USING (
  EXISTS (
    SELECT 1
    FROM public.repositories r
    WHERE r.id = pull_requests.repository_id
      AND r.profile_id = auth.uid()
  )
)
WITH CHECK (
  EXISTS (
    SELECT 1
    FROM public.repositories r
    WHERE r.id = pull_requests.repository_id
      AND r.profile_id = auth.uid()
  )
);

-- -----------------------------------------------------------------------------
-- PR REVIEWS POLICIES
-- -----------------------------------------------------------------------------
CREATE POLICY "pr_reviews_select_own"
ON public.pr_reviews
FOR SELECT
TO authenticated
USING (
  EXISTS (
    SELECT 1
    FROM public.pull_requests pr
    JOIN public.repositories r ON r.id = pr.repository_id
    WHERE pr.id = pr_reviews.pull_request_id
      AND r.profile_id = auth.uid()
  )
);

CREATE POLICY "pr_reviews_insert_own"
ON public.pr_reviews
FOR INSERT
TO authenticated
WITH CHECK (
  EXISTS (
    SELECT 1
    FROM public.pull_requests pr
    JOIN public.repositories r ON r.id = pr.repository_id
    WHERE pr.id = pr_reviews.pull_request_id
      AND r.profile_id = auth.uid()
  )
);

CREATE POLICY "pr_reviews_update_own"
ON public.pr_reviews
FOR UPDATE
TO authenticated
USING (
  EXISTS (
    SELECT 1
    FROM public.pull_requests pr
    JOIN public.repositories r ON r.id = pr.repository_id
    WHERE pr.id = pr_reviews.pull_request_id
      AND r.profile_id = auth.uid()
  )
)
WITH CHECK (
  EXISTS (
    SELECT 1
    FROM public.pull_requests pr
    JOIN public.repositories r ON r.id = pr.repository_id
    WHERE pr.id = pr_reviews.pull_request_id
      AND r.profile_id = auth.uid()
  )
);

-- -----------------------------------------------------------------------------
-- CLOUD COSTS POLICIES
-- -----------------------------------------------------------------------------
CREATE POLICY "cloud_costs_select_own"
ON public.cloud_costs
FOR SELECT
TO authenticated
USING (auth.uid() = profile_id);

CREATE POLICY "cloud_costs_insert_own"
ON public.cloud_costs
FOR INSERT
TO authenticated
WITH CHECK (auth.uid() = profile_id);

CREATE POLICY "cloud_costs_update_own"
ON public.cloud_costs
FOR UPDATE
TO authenticated
USING (auth.uid() = profile_id)
WITH CHECK (auth.uid() = profile_id);

CREATE POLICY "cloud_costs_delete_own"
ON public.cloud_costs
FOR DELETE
TO authenticated
USING (auth.uid() = profile_id);

COMMIT;
