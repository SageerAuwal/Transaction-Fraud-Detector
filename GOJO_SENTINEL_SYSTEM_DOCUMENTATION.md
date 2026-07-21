# 🛡️ GOJO SENTINEL
## Hybrid Transaction Fraud Detection & Regulatory Compliance System for Nigerian Banking

---

### **Executive Summary**
Gojo Sentinel is an enterprise-grade, hybrid artificial intelligence and regulatory compliance transaction screening platform built specifically for the Nigerian financial ecosystem. Financial fraud in Nigeria across electronic payment channels—such as NIBSS Instant Payments (NIP), USSD banking, Mobile Money, and Web portals—poses critical security challenges. Gojo Sentinel addresses these risks by coupling deterministic Central Bank of Nigeria (CBN) regulatory compliance rules with probabilistic Machine Learning (XGBoost) fraud scoring.

The system processes both single real-time transactions and large bulk datasets (CSV), delivering sub-second risk classification across four distinct verdicts: **APPROVE (Low Risk)**, **REVIEW (Medium Risk)**, **DECLINE (High Risk)**, and **BLOCK (Critical Policy Breach)**.

---

### **1. System Architecture & Design**
The system operates on a dual-engine architecture designed to ensure zero tolerance for statutory regulatory breaches while maintaining ultra-low false-positive rates using machine learning:

| Layer / Module | Technology Stack | Functional Purpose |
| :--- | :--- | :--- |
| **Backend REST API** | FastAPI / Python 3.10+ | High-throughput asynchronous API serving real-time prediction and dataset batch processing. |
| **Compliance Engine** | Deterministic Rule Set (CBN) | Instant verification against USSD caps, NIP single transfer limits, velocity thresholds, and restricted bank lists. |
| **AI Machine Learning Engine** | XGBoost Classifier | Probabilistic feature evaluation calculating exact fraud likelihood percentages based on historical transaction dynamics. |
| **User Interface (Web & Mobile)** | HTML5, Vanilla CSS, JS, Cordova | Responsive single-page web app & Cordova mobile APK featuring Gemini-style Collapsible Rail Sidebar, Live Terminal Logs, and Trend Analytics. |

---

### **2. Central Bank of Nigeria (CBN) Compliance Module**
- **USSD Transfer Caps**: Transactions initiated via USSD channel (`*901#`, `*737#`, `*894#`, etc.) exceeding **₦100,000 NGN** daily limit are automatically flagged as `CRITICAL` / `BLOCK` violations.
- **NIP Single Transfer Limit**: Single transfers over NIBSS Instant Payment (NIP) exceeding **₦5,000,000 NGN** are flagged for mandatory compliance review.
- **Midnight Velocity Spikes**: High-value transfers occurring between 11:00 PM and 04:30 AM are subjected to elevated risk scoring due to historical fraud correlation during non-operating hours.
- **Restricted Bank List**: Automatic flagging of transactions routed to or from high-risk accounts or institutions with active regulatory flags.

---

### **3. Risk Verdict Matrix**
| Risk Level | Probability Score | Action / Verdict | System Behavior |
| :--- | :--- | :--- | :--- |
| **LOW RISK** | 0.0% - 29.9% | **APPROVE** | Transaction cleared automatically without friction. |
| **MEDIUM RISK** | 30.0% - 59.9% | **REVIEW** | Transaction held for secondary verification or 2FA OTP prompt. |
| **HIGH RISK** | 60.0% - 84.9% | **DECLINE** | Transaction declined due to elevated fraud indicators. |
| **CRITICAL RISK** | 85.0% - 100.0% | **BLOCK** | Transaction blocked immediately; compliance audit alert generated. |

---

### **4. Dataset Batch Screening & Data Flow Pipeline**
1. **Stage 1 — CSV Ingestion**: Uploads and parses raw transaction records, validating schema and data types.
2. **Stage 2 — Banking Rules Verification**: Executed bulk evaluation against CBN policy thresholds and flags violations.
3. **Stage 3 — AI Fraud Model Scoring**: Passes feature vectors through the XGBoost engine to calculate individual risk scores.
4. **Stage 4 — Risk Verdict & Audit Generation**: Generates summary statistics, interactive doughnut charts, and a filterable audited table exportable as CSV.

---

### **5. Frontend Interface & User Experience**
- **Gemini-Style Collapsible Rail Sidebar**: Supports both Expanded Mode (260px with branding & text labels) and Collapsible Rail Mode (72px compact icon bar with centered SVGs and tooltips).
- **Real-Time Execution Console & Progress Bar**: Includes a dark green terminal logger streaming live timestamped pipeline logs alongside a smooth 0-100% progress bar.
- **30-Day Activity Trend Chart**: Permanently displayed on the main dashboard, dynamically updating legitimate vs. fraudulent volume trends in real time.
- **Vector SVG Design System**: All UI components use scalable SVG vector graphics instead of raster graphics or emojis for a professional, crisp financial software aesthetic.

---

### **6. Multi-Platform Deployment & Security**
- **Cloud Hosting**: Backend and Web Frontend hosted on Hugging Face Spaces with Docker containerization.
- **Mobile Android APK**: Packaged using Apache Cordova, providing native mobile functionality across Android devices.
- **Authentication & Security**: JWT (JSON Web Token) authentication with role-based access control (Admin / Analyst roles).
