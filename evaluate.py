import json
import pandas as pd
from sklearn.metrics import precision_score, recall_score, f1_score, confusion_matrix
from config import OUTPUT_DIR

df = pd.read_csv(OUTPUT_DIR / "processed_events.csv")
y = df["injected_anomaly"].astype(int)
pred = df["is_anomaly"].astype(int)
cm = confusion_matrix(y, pred).ravel().tolist()
metrics = {
    "known_fault_events": int(y.sum()),
    "rule_flagged_events": int(pred.sum()),
    "precision": float(precision_score(y, pred, zero_division=0)),
    "recall": float(recall_score(y, pred, zero_division=0)),
    "f1": float(f1_score(y, pred, zero_division=0)),
    "confusion_matrix_tn_fp_fn_tp": cm
}
(OUTPUT_DIR / "anomaly_metrics.json").write_text(json.dumps(metrics, indent=2))
print(json.dumps(metrics, indent=2))
