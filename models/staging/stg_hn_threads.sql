{{ config(materialized='view') }}

-- Staging model for hn_threads table

SELECT
    id,
    title,
    url,
    posted_at,
    fetched_at
FROM jobmarket.hn_threads
