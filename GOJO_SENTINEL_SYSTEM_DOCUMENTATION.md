# 🛡️ GOJO SENTINEL
## Comprehensive System Architecture, Research Design, Implementation & Operational Guide

---

### **1. Problem Statement of the Study**
The rapid digitization of the Nigerian financial services sector—driven by the Central Bank of Nigeria (CBN) Cashless Policy and NIBSS Instant Payments (NIP)—has led to exponential growth in electronic transaction volumes. However, this expansion has been accompanied by a sophisticated rise in electronic financial fraud, costing Nigerian financial institutions billions of Naira annually.

Traditional fraud detection mechanisms in Nigerian banks rely primarily on static rule-based systems. While effective at enforcing hard statutory limits (such as daily transfer caps), static rules fail to adapt to complex, evolving fraud tactics like SIM-swap scams, credential harvesting, velocity attacks, and midnight account draining. Conversely, pure machine learning approaches often operate as "black boxes" that ignore statutory Central Bank of Nigeria (CBN) regulatory thresholds, leading to compliance risk and non-compliance fines.

Therefore, there is a critical need for a unified, hybrid fraud prevention system tailored to the Nigerian financial context that simultaneously guarantees 100% regulatory compliance while dynamically detecting complex fraud patterns with machine learning.

---

### **2. Aim & Objectives of the Study**
The primary aim of this project is to design, develop, and deploy **Gojo Sentinel**—a hybrid transaction fraud detection and regulatory compliance platform specifically engineered for Nigerian banking channels.

- **Objective 1 — Enforce Regulatory Compliance**: Implement a deterministic Nigerian Banking Compliance Engine enforcing CBN operational caps (USSD ₦100,000 daily limit, NIP ₦5,000,000 single transfer cap, midnight velocity checks, and restricted bank watchlists).
- **Objective 2 — Train Machine Learning Model**: Develop and train an XGBoost (Extreme Gradient Boosting) classifier to evaluate non-linear feature interactions and compute probabilistic fraud risk scores.
- **Objective 3 — Dual-Mode Screening Pipeline**: Build a unified pipeline supporting both real-time single transaction scoring and high-volume CSV dataset batch screening with live audit terminal logs.
- **Objective 4 — Modern Multi-Device Interface**: Design a responsive frontend UI featuring a Gemini-style Collapsible Rail Sidebar, 30-Day Activity Trend Analytics, and an Apache Cordova Android mobile APK package.
- **Objective 5 — Enterprise Security & Access Control**: Implement role-based security using JWT authentication, admin rule management, and analyst monitoring privileges.

---

### **3. What the System Does (Risk Verdict Matrix)**

| Risk Level | Fraud Probability Range | Action Verdict | Operational System Behavior |
| :--- | :--- | :--- | :--- |
| **LOW RISK** | 0.0% - 29.9% | **`APPROVE`** | Transaction is processed instantly without user friction. |
| **MEDIUM RISK** | 30.0% - 59.9% | **`REVIEW`** | Held for step-up multi-factor authentication (2FA / OTP check). |
| **HIGH RISK** | 60.0% - 84.9% | **`DECLINE`** | Transaction declined; suspicious activity alert logged. |
| **CRITICAL RISK** | 85.0% - 100.0% | **`BLOCK`** | Transaction blocked immediately due to rule violation or critical fraud score. |

---

### **4. Frontend Architecture & Technology Stack**
- **Core Web Stack**: HTML5, Vanilla CSS3 (HSL dark mode design system, glassmorphism), Vanilla JavaScript (ES6+ async/await, Fetch API).
- **Gemini-Style Collapsible Rail Sidebar**: Supports Expanded Mode (260px with branding & text labels) and Collapsible Rail Mode (72px compact icon bar with centered SVGs and tooltips).
- **Real-Time Terminal Console & Progress Bar**: Animated 0-100% progress bar alongside a dark green live terminal logger outputting timestamped execution events during dataset batch processing.
- **Analytics & Visualizations**: Chart.js rendering 30-Day Activity Trends and interactive Risk Distribution Doughnut charts.
- **Vector SVG System**: 100% scalable SVG vector graphics across all icons, cards, and badges.

---

### **5. Backend Architecture & Technology Stack**
- **FastAPI & Uvicorn**: Asynchronous Python web framework delivering high concurrency.
- **XGBoost Classifier (`xgboost`)**: Extreme Gradient Boosting algorithm computing exact probability scores.
- **Data Preprocessing (`pandas`, `numpy`, `scikit-learn`)**: Data pipeline for real-time and bulk CSV records.
- **Security (`PyJWT`, `passlib`)**: JWT stateless authentication and bcrypt password hashing.

---

### **6. Detailed Step-by-Step User Guide**

#### **6.1 How to Start the System Locally**
- **Windows**: Double-click `run_offline.bat` in the project folder.
- **Linux / macOS**: Execute `./run_linux.sh` in terminal.

#### **6.2 Scoring Single Transactions**
1. Open the **Dashboard** tab.
2. Select a channel (NIP, USSD, POS, Mobile, Web).
3. Click **Normal Pattern** or **High-Risk Pattern** to fill sample data.
4. Click **Score Transaction** to view immediate Risk %, Decision Badge, and Compliance Violation tags.

#### **6.3 Bulk Dataset Batch Screening**
1. Open the **Batch Scanner** tab.
2. Drag & drop a dataset CSV file.
3. Observe the 4-Step Visualizer Boxes glow in real-time as the Live Terminal Console streams execution timestamps.
4. View the 4 Summary Stat Cards, Doughnut Chart, Top Rule Breaches, and Filterable Table.
5. Click **Export Audited CSV** to download the completed audit report.

#### **6.4 Admin Management**
1. Click **Admin Access** on the user card and log in (`admin` / `admin123`).
2. Manage rules under **Rules** tab or add users under **Users** tab.
