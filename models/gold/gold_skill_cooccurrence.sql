{{ config(
    materialized='table',
    tags=['gold']
) }}

-- Gold Mart 8: Skill co-occurrence pairs
-- Which skills appear together in the same job posting
-- Source: jobs_silver

WITH skill_pairs AS (
    SELECT 
        s1.skill as skill_a,
        s2.skill as skill_b,
        count(*) as job_count
    FROM {{ ref('jobs_silver') }},
         LATERAL unnest(skills_std) AS s1(skill),
         LATERAL unnest(skills_std) AS s2(skill)
    WHERE skills_std IS NOT NULL 
      AND array_length(skills_std, 1) > 1
      AND s1.skill < s2.skill
    GROUP BY s1.skill, s2.skill
)
SELECT skill_a, skill_b, job_count,
       round(job_count::numeric / (SELECT count(*) FROM {{ ref('jobs_silver') }} WHERE skills_std IS NOT NULL AND array_length(skills_std, 1) > 1) * 100, 2) AS pct_of_multi_skill_jobs
FROM skill_pairs
ORDER BY job_count DESC
