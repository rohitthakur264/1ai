# Deliverable 2: Distilled Prompt and Raw Prompt (Mandatory)

> **Submission Requirement**: The single prompt you fed into Claude Code or Cursor or any other AI coding tool.

---

## 1. Raw Prompt (Initial Assessment Prompt)

```text
A payments company's books don't balance at month end. They know every transaction their platform processed. They know what the bank says actually arrived. The two should match. They don't. Find out why. Show them where the gaps are.

Test Data:
No files provided. Generate your own — that's part of the assessment. A payments platform records a transaction instantly when a customer pays. The bank batches and settles funds 1–2 days later. At month end every transaction should have a matching settlement.
Plant these gap types:
- a transaction that settled the following month
- a rounding difference that only shows when summed
- a duplicate entry in one dataset
- a refund with no matching original transaction.
State your assumptions. There are no wrong ones as long as you name them.

What to Submit:
1. Brainstorming thread (Full LLM convo. Do not clean it up)
2. Distilled prompt and Raw Prompt (mandatory)
3. Claude Code thread (Full execution thread including wrong turns)
4. Test cases (What you wrote to verify your solution works)
5. Working output (Deployed link + code zip + Demo video + 3 sentences on what it would get wrong in production)
```

---

## 2. Distilled Single Prompt (Fed into Claude Code / Cursor)

```text
Build a Python payments reconciliation project (pandas + Decimal, Streamlit UI, pytest) that finds why a payments company's month-end books don't balance, and shows exactly where the gaps are.

CONTEXT: Platform records each transaction instantly at payment time. Bank batches and settles 1-2 days later. At month end every platform transaction should have a bank settlement.

FILES TO IMPLEMENT:
1. generate_data.py - deterministic (seeded) generator for one month (default Oct 2026), ~400 transactions, INR. Output data/platform_transactions.csv (txn_id, created_at, type PAYMENT|REFUND, amount, currency, original_txn_id) and data/bank_settlements.csv (settlement_id, bank_ref, settled_at, type, amount, currency). Bank file only contains settlements dated inside the month. Refunds are negative amounts. Plant exactly these gaps and return a ground-truth dict (category -> txn_ids):
   - TIMING: payments created in the last 2 days whose settlement falls next month (absent from bank file)
   - ROUNDING: ~80 rows where platform keeps 3 decimals and bank truncates to 2; per-row diff < 0.01, material only when summed
   - DUPLICATE_PLATFORM (3) and DUPLICATE_BANK (1): same id twice in one dataset
   - ORPHAN_REFUND (2): refund whose original_txn_id is not in the ledger
   Also add 5 VALID refunds (with originals) and 4 PRIOR_MONTH_CARRYOVER bank rows (last month's late payments settling on day 1-2) as negative controls. Each txn carries at most one planted gap. Document every assumption in the module docstring.

2. reconcile.py - reconcile(platform_df, bank_df, year, month) -> dict with findings DataFrame (category, txn_id, platform_amount, bank_amount, impact, detail), a bridge DataFrame, totals and residual. Use Decimal, never float. Logic:
   - dedupe each dataset by id (keep first, flag extras into DUPLICATE_PLATFORM / DUPLICATE_BANK);
   - flag refunds with unknown originals as ORPHAN_REFUND;
   - outer-merge on txn_id and classify: exact match, ROUNDING (0 < |diff| < 0.01), AMOUNT_MISMATCH, TIMING (platform-only and created_date + 2 days > month end), MISSING_FROM_BANK (platform-only otherwise), PRIOR_MONTH_CARRYOVER (bank-only settled in first 2 days), UNEXPECTED_IN_BANK.
   Bridge must mathematically prove: platform_total - bank_total = sum(impacts) + residual, where residual must be strictly 0.000. Include a CLI that writes output/findings.csv and output/bridge.csv.

3. test_reconcile.py (pytest) - hand-built cases: clean data, timing-vs-missing boundary on Oct 28/29/30/31, rounding invisible per row but visible in sum, real mismatch not hidden as rounding, duplicates in each dataset, orphan vs valid refund, late-month bank-only row, empty inputs. Plus parametrized tests over 3 seeds asserting findings EXACTLY equal the generator's ground truth and residual == 0.

4. app.py - Streamlit: sidebar to generate synthetic data (with seed and N slider) or upload two CSVs; metric cards (platform total, bank total, gap, unexplained residual); bridge breakdown table; findings table with category multi-select filter and CSV download.

Also write requirements.txt and README.md. Run pytest and verify all tests pass with zero residual.
```

---

## 3. Explicit Stated Assumptions

* **A1 (Currency & Locale)**: Transactions are in INR (`₹`), processed within a single standard timezone (IST / UTC).
* **A2 (Settlement Window)**: The bank settlement window is 1 to 2 calendar days (`T + 1` or `T + 2`).
* **A3 (Reference Identifier)**: The bank echoes the platform's internal `txn_id` in its settlement records as `bank_ref`.
* **A4 (Precision & Truncation)**: The platform maintains 3 decimal places for micro-fee tracking; the bank clearing system truncates/rounds to 2 decimal places. Per-row differences under `0.01` are treated as cumulative rounding drift.
* **A5 (Sign Convention)**: Refunds and fee debits are represented as negative numbers in both datasets (`-amount`).
* **A6 (Month Boundary & Cutoff)**: The bank settlement statement strictly covers settlements cleared between the 1st and last day of the calendar month. Legitimate prior-month transactions settling on days 1–2 appear as `PRIOR_MONTH_CARRYOVER`.
* **A7 (Orphan Refund Nature)**: Orphan refunds (refunds with no corresponding original transaction in the platform ledger) move money in both accounts but represent an operational/compliance risk requiring manual review (`impact = 0` on unadjusted variance bridge, flagged for investigation).
