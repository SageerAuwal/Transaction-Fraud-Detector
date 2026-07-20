# Gojo Sentinel — Production Implementation Plan (Real Transaction Dataset Integration)

## 📌 Executive Summary
This document provides the full technical roadmap for transitioning **Gojo Sentinel** from its initial synthetic demonstration phase to a production-ready AI fraud detection engine trained on real transaction data. 

The goal is to replace synthetic training pipelines, engineer domain-specific financial features, calibrate detection thresholds to minimize false positives, and update both the cloud API (Hugging Face) and mobile applications (Android APK).

---

## 🚀 Phase 1: Data Audit & Schema Mapping

### 1.1 Dataset Inspection & Quality Check
- **Data Format**: Ingest dataset format (`.csv`, `.parquet`, or SQL database export).
- **Class Ratio Analysis**: Measure the exact proportion of fraudulent vs. legitimate transactions (e.g., $0.1\% - 1.5\%$ fraud rate).
- **Missing Value & Outlier Check**: Audit missing data across sensitive columns (bank names, payment channels, device IDs).

### 1.2 Column Mapping Matrix
Map raw dataset fields to Gojo Sentinel's internal feature contract:

| Raw Data Field | Standardized Feature | Description |
| :--- | :--- | :--- |
| `Timestamp` / `TxnDate` | `txn_datetime` | Date & time used for velocity aggregation |
| `Amount` / `Val` | `amount_ngn` | Transaction value in NGN |
| `SenderBank` / `OriginBank` | `sender_bank` | Originating bank entity |
| `ReceiverBank` / `DestBank` | `receiver_bank` | Destination bank entity |
| `Channel` / `TxnType` | `channel` | Payment channel (`NIP`, `POS`, `USSD`, `Web`) |
| `UserId` / `AccNum` | `user_id` | Unique account or customer identifier |
| `FraudFlag` / `Label` | `is_fraud` | Binary target (`0` = Normal, `1` = Fraud) |

---

## ⚙️ Phase 2: Preprocessing & Feature Engineering Pipeline

### 2.1 Velocity & Behavioral Feature Calculation
Extract aggregate time-window signals essential for catching financial fraud:
- **`txn_count_1h` & `txn_count_24h`**: Number of transactions initiated by the account within 1-hour and 24-hour windows.
- **`amt_sum_24h` & `amt_avg_24h`**: Total and mean transaction value spent over the last 24 hours.
- **`amt_ratio_vs_avg`**: Ratio of current transaction amount vs. customer's historical 30-day average.
- **`time_since_last_txn`**: Time delta (in seconds) since previous transaction to flag rapid burst velocity attacks.
- **`cyclical_time`**: Sine/Cosine transforms for hour-of-day and day-of-week patterns.

### 2.2 Feature Preprocessing (`preprocessing.py`)
- **Categorical Encoding**: Utilize `category-encoders` (Target Encoding or Frequency Encoding) to convert high-cardinality bank names and channels into numerical representations.
- **Scaling**: Apply `RobustScaler` or log-transforms to transaction amounts to prevent extreme high-value transactions from distorting model gradients.
- **Class Imbalance Management**: Apply SMOTE/ADASYN during training or adjust XGBoost's `scale_pos_weight = N_legitimate / N_fraud`.

---

## 📊 Phase 3: Model Retraining, Evaluation & Threshold Calibration

### 3.1 Time-Series Validation Strategy
- **Chronological Split**: Split dataset by time (e.g., train on first 80% of historical months, validate on remaining 20%) to prevent data leakage and simulate live inference accurately.

### 3.2 Evaluation Metrics
Focus on precision and recall rather than overall accuracy:
1. **PR-AUC (Precision-Recall Area Under Curve)**: Primary optimization metric.
2. **Recall at Fixed False Positive Rate (FPR)**: Target $\ge 90\%$ fraud detection rate at $\le 1\%$ false positive rate.
3. **Financial Loss vs. Friction Matrix**: Calculate cost of missed fraud (chargebacks/losses) vs. blocked legitimate users (customer friction).

### 3.3 Decision Boundary Calibration
- Determine the optimal risk threshold (e.g., `0.32` instead of default `0.50`).
- Export decision boundaries and rule overrides to `models/threshold.json`.

---

## 📦 Phase 4: Model Export & API/Database Update

### 4.1 Production Model Artifacts
Generate and save new model binaries to the `models/` directory:
- `xgb_model.json` — Retrained XGBoost classifier model binary.
- `preprocessor.pkl` — Scikit-learn / Category Encoder pipeline artifact.
- `threshold.json` — Calibrated risk thresholds.
- `model_version.json` — Model metadata, metrics, and training timestamp.

### 4.2 Backend & DB Alignment (`app.py`)
- Update Pydantic request models if new input parameters are added.
- Update prediction logging database schema (SQLite/PostgreSQL) to record new feature metrics.

---

## 🌐 Phase 5: Verification & Production Deployment

### 5.1 Local & Offline Verification
- Execute offline evaluation tests via `run_offline.bat` (Windows) or `run_linux.sh` (Linux).
- Validate API response times ($\le 50\text{ms}$ per prediction request).

### 5.2 Cloud Deployment & Mobile APK Build
- **GitHub**: Commit updated model artifacts and code to `main` branch.
- **Hugging Face Space**: Automatic rebuild & deployment of the live API & web dashboard.
- **GitHub Actions**: Automated CI/CD workflow compiles the updated Android APK pointing to the production cloud endpoint.

---

## 📋 Checklist for Team Execution

- [ ] Obtain & upload real dataset (`.csv` / `.parquet`).
- [ ] Map dataset columns to standardized schema.
- [ ] Run preprocessing & feature extraction pipeline.
- [ ] Train XGBoost model & evaluate PR-AUC curves.
- [ ] Calibrate decision threshold to minimize false positives.
- [ ] Save updated artifacts to `models/` folder.
- [ ] Push updates to GitHub (`git push origin main`).
- [ ] Download updated Android APK from GitHub Actions artifact release.

---
*Gojo Sentinel — AI-Powered Nigerian Fintech Security System*
