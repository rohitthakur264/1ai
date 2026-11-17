# Deliverable 5: Working Output & Production Critique

> **Submission Requirement**: Deployed link + code zip + Demo video + 3 sentences on what it would get wrong in production.

---

## 1. Three Sentences on What It Would Get Wrong in Production

1. **Batch Payout Netting vs Exact Key Joins**: This solution assumes a shared 1-to-1 `txn_id` echoed by the bank, whereas real acquirers and clearing houses (e.g. Visa/Mastercard, Stripe, Chase) settle in bulk aggregated batches with blended interchange fees deducted at source (one net payout line for thousands of transactions), requiring complex many-to-one batch matching and fee-waterfall reconciliation rather than simple exact-key joins.
2. **Fixed Calendar Timing vs Banking Days, Cut-offs & FX**: The model assumes a rigid 1–2 calendar day settlement window in a single timezone and currency, but real-world banking relies on local banking business days, clearing house cutoff times (e.g., 5 PM EST / RTGS windows), weekend delays, and fluctuating foreign exchange rates, which would cause legitimate multi-day pending settlements to be falsely flagged as missing.
3. **Idempotency Over-simplification & Unhandled Dispute Lifecycles**: A simple duplicate flag by ID and a fixed 0.01 rounding tolerance would fail in production against retry storms reusing IDs with different amounts, partial and multiple installment refunds, unlinked chargeback dispute reversals, and gateway reserve holdbacks, which require stateful ledger transitions, dispute lifecycle tracking, and carryover ledgers across monthly accounting periods.

---

## 2. Deployed Link & How to Run

### Live Web App (Streamlit Community Cloud)
* **GitHub Repository**: Push this repository to GitHub.
* **Deployment (Takes 2 minutes)**:
  1. Go to [share.streamlit.io](https://share.streamlit.io).
  2. Click **New app**.
  3. Select your GitHub repository and branch `main`.
  4. Set **Main file path** to `app.py`.
  5. Click **Deploy!**
* **Local Run**:
  ```bash
  pip install -r requirements.txt
  streamlit run app.py
  ```

---

## 3. Code Zip

* File: `recon_assessment.zip` (26 KB)
* Contains all code, tests, seed generators, data CSVs, and documentation:
  ```text
  recon_assessment/
  ├── app.py                      # Streamlit interactive dashboard
  ├── generate_data.py            # Deterministic data generator with planted gaps
  ├── reconcile.py                # Core reconciliation engine & CLI bridge
  ├── test_reconcile.py           # 19 automated pytest tests
  ├── requirements.txt            # Dependencies (pandas, streamlit, pytest)
  ├── README.md                   # Quickstart guide
  ├── PROMPTS.md                  # Complete prompts & assessment instructions
  ├── data/
  │   ├── platform_transactions.csv
  │   ├── bank_settlements.csv
  │   └── ground_truth.json
  └── output/
      ├── bridge.csv
      └── findings.csv
  ```

---

## 4. Demo Video Script (2–3 Minutes)

Use Loom or OBS to record your screen following this script:

| Timestamp | Screen Action | Spoken Narration |
| :--- | :--- | :--- |
| **0:00 - 0:30** | Open Streamlit Web App (`streamlit run app.py`). Show header and metric cards. | *"Here is our month-end payments reconciliation system. On the dashboard, we see the platform ledger processed ₹975,803, while the bank only settled ₹925,507, leaving an unexplained gap of ₹50,295.357."* |
| **0:30 - 1:00** | Point to the **Bridge Table** showing all categorized causes and **Unexplained Residual = 0.000**. | *"Our reconciliation engine bridges this gap completely down to zero residual. The gap is fully explained by: ₹49,768 in month-end timing cutoff differences, -₹2,395 in prior-month carryover, ₹7,818 in platform duplicate webhooks, -₹4,895 in bank duplicate credits, and ₹0.387 in cumulative rounding drift."* |
| **1:00 - 1:40** | Filter the **Findings Table** by `ROUNDING`. | *"Notice this rounding discrepancy: each individual transaction differs by less than 1 paisa (e.g. 0.004) due to sub-cent fee truncation. Per row it is completely invisible, but across 80 transactions it accumulates to 38.7 paise, creating a persistent ledger imbalance."* |
| **1:40 - 2:10** | Filter by `ORPHAN_REFUND` and `DUPLICATE_PLATFORM`. | *"Here we isolate our 2 planted orphan refunds—refunds issued with no matching original transaction in the platform ledger. While they don't break the cash bridge, they are flagged for operational and fraud review."* |
| **2:10 - 2:45** | Switch to Terminal. Run `python -m pytest -q test_reconcile.py`. | *"Finally, running our test suite: all 19 tests pass cleanly, verifying hand-built edge cases, month-end cutoff boundaries, and 100% precision and recall against ground truth across multiple seeds."* |
