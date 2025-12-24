import streamlit as st
import pandas as pd
import folium
import math
import random
from streamlit_folium import st_folium

# --------------------------------------------------
# CONFIG
# --------------------------------------------------
st.set_page_config(layout="wide")
st.title("NeeV Salone EV Fleet Management Platform – Live Business Operations")

ENERGY_COST_PER_KWH = 0.25
BATTERY_CAPACITY_KWH = 60

SERVICE_RATES = {
    "Ride-Hailing": 2.5,
    "Airport Shuttle": 3.0,
    "School Transport": 1.5,
    "Corporate Hire": 2.0,
    "Daily Rentals": 40.0,
    "Tourism Shuttle": 3.5
}

SERVICE_FLEET_SIZE = {
    "Ride-Hailing": 9,
    "Airport Shuttle": 9,
    "School Transport": 5,
    "Corporate Hire": 9,
    "Daily Rentals": 9,
    "Tourism Shuttle": 9
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
# RESET
# --------------------------------------------------
st.sidebar.header("System Controls")
if st.sidebar.button("🔄 Reset Fleet"):
    for k in ["fleet","drivers","stations","energy_log"]:
        st.session_state.pop(k, None)
    st.rerun()

# --------------------------------------------------
# INITIALIZE STATE
# --------------------------------------------------
if "fleet" not in st.session_state:
    fleet_data = []
    ev_id = 1
    for service, count in SERVICE_FLEET_SIZE.items():
        for _ in range(count):
            fleet_data.append({
                "id": f"EV-{ev_id:02d}",
                "service": service,
                "battery": random.randint(45, 90),
                "status": "Idle",
                "lat": 8.48 + random.uniform(-0.04, 0.04),
                "lon": -13.25 + random.uniform(-0.04, 0.04),
                "station": None,
                "driver": None,
                "revenue": 0.0
            })
            ev_id += 1
    st.session_state.fleet = pd.DataFrame(fleet_data)

if "drivers" not in st.session_state:
    st.session_state.drivers = pd.DataFrame([
        {"id": f"DRV-{i:02d}", "name": f"Driver {i}", "status": "Available"}
        for i in range(1, 61)
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
# SIDEBAR – SIMULATION
# --------------------------------------------------
st.sidebar.header("Simulation Engine")
selected_ev = st.sidebar.selectbox("Select EV", fleet["id"])
available_drivers = drivers[drivers.status=="Available"]["id"].tolist()
selected_driver = st.sidebar.selectbox("Assign Driver", available_drivers if available_drivers else ["None"])

if st.sidebar.button("Assign Driver") and selected_driver != "None":
    ev_idx = fleet[fleet.id == selected_ev].index[0]
    drv_idx = drivers[drivers.id == selected_driver].index[0]
    fleet.loc[ev_idx, ["driver","status"]] = [selected_driver, "Active"]
    drivers.loc[drv_idx, "status"] = "Assigned"

# --------------------------------------------------
# SIMULATION STEP
# --------------------------------------------------
if st.sidebar.button("▶ Simulate 1 Minute"):
    for i, ev in fleet.iterrows():

        if ev.status == "Active":
            drain = 1.5 if ev.service in ["Daily Rentals","Tourism Shuttle"] else 1
            fleet.loc[i, "battery"] -= drain

            rate = SERVICE_RATES[ev.service]
            fleet.loc[i, "revenue"] += rate / (24*60) if ev.service=="Daily Rentals" else rate

        if fleet.loc[i,"battery"] < 20 and ev.status not in ["Charging","Moving to Charge"]:
            nearest = min(stations.itertuples(), key=lambda s: distance(ev.lat, ev.lon, s.lat, s.lon))
            fleet.loc[i, ["station","status"]] = [nearest.id, "Moving to Charge"]

        if ev.status == "Moving to Charge":
            stn = stations[stations.id == ev.station].iloc[0]
            lat, lon = move_towards(ev.lat, ev.lon, stn.lat, stn.lon)
            fleet.loc[i, ["lat","lon"]] = lat, lon
            if lat == stn.lat and lon == stn.lon:
                fleet.loc[i, "status"] = "Charging"

        if ev.status == "Charging":
            fleet.loc[i, "battery"] += 2
            st.session_state.energy_log.append(2/100 * BATTERY_CAPACITY_KWH)
            if fleet.loc[i, "battery"] >= 100:
                fleet.loc[i, ["battery","status","station"]] = [100,"Idle",None]

# --------------------------------------------------
# TABS
# --------------------------------------------------
tab1, tab2, tab3 = st.tabs(["🚗 Live Operations", "🔌 Charging & Drivers", "📊 Analytics"])

# ---------------- MAP ----------------
with tab1:
    m = folium.Map(location=[8.48, -13.23], zoom_start=12)
    for s in stations.itertuples():
        folium.Marker([s.lat,s.lon],popup=s.name,
            icon=folium.Icon(color="purple",icon="flash",prefix="fa")).add_to(m)

    for ev in fleet.itertuples():
        color = "green"
        if ev.status == "Charging": color = "blue"
        if ev.status == "Moving to Charge": color = "orange"
        if ev.battery < 20: color = "red"

        folium.Marker(
            [ev.lat,ev.lon],
            popup=f"{ev.id}<br>{ev.service}<br>{ev.status}<br>Battery: {ev.battery:.0f}%",
            icon=folium.Icon(color=color,icon="bolt",prefix="fa")
        ).add_to(m)

    st_folium(m, width=1100, height=500)

# ---------------- TABLES ----------------
with tab2:
    st.dataframe(fleet, use_container_width=True)
    st.dataframe(drivers, use_container_width=True)
    st.dataframe(stations, use_container_width=True)

# ---------------- ANALYTICS + LIVE CHARTS ----------------
with tab3:
    total_energy = sum(st.session_state.energy_log)
    total_cost = total_energy * ENERGY_COST_PER_KWH
    total_revenue = fleet.revenue.sum()

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Fleet Size", len(fleet))
    c2.metric("Avg Battery (%)", f"{fleet.battery.mean():.1f}")
    c3.metric("Active EVs", len(fleet[fleet.status=="Active"]))
    c4.metric("Revenue ($)", f"{total_revenue:.2f}")

    # ---------- BATTERY DISTRIBUTION ----------
    st.subheader("🔋 Battery Level Distribution")
    st.bar_chart(fleet["battery"].value_counts().sort_index())

    # ---------- REVENUE BY SERVICE ----------
    st.subheader("💰 Revenue by Service")
    revenue_by_service = fleet.groupby("service")["revenue"].sum()
    st.bar_chart(revenue_by_service)

    # ---------- UTILIZATION ----------
    st.subheader("🚗 Fleet Utilization")
    utilization = fleet["status"].value_counts()
    st.bar_chart(utilization)

    st.metric("Energy Cost ($)", f"{total_cost:.2f}")
    st.metric("Net Margin ($)", f"{total_revenue-total_cost:.2f}")

    st.success("Live operational intelligence: batteries, revenue, utilization, charging.")
