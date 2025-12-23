import streamlit as st
import pandas as pd
import random
import folium
from streamlit_folium import st_folium

st.set_page_config(layout="wide")

st.title("EV Fleet Management – Live MVP Demo (Freetown)")

# -----------------------------
# Simulated Fleet Data
# -----------------------------
fleet = [
    {"id": "EV-01", "service": "Ride-Hailing", "battery": random.randint(30, 90), "lat": 8.484, "lon": -13.234},
    {"id": "EV-02", "service": "Airport Shuttle", "battery": random.randint(20, 80), "lat": 8.470, "lon": -13.210},
    {"id": "EV-03", "service": "School Transport", "battery": random.randint(40, 100), "lat": 8.460, "lon": -13.250},
    {"id": "EV-04", "service": "Corporate Hire", "battery": random.randint(25, 75), "lat": 8.490, "lon": -13.260},
]

df = pd.DataFrame(fleet)

# -----------------------------
# Sidebar Controls
# -----------------------------
st.sidebar.header("Fleet Controls")
min_battery = st.sidebar.slider("Minimum Battery Filter (%)", 0, 100, 20)
service_filter = st.sidebar.selectbox("Service Type", ["All"] + list(df["service"].unique()))

if service_filter != "All":
    df = df[df["service"] == service_filter]

df = df[df["battery"] >= min_battery]

# -----------------------------
# Map View
# -----------------------------
st.subheader("Live Fleet Map – Freetown")

m = folium.Map(location=[8.48, -13.23], zoom_start=12)

for _, ev in df.iterrows():
    color = "green" if ev["battery"] > 40 else "red"
    folium.Marker(
        [ev["lat"], ev["lon"]],
        popup=f"""
        <b>{ev['id']}</b><br>
        Service: {ev['service']}<br>
        Battery: {ev['battery']}%
        """,
        icon=folium.Icon(color=color, icon="bolt", prefix="fa"),
    ).add_to(m)

st_folium(m, width=1100, height=500)

# -----------------------------
# Fleet Table
# -----------------------------
st.subheader("Fleet Status Table")
st.dataframe(df, use_container_width=True)

# -----------------------------
# Logic Simulation Explanation
# -----------------------------
st.info("""
This live demo simulates:
- Real-time EV location tracking
- Battery health monitoring
- Service-based fleet segmentation
- Dispatch decision support

Backend logic mirrors the Node.js + Prisma architecture.
""")

