# Onelab AI Fitness Assessment - Prompts & Submission Kit

> The assessment grades your PROCESS. Run these prompts yourself in Gemini / Claude Code / Cursor and
> export the REAL threads (including wrong turns). Do not paste cleaned-up or invented transcripts.

---

## 1. BRAINSTORMING PROMPT (paste into Gemini - deliverable #1)

```
You are my senior fintech engineer and sparring partner. I have a 2-hour assessment:

"A payments company's books don't balance at month end. They know every transaction their
platform processed. They know what the bank says actually arrived. The two should match.
They don't. Find out why. Show them where the gaps are."

No data is provided - I must generate my own. A platform records a transaction instantly when
a customer pays; the bank batches and settles funds 1-2 days later; at month end every
transaction should have a matching settlement. I must plant these gap types:
(a) a transaction that settled the following month
(b) a rounding difference that only shows when summed
(c) a duplicate entry in one dataset
(d) a refund with no matching original transaction
I must state my assumptions. Deliverables: working output (deployed link + code + demo video),
test cases, and 3 sentences on what would go wrong in production.

Do NOT write code yet. Work through this with me, and push back where my thinking is weak:
1. How does real-world payments reconciliation work (ledger vs bank statement, settlement lag,
   batches, fees, chargebacks)? What am I likely to oversimplify?
2. Propose a data model for both datasets (columns, types, how refunds and amounts are stored).
3. How do I generate data where the gaps are KNOWN ground truth, so I can test the detector?
   Make each planted gap realistic, not obvious.
4. For (b): how do I design a rounding gap that is invisible row-by-row but shows in the sum?
   Float vs Decimal implications?
5. Propose the matching algorithm and a classification taxonomy, including how to tell
   "timing difference" from "genuinely missing" near month end (boundary cases!).
6. How do I PROVE the explanation is complete? (I'm thinking a bridge: gap = sum of causes + residual.)
7. Edge cases and test cases I should write.
8. Stack/deployment suggestion for a 2-hour budget.
9. What would break in production? Give me the 3 most important points.
Finish with a short list of decisions I need to make and your recommendation for each.
```

