-- =====================================================================
-- Consumer Complaints KPI queries (SQLite dialect; table: complaints)
-- Table is loaded from Consumer_Complaints_Cleaned.csv by run_kpis.py
-- Each query starts with "-- name: <id>" so the runner can execute and export it.
-- Conventions:
--   * Complaint volume = COUNT of rows (Complaint ID is unique)
--   * Time fields use Date submitted (date CFPB received the complaint)
--   * Timely % uses ONLY Timely_Valid = 1 (Yes/No); In-progress reported separately
--   * Forwarding interval = Date received - Date submitted (CFPB intake -> sent to company)
-- =====================================================================

-- name: kpi01_total_complaints
SELECT COUNT(*) AS total_complaints,
       COUNT(DISTINCT "Complaint ID") AS distinct_ids,
       MIN("Date submitted") AS first_date, MAX("Date submitted") AS last_date
FROM complaints;

-- name: kpi02_annual_volume
SELECT Year, COUNT(*) AS complaints,
       MIN("Date submitted") AS first_date, MAX("Date submitted") AS last_date,
       COUNT(DISTINCT Year_Month) AS months_covered,
       CASE WHEN COUNT(DISTINCT Year_Month) < 12 THEN 'Partial year' ELSE 'Full year' END AS coverage
FROM complaints GROUP BY Year ORDER BY Year;

-- name: kpi03_monthly_volume
SELECT Year_Month, Year, Month_Num, COUNT(*) AS complaints,
       MAX(Is_Boundary_Month) AS is_boundary_month
FROM complaints GROUP BY Year_Month, Year, Month_Num ORDER BY Year_Month;

-- name: kpi04_07_product_volume_and_share
SELECT Product, Product_Short, COUNT(*) AS complaints,
       ROUND(100.0 * COUNT(*) / (SELECT COUNT(*) FROM complaints), 2) AS pct_of_total
FROM complaints GROUP BY Product, Product_Short ORDER BY complaints DESC;

-- name: kpi05_issue_volume
SELECT Issue_Std AS issue, COUNT(*) AS complaints,
       ROUND(100.0 * COUNT(*) / (SELECT COUNT(*) FROM complaints), 2) AS pct_of_total
FROM complaints GROUP BY Issue_Std ORDER BY complaints DESC;

-- name: kpi05b_top10_issues_by_product
SELECT Product_Short, issue, complaints, pct_of_product FROM (
  SELECT Product_Short, Issue_Std AS issue, COUNT(*) AS complaints,
         ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (PARTITION BY Product_Short), 2) AS pct_of_product,
         ROW_NUMBER() OVER (PARTITION BY Product_Short ORDER BY COUNT(*) DESC) AS rn
  FROM complaints GROUP BY Product_Short, Issue_Std)
WHERE rn <= 5 ORDER BY Product_Short, complaints DESC;

-- name: kpi06a_subproduct_volume
SELECT Product_Short, Sub_product_Clean AS sub_product, COUNT(*) AS complaints,
       ROUND(100.0 * COUNT(*) / (SELECT COUNT(*) FROM complaints), 2) AS pct_of_total
FROM complaints GROUP BY Product_Short, Sub_product_Clean ORDER BY complaints DESC;

-- name: kpi06b_subissue_volume
SELECT Issue_Std AS issue, Sub_issue_Clean AS sub_issue, COUNT(*) AS complaints,
       ROUND(100.0 * COUNT(*) / (SELECT COUNT(*) FROM complaints), 2) AS pct_of_total
FROM complaints GROUP BY Issue_Std, Sub_issue_Clean ORDER BY complaints DESC;

-- name: kpi06c_subissue_missing_summary
SELECT CASE WHEN Sub_issue_Clean = 'No sub-issue recorded' THEN 'No sub-issue recorded' ELSE 'Sub-issue recorded' END AS status,
       COUNT(*) AS complaints,
       ROUND(100.0 * COUNT(*) / (SELECT COUNT(*) FROM complaints), 2) AS pct
FROM complaints GROUP BY 1;

-- name: kpi08_response_distribution
SELECT Response_Clean AS company_response, COUNT(*) AS complaints,
       ROUND(100.0 * COUNT(*) / (SELECT COUNT(*) FROM complaints), 2) AS pct_of_total
FROM complaints GROUP BY Response_Clean ORDER BY complaints DESC;

-- name: kpi08b_public_response_distribution
SELECT Public_Response_Clean AS public_response, COUNT(*) AS complaints,
       ROUND(100.0 * COUNT(*) / (SELECT COUNT(*) FROM complaints), 2) AS pct_of_total
FROM complaints GROUP BY Public_Response_Clean ORDER BY complaints DESC;

-- name: kpi08c_response_by_year_pct
SELECT Year, Response_Clean AS company_response, COUNT(*) AS complaints,
       ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (PARTITION BY Year), 2) AS pct_of_year
FROM complaints GROUP BY Year, Response_Clean ORDER BY Year, complaints DESC;

