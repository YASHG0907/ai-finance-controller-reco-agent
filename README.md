# AI Finance Controller — Reconciliation Agent

**Razorpay Buildathon · Track 04: AI Finance Controller**

Closes one finance-ops loop end to end: reads a bank statement and an
invoice ledger, matches each payment to the invoice it settles, and
produces an **honest exception list** for everything it can't confidently
match — with **measured accuracy** proven against a held-out answer key,
not a cherry-picked demo.

---

## 1. What this project does

Every business has this problem: money comes into the bank account, but
someone still has to manually figure out _which invoice_ each payment
paid. Bank narrations are messy (typos, reference number noise,
abbreviated names), amounts don't always match exactly (fees, rounding),
and payments settle days after the invoice date.

This agent automates that matching:

1. **Exact + fuzzy matching** across three signals: amount closeness, date
   proximity, and text similarity of the description/party name.
2. Every match gets a transparent **confidence score** — you can see
   exactly why the agent thinks BNK0012 pays INV0034.
3. Anything that doesn't clear the confidence bar becomes an **exception**
   with a plain-English reason — never silently dropped or force-matched.
4. Accuracy is scored against a secretly-generated **ground truth** the
   engine never sees while matching — a held-out-style test, exactly what
   the brief's bar asks for: _"Throughput plus measured accuracy plus an
   honest exception list. One cherry-picked match proves nothing."_

### Actual results on the bundled sample data (default thresholds)

| Metric                                | Value                           |
| ------------------------------------- | ------------------------------- |
| Match rate                            | 86.9% (53/61 bank transactions) |
| Money reconciled                      | Rs. 22,44,345 of Rs. 22,55,184  |
| Bank exceptions                       | 8, each with a stated reason    |
| Unpaid invoices flagged               | 15                              |
| Precision (vs. held-out ground truth) | 1.000                           |
| Recall (vs. held-out ground truth)    | 1.000                           |
| F1 score                              | 1.000                           |

We also stress-tested the confidence threshold live: raising **minimum
confidence to auto-match** from 0.55 -> 0.89 drops the match rate from
86.9% -> 57.4% and recall from 1.000 -> 0.660, while **precision stays at
1.000 throughout**. That's a visible, tunable precision/recall trade-off
— not just a claimed one.

---

## 2. Project structure

```
reco-agent/
├── data_generator.py          # Creates realistic messy synthetic bank + invoice data
├── reconciliation_engine.py    # The core matching agent (no ML training needed)
├── evaluate.py                  # Grades the agent honestly against hidden ground truth
├── app.py                       # Streamlit dashboard — the live demo
├── requirements.txt
├── quickstart.sh                # One-command install + full pipeline run
├── .gitignore
├── README.md                     (this file)
├── VSCODE_GIT_SETUP.md           # Beginner VS Code + Git workflow, step by step
├── PITCH_SCRIPT.md               # Timed, pause-annotated 5-minute pitch script
├── PITCH_SCRIPT_TTS_PLAIN.txt    # Plain-text version for TTS engines
└── data/                         (created automatically when you run data_generator.py)
    ├── bank_statement.csv
    ├── invoices.csv
    ├── ground_truth.csv          (secret answer key — never shown to the engine)
    ├── matched.csv
    ├── exceptions_bank.csv
    └── exceptions_invoices.csv
```

---

## 3. Beginner setup (command line)

```bash
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
python3 data_generator.py
python3 reconciliation_engine.py
python3 evaluate.py
streamlit run app.py
```

Or just run everything in one shot:

```bash
bash quickstart.sh
```

**For a full step-by-step walkthrough using VS Code specifically — including
Git setup, staging, and commit-by-stage practices — see
[`VSCODE_GIT_SETUP.md`](./VSCODE_GIT_SETUP.md).**

---

## 4. How the matching actually works (for pitch / technical Q&A)

For every (bank transaction, invoice) pair, we compute three 0-1 scores:

| Signal         | What it checks                                                                                                                     | Weight |
| -------------- | ---------------------------------------------------------------------------------------------------------------------------------- | ------ |
| `amount_score` | How close the amounts are, tolerant of small fee deductions/rounding                                                               | 50%    |
| `desc_score`   | Fuzzy text similarity between bank narration and invoice party name (typos, abbreviations, reference-number noise) via `rapidfuzz` | 35%    |
| `date_score`   | How close the bank transaction date is to the invoice date, allowing for settlement lag                                            | 15%    |

These combine into one `confidence` score. Pairs are sorted by confidence
and greedily assigned — highest-confidence pairs matched first, and once
a bank transaction or invoice is claimed, it can't be reused. Anything
below `MIN_CONFIDENCE_TO_ACCEPT` (default 0.55) is left as an exception
rather than being force-matched.

### Known hard case, handled correctly

The synthetic data deliberately includes **duplicate invoices**: same
party, same amount, dates one day apart, where only one of the two
actually gets paid. The engine resolves this correctly using date
proximity as the tiebreaker (the paid invoice's date is always closer to
the actual bank settlement date) — this is a real, explainable signal,
not luck, and it's part of why precision holds at 1.000 even on the
harder cases.

---

## 👨‍💻 Author

**Yash Ghadi**
Electronics & Telecommunication Engineering · Software Development, Data Analytics, AI & Automation

- GitHub: [github.com/YASHG0907](https://github.com/YASHG0907)
- LinkedIn: [linkedin.com/in/yashg0907/](https://www.linkedin.com/in/yashg0907/)
- Email — yashghadi2005@gmail.com

---