**Good follow-ups to send in the same thread (keep it messy, it's meant to be real):**
- "Why not match on amount+date instead of txn_id? When would that be necessary?"
- "What if the bank sends one net payout line per batch instead of per transaction?"
- "Challenge my assumption that settlement lag is calendar days."
- "Review my test list - what am I missing?"

---

## 2. DISTILLED / RAW PROMPT (paste into Claude Code or Cursor - deliverable #2, mandatory)

```
Build a Python payments reconciliation project (pandas + Decimal, Streamlit UI, pytest) that finds
why a payments company's month-end books don't balance, and shows exactly where the gaps are.

CONTEXT: Platform records each transaction instantly at payment time. Bank batches and settles
1-2 days later. At month end every platform transaction should have a bank settlement.

FILES
1. generate_data.py - deterministic (seeded) generator for one month (default Oct 2026), ~400
   transactions, INR. Output platform_transactions.csv (txn_id, created_at, type PAYMENT|REFUND,
   amount, currency, original_txn_id) and bank_settlements.csv (settlement_id, bank_ref, settled_at,
   type, amount, currency). Bank file only contains settlements dated inside the month. Refunds are
   negative. Plant exactly these gaps and return a ground-truth dict (category -> txn_ids):
   - TIMING: payments created in the last 2 days whose settlement falls next month (absent from bank file)
   - ROUNDING: ~80 rows where platform keeps 3 decimals and bank truncates to 2; per-row diff < 0.01,
     material only when summed
   - DUPLICATE_PLATFORM (3) and DUPLICATE_BANK (1): same id twice in one dataset
   - ORPHAN_REFUND (2): refund whose original_txn_id is not in the ledger
   Also add 5 VALID refunds (with originals) and 4 PRIOR_MONTH_CARRYOVER bank rows (last month's late
   payments settling on day 1-2) as negative controls. Each txn carries at most one planted gap.
   Document every assumption in the module docstring.

2. reconcile.py - reconcile(platform_df, bank_df, year, month) -> dict with findings DataFrame
   (category, txn_id, platform_amount, bank_amount, impact, detail), a bridge DataFrame, totals and
   residual. Use Decimal, never float. Logic: dedupe each dataset by id (keep first, flag extras);
   flag refunds with unknown originals; outer-merge on txn_id and classify: exact match, ROUNDING
   (0 < |diff| < 0.01), AMOUNT_MISMATCH, TIMING (platform-only and created_date + 2 days > month end),
   MISSING_FROM_BANK (platform-only otherwise), PRIOR_MONTH_CARRYOVER (bank-only settled in first 2 days),
   UNEXPECTED_IN_BANK. Bridge must prove: platform_total - bank_total = sum(impacts) + residual,
   residual must be 0. Include a CLI that writes findings.csv and bridge.csv.

3. test_reconcile.py (pytest) - hand-built cases: clean data, timing-vs-missing boundary on Oct 28/29/30/31,
   rounding invisible per row but visible in sum, real mismatch not hidden as rounding, duplicates in
   each dataset, orphan vs valid refund, late-month bank-only row, empty inputs. Plus parametrized
   tests over 3 seeds asserting findings EXACTLY equal the generator's ground truth and residual == 0.

4. app.py - Streamlit: sidebar to generate synthetic data or upload two CSVs; metric cards (platform
   total, bank total, gap, unexplained); bridge table; findings table with category filter and CSV download.

Also write requirements.txt and README.md. Run pytest and fix until green. Keep code simple and commented.
```

---

## 3. CLAUDE CODE THREAD (deliverable #3)
Run the prompt above in Claude Code/Cursor. Export the **entire** session, including errors and fix-ups.
Reference solution is in this folder; compare against it, but your thread must be your own real run.

## 4. TEST CASES (deliverable #4)
`test_reconcile.py` - 19 tests (run `pytest -q`). Screenshot the green run for the submission.

## 5. WORKING OUTPUT (deliverable #5)
**Deploy (free, ~5 min):** push this folder to a public GitHub repo -> https://share.streamlit.io ->
New app -> pick repo, main file `app.py` -> Deploy. Paste the URL in your submission.
**Code zip:** `recon_assessment.zip` (provided).
**Demo video (2-3 min, screen record):**
1. Show the problem: platform total vs bank total, gap of ~50,295.
2. Generate data; show the planted-gap counts (sidebar "Planted gaps").
3. Show the bridge: every rupee of the gap attributed, UNEXPLAINED = 0.
4. Filter findings by category; click ROUNDING (80 rows, each < 0.01, total 0.387) - "invisible row by row".
5. Run `pytest -q` - 19 passed.

**3 sentences on what would get wrong in production (paste as-is or reword):**
1. This matches on a shared `txn_id`, but real banks usually settle in batches with one net payout line (fees deducted, no per-transaction reference), so production needs many-to-one batch matching with fuzzy fallbacks rather than exact-key joins.
2. The timing rule assumes a fixed 1-2 calendar-day lag in one timezone and currency, so weekends, bank holidays, cut-off times at month end and FX would create false TIMING/MISSING flags (and a "TIMING" label can mask a payment that never settles unless it is re-checked next month).
3. Dedupe-by-id and the 0.01 rounding tolerance can hide real problems - a retry reusing an id with a different amount, partial refunds, chargebacks or fees would be misclassified - so flagged items need human review, audit logging and carry-forward of open items across months.

## ASSUMPTIONS (state these in your submission)
A1 INR, single currency/timezone. A2 settlement lag = 1 or 2 calendar days. A3 bank echoes our txn_id as bank_ref.
A4 bank truncates to 2 decimals, platform keeps 3. A5 refunds are negative in both datasets.
A6 bank file contains only settlements dated within the month; prior-month payments settling on day 1-2 appear as carryover.
A7 orphan refunds exist in both datasets (so they flag for review but don't move the balance).
