# Transaction-Fraud-Detector: Gojo Sentinel AI

Gojo Sentinel is a professional-grade, real-time fraud detection system designed for the digital payment landscape. It combines advanced XGBoost machine learning models with a flexible rule engine to identify and block fraudulent transactions across multiple channels (NIP, POS, USSD, and Web).

## 🚀 Features

- **Real-Time Prediction**: Millisecond-level fraud scoring.
- **Explainable AI**: Risk indicators explaining why a transaction was flagged.
- **Hybrid System**: Combines machine learning with customizable administrative rules.
- **Premium Dashboard**: High-performance, responsive UI with interactive charts and gauges.
- **Offline Capable**: Designed to run in secure, internal bank environments without external dependencies.

## 🛠️ Tech Stack

- **Backend**: FastAPI (Python)
- **Machine Learning**: XGBoost, Scikit-learn
- **Frontend**: Vanilla JS, CSS3, HTML5
- **Database**: SQLite (Local) / PostgreSQL (Production)

## 📋 Prerequisites

- Python 3.8+
- Node.js (Optional, for advanced frontend development)

## 🔧 Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/SagirAuwal/Transaction-Fraud-Detector.git
   cd Transaction-Fraud-Detector
   ```

2. **Create a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Setup configuration**:
   - Copy `config.env.example` to `config.env`.
   - Update `API_KEY` and other settings as needed.

## 🏃 Running the Application

Start the FastAPI server:
```bash
python app.py
```
Or use uvicorn directly:
```bash
uvicorn app:app --reload
```

The dashboard will be available at `http://127.0.0.1:8000`.

## 🧠 Model Management

- **Retraining**: Run `python retrain.py` to update the model with new data.
- **Preprocessing**: Logic for feature engineering is located in `preprocessing.py`.
- **Models**: Pre-trained model files are stored in the `models/` directory.

## 📖 Documentation

For detailed technical specifications, architecture diagrams, and usage guides, please refer to the [System Documentation](doc/SYSTEM_DOCUMENTATION.md).

## 📄 License

[MIT License](LICENSE) (You may want to add a LICENSE file)
