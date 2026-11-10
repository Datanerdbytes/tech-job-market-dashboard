{{ config(
    materialized='table',
    tags=['gold']
) }}

-- Gold Mart 12: Seniority deep-dive analysis
-- Source: jobs_silver

SELECT 
    seniority_std,
    count(*) as job_count,
    round(avg(salary_min)::numeric, 2) as avg_salary_min,
    round(avg(salary_max)::numeric, 2) as avg_salary_max,
    count(*) FILTER (WHERE salary_min IS NOT NULL) as jobs_with_salary
FROM {{ ref('jobs_silver') }}
GROUP BY seniority_std
ORDER BY job_count DESC