-- name: kpi09_timely_overall
SELECT SUM(Timely_Valid) AS valid_records_denominator,
       SUM(CASE WHEN Timely_Flag = 'Yes' THEN 1 ELSE 0 END) AS timely_yes,
       SUM(CASE WHEN Timely_Flag = 'No'  THEN 1 ELSE 0 END) AS timely_no,
       ROUND(100.0 * SUM(CASE WHEN Timely_Flag = 'Yes' THEN 1 ELSE 0 END) / SUM(Timely_Valid), 2) AS timely_pct,
       SUM(1 - Timely_Valid) AS excluded_not_assessed,
       COUNT(*) AS total_records
FROM complaints;

-- name: kpi09b_timely_by_year
SELECT Year, SUM(Timely_Valid) AS valid_records,
       SUM(CASE WHEN Timely_Flag = 'No' THEN 1 ELSE 0 END) AS timely_no,
       ROUND(100.0 * SUM(CASE WHEN Timely_Flag = 'Yes' THEN 1 ELSE 0 END) / SUM(Timely_Valid), 2) AS timely_pct,
       SUM(1 - Timely_Valid) AS excluded_in_progress
FROM complaints GROUP BY Year ORDER BY Year;

-- name: kpi09c_timely_by_product
SELECT Product_Short, SUM(Timely_Valid) AS valid_records,
       SUM(CASE WHEN Timely_Flag = 'No' THEN 1 ELSE 0 END) AS timely_no,
       ROUND(100.0 * SUM(CASE WHEN Timely_Flag = 'Yes' THEN 1 ELSE 0 END) / SUM(Timely_Valid), 2) AS timely_pct,
       SUM(1 - Timely_Valid) AS excluded_in_progress
FROM complaints GROUP BY Product_Short ORDER BY valid_records DESC;

-- name: kpi10_in_progress
SELECT SUM(Is_In_Progress) AS in_progress_complaints,
       ROUND(100.0 * SUM(Is_In_Progress) / COUNT(*), 2) AS pct_of_all,
       MIN(CASE WHEN Is_In_Progress = 1 THEN "Date submitted" END) AS earliest_in_progress_submitted,
       MAX(CASE WHEN Is_In_Progress = 1 THEN "Date submitted" END) AS latest_in_progress_submitted
FROM complaints;

-- name: kpi10b_in_progress_by_month
SELECT Year_Month, SUM(Is_In_Progress) AS in_progress, COUNT(*) AS complaints,
       ROUND(100.0 * SUM(Is_In_Progress) / COUNT(*), 2) AS pct_in_progress
FROM complaints WHERE Year = 2023 GROUP BY Year_Month ORDER BY Year_Month;

-- name: kpi11_forwarding_interval_summary
WITH ranked AS (
  SELECT Forwarding_Interval_Days AS d,
         ROW_NUMBER() OVER (ORDER BY Forwarding_Interval_Days) AS rn,
         COUNT(*) OVER () AS n FROM complaints)
SELECT (SELECT ROUND(AVG(Forwarding_Interval_Days), 3) FROM complaints) AS avg_days,
       (SELECT AVG(d) FROM ranked WHERE rn IN ((n + 1) / 2, (n + 2) / 2)) AS median_days,
       (SELECT MIN(Forwarding_Interval_Days) FROM complaints) AS min_days,
       (SELECT MAX(Forwarding_Interval_Days) FROM complaints) AS max_days,
       (SELECT MIN(d) FROM ranked WHERE rn >= 0.95 * n) AS p95_days,
       (SELECT MIN(d) FROM ranked WHERE rn >= 0.99 * n) AS p99_days,
       (SELECT ROUND(100.0 * SUM(Forwarding_Interval_Days = 0) / COUNT(*), 2) FROM complaints) AS pct_same_day,
       (SELECT SUM(Long_Interval_Flag) FROM complaints) AS long_interval_30plus;

-- name: kpi11b_interval_distribution
SELECT Interval_Band, COUNT(*) AS complaints,
       ROUND(100.0 * COUNT(*) / (SELECT COUNT(*) FROM complaints), 2) AS pct_of_total
FROM complaints GROUP BY Interval_Band
ORDER BY CASE Interval_Band WHEN 'Same day' THEN 1 WHEN '1 day' THEN 2 WHEN '2-3 days' THEN 3
                            WHEN '4-7 days' THEN 4 WHEN '8-29 days' THEN 5 ELSE 6 END;

-- name: kpi11c_interval_by_product
SELECT Product_Short, COUNT(*) AS complaints,
       ROUND(AVG(Forwarding_Interval_Days), 3) AS avg_days,
       MAX(Forwarding_Interval_Days) AS max_days,
       SUM(Long_Interval_Flag) AS long_interval_30plus,
       ROUND(100.0 * SUM(Long_Interval_Flag) / COUNT(*), 2) AS pct_long
FROM complaints GROUP BY Product_Short ORDER BY avg_days DESC;

-- name: kpi11d_interval_by_year
SELECT Year, COUNT(*) AS complaints, ROUND(AVG(Forwarding_Interval_Days), 3) AS avg_days,
       MAX(Forwarding_Interval_Days) AS max_days, SUM(Long_Interval_Flag) AS long_interval_30plus
