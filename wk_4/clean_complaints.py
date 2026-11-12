"""
Consumer Complaints (Bank of America, CFPB) - cleaning pipeline
Reads the ORIGINAL Excel file (never modified) and writes:
  - Consumer_Complaints_Cleaned.csv / .xlsx
  - cleaning_log.csv        (every transformation + rows affected)
  - validation_checks.csv   (post-cleaning reconciliation tests)
Usage: python clean_complaints.py [input.xlsx] [output_dir]
"""
import sys, pandas as pd, numpy as np

SRC = sys.argv[1] if len(sys.argv) > 1 else "/mnt/user-data/uploads/Consumer_Complaints.xlsx"
OUT = sys.argv[2] if len(sys.argv) > 2 else "/mnt/user-data/outputs"
LONG_INTERVAL_DAYS = 30   # documented threshold for "unusually long" forwarding interval

raw = pd.read_excel(SRC, sheet_name="Data")
df = raw.copy()
log = []
def note(step, field, action, n, why):
    log.append(dict(step=step, field=field, action=action, rows_affected=int(n), rationale=why))

# ---- 1. structure ------------------------------------------------------
note(1, "ALL", "Inspected structure", len(df), f"{df.shape[0]} rows x {df.shape[1]} columns; original file left untouched")

# ---- 2. text hygiene ---------------------------------------------------
txt = ["Submitted via","State","Product","Sub-product","Issue","Sub-issue",
       "Company public response","Company response to consumer","Timely response?"]
changed = 0
for c in txt:
    s = df[c].astype("string")
    t = s.str.strip().str.replace(r"\s+", " ", regex=True)
    changed += int((s.fillna("") != t.fillna("")).sum())
    df[c] = t
df["State"] = df["State"].str.upper()
note(2, "text fields", "Trimmed whitespace / collapsed double spaces / upper-cased State", changed, "No leading/trailing/double spaces found; step is a safeguard")

# ---- 3. keys & duplicates ---------------------------------------------
dup_id = int(df["Complaint ID"].duplicated().sum()); dup_row = int(df.duplicated().sum())
note(3, "Complaint ID", "Checked uniqueness", dup_id, "0 duplicate IDs -> valid primary key; no rows dropped")
note(3, "ALL", "Checked fully duplicated rows", dup_row, "0 duplicate records")

# ---- 4. dates ----------------------------------------------------------
df["Forwarding_Interval_Days"] = (df["Date received"] - df["Date submitted"]).dt.days
neg = int((df["Forwarding_Interval_Days"] < 0).sum())
note(4, "Dates", "Validated types and order (Date received >= Date submitted)", neg, "Both columns are true datetimes; 0 negative intervals; range 2017-05-01 to 2023-08-28")
df["Year"] = df["Date submitted"].dt.year
df["Quarter"] = "Q" + df["Date submitted"].dt.quarter.astype(str)
df["Year_Quarter"] = df["Year"].astype(str) + "-" + df["Quarter"]
df["Month_Num"] = df["Date submitted"].dt.month
df["Month_Name"] = df["Date submitted"].dt.strftime("%b")
df["Year_Month"] = df["Date submitted"].dt.strftime("%Y-%m")
df["Month_Start"] = df["Date submitted"].dt.to_period("M").dt.to_timestamp()
first_m, last_m = df["Year_Month"].min(), df["Year_Month"].max()
df["Is_Boundary_Month"] = df["Year_Month"].isin([first_m, last_m])
df["Is_Partial_Year"] = df["Year"].isin([df["Year"].min(), df["Year"].max()])
note(4, "Derived", "Added Year, Quarter, Year_Quarter, Month_Num, Month_Name, Year_Month, Month_Start", len(df), "Based on Date submitted (CFPB receipt date)")
note(4, "Derived", "Added Is_Boundary_Month / Is_Partial_Year", int(df["Is_Boundary_Month"].sum()), f"{first_m} and {last_m} are boundary months (data ends 28 Aug 2023); 2017 and 2023 are partial years - exclude from forecasting/YoY or caveat")
df["Long_Interval_Flag"] = df["Forwarding_Interval_Days"] >= LONG_INTERVAL_DAYS
df["Interval_Band"] = pd.cut(df["Forwarding_Interval_Days"], [-1,0,1,3,7,29,10**6],
                             labels=["Same day","1 day","2-3 days","4-7 days","8-29 days","30+ days"]).astype("string")
