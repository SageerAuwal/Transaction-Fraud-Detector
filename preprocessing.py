import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler, OneHotEncoder, FunctionTransformer
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
import category_encoders as ce
import joblib
import os


# ── Feature Engineering ───────────────────────────────────────────────────────
def create_features(X: pd.DataFrame) -> pd.DataFrame:
    """
    Engineering step applied inside the sklearn pipeline.
    Extracts temporal features from 'timestamp', drops ID columns.
    Velocity features (txn_count_1h, txn_count_24h, amt_sum_24h) are
    pre-computed in generate_data.py and passed through as-is.
    """
    X = X.copy()

    # Temporal
    if "timestamp" in X.columns:
        X["timestamp"]    = pd.to_datetime(X["timestamp"])
        X["hour"]         = X["timestamp"].dt.hour
        X["day_of_week"]  = X["timestamp"].dt.dayofweek
        X["is_late_night"]= ((X["hour"] >= 0) & (X["hour"] <= 4)).astype(int)
        X = X.drop(columns=["timestamp"])

    # Drop raw ID columns (user_id handled by target-encoding step)
    drop_cols = [c for c in ["transaction_id", "sender_nuban", "receiver_nuban"]
                 if c in X.columns]
    X = X.drop(columns=drop_cols)

    return X


def get_preprocessor(target_encoder_cols=None):
    """
    Returns a full sklearn Pipeline:

    Step 1 — feature_engineering  : datetime extraction, drop IDs
    Step 2 — target_encode_user   : TargetEncoder for user_id
    Step 3 — column_transformer   : StandardScaler (numeric) + OHE (categorical)

    Parameters
    ----------
    target_encoder_cols : list or None
        Passed at fit-time so TargetEncoder knows about training labels.
        At inference time the encoder is already fitted, so this is ignored.
    """

    numeric_features     = [
        "amount_ngn", "hour", "day_of_week", "is_late_night", "bvn_match",
        "txn_count_1h", "txn_count_24h", "amt_sum_24h"
    ]
    categorical_features = ["sender_bank", "receiver_bank", "channel"]

    numeric_transformer = Pipeline(steps=[
        ("scaler", StandardScaler())
    ])

    categorical_transformer = Pipeline(steps=[
        ("onehot", OneHotEncoder(handle_unknown="ignore", sparse_output=False))
    ])

    col_transformer = ColumnTransformer(
        transformers=[
            ("num", numeric_transformer, numeric_features),
            ("cat", categorical_transformer, categorical_features),
        ],
        remainder="drop"     # user_id already target-encoded and renamed
    )

    # Target-encoder wraps user_id into a numeric column before col_transformer
    target_encoder = ce.TargetEncoder(cols=["user_id"], smoothing=10)

    pipeline = Pipeline(steps=[
        ("feature_engineering", FunctionTransformer(create_features, validate=False)),
        ("target_encoder",      target_encoder),
        ("preprocessor",        col_transformer),
    ])

    return pipeline


if __name__ == "__main__":
    # Sanity check
    df = pd.DataFrame({
        "transaction_id": ["TXN00000001"],
        "user_id":        ["U00001"],
        "amount_ngn":     [25000.0],
        "sender_bank":    ["GTBank"],
        "receiver_bank":  ["Opay"],
        "channel":        ["NIP"],
        "sender_nuban":   ["1234567890"],
        "receiver_nuban": ["0987654321"],
        "bvn_match":      [1],
        "timestamp":      ["2023-06-15 02:30:00"],
        "txn_count_1h":   [3],
        "txn_count_24h":  [8],
        "amt_sum_24h":    [75000.0],
    })
    y = pd.Series([0])

    pipeline = get_preprocessor()
    out = pipeline.fit_transform(df, y)
    print("Output shape:", out.shape)
    print("Pipeline OK")
