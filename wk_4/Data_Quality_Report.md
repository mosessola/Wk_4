# Data Quality & Cleaning Report: Bank of America Consumer Complaints (CFPB)

**Source:** `Consumer_Complaints.xlsx` (sheet `Data`), 62,516 rows x 12 columns, submitted 2017-05-01 to 2023-08-28.
**Original file:** never modified. `clean_complaints.py` reads it and writes new files.
**Reproduce:** `python clean_complaints.py <input.xlsx> <output_dir>`

## 1. Findings from inspection

| Check | Result | Decision |
|---|---|---|
| Complaint ID unique | 0 duplicate IDs, 0 duplicate rows | Valid primary key; no rows dropped |
| Date types | Both are true datetimes | None needed |
| Date order | 0 negative intervals (Date received >= Date submitted) | None needed |
| Missing months | 76 months, all present, none empty | No zero-fill needed for forecasting |
| Whitespace / case | None found | Safeguard trim kept in script |
| Sub-issue blank | 10,858 (17.4%) | Structural (many Issues have no sub-issues). Labelled "No sub-issue recorded" |
| Public response blank | 2,175 (3.5%) | Optional field. Labelled "No public response recorded" |
| Timely response blank | 1,494 (2.4%) | **Not "No".** Exactly the In-progress records (all 2023). Labelled "Not assessed (In progress)" |
| Sub-product blank | 7 | All Checking/Savings with credit-reporting issues (possible mis-tagging). Labelled "Not provided" and kept |
| Bare "Closed" response | 8 rows, all Timely = No | Kept as its own category, "Closed (no detail recorded)" |
| Long forwarding intervals | 454 rows >= 30 days; max 275 days | Valid dates, so flagged (`Long_Interval_Flag`), not removed |

## 2. Added fields
`Year, Quarter, Year_Quarter, Month_Num, Month_Name, Year_Month, Month_Start` (from Date submitted), `Forwarding_Interval_Days`, `Interval_Band`, `Long_Interval_Flag`, `Product_Short`, `Issue_Std`, `Sub_issue_Clean`, `Sub_product_Clean`, `Public_Response_Clean`, `Response_Clean`, `Timely_Flag`, `Timely_Valid`, `Is_In_Progress`, `Is_Boundary_Month`, `Is_Partial_Year`, `Weekend_Submission`.
All original columns are retained unchanged beside the cleaned versions.

## 3. Baseline validated numbers (for cross-track consistency)

| KPI | Value |
|---|---|
| Total complaints | 62,516 |
| Timely-response % (Yes / (Yes+No)) | 96.06% (58,619 / 61,022) |
| Excluded from timely % (In progress) | 1,494 (reported separately) |
| Avg forwarding interval | 1.225 days |
| Median forwarding interval | 0 days |
| Forwarded same day | 79.39% |
| Annual counts 2017-2023 | 5,394 / 7,872 / 7,075 / 8,942 / 11,149 / 12,953 / 9,131 |

## 4. Caveats and decisions to be aware of

1. **Partial periods.** 2017 (from May) and 2023 (to 28 Aug) are partial years. Aug 2023 is a partial month. May 2017 is flagged as a boundary month per the brief, although the data starts on 1 May. Exclude or caveat these in YoY and forecasting.
2. **Issue wording variants.** Only 2 variants within the same product were merged in `Issue_Std`: "Problem with an overdraft" and "Was approved for a loan, but didn't receive money". Near-duplicates such as "Closing an account" vs "Closing your account" and "Trouble using the card" vs "Trouble using your card" appear to be CFPB taxonomy differences across products, so they were **not** merged. Revisit if the team agrees on a mapping.
3. **Unexplained patterns, noted but not interpreted.** July 2023 spike (1,749 vs about 1,050 in neighbouring months). Dip from Nov 2018 to Mar 2019. Timely = No jumps to 1,224 in 2021. None of these can be explained from the data, and none should be read as misconduct.
4. **Forwarding interval is CFPB intake-to-forward time**, not company response or resolution time.
5. **Dashboard and statistics note.** In-progress cases are all from 2023, so 2023 response distributions are not comparable with earlier years.
6. **Small categories.** Student loan (39), "Email" channel (2) and "Web Referral" (90) are too small for reliable segment analysis.
7. **Complaints are consumer-reported issues,** not verified misconduct. Recorded responses do not prove satisfactory resolution.

## 5. Validation tests (all passed)
Row count unchanged; ID unique; original values preserved; yearly, monthly and product counts each sum to 62,516; Timely Yes + No + Not assessed = total; Not assessed matches In progress 1:1; no negative intervals; no missing months. See `validation_checks.csv`.
