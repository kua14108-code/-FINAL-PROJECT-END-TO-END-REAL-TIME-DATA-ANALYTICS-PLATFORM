# Smart Campus — End-to-End Real-Time Data Analytics Platform

**Team:** Ayazhan Temirbolatova and Aliya Kuanysh  
**Scenario:** Smart-campus classroom monitoring.

## 1. Overview
The platform simulates timestamped IoT events from six sensors in three classrooms. It validates and cleans incoming records, calculates rolling indicators, detects rule-based anomalies, predicts next-reading comfort status with Random Forest, processes room partitions in parallel worker processes, displays analytics in a Streamlit dashboard, and persists records in SQLite.

## 2. Architecture
`IoT Generator → Micro-batch Ingestion → Validation/Cleaning → Room-partitioned Workers → Rolling Analytics & Anomaly Rules → Random Forest Inference/Evaluation → Streamlit Dashboard → SQLite`

## 3. Requirements
- Python 3.10+
- Install packages: `pip install -r requirements.txt`

## 4. Run the full pipeline
From the project root:
```bash
python src/pipeline.py --polls 1200 --workers 3
```
Fast replay is the default. For a slower live-like demonstration:
```bash
python src/pipeline.py --polls 60 --workers 3 --speed 1
```

## 5. Launch dashboard
In a second terminal:
```bash
streamlit run src/dashboard.py
```
Open the local URL printed by Streamlit (normally http://localhost:8501).

## 6. Outputs
- `data/historical_stream.csv` — reproducible generated raw stream.
- `outputs/processed_events.csv` — cleaned and enriched events.
- `outputs/alerts.csv` — detected anomalies.
- `outputs/minute_summary.csv` — one-minute classroom aggregates.
- `outputs/metrics.json` — machine-learning metrics.
- `outputs/performance.json` — throughput and latency measurements.
- `outputs/smart_campus.db` — SQLite database.

## 7. Reproducibility
The generator uses a fixed random seed (42). The same configuration and seed reproduce the same synthetic input stream. Results are simulated and should not be interpreted as measurements from real campus sensors.

## 8. Distributed processing design
The incoming micro-batch is partitioned by `room_id`. Each partition is sent to a separate process through `ProcessPoolExecutor`. The workers independently clean and enrich the room data; the main process merges the outputs and persists them. This demonstrates partitioning and parallel workers on one machine. It is not a multi-node cluster.

## 9. Tests
```bash
pip install pytest
pytest -q
```

## 10. Limitations
- Sensor measurements are synthetic.
- Rule thresholds are illustrative and require calibration for real sensors.
- The demo uses local multiprocessing rather than a Kafka/Spark cluster.
- The dashboard reads persisted data and is refreshed manually.
- ML labels are derived from the next simulated reading's comfort rule; real deployment needs expert-labelled operational data.


## 11. Completed experiment snapshot
- Events: 5,400
- Polls: 900
- Throughput: 110.88 events/second
- Mean batch latency: 53.95 ms
- P95 batch latency: 71.45 ms
- ML accuracy: 98.96%; F1: 99.44%; ROC-AUC: 0.9955
- Anomaly detection against known synthetic fault labels: precision 100.00%, recall 100.00%
- Automated tests: 3 passed

These metrics are from the included 5,400-event synthetic run. They are not real campus sensor measurements.