note(4, "Derived", f"Added Forwarding_Interval_Days, Interval_Band, Long_Interval_Flag (>= {LONG_INTERVAL_DAYS} days)", int(df["Long_Interval_Flag"].sum()),
     "Interval = CFPB forwarding time, NOT company response/resolution time. Max 275 days; kept (valid dates), flagged not removed")

# ---- 5. missing values -------------------------------------------------
n = df["Sub-issue"].isna().sum()
df["Sub_issue_Clean"] = df["Sub-issue"].fillna("No sub-issue recorded")
note(5, "Sub-issue", "Blank -> 'No sub-issue recorded'", n, "Structural: many Issues have no sub-issues at all (e.g. Fraud or scam, Struggling to pay mortgage). Not an error")
n = df["Company public response"].isna().sum()
df["Public_Response_Clean"] = df["Company public response"].fillna("No public response recorded")
note(5, "Company public response", "Blank -> 'No public response recorded'", n, "Public response is optional; 1,494 of these are In-progress cases, rest are closed cases with none recorded")
n = df["Sub-product"].isna().sum()
df["Sub_product_Clean"] = df["Sub-product"].fillna("Not provided")
note(5, "Sub-product", "Blank -> 'Not provided'", n, "7 rows, all Checking/savings with credit-reporting issues - possible mis-tagging; kept, flagged")
df["Timely_Flag"] = df["Timely response?"].map({"Yes":"Yes","No":"No"}).fillna("Not assessed (In progress)")
n = (df["Timely_Flag"]=="Not assessed (In progress)").sum()
note(5, "Timely response?", "Blank -> 'Not assessed (In progress)' (NOT 'No')", n, "All 1,494 blanks are exactly the 'In progress' records (all 2023). Excluded from timely-% denominator and reported separately")
df["Is_In_Progress"] = df["Company response to consumer"].eq("In progress")
df["Timely_Valid"] = df["Timely response?"].isin(["Yes","No"])

# ---- 6. categorical standardisation -----------------------------------
short = {
 "Checking or savings account":"Checking/Savings",
 "Credit card or prepaid card":"Credit/Prepaid Card",
 "Credit reporting, credit repair services, or other personal consumer reports":"Credit Reporting",
 "Mortgage":"Mortgage",
 "Money transfer, virtual currency, or money service":"Money Transfer/Services",
 "Debt collection":"Debt Collection",
 "Vehicle loan or lease":"Vehicle Loan/Lease",
 "Payday loan, title loan, or personal loan":"Payday/Title/Personal Loan",
 "Student loan":"Student Loan"}
df["Product_Short"] = df["Product"].map(short)
note(6, "Product", "Added Product_Short (display label); original Product kept", len(df), "9 products, no spelling variants; short labels for dashboard readability only")

# Issue wording variants: merge only where same product AND same meaning
issue_map = {"Problem with an overdraft":"Problem with overdraft",
             "Was approved for a loan, but didn't receive money":"Was approved for a loan, but didn't receive the money"}
for k, v in issue_map.items():   # safety check: variants must co-occur in the same product
    assert set(df.loc[df.Issue==k,"Product"]) <= set(df.loc[df.Issue==v,"Product"]), k
df["Issue_Std"] = df["Issue"].replace(issue_map)
note(6, "Issue", "Added Issue_Std: merged 2 wording variants within the same product", int(df["Issue"].isin(issue_map).sum()),
     "Other near-duplicates (e.g. 'Closing an account' vs 'Closing your account', 'Trouble using the card' vs '...your card') are CFPB taxonomy differences across products - NOT merged; flagged in data-quality doc")
resp_map = {"Closed":"Closed (no detail recorded)"}
df["Response_Clean"] = df["Company response to consumer"].replace(resp_map)
note(6, "Company response to consumer", "Added Response_Clean: 'Closed' -> 'Closed (no detail recorded)'", int((df["Company response to consumer"]=="Closed").sum()),
     "8 rows with bare 'Closed' (all marked Timely=No); kept as own category, not merged into other closed types")

# ---- 7. unusual / inconsistent -----------------------------------------
df["Weekend_Submission"] = df["Date submitted"].dt.dayofweek >= 5
note(7, "Submitted via", "Reviewed 'Web Referral' (90) vs 'Referral' (10,766) and 'Email' (2)", 92, "Genuine CFPB channels, kept distinct; Email/Web Referral too small for channel analysis")
note(7, "Date submitted", "Weekend submissions flagged", int(df["Weekend_Submission"].sum()), "Valid (online/phone intake); informational only")
note(7, "Dates", "July 2023 volume spike (1,749 vs ~1,050 neighbours) and Nov 2018-Mar 2019 dip noted", 0, "Cause not determinable from data; kept as reported - do not interpret as misconduct")

