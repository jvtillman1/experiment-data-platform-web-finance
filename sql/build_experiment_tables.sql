-- build_experiment_tables.sql
--
-- Example SQL for building experiment outcomes and aggregated tables
-- from a raw user-level experiment table.
--
-- The structure here matches the synthetic dataset in:
--   data/synthetic_experiment_outcomes.csv
--
-- Assumptions:
--   1) You have loaded the CSV into a staging table called:
--        stg_experiment_user_level
--   2) That table has the following columns (or their equivalents):
--        user_id
--        experiment_name
--        variant
--        first_exposure_date
--        region
--        device_type
--        package_group
--        list_size_group
--        is_eligible_visitor
--        is_activated
--        is_converted
--        new_booking_flag
--        nb_mrr
--        total_revenue
--        contamination_flag
--        duplication_rank
--
-- This script shows how you would turn that into:
--   - experiment_outcomes         (user-level outcomes)
--   - experiment_outcomes_clean   (filtered, non-contaminated cohort)
--   - experiment_aggregated       (variant/segment-level rollups)
--
-- The SQL is written in a BigQuery-style dialect, but the pattern
-- is portable to most warehouses with minor syntax changes.


-- ============================================================
-- 1. User-level outcomes table
-- ============================================================

CREATE OR REPLACE TABLE experiment_outcomes AS
SELECT
    user_id,
    experiment_name,
    variant,
    first_exposure_date,
    region,
    device_type,
    package_group,
    list_size_group,

    -- Core funnel flags (already computed in the staging table)
    CAST(is_eligible_visitor AS BOOL) AS is_eligible_visitor,
    CAST(is_activated AS BOOL)        AS is_activated,
    CAST(is_converted AS BOOL)        AS is_converted,
    CAST(new_booking_flag AS BOOL)    AS new_booking_flag,

    -- Financial metrics
    CAST(nb_mrr AS FLOAT64)          AS nb_mrr,
    CAST(total_revenue AS FLOAT64)   AS total_revenue,

    -- Data quality / cohort control flags
    contamination_flag,
    duplication_rank
FROM
    stg_experiment_user_level;


-- ============================================================
-- 2. Clean cohort for analysis
-- ============================================================
-- Filters out users who:
--   - were not eligible visitors
--   - are contaminated across variants
--   - are duplicate representations of the same user
-- This table is what the Python scripts expect to work from.

CREATE OR REPLACE TABLE experiment_outcomes_clean AS
SELECT
    *
FROM
    experiment_outcomes
WHERE
    is_eligible_visitor = TRUE
    AND contamination_flag = 'Not Contaminated'
    AND duplication_rank = 1;


-- ============================================================
-- 3. Aggregated table for dashboards & stats
-- ============================================================
-- Aggregates the clean cohort by variant and key segments.
-- You can add or remove grouping dimensions depending on your
-- real use case (geo, channel, plan, etc.).

CREATE OR REPLACE TABLE experiment_aggregated AS
SELECT
    experiment_name,
    variant,
    region,
    package_group,
    list_size_group,

    -- Base counts
    COUNT(DISTINCT user_id) AS users,
    SUM(CASE WHEN is_activated      THEN 1 ELSE 0 END) AS activations,
    SUM(CASE WHEN is_converted      THEN 1 ELSE 0 END) AS conversions,
    SUM(CASE WHEN new_booking_flag  THEN 1 ELSE 0 END) AS new_bookings,

    -- Financials
    SUM(nb_mrr)         AS total_new_mrr,
    SUM(total_revenue)  AS total_revenue

FROM
    experiment_outcomes_clean
GROUP BY
    experiment_name,
    variant,
    region,
    package_group,
    list_size_group;


-- ============================================================
-- 4. Example: pull data for analysis
-- ============================================================
-- The Python scripts in python/ can work either directly from
-- experiment_outcomes_clean (user-level) or from this aggregated
-- view if you prefer to pre-compute segment-level metrics.

-- Example: aggregated results for a single experiment
--
--   SELECT *
--   FROM experiment_aggregated
--   WHERE experiment_name = 'homepage_cta_test';
--
-- Example: user-level clean cohort for the same experiment
--
--   SELECT *
--   FROM experiment_outcomes_clean
--   WHERE experiment_name = 'homepage_cta_test';
