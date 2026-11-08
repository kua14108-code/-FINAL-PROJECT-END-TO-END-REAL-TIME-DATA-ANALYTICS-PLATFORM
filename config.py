from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
OUTPUT_DIR = ROOT / "outputs"
DB_PATH = OUTPUT_DIR / "smart_campus.db"
RAW_CSV = DATA_DIR / "historical_stream.csv"
METRICS_JSON = OUTPUT_DIR / "metrics.json"

RANDOM_SEED = 42
ROOMS = ["Lecture-101", "Lecture-202", "Lab-303"]
SENSORS_PER_ROOM = 2
POLL_INTERVAL_SECONDS = 10
ROLLING_WINDOW = 30  # 30 readings x 10 seconds = 5 minutes
CO2_WARNING = 1000
CO2_CRITICAL = 1500
TEMP_MIN, TEMP_MAX = 18.0, 28.0
HUMIDITY_MIN, HUMIDITY_MAX = 0.0, 100.0
