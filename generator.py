import numpy as np
import pandas as pd
from datetime import datetime, timedelta, timezone
from config import ROOMS, SENSORS_PER_ROOM, RANDOM_SEED, POLL_INTERVAL_SECONDS

def generate_stream(polls=1200, seed=RANDOM_SEED, inject_faults=True):
    """Generate timestamped classroom IoT events; one poll contains six sensor events."""
    rng = np.random.default_rng(seed)
    start = datetime(2026, 10, 1, 8, 0, 0, tzinfo=timezone.utc)
    rows = []
    sensor_index = 0
    room_state = {room: {"co2": rng.uniform(480, 620), "temp": rng.uniform(21, 23)} for room in ROOMS}
    for poll in range(polls):
        ts = start + timedelta(seconds=poll * POLL_INTERVAL_SECONDS)
        for room in ROOMS:
            room_num = ROOMS.index(room)
            occupancy = int(np.clip(8 + 4 * np.sin(poll / 35 + room_num) + rng.normal(0, 2), 0, 35))
            for local_sensor in range(SENSORS_PER_ROOM):
                sensor_id = f"S{room_num+1}{local_sensor+1}"
                state = room_state[room]
                # CO2 gradually responds to occupancy and ventilation.
                state["co2"] += 0.18 * (600 + occupancy * 7 - state["co2"]) + rng.normal(0, 5)
                state["co2"] = float(np.clip(state["co2"], 420, 1250))
                temp = state["temp"] + 0.003 * occupancy + rng.normal(0, 0.12)
                state["temp"] = float(np.clip(temp, 19, 27))
                humidity = float(np.clip(42 + 0.25 * occupancy + rng.normal(0, 3), 25, 75))
                power = float(max(0.3, 0.35 + occupancy * 0.12 + rng.normal(0, 0.12)))
                # Inject labelled anomalies into a small, known subset of records.
                injected = False
                if inject_faults and poll in (180, 181, 182) and room == "Lecture-101" and local_sensor == 0:
                    state["co2"] = 1750 + rng.normal(0, 15)
                    injected = True
                if inject_faults and poll == 420 and room == "Lecture-202" and local_sensor == 1:
                    temp = 31.5
                    injected = True
                if inject_faults and poll == 720 and room == "Lab-303" and local_sensor == 0:
                    power = 4.8
                    injected = True
                if inject_faults and room == "Lecture-101" and poll in (180, 181, 182, 183) and state["co2"] >= 1000:
                    injected = True
                rows.append({
                    "timestamp": ts.isoformat(), "poll_id": poll, "room_id": room,
                    "sensor_id": sensor_id, "temperature_c": round(float(temp), 2),
                    "humidity_pct": round(humidity, 2), "co2_ppm": round(float(state["co2"]), 1),
                    "occupancy": occupancy, "power_kw": round(power, 3),
                    "injected_anomaly": int(injected)
                })
                sensor_index += 1
    return pd.DataFrame(rows)

if __name__ == "__main__":
    from config import RAW_CSV
    df = generate_stream()
    RAW_CSV.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(RAW_CSV, index=False)
    print(f"Generated {len(df):,} events -> {RAW_CSV}")
