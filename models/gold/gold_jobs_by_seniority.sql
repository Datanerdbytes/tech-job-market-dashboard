{{ config(
    materialized='table',
    tags=['gold']
) }}

-- Gold Mart 4: Job counts and salary statistics by standardized seniority
-- Source: jobs_silver

SELECT 
    seniority_std,
    count(*) AS job_count,
    round(avg(salary_min)::numeric, 2) AS avg_salary_min,
    round(avg(salary_max)::numeric, 2) AS avg_salary_max
FROM {{ ref('jobs_silver') }}
GROUP BY seniority_std
ORDER BY job_count DESC
