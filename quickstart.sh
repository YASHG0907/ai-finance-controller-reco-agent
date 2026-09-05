#!/bin/bash
# One-command setup + full pipeline run, for verifying everything works
# on a fresh machine before demo day.
set -e

echo "Installing dependencies..."
pip install -r requirements.txt --quiet

echo ""
echo "Generating synthetic data..."
python3 data_generator.py

echo ""
echo "Running reconciliation engine..."
python3 reconciliation_engine.py

echo ""
echo "Scoring against held-out ground truth..."
python3 evaluate.py

echo ""
echo "All checks passed. Launching dashboard..."
echo "(Press Ctrl+C to stop, then run 'streamlit run app.py' any time)"
streamlit run app.py
