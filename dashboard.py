import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import streamlit as st
import pandas as pd
import plotly.express as px
from storage import load_events
from config import DB_PATH

st.set_page_config(page_title="Smart Campus Analytics", layout="wide")
st.title("Smart Campus — Real-Time Classroom Analytics")
st.caption("Live-like IoT stream | six sensors | three classrooms | SQLite persistence")
if not DB_PATH.exists():
    st.warning("No database found. Run `python src/pipeline.py` first.")
    st.stop()
df = load_events(10000)
if df.empty:
    st.info("No events stored yet.")
    st.stop()
df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True)
latest = df.sort_values("timestamp").groupby("room_id").tail(2)
c1,c2,c3,c4 = st.columns(4)
c1.metric("Events stored", f"{len(df):,}")
c2.metric("Latest average CO₂", f"{df.co2_ppm.mean():.0f} ppm")
c3.metric("Detected alerts", f"{int(df.is_anomaly.sum()):,}")
c4.metric("Average occupancy", f"{df.occupancy.mean():.1f}")
left,right = st.columns(2)
with left:
    st.subheader("CO₂ over time")
    fig = px.line(df.sort_values("timestamp"), x="timestamp", y="co2_ppm", color="room_id",
                  title="CO₂ concentration by classroom")
    fig.add_hline(y=1000, line_dash="dash", annotation_text="Warning threshold")
    st.plotly_chart(fig, use_container_width=True)
with right:
    st.subheader("Occupancy and power")
    agg = df.groupby("room_id", as_index=False).agg(occupancy=("occupancy","mean"), power=("power_kw","mean"))
    fig2 = px.scatter(agg, x="occupancy", y="power", color="room_id", size="occupancy",
                      title="Average occupancy vs. power consumption")
    st.plotly_chart(fig2, use_container_width=True)
st.subheader("Latest sensor readings")
st.dataframe(df.sort_values("timestamp", ascending=False).head(20), use_container_width=True)
st.subheader("Anomaly log")
st.dataframe(df[df.is_anomaly == 1].sort_values("timestamp", ascending=False).head(50),
             use_container_width=True)
st.caption("Refresh the page after a new pipeline run to view updated records.")
