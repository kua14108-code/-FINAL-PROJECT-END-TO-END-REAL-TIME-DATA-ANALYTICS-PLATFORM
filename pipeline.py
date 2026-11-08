import time
from concurrent.futures import ProcessPoolExecutor
import pandas as pd
from generator import generate_stream
from processing import clean_batch, add_indicators, aggregate_minute
from workers import process_parallel
from storage import init_db, save_events, save_summary
from ml_model import train_and_evaluate
from config import RAW_CSV, OUTPUT_DIR, POLL_INTERVAL_SECONDS

def run_pipeline(polls=1200, workers=3, speed=0.0, use_parallel=True):
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    init_db(reset=True)
    history_by_room = {}
    stream = generate_stream(polls=polls)
    stream.to_csv(RAW_CSV, index=False)
    all_processed, latencies = [], []
    executor = ProcessPoolExecutor(max_workers=workers) if use_parallel else None
    start = time.perf_counter()
    for poll_id, batch in stream.groupby("poll_id", sort=True):
        tick = time.perf_counter()
        processed = process_parallel(batch, workers, history_by_room, executor=executor) if use_parallel else add_indicators(clean_batch(batch))
        # Keep the last 30 raw observations per sensor and room for rolling features.
        for room, room_batch in batch.groupby("room_id"):
            previous = history_by_room.get(room)
            updated = pd.concat([previous, room_batch], ignore_index=True) if previous is not None else room_batch.copy()
            history_by_room[room] = updated.sort_values("timestamp").groupby("sensor_id").tail(30).reset_index(drop=True)
        save_events(processed)
        all_processed.append(processed)
        latencies.append((time.perf_counter() - tick) * 1000)
        if speed > 0:
            time.sleep(speed)
    if executor is not None:
        executor.shutdown(wait=True)
    result = pd.concat(all_processed, ignore_index=True)
    summary = aggregate_minute(result)
    save_summary(summary)
    elapsed = time.perf_counter() - start
    throughput = len(result) / elapsed if elapsed else 0
    perf = {
        "events_processed": int(len(result)), "polls": int(polls), "workers": int(workers if use_parallel else 1),
        "processing_mode": "room-partitioned multiprocessing" if use_parallel else "single process",
        "elapsed_seconds": round(elapsed, 3), "throughput_events_per_second": round(throughput, 2),
        "mean_batch_latency_ms": round(sum(latencies)/len(latencies), 3),
        "p95_batch_latency_ms": round(float(pd.Series(latencies).quantile(.95)), 3),
        "max_batch_latency_ms": round(max(latencies), 3),
        "poll_interval_seconds": POLL_INTERVAL_SECONDS
    }
    (OUTPUT_DIR/"performance.json").write_text(__import__("json").dumps(perf, indent=2))
    model, ml_metrics = train_and_evaluate(result)
    result.to_csv(OUTPUT_DIR/"processed_events.csv", index=False)
    summary.to_csv(OUTPUT_DIR/"minute_summary.csv", index=False)
    result[result.is_anomaly == 1].to_csv(OUTPUT_DIR/"alerts.csv", index=False)
    return result, summary, perf, ml_metrics

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--polls", type=int, default=1200)
    parser.add_argument("--workers", type=int, default=3)
    parser.add_argument("--speed", type=float, default=0.0, help="seconds to wait between polls; use 0 for fast replay")
    parser.add_argument("--single-process", action="store_true")
    args = parser.parse_args()
    result, summary, perf, metrics = run_pipeline(args.polls, args.workers, args.speed, not args.single_process)
    print("PIPELINE COMPLETE")
    print(perf)
    print(metrics)