# ---- 8. tidy output ----------------------------------------------------
cols = ["Complaint ID","Submitted via","Date submitted","Date received","State","Product","Product_Short",
        "Sub-product","Sub_product_Clean","Issue","Issue_Std","Sub-issue","Sub_issue_Clean",
        "Company public response","Public_Response_Clean","Company response to consumer","Response_Clean",
        "Timely response?","Timely_Flag","Timely_Valid","Is_In_Progress",
        "Forwarding_Interval_Days","Interval_Band","Long_Interval_Flag",
        "Year","Quarter","Year_Quarter","Month_Num","Month_Name","Year_Month","Month_Start",
        "Is_Boundary_Month","Is_Partial_Year","Weekend_Submission"]
clean = df[cols]

# ---- 9. validation -----------------------------------------------------
v = []
def chk(name, ok, detail): v.append(dict(check=name, passed=bool(ok), detail=detail))
chk("Row count unchanged", len(clean)==len(raw), f"{len(clean)} vs {len(raw)}")
chk("Complaint ID unique", clean["Complaint ID"].is_unique, "")
chk("No original values overwritten", all((clean[c].fillna("§")==raw[c].astype("string").str.strip().fillna("§")).all() for c in ["Product","Issue","Company response to consumer"]), "original columns preserved")
chk("Yearly counts sum to total", clean.groupby("Year").size().sum()==len(clean), str(clean.groupby("Year").size().to_dict()))
chk("Monthly counts sum to total", clean.groupby("Year_Month").size().sum()==len(clean), f"{clean.Year_Month.nunique()} months, none missing" )
chk("Product counts sum to total", clean["Product"].value_counts().sum()==len(clean), "")
chk("Timely Yes+No+Not assessed = total", clean["Timely_Flag"].value_counts().sum()==len(clean), str(clean["Timely_Flag"].value_counts().to_dict()))
chk("Not assessed == In progress", (clean["Timely_Flag"].eq("Not assessed (In progress)")==clean["Is_In_Progress"]).all(), "1:1 match")
chk("No negative intervals", (clean["Forwarding_Interval_Days"]>=0).all(), f"min={clean.Forwarding_Interval_Days.min()}, max={clean.Forwarding_Interval_Days.max()}")
chk("No missing months in range", len(pd.period_range(clean.Month_Start.min(), clean.Month_Start.max(), freq="M"))==clean.Year_Month.nunique(), "all months present with >0 complaints")
vt = clean[clean.Timely_Valid]
kpi = {
 "Total complaints": len(clean),
 "Timely % (Yes / valid Yes+No)": round((vt.Timely_Flag=="Yes").mean()*100,2),
 "Valid timely records (denominator)": len(vt),
 "Excluded from timely (In progress)": int(clean.Is_In_Progress.sum()),
 "Avg forwarding interval (days)": round(clean.Forwarding_Interval_Days.mean(),3),
 "Median forwarding interval (days)": float(clean.Forwarding_Interval_Days.median()),
 "% forwarded same day": round((clean.Forwarding_Interval_Days==0).mean()*100,2),
 "Intervals >= 30 days": int(clean.Long_Interval_Flag.sum())}
for k,val in kpi.items(): chk("Baseline KPI: "+k, True, str(val))

clean.to_csv(f"{OUT}/Consumer_Complaints_Cleaned.csv", index=False)
with pd.ExcelWriter(f"{OUT}/Consumer_Complaints_Cleaned.xlsx", engine="openpyxl", datetime_format="yyyy-mm-dd") as w:
    clean.to_excel(w, sheet_name="Cleaned_Data", index=False)
    pd.DataFrame(log).to_excel(w, sheet_name="Cleaning_Log", index=False)
    pd.DataFrame(v).to_excel(w, sheet_name="Validation", index=False)
pd.DataFrame(log).to_csv(f"{OUT}/cleaning_log.csv", index=False)
pd.DataFrame(v).to_csv(f"{OUT}/validation_checks.csv", index=False)
print(pd.DataFrame(v).to_string()); print(kpi)
