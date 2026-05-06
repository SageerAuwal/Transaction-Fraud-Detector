import pandas as pd
import numpy as np
import random
from datetime import datetime, timedelta
import os


def generate_synthetic_data(num_records=50000, fraud_ratio=0.05):
    print(f"Generating {num_records} synthetic transactions for Nigerian context...")
    np.random.seed(42)
    random.seed(42)

    # ── Nigerian Banking Specifics ────────────────────────────────────────────
    banks    = ["GTBank", "Zenith Bank", "Access Bank", "UBA", "First Bank",
                "Opay", "Moniepoint", "Kuda", "Fidelity Bank", "Sterling Bank"]
    channels = ["NIP", "POS", "USSD", "Web"]
    fintechs = ["Opay", "Moniepoint", "Kuda"]

    def generate_nuban():
        return f"{random.randint(1000000000, 9999999999)}"

    user_ids = [f"U{str(i).zfill(5)}" for i in range(1, 1001)]

    # ── Build raw event list (with timestamps) ────────────────────────────────
    raw = []
    start_date = datetime(2023, 1, 1)
    num_frauds = int(num_records * fraud_ratio)
    num_legit  = num_records - num_frauds

    # Legitimate transactions
    for _ in range(num_legit):
        user          = random.choice(user_ids)
        amount        = round(np.random.lognormal(mean=8, sigma=1.5), 2)
        if amount < 100:
            amount = 100.0
        sender_bank   = random.choice(banks)
        receiver_bank = random.choice(banks)
        channel       = random.choice(channels)
        sender_nuban  = generate_nuban()
        recv_nuban    = generate_nuban()
        bvn_match     = 1 if random.random() > 0.05 else 0
        time_offset   = timedelta(minutes=random.randint(0, 365 * 24 * 60))
        txn_time      = start_date + time_offset
        raw.append([user, amount, sender_bank, receiver_bank, channel,
                    sender_nuban, recv_nuban, bvn_match, txn_time, 0])

    # Fraudulent transactions
    for _ in range(num_frauds):
        user          = random.choice(user_ids)
        amount        = round(np.random.uniform(500000, 5000000), 2)
        sender_bank   = random.choice(banks)
        receiver_bank = random.choices(fintechs, weights=[0.4, 0.4, 0.2])[0]
        channel       = random.choices(["USSD", "Web", "NIP"], weights=[0.4, 0.4, 0.2])[0]
        sender_nuban  = generate_nuban()
        recv_nuban    = generate_nuban()
        bvn_match     = 0 if random.random() > 0.1 else 1
        time_offset   = timedelta(minutes=random.randint(0, 365 * 24 * 60))
        txn_time      = start_date + time_offset
        if random.random() > 0.5:
            txn_time  = txn_time.replace(hour=random.randint(0, 4))
        raw.append([user, amount, sender_bank, receiver_bank, channel,
                    sender_nuban, recv_nuban, bvn_match, txn_time, 1])

    # ── Assemble DataFrame ────────────────────────────────────────────────────
    df = pd.DataFrame(raw, columns=[
        "user_id", "amount_ngn", "sender_bank", "receiver_bank", "channel",
        "sender_nuban", "receiver_nuban", "bvn_match", "timestamp", "is_fraud"
    ])

    # Sort chronologically (important for velocity features & chrono split)
    df = df.sort_values("timestamp").reset_index(drop=True)
    df.insert(0, "transaction_id",
              [f"TXN{str(i).zfill(8)}" for i in range(1, num_records + 1)])

    # ── Velocity Features ─────────────────────────────────────────────────────
    # Computed per-user, looking back in time from each transaction.
    # We iterate chronologically — O(n) via a user-keyed deque approach.
    print("Computing velocity features...")

    from collections import deque

    txn_count_1h   = np.zeros(len(df), dtype=np.int32)
    txn_count_24h  = np.zeros(len(df), dtype=np.int32)
    amt_sum_24h    = np.zeros(len(df), dtype=np.float64)

    # Per-user sliding windows: deque of (timestamp, amount)
    user_windows: dict[str, deque] = {}

    for idx, row in df.iterrows():
        uid = row["user_id"]
        ts  = row["timestamp"]
        amt = row["amount_ngn"]

        if uid not in user_windows:
            user_windows[uid] = deque()

        win = user_windows[uid]

        # Expire entries older than 24 h
        cutoff_24h = ts - timedelta(hours=24)
        cutoff_1h  = ts - timedelta(hours=1)
        while win and win[0][0] < cutoff_24h:
            win.popleft()

        # Count / sum over active window
        c1h  = sum(1   for t, _ in win if t >= cutoff_1h)
        c24h = len(win)
        s24h = sum(a   for _, a in win)

        txn_count_1h[idx]  = c1h
        txn_count_24h[idx] = c24h
        amt_sum_24h[idx]   = s24h

        # Add current transaction to window
        win.append((ts, amt))

    df["txn_count_1h"]  = txn_count_1h
    df["txn_count_24h"] = txn_count_24h
    df["amt_sum_24h"]   = amt_sum_24h

    # ── Save ──────────────────────────────────────────────────────────────────
    os.makedirs("data", exist_ok=True)
    file_path = os.path.join("data", "synthetic_transactions_ng.csv")
    df.to_csv(file_path, index=False)

    print(f"Data generation complete. Saved to {file_path}")
    print(f"Shape: {df.shape}")
    print(df["is_fraud"].value_counts(normalize=True))
    print("\nVelocity feature sample (fraud):")
    print(df[df["is_fraud"] == 1][["txn_count_1h", "txn_count_24h", "amt_sum_24h"]].describe())


if __name__ == "__main__":
    generate_synthetic_data()
