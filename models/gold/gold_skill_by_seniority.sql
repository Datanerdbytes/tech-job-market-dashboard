{{ config(
    materialized='table',
    tags=['gold']
) }}

-- Gold Mart 10: Top skills by seniority level
-- Source: jobs_silver

WITH senior_skills AS (
    SELECT 
        unnest(skills_std) as skill,
        seniority_std
    FROM {{ ref('jobs_silver') }}
    WHERE skills_std IS NOT NULL 
      AND array_length(skills_std, 1) > 0
      AND seniority_std IS NOT NULL
)
SELECT 
    seniority_std,
    skill,
    count(*) as job_count,
    round(count(*)::numeric / sum(count(*)) OVER (PARTITION BY seniority_std) * 100, 2) AS pct_of_seniority_jobs
FROM senior_skills
GROUP BY seniority_std, skill
ORDER BY seniority_std, job_count DESC
