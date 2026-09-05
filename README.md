# AI Finance Controller — Reconciliation Agent
**Razorpay Buildathon · Track 04: AI Finance Controller**

Closes one finance-ops loop end to end: it reads a bank statement and an
invoice ledger, matches each payment to the invoice it settles, and produces
an **honest exception list** for everything it can't confidently match — with
**measured accuracy** proven against a held-out answer key, not a
cherry-picked demo.

---

## 1. What this project actually does

Every business has this problem: money comes into the bank account, but
someone still has to manually figure out *which invoice* each payment paid.
Bank narrations are messy (typos, reference number noise, abbreviated
names), amounts don't always match exactly (fees, rounding), and payments
settle days after the invoice date.

This agent automates that matching:

1. **Exact + fuzzy matching** across three signals: amount closeness, date
   proximity, and text similarity of the description/party name.
2. Every match gets a transparent **confidence score** — you can see exactly
   *why* the agent thinks BNK0012 pays INV0034.
3. Anything that doesn't clear the confidence bar becomes an **exception**
   with a plain-English reason — never silently dropped or force-matched.
4. Because we control the synthetic data generation, we secretly know the
   "correct" answer for every transaction. `evaluate.py` scores the agent
   against that hidden answer key — exactly what the brief's bar asks for:
   *"Throughput plus measured accuracy plus an honest exception list. One
   cherry-picked match proves nothing."*

---

## 2. Project structure

```
reco-agent/
├── data_generator.py       # Creates realistic messy synthetic bank + invoice data
├── reconciliation_engine.py # The core matching agent (no ML training needed)
├── evaluate.py              # Grades the agent honestly against hidden ground truth
├── app.py                   # Streamlit dashboard — THIS is what you demo live
├── requirements.txt
├── README.md                 (this file)
└── data/                     (created automatically when you run data_generator.py)
    ├── bank_statement.csv
    ├── invoices.csv
    ├── ground_truth.csv       (secret answer key — never shown to the engine)
    ├── matched.csv            (created after running the engine)
    ├── exceptions_bank.csv
    └── exceptions_invoices.csv
```

---

## 3. Complete beginner setup (step by step)

