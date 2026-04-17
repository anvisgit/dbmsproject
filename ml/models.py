import os, sys, json
import numpy as np
import joblib
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.metrics import mean_absolute_error, r2_score, accuracy_score, classification_report

BASE_DIR   = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODELS_DIR = os.path.join(BASE_DIR, "ml", "models")
os.makedirs(MODELS_DIR, exist_ok=True)

_EMP_MAP = {"Salaried": 3, "Self-Employed": 2, "Business": 4, "Retired": 1}
_cache   = {}


def _load(name):
    if name not in _cache:
        path = os.path.join(MODELS_DIR, name)
        if not os.path.exists(path):
            raise FileNotFoundError(f"Model not found: {path}  -- run: python ml/models.py")
        _cache[name] = joblib.load(path)
    return _cache[name]


def _enc_emp(emp): return _EMP_MAP.get(emp, 2)


def train_all():
    np.random.seed(42)
    N = 5000

    monthly_income  = np.random.randint(15000, 300000, N).astype(float)
    emp_labels      = np.random.choice(["Salaried","Self-Employed","Business","Retired"], N, p=[0.55,0.20,0.20,0.05])
    emp_enc         = np.array([_enc_emp(e) for e in emp_labels])
    total_loans     = np.random.randint(0, 8, N).astype(float)
    total_defaults  = np.clip(np.random.poisson(0.3, N) + (total_loans > 4).astype(int), 0, total_loans).astype(float)
    loan_amount     = np.random.randint(50000, 5000000, N).astype(float)
    tenure          = np.random.choice([12,18,24,36,48,60,84,120,240,300,360], N).astype(float)
    interest_rate   = np.clip(np.random.normal(10, 3, N), 6, 18).astype(float)
    overdue_days    = np.where(total_defaults > 0, np.random.randint(15, 200, N), np.zeros(N)).astype(float)

    score_value = (
        350
        + (monthly_income / 300000) * 200
        + (emp_enc / 4.0) * 80
        + (1 - total_defaults / (total_loans + 1)) * 200
        - (loan_amount / 5000000) * 50
        - (total_defaults * 30)
        + np.random.normal(0, 20, N)
    ).clip(300, 900).astype(int)

    risk_level = np.where(score_value >= 751, "Low", np.where(score_value >= 601, "Medium", "High"))

    default_prob_raw = (
        0.05 + 0.3*(total_defaults/(total_loans+1)) + 0.2*(overdue_days/200.0)
        + 0.15*(1-score_value/900.0) + 0.1*(interest_rate/18.0) + 0.05*(total_loans/8.0)
    )
    will_default = (default_prob_raw + np.random.normal(0, 0.05, N) > 0.4).astype(int)

    print("Training Model 1: Credit Score Predictor")
    X = np.column_stack([monthly_income, emp_enc, total_loans, total_defaults, loan_amount, tenure])
    Xtr, Xte, ytr, yte = train_test_split(X, score_value.astype(float), test_size=0.2, random_state=42)
    m1 = RandomForestRegressor(n_estimators=200, max_depth=12, random_state=42, n_jobs=-1)
    m1.fit(Xtr, ytr)
    print(f"  MAE={mean_absolute_error(yte, m1.predict(Xte)):.2f}  R2={r2_score(yte, m1.predict(Xte)):.4f}")
    joblib.dump(m1, os.path.join(MODELS_DIR, "credit_score_model.pkl"))

    print("Training Model 2: Risk Classifier")
    le = LabelEncoder()
    yr = le.fit_transform(risk_level)
    X2 = np.column_stack([score_value, total_defaults, monthly_income, loan_amount])
    Xtr, Xte, ytr, yte = train_test_split(X2, yr, test_size=0.2, random_state=42, stratify=yr)
    m2 = RandomForestClassifier(n_estimators=200, max_depth=10, random_state=42, n_jobs=-1)
    m2.fit(Xtr, ytr)
    print(f"  Accuracy={accuracy_score(yte, m2.predict(Xte)):.4f}")
    joblib.dump(m2, os.path.join(MODELS_DIR, "risk_classifier.pkl"))
    joblib.dump(le, os.path.join(MODELS_DIR, "risk_label_encoder.pkl"))

    print("Training Model 3: Default Predictor")
    X3  = np.column_stack([score_value, overdue_days, tenure, interest_rate, total_defaults])
    sc  = StandardScaler()
    X3s = sc.fit_transform(X3)
    Xtr, Xte, ytr, yte = train_test_split(X3s, will_default, test_size=0.2, random_state=42, stratify=will_default)
    m3  = LogisticRegression(max_iter=1000, class_weight="balanced", random_state=42)
    m3.fit(Xtr, ytr)
    print(f"  Accuracy={accuracy_score(yte, m3.predict(Xte)):.4f}")
    joblib.dump(m3, os.path.join(MODELS_DIR, "default_predictor.pkl"))
    joblib.dump(sc, os.path.join(MODELS_DIR, "default_scaler.pkl"))

    meta = {
        "credit_score_model": {"type":"RandomForestRegressor","features":["monthly_income","employment_enc","total_loans","total_defaults","loan_amount","tenure"]},
        "risk_classifier":    {"type":"RandomForestClassifier","classes":le.classes_.tolist()},
        "default_predictor":  {"type":"LogisticRegression","features":["score_value","overdue_days","tenure","interest_rate","total_defaults"]}
    }
    with open(os.path.join(MODELS_DIR, "metadata.json"), "w") as f:
        json.dump(meta, f, indent=2)
    print("All models saved to ml/models/")


