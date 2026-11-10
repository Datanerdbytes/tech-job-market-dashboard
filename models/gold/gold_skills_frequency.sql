{{ config(
    materialized='table',
    tags=['gold']
) }}

-- Gold Mart 7: Unique skill frequency distribution
-- Source: jobs_silver

SELECT 
    skill,
    count(*) AS job_count,
    round(count(*)::numeric / (SELECT count(*) FROM {{ ref('jobs_silver') }} WHERE skills_std IS NOT NULL AND array_length(skills_std, 1) > 0) * 100, 2) AS pct_of_jobs_with_skills
FROM {{ ref('jobs_silver') }},
     LATERAL unnest(skills_std) AS skill
WHERE skills_std IS NOT NULL AND array_length(skills_std, 1) > 0
GROUP BY skill
ORDER BY job_count DESC
