{{ config(
    materialized='table',
    tags=['gold']
) }}

-- Gold Mart 6: Overall salary summary statistics
-- Source: jobs_silver

SELECT 
    count(*) AS total_jobs,
    count(*) FILTER (WHERE salary_min IS NOT NULL) AS jobs_with_salary,
    round(avg(salary_min)::numeric, 2) AS avg_salary_min,
    round(avg(salary_max)::numeric, 2) AS avg_salary_max,
    round(min(salary_min)::numeric, 2) AS min_salary_min,
    round(max(salary_max)::numeric, 2) AS max_salary_max
FROM {{ ref('jobs_silver') }}
