{{ config(
    materialized='table',
    tags=['gold']
) }}

-- Gold Mart 1: Job counts and salary statistics by company
-- Source: jobs_silver

SELECT 
    company,
    count(*) AS job_count,
    round(avg(salary_min)::numeric, 2) AS avg_salary_min,
    round(avg(salary_max)::numeric, 2) AS avg_salary_max,
    count(*) FILTER (WHERE salary_min IS NOT NULL) AS jobs_with_salary
FROM {{ ref('jobs_silver') }}
WHERE company IS NOT NULL AND company <> ''
GROUP BY company
ORDER BY job_count DESC
