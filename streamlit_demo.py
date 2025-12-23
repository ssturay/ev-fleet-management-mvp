import streamlit as st
import pandas as pd
import folium
import math
import time
from streamlit_folium import st_folium

# --------------------------------------------------
# CONFIG
# --------------------------------------------------
st.set_page_config(layout="wide")
st.title("EV Fleet Management – Live MVP Demo (Freetown)")

ENERGY_COST_PER_KWH = 0.25   # USD (demo assumption)
BATTERY_CAPACITY_KWH = 60   # typical EV battery

# --------------------------------------------------
# HELPER FUNCTIONS
# --------------------------------------------------
def distance(lat1, lon1, lat2, lon2):
    return math.sqrt((lat1-lat2)**2 + (lon1-lon2)**2)

def move_towards(lat, lon, target_lat, target_lon, step=0.001):
    if abs(lat - target_lat) < step and abs(lon - target_lon) < step:
        return target_lat, target_lon
    lat += step if lat < target_lat else -step
    lon += step if lon < target_lon else -step
    return lat, lon

# --------------------------------------------------
# INITIALIZE FLEET
# --------------------------------------------------
if "fleet" not in st.session_state:
    st.session_state.fleet = pd.DataFrame([
        {"id":"EV-01","service":"Ride-Hailing","battery":72,"status":"Idle","lat":8.484,"lon":-13.234,"station":None},
        {"id":"EV-02","service":"Airport Shuttle","battery":38,"status":"Idle","lat":8.470,"lon":-13.210,"station":None},
        {"id":"EV-03","service":"School Transport","battery":55,"status":"Idle","lat":8.460,"lon":-13.250,"station":None},
        {"id":"EV-04","service":"Corporate Hire","battery":18,"status":"Idle","lat":8.490,"lon":-13.260,"station":None},
    ])

# --------------------------------------------------
# INITIALIZE CHARGING STATIONS
# --------------------------------------------------
if "stations" not in st.session_state:
    st.session_state.stations = pd.DataFrame([
        {"id":"CS-01","name":"Aberdeen Hub","lat":8.495,"lon":-13.293,"capacity":4},
        {"id":"CS-02","name":"CBD Station","lat":8.484,"lon":-13.231,"capacity":3},
        {"id":"CS-03","name":"Lumley Beach","lat":8.500,"lon":-13.280,"capacity":2},
    ])

if "energy_log" not in st.session_state:
    st.session_state.energy_log = []

fleet = st.session_state.fleet
stations = st.session_state.stations

# --------------------------------------------------
# SIDEBAR CONTROLS
# --------------------------------------------------
st.sidebar.header("Fleet Operations")

selected_ev = st.sidebar.selectbox("Select EV", fleet["id"])

if st.sidebar.button("Auto-Assign Nearest Charging Station"):
    ev = fleet[fleet["id"] == selected_ev].iloc[0]

    nearest = min(
        stations.itertuples(),
        key=lambda s: distance(ev.lat, ev.lon, s.lat, s.lon)
    )

    idx = fleet[fleet["id"] == selected_ev].index[0]
    fleet.loc[idx, "station"] = nearest.id
    fleet.loc[idx, "status"] = "Moving to Charge"

if st.sidebar.button("Simulate 1 Minute"):
    for idx, ev in fleet.iterrows():

        # VEHICLE MOVEMENT
        if ev["status"] == "Moving to Charge":
            station = stations[stations["id"] == ev["station"]].iloc[0]
            new_lat, new_lon = move_towards(ev["lat"], ev["lon"], station.lat, station.lon)
            fleet.loc[idx, "lat"] = new_lat
            fleet.loc[idx, "lon"] = new_lon

            if new_lat == station.lat and new_lon == station.lon:
                fleet.loc[idx, "status"] = "Charging"

        # CHARGING LOGIC
        if ev["status"] == "Charging" and ev["battery"] < 100:
            fleet.loc[idx, "battery"] += 2  # 2% per minute
            energy_added = (2/100) * BATTERY_CAPACITY_KWH
            st.session_state.energy_log.append(energy_added)

            if fleet.loc[idx, "battery"] >= 100:
                fleet.loc[idx, "battery"] = 100
                fleet.loc[idx, "status"] = "Ready"
                fleet.loc[idx, "station"] = None

# --------------------------------------------------
# MAP
# --------------------------------------------------
st.subheader("Live Fleet & Charging Map – Freetown")
m = folium.Map(location=[8.48, -13.23], zoom_start=12)

# Stations
for s in stations.itertuples():
    folium.Marker(
        [s.lat, s.lon],
        popup=f"{s.name} (Capacity: {s.capacity})",
        icon=folium.Icon(color="purple", icon="flash", prefix="fa")
    ).add_to(m)

# Vehicles
for ev in fleet.itertuples():
    if ev.status == "Charging":
        color = "blue"
    elif ev.battery < 25:
        color = "red"
    elif ev.status == "Moving to Charge":
        color = "orange"
    else:
        color = "green"

    folium.Marker(
        [ev.lat, ev.lon],
        popup=f"""
        <b>{ev.id}</b><br>
        Service: {ev.service}<br>
        Status: {ev.status}<br>
        Battery: {ev.battery}%<br>
        Station: {ev.station}
        """,
        icon=folium.Icon(color=color, icon="bolt", prefix="fa")
    ).add_to(m)

st_folium(m, width=1100, height=500)

# --------------------------------------------------
# TABLES
# --------------------------------------------------
st.subheader("Fleet Status")
st.dataframe(fleet, use_container_width=True)

st.subheader("Charging Stations")
st.dataframe(stations, use_container_width=True)

# --------------------------------------------------
# ENERGY & COST DASHBOARD
# --------------------------------------------------
st.subheader("Energy & Charging Cost Dashboard")

total_energy = sum(st.session_state.energy_log)
total_cost = total_energy * ENERGY_COST_PER_KWH

col1, col2, col3 = st.columns(3)
col1.metric("Total Energy Delivered (kWh)", f"{total_energy:.2f}")
col2.metric("Energy Cost ($)", f"${total_cost:.2f}")
col3.metric("Avg Cost per EV ($)", f"${total_cost/len(fleet):.2f}")

st.info("""
This live demo shows:
• Automatic nearest-station assignment  
• Vehicle movement to chargers  
• Time-based charging simulation  
• Energy consumption & cost tracking  

This mirrors production EV fleet operations.
""")
