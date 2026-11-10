{{ config(
    materialized='table',
    tags=['gold']
) }}

-- Gold Mart 2: Job counts and salary statistics by location
-- Source: jobs_silver

SELECT 
    location,
    count(*) AS job_count,
    round(avg(salary_min)::numeric, 2) AS avg_salary_min,
    round(avg(salary_max)::numeric, 2) AS avg_salary_max
FROM {{ ref('jobs_silver') }}
WHERE location IS NOT NULL AND location <> ''
GROUP BY location
ORDER BY job_count DESC
