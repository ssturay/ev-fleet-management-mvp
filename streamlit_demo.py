import streamlit as st
import pandas as pd
import folium
import math
from streamlit_folium import st_folium

# --------------------------------------------------
# CONFIG
# --------------------------------------------------
st.set_page_config(layout="wide")
st.title("EV Fleet Management Platform – Operations + Driver App Demo")

ENERGY_COST_PER_KWH = 0.25
BATTERY_CAPACITY_KWH = 60
CHARGE_RATE_KWH_PER_MIN = 2

SERVICE_RATES = {
    "Ride-Hailing": 2.5,
    "Airport Shuttle": 3.0,
    "School Transport": 1.5,
    "Corporate Hire": 2.0,
    "Daily Rentals": 40/1440,
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
# INIT STATE
# --------------------------------------------------
if "fleet" not in st.session_state:
    st.session_state.fleet = pd.DataFrame([
        {"id":"EV-01","service":"Ride-Hailing","battery":70,"status":"Idle","lat":8.484,"lon":-13.234,"driver":None,"station":None,"revenue":0,"energy":0},
        {"id":"EV-02","service":"Airport Shuttle","battery":45,"status":"Idle","lat":8.470,"lon":-13.210,"driver":None,"station":None,"revenue":0,"energy":0},
        {"id":"EV-03","service":"School Transport","battery":55,"status":"Active","lat":8.460,"lon":-13.250,"driver":"DRV-03","station":None,"revenue":0,"energy":0},
    ])

if "drivers" not in st.session_state:
    st.session_state.drivers = pd.DataFrame([
        {"id":"DRV-01","name":"Driver A","status":"Available","earnings":0,"ev":None},
        {"id":"DRV-02","name":"Driver B","status":"Available","earnings":0,"ev":None},
        {"id":"DRV-03","name":"Driver C","status":"On-Trip","earnings":0,"ev":"EV-03"},
    ])

if "stations" not in st.session_state:
    st.session_state.stations = pd.DataFrame([
        {"id":"CS-01","name":"Aberdeen Hub","lat":8.495,"lon":-13.293},
        {"id":"CS-02","name":"CBD Station","lat":8.484,"lon":-13.231},
    ])

fleet = st.session_state.fleet
drivers = st.session_state.drivers
stations = st.session_state.stations

# --------------------------------------------------
# SIDEBAR – DISPATCH
# --------------------------------------------------
st.sidebar.header("Dispatch & Simulation")

selected_ev = st.sidebar.selectbox("Select EV", fleet.id)
available_drivers = drivers[drivers.status=="Available"].id.tolist()

if available_drivers:
    selected_driver = st.sidebar.selectbox("Assign Driver", available_drivers)
    if st.sidebar.button("Assign Driver"):
        fleet.loc[fleet.id==selected_ev,"driver"] = selected_driver
        fleet.loc[fleet.id==selected_ev,"status"] = "Active"
        drivers.loc[drivers.id==selected_driver,"status"] = "On-Trip"
        drivers.loc[drivers.id==selected_driver,"ev"] = selected_ev

if st.sidebar.button("Simulate 1 Minute"):
    for i, ev in fleet.iterrows():

        # ACTIVE TRIP
        if ev.status == "Active":
            fleet.loc[i,"battery"] -= 1
            fleet.loc[i,"energy"] += 1
            fleet.loc[i,"revenue"] += SERVICE_RATES[ev.service]

            drv = drivers[drivers.id==ev.driver]
            if not drv.empty:
                drivers.loc[drv.index,"earnings"] += SERVICE_RATES[ev.service]*0.4

        # AUTO CHARGE
        if ev.battery < 20 and ev.status != "Charging":
            stn = min(stations.itertuples(),
                      key=lambda s: distance(ev.lat, ev.lon, s.lat, s.lon))
            fleet.loc[i,"station"] = stn.id
            fleet.loc[i,"status"] = "Moving to Charge"

        # MOVE TO CHARGE
        if ev.status == "Moving to Charge":
            stn = stations[stations.id==ev.station].iloc[0]
            lat, lon = move_towards(ev.lat, ev.lon, stn.lat, stn.lon)
            fleet.loc[i,["lat","lon"]] = lat, lon
            if lat == stn.lat and lon == stn.lon:
                fleet.loc[i,"status"] = "Charging"
                drivers.loc[drivers.ev==ev.id,"status"] = "Charging"

        # CHARGING
        if ev.status == "Charging":
            fleet.loc[i,"battery"] += CHARGE_RATE_KWH_PER_MIN
            fleet.loc[i,"energy"] += CHARGE_RATE_KWH_PER_MIN
            if fleet.loc[i,"battery"] >= 100:
                fleet.loc[i,"battery"] = 100
                fleet.loc[i,"status"] = "Idle"
                fleet.loc[i,"station"] = None
                drivers.loc[drivers.ev==ev.id,"status"] = "Available"
                drivers.loc[drivers.ev==ev.id,"ev"] = None

# --------------------------------------------------
# TABS
# --------------------------------------------------
tab1, tab2, tab3, tab4 = st.tabs(
    ["🗺 Live Map","📱 Driver App","💰 Service Profitability","📊 Management KPIs"]
)

# ---------------- MAP ----------------
with tab1:
    m = folium.Map(location=[8.48,-13.23], zoom_start=12)
    for s in stations.itertuples():
        folium.Marker([s.lat,s.lon],popup=s.name,
                      icon=folium.Icon(color="purple",icon="bolt")).add_to(m)

    for ev in fleet.itertuples():
        color = "green"
        if ev.status=="Charging": color="blue"
        if ev.battery<20: color="red"
        folium.Marker(
            [ev.lat,ev.lon],
            popup=f"{ev.id}<br>{ev.service}<br>{ev.status}<br>{ev.battery:.0f}%",
            icon=folium.Icon(color=color,icon="car")
        ).add_to(m)

    st_folium(m, width=1100, height=500)

# ---------------- DRIVER APP ----------------
with tab2:
    st.subheader("Driver Mobile App (Simulation)")
    for d in drivers.itertuples():
        with st.expander(f"{d.name} ({d.status})"):
            st.metric("Earnings ($)", f"{d.earnings:.2f}")
            st.write("Assigned EV:", d.ev)

# ---------------- SERVICE PROFITABILITY ----------------
with tab3:
    svc = fleet.groupby("service").agg(
        Revenue=("revenue","sum"),
        Energy=("energy","sum")
    ).reset_index()
    svc["Energy Cost"] = svc.Energy * ENERGY_COST_PER_KWH
    svc["Net Margin"] = svc.Revenue - svc["Energy Cost"]
    st.dataframe(svc, use_container_width=True)

# ---------------- KPIs ----------------
with tab4:
    st.metric("Total Revenue ($)", fleet.revenue.sum())
    st.metric("Total Energy Cost ($)", fleet.energy.sum()*ENERGY_COST_PER_KWH)
    st.metric("Net Profit ($)",
              fleet.revenue.sum() - fleet.energy.sum()*ENERGY_COST_PER_KWH)
