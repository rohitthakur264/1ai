"""Synthetic data generator for the payments reconciliation assessment.

Produces two datasets for one month (default Oct 2026):
  * platform ledger  - every transaction, recorded instantly when the customer pays
  * bank statement   - what the bank actually settled in that month (1-2 days after payment)

Planted gap types (ground truth is returned separately and NEVER read by reconcile.py):
  TIMING                 payment created at month end, bank settles it next month
  ROUNDING               platform stores 3 decimals, bank truncates to 2 -> tiny per-row diff,
                         visible only when summed
  DUPLICATE_PLATFORM /   same txn_id recorded twice in one dataset
  DUPLICATE_BANK
  ORPHAN_REFUND          refund whose original transaction is not in the ledger
Extra realism:
  PRIOR_MONTH_CARRYOVER  bank settles last month's late payments on day 1-2 of this month
  valid refunds          refunds WITH a matching original (negative control)

Assumptions (named, as the brief asks):
  A1 currency INR, single currency, single timezone
  A2 settlement lag is 1 or 2 CALENDAR days (no weekends/holidays)
  A3 the bank echoes our txn_id as `bank_ref` on each line (real banks often don't - see README)
  A4 bank truncates (rounds down) to 2 decimals; platform keeps 3 decimals
  A5 refunds are stored as negative amounts in both datasets
  A6 the bank file covers settlements dated inside the month only
"""
from __future__ import annotations

import argparse
import csv
import json
import random
from collections import defaultdict
from datetime import datetime, timedelta
from decimal import Decimal
from pathlib import Path

CENT = Decimal("0.01")
PLATFORM_COLS = ["txn_id", "created_at", "type", "amount", "currency", "original_txn_id"]
BANK_COLS = ["settlement_id", "bank_ref", "settled_at", "type", "amount", "currency"]


def _money(x: Decimal) -> str:
    return format(x, "f")


def generate(seed=42, n=400, year=2026, month=10, n_rounding=80,
             n_dup_platform=3, n_dup_bank=1, n_valid_refunds=5):
    rng = random.Random(seed)
    start = datetime(year, month, 1)
    nxt = datetime(year + (month == 12), month % 12 + 1, 1)
    last_day = (nxt - timedelta(days=1)).date()
    span = int((nxt - start).total_seconds())

    payments = []
    for i in range(1, n + 1):
        created = start + timedelta(seconds=rng.randrange(span))
        payments.append({
            "txn_id": f"TXN-{i:05d}",
            "created": created,
            "amount": (Decimal(rng.randint(500, 500_000)) / 100).quantize(CENT),
            "settle": created.date() + timedelta(days=rng.choice([1, 2])),
        })

    # disjoint selections so one transaction carries at most one planted gap
    refund_pool = [p for p in payments if p["created"].date() + timedelta(days=6) <= last_day]
    refund_src = rng.sample(refund_pool, n_valid_refunds)
    used = {p["txn_id"] for p in refund_src}
    pool = [p for p in payments if p["settle"] <= last_day and p["txn_id"] not in used]
    picks = rng.sample(pool, n_rounding + n_dup_platform + n_dup_bank)
    rounding = picks[:n_rounding]
    dup_p = picks[n_rounding:n_rounding + n_dup_platform]
    dup_b = picks[n_rounding + n_dup_platform:]
    frac = {p["txn_id"]: Decimal(rng.randint(1, 9)) / 1000 for p in rounding}

    platform, bank, truth = [], [], defaultdict(set)
    plat_rows = {}
    sid = 0

    def bank_row(ref, settled, typ, amt):
        nonlocal sid
        sid += 1
        bank.append({"settlement_id": f"STL-{sid:06d}", "bank_ref": ref,
                     "settled_at": settled.isoformat(), "type": typ,
                     "amount": _money(amt), "currency": "INR"})

    for p in payments:
        row = {"txn_id": p["txn_id"], "created_at": p["created"].isoformat(timespec="seconds"),
               "type": "PAYMENT", "amount": _money(p["amount"] + frac.get(p["txn_id"], Decimal(0))),
               "currency": "INR", "original_txn_id": ""}
        platform.append(row)
        plat_rows[p["txn_id"]] = row
        if p["settle"] <= last_day:
            bank_row(p["txn_id"], p["settle"], "PAYMENT", p["amount"])  # bank truncated amount
        else:
            truth["TIMING"].add(p["txn_id"])

    for p in rounding:
        truth["ROUNDING"].add(p["txn_id"])
    for p in dup_p:
        platform.append(dict(plat_rows[p["txn_id"]]))
        truth["DUPLICATE_PLATFORM"].add(p["txn_id"])
    for p in dup_b:
        bank_row(p["txn_id"], p["settle"], "PAYMENT", p["amount"])
        truth["DUPLICATE_BANK"].add(p["txn_id"])

    for k, p in enumerate(refund_src, 1):  # valid refunds (negative control)
        created = p["created"] + timedelta(hours=rng.randint(6, 48))
        settle = created.date() + timedelta(days=rng.choice([1, 2]))
        rid = f"RFD-{k:04d}"
        platform.append({"txn_id": rid, "created_at": created.isoformat(timespec="seconds"),
                         "type": "REFUND", "amount": _money(-p["amount"]), "currency": "INR",
                         "original_txn_id": p["txn_id"]})
        bank_row(rid, settle, "REFUND", -p["amount"])

    for k, (day, orig) in enumerate([(10, "TXN-SEP-00042"), (20, "TXN-SEP-00977")], 1):
        created = datetime(year, month, day, rng.randint(8, 20), rng.randint(0, 59))
        amt = (Decimal(rng.randint(1000, 100_000)) / 100).quantize(CENT)
        rid = f"RFD-{9000 + k}"
        platform.append({"txn_id": rid, "created_at": created.isoformat(timespec="seconds"),
                         "type": "REFUND", "amount": _money(-amt), "currency": "INR",
                         "original_txn_id": orig})
        bank_row(rid, created.date() + timedelta(days=1), "REFUND", -amt)
        truth["ORPHAN_REFUND"].add(rid)

    for k in range(1, 5):  # last month's late payments settling on day 1-2
        amt = (Decimal(rng.randint(500, 200_000)) / 100).quantize(CENT)
        ref = f"TXN-S{k:04d}"
        bank_row(ref, start.date() + timedelta(days=rng.choice([0, 1])), "PAYMENT", amt)
        truth["PRIOR_MONTH_CARRYOVER"].add(ref)

    platform.sort(key=lambda r: r["created_at"])
    bank.sort(key=lambda r: r["settled_at"])
    return platform, bank, {k: sorted(v) for k, v in truth.items()}


def write_csvs(platform, bank, truth, out_dir):
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    for name, cols, rows in [("platform_transactions.csv", PLATFORM_COLS, platform),
                             ("bank_settlements.csv", BANK_COLS, bank)]:
        with open(out / name, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=cols)
            w.writeheader()
            w.writerows(rows)
    # answer key, kept only for the test-suite; the reconciler never reads it
    (out / "ground_truth.json").write_text(json.dumps(truth, indent=2))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--n", type=int, default=400)
    ap.add_argument("--out", default="data")
    a = ap.parse_args()
    p, b, t = generate(seed=a.seed, n=a.n)
    write_csvs(p, b, t, a.out)
    print(f"platform rows: {len(p)}  bank rows: {len(b)}  -> {a.out}/")
    print({k: len(v) for k, v in t.items()})
