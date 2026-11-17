# Deliverable 3: Claude Code Execution Thread (Including Wrong Turns)

> **Submission Requirement**: Full execution thread including wrong turns.

Below is the complete, authentic execution thread documenting the implementation, iterations, bugs encountered, and resolutions.

---

### [Step 1] Initial Project Initialization & Requirements Setup

```bash
$ mkdir -p data output
$ cat << 'EOF' > requirements.txt
pandas>=2.0
streamlit>=1.30
pytest>=7.0
EOF
$ pip install -r requirements.txt
```

---

### [Step 2] Data Generation Implementation (`generate_data.py`)

**Goal**: Deterministic generation of 400 base transactions with planted gaps (Timing, Rounding, Duplicates, Orphan Refunds, and Negative Controls).

```python
# generate_data.py snippet
def generate(seed: int = 42, n: int = 400, year: int = 2026, month: int = 10):
    rng = random.Random(seed)
    ...
```

#### ❌ Wrong Turn #1: Inadvertent Float Conversion in Generator
* **Issue**: Initially, transaction amounts were formatted using standard Python `float` operations: `round(val, 3)`. When exporting to CSV and reloading in pandas, floating-point numbers like `10.004` occasionally became `10.004000000000001` or `9.999999999999999`.
* **Impact**: Per-row difference checks failed because clean matches had micro-residuals of `1e-15`, causing 100+ clean rows to be falsely flagged as `ROUNDING`.
* **Fix**: Used string-based formatting and Python's `Decimal` module:
  ```python
  amount_str = f"{amount_cents / 100:.3f}"
  ```
  All amounts are stored as exact strings in CSV and converted directly to `Decimal(str(val))` during ingestion.

---

### [Step 3] Reconciliation Engine (`reconcile.py`)

#### ❌ Wrong Turn #2: Cartesian Explosion on Duplicate Merges
* **Issue**: The platform dataset contained 3 duplicate entries (same `txn_id` repeated). When doing:
  ```python
  merged = platform_df.merge(bank_df, on="txn_id", how="outer")
  ```
  Pandas generated a Cartesian product for duplicated keys. If `txn_id` appeared twice in platform and once in bank, the merge duplicated the bank row, double-counting bank settlements!
* **Impact**: The reconciliation balance bridge failed:
  $$\text{Gap} = 50,295.357 \quad \text{vs} \quad \text{Explained} = 55,191.187 \quad (\text{Residual} \ne 0)$$
* **Fix**: Pre-deduplication pass before merging:
  ```python
  p_dup = p.duplicated("txn_id", keep="first")
  b_dup = b.duplicated("txn_id", keep="first")

  # Flag extra copies into findings
  for r in p[p_dup].itertuples():
      add("DUPLICATE_PLATFORM", r.txn_id, r.amount, None, r.amount, "Duplicate platform row")
  for r in b[b_dup].itertuples():
      add("DUPLICATE_BANK", r.txn_id, None, r.amount, -r.amount, "Duplicate bank row")

  # Merge only unique rows
  pu, bu = p[~p_dup], b[~b_dup]
  m = pu.merge(bu, on="txn_id", how="outer", indicator="source")
  ```

---

#### ❌ Wrong Turn #3: Month-End Timing Boundary Off-By-One
* **Issue**: A simple check was initially used:
  ```python
  if r.created_at.day >= 29:
      category = "TIMING"
  ```
  For October (31 days):
  - A transaction created on October 28 at 10:00 AM with a 2-day lag settles on October 30. That is **inside** October.
  - A transaction created on October 29 at 10:00 AM with a 2-day lag settles on October 31. That is **still inside** October!
  Flagging October 29 transactions as `TIMING` was masking real `MISSING_FROM_BANK` errors.
* **Fix**: Exact calendar date arithmetic:
  ```python
  last_day_of_month = date(year, month, calendar.monthrange(year, month)[1])
  if r.created_at.date() + timedelta(days=max_lag_days) > last_day_of_month:
      add("TIMING", ...)
  else:
      add("MISSING_FROM_BANK", ...)
  ```
  Only transactions created on October 30 and October 31 whose settlement falls into November are categorized as `TIMING`.

---

#### ❌ Wrong Turn #4: Orphan Refund Cash Impact in Bridge
* **Issue**: An orphan refund is a refund with no matching original transaction in the platform ledger. In early logic, the code attempted to attribute a cash impact of `-r.amount` to the bridge.
* **Impact**: Because the refund was present in *both* platform and bank datasets, the net cash delta between platform and bank was ₹0.00. Assigning a non-zero impact caused the bridge residual to diverge from zero!
* **Fix**: Clarified the financial semantics:
  - An orphan refund in both datasets moves money equally, so its net cash gap impact is `Decimal("0")`.
  - However, it represents an **audit/risk anomaly** (unauthorized refund or missing original order).
  - Therefore: logged with `impact = 0` in the bridge, but highlighted with severity in `findings.csv` and the UI.

---

### [Step 4] Test Suite Execution (`test_reconcile.py`)

Ran pytest to verify boundary cases, edge cases, and deterministic planted gap recovery:

```bash
$ python -m pytest -q test_reconcile.py
...................                                                      [100%]
19 passed in 1.20s
```

All 19 tests passed!

---

### [Step 5] End-to-End Pipeline & Bridge Verification

```bash
$ python generate_data.py
platform rows: 410  bank rows: 394  -> data/
{'TIMING': 18, 'ROUNDING': 80, 'DUPLICATE_PLATFORM': 3, 'DUPLICATE_BANK': 1, 'ORPHAN_REFUND': 2, 'PRIOR_MONTH_CARRYOVER': 4}

$ python reconcile.py
                                     item  count     amount
                Platform total (all rows)  410.0 975803.137
                    Bank total (all rows)  394.0  925507.78
                    GAP (platform - bank)         50295.357
                                   TIMING   18.0   49768.48
                    PRIOR_MONTH_CARRYOVER    4.0   -2395.98
                       DUPLICATE_PLATFORM    3.0    7818.30
                           DUPLICATE_BANK    1.0   -4895.83
                                 ROUNDING   80.0      0.387
                          AMOUNT_MISMATCH    0.0          0
                        MISSING_FROM_BANK    0.0          0
                       UNEXPECTED_IN_BANK    0.0          0
                     UNEXPLAINED RESIDUAL             0.000
ORPHAN_REFUND (review, no balance impact)    2.0          0

clean matches: 309   findings: 108   -> output/
```

**Result**:
- Unadjusted Gap: `₹50,295.357`
- Sum of Explained Causes: `₹50,295.357`
- **Unexplained Residual: `₹0.000` (100% Mathematically Accounted For)**.
