"""
retrain.py — NaijaGuard Scheduled Retraining Script
─────────────────────────────────────────────────────
Reads confirmed fraud feedback from the predictions SQLite DB,
merges with the base training data, and retrains the model.

Usage:
    python retrain.py                  # run once
    python retrain.py --min-feedback 50  # only retrain if >= 50 feedback records exist

Schedule (Windows Task Scheduler):
    Action: python C:\\path\\to\\retrain.py
    Trigger: Weekly, Sunday 02:00 AM
"""

import sqlite3
import pandas as pd
import json
import argparse
import os
import sys
from datetime import datetime


def load_feedback(db_path: str) -> pd.DataFrame:
    """Load confirmed fraud/legit feedback from predictions DB."""
    if not os.path.exists(db_path):
        return pd.DataFrame()

    conn = sqlite3.connect(db_path)
    try:
        df = pd.read_sql_query(
            "SELECT * FROM predictions WHERE confirmed_fraud IS NOT NULL",
            conn
        )
    except Exception:
        df = pd.DataFrame()
    finally:
        conn.close()
    return df


def main():
    parser = argparse.ArgumentParser(description="NaijaGuard Retraining Script")
    parser.add_argument("--min-feedback", type=int, default=10,
                        help="Minimum new feedback records required to retrain")
    parser.add_argument("--db-path", default="data/predictions.db")
    args = parser.parse_args()

    print("=" * 60)
    print("  NaijaGuard — Retraining Pipeline")
    print(f"  {datetime.now().isoformat()}")
    print("=" * 60)

    # Load feedback
    feedback_df = load_feedback(args.db_path)
    n_feedback  = len(feedback_df)
    print(f"\nFeedback records with confirmed labels: {n_feedback}")

    if n_feedback < args.min_feedback:
        print(f"[SKIP] Need at least {args.min_feedback} feedback records. "
              f"Only {n_feedback} available. Exiting.")
        sys.exit(0)

    print(f"[OK] Sufficient feedback. Merging with base training data...")

    # Load base training data
    base_df = pd.read_csv("data/synthetic_transactions_ng.csv")

    if not feedback_df.empty:
        # Map feedback columns to training schema
        feedback_mapped = pd.DataFrame({
            "transaction_id": feedback_df["transaction_id"],
            "user_id":        feedback_df.get("user_id",        "UNKNOWN"),
            "amount_ngn":     pd.to_numeric(feedback_df.get("amount_ngn", 0), errors="coerce").fillna(0),
            "sender_bank":    feedback_df.get("sender_bank",    "GTBank"),
            "receiver_bank":  feedback_df.get("receiver_bank",  "GTBank"),
            "channel":        feedback_df.get("channel",        "NIP"),
            "sender_nuban":   feedback_df.get("sender_nuban",   "0000000000"),
            "receiver_nuban": feedback_df.get("receiver_nuban", "0000000000"),
            "bvn_match":      pd.to_numeric(feedback_df.get("bvn_match", 1), errors="coerce").fillna(1).astype(int),
            "timestamp":      feedback_df.get("scored_at",      datetime.now().isoformat()),
            "txn_count_1h":   pd.to_numeric(feedback_df.get("txn_count_1h",  0), errors="coerce").fillna(0).astype(int),
            "txn_count_24h":  pd.to_numeric(feedback_df.get("txn_count_24h", 0), errors="coerce").fillna(0).astype(int),
            "amt_sum_24h":    pd.to_numeric(feedback_df.get("amt_sum_24h",   0), errors="coerce").fillna(0),
            "is_fraud":       feedback_df["confirmed_fraud"].astype(int),
        })
        combined_df = pd.concat([base_df, feedback_mapped], ignore_index=True)
        combined_df.to_csv("data/synthetic_transactions_ng.csv", index=False)
        print(f"[OK] Combined dataset: {len(combined_df)} rows "
              f"(+{n_feedback} feedback rows)")
    else:
        print("[INFO] No new feedback to merge.")

    # Retrain
    print("\n[OK] Starting model training...")
    from train import train_model
    train_model()

    print("\n[DONE] Retraining complete.")


if __name__ == "__main__":
    main()
