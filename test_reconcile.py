"""Tests: hand-built edge cases + planted-gap recovery on generated data."""
from decimal import Decimal

import pandas as pd
import pytest

from generate_data import BANK_COLS, PLATFORM_COLS, generate
from reconcile import reconcile


def P(txn_id, created, amount, typ="PAYMENT", orig=""):
    return dict(txn_id=txn_id, created_at=created, type=typ, amount=amount,
                currency="INR", original_txn_id=orig)


def B(ref, settled, amount, typ="PAYMENT"):
    return dict(settlement_id=f"S-{ref}", bank_ref=ref, settled_at=settled, type=typ,
                amount=amount, currency="INR")


def run(platform, bank, year=2026, month=10):
    return reconcile(pd.DataFrame(platform, columns=PLATFORM_COLS),
                     pd.DataFrame(bank, columns=BANK_COLS), year, month)


def cats(res):
    return res["findings"]["category"].tolist()


# ---------- hand-built cases ----------

def test_clean_data_has_no_findings():
    res = run([P("T1", "2026-10-05T10:00:00", "100.00")], [B("T1", "2026-10-06", "100.00")])
    assert cats(res) == [] and res["gap"] == 0 and res["residual"] == 0


@pytest.mark.parametrize("created,expected", [
    ("2026-10-28T12:00:00", "MISSING_FROM_BANK"),  # 28+2 = Oct 30: should have settled
    ("2026-10-29T12:00:00", "MISSING_FROM_BANK"),  # 29+2 = Oct 31: still inside month
    ("2026-10-30T12:00:00", "TIMING"),              # 30+2 = Nov 1: legitimately next month
    ("2026-10-31T23:59:00", "TIMING"),
])
def test_timing_vs_missing_boundary(created, expected):
    res = run([P("T1", created, "50.00")], [])
    assert cats(res) == [expected] and res["residual"] == 0


def test_rounding_is_invisible_per_row_but_visible_in_sum():
    plat = [P(f"T{i}", "2026-10-05T10:00:00", "10.004") for i in range(3)]
    bank = [B(f"T{i}", "2026-10-06", "10.00") for i in range(3)]
    res = run(plat, bank)
    assert cats(res) == ["ROUNDING"] * 3            # none escalated to AMOUNT_MISMATCH
    assert res["gap"] == Decimal("0.012") and res["residual"] == 0


def test_real_amount_mismatch_not_hidden_as_rounding():
    res = run([P("T1", "2026-10-05T10:00:00", "10.00")], [B("T1", "2026-10-06", "9.50")])
    assert cats(res) == ["AMOUNT_MISMATCH"] and res["residual"] == 0


def test_platform_duplicate_flagged_once_and_not_double_matched():
    plat = [P("T1", "2026-10-05T10:00:00", "100.00")] * 2
    res = run(plat, [B("T1", "2026-10-06", "100.00")])
    assert cats(res) == ["DUPLICATE_PLATFORM"]
    assert res["gap"] == Decimal("100.00") and res["residual"] == 0


def test_bank_duplicate():
    res = run([P("T1", "2026-10-05T10:00:00", "100.00")],
              [B("T1", "2026-10-06", "100.00"), B("T1", "2026-10-06", "100.00")])
    assert cats(res) == ["DUPLICATE_BANK"] and res["gap"] == Decimal("-100.00")


def test_orphan_refund_flagged_valid_refund_not():
    plat = [P("T1", "2026-10-05T10:00:00", "100.00"),
            P("R1", "2026-10-06T10:00:00", "-100.00", "REFUND", "T1"),       # valid
            P("R2", "2026-10-07T10:00:00", "-30.00", "REFUND", "TXN-SEP-1")]  # orphan
    bank = [B("T1", "2026-10-06", "100.00"), B("R1", "2026-10-08", "-100.00", "REFUND"),
            B("R2", "2026-10-08", "-30.00", "REFUND")]
    res = run(plat, bank)
    f = res["findings"]
    assert f["category"].tolist() == ["ORPHAN_REFUND"] and f["txn_id"].tolist() == ["R2"]
    assert res["gap"] == 0                           # orphan is a review flag, not a balance gap


def test_bank_only_row_late_in_month_is_unexpected_not_carryover():
    res = run([], [B("X1", "2026-10-15", "75.00")])
    assert cats(res) == ["UNEXPECTED_IN_BANK"]


def test_empty_inputs():
    res = run([], [])
    assert res["gap"] == 0 and cats(res) == []


# ---------- planted-gap recovery on generated data ----------

@pytest.mark.parametrize("seed", [1, 42, 2026])
def test_every_planted_gap_found_and_nothing_else(seed):
    platform, bank, truth = generate(seed=seed)
    res = run(platform, bank)
    f = res["findings"]
    found = {c: sorted(g["txn_id"]) for c, g in f.groupby("category")}
    assert found == truth, "findings must equal the planted ground truth exactly"
    assert res["residual"] == 0


@pytest.mark.parametrize("seed", [1, 42, 2026])
def test_rounding_hidden_per_row_but_material_in_aggregate(seed):
    res = run(*generate(seed=seed)[:2])
    r = res["findings"][res["findings"]["category"] == "ROUNDING"]["impact"]
    assert all(abs(x) < Decimal("0.01") for x in r)
    assert sum(r, Decimal(0)) >= Decimal("0.01")


def test_generator_is_deterministic():
    assert generate(seed=7) == generate(seed=7)
    assert generate(seed=7) != generate(seed=8)
