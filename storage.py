import sqlite3
import pandas as pd
from config import DB_PATH

def init_db(path=DB_PATH, reset=False):
    path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(path) as con:
        con.execute("""CREATE TABLE IF NOT EXISTS events (
            timestamp TEXT, poll_id INTEGER, room_id TEXT, sensor_id TEXT,
            temperature_c REAL, humidity_pct REAL, co2_ppm REAL, occupancy REAL,
            power_kw REAL, quality_flag TEXT, is_anomaly INTEGER, anomaly_reason TEXT,
            comfort_flag INTEGER, PRIMARY KEY(sensor_id, timestamp))""")
        con.execute("""CREATE TABLE IF NOT EXISTS minute_summary (
            minute TEXT, room_id TEXT, events INTEGER, avg_co2 REAL,
            avg_temperature REAL, avg_occupancy REAL, total_power_kw REAL,
            anomaly_count INTEGER, PRIMARY KEY(minute, room_id))""")
        if reset:
            con.execute("DELETE FROM events")
            con.execute("DELETE FROM minute_summary")

def save_events(df, path=DB_PATH):
    cols = ["timestamp","poll_id","room_id","sensor_id","temperature_c","humidity_pct",
            "co2_ppm","occupancy","power_kw","quality_flag","is_anomaly","anomaly_reason","comfort_flag"]
    rows = []
    for row in df[cols].itertuples(index=False, name=None):
        rows.append(tuple(str(v) if i == 0 else v for i, v in enumerate(row)))
    sql = "INSERT OR REPLACE INTO events (" + ",".join(cols) + ") VALUES (" + ",".join(["?"]*len(cols)) + ")"
    with sqlite3.connect(path) as con:
        con.executemany(sql, rows)

def save_summary(df, path=DB_PATH):
    if df.empty: return
    with sqlite3.connect(path) as con:
        df.assign(minute=lambda x: x.minute.astype(str)).to_sql(
            "minute_summary", con, if_exists="replace", index=False
        )

def load_events(limit=5000, path=DB_PATH):
    with sqlite3.connect(path) as con:
        return pd.read_sql_query(f"SELECT * FROM events ORDER BY timestamp DESC LIMIT {int(limit)}", con)
