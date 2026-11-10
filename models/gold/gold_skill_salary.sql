{{ config(
    materialized='table',
    tags=['gold']
) }}

-- Gold Mart 9: Salary statistics by individual skill
-- Source: jobs_silver

WITH skill_salary AS (
    SELECT 
        unnest(skills_std) as skill,
        salary_min,
        salary_max
    FROM {{ ref('jobs_silver') }}
    WHERE skills_std IS NOT NULL 
      AND array_length(skills_std, 1) > 0
      AND salary_min IS NOT NULL
)
SELECT 
    skill,
    count(*) as job_count,
    round(avg(salary_min)::numeric, 2) as avg_salary_min,
    round(avg(salary_max)::numeric, 2) as avg_salary_max,
    round(min(salary_min)::numeric, 2) as min_salary_min,
    round(max(salary_max)::numeric, 2) as max_salary_max
FROM skill_salary
GROUP BY skill
ORDER BY avg_salary_max DESC