def predict_credit_score(monthly_income, employment_type, total_loans, total_defaults, loan_amount, tenure):
    m   = _load("credit_score_model.pkl")
    X   = np.array([[monthly_income, _enc_emp(employment_type), total_loans, total_defaults, loan_amount, tenure]], dtype=float)
    return int(np.clip(m.predict(X)[0], 300, 900))


def predict_risk_level(score_value, total_defaults, monthly_income, loan_amount):
    m  = _load("risk_classifier.pkl")
    le = _load("risk_label_encoder.pkl")
    X  = np.array([[score_value, total_defaults, monthly_income, loan_amount]], dtype=float)
    enc = m.predict(X)[0]
    proba = m.predict_proba(X)[0]
    return {
        "risk_level":    le.inverse_transform([enc])[0],
        "probabilities": {le.inverse_transform([i])[0]: round(float(p), 4) for i, p in enumerate(proba)}
    }


def predict_default_probability(score_value, overdue_days, tenure, interest_rate, total_defaults):
    m  = _load("default_predictor.pkl")
    sc = _load("default_scaler.pkl")
    X  = sc.transform(np.array([[score_value, overdue_days, tenure, interest_rate, total_defaults]], dtype=float))
    p  = m.predict_proba(X)[0]
    dp = float(p[1])
    return {
        "will_default": bool(m.predict(X)[0]),
        "probability":  round(dp, 4),
        "no_default_prob": round(float(p[0]), 4),
        "confidence":   ("Very High" if dp > 0.75 else "High" if dp > 0.55 else "Moderate" if dp > 0.35 else "Low")
    }


def run_full_prediction(monthly_income, employment_type, total_loans, total_defaults,
                        loan_amount, tenure, interest_rate, overdue_days=0):
    score   = predict_credit_score(monthly_income, employment_type, total_loans, total_defaults, loan_amount, tenure)
    risk    = predict_risk_level(score, total_defaults, monthly_income, loan_amount)
    default = predict_default_probability(score, overdue_days, tenure, interest_rate, total_defaults)
    return {
        "credit_score":        score,
        "risk_level":          risk["risk_level"],
        "risk_probabilities":  risk["probabilities"],
        "default_probability": default["probability"],
        "will_default":        default["will_default"],
        "default_confidence":  default["confidence"],
        "auto_approved":       (score > 600) and (default["probability"] < 0.4)
    }


if __name__ == "__main__":
    train_all()
