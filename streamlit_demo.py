import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium

st.set_page_config(layout="wide")
st.title("EV Fleet Management – Live MVP Demo (Freetown)")

# -----------------------------
# INITIALIZE FLEET (RUN ONCE)
# -----------------------------
if "fleet" not in st.session_state:
    st.session_state.fleet = pd.DataFrame([
        {"id": "EV-01", "service": "Ride-Hailing", "battery": 72, "status": "Idle", "lat": 8.484, "lon": -13.234},
        {"id": "EV-02", "service": "Airport Shuttle", "battery": 38, "status": "Idle", "lat": 8.470, "lon": -13.210},
        {"id": "EV-03", "service": "School Transport", "battery": 55, "status": "Idle", "lat": 8.460, "lon": -13.250},
        {"id": "EV-04", "service": "Corporate Hire", "battery": 18, "status": "Idle", "lat": 8.490, "lon": -13.260},
    ])

fleet = st.session_state.fleet

# -----------------------------
# INITIALIZE CHARGING STATIONS
# -----------------------------
if "stations" not in st.session_state:
    st.session_state.stations = pd.DataFrame([
        {
            "id": "CS-01",
            "name": "Aberdeen Charging Hub",
            "lat": 8.495,
            "lon": -13.293,
            "capacity": 4
        },
        {
            "id": "CS-02",
            "name": "CBD Charging Point",
            "lat": 8.484,
            "lon": -13.231,
            "capacity": 3
        },
        {
            "id": "CS-03",
            "name": "Lumley Beach Station",
            "lat": 8.500,
            "lon": -13.280,
            "capacity": 2
        },
    ])

# -----------------------------
# SIDEBAR CONTROLS
# -----------------------------
st.sidebar.header("Fleet Controls")

service_filter = st.sidebar.selectbox(
    "Service Type",
    ["All"] + list(fleet["service"].unique())
)

min_battery = st.sidebar.slider("Minimum Battery (%)", 0, 100, 20)

# -----------------------------
# CHARGING CONTROL
# -----------------------------
st.sidebar.header("Charging Control")

selected_ev = st.sidebar.selectbox(
    "Select EV to Charge",
    fleet["id"]
)

if st.sidebar.button("Start Charging"):
    idx = fleet[fleet["id"] == selected_ev].index[0]
    fleet.loc[idx, "status"] = "Charging"

if st.sidebar.button("Simulate 10% Charge Increase"):
    idx = fleet[fleet["id"] == selected_ev].index[0]
    if fleet.loc[idx, "battery"] < 100:
        fleet.loc[idx, "battery"] += 10
        fleet.loc[idx, "status"] = "Charging"

if st.sidebar.button("Stop Charging"):
    idx = fleet[fleet["id"] == selected_ev].index[0]
    fleet.loc[idx, "status"] = "Idle"

# -----------------------------
# FILTER DATA
# -----------------------------
df = fleet.copy()

if service_filter != "All":
    df = df[df["service"] == service_filter]

df = df[df["battery"] >= min_battery]

# -----------------------------
# MAP VIEW
# -----------------------------
st.subheader("Live Fleet Map – Freetown")

m = folium.Map(location=[8.48, -13.23], zoom_start=12)

for _, ev in df.iterrows():
    if ev["status"] == "Charging":
        color = "blue"
    elif ev["battery"] > 40:
        color = "green"
    else:
        color = "red"

    folium.Marker(
        [ev["lat"], ev["lon"]],
        popup=f"""
        <b>{ev['id']}</b><br>
        Service: {ev['service']}<br>
        Status: {ev['status']}<br>
        Battery: {ev['battery']}%
        """,
        icon=folium.Icon(color=color, icon="bolt", prefix="fa"),
    ).add_to(m)

st_folium(m, width=1100, height=500)

# -----------------------------
# FLEET TABLE
# -----------------------------
st.subheader("Fleet Status Table")
st.dataframe(df, use_container_width=True)

# -----------------------------
# EXPLANATION
# -----------------------------
st.success("""
Live demo features:
• Stable fleet visualization (no blinking)
• Manual charging simulation
• Battery-based alerts
• Service-based filtering

This mirrors production EV fleet operations.
""")
