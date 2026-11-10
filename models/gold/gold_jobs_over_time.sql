{{ config(
    materialized='table',
    tags=['gold']
) }}

-- Gold Mart 5: Monthly job posting trends
-- Source: jobs_silver

SELECT 
    date_trunc('month', posted_at) AS month,
    count(*) AS job_count,
    count(*) FILTER (WHERE salary_min IS NOT NULL) AS jobs_with_salary
FROM {{ ref('jobs_silver') }}
GROUP BY date_trunc('month', posted_at)
ORDER BY month
