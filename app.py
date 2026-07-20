from fastapi import FastAPI, HTTPException, Depends, Header, UploadFile, File
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import pandas as pd
import joblib
import xgboost as xgb
import uvicorn
import os
import json
import sqlite3
import hashlib
import secrets
import io
from datetime import datetime
from typing import Optional, List
from pathlib import Path
from contextlib import asynccontextmanager
import sqlite3

# Try importing psycopg2 for production PostgreSQL support
try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
    POSTGRES_AVAILABLE = True
except ImportError:
    POSTGRES_AVAILABLE = False

# ─── App Init ──────────────────────────────────────────────────────────────────
app = FastAPI(
    title="Gojo Sentinel — AI Fraud Detection API",
    description="Real-time AI-powered fraud detection for Nigerian banking transactions (NIP, POS, USSD, Web).",
    version="3.0.0"
)

# CORS — allow frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from fastapi.responses import JSONResponse
from fastapi import Request

# ─── Global Error Handler ──────────────────────────────────────────────────────
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"error": "Gojo Sentinel Internal Error", "detail": str(exc), "path": request.url.path}
    )

# ─── Database Config ────────────────────────────────────────────────────────────
DB_PATH = "data/gojo.db"
RULES_PATH = "data/rules.json"
DATABASE_URL = os.getenv("DATABASE_URL") # Provided by Render/Heroku

def get_db_conn():
    """Returns a database connection and a flag indicating if it's PostgreSQL."""
    global DATABASE_URL
    if DATABASE_URL and (DATABASE_URL.startswith("postgres") or "supabase" in DATABASE_URL):
        if not POSTGRES_AVAILABLE:
            print("❌ psycopg2-binary not installed. Falling back to SQLite.")
        else:
            # Fix for common URL prefix issues
            url = DATABASE_URL.replace("postgres://", "postgresql://", 1)
            try:
                # 5 second timeout to keep the app responsive
                conn = psycopg2.connect(url, connect_timeout=5)
                return conn, True
            except Exception as e:
                print(f"⚠️ Supabase Connection Failed: {e}")
                print("🔄 Using local SQLite database instead.")
    
    # Absolute path for SQLite to ensure it works on Render/Vercel
    Path("data").mkdir(exist_ok=True)
    db_path = os.path.abspath(DB_PATH)
    conn = sqlite3.connect(db_path)
    return conn, False

def execute_query(query: str, params: tuple = ()):
    """Executes a query and returns the cursor, handling placeholder differences."""
    conn, is_pg = get_db_conn()
    if is_pg:
        query = query.replace("?", "%s")
    
    # SQLite doesn't support 'SERIAL' or 'AUTOINCREMENT' in the same way
    # But since we use 'IF NOT EXISTS', we handle it in init_db
    
    cursor = conn.cursor()
    cursor.execute(query, params)
    return conn, cursor, is_pg

# ─── Load Models ───────────────────────────────────────────────────────────────
MODEL_LOADED = False
preprocessor = None
model = None
MODEL_VERSION = {"version": "3.0", "trained_at": datetime.utcnow().isoformat()}

def load_models():
    global preprocessor, model, MODEL_LOADED
    try:
        model_path = os.path.join("models", "xgb_model.json")
        prep_path = os.path.join("models", "preprocessor.pkl")
        if os.path.exists(prep_path) and os.path.exists(model_path):
            preprocessor = joblib.load(prep_path)
            model = xgb.XGBClassifier()
            model.load_model(model_path)
            MODEL_LOADED = True
            print("[OK] Gojo Sentinel models loaded successfully.")
        else:
            print("[WARN] Models not found in 'models/' folder. Please check your files.")
    except Exception as e:
        print(f"[ERROR] Model loading failed: {e}")

load_models()

