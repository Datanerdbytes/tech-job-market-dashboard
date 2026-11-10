{{ config(materialized='view') }}

-- Staging model for excluded_comments table

SELECT
    id,
    thread_id,
    comment_id,
    raw_text,
    archived_at
FROM jobmarket.excluded_comments
