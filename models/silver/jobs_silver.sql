{{ config(
    materialized='table',
    tags=['silver']
) }}

-- Silver layer: cleaned, standardized, deduplicated jobs data
-- Source: stg_jobs (bronze)
-- All bronze data is preserved; silver is derived via cleaning rules

WITH base AS (
    SELECT *,
        trim(company) as company_t,
        trim(job_title) as job_title_t,
        trim(location) as location_t,
        trim(remote_policy) as remote_policy_t,
        trim(salary_currency) as salary_currency_t,
        trim(seniority) as seniority_t
    FROM {{ ref('stg_jobs') }}
    WHERE NOT (
        (company IS NULL OR trim(company) = '')
        AND
        (job_title IS NULL OR trim(job_title) = '')
    )
),
remote_clean AS (
    SELECT b.*,
        CASE 
            WHEN remote_policy_t IS NULL OR remote_policy_t = '' THEN 'Unknown'
            ELSE (
                SELECT string_agg(DISTINCT canon, '; ' ORDER BY canon)
                FROM (
                    SELECT DISTINCT 
                        CASE 
                            WHEN lower(p) ~ 'remote|wfh|work.from.home' THEN 'Remote'
                            WHEN lower(p) ~ 'onsite|on.site|on-site' THEN 'Onsite'
                            WHEN lower(p) ~ 'hybrid' THEN 'Hybrid'
                            WHEN lower(p) ~ 'anywhere' THEN 'Anywhere'
                            ELSE 'Unknown'
                        END as canon
                    FROM regexp_split_to_table(remote_policy_t, '\s*;\s*') as p
                    WHERE trim(p) <> ''
                ) sub
            )
        END as remote_policy_std
    FROM base b
),
seniority_clean AS (
    SELECT r.*,
        CASE 
            WHEN seniority_t IS NULL OR seniority_t = '' THEN 'Unknown'
            ELSE (
                SELECT string_agg(DISTINCT canon, '; ' ORDER BY canon)
                FROM (
                    SELECT DISTINCT 
                        CASE 
                            WHEN lower(p) ~ 'intern|fresher' THEN 'Intern'
                            WHEN lower(p) ~ 'entry.level|new grad|graduate' THEN 'Entry'
                            WHEN lower(p) ~ 'junior' THEN 'Junior'
                            WHEN lower(p) ~ 'mid.level|midlevel' THEN 'Mid'
                            WHEN lower(p) ~ 'senior' THEN 'Senior'
                            WHEN lower(p) ~ 'lead' THEN 'Lead'
                            WHEN lower(p) ~ 'manager' THEN 'Manager'
                            WHEN lower(p) ~ 'director' THEN 'Director'
                            WHEN lower(p) ~ 'staff' THEN 'Staff'
                            WHEN lower(p) ~ 'principal' THEN 'Principal'
                            ELSE 'Unknown'
                        END as canon
                    FROM regexp_split_to_table(seniority_t, '\s*;\s*') as p
                    WHERE trim(p) <> ''
                ) sub
            )
        END as seniority_std
    FROM remote_clean r
),
deduped AS (
    SELECT *,
        ROW_NUMBER() OVER (
            PARTITION BY company_t, job_title_t, location_t 
            ORDER BY posted_at DESC NULLS LAST, fetched_at DESC NULLS LAST, id DESC
        ) as rn
    FROM seniority_clean
)
SELECT 
    id as _source_bronze_id,
    thread_id,
    comment_id,
    company_t as company,
    job_title_t as job_title,
    raw_text,
    location_t as location,
    remote_policy_t as remote_policy_original,
    remote_policy_std,
    salary_min,
    salary_max,
    salary_currency_t as salary_currency,
    seniority_t as seniority_original,
    seniority_std,
    skills,
    posted_at,
    fetched_at,
    (rn > 1) as is_deduped,
    now() as _cleaned_at,
    -- Standardized skills: lowercase, trimmed, deduplicated, sorted
    CASE 
        WHEN skills IS NOT NULL AND array_length(skills, 1) > 0 THEN (
            SELECT array_agg(DISTINCT lower(trim(s)) ORDER BY lower(trim(s)))
            FROM unnest(skills) AS s
            WHERE trim(s) <> ''
        )
        ELSE NULL
    END as skills_std
FROM deduped
WHERE rn = 1
