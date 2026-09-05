"""
data_generator.py
------------------
Generates SYNTHETIC bank statement + invoice ledger data for the
AI Finance Controller reconciliation project.

Why synthetic ground truth matters:
The hackathon brief says "THE BAR: Throughput plus measured accuracy
plus an honest exception list. One cherry-picked match proves nothing."

To prove our accuracy honestly (not cherry-picked), we secretly know
which bank transaction SHOULD match which invoice (ground_truth.csv).
We never show this file to the matching engine -- we only use it
afterwards, in evaluate.py, to grade ourselves the way a judge would.

Run:
    python data_generator.py
Outputs (in ./data/):
    bank_statement.csv   -> what the matching engine sees
    invoices.csv          -> what the matching engine sees
    ground_truth.csv       -> secret answer key (used only by evaluate.py)
"""

import pandas as pd
import numpy as np
import random
from datetime import datetime, timedelta
import os

random.seed(42)
np.random.seed(42)

OUT_DIR = os.path.join(os.path.dirname(__file__), "data")
os.makedirs(OUT_DIR, exist_ok=True)

PARTIES = [
    "Sharma Textiles", "Verma Electronics", "Kolhapur Traders",
    "Om Sai Enterprises", "Patil Logistics", "Deshmukh & Co",
    "Nakoda Fabrics", "Global Spares Ltd", "Konkan Foods",
    "Raj Hardware", "Blue Star Distributors", "Anand Motors",
]

BASE_DATE = datetime(2026, 8, 1)
N_TRUE_TRANSACTIONS = 60  # real underlying business transactions


def jitter_amount(amount, kind):
    """Simulate the kinds of small differences real bank vs invoice
    amounts have (bank fees, rounding, partial settlement)."""
    if kind == "exact":
        return round(amount, 2)
    if kind == "rounding":
        return round(amount + random.choice([-2, -1, -0.5, 0.5, 1, 2]), 2)
    if kind == "fee_deducted":
        return round(amount - random.uniform(5, 25), 2)  # payment gateway fee
    return round(amount, 2)


def jitter_date(date, kind):
    if kind == "same_day":
        return date
    if kind == "delayed":
        return date + timedelta(days=random.choice([1, 2, 3]))
    return date


def jitter_description(name, kind):
    if kind == "clean":
        return name
    if kind == "abbreviated":
        return "".join([w[:4].upper() for w in name.split()])
    if kind == "with_ref_noise":
        return f"{name} NEFT/{random.randint(100000,999999)}/TXN"
    if kind == "typo":
        chars = list(name)
        if len(chars) > 4:
            i = random.randint(1, len(chars) - 2)
            chars[i], chars[i + 1] = chars[i + 1], chars[i]
        return "".join(chars)
    return name


