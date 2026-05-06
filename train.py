import pandas as pd
import numpy as np
import xgboost as xgb
import json
import os
import joblib
from datetime import datetime

from sklearn.metrics import (
    classification_report, average_precision_score,
    confusion_matrix, precision_recall_curve
)
from imblearn.over_sampling import SMOTE
from preprocessing import get_preprocessor


# ── Helpers ───────────────────────────────────────────────────────────────────
def find_optimal_threshold(y_true, y_proba, beta=1.0):
    """
    Find threshold that maximises F-beta score on PR curve.
    beta=1 -> F1. beta=0.5 -> precision-weighted (fewer false alarms).
    beta=2 -> recall-weighted (miss fewer frauds).
    For fraud, beta=2 is typical.
    """
    precision, recall, thresholds = precision_recall_curve(y_true, y_proba)
    beta2 = beta ** 2
    # Avoid divide-by-zero
    f_scores = np.where(
        (beta2 * precision + recall) > 0,
        (1 + beta2) * precision * recall / (beta2 * precision + recall),
        0.0
    )
    best_idx = np.argmax(f_scores[:-1])   # thresholds is 1 shorter than p/r
    return float(thresholds[best_idx]), float(f_scores[best_idx])


# ── Main Training Function ────────────────────────────────────────────────────
def train_model():
    print("=" * 60)
    print("  NaijaGuard — Model Training Pipeline")
    print("=" * 60)

    # 1. Load data
    print("\n[1/7] Loading Nigerian transaction data...")
    df = pd.read_csv("data/synthetic_transactions_ng.csv")
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    print(f"      Shape: {df.shape}")
    print(f"      Fraud ratio: {df['is_fraud'].mean():.4f}")

    # 2. Chronological split (no data leakage)
    print("\n[2/7] Chronological train/test split (80/20)...")
    df = df.sort_values("timestamp").reset_index(drop=True)
    split_idx  = int(len(df) * 0.80)
    train_df   = df.iloc[:split_idx]
    test_df    = df.iloc[split_idx:]

    y_train = train_df["is_fraud"]
    X_train = train_df.drop(columns=["is_fraud"])
    y_test  = test_df["is_fraud"]
    X_test  = test_df.drop(columns=["is_fraud"])

    print(f"      Train: {X_train.shape}, fraud={y_train.mean():.4f}")
    print(f"      Test : {X_test.shape},  fraud={y_test.mean():.4f}")

    # 3. Preprocess
    print("\n[3/7] Fitting preprocessor...")
    pipeline = get_preprocessor()
    # TargetEncoder needs y at fit time
    X_train_proc = pipeline.fit_transform(X_train, y_train)
    X_test_proc  = pipeline.transform(X_test)

    # 4. SMOTE on training set
    print("\n[4/7] Applying SMOTE to balance training set...")
    neg = int((y_train == 0).sum())
    pos = int((y_train == 1).sum())
    print(f"      Before SMOTE — legit: {neg}, fraud: {pos}")

    smote = SMOTE(random_state=42, k_neighbors=5)
    X_train_res, y_train_res = smote.fit_resample(X_train_proc, y_train)
    print(f"      After  SMOTE — legit: {int((y_train_res==0).sum())}, "
          f"fraud: {int((y_train_res==1).sum())}")

    # 5. Train XGBoost
    print("\n[5/7] Training XGBoost model...")
    model = xgb.XGBClassifier(
        n_estimators=200,
        max_depth=6,
        learning_rate=0.07,
        subsample=0.8,
        colsample_bytree=0.8,
        min_child_weight=3,
        gamma=0.1,
        random_state=42,
        eval_metric="aucpr",
        verbosity=0,
        # No scale_pos_weight needed — SMOTE already balanced
    )
    model.fit(X_train_res, y_train_res)

    # 6. Evaluate + find optimal threshold
    print("\n[6/7] Evaluating on held-out test set...")
    y_proba = model.predict_proba(X_test_proc)[:, 1]

    opt_threshold, opt_f2 = find_optimal_threshold(y_test, y_proba, beta=2.0)
    print(f"      Optimal threshold (F2): {opt_threshold:.4f}  (F2={opt_f2:.4f})")

    y_pred_opt = (y_proba >= opt_threshold).astype(int)

    print("\n--- Classification Report (optimal threshold) ---")
    print(classification_report(y_test, y_pred_opt,
                                target_names=["Legitimate", "Fraud"]))

    pr_auc = average_precision_score(y_test, y_proba)
    print(f"PR-AUC Score: {pr_auc:.4f}")

    print("\n--- Confusion Matrix ---")
    print(confusion_matrix(y_test, y_pred_opt))

    # 7. Save artefacts
    print("\n[7/7] Saving model artefacts...")
    os.makedirs("models", exist_ok=True)

    joblib.dump(pipeline, "models/preprocessor.pkl")
    model.save_model("models/xgb_model.json")

    # Threshold file
    threshold_data = {"threshold": opt_threshold, "f2_score": opt_f2}
    with open("models/threshold.json", "w") as f:
        json.dump(threshold_data, f, indent=2)

    # Version file
    version_data = {
        "version": datetime.now().strftime("%Y%m%d_%H%M%S"),
        "trained_at": datetime.now().isoformat(),
        "train_rows": int(X_train.shape[0]),
        "test_rows": int(X_test.shape[0]),
        "pr_auc": round(float(pr_auc), 4),
        "optimal_threshold": round(opt_threshold, 4),
        "f2_score": round(float(opt_f2), 4),
        "features": [
            "amount_ngn", "hour", "day_of_week", "is_late_night", "bvn_match",
            "txn_count_1h", "txn_count_24h", "amt_sum_24h",
            "user_id (target-encoded)",
            "sender_bank (OHE)", "receiver_bank (OHE)", "channel (OHE)"
        ]
    }
    with open("models/model_version.json", "w") as f:
        json.dump(version_data, f, indent=2)

    print("      [OK] models/preprocessor.pkl")
    print("      [OK] models/xgb_model.json")
    print("      [OK] models/threshold.json")
    print("      [OK] models/model_version.json")
    print(f"\n[DONE] Model v{version_data['version']} saved. PR-AUC={pr_auc:.4f}")


if __name__ == "__main__":
    train_model()
