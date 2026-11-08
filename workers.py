from concurrent.futures import ProcessPoolExecutor
import pandas as pd
from processing import clean_batch, add_indicators

def _worker_process(payload):
    room_batch, history = payload
    combined = pd.concat([history, room_batch], ignore_index=True) if history is not None and len(history) else room_batch.copy()
    cleaned = clean_batch(combined)
    enriched = add_indicators(cleaned)
    keys = room_batch[["sensor_id", "timestamp"]].drop_duplicates().copy()
    keys["timestamp"] = pd.to_datetime(keys["timestamp"], utc=True, errors="coerce")
    return enriched.merge(keys, on=["sensor_id", "timestamp"], how="inner")

def process_parallel(batch, workers=3, history_by_room=None, executor=None):
    history_by_room = history_by_room or {}
    groups = []
    for room, group in batch.groupby("room_id"):
        history = history_by_room.get(room)
        groups.append((group.copy(), history.copy() if history is not None else None))
    if len(groups) <= 1 or workers <= 1:
        return _worker_process(groups[0]) if groups else pd.DataFrame()
    if executor is not None:
        results = list(executor.map(_worker_process, groups))
    else:
        with ProcessPoolExecutor(max_workers=min(workers, len(groups))) as pool:
            results = list(pool.map(_worker_process, groups))
    return pd.concat(results, ignore_index=True).sort_values(["timestamp", "room_id", "sensor_id"])
