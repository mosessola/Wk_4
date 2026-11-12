# Consumer Complaint Monitoring & Response Dashboard: Data Analytics Track (Week 4)

**AnalystLab Africa | Experience Lab Internship Programme**
**Project:** Consumer Complaint Trends and Response Intelligence Platform
**Track:** Data Analytics | **Author:** _<your name>_ | **Date:** _<date>_

## 1. Project overview
Stakeholders need a reliable way to monitor consumer complaints recorded against Bank of America (CFPB data, 1 May 2017 to 28 Aug 2023, 62,516 records). This track delivers a validated analytics foundation (cleaned data, SQL KPIs, documentation) for a Power BI dashboard covering complaint trends, products and issues, company response categories, and CFPB forwarding intervals.

> A complaint is an issue reported by a consumer. It does not establish misconduct or prove a regulatory violation. Recorded company responses do not prove satisfactory resolution.

## 2. Status
| Deliverable | Status |
|---|---|
| Cleaned dataset + reproducible cleaning script | Done |
| Data-quality documentation | Done |
| SQL queries / analytical scripts (31 queries) | Done, cross-validated |
| KPI definitions & calculations (12 required KPIs) | Done |
| Power BI dashboard (4 pages) | _Not yet built_ |
| Business insights (5+) and recommendations (3+) | _Not yet written_ |
| Recorded presentation, GitHub/LinkedIn/X posts | _To do_ |

## 3. Repository structure
```
Consumer_Complaints.xlsx                  # ORIGINAL (supplied, never modified)
ConsumerComplaints_DataDictionary.csv     # supplied data dictionary
clean_complaints.py                       # step 1: cleaning pipeline
Consumer_Complaints_Cleaned.csv / .xlsx   # cleaned dataset (+ cleaning log & validation sheets in .xlsx)
cleaning_log.csv                          # every transformation and rows affected
validation_checks.csv                     # post-cleaning reconciliation tests
Data_Quality_Report.md                    # data-quality findings and decisions
kpi_queries.sql                           # step 2: all KPI queries (SQLite dialect)
run_kpis.py                               # runs SQL, exports results, cross-validates vs pandas
kpi_results/*.csv, KPI_Results.xlsx       # query outputs (use these as dashboard sources)
KPI_Definitions.md                        # KPI definitions, results, interpretation notes
```

## 4. Setup and reproduction
Requirements: Python 3.10+, `pandas`, `openpyxl` (SQLite is built into Python).
```bash
pip install pandas openpyxl
python clean_complaints.py Consumer_Complaints.xlsx .   # writes cleaned data, cleaning log, validation checks
python run_kpis.py Consumer_Complaints_Cleaned.csv .    # runs kpi_queries.sql, exports results, cross-validates
```
`run_kpis.py` stops with an error if any SQL result disagrees with the independent pandas calculation (23 checks, all currently passing). The SQL file can also be run in any SQLite client against a table named `complaints` loaded from the cleaned CSV. For SQL Server or PostgreSQL, adapt the median calculation and the `LAG` / `ROW_NUMBER` syntax as needed.

## 5. Methodology
1. **Inspection:** structure, types, ID uniqueness, duplicates, missing values, date validity, category consistency.
2. **Cleaning** (documented in `cleaning_log.csv`; original columns preserved beside cleaned ones):
   - Blank Sub-issue, Public response and Sub-product values are labelled according to their meaning, not dropped.
   - Blank *Timely response?* is **not** treated as "No". It is labelled "Not assessed (In progress)" and excluded from the timely-% denominator.
   - Only two clear wording variants of Issue were merged, within the same product. The 8 bare "Closed" responses are kept as their own category.
   - Derived fields added: year, quarter, month, forwarding interval, interval band, and flags for long interval, boundary month and partial year.
3. **KPIs:** calculated in SQL, with every table reconciled to the 62,516 total.
4. **Validation:** row counts, key uniqueness, totals reconcile across year/month/product/response, the in-progress to blank-timely match is exact, and SQL results match pandas.

## 6. Headline results (validated)
| Metric | Value |
|---|---|
| Total complaints | 62,516 (peak year 2022: 12,953) |
| Largest products | Checking/Savings 39.7%, Credit & Prepaid Card 25.9%, Credit Reporting 12.3%, Mortgage 10.6% |
| Most frequent issue | Managing an account (24.2%) |
| Most frequent response | Closed with explanation (65.7%) |
| Timely response | 96.06% of 61,022 valid records; 1,494 In-progress records excluded |
| Forwarding interval | Average 1.23 days, median 0; 79.4% same day; 454 (0.7%) take 30+ days |

Full tables are in `KPI_Definitions.md` and `kpi_results/`.

## 7. Assumptions
- Time analysis uses **Date submitted** (CFPB receipt date).
- The forwarding interval is **CFPB intake to forwarding**, not company response or resolution time.
- Volume is the count of records, with Complaint ID as the unique key.
- The 30-day "unusually long interval" threshold is an analyst choice (p99 = 25 days).

## 8. Limitations
- **Partial periods:** 2017 (from May) and 2023 (to 28 Aug) are incomplete, so use the like-for-like comparison (`kpi12b`) rather than raw 2023 vs 2022.
- **Snapshot effects:** all 1,494 In-progress records are from 2023, mainly Jul-Aug, so 2023 response distributions are not comparable with earlier years.
- **Unexplained patterns:** the July 2023 volume spike, the Nov 2018 to Mar 2019 dip, and the rise in Timely = No from June 2021 (spread across several products) cannot be explained from this data. They are reported as observed, with no causal claim.
- **No complaint narratives** and no complaint-level resolution detail, so questions about root causes, customer satisfaction or actual outcomes cannot be answered.
- **Issue taxonomy changed over time and across products** (for example "Closing an account" vs "Closing your account"), so issue trends should be read within a product.
- **Small categories** (Student loan n = 39, Email channel n = 2, Web Referral n = 90) are unsuitable for segment comparisons.
- The data covers one company, with no benchmark against other institutions or consumer populations, so complaint counts are not rates.

## 9. Cross-track integration
- `kpi_results/` and `KPI_Definitions.md` give the Data Science, ML and GenAI tracks one shared set of validated definitions and baseline numbers.
- ML track: the monthly series (`kpi03`) has no missing months; treat May 2017 and Aug 2023 as boundary periods.
- GenAI track: `run_kpis.py` and `kpi_queries.sql` can serve as the controlled calculation layer, so assistant answers come from actual queries.

## 10. Attribution
Data: Consumer Financial Protection Bureau, Consumer Complaints on Financial Products and Services (Bank of America, 2017-2023), supplied by AnalystLab Africa.
