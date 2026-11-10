{{ config(
    materialized='table',
    tags=['gold']
) }}

-- Gold Mart 3: Job counts and salary statistics by standardized remote policy
-- Source: jobs_silver

SELECT 
    remote_policy_std,
    count(*) AS job_count,
    round(avg(salary_min)::numeric, 2) AS avg_salary_min,
    round(avg(salary_max)::numeric, 2) AS avg_salary_max,
    count(*) FILTER (WHERE salary_min IS NOT NULL) AS jobs_with_salary
FROM {{ ref('jobs_silver') }}
GROUP BY remote_policy_std
ORDER BY job_count DESC
