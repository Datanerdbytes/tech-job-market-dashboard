{{ config(materialized='view') }}

-- Staging model for the raw jobs table (bronze source of truth)
-- Never modified; all cleaning happens in silver layer

SELECT
    id,
    thread_id,
    comment_id,
    company,
    job_title,
    raw_text,
    location,
    remote_policy,
    salary_min,
    salary_max,
    salary_currency,
    seniority,
    skills,
    posted_at,
    fetched_at
FROM jobmarket.jobs
