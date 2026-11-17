"""Month-end reconciliation: platform ledger vs bank settlements.

Every row is classified, and a bridge proves the totals:
    platform_total - bank_total = sum(category impacts) + unexplained residual
A non-zero residual means some row was not classified (a bug, or a gap type we don't know).

Money uses Decimal everywhere - never float.
"""
from __future__ import annotations

import argparse
import calendar
from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path

import pandas as pd

ZERO = Decimal("0")
ROUNDING_TOLERANCE = Decimal("0.01")   # per-row diffs below this are 'rounding', not errors
MAX_LAG_DAYS = 2                       # bank settles 1-2 days after payment

# categories that move the platform-vs-bank gap, in bridge order
BRIDGE_ORDER = ["TIMING", "PRIOR_MONTH_CARRYOVER", "DUPLICATE_PLATFORM", "DUPLICATE_BANK",
                "ROUNDING", "AMOUNT_MISMATCH", "MISSING_FROM_BANK", "UNEXPECTED_IN_BANK"]
FINDING_COLS = ["category", "txn_id", "platform_amount", "bank_amount", "impact", "detail"]


def _dec(v) -> Decimal:
    return Decimal(str(v).strip())


def _prep(platform_df: pd.DataFrame, bank_df: pd.DataFrame):
    p, b = platform_df.copy(), bank_df.copy()
    p["amount"] = p["amount"].map(_dec)
    p["created_at"] = pd.to_datetime(p["created_at"])
    if "original_txn_id" not in p:
        p["original_txn_id"] = ""
    p["original_txn_id"] = p["original_txn_id"].fillna("").astype(str)
    b = b.rename(columns={"bank_ref": "txn_id"})
    b["amount"] = b["amount"].map(_dec)
    b["settled_at"] = pd.to_datetime(b["settled_at"])
    return p, b


def reconcile(platform_df, bank_df, year: int, month: int,
              tolerance: Decimal = ROUNDING_TOLERANCE, max_lag_days: int = MAX_LAG_DAYS) -> dict:
    p, b = _prep(platform_df, bank_df)
    first = date(year, month, 1)
    last = date(year, month, calendar.monthrange(year, month)[1])
    findings = []

    def add(category, txn_id, p_amt, b_amt, impact, detail):
        findings.append(dict(zip(FINDING_COLS, [category, txn_id, p_amt, b_amt, impact, detail])))

    # 1) duplicates inside one dataset (extra copies only; first occurrence is kept)
    p_dup = p.duplicated("txn_id", keep="first")
    b_dup = b.duplicated("txn_id", keep="first")
    for r in p[p_dup].itertuples():
        add("DUPLICATE_PLATFORM", r.txn_id, r.amount, None, r.amount,
            "txn_id appears more than once in the platform ledger; extra copy overstates platform total")
    for r in b[b_dup].itertuples():
        add("DUPLICATE_BANK", r.txn_id, None, r.amount, -r.amount,
            "bank_ref appears more than once in the bank file; extra copy overstates bank total")
    pu, bu = p[~p_dup], b[~b_dup]

    # 2) refunds whose original payment is not in the ledger (flag only, no balance impact)
    payment_ids = set(pu.loc[pu["type"] == "PAYMENT", "txn_id"])
    for r in pu[pu["type"] == "REFUND"].itertuples():
        if r.original_txn_id not in payment_ids:
            add("ORPHAN_REFUND", r.txn_id, r.amount, None, ZERO,
                f"refund references '{r.original_txn_id or '(blank)'}' which is not in the ledger - review")

    # 3) match on txn_id and classify every remaining row
    m = pu.merge(bu, on="txn_id", how="outer", suffixes=("_p", "_b"), indicator="source")
    clean = 0
    for r in m.itertuples():
        if r.source == "both":
            diff = r.amount_p - r.amount_b
            if diff == ZERO:
                clean += 1
            elif abs(diff) < tolerance:
                add("ROUNDING", r.txn_id, r.amount_p, r.amount_b, diff,
                    f"differs by {diff} - below per-row tolerance, only visible when summed")
            else:
                add("AMOUNT_MISMATCH", r.txn_id, r.amount_p, r.amount_b, diff,
                    f"amounts differ by {diff}")
        elif r.source == "left_only":   # in platform, not in bank
            if r.created_at.date() + timedelta(days=max_lag_days) > last:
                add("TIMING", r.txn_id, r.amount_p, None, r.amount_p,
                    "created at month end; bank settlement expected next month")
            else:
                add("MISSING_FROM_BANK", r.txn_id, r.amount_p, None, r.amount_p,
                    "should have settled within the month but is absent from the bank file")
        else:                           # in bank, not in platform
            if r.settled_at.date() <= first + timedelta(days=max_lag_days - 1):
                add("PRIOR_MONTH_CARRYOVER", r.txn_id, None, r.amount_b, -r.amount_b,
                    "settled in first days of month; probably last month's payment (confirm vs prior ledger)")
            else:
                add("UNEXPECTED_IN_BANK", r.txn_id, None, r.amount_b, -r.amount_b,
                    "bank settled money with no platform record")

    f = pd.DataFrame(findings, columns=FINDING_COLS)
    p_total = sum(p["amount"], ZERO)
    b_total = sum(b["amount"], ZERO)
    gap = p_total - b_total

    rows = [("Platform total (all rows)", len(p), p_total),
            ("Bank total (all rows)", len(b), b_total),
            ("GAP (platform - bank)", None, gap)]
    explained = ZERO
    for cat in BRIDGE_ORDER:
        g = f[f["category"] == cat]
        amt = sum(g["impact"], ZERO)
        explained += amt
        rows.append((cat, len(g), amt))
    residual = gap - explained
    rows.append(("UNEXPLAINED RESIDUAL", None, residual))
    rows.append(("ORPHAN_REFUND (review, no balance impact)", int((f["category"] == "ORPHAN_REFUND").sum()), ZERO))
    bridge = pd.DataFrame(rows, columns=["item", "count", "amount"])

    return {"findings": f, "bridge": bridge, "platform_total": p_total, "bank_total": b_total,
            "gap": gap, "residual": residual, "clean_matches": clean}


def to_display(df: pd.DataFrame) -> pd.DataFrame:
    def fmt(v):
        if isinstance(v, Decimal):
            return format(v, "f")
        if v is None or (isinstance(v, float) and v != v):
            return ""
        return v
    out = df.copy()
    for c in out.columns:
        out[c] = out[c].map(fmt)
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--platform", default="data/platform_transactions.csv")
    ap.add_argument("--bank", default="data/bank_settlements.csv")
    ap.add_argument("--month", help="YYYY-MM (default: month of earliest platform transaction)")
    ap.add_argument("--out", default="output")
    a = ap.parse_args()
    p = pd.read_csv(a.platform, dtype=str, keep_default_na=False)
    b = pd.read_csv(a.bank, dtype=str, keep_default_na=False)
    if a.month:
        year, month = map(int, a.month.split("-"))
    else:
        d = pd.to_datetime(p["created_at"]).min()
        year, month = d.year, d.month
    res = reconcile(p, b, year, month)
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    to_display(res["findings"]).to_csv(out / "findings.csv", index=False)
    to_display(res["bridge"]).to_csv(out / "bridge.csv", index=False)
    print(to_display(res["bridge"]).to_string(index=False))
    print(f"\nclean matches: {res['clean_matches']}   findings: {len(res['findings'])}   -> {out}/")


if __name__ == "__main__":
    main()