FROM complaints GROUP BY Year ORDER BY Year;

-- name: kpi11e_interval_by_channel
SELECT "Submitted via" AS channel, COUNT(*) AS complaints,
       ROUND(AVG(Forwarding_Interval_Days), 3) AS avg_days,
       ROUND(100.0 * SUM(Forwarding_Interval_Days = 0) / COUNT(*), 2) AS pct_same_day
FROM complaints GROUP BY "Submitted via" ORDER BY complaints DESC;

-- name: kpi11f_longest_intervals_top25
SELECT "Complaint ID", "Date submitted", "Date received", Forwarding_Interval_Days,
       "Submitted via" AS channel, Product_Short, Issue_Std AS issue
FROM complaints ORDER BY Forwarding_Interval_Days DESC, "Complaint ID" LIMIT 25;

-- name: kpi12_yoy_calendar_year
SELECT Year, COUNT(*) AS complaints,
       LAG(COUNT(*)) OVER (ORDER BY Year) AS prior_year,
       COUNT(*) - LAG(COUNT(*)) OVER (ORDER BY Year) AS abs_change,
       ROUND(100.0 * (COUNT(*) - LAG(COUNT(*)) OVER (ORDER BY Year)) / LAG(COUNT(*)) OVER (ORDER BY Year), 2) AS yoy_pct,
       CASE WHEN Year IN (2017, 2023) THEN 'Partial year - not like-for-like' ELSE 'OK' END AS comparability
FROM complaints GROUP BY Year ORDER BY Year;

-- name: kpi12b_yoy_like_for_like_jan_aug
-- Fair comparison for partial 2023: Jan-Aug (to 28 Aug) in every year, 2018-2023.
-- Note: Aug 2023 ends on the 28th, so the 2023 figure is slightly understated vs full Augusts.
SELECT Year, COUNT(*) AS complaints_jan_aug,
       LAG(COUNT(*)) OVER (ORDER BY Year) AS prior_year,
       ROUND(100.0 * (COUNT(*) - LAG(COUNT(*)) OVER (ORDER BY Year)) / LAG(COUNT(*)) OVER (ORDER BY Year), 2) AS yoy_pct
FROM complaints WHERE Month_Num BETWEEN 1 AND 8 AND Year >= 2018
GROUP BY Year ORDER BY Year;

-- name: kpi12c_yoy_by_product
SELECT Product_Short, Year, COUNT(*) AS complaints,
       ROUND(100.0 * (COUNT(*) - LAG(COUNT(*)) OVER (PARTITION BY Product_Short ORDER BY Year))
             / LAG(COUNT(*)) OVER (PARTITION BY Product_Short ORDER BY Year), 2) AS yoy_pct
FROM complaints GROUP BY Product_Short, Year ORDER BY Product_Short, Year;

-- name: extra_product_by_year
SELECT Product_Short, Year, COUNT(*) AS complaints
FROM complaints GROUP BY Product_Short, Year ORDER BY Product_Short, Year;

-- name: extra_response_by_product
SELECT Product_Short, Response_Clean AS company_response, COUNT(*) AS complaints,
       ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (PARTITION BY Product_Short), 2) AS pct_of_product
FROM complaints GROUP BY Product_Short, Response_Clean ORDER BY Product_Short, complaints DESC;

-- name: extra_channel_by_year
SELECT Year, "Submitted via" AS channel, COUNT(*) AS complaints
FROM complaints GROUP BY Year, "Submitted via" ORDER BY Year, complaints DESC;

-- name: extra_top_states
SELECT State, COUNT(*) AS complaints,
       ROUND(100.0 * COUNT(*) / (SELECT COUNT(*) FROM complaints), 2) AS pct_of_total
FROM complaints GROUP BY State ORDER BY complaints DESC LIMIT 15;

-- name: extra_data_quality_summary
SELECT 'Missing sub-issue' AS item, SUM(CASE WHEN Sub_issue_Clean = 'No sub-issue recorded' THEN 1 ELSE 0 END) AS records FROM complaints
UNION ALL SELECT 'Missing public response', SUM(CASE WHEN Public_Response_Clean = 'No public response recorded' THEN 1 ELSE 0 END) FROM complaints
UNION ALL SELECT 'Missing sub-product', SUM(CASE WHEN Sub_product_Clean = 'Not provided' THEN 1 ELSE 0 END) FROM complaints
UNION ALL SELECT 'Timely not assessed (In progress)', SUM(1 - Timely_Valid) FROM complaints
UNION ALL SELECT 'Bare "Closed" responses', SUM(CASE WHEN Response_Clean LIKE 'Closed (no detail%' THEN 1 ELSE 0 END) FROM complaints
UNION ALL SELECT 'Forwarding interval >= 30 days', SUM(Long_Interval_Flag) FROM complaints
UNION ALL SELECT 'Boundary-month records', SUM(Is_Boundary_Month) FROM complaints;
