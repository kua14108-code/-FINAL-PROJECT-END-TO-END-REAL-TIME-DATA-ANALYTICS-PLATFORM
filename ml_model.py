import json
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (accuracy_score, precision_score, recall_score, f1_score,
                             roc_auc_score, confusion_matrix, classification_report)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import make_pipeline
from sklearn.impute import SimpleImputer
from config import RANDOM_SEED, METRICS_JSON

FEATURES = ["temperature_c", "humidity_pct", "co2_ppm", "occupancy", "power_kw"]

def train_and_evaluate(df):
    """Predict whether the next reading will violate the comfort rule."""
    x = df.sort_values(["sensor_id", "timestamp"]).copy()
    x["next_comfort"] = x.groupby("sensor_id")["comfort_flag"].shift(-1).fillna(0).astype(int)
    x["target"] = 1 - x["next_comfort"]  # 1 = at-risk next step; 0 = comfortable
    x = x.dropna(subset=FEATURES + ["target"])
    X, y = x[FEATURES], x["target"]
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.25, random_state=RANDOM_SEED, stratify=y
    )
    model = make_pipeline(
        SimpleImputer(strategy="median"),
        RandomForestClassifier(n_estimators=160, max_depth=9, min_samples_leaf=3,
                               class_weight="balanced", random_state=RANDOM_SEED, n_jobs=-1)
    )
    model.fit(X_train, y_train)
    pred = model.predict(X_test)
    prob = model.predict_proba(X_test)[:, 1]
    metrics = {
        "task": "next-reading risk classification (1=at-risk, 0=comfortable)",
        "rows": int(len(x)), "train_rows": int(len(X_train)), "test_rows": int(len(X_test)),
        "accuracy": float(accuracy_score(y_test, pred)),
        "precision": float(precision_score(y_test, pred, zero_division=0)),
        "recall": float(recall_score(y_test, pred, zero_division=0)),
        "f1": float(f1_score(y_test, pred, zero_division=0)),
        "roc_auc": float(roc_auc_score(y_test, prob)) if len(np.unique(y_test)) > 1 else None,
        "confusion_matrix": confusion_matrix(y_test, pred).tolist(),
        "class_distribution": {str(int(k)): int(v) for k,v in y.value_counts().items()}
    }
    METRICS_JSON.parent.mkdir(parents=True, exist_ok=True)
    METRICS_JSON.write_text(json.dumps(metrics, indent=2))
    return model, metrics
