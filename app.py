import streamlit as st
import pandas as pd
import numpy as np
import requests
import folium
import plotly.express as px
from streamlit_folium import st_folium
from datetime import datetime

st.set_page_config(page_title="Farmer Decision Intelligence", layout="wide")

# ==============================
# ATTRACTIVE BACKGROUND
# ==============================
page_bg = """
<style>
[data-testid="stAppViewContainer"] {
    background: linear-gradient(135deg, #f6d365 0%, #fda085 100%);
}
[data-testid="stSidebar"] {
    background-color: #ffffff;
}
</style>
"""
st.markdown(page_bg, unsafe_allow_html=True)

st.title("🥭 Farmer Decision Intelligence System")

# ==============================
# CONFIG
# ==============================
RADIUS_KM = 80
TRANSPORT_RATE_PER_10KM_PER_TONNE = 2000
SPOILAGE_PER_10KM = 0.004
HANDLING_RISK = 0.002

# ==============================
# LOAD DATA
# ==============================
@st.cache_data
def load_data():
    villages = pd.read_csv("Village data.csv")
    prices = pd.read_csv("cleaned_price_data.csv")
    geo = pd.read_csv("cleaned_geo_locations.csv")
    processing = pd.read_csv("cleaned_processing_facilities.csv")
    pulp = pd.read_csv("Pulp_units_merged_lat_long.csv")
    pickle_units = pd.read_csv("cleaned_pickle_units.csv")
    local_export = pd.read_csv("cleaned_local_export.csv")
    abroad_export = pd.read_csv("cleaned_abroad_export.csv")

    for df in [villages, prices, geo, processing,
               pulp, pickle_units, local_export, abroad_export]:
        df.columns = df.columns.str.strip().str.lower()

    return villages, prices, geo, processing, pulp, pickle_units, local_export, abroad_export

villages, prices, geo, processing, pulp, pickle_units, local_export, abroad_export = load_data()

