-- tech_job_market :: compensation by job title and work arrangement
-- Generated via the Auto-Ontology semantic layer (ask_question / text-to-SQL agent),
-- then independently re-verified against the dbt target (jobmarket.jobs_silver).
--
-- Source table : tech_job_market.jobmarket.jobs_silver  (silver layer; deduped + standardized)
-- Dimensions   : job_title, remote_policy_std  (certified glossary attribute "Remote Policy Standard")
-- Measures     : COUNT(*), AVG(salary_min), AVG(salary_max), null-salary count
-- Notes        : ~90% of postings carry no salary (salary_min IS NULL); averages are computed
--                over the subset that DOES disclose a range, so they are not population averages.

-- Q1: top 5 job titles by demand, with salary range per RAW remote policy string
WITH aggregated AS (
    SELECT job_title, remote_policy, COUNT(*) AS postings,
           AVG(salary_min) AS avg_salary_min, AVG(salary_max) AS avg_salary_max
    FROM tech_job_market.jobmarket.jobs
    WHERE job_title IS NOT NULL AND remote_policy IS NOT NULL
    GROUP BY job_title, remote_policy
),
title_totals AS (
    SELECT job_title, SUM(postings) AS total_postings FROM aggregated GROUP BY job_title
),
top_titles AS (
    SELECT job_title, total_postings FROM title_totals
    ORDER BY total_postings DESC, job_title ASC LIMIT 5
)
SELECT a.job_title, a.remote_policy, a.postings,
       CAST(a.avg_salary_min AS NUMERIC) AS average_salary_min,
       CAST(a.avg_salary_max AS NUMERIC) AS average_salary_max
FROM aggregated a JOIN top_titles t ON a.job_title = t.job_title
ORDER BY t.total_postings DESC, a.job_title, a.remote_policy;

-- Q2 (used for the chart): top 5 job titles by demand, salary range per STANDARDIZED policy
WITH top_titles AS (
    SELECT job_title
    FROM tech_job_market.jobmarket.jobs_silver
    WHERE job_title IS NOT NULL
    GROUP BY job_title
    ORDER BY COUNT(*) DESC, job_title LIMIT 5
)
SELECT j.job_title, j.remote_policy_std,
       COUNT(*) AS postings,
       CAST(AVG(j.salary_min) AS NUMERIC) AS avg_salary_min,
       CAST(AVG(j.salary_max) AS NUMERIC) AS avg_salary_max,
       COUNT(CASE WHEN j.salary_min IS NULL THEN 1 END) AS null_salary_min_count
FROM tech_job_market.jobmarket.jobs_silver AS j
INNER JOIN top_titles AS t ON j.job_title = t.job_title
GROUP BY j.job_title, j.remote_policy_std
ORDER BY j.job_title, j.remote_policy_std;

-- Q3 (FINAL — the query behind the chart): top 5 roles, rolled up to Remote / Onsite / Hybrid / Unknown.
-- Verbatim Auto-Ontology output (run 4), re-verified row-for-row against the dbt target.
-- Classification: Hybrid = mentions hybrid, OR mentions both remote and onsite;
--                  Remote = mentions remote but not onsite/hybrid;
--                  Onsite = mentions onsite but not remote/hybrid;
--                  Unknown = NULL policy or no keyword match.
WITH top_job_titles AS (
    SELECT job_title
    FROM tech_job_market.jobmarket.jobs_silver
    WHERE job_title IS NOT NULL
    GROUP BY job_title
    ORDER BY COUNT(*) DESC, job_title ASC
    LIMIT 5
),
classified AS (
    SELECT
        j.job_title,
        CASE
            WHEN j.remote_policy_std IS NULL THEN 'Unknown'
            WHEN j.remote_policy_std ILIKE '%hybrid%'
              OR (j.remote_policy_std ILIKE '%remote%' AND j.remote_policy_std ILIKE '%onsite%') THEN 'Hybrid'
            WHEN j.remote_policy_std ILIKE '%remote%'
              AND j.remote_policy_std NOT ILIKE '%onsite%'
              AND j.remote_policy_std NOT ILIKE '%hybrid%' THEN 'Remote'
            WHEN j.remote_policy_std ILIKE '%onsite%'
              AND j.remote_policy_std NOT ILIKE '%remote%'
              AND j.remote_policy_std NOT ILIKE '%hybrid%' THEN 'Onsite'
            ELSE 'Unknown'
        END AS work_arrangement,
        j.salary_min,
        j.salary_max
    FROM tech_job_market.jobmarket.jobs_silver j
    INNER JOIN top_job_titles t ON j.job_title = t.job_title
)
SELECT
    c.job_title,
    c.work_arrangement,
    COUNT(*) AS posting_count,
    CAST(AVG(c.salary_min) AS NUMERIC) AS avg_salary_min,
    CAST(AVG(c.salary_max) AS NUMERIC) AS avg_salary_max,
    COUNT(CASE WHEN c.salary_min IS NULL THEN 1 END) AS null_salary_min_count
FROM classified c
GROUP BY c.job_title, c.work_arrangement
ORDER BY c.job_title, c.work_arrangement;

-- ---------------------------------------------------------------------------
-- RECEIPT / VALIDATION NOTES
--
-- Run 1 (Q1) grouped on the RAW `remote_policy` string (96 distinct values in
--   `jobs`), producing a combinatorial set like 'anywhere; fully remote; remote'.
--   Valid SQL, valid rows, but the raw string is the wrong dimension for a
--   remote-vs-onsite question. Superseded by Q2/Q3.
--
-- Run 2 (Q2) grouped on the certified `remote_policy_std` attribute
--   (16 distinct values, e.g. 'Hybrid; Onsite; Remote') and returned 46 rows
--   over 5 titles. Verified row-for-row against the dbt target: identical.
--
-- Run 3 (Q3, first attempt) was DEFECTIVE: its `top_titles` CTE omitted
--   `WHERE job_title IS NOT NULL`, so the 3,513 postings with a NULL job_title
--   took the #1 slot and pushed 'Engineering' (114 postings) out of the top 5.
--   The result silently covered only 4 roles. Caught by re-running against the
--   dbt target and comparing the title set against Q2. Run 4 fixed it.
--
-- Run 4 (Q3, final) is the query above. 20 rows, 5 titles x 4 arrangements.
--   Verified row-for-row against the dbt target: identical.
--
-- Population notes:
--   - `jobs_silver` is the deduplicated, standardized layer (21,310 rows from
--     33,392 raw `jobs` rows).
--   - 19,288 of 21,310 silver postings have NO salary_min (90.5%). Every
--     AVG above is therefore computed over the subset that discloses a range,
--     not over all postings in the cell.
--   - A NULL avg_salary_min/avg_salary_max means every posting in that cell
--     had a NULL salary, which is different from a salary of zero.
