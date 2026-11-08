import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
import pandas as pd
from generator import generate_stream
from processing import clean_batch, add_indicators

def test_generator_schema_and_count():
    df = generate_stream(polls=5)
    assert len(df) == 5 * 6
    assert {"timestamp","room_id","sensor_id","co2_ppm","temperature_c"}.issubset(df.columns)

def test_cleaning_removes_duplicate():
    df = generate_stream(polls=2)
    df = pd.concat([df, df.iloc[[0]]], ignore_index=True)
    out = clean_batch(df)
    assert not out.duplicated(["sensor_id","timestamp"]).any()

def test_anomaly_rules_flag_high_co2():
    df = generate_stream(polls=200)
    out = add_indicators(clean_batch(df))
    assert (out["is_anomaly"] == 1).any()