### Step 0 — Prerequisites
You need Python 3.9+ installed. Check with:
```bash
python3 --version
```
If that fails, install Python from [python.org](https://python.org) first.

### Step 1 — Get the files onto your machine
If you're starting from this chat, download the files into a folder called
`reco-agent`. If you're using this as a GitHub repo, clone it:
```bash
git clone <your-repo-url>
cd reco-agent
```

### Step 2 — Create a virtual environment (keeps dependencies clean)
```bash
python3 -m venv venv
source venv/bin/activate        # On Windows: venv\Scripts\activate
```

### Step 3 — Install dependencies
```bash
pip install -r requirements.txt
```

### Step 4 — Generate the synthetic dataset
```bash
python3 data_generator.py
```
You should see output confirming ~60 bank transactions and ~65+ invoices
were created in a new `data/` folder.

### Step 5 — Run the reconciliation engine from the command line
```bash
python3 reconciliation_engine.py
```
This prints the match rate and writes `matched.csv`,
`exceptions_bank.csv`, and `exceptions_invoices.csv` into `data/`.

### Step 6 — Score it honestly
```bash
python3 evaluate.py
```
This compares what the engine predicted against the secret ground truth
and prints precision, recall, and F1 — the numbers you put on your
submission and pitch slide.

### Step 7 — Launch the live demo dashboard
```bash
streamlit run app.py
```
This opens a browser window at `http://localhost:8501`. Use the sidebar to
adjust matching thresholds live and click **Run Reconciliation** — this is
what you show the judges instead of a static screenshot.

---

## 4. How the matching actually works (for your pitch / technical Q&A)

For every (bank transaction, invoice) pair, we compute three 0–1 scores:

| Signal | What it checks | Weight |
|---|---|---|
| `amount_score` | How close the amounts are, tolerant of small fee deductions/rounding | 50% |
| `desc_score` | Fuzzy text similarity between bank narration and invoice party name (handles typos, abbreviations, reference-number noise) via `rapidfuzz` | 35% |
| `date_score` | How close the bank transaction date is to the invoice date, allowing for settlement lag | 15% |

These combine into one `confidence` score. Pairs are sorted by confidence
and greedily assigned — highest-confidence pairs get matched first, and
once a bank transaction or invoice is claimed, it can't be reused. Anything
below `MIN_CONFIDENCE_TO_ACCEPT` (default 0.55) is left as an exception
rather than being force-matched. **This threshold is a deliberate,
visible design choice** — you can defend the precision/recall trade-off it
creates (raise it → fewer false positives but more manual review; lower it
→ higher automation but more risk of a wrong match).

### Why this counts as "AI" and not just a spreadsheet formula
Fuzzy string matching (`rapidfuzz`) and multi-signal confidence scoring are
exactly the kind of lightweight, explainable ML technique real fintech
reconciliation tools use — and "explainable" is explicitly part of what
judges are told to look for across every track. If you have time left
after the core build, the natural upgrade path (mention this in your
pitch as future work) is replacing the hand-tuned weights with a small
logistic regression trained on labelled matches.

---

## 5. Suggested 1-day build timeline

| Time | Task |
|---|---|
| Hour 0–1 | Read this README, run Steps 1–7 once so you have a working baseline |
| Hour 1–2 | Tweak `data_generator.py` if you want your own harder edge cases |
| Hour 2–4 | Polish `reconciliation_engine.py` — try adjusting thresholds, add a new signal if you have time (e.g. GSTIN/reference number exact match as a bonus signal) |
| Hour 4–5 | Polish the Streamlit UI — add your team branding, clean up labels |
| Hour 5–6 | Record your 5-minute pitch video (see Section 7) |
| Hour 6–7 | Write up Build Challenges & Technical Obstacles for the submission form (be honest — judges like real friction, not a fake-smooth story) |
| Hour 7–8 | Push to GitHub, fill out the submission form, buffer time for bugs |

---

## 6. Filling out the submission form

Based on the form fields:

- **Selected Track:** AI Finance Controller
- **Project Name/Title:** e.g. "LedgerLoop — AI Reconciliation Agent" (pick something memorable, not generic)
- **Project Objectives:** *"Automates matching bank settlements to invoices using multi-signal fuzzy confidence scoring, closes the finance-ops reconciliation loop, and reports measured match-rate accuracy plus an honest, categorized exception list — instead of the manual spreadsheet cross-referencing finance teams do today."*
- **GitHub Repository URL:** push this folder as a repo (see Section 8)
- **5-min Pitch Video Link:** see Section 7
- **Build Challenges & Technical Obstacles:** Be specific and honest. Good real examples to draw from: tuning the amount/date tolerance so it's strict enough to avoid false positives but loose enough to catch settlement-fee deductions; handling the ambiguous case where two invoices from the same party have identical amounts (resolved using date proximity as the tiebreaker — mention this shows up in your evaluate.py numbers).

---

## 7. Suggested 5-minute pitch video structure

1. **0:00–0:30 — The problem.** Finance teams manually cross-reference bank
   statements against invoices every day. It's slow and error-prone at scale.
2. **0:30–1:00 — What you built.** One sentence: an agent that reads both
   files and closes the loop automatically, with proof it works.
3. **1:00–3:00 — Live demo.** Open the Streamlit app, run it live, walk
   through: match rate, money reconciled, then click into the Exceptions
   tab and show a real exception with its reason.
4. **3:00–4:00 — The honesty part (this is what wins).** Show the
   `evaluate.py` precision/recall output. Say explicitly: *"We scored this
   against a held-out answer key our engine never saw — this isn't a
   cherry-picked match."*
5. **4:00–5:00 — What's next.** Mention the logistic-regression upgrade
   path, multi-currency support, or plugging into a real bank statement API.

---

## 8. Pushing to GitHub (if you haven't done this before)

```bash
cd reco-agent
git init
git add .
git commit -m "AI Finance Controller reconciliation agent"
git branch -M main
git remote add origin https://github.com/<your-username>/<repo-name>.git
git push -u origin main
```
If you don't have a GitHub repo yet, create one first at github.com/new
(don't initialize it with a README — you already have one).

**Add a `.gitignore`** so you don't commit your virtual environment:
```
venv/
__pycache__/
*.pyc
```

---

## 9. Judging-day checklist

- [ ] `python3 data_generator.py` runs clean on a fresh clone
- [ ] `python3 reconciliation_engine.py` runs clean and prints a match rate
- [ ] `python3 evaluate.py` prints precision/recall/F1
- [ ] `streamlit run app.py` opens and the "Run Reconciliation" button works
- [ ] README explains the approach without needing you to talk through code
- [ ] Pitch video is under 5 minutes and shows the live demo, not just slides
- [ ] You can answer: "What happens if two invoices could both match one payment?" (Section 4 above)
- [ ] You can answer: "How do you know your accuracy number isn't cherry-picked?" (Section 1/6 above — held-out ground truth)