# ─── Database Init ──────────────────────────────────────────────────────────────
def init_db():
    conn = None
    try:
        conn, is_pg = get_db_conn()
        c = conn.cursor()

        # PK Syntax differences
        id_pk = "SERIAL PRIMARY KEY" if is_pg else "INTEGER PRIMARY KEY AUTOINCREMENT"

        # Prediction history
        c.execute(f"""
            CREATE TABLE IF NOT EXISTS predictions (
                id {id_pk},
                transaction_id TEXT,
                user_id TEXT,
                amount_ngn REAL,
                sender_bank TEXT,
                receiver_bank TEXT,
                channel TEXT,
                bvn_match INTEGER,
                fraud_probability REAL,
                is_fraud INTEGER,
                risk_level TEXT,
                recommendation TEXT,
                scored_at TEXT
            )
        """)

        # Users table
        c.execute(f"""
            CREATE TABLE IF NOT EXISTS users (
                id {id_pk},
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL DEFAULT 'staff',
                full_name TEXT,
                email TEXT,
                is_active INTEGER DEFAULT 1,
                created_at TEXT,
                last_login TEXT
            )
        """)

        # Sessions table
        c.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                token TEXT PRIMARY KEY,
                user_id INTEGER,
                username TEXT,
                role TEXT,
                created_at TEXT
            )
        """)

        # Seed default admin if no users exist
        c.execute("SELECT COUNT(*) FROM users")
        if c.fetchone()[0] == 0:
            admin_hash = hashlib.sha256("gojo2026".encode()).hexdigest()
            placeholder = "%s" if is_pg else "?"
            c.execute(f"""
                INSERT INTO users (username, password_hash, role, full_name, email, created_at)
                VALUES ({placeholder}, {placeholder}, 'admin', 'System Administrator', 'admin@gojosentinel.ng', {placeholder})
            """, ("admin", admin_hash, datetime.utcnow().isoformat()))
            print("[OK] Default admin created: admin / gojo2026")

        conn.commit()
        print("[OK] Database initialized.")
    except Exception as e:
        print(f"[ERROR] Database initialization failed: {e}")
    finally:
        if conn:
            conn.close()

# Initialize everything
init_db()

# ─── Rules Init ────────────────────────────────────────────────────────────────
def init_rules():
    if not os.path.exists(RULES_PATH):
        default_rules = [
            {"id": 1, "name": "High Amount Alert", "type": "amount_threshold", "value": 500000, "enabled": True, "action": "REVIEW", "description": "Flag transactions above ₦500,000"},
            {"id": 2, "name": "Critical Amount Block", "type": "amount_threshold", "value": 2000000, "enabled": True, "action": "BLOCK", "description": "Block transactions above ₦2,000,000"},
            {"id": 3, "name": "Late Night Window", "type": "time_window", "value": "00:00-04:00", "enabled": True, "action": "REVIEW", "description": "Flag transactions between 12AM – 4AM"},
            {"id": 4, "name": "BVN Mismatch Block", "type": "bvn_mismatch", "value": 0, "enabled": True, "action": "DECLINE", "description": "Decline if BVN names do not match"},
            {"id": 5, "name": "USSD High Risk", "type": "channel_risk", "value": "USSD", "enabled": True, "action": "REVIEW", "description": "Flag all high-value USSD transactions"},
        ]
        with open(RULES_PATH, "w") as f:
            json.dump(default_rules, f, indent=2)
        print("[OK] Default fraud rules created.")

try:
    init_rules()
except Exception as e:
    print(f"[ERROR] Rules initialization failed: {e}")

# ─── Auth Helpers ───────────────────────────────────────────────────────────────
def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def create_session(user_id: int, username: str, role: str) -> str:
    token = secrets.token_hex(32)
    conn, is_pg = get_db_conn()
    c = conn.cursor()
    placeholder = "%s" if is_pg else "?"
    c.execute(f"INSERT INTO sessions (token, user_id, username, role, created_at) VALUES ({placeholder},{placeholder},{placeholder},{placeholder},{placeholder})",
              (token, user_id, username, role, datetime.utcnow().isoformat()))
    c.execute(f"UPDATE users SET last_login={placeholder} WHERE id={placeholder}", (datetime.utcnow().isoformat(), user_id))
    conn.commit()
    conn.close()
    return token

def get_session(token: str) -> Optional[dict]:
    if not token:
        return None
    conn, is_pg = get_db_conn()
    c = conn.cursor()
    placeholder = "%s" if is_pg else "?"
    c.execute(f"SELECT user_id, username, role FROM sessions WHERE token={placeholder}", (token,))
    row = c.fetchone()
    conn.close()
    if row:
        return {"user_id": row[0], "username": row[1], "role": row[2]}
    return None

def require_auth(authorization: str = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Authentication required")
    token = authorization[7:]
    session = get_session(token)
    if not session:
        raise HTTPException(status_code=401, detail="Invalid or expired session")
    return session

def require_admin(session: dict = Depends(require_auth)):
    if session["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return session

# ─── Nigerian Context Constants ─────────────────────────────────────────────────
NIGERIAN_BANKS = [
    "GTBank", "Zenith Bank", "Access Bank", "UBA", "First Bank",
    "Opay", "Moniepoint", "Kuda", "Fidelity Bank", "Sterling Bank"
]
CHANNELS = ["NIP", "POS", "USSD", "Web"]

# ─── Schemas ───────────────────────────────────────────────────────────────────
class TransactionReq(BaseModel):
    transaction_id: str
    user_id: str
    amount_ngn: float
    sender_bank: str
    receiver_bank: str
    channel: str
    sender_nuban: str
    receiver_nuban: str
    bvn_match: int
    timestamp: str
    txn_count_1h: int = 0
    txn_count_24h: int = 0
    amt_sum_24h: float = 0.0

class FraudResp(BaseModel):
    transaction_id: str
    fraud_probability: float
    is_fraud: bool
    risk_level: str
    recommendation: str

class HealthResp(BaseModel):
    status: str
    model_loaded: bool
    api_version: str
    model_version: dict
    supported_banks: list
    supported_channels: list
    total_predictions: int

class LoginReq(BaseModel):
    username: str
    password: str

class UserCreateReq(BaseModel):
    username: str
    password: str
    role: str = "staff"
    full_name: str = ""
    email: str = ""

class UserUpdateReq(BaseModel):
    full_name: Optional[str] = None
    email: Optional[str] = None
    role: Optional[str] = None
    is_active: Optional[int] = None
    password: Optional[str] = None

class RuleCreateReq(BaseModel):
    name: str
    type: str
    value: object
    enabled: bool = True
    action: str
    description: str = ""

# ─── Helpers ───────────────────────────────────────────────────────────────────
def get_risk_level(prob: float) -> tuple:
    if prob < 0.25:
        return "LOW", "APPROVE"
    elif prob < 0.50:
        return "MEDIUM", "REVIEW"
    elif prob < 0.75:
        return "HIGH", "DECLINE"
    else:
        return "CRITICAL", "BLOCK"

def ensure_velocity_features(df: pd.DataFrame) -> pd.DataFrame:
    for col in ["txn_count_1h", "txn_count_24h", "amt_sum_24h"]:
        if col not in df.columns:
            df[col] = 0
    return df

def log_prediction(txn: TransactionReq, result: FraudResp):
    try:
        conn, is_pg = get_db_conn()
        c = conn.cursor()
        placeholder = "%s" if is_pg else "?"
        c.execute(f"""
            INSERT INTO predictions
            (transaction_id, user_id, amount_ngn, sender_bank, receiver_bank, channel,
             bvn_match, fraud_probability, is_fraud, risk_level, recommendation, scored_at)
            VALUES ({placeholder},{placeholder},{placeholder},{placeholder},{placeholder},{placeholder},{placeholder},{placeholder},{placeholder},{placeholder},{placeholder},{placeholder})
        """, (txn.transaction_id, txn.user_id, txn.amount_ngn, txn.sender_bank,
              txn.receiver_bank, txn.channel, txn.bvn_match,
              result.fraud_probability, int(result.is_fraud),
              result.risk_level, result.recommendation, datetime.utcnow().isoformat()))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"[WARN] Failed to log prediction: {e}")

# ─── Auth Endpoints ─────────────────────────────────────────────────────────────
@app.post("/api/v1/auth/login")
async def login(req: LoginReq):
    conn, is_pg = get_db_conn()
    c = conn.cursor()
    placeholder = "%s" if is_pg else "?"
    c.execute(f"SELECT id, username, role, full_name, is_active FROM users WHERE username={placeholder} AND password_hash={placeholder}",
              (req.username, hash_password(req.password)))
    row = c.fetchone()
    conn.close()
    if not row:
        raise HTTPException(status_code=401, detail="Invalid username or password")
    if not row[4]:
        raise HTTPException(status_code=403, detail="Account is disabled")
    token = create_session(row[0], row[1], row[2])
    return {
        "token": token,
        "username": row[1],
        "role": row[2],
        "full_name": row[3] or row[1],
        "message": "Login successful"
    }

@app.post("/api/v1/auth/logout")
async def logout(session: dict = Depends(require_auth), authorization: str = Header(None)):
    token = authorization[7:]
    conn, is_pg = get_db_conn()
    placeholder = "%s" if is_pg else "?"
    conn.execute(f"DELETE FROM sessions WHERE token={placeholder}", (token,))
    conn.commit()
    conn.close()
    return {"message": "Logged out successfully"}

@app.get("/api/v1/auth/me")
async def get_me(session: dict = Depends(require_auth)):
    conn, is_pg = get_db_conn()
    c = conn.cursor()
    placeholder = "%s" if is_pg else "?"
    c.execute(f"SELECT id, username, role, full_name, email, created_at, last_login FROM users WHERE id={placeholder}", (session["user_id"],))
    row = c.fetchone()
    conn.close()
    if not row:
        raise HTTPException(status_code=404, detail="User not found")
    return {
        "id": row[0], "username": row[1], "role": row[2],
        "full_name": row[3], "email": row[4],
        "created_at": row[5], "last_login": row[6]
    }

# ─── User Management Endpoints ──────────────────────────────────────────────────
@app.get("/api/v1/users")
async def list_users(session: dict = Depends(require_admin)):
    conn, is_pg = get_db_conn()
    c = conn.cursor()
    c.execute("SELECT id, username, role, full_name, email, is_active, created_at, last_login FROM users ORDER BY created_at DESC")
    rows = c.fetchall()
    conn.close()
    return [{"id": r[0], "username": r[1], "role": r[2], "full_name": r[3],
             "email": r[4], "is_active": r[5], "created_at": r[6], "last_login": r[7]}
            for r in rows]

@app.post("/api/v1/users", status_code=201)
async def create_user(req: UserCreateReq, session: dict = Depends(require_admin)):
    if req.role not in ("admin", "sub_admin", "staff"):
        raise HTTPException(status_code=400, detail="Role must be: admin, sub_admin, or staff")
    try:
        conn, is_pg = get_db_conn()
        c = conn.cursor()
        placeholder = "%s" if is_pg else "?"
        c.execute(f"""
            INSERT INTO users (username, password_hash, role, full_name, email, created_at)
            VALUES ({placeholder},{placeholder},{placeholder},{placeholder},{placeholder},{placeholder})
        """, (req.username, hash_password(req.password), req.role,
              req.full_name, req.email, datetime.utcnow().isoformat()))
        new_id = c.lastrowid if not is_pg else c.fetchone() # Postgres RETURNING would be better but let's keep it simple
        # For Postgres, c.lastrowid is usually not reliable without RETURNING
        if is_pg:
            # Re-fetch the ID if needed, or just return success
            new_id = 0 
        conn.commit()
        conn.close()
        return {"id": new_id, "username": req.username, "role": req.role, "message": "User created"}
    except (sqlite3.IntegrityError, Exception) as e:
        raise HTTPException(status_code=409, detail=f"User creation failed: {e}")

@app.put("/api/v1/users/{user_id}")
async def update_user(user_id: int, req: UserUpdateReq, session: dict = Depends(require_admin)):
    conn, is_pg = get_db_conn()
    c = conn.cursor()
    placeholder = "%s" if is_pg else "?"
    fields, vals = [], []
    if req.full_name is not None: fields.append("full_name="+placeholder); vals.append(req.full_name)
    if req.email is not None: fields.append("email="+placeholder); vals.append(req.email)
    if req.role is not None: fields.append("role="+placeholder); vals.append(req.role)
    if req.is_active is not None: fields.append("is_active="+placeholder); vals.append(req.is_active)
    if req.password is not None: fields.append("password_hash="+placeholder); vals.append(hash_password(req.password))
    if not fields:
        conn.close()
        raise HTTPException(status_code=400, detail="No fields to update")
    vals.append(user_id)
    c.execute(f"UPDATE users SET {', '.join(fields)} WHERE id={placeholder}", vals)
    conn.commit()
    conn.close()
    return {"message": "User updated"}

@app.delete("/api/v1/users/{user_id}")
async def delete_user(user_id: int, session: dict = Depends(require_admin)):
    if user_id == session["user_id"]:
        raise HTTPException(status_code=400, detail="Cannot delete your own account")
    conn, is_pg = get_db_conn()
    placeholder = "%s" if is_pg else "?"
    conn.execute(f"DELETE FROM users WHERE id={placeholder}", (user_id,))
    conn.commit()
    conn.close()
    return {"message": "User deleted"}

# ─── Fraud Rules Endpoints ──────────────────────────────────────────────────────
@app.get("/api/v1/rules")
async def get_rules(session: dict = Depends(require_auth)):
    with open(RULES_PATH) as f:
        return json.load(f)

@app.post("/api/v1/rules", status_code=201)
async def create_rule(req: RuleCreateReq, session: dict = Depends(require_admin)):
    with open(RULES_PATH) as f:
        rules = json.load(f)
    new_id = max((r["id"] for r in rules), default=0) + 1
    new_rule = {"id": new_id, "name": req.name, "type": req.type,
                "value": req.value, "enabled": req.enabled,
                "action": req.action, "description": req.description}
    rules.append(new_rule)
    with open(RULES_PATH, "w") as f:
        json.dump(rules, f, indent=2)
    return new_rule

@app.put("/api/v1/rules/{rule_id}")
async def update_rule(rule_id: int, req: RuleCreateReq, session: dict = Depends(require_admin)):
    with open(RULES_PATH) as f:
        rules = json.load(f)
    for i, r in enumerate(rules):
        if r["id"] == rule_id:
            rules[i] = {"id": rule_id, "name": req.name, "type": req.type,
                        "value": req.value, "enabled": req.enabled,
                        "action": req.action, "description": req.description}
            with open(RULES_PATH, "w") as f:
                json.dump(rules, f, indent=2)
            return rules[i]
    raise HTTPException(status_code=404, detail="Rule not found")

@app.delete("/api/v1/rules/{rule_id}")
async def delete_rule(rule_id: int, session: dict = Depends(require_admin)):
    with open(RULES_PATH) as f:
        rules = json.load(f)
    rules = [r for r in rules if r["id"] != rule_id]
    with open(RULES_PATH, "w") as f:
        json.dump(rules, f, indent=2)
    return {"message": "Rule deleted"}

# ─── Transactions History Endpoint ──────────────────────────────────────────────
@app.get("/api/v1/transactions/history")
async def get_transaction_history(limit: int = 100, session: dict = Depends(require_auth)):
    conn, is_pg = get_db_conn()
    c = conn.cursor()
    placeholder = "%s" if is_pg else "?"
    c.execute(f"""
        SELECT id, transaction_id, user_id, amount_ngn, sender_bank, receiver_bank,
               channel, bvn_match, fraud_probability, is_fraud, risk_level, recommendation, scored_at
        FROM predictions ORDER BY id DESC LIMIT {placeholder}
    """, (limit,))
    rows = c.fetchall()
    conn.close()
    keys = ["id","transaction_id","user_id","amount_ngn","sender_bank","receiver_bank",
            "channel","bvn_match","fraud_probability","is_fraud","risk_level","recommendation","scored_at"]
    return [dict(zip(keys, r)) for r in rows]

@app.get("/api/v1/transactions/stats")
async def get_stats(session: dict = Depends(require_auth)):
    conn, is_pg = get_db_conn()
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM predictions")
    total = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM predictions WHERE is_fraud=1")
    fraud_count = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM predictions WHERE risk_level='CRITICAL'")
    critical = c.fetchone()[0]
    c.execute("SELECT AVG(fraud_probability) FROM predictions")
    avg_prob = c.fetchone()[0] or 0
    conn.close()
    return {
        "total_predictions": total,
        "fraud_detected": fraud_count,
        "critical_alerts": critical,
        "avg_fraud_probability": round(avg_prob, 4),
        "fraud_rate": round(fraud_count / total * 100, 2) if total > 0 else 0
    }

# ─── Predict Endpoint ───────────────────────────────────────────────────────────
@app.post("/api/v1/predict", response_model=FraudResp)
async def predict_fraud(transaction: TransactionReq):
    if not MODEL_LOADED:
        raise HTTPException(
            status_code=503,
            detail="Model not loaded. Run: python generate_data.py && python train.py"
        )
    try:
        df = pd.DataFrame([{
            "transaction_id": transaction.transaction_id,
            "user_id": transaction.user_id,
            "amount_ngn": transaction.amount_ngn,
            "sender_bank": transaction.sender_bank,
            "receiver_bank": transaction.receiver_bank,
            "channel": transaction.channel,
            "sender_nuban": transaction.sender_nuban,
            "receiver_nuban": transaction.receiver_nuban,
            "bvn_match": transaction.bvn_match,
            "timestamp": transaction.timestamp,
            "txn_count_1h": transaction.txn_count_1h,
            "txn_count_24h": transaction.txn_count_24h,
            "amt_sum_24h": transaction.amt_sum_24h,
        }])
        df = ensure_velocity_features(df)
        X_processed = preprocessor.transform(df)
        proba = float(model.predict_proba(X_processed)[0][1])
        is_fraud = proba >= 0.5
        risk_level, recommendation = get_risk_level(proba)

        result = FraudResp(
            transaction_id=transaction.transaction_id,
            fraud_probability=round(proba, 4),
            is_fraud=is_fraud,
            risk_level=risk_level,
            recommendation=recommendation
        )
        log_prediction(transaction, result)
        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction error: {str(e)}")

# ─── Batch Prediction Endpoint ──────────────────────────────────────────────────
@app.post("/api/v1/batch-predict")
async def batch_predict(file: UploadFile = File(...)):
    if not MODEL_LOADED:
        raise HTTPException(
            status_code=503,
            detail="Model not loaded. Please train the model first."
        )
    if not file.filename.endswith(('.csv', '.txt')):
        raise HTTPException(status_code=400, detail="Only CSV files are supported.")
    
    try:
        contents = await file.read()
        df_raw = pd.read_csv(io.BytesIO(contents))
        if df_raw.empty:
            raise HTTPException(status_code=400, detail="Uploaded CSV file is empty.")
        
        # Standardize column headers (case-insensitive & alias mapping)
        cols_lower = {str(c).strip().lower(): c for c in df_raw.columns}
        
        def find_col(aliases, default=None):
            for alias in aliases:
                if alias in cols_lower:
                    return df_raw[cols_lower[alias]]
            return default

        n_rows = len(df_raw)
        
        # Extract or assign defaults
        txn_ids = find_col(["transaction_id", "txnid", "id", "reference", "ref"], pd.Series([f"TXN-{i+1:05d}" for i in range(n_rows)]))
        user_ids = find_col(["user_id", "account_number", "accnum", "customer_id", "userid"], pd.Series([f"U{i+1:05d}" for i in range(n_rows)]))
        amounts = find_col(["amount_ngn", "amount", "val", "amt", "transaction_amount"], pd.Series([25000.0]*n_rows))
        sender_banks = find_col(["sender_bank", "origin_bank", "from_bank", "bank"], pd.Series(["GTBank"]*n_rows))
        receiver_banks = find_col(["receiver_bank", "dest_bank", "to_bank"], pd.Series(["Opay"]*n_rows))
        channels = find_col(["channel", "txn_type", "type", "payment_channel"], pd.Series(["NIP"]*n_rows))
        timestamps = find_col(["timestamp", "txndate", "date", "created_at"], pd.Series([datetime.utcnow().isoformat()]*n_rows))
        
        # Parse numeric amounts
        amounts = pd.to_numeric(amounts, errors='coerce').fillna(25000.0)
        
        # Build normalized DataFrame for model feature pipeline
        df_norm = pd.DataFrame({
            "transaction_id": txn_ids,
            "user_id": user_ids,
            "amount_ngn": amounts,
            "sender_bank": sender_banks,
            "receiver_bank": receiver_banks,
            "channel": channels,
            "sender_nuban": find_col(["sender_nuban", "from_acc"], pd.Series(["4609537366"]*n_rows)),
            "receiver_nuban": find_col(["receiver_nuban", "to_acc"], pd.Series(["4543049469"]*n_rows)),
            "bvn_match": pd.to_numeric(find_col(["bvn_match", "bvn"], pd.Series([1]*n_rows)), errors='coerce').fillna(1),
            "timestamp": timestamps,
            "txn_count_1h": find_col(["txn_count_1h"], pd.Series([0]*n_rows)),
            "txn_count_24h": find_col(["txn_count_24h"], pd.Series([0]*n_rows)),
            "amt_sum_24h": find_col(["amt_sum_24h"], pd.Series([0.0]*n_rows))
        })
        
        df_norm = ensure_velocity_features(df_norm)
        
        # Model predictions
        X_proc = preprocessor.transform(df_norm)
        probabilities = model.predict_proba(X_proc)[:, 1]
        
        # Load active Nigerian Banking & Security Rules
        rules = []
        if os.path.exists(RULES_PATH):
            try:
                with open(RULES_PATH) as f:
                    rules = [r for r in json.load(f) if r.get("enabled", True)]
            except Exception:
                pass
        
        results_list = []
        risk_counts = {"LOW": 0, "MEDIUM": 0, "HIGH": 0, "CRITICAL": 0}
        channel_stats = {}
        rule_violation_counts = {}
        
        approved_vol = 0.0
        blocked_vol = 0.0
        
        for idx in range(n_rows):
            t_id = str(df_norm.at[idx, "transaction_id"])
            u_id = str(df_norm.at[idx, "user_id"])
            amt = float(df_norm.at[idx, "amount_ngn"])
            s_bank = str(df_norm.at[idx, "sender_bank"])
            r_bank = str(df_norm.at[idx, "receiver_bank"])
            ch = str(df_norm.at[idx, "channel"]).upper()
            prob = float(probabilities[idx])
            
            # Rule compliance checks
            violations = []
            forced_action = None
            
            # Nigerian Banking Rule 1: USSD Single/Daily Transfer Limit (Max N100,000)
            if ch == "USSD" and amt > 100000:
                violations.append("USSD transfer exceeds CBN ₦100,000 daily limit")
                forced_action = "BLOCK"
            
            # Nigerian Banking Rule 2: NIP High-Value Single Transfer Limit (Max N5,000,000)
            if ch == "NIP" and amt > 5000000:
                violations.append("NIP transfer exceeds single-txn threshold (₦5,000,000)")
                forced_action = "DECLINE"
                
            # Rule 3: Velocity Spike / Midnight High-Value Spikes
            if amt >= 1000000 and s_bank.lower() == r_bank.lower():
                violations.append("Self-transfer high value anomaly")
            
            # Custom Rules Check
            for r in rules:
                r_type = r.get("type")
                r_val = r.get("value")
                r_act = r.get("action", "FLAG")
                if r_type == "max_amount" and amt > float(r_val):
                    violations.append(f"Breached rule: {r.get('name')}")
                    if r_act in ["BLOCK", "DECLINE"]: forced_action = r_act
                elif r_type == "blocked_bank" and (s_bank.lower() == str(r_val).lower() or r_bank.lower() == str(r_val).lower()):
                    violations.append(f"Restricted Bank: {r_val}")
                    if r_act in ["BLOCK", "DECLINE"]: forced_action = r_act

            # Determine final risk & action
            if forced_action == "BLOCK":
                risk_level = "CRITICAL"
                recommendation = "BLOCK"
                prob = max(prob, 0.95)
                is_fraud = True
            elif forced_action == "DECLINE":
                risk_level = "HIGH"
                recommendation = "DECLINE"
                prob = max(prob, 0.75)
                is_fraud = True
            else:
                risk_level, recommendation = get_risk_level(prob)
                is_fraud = prob >= 0.5
            
            risk_counts[risk_level] += 1
            
            if recommendation in ["APPROVE"]:
                approved_vol += amt
            else:
                blocked_vol += amt

            # Channel aggregate stats
            if ch not in channel_stats:
                channel_stats[ch] = {"total": 0, "blocked": 0, "volume": 0.0}
            channel_stats[ch]["total"] += 1
            channel_stats[ch]["volume"] += amt
            if recommendation in ["DECLINE", "BLOCK"]:
                channel_stats[ch]["blocked"] += 1

            for v in violations:
                rule_violation_counts[v] = rule_violation_counts.get(v, 0) + 1
            
            results_list.append({
                "id": idx + 1,
                "transaction_id": t_id,
                "user_id": u_id,
                "amount_ngn": amt,
                "sender_bank": s_bank,
                "receiver_bank": r_bank,
                "channel": ch,
                "fraud_probability": round(prob, 4),
                "is_fraud": is_fraud,
                "risk_level": risk_level,
                "recommendation": recommendation,
                "violations": violations
            })

        # Top rule violations sorted
        top_violations = [{"rule": k, "count": v} for k, v in sorted(rule_violation_counts.items(), key=lambda x: x[1], reverse=True)]

        return {
            "file_name": file.filename,
            "total_transactions": n_rows,
            "approved_count": risk_counts["LOW"],
            "review_count": risk_counts["MEDIUM"],
            "blocked_count": risk_counts["HIGH"] + risk_counts["CRITICAL"],
            "approved_volume_ngn": round(approved_vol, 2),
            "blocked_volume_ngn": round(blocked_vol, 2),
            "risk_distribution": risk_counts,
            "channel_stats": channel_stats,
            "top_violations": top_violations,
            "records": results_list[:500]
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Batch processing error: {str(e)}")

# ─── Health Endpoint ────────────────────────────────────────────────────────────
@app.get("/api/v1/health", response_model=HealthResp)
async def health_check():
    total = 0
    try:
        conn, is_pg = get_db_conn()
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM predictions")
        total = c.fetchone()[0]
        conn.close()
    except Exception:
        pass
    return HealthResp(
        status="healthy" if MODEL_LOADED else "degraded",
        model_loaded=MODEL_LOADED,
        api_version="3.0.0",
        model_version=MODEL_VERSION,
        supported_banks=NIGERIAN_BANKS,
        supported_channels=CHANNELS,
        total_predictions=total
    )

@app.get("/ping")
async def ping():
    return {"status": "ok", "message": "Gojo Sentinel is alive"}

# ─── Frontend Serving ───────────────────────────────────────────────────────────
# Mount frontend files safely
if os.path.exists("frontend"):
    app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")
else:
    print("[WARN] frontend directory not found. Static files will not be served.")

if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
