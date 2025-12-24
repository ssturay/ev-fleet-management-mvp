import streamlit as st
import pandas as pd
import folium
import math
from streamlit_folium import st_folium

# --------------------------------------------------
# CONFIG
# --------------------------------------------------
st.set_page_config(layout="wide")
st.title("NeeV Salone EV Fleet Management Platform – Live Business Operations")

ENERGY_COST_PER_KWH = 0.25
BATTERY_CAPACITY_KWH = 60

SERVICE_RATES = {
    "Ride-Hailing": 2.5,        # $ per minute
    "Airport Shuttle": 3.0,
    "School Transport": 1.5,
    "Corporate Hire": 2.0,
    "Daily Rentals": 40.0,      # $ per day (simulated per minute)
    "Tourism Shuttle": 3.5
}

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
        {"id":"EV-01","service":"Ride-Hailing","battery":72,"status":"Idle","lat":8.484,"lon":-13.234,"station":None,"driver":None,"revenue":0},
        {"id":"EV-02","service":"Airport Shuttle","battery":38,"status":"Idle","lat":8.470,"lon":-13.210,"station":None,"driver":None,"revenue":0},
        {"id":"EV-03","service":"School Transport","battery":55,"status":"Active","lat":8.460,"lon":-13.250,"station":None,"driver":"DRV-03","revenue":0},
        {"id":"EV-04","service":"Corporate Hire","battery":18,"status":"Idle","lat":8.490,"lon":-13.260,"station":None,"driver":None,"revenue":0},
        {"id":"EV-05","service":"Daily Rentals","battery":80,"status":"Active","lat":8.475,"lon":-13.245,"station":None,"driver":"DRV-05","revenue":0},
        {"id":"EV-06","service":"Tourism Shuttle","battery":65,"status":"Active","lat":8.505,"lon":-13.275,"station":None,"driver":"DRV-06","revenue":0},
    ])

if "drivers" not in st.session_state:
    st.session_state.drivers = pd.DataFrame([
        {"id":"DRV-01","name":"Driver A","status":"Available"},
        {"id":"DRV-02","name":"Driver B","status":"Available"},
        {"id":"DRV-03","name":"Driver C","status":"Assigned"},
        {"id":"DRV-04","name":"Driver D","status":"Available"},
        {"id":"DRV-05","name":"Driver E","status":"Assigned"},
        {"id":"DRV-06","name":"Driver F","status":"Assigned"},
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
drivers = st.session_state.drivers
stations = st.session_state.stations

# --------------------------------------------------
# SIDEBAR – CONTROL PANEL
# --------------------------------------------------
st.sidebar.header("Simulation Engine")

selected_ev = st.sidebar.selectbox("Select EV", fleet["id"])

available_drivers = drivers[drivers.status=="Available"]["id"].tolist()

if available_drivers:
    selected_driver = st.sidebar.selectbox("Assign Driver", available_drivers)
else:
    selected_driver = None
    st.sidebar.info("No drivers available")

if st.sidebar.button("Assign Driver to EV") and selected_driver:
    ev_idx = fleet[fleet.id == selected_ev].index[0]
    drv_idx = drivers[drivers.id == selected_driver].index[0]
    fleet.loc[ev_idx, "driver"] = selected_driver
    fleet.loc[ev_idx, "status"] = "Active"
    drivers.loc[drv_idx, "status"] = "Assigned"

if st.sidebar.button("Simulate 1 Minute of Operations"):
    for i, ev in fleet.iterrows():

        # ACTIVE VEHICLE OPERATIONS
        if ev.status == "Active":
            drain = 1
            if ev.service in ["Daily Rentals", "Tourism Shuttle"]:
                drain = 1.5
            fleet.loc[i, "battery"] -= drain

            # Revenue logic
            rate = SERVICE_RATES[ev.service]
            if ev.service == "Daily Rentals":
                fleet.loc[i, "revenue"] += rate / (24*60)
            else:
                fleet.loc[i, "revenue"] += rate

        # AUTO SEND TO CHARGING
        if fleet.loc[i, "battery"] < 20 and ev.status != "Charging":
            nearest = min(
                stations.itertuples(),
                key=lambda s: distance(ev.lat, ev.lon, s.lat, s.lon)
            )
            fleet.loc[i, "station"] = nearest.id
            fleet.loc[i, "status"] = "Moving to Charge"

        # MOVE TO CHARGER
        if ev.status == "Moving to Charge":
            stn = stations[stations.id == ev.station].iloc[0]
            lat, lon = move_towards(ev.lat, ev.lon, stn.lat, stn.lon)
            fleet.loc[i, ["lat","lon"]] = lat, lon
            if lat == stn.lat and lon == stn.lon:
                fleet.loc[i, "status"] = "Charging"

        # CHARGING
        if ev.status == "Charging":
            fleet.loc[i, "battery"] += 2
            st.session_state.energy_log.append((2/100)*BATTERY_CAPACITY_KWH)
            if fleet.loc[i, "battery"] >= 100:
                fleet.loc[i, "battery"] = 100
                fleet.loc[i, "status"] = "Idle"
                fleet.loc[i, "station"] = None

# --------------------------------------------------
# TABS
# --------------------------------------------------
tab1, tab2, tab3 = st.tabs(["🚗 Live Operations", "🔌 Charging & Drivers", "💰 Analytics"])

# ---------------- MAP ----------------
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
            popup=f"""
            <b>{ev.id}</b><br>
            {ev.service}<br>
            Status: {ev.status}<br>
            Battery: {ev.battery:.0f}%<br>
            Driver: {ev.driver}<br>
            Revenue: ${ev.revenue:.2f}
            """,
            icon=folium.Icon(color=color, icon="bolt", prefix="fa")
        ).add_to(m)

    st_folium(m, width=1100, height=500)

# ---------------- CHARGING & DRIVERS ----------------
with tab2:
    st.subheader("Fleet")
    st.dataframe(fleet, use_container_width=True)

    st.subheader("Drivers")
    st.dataframe(drivers, use_container_width=True)

    st.subheader("Charging Stations")
    st.dataframe(stations, use_container_width=True)

# ---------------- ANALYTICS ----------------
with tab3:
    total_energy = sum(st.session_state.energy_log)
    total_cost = total_energy * ENERGY_COST_PER_KWH
    total_revenue = fleet.revenue.sum()

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Fleet Size", len(fleet))
    c2.metric("Active EVs", len(fleet[fleet.status=="Active"]))
    c3.metric("Charging EVs", len(fleet[fleet.status=="Charging"]))
    c4.metric("Total Revenue ($)", f"{total_revenue:.2f}")

    st.metric("Energy Cost ($)", f"{total_cost:.2f}")
    st.metric("Net Operating Margin ($)", f"{total_revenue-total_cost:.2f}")

    st.success(
        "This MVP demonstrates full EV fleet operations: dispatch, drivers, charging, and revenue."
    )