# ==============================
# HELPER FUNCTIONS
# ==============================
def haversine(lat1, lon1, lat2, lon2):
    R = 6371
    lat1, lon1, lat2, lon2 = map(np.radians,[lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = np.sin(dlat/2)**2 + np.cos(lat1)*np.cos(lat2)*np.sin(dlon/2)**2
    return R * 2*np.arcsin(np.sqrt(a))

def detect_cols(df):
    name, lat, lon = None, None, None
    for c in df.columns:
        if "lat" in c: lat = c
        if "lon" in c: lon = c
        if any(x in c for x in ["name","firm","facility","hub","market","place","panchayat","village"]):
            name = c
    return name, lat, lon

# ==============================
# FARMER REGISTRATION
# ==============================
st.sidebar.header("🧑‍🌾 Farmer Registration")

farmer_name = st.sidebar.text_input("Farmer Name")
mobile = st.sidebar.text_input("Mobile")
district = st.sidebar.text_input("District")

if st.sidebar.button("Register Farmer"):
    st.session_state["farmer"] = {
        "Name": farmer_name,
        "Mobile": mobile,
        "District": district
    }
    st.sidebar.success("Registered Successfully")

# ==============================
# INPUT PANEL
# ==============================
st.sidebar.header("📊 Crop Input")

village_input = st.sidebar.text_input("Village Name")
variety = st.sidebar.selectbox(
    "Mango Variety",
    ["Banganapalli","Totapuri","Neelam","Rasalu"]
)
TONNES = st.sidebar.number_input("Quantity (Tonnes)", min_value=1, value=10)

run = st.sidebar.button("Run Smart Analysis")

# ==============================
# VARIETY ACCEPTANCE
# ==============================
variety_acceptance = {
    "Mandi": ["Banganapalli","Totapuri","Neelam","Rasalu"],
    "Processing": ["Totapuri","Neelam"],
    "Pulp": ["Totapuri"],
    "Pickle": ["Totapuri","Rasalu"],
    "Local Export": ["Banganapalli"],
    "Abroad Export": ["Banganapalli"]
}

category_params = {
    "Mandi": {"margin":0, "color":"blue"},
    "Processing": {"margin":0.03, "color":"orange"},
    "Pulp": {"margin":0.04, "color":"purple"},
    "Pickle": {"margin":0.025, "color":"cadetblue"},
    "Local Export": {"margin":0.05, "color":"darkgreen"},
    "Abroad Export": {"margin":0.07, "color":"red"},
}

# ==============================
# RUN LOGIC
# ==============================
if run:

    v_name_col, v_lat_col, v_lon_col = detect_cols(villages)
    villages[v_name_col] = villages[v_name_col].str.lower()

    if village_input.lower() not in villages[v_name_col].values:
        st.error("Village not found")
        st.stop()

    village = villages[villages[v_name_col] == village_input.lower()].iloc[0]
    v_lat = village[v_lat_col]
    v_lon = village[v_lon_col]

    st.subheader("🧠 Variety Logic")

    allowed = [c for c in variety_acceptance if variety in variety_acceptance[c]]
    rejected = [c for c in variety_acceptance if variety not in variety_acceptance[c]]

    st.success(f"Allowed Categories: {allowed}")
    st.error(f"Not Suitable: {rejected}")

    # ==============================
    # BASE MARKET PRICE
    # ==============================
    mandi_data = prices.merge(geo, on="market", how="left")
    mandi_data = mandi_data.dropna(subset=["latitude","longitude"])

    mandi_data["approx"] = mandi_data.apply(
        lambda r: haversine(v_lat,v_lon,r["latitude"],r["longitude"]), axis=1
    )

    nearest = mandi_data.loc[mandi_data["approx"].idxmin()]
    base_price = nearest["today_price(rs/kg)"]

    st.subheader("🏪 Nearest Market")
    st.write("Market:", nearest["market"])
    st.write("Base Price (₹/kg):", base_price)

    # ==============================
    # COLLECT OPTIONS
    # ==============================
    def collect_all(df, category):
        if variety not in variety_acceptance[category]:
            return pd.DataFrame()

        name_col, lat_col, lon_col = detect_cols(df)
        rows = []

        for _, row in df.iterrows():
            if pd.notnull(row[lat_col]) and pd.notnull(row[lon_col]):
                approx = haversine(v_lat,v_lon,row[lat_col],row[lon_col])
                if approx <= RADIUS_KM:
                    rows.append({
                        "Type":category,
                        "Name":row[name_col],
                        "Lat":row[lat_col],
                        "Lon":row[lon_col],
                        "Approx":approx
                    })
        return pd.DataFrame(rows)

    df_all = pd.concat([
        collect_all(mandi_data,"Mandi"),
        collect_all(processing,"Processing"),
        collect_all(pulp,"Pulp"),
        collect_all(pickle_units,"Pickle"),
        collect_all(local_export,"Local Export"),
        collect_all(abroad_export,"Abroad Export")
    ], ignore_index=True)

    results = []

    for _, row in df_all.iterrows():

        try:
            route = requests.get(
                f"http://router.project-osrm.org/route/v1/driving/"
                f"{v_lon},{v_lat};{row['Lon']},{row['Lat']}?overview=false",
                timeout=10
            ).json()

            km = route["routes"][0]["distance"]/1000 if "routes" in route else row["Approx"]
        except:
            km = row["Approx"]

        if km > RADIUS_KM:
            continue

        cat = row["Type"]
        margin = category_params[cat]["margin"]

        adjusted_price = base_price * (1 + margin)
        revenue = adjusted_price * 1000 * TONNES
        transport = (km/10) * TRANSPORT_RATE_PER_10KM_PER_TONNE * TONNES

        spoilage_risk = SPOILAGE_PER_10KM * (km/10)
        risk_rate = spoilage_risk + HANDLING_RISK
        risk_cost = revenue * risk_rate

        net_profit = revenue - transport - risk_cost

        results.append({
            "Type":cat,
            "Name":row["Name"],
            "Distance_km":round(km,2),
            "Net_Profit":round(net_profit,2),
            "Lat":row["Lat"],
            "Lon":row["Lon"]
        })

    df = pd.DataFrame(results)
    df_top10 = df.sort_values("Distance_km").head(10)

    st.subheader("📊 Top 10 Closest Options")
    st.dataframe(df_top10)

    best = df_top10.loc[df_top10["Net_Profit"].idxmax()]
    st.success(f"🏆 Most Profitable: {best['Name']} ({best['Type']})")

    # ==============================
    # PROFIT CHART
    # ==============================
    fig = px.bar(df_top10, x="Name", y="Net_Profit",
                 title="Net Profit Comparison")
    st.plotly_chart(fig, use_container_width=True)

    # ==============================
    # MAP
    # ==============================
    m = folium.Map(location=[v_lat, v_lon], zoom_start=10)
    folium.Marker([v_lat, v_lon], popup="Village").add_to(m)

    for _, row in df_top10.iterrows():
        folium.Marker(
            [row["Lat"], row["Lon"]],
            popup=f"{row['Name']} ({row['Type']})"
        ).add_to(m)

    st_folium(m, width=1000)

    # ==============================
    # REPORT DOWNLOAD
    # ==============================
    farmer_info = st.session_state.get("farmer", {})
    report = f"""
Farmer: {farmer_info.get('Name','-')}
Village: {village_input}
Variety: {variety}
Quantity: {TONNES} tonnes
Base Price: ₹{base_price}
Best Option: {best['Name']} ({best['Type']})
"""
    st.download_button("Download Advisory Report", report, "farmer_report.txt")

