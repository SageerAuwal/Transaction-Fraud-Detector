# Gojo Sentinel — System Documentation

## 1. Requirement Analysis
Gojo Sentinel was developed to address the critical need for real-time fraud detection in the rapidly evolving Nigerian digital payment landscape. The primary requirements included:
- **Multi-Channel Support**: Ability to analyze transactions across NIP (New Inter-bank Payment), POS, USSD, and Web channels.
- **Low Latency**: Decisions must be made in milliseconds to prevent fraudulent transactions before they are finalized.
- **Explainability**: The system must provide "Risk Indicators" explaining *why* a transaction was flagged (e.g., late-night window, large amount).
- **Rule-Based Overrides**: Admins need the ability to set hard limits (e.g., "Block all transactions above ₦5M") that override the AI model.

## 2. Planning
The project was planned with a focus on portability and performance:
- **Backend**: FastAPI was chosen for its high performance and native support for asynchronous operations.
- **AI Model**: XGBoost (Extreme Gradient Boosting) was selected for its superior performance on tabular transaction data.
- **Database**: A dual-layer strategy was planned—SQLite for local development/offline use and PostgreSQL for production cloud environments.
- **Frontend**: A custom Vanilla JS architecture was chosen over heavy frameworks to ensure zero dependencies and maximum performance.

## 3. Design
Gojo Sentinel utilizes a **Premium Dark Intelligence** aesthetic.
- **Visual Language**: Uses a palette of Deep Neon Cyan (Accent), Midnight Blues, and High-Contrast Status Colors (Red for Fraud, Green for Legitimate).
- **Data Visualization**: Features a 30-day dual-line activity trend chart and circular risk score gauges.
- **User Interface**: Designed with a "Dashboard-First" approach, placing the most critical scoring tools at the user's fingertips.

## 4. Development
The development followed a modular architecture:
- **Preprocessing Layer (`preprocessing.py`)**: Handles feature engineering, extracting temporal features (hour, day of week) and performing target encoding for user behavior.
- **Core API (`app.py`)**: Provides endpoints for prediction, rule management, and administrative health checks.
- **Frontend Layer**: Implemented as a Single Page Application (SPA) with a custom design system built in `styles.css`.
- **Security**: Implemented JWT (JSON Web Token) authentication with hashed passwords (SHA-256) for secure admin access.

## 5. Testing
The system underwent rigorous testing phases:
- **Simulation Testing**: Integrated "Normal" and "High-Risk" pattern simulators to verify model accuracy without needing live production data.
- **Rule Engine Validation**: Stress-tested the logic to ensure that user-defined rules (e.g., BVN mismatch) correctly override AI scores when required.
- **Responsive Testing**: Verified UI stability across different screen sizes (mobile/tablet/desktop) and browser themes.

## 6. Deployment
Gojo Sentinel is optimized for modern cloud platforms like **Render** or **Heroku**.
- **Environment Handling**: Uses `DATABASE_URL` to automatically switch between SQLite and PostgreSQL.
- **Process Management**: Configured with `Gunicorn` and `uvicorn` for production-grade reliability.
- **Asset Portability**: All icons are inline SVGs, and fonts are locally served, allowing the system to run completely offline in internal bank environments.

## 7. Maintenance and Updates
- **Model Retraining**: The system includes a `retrain.py` script to update the model as new fraud patterns emerge.
- **Rule Updates**: Rules can be deployed in real-time via the Admin Rules panel without restarting the server.
- **Scalability**: The modular backend can be easily extended to support additional payment channels or more complex AI risk factors.

---

## How the System Works (The Engine)

1. **Input Data**: The user enters transaction details (Amount, Channel, Bank, etc.) or clicks a simulation pattern.
2. **Feature Engineering**: The system automatically extracts hidden features:
   - **Temporal**: Is it a "Late Night" transaction (12 AM - 4 AM)?
   - **Behavioral**: How does this amount compare to the user's 24-hour average?
   - **Identity**: Is there a BVN name match?
3. **AI Scoring**: The cleaned data is passed to the **XGBoost Classifier**. The model compares the input against millions of known fraud patterns to generate a **Fraud Probability (0-100%)**.
4. **Rule Check**: Before the final verdict, the system checks against the **Active Rules Library**. If the transaction triggers a specific rule (e.g., "Amount > 1M"), the rule's recommendation (e.g., BLOCK) takes precedence.
5. **Verdict Delivery**: The final result is displayed on the dashboard with a circular gauge and a detailed breakdown of risk factors.

---

## How to Use Gojo Sentinel

### 1. Scoring a Transaction
- Navigate to the **Dashboard**.
- Select the **Payment Channel** (NIP, POS, USSD, or Web).
- Enter the **Transaction Amount** and select the banks.
- Click **Score Transaction**. The result will appear instantly in the result panel.
- *Tip: Use the "High-Risk Pattern" button to see how the system handles suspicious data.*

### 2. Managing Rules
- Log in as an **Admin** via the sidebar.
- Navigate to the **Rules** section.
- You can create rules based on:
  - **Amount Thresholds**: Set limits for specific actions.
  - **Time Windows**: Flag transactions happening at odd hours.
  - **BVN Match**: Automatically decline if identities don't match.
- Click **Deploy Rule** to make it active across the entire system.

### 3. Monitoring Trends
- Use the **30-Day Activity Trend** button on the dashboard to expand the chart.
- The **Green Line** shows legitimate transaction volume.
- The **Red Line** shows blocked or fraudulent attempts.
- Monitor these lines to see if there is a sudden spike in fraud attempts in your environment.

### 4. Admin Management
- In the **Users** section (Admin only), you can create accounts for Staff (Observers) or Sub-Admins (Managers).
- Each role has specific permissions ensuring that only authorized personnel can change rules or view detailed history.

---

## Summary
Gojo Sentinel is a professional-grade, AI-first security platform designed for the Nigerian fintech ecosystem. By combining advanced machine learning with a flexible rule engine and a premium enterprise UI, it provides a robust "first line of defense" for digital payment processors.
