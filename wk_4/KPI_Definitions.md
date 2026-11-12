# KPI Definitions & Calculations

All KPIs are computed in SQL (`kpi_queries.sql`) on `Consumer_Complaints_Cleaned.csv` and cross-validated against an independent pandas calculation (`run_kpis.py`, 23 checks, all passing).
**Reporting period:** 1 May 2017 to 28 Aug 2023 (Date submitted). **Population:** all 62,516 records unless stated.

| # | KPI | Definition | Query | Result |
|---|---|---|---|---|
| 1 | Total complaints | Count of records (Complaint ID is unique) | `kpi01` | **62,516** |
| 2 | Annual complaint volume | Count by calendar year of Date submitted | `kpi02` | 2017: 5,394 (partial) / 2018: 7,872 / 2019: 7,075 / 2020: 8,942 / 2021: 11,149 / 2022: 12,953 / 2023: 9,131 (partial) |
| 3 | Monthly complaint volume | Count by Year_Month (76 months, none missing) | `kpi03` | Range 356 (Feb 2019) to 1,749 (Jul 2023) |
| 4 | Complaints by product | Count by Product (9 products) | `kpi04_07` | Checking/Savings 24,814 / Credit & Prepaid Card 16,197 / Credit Reporting 7,710 / Mortgage 6,601 / Money Transfer 3,453 / Debt Collection 2,736 / Vehicle 633 / Payday-Title-Personal 333 / Student Loan 39 |
| 5 | Complaints by issue | Count by Issue_Std | `kpi05`, `kpi05b` | Top: Managing an account 15,109 (24.17%); Incorrect information on your report 4,931 (7.89%); Problem with a purchase shown on your statement 4,415 (7.06%) |
| 6 | Complaints by sub-product / sub-issue | Count by Sub_product_Clean / Sub_issue_Clean. Sub-issue is blank for 17.4% of records (structural, see Data Quality Report) | `kpi06a-c` | Top sub-product: Checking account 20,768 (33.22%) |
| 7 | Product % of total | Product count / 62,516 x 100 | `kpi04_07` | Checking/Savings 39.69%, Credit/Prepaid 25.91%, Credit Reporting 12.33%, Mortgage 10.56% |
| 8 | Company response distribution | Count and % by Response_Clean (and by public response) | `kpi08`, `kpi08b`, `kpi08c` | Closed with explanation 65.65% / monetary relief 23.51% / non-monetary relief 8.43% / In progress 2.39% / bare Closed 0.01%. Public response: 96.47% "chooses not to provide a public response"; 3.48% none recorded; 30 records (about 0.05%) a specific stance |
| 9 | Timely-response % | Yes / (Yes + No). **Denominator = valid Yes/No records only** (61,022). In-progress records (1,494) are excluded and reported separately | `kpi09`, `09b`, `09c` | **96.06%** (58,619 Yes; 2,403 No). By year: 99.8-99.9% (2017-19), 99.3% (2020), 89.0% (2021), 95.6% (2022), 93.2% (2023) |
| 10 | In-progress complaints | Count where Company response = "In progress" | `kpi10`, `kpi10b` | **1,494** (2.39%), all submitted in 2023: 863 in Jul and 587 in Aug |
| 11 | Forwarding interval (avg / median) | Date received - Date submitted, in days. Measures **CFPB intake-to-forward time, not company response or resolution time** | `kpi11`, `11b-f` | **Avg 1.225 days; median 0**; 79.39% same day; p95 = 5; p99 = 25; max 275; 454 records (0.73%) are 30+ days |
| 12 | Year-over-year change | (Year N - Year N-1) / Year N-1. 2017 and 2023 are partial years, so a like-for-like Jan-Aug comparison is also provided | `kpi12`, `12b`, `12c` | 2018 +45.9% / 2019 -10.1% / 2020 +26.4% / 2021 +24.7% / 2022 +16.2%. 2023 vs 2022: -29.5% (not like-for-like). Like-for-like Jan-Aug: 2023 +9.4% vs 2022 |

## Supporting definitions
- **Timely_Flag:** Yes / No / "Not assessed (In progress)". Blank is never recoded to No.
- **Long forwarding interval:** 30 or more days (threshold documented and adjustable in `clean_complaints.py`; the p99 is 25 days).
- **Interval bands:** Same day, 1 day, 2-3, 4-7, 8-29, 30+ days.
- **Boundary months:** May 2017 (first) and Aug 2023 (last, ends on the 28th).

## Interpretation notes (use these on the dashboard and in the AI assistant)
1. A complaint is a consumer-reported issue, not verified misconduct.
2. A recorded response category does not prove satisfactory resolution.
3. The 2023 "In progress" count reflects data cut-off timing: 49% of July 2023 and 82% of August 2023 complaints were still in progress. The count is not a backlog measure.
4. Records marked Timely = No rise sharply from June 2021 across several products, with no single product responsible. The data cannot explain why.
5. The YoY decline shown for 2023 is mostly a coverage effect (8 months vs 12).