def generate():
    true_txns = []
    for i in range(N_TRUE_TRANSACTIONS):
        true_txns.append({
            "true_id": f"T{i+1:04d}",
            "party": random.choice(PARTIES),
            "amount": round(random.uniform(1500, 95000), 2),
            "invoice_date": BASE_DATE + timedelta(days=random.randint(0, 30)),
        })

    bank_rows = []
    invoice_rows = []
    ground_truth = []  # (bank_id, invoice_id) or (bank_id, None) / (None, invoice_id)

    bank_counter, invoice_counter = 1, 1

    for txn in true_txns:
        roll = random.random()

        # invoice_id always exists (every real transaction has an invoice)
        inv_id = f"INV{invoice_counter:04d}"
        invoice_counter += 1
        inv_desc_kind = random.choice(["clean", "clean", "abbreviated"])
        invoice_rows.append({
            "invoice_id": inv_id,
            "invoice_date": txn["invoice_date"].strftime("%Y-%m-%d"),
            "party_name": jitter_description(txn["party"], inv_desc_kind),
            "invoice_amount": txn["amount"],
        })

        if roll < 0.72:
            # CASE A: clean, easy match (bank txn exists, close to invoice)
            bank_id = f"BNK{bank_counter:04d}"
            bank_counter += 1
            amt_kind = random.choice(["exact", "exact", "rounding"])
            date_kind = random.choice(["same_day", "delayed"])
            desc_kind = random.choice(["clean", "with_ref_noise", "typo"])
            bank_rows.append({
                "bank_txn_id": bank_id,
                "txn_date": jitter_date(txn["invoice_date"], date_kind).strftime("%Y-%m-%d"),
                "narration": jitter_description(txn["party"], desc_kind),
                "credit_amount": jitter_amount(txn["amount"], amt_kind),
            })
            ground_truth.append({"bank_txn_id": bank_id, "invoice_id": inv_id})

        elif roll < 0.85:
            # CASE B: fee-deducted settlement -> harder amount match
            bank_id = f"BNK{bank_counter:04d}"
            bank_counter += 1
            bank_rows.append({
                "bank_txn_id": bank_id,
                "txn_date": jitter_date(txn["invoice_date"], "delayed").strftime("%Y-%m-%d"),
                "narration": jitter_description(txn["party"], "with_ref_noise"),
                "credit_amount": jitter_amount(txn["amount"], "fee_deducted"),
            })
            ground_truth.append({"bank_txn_id": bank_id, "invoice_id": inv_id})

        else:
            # CASE C: invoice NOT yet paid -> genuine exception, no bank txn
            ground_truth.append({"bank_txn_id": None, "invoice_id": inv_id})

    # CASE E: AMBIGUOUS duplicates -- two invoices, same party, same
    # amount, close dates. A real bank txn can only pay one of them,
    # but both look equally valid to a naive matcher. This is the
    # hardest, most realistic case and it's OK if the engine gets
    # some of these wrong -- that's what "honest accuracy" means.
    for _ in range(4):
        party = random.choice(PARTIES)
        amount = round(random.uniform(2000, 20000), 2)
        base_date = BASE_DATE + timedelta(days=random.randint(5, 25))

        inv_id_1 = f"INV{invoice_counter:04d}"; invoice_counter += 1
        inv_id_2 = f"INV{invoice_counter:04d}"; invoice_counter += 1
        invoice_rows.append({"invoice_id": inv_id_1, "invoice_date": base_date.strftime("%Y-%m-%d"),
                              "party_name": party, "invoice_amount": amount})
        invoice_rows.append({"invoice_id": inv_id_2,
                              "invoice_date": (base_date + timedelta(days=1)).strftime("%Y-%m-%d"),
                              "party_name": party, "invoice_amount": amount})

        # only ONE of the two duplicate invoices actually gets paid
        bank_id = f"BNK{bank_counter:04d}"; bank_counter += 1
        paid_invoice = random.choice([inv_id_1, inv_id_2])
        paid_date = base_date if paid_invoice == inv_id_1 else base_date + timedelta(days=1)
        bank_rows.append({
            "bank_txn_id": bank_id,
            "txn_date": paid_date.strftime("%Y-%m-%d"),
            "narration": party,
            "credit_amount": amount,
        })
        ground_truth.append({"bank_txn_id": bank_id, "invoice_id": paid_invoice})
        unpaid_invoice = inv_id_2 if paid_invoice == inv_id_1 else inv_id_1
        ground_truth.append({"bank_txn_id": None, "invoice_id": unpaid_invoice})

    # CASE D: bank-only noise -- transactions with no invoice at all
    # (bank fees, refunds, unrelated transfers). These MUST end up as
    # exceptions. A system that force-matches these is dishonest.
    for _ in range(8):
        bank_id = f"BNK{bank_counter:04d}"
        bank_counter += 1
        bank_rows.append({
            "bank_txn_id": bank_id,
            "txn_date": (BASE_DATE + timedelta(days=random.randint(0, 33))).strftime("%Y-%m-%d"),
            "narration": random.choice([
                "BANK CHARGES-GST", "NEFT REFUND-UNAPPLIED", "INTEREST CREDIT",
                "RTGS-UNKNOWN PARTY", "POS SETTLEMENT-MISC"
            ]),
            "credit_amount": round(random.uniform(50, 3000), 2),
        })
        ground_truth.append({"bank_txn_id": bank_id, "invoice_id": None})

    bank_df = pd.DataFrame(bank_rows).sample(frac=1, random_state=1).reset_index(drop=True)
    invoice_df = pd.DataFrame(invoice_rows).sample(frac=1, random_state=2).reset_index(drop=True)
    truth_df = pd.DataFrame(ground_truth)

    bank_df.to_csv(os.path.join(OUT_DIR, "bank_statement.csv"), index=False)
    invoice_df.to_csv(os.path.join(OUT_DIR, "invoices.csv"), index=False)
    truth_df.to_csv(os.path.join(OUT_DIR, "ground_truth.csv"), index=False)

    print(f"Generated {len(bank_df)} bank transactions -> data/bank_statement.csv")
    print(f"Generated {len(invoice_df)} invoices -> data/invoices.csv")
    print(f"Ground truth (secret answer key) -> data/ground_truth.csv")
    print("\nDo NOT show ground_truth.csv to the matching engine.")
    print("It exists only so evaluate.py can honestly grade the engine afterwards.")


if __name__ == "__main__":
    generate()
