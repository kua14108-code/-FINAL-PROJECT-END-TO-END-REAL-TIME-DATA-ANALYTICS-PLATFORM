import numpy as np
import pandas as pd
from config import CO2_WARNING, CO2_CRITICAL, TEMP_MIN, TEMP_MAX, HUMIDITY_MIN, HUMIDITY_MAX

NUMERIC_RANGES = {
    "temperature_c": (-10, 50), "humidity_pct": (HUMIDITY_MIN, HUMIDITY_MAX),
    "co2_ppm": (300, 5000), "occupancy": (0, 1000), "power_kw": (0, 100)
}

def clean_batch(batch):
    df = batch.copy()
    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce", utc=True)
    df = df.dropna(subset=["timestamp", "sensor_id", "room_id"])
    for col, (lo, hi) in NUMERIC_RANGES.items():
        df[col] = pd.to_numeric(df[col], errors="coerce")
        df.loc[~df[col].between(lo, hi), col] = np.nan
    df = df.drop_duplicates(subset=["sensor_id", "timestamp"])
    for col in NUMERIC_RANGES:
        df[col] = df.groupby("sensor_id")[col].transform(lambda s: s.ffill(limit=2))
    df["quality_flag"] = np.where(df[list(NUMERIC_RANGES)].isna().any(axis=1), "incomplete", "ok")
    return df

def add_indicators(df, history=None):
    """Calculate rolling indicators per sensor; historical rows are used only for context."""
    current = df.copy()
    combined = pd.concat([history, current], ignore_index=True) if history is not None and len(history) else current.copy()
    combined = combined.sort_values(["sensor_id", "timestamp"])
    for col in ["temperature_c", "humidity_pct", "co2_ppm", "power_kw"]:
        grp = combined.groupby("sensor_id")[col]
        combined[f"{col}_ma"] = grp.transform(lambda s: s.rolling(30, min_periods=3).mean())
        combined[f"{col}_std"] = grp.transform(lambda s: s.rolling(30, min_periods=3).std())
        prev_mean = grp.transform(lambda s: s.shift(1).rolling(30, min_periods=3).mean())
        prev_std = grp.transform(lambda s: s.shift(1).rolling(30, min_periods=3).std()).clip(lower=1.0)
        combined[f"{col}_z"] = (combined[col] - prev_mean) / prev_std
    combined["co2_rate_per_min"] = combined.groupby("sensor_id")["co2_ppm"].transform(
        lambda s: s.diff(3) / 0.5
    )
    combined["comfort_flag"] = (
        (combined["co2_ppm"] <= CO2_WARNING) &
        combined["temperature_c"].between(20, 24)
    ).astype(int)
    combined["anomaly_reason"] = ""
    combined.loc[combined["co2_ppm"] >= CO2_CRITICAL, "anomaly_reason"] += "CO2_CRITICAL;"
    combined.loc[combined["co2_ppm"].between(CO2_WARNING, CO2_CRITICAL, inclusive="left"), "anomaly_reason"] += "CO2_HIGH;"
    combined.loc[~combined["temperature_c"].between(TEMP_MIN, TEMP_MAX), "anomaly_reason"] += "TEMP_OUT_OF_RANGE;"
    combined.loc[combined["power_kw"] > 3.0, "anomaly_reason"] += "POWER_SPIKE;"
    combined["is_anomaly"] = (combined["anomaly_reason"] != "").astype(int)
    current_keys = current[["sensor_id", "timestamp"]].drop_duplicates()
    return combined.merge(current_keys, on=["sensor_id", "timestamp"], how="inner")

def aggregate_minute(df):
    if df.empty:
        return pd.DataFrame()
    x = df.copy()
    x["minute"] = x["timestamp"].dt.floor("min")
    return x.groupby(["minute", "room_id"], as_index=False).agg(
        events=("sensor_id", "count"), avg_co2=("co2_ppm", "mean"),
        avg_temperature=("temperature_c", "mean"), avg_occupancy=("occupancy", "mean"),
        total_power_kw=("power_kw", "sum"), anomaly_count=("is_anomaly", "sum")
    )
