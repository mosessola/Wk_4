"""
Runs every query in kpi_queries.sql against the cleaned data (SQLite), exports each result
to kpi_results/*.csv and one Excel workbook, then CROSS-VALIDATES the headline KPIs against
an independent pandas calculation. Fails loudly if SQL and pandas disagree.
Usage: python run_kpis.py [cleaned_csv] [out_dir]
"""
import sys, re, sqlite3, os, pandas as pd, numpy as np
here = os.path.dirname(os.path.abspath(__file__))
CSV = sys.argv[1] if len(sys.argv) > 1 else os.path.join(here, "Consumer_Complaints_Cleaned.csv")
OUT = sys.argv[2] if len(sys.argv) > 2 else here
os.makedirs(f"{OUT}/kpi_results", exist_ok=True)

df = pd.read_csv(CSV, parse_dates=["Date submitted", "Date received", "Month_Start"])
for c in ["Timely_Valid", "Is_In_Progress", "Long_Interval_Flag", "Is_Boundary_Month", "Is_Partial_Year", "Weekend_Submission"]:
    df[c] = df[c].astype(int)
for c in ["Date submitted", "Date received", "Month_Start"]:
    df[c] = df[c].dt.strftime("%Y-%m-%d")
con = sqlite3.connect(":memory:")
df.to_sql("complaints", con, index=False)

sql = open(f"{here}/kpi_queries.sql").read()
blocks = re.split(r"^-- name:\s*(\S+)\s*$", sql, flags=re.M)[1:]
res = {}
for name, body in zip(blocks[0::2], blocks[1::2]):
    q = "\n".join(l for l in body.splitlines() if not l.strip().startswith("--")).strip()
    res[name] = pd.read_sql_query(q, con)
    res[name].to_csv(f"{OUT}/kpi_results/{name}.csv", index=False)
print(f"Ran {len(res)} queries")

# ---------- independent pandas cross-check ----------
raw = pd.read_csv(CSV, parse_dates=["Date submitted", "Date received"])
d = (raw["Date received"] - raw["Date submitted"]).dt.days
valid = raw[raw["Timely response?"].isin(["Yes", "No"])]
checks = []
def chk(name, sql_val, pd_val, tol=1e-6):
    ok = abs(float(sql_val) - float(pd_val)) <= tol
    checks.append(dict(check=name, sql=sql_val, pandas=pd_val, match=ok))
chk("Total complaints", res["kpi01_total_complaints"].total_complaints[0], len(raw))
chk("Sum of annual volume", res["kpi02_annual_volume"].complaints.sum(), len(raw))
chk("Sum of monthly volume", res["kpi03_monthly_volume"].complaints.sum(), len(raw))
chk("Sum of product volume", res["kpi04_07_product_volume_and_share"].complaints.sum(), len(raw))
chk("Product shares sum to ~100", res["kpi04_07_product_volume_and_share"].pct_of_total.sum(), 100, 0.05)
chk("Top product volume", res["kpi04_07_product_volume_and_share"].complaints[0], raw.Product.value_counts().iloc[0])
chk("Sum of issue volume", res["kpi05_issue_volume"].complaints.sum(), len(raw))
chk("Sum of sub-product volume", res["kpi06a_subproduct_volume"].complaints.sum(), len(raw))
chk("Sum of sub-issue volume", res["kpi06b_subissue_volume"].complaints.sum(), len(raw))
chk("Sum of response categories", res["kpi08_response_distribution"].complaints.sum(), len(raw))
chk("Timely denominator", res["kpi09_timely_overall"].valid_records_denominator[0], len(valid))
chk("Timely %", res["kpi09_timely_overall"].timely_pct[0], round((valid["Timely response?"] == "Yes").mean() * 100, 2), 0.005)
chk("Timely excluded", res["kpi09_timely_overall"].excluded_not_assessed[0], len(raw) - len(valid))
chk("In progress count", res["kpi10_in_progress"].in_progress_complaints[0], (raw["Company response to consumer"] == "In progress").sum())
chk("Avg interval", res["kpi11_forwarding_interval_summary"].avg_days[0], round(d.mean(), 3), 0.0005)
chk("Median interval", res["kpi11_forwarding_interval_summary"].median_days[0], d.median())
chk("Max interval", res["kpi11_forwarding_interval_summary"].max_days[0], d.max())
chk("Same-day %", res["kpi11_forwarding_interval_summary"].pct_same_day[0], round((d == 0).mean() * 100, 2), 0.005)
chk("Long intervals (30+)", res["kpi11_forwarding_interval_summary"].long_interval_30plus[0], (d >= 30).sum())
chk("Interval bands sum", res["kpi11b_interval_distribution"].complaints.sum(), len(raw))
yoy = res["kpi12_yoy_calendar_year"]; ann = raw["Date submitted"].dt.year.value_counts().sort_index()
chk("YoY 2022 vs 2021 %", yoy.loc[yoy.Year == 2022, "yoy_pct"].iloc[0], round((ann[2022] / ann[2021] - 1) * 100, 2), 0.005)
chk("Annual 2020 count", yoy.loc[yoy.Year == 2020, "complaints"].iloc[0], ann[2020])
chk("Monthly months count", len(res["kpi03_monthly_volume"]), raw["Date submitted"].dt.to_period("M").nunique())
v = pd.DataFrame(checks); v.to_csv(f"{OUT}/kpi_results/_cross_validation_sql_vs_pandas.csv", index=False)
print(v.to_string(index=False))
assert v.match.all(), "SQL and pandas results disagree - investigate!"
print("\nALL CROSS-VALIDATION CHECKS PASSED")

with pd.ExcelWriter(f"{OUT}/KPI_Results.xlsx", engine="openpyxl") as w:
    v.to_excel(w, sheet_name="Cross_Validation", index=False)
    for name, t in res.items():
        t.to_excel(w, sheet_name=name[:31], index=False)
    for ws in w.book.worksheets:
        for col in ws.columns:
            ws.column_dimensions[col[0].column_letter].width = min(60, max(10, max(len(str(c.value or "")) for c in col[:60]) + 2))
        for c in ws[1]:
            c.font = c.font.copy(bold=True, name="Arial")
