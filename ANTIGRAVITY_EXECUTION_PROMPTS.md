# Antigravity AI Execution Prompts for Real Data Integration

This document contains copy-pasteable prompts for your colleague to give to **Antigravity AI** to complete the real dataset integration step-by-step.

---

## 📌 How to Use
1. Copy each prompt in order (Step 1 to Step 5).
2. Paste the prompt into Antigravity chat.
3. Replace bracketed placeholders like `[your_dataset_name.csv]` with your actual filenames and column names.

---

## 🧪 Step 1: Dataset Inspection & Column Mapping

```text
Hello Antigravity! We are transitioning Gojo Sentinel from synthetic demo data to our real transaction dataset.

I have placed our real dataset file inside the project folder at: data/[your_dataset_name.csv].

Please inspect this dataset and tell me:
1. Total row count, missing values, and column names.
2. The proportion of fraudulent vs. legitimate transactions (target class ratio).
3. Map our dataset columns to Gojo Sentinel's internal schema (Amount, Sender Bank, Receiver Bank, Channel, Timestamp, User ID, and Fraud Label).
4. Update or create an ingestion script to standardize the column names if needed.
```

---

## ⚙️ Step 2: Feature Engineering & Preprocessing Pipeline

```text
Antigravity, please update `preprocessing.py` to process our real transaction dataset:

1. Extract time-series velocity features using transaction timestamps:
   - `txn_count_1h` and `txn_count_24h` (transaction counts per user/account).
   - `amt_sum_24h` and `amt_avg_24h` (total and mean transaction value in 24 hours).
   - `amt_ratio_vs_avg` (ratio of current transaction amount vs historical average).
   - `time_since_last_txn` (seconds since the user's previous transaction).
2. Handle categorical variables (Bank Names, Payment Channels) using `category-encoders`.
3. Apply `RobustScaler` or log-transformation to transaction amounts.
4. Make sure missing values are properly imputed.
```

---

## 📊 Step 3: Model Retraining & Evaluation

```text
Antigravity, please update `train.py` and retrain the XGBoost fraud detection model on our real dataset:

1. Use a chronological / time-series split (e.g., first 80% for training, final 20% for testing) to prevent data leakage.
2. Handle class imbalance using `scale_pos_weight` in XGBoost or `SMOTE`.
3. Evaluate the model performance using:
   - PR-AUC (Precision-Recall Area Under Curve).
   - Recall at 95% Precision.
   - Confusion Matrix (False Positives vs False Negatives).
4. Save the trained model and preprocessor artifacts to the `models/` directory:
   - `models/xgb_model.json`
   - `models/preprocessor.pkl`
   - `models/model_version.json`
```

---

## 🎯 Step 4: Risk Threshold Calibration

```text
Antigravity, please calibrate the decision boundary for our model:

1. Analyze the Precision-Recall curve to find the optimal decision threshold (e.g. 0.30 - 0.40) that maximizes fraud detection while keeping false positive rate below 1%.
2. Save the optimal threshold value into `models/threshold.json`.
3. Verify that `app.py` correctly loads `models/threshold.json` and returns accurate risk levels (LOW, MEDIUM, HIGH, CRITICAL) for prediction requests.
```

---

## 🌐 Step 5: Verification & Production Deployment

```text
Antigravity, let's verify and deploy the updated real model:

1. Test the API locally by running the server script (`run_offline.bat` on Windows or `run_linux.sh` on Linux).
2. Send a test prediction request to `http://localhost:8000/api/v1/predict` to confirm predictions work.
3. Commit and push the updated model artifacts and code to GitHub (`git add . && git commit -m "Deploy real model" && git push origin main`).
4. Confirm that Hugging Face automatically rebuilds the web dashboard and GitHub Actions triggers a fresh Android APK build.
```

---
*Gojo Sentinel — AI-Powered Nigerian Fintech Security System*
