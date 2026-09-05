"""
app.py
------
Streamlit dashboard for the AI Finance Controller reconciliation agent.

Run:
    streamlit run app.py

This is what you show judges live: upload data (or use the bundled
sample), click "Run Reconciliation", see the match rate, money
reconciled, and -- critically -- the honest exception list with
reasons. If ground_truth.csv is present (demo mode), it also shows
the measured precision/recall so judges see real numbers, not vibes.
"""

import streamlit as st
import pandas as pd
import os
import sys

sys.path.append(os.path.dirname(__file__))
from reconciliation_engine import reconcile, load_data
import evaluate as eval_module

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")

st.set_page_config(page_title="AI Finance Controller", page_icon="\U0001F4B0", layout="wide")

st.title("\U0001F4B0 AI Finance Controller — Reconciliation Agent")
st.caption(
    "Track 04 · Closes the bank-statement ↔ invoice reconciliation loop, "
    "reports match rate and an honest exception list."
)

with st.sidebar:
    st.header("Data source")
    use_sample = st.toggle("Use bundled sample data", value=True)

    if not use_sample:
        bank_file = st.file_uploader("Bank statement CSV", type="csv")
        invoice_file = st.file_uploader("Invoices CSV", type="csv")
    else:
        bank_file, invoice_file = None, None
        st.info("Using data/bank_statement.csv and data/invoices.csv")

    st.divider()
    st.header("Matching thresholds")
    st.caption("These control how strict the agent is. Shown for transparency, not hidden.")
    import reconciliation_engine as engine
    engine.AMOUNT_TOLERANCE_PCT = st.slider("Amount tolerance (%)", 0.0, 10.0, 3.0) / 100
    engine.DATE_WINDOW_DAYS = st.slider("Settlement window (days)", 0, 10, 5)
    engine.MIN_CONFIDENCE_TO_ACCEPT = st.slider("Minimum confidence to auto-match", 0.0, 1.0, 0.55)

    run_btn = st.button("\u25B6 Run Reconciliation", type="primary", use_container_width=True)

if run_btn:
    if use_sample:
        bank_df, invoice_df = load_data()
    else:
        if bank_file is None or invoice_file is None:
            st.error("Please upload both files, or switch on 'Use bundled sample data'.")
            st.stop()
        bank_df = pd.read_csv(bank_file)
        invoice_df = pd.read_csv(invoice_file)
        bank_df["txn_date"] = pd.to_datetime(bank_df["txn_date"])
        invoice_df["invoice_date"] = pd.to_datetime(invoice_df["invoice_date"])

    with st.spinner("Matching bank transactions to invoices..."):
        matched_df, unmatched_bank, unmatched_invoices = reconcile(bank_df, invoice_df)

    total_bank = len(bank_df)
    matched_count = len(matched_df)
    match_rate = (matched_count / total_bank * 100) if total_bank else 0
    money_matched = matched_df["bank_amount"].sum() if not matched_df.empty else 0
    money_total = bank_df["credit_amount"].sum()

    st.subheader("Results")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Match rate", f"{match_rate:.1f}%", f"{matched_count}/{total_bank} txns")
    c2.metric("Money reconciled", f"Rs. {money_matched:,.0f}", f"of Rs. {money_total:,.0f}")
    c3.metric("Bank exceptions", len(unmatched_bank))
    c4.metric("Unpaid invoices", len(unmatched_invoices))

    # If secret ground truth exists (demo/judging mode), show honest accuracy too
    truth_path = os.path.join(DATA_DIR, "ground_truth.csv")
    if use_sample and os.path.exists(truth_path):
        matched_df.to_csv(os.path.join(DATA_DIR, "matched.csv"), index=False)
        metrics = eval_module.evaluate()
        st.subheader("Measured accuracy (scored against held-out ground truth)")
        m1, m2, m3 = st.columns(3)
        m1.metric("Precision", f"{metrics['precision']:.3f}")
        m2.metric("Recall", f"{metrics['recall']:.3f}")
        m3.metric("F1 score", f"{metrics['f1']:.3f}")
        st.caption(
            f"True positives: {metrics['true_positives']} · "
            f"False positives: {metrics['false_positives']} · "
            f"False negatives: {metrics['false_negatives']}"
        )

    tab1, tab2, tab3 = st.tabs(["\u2705 Matched", "\u26A0\uFE0F Bank Exceptions", "\U0001F4C4 Unpaid Invoices"])

    with tab1:
        st.caption("Every match includes a confidence score and the three signals behind it (audit trail).")
        st.dataframe(matched_df.sort_values("confidence"), use_container_width=True)
        st.download_button("Download matched.csv", matched_df.to_csv(index=False), "matched.csv")

    with tab2:
        st.caption("Bank transactions the agent could NOT confidently match. Nothing is silently dropped.")
        st.dataframe(unmatched_bank, use_container_width=True)
        st.download_button("Download exceptions_bank.csv", unmatched_bank.to_csv(index=False), "exceptions_bank.csv")

    with tab3:
        st.caption("Invoices with no matching payment found -- likely pending or overdue.")
        st.dataframe(unmatched_invoices, use_container_width=True)
        st.download_button("Download exceptions_invoices.csv", unmatched_invoices.to_csv(index=False), "exceptions_invoices.csv")

else:
    st.info("Set your options in the sidebar, then click **Run Reconciliation**.")
    st.markdown("""
    ### How this works
    1. **Exact + fuzzy matching** on amount, date, and description — not a black box.
    2. Every match gets a **confidence score** built from three visible signals.
    3. Anything below the confidence bar becomes an **exception with a stated reason**.
    4. Accuracy is **measured against held-out ground truth**, not cherry-picked.
    """)
