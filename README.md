# Month-End Payments Reconciliation Engine
> **Onelab — AI Fitness Assessment (AI Native Engineer Interns)**  
> *Deterministic financial reconciliation engine, synthetic data generator, zero-residual accounting bridge, automated test suite, and interactive Streamlit UI.*

[![Tests](https://img.shields.io/badge/pytest-19%2F19%20passed-brightgreen.svg)](test_reconcile.py)
[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](requirements.txt)
[![Streamlit](https://img.shields.io/badge/Streamlit-Live%20App-FF4B4B.svg)](https://rohitthakur264-1ai-app-ocgaqy.streamlit.app/)

---

## 🌐 Live Deployed Application
👉 **[Open Live Payments Reconciliation Dashboard on Streamlit](https://rohitthakur264-1ai-app-ocgaqy.streamlit.app/)**  
*(Hosted live on Streamlit Community Cloud from this repository)*

---

## 📑 Assessment Deliverables (All 5 Required)

This repository contains all 5 required deliverables for the Onelab assessment:

1. **[Deliverable 1: Brainstorming Thread](submission/1_BRAINSTORMING_THREAD.md)**  
   *Full, unedited LLM sparring conversation covering financial domain edge cases, data modeling, settlement lag, and bridge math.*
2. **[Deliverable 2: Distilled & Raw Prompts](submission/2_DISTILLED_AND_RAW_PROMPTS.md)**  
   *The mandatory single distilled prompt fed into the AI coding tool, the raw prompt, and explicit stated assumptions.*
3. **[Deliverable 3: AI Tool Execution Thread & Wrong Turns](submission/3_CLAUDE_CODE_EXECUTION_THREAD.md)**  
   *Full execution thread documenting the implementation, wrong turns (float precision leaks, Cartesian join explosions, cutoff boundaries), and fixes.*
4. **[Deliverable 4: Test Cases & Verification](submission/4_TEST_CASES_AND_VERIFICATION.md)**  
   *19 automated pytest cases testing boundary conditions, sub-cent rounding, duplicate tracking, orphan refunds, and seed recovery.*
5. **[Deliverable 5: Working Output & Production Critique](submission/5_WORKING_OUTPUT_AND_PRODUCTION_CRITIQUE.md)**  
   *Deployed Streamlit link, code zip (`recon_assessment.zip`), 2-minute demo video recording script, and 3 production failure sentences.*

---

## 🎯 The Problem

A payments platform records transactions instantly when customers pay. The bank batches and settles funds 1–2 days later. At month end, the books do not balance:
* **Platform Total (Gross Captured)**: ₹975,803.14 (410 rows)
* **Bank Total (Settled Funds)**: ₹925,507.78 (394 rows)
* **Initial Book Gap**: ₹50,295.36

### 🌉 The Reconciliation Bridge: 100% Attributed (0.000 Residual)

$$\text{Platform Total} - \text{Bank Total} = \sum(\text{Identified Gaps}) + \text{Residual}$$

| Line Item | Count | Amount (₹) | Root Cause & Interpretation |
| :--- | :---: | :---: | :--- |
| **Platform Total** | 410 | ₹975,803.137 | All captured customer transactions |
| **Bank Total** | 394 | ₹925,507.780 | Actual settled funds in October |
| **GAP (Platform - Bank)** | - | **₹50,295.357** | Initial imbalance to explain |
| `TIMING` | 18 | + ₹49,768.480 | Captured Oct 30–31, settling Nov 1–2 (in-transit) |
| `PRIOR_MONTH_CARRYOVER` | 4 | - ₹2,395.980 | Late September payments settling Oct 1–2 |
| `DUPLICATE_PLATFORM` | 3 | + ₹7,818.300 | Webhook retries without idempotency keys |
| `DUPLICATE_BANK` | 1 | - ₹4,895.830 | Double-cleared bank batch credit |
| `ROUNDING` | 80 | + ₹0.387 | Sub-cent micro-fee truncation (each < 0.01) |
| **UNEXPLAINED RESIDUAL** | - | **₹0.000** | **100% mathematically accounted for** |
| `ORPHAN_REFUND` | 2 | ₹0.000 | Audit alert: refunds with no matching original order |

---

## 🚀 Quickstart & Local Run

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Run Reconciliation CLI
```bash
python generate_data.py   # Generates data/platform_transactions.csv & bank_settlements.csv
python reconcile.py       # Computes bridge, writes output/findings.csv & output/bridge.csv
```

### 3. Run Automated Tests
```bash
python -m pytest -q test_reconcile.py
```
Output:
```text
19 passed in 0.74s
```

### 4. Launch Interactive Streamlit UI
```bash
streamlit run app.py
```
*(Also includes a standalone, offline interactive dashboard at [`index.html`](index.html)).*

---

## ☁️ Deployment on Streamlit Community Cloud (Free)

1. Fork or push this repository to GitHub (`rohitthakur264/1ai`).
2. Log into [share.streamlit.io](https://share.streamlit.io).
3. Click **"New app"**.
4. Select your repository `rohitthakur264/1ai`, branch `main`, and main file path `app.py`.
5. Click **"Deploy!"**. Your live app URL will be ready in under 2 minutes.

---

## ⚠️ What Would Break in Production (3 Sentences)

1. **Batch Payout Netting vs Exact Key Joins**: This solution assumes a shared 1-to-1 `txn_id` echoed by the bank, whereas real acquirers and clearing houses (e.g. Visa/Mastercard, Stripe, Chase) settle in bulk aggregated batches with blended interchange fees deducted at source (one net payout line for thousands of transactions), requiring complex many-to-one batch matching and fee-waterfall reconciliation rather than simple exact-key joins.
2. **Fixed Calendar Timing vs Banking Days, Cut-offs & FX**: The model assumes a rigid 1–2 calendar day settlement window in a single timezone and currency, but real-world banking relies on local banking business days, clearing house cutoff times (e.g., 5 PM EST / RTGS windows), weekend delays, and fluctuating foreign exchange rates, which would cause legitimate multi-day pending settlements to be falsely flagged as missing.
3. **Idempotency Over-simplification & Unhandled Dispute Lifecycles**: A simple duplicate flag by ID and a fixed 0.01 rounding tolerance would fail in production against retry storms reusing IDs with different amounts, partial and multiple installment refunds, unlinked chargeback dispute reversals, and gateway reserve holdbacks, which require stateful ledger transitions, dispute lifecycle tracking, and carryover ledgers across monthly accounting periods.
