
import os
import io
import json
import pandas as pd
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
import gspread_dataframe

# ── Authenticate to Google APIs ───────────────────────────────────────────────
SERVICE_ACCOUNT_FILE = os.environ["GOOGLE_SERVICE_ACCOUNT_JSON"]
creds = Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE,
    scopes=[
        "https://www.googleapis.com/auth/spreadsheets.readonly",
        "https://www.googleapis.com/auth/drive.readonly",
    ],
)
sheets_service = build("sheets", "v4", credentials=creds)

# ── Helper to load a sheet into a DataFrame ────────────────────────────────────
def read_sheet(sheet_name: str) -> pd.DataFrame:
    client = gspread.authorize(creds)
    ws     = client.open_by_key(os.environ["SPREADSHEET_ID"]).worksheet(sheet_name)
    return pd.DataFrame(ws.get_all_records())


# ── Load your sheets ───────────────────────────────────────────────────────────
bills_df   = read_sheet("MonthlyBills")
props_df   = read_sheet("Proportions")

# ── Clean & filter bills for the target month ─────────────────────────────────
bills_df["amount"] = pd.to_numeric(bills_df["amount"], errors="coerce")
month_bills = bills_df[
    (bills_df["month"] == os.environ["TARGET_MONTH"]) &
    bills_df["amount"].notna()
].copy()

# ── Compute income shares ───────────────────────────────────────────────────────
pr = props_df[props_df["month"] == os.environ["TARGET_MONTH"]]
if pr.empty:
    raise ValueError(f"No data for {os.environ['TARGET_MONTH']}")
income_series = pr.iloc[0].drop("month").fillna(0)
shares = (income_series / income_series.sum()).to_dict()

# ── Build per-bill breakdown ───────────────────────────────────────────────────
bills_summary = []
for _, row in month_bills.iterrows():
    amt = row["amount"]
    meta = {k: v for k, v in row.items() if k not in ["month", "amount"]}
    breakdown = {p: round(amt * share, 2) for p, share in shares.items()}
    bills_summary.append({**meta, "amount": round(amt, 2), "breakdown": breakdown})

# ── Compute overall totals ─────────────────────────────────────────────────────
total = month_bills["amount"].sum()
owed  = {p: round(total * share, 2) for p, share in shares.items()}

# ── Print final JSON ───────────────────────────────────────────────────────────
result = {
    "month": os.environ["TARGET_MONTH"],
    "bills": bills_summary,
    "total": round(total, 2),
    "proportions": shares,
    "owed": owed
}
print(json.dumps(result, indent=2))


