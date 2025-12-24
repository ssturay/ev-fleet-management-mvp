import streamlit as st
import pandas as pd
import folium
import math
from streamlit_folium import st_folium

# --------------------------------------------------
# CONFIG
# --------------------------------------------------
st.set_page_config(layout="wide")
st.title("EV Fleet Management Platform – Live Operations Demo (Freetown)")

ENERGY_COST_PER_KWH = 0.25
BATTERY_CAPACITY_KWH = 60

# --------------------------------------------------
# HELPERS
# --------------------------------------------------
def distance(lat1, lon1, lat2, lon2):
    return math.sqrt((lat1-lat2)**2 + (lon1-lon2)**2)

def move_towards(lat, lon, tlat, tlon, step=0.001):
    if abs(lat-tlat) < step and abs(lon-tlon) < step:
        return tlat, tlon
    lat += step if lat < tlat else -step
    lon += step if lon < tlon else -step
    return lat, lon

# --------------------------------------------------
# INITIALIZE STATE
# --------------------------------------------------
if "fleet" not in st.session_state:
    st.session_state.fleet = pd.DataFrame([
        {"id":"EV-01","service":"Ride-Hailing","battery":72,"status":"Idle","lat":8.484,"lon":-13.234,"station":None},
        {"id":"EV-02","service":"Airport Shuttle","battery":38,"status":"Idle","lat":8.470,"lon":-13.210,"station":None},
        {"id":"EV-03","service":"School Transport","battery":55,"status":"Idle","lat":8.460,"lon":-13.250,"station":None},
        {"id":"EV-04","service":"Corporate Hire","battery":18,"status":"Idle","lat":8.490,"lon":-13.260,"station":None},
        {"id":"EV-05","service":"Daily Rentals","battery":80,"status":"Active","lat":8.475,"lon":-13.245,"station":None},
        {"id":"EV-06","service":"Tourism Shuttle","battery":65,"status":"Active","lat":8.505,"lon":-13.275,"station":None},
    ])

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
# SIDEBAR – SIMULATION ENGINE
# --------------------------------------------------
st.sidebar.header("Simulation Engine")

if st.sidebar.button("Simulate 1 Minute of Operations"):
    for i, ev in fleet.iterrows():

        # SERVICE-BASED BATTERY DRAIN
        if ev["status"] == "Active":
            if ev["service"] in ["Daily Rentals", "Tourism Shuttle"]:
                fleet.loc[i, "battery"] -= 1.5
            elif ev["service"] == "Ride-Hailing":
                fleet.loc[i, "battery"] -= 1
            elif ev["service"] == "Airport Shuttle":
                fleet.loc[i, "battery"] -= 0.8

        # AUTO SEND TO CHARGING
        if fleet.loc[i, "battery"] < 20 and ev["status"] != "Charging":
            nearest = min(
                stations.itertuples(),
                key=lambda s: distance(ev.lat, ev.lon, s.lat, s.lon)
            )
            fleet.loc[i, "station"] = nearest.id
            fleet.loc[i, "status"] = "Moving to Charge"

        # MOVE TO CHARGER
        if ev["status"] == "Moving to Charge":
            stn = stations[stations["id"] == ev["station"]].iloc[0]
            lat, lon = move_towards(ev.lat, ev.lon, stn.lat, stn.lon)
            fleet.loc[i, ["lat","lon"]] = lat, lon
            if lat == stn.lat and lon == stn.lon:
                fleet.loc[i, "status"] = "Charging"

        # CHARGING
        if ev["status"] == "Charging":
            fleet.loc[i, "battery"] += 2
            st.session_state.energy_log.append((2/100)*BATTERY_CAPACITY_KWH)
            if fleet.loc[i, "battery"] >= 100:
                fleet.loc[i, "battery"] = 100
                fleet.loc[i, "status"] = "Idle"
                fleet.loc[i, "station"] = None

# --------------------------------------------------
# TABS (THIS IS THE BIG DIFFERENCE)
# --------------------------------------------------
tab1, tab2, tab3 = st.tabs(["🚗 Operations Map", "🔌 Charging Overview", "📊 Analytics"])

# ---------------- MAP TAB ----------------
with tab1:
    m = folium.Map(location=[8.48, -13.23], zoom_start=12)

    for s in stations.itertuples():
        folium.Marker(
            [s.lat, s.lon],
            popup=s.name,
            icon=folium.Icon(color="purple", icon="flash", prefix="fa")
        ).add_to(m)

    for ev in fleet.itertuples():
        color = "green"
        if ev.status == "Charging": color = "blue"
        if ev.status == "Moving to Charge": color = "orange"
        if ev.battery < 20: color = "red"

        folium.Marker(
            [ev.lat, ev.lon],
            popup=f"{ev.id}<br>{ev.service}<br>{ev.status}<br>{ev.battery:.0f}%",
            icon=folium.Icon(color=color, icon="bolt", prefix="fa")
        ).add_to(m)

    st_folium(m, width=1100, height=500)

# ---------------- CHARGING TAB ----------------
with tab2:
    st.subheader("Fleet & Charging Status")
    st.dataframe(fleet, use_container_width=True)
    st.dataframe(stations, use_container_width=True)

# ---------------- ANALYTICS TAB ----------------
with tab3:
    total_energy = sum(st.session_state.energy_log)
    total_cost = total_energy * ENERGY_COST_PER_KWH

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Fleet Size", len(fleet))
    c2.metric("Active EVs", len(fleet[fleet.status=="Active"]))
    c3.metric("Charging EVs", len(fleet[fleet.status=="Charging"]))
    c4.metric("Energy Cost ($)", f"{total_cost:.2f}")

    st.success("This dashboard demonstrates operational, energy, and service-level control of EV fleets.")
