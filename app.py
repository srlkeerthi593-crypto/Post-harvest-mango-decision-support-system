# ============================================================
# 🥭 FARMER PROFIT INTELLIGENCE SYSTEM
# FINAL STABLE VERSION (CUSTOMIZED TO YOUR CSV STRUCTURE)
# ============================================================

import streamlit as st
import pandas as pd
import numpy as np
import folium
from streamlit_folium import st_folium
import plotly.express as px

st.set_page_config(layout="wide")

# ---------------- STYLE ----------------
st.markdown("""
    <style>
    body {background-color: #f4f7fb;}
    .stMetric {font-size:20px;}
    </style>
""", unsafe_allow_html=True)

st.title("🥭 Farmer Profit Intelligence System")
st.subheader("Smart Mango Marketing Decision Engine")

# ---------------- LOAD DATA ----------------
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

    dfs = [villages, prices, geo, processing,
           pulp, pickle_units, local_export, abroad_export]

    for df in dfs:
        df.columns = df.columns.str.strip().str.lower()

    return villages, prices, geo, processing, pulp, pickle_units, local_export, abroad_export

villages, prices, geo, processing, pulp, pickle_units, local_export, abroad_export = load_data()

# ---------------- SIDEBAR ----------------
st.sidebar.header("👨‍🌾 Farmer Details")

farmer_name = st.sidebar.text_input("Farmer Name")
mobile = st.sidebar.text_input("Mobile Number")

village_name_col = "gram panchayat"
v_lat_col = "latitude"
v_lon_col = "longitude"

selected_village = st.sidebar.selectbox(
    "Select Village",
    villages[village_name_col].unique()
)

variety = st.sidebar.selectbox(
    "Select Variety",
    ["Banganapalli","Totapuri","Neelam","Rasalu"]
)

quantity_qtl = st.sidebar.number_input("Quantity (Quintals)", min_value=1, value=10)

run = st.sidebar.button("🚀 Run Smart Analysis")

# ---------------- VARIETY LOGIC ----------------
variety_acceptance = {
    "Mandi": ["Banganapalli","Totapuri","Neelam","Rasalu"],
    "Processing": ["Totapuri","Neelam"],
    "Pulp": ["Totapuri"],
    "Pickle": ["Totapuri","Rasalu"],
    "Local Export": ["Banganapalli"],
    "Abroad Export": ["Banganapalli"]
}

# ---------------- DISTANCE FUNCTION ----------------
def haversine(lat1, lon1, lat2, lon2):
    R = 6371
    lat1, lon1, lat2, lon2 = map(np.radians,[lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = np.sin(dlat/2)**2 + np.cos(lat1)*np.cos(lat2)*np.sin(dlon/2)**2
    return R * 2*np.arcsin(np.sqrt(a))

# ---------------- MAIN ANALYSIS ----------------
if run:

    village_row = villages[villages[village_name_col] == selected_village].iloc[0]
    v_lat = village_row[v_lat_col]
    v_lon = village_row[v_lon_col]

    # Correct merge
    mandi_data = prices.merge(geo, on="market", how="left")

    mandi_data = mandi_data.dropna(subset=["latitude","longitude"])

    mandi_data["distance"] = mandi_data.apply(
        lambda r: haversine(v_lat,v_lon,r["latitude"],r["longitude"]), axis=1
    )

    nearest = mandi_data.loc[mandi_data["distance"].idxmin()]
    base_price = nearest["today_price(rs/kg)"]

    results = []

    category_dfs = {
        "Mandi": mandi_data,
        "Processing": processing,
        "Pulp": pulp,
        "Pickle": pickle_units,
        "Local Export": local_export,
        "Abroad Export": abroad_export
    }

    for category, df in category_dfs.items():

        if variety not in variety_acceptance[category]:
            continue

        if "latitude" not in df.columns:
            continue

        for _, row in df.iterrows():

            if pd.notnull(row["latitude"]) and pd.notnull(row["longitude"]):

                dist = haversine(v_lat, v_lon,
                                 row["latitude"],
                                 row["longitude"])

                transport = (dist/10) * 2000 * quantity_qtl

                margin = {
                    "Mandi":0,
                    "Processing":0.03,
                    "Pulp":0.04,
                    "Pickle":0.025,
                    "Local Export":0.05,
                    "Abroad Export":0.07
                }[category]

                adjusted_price = base_price * (1+margin)
                revenue = adjusted_price * 100 * quantity_qtl
                net_profit = revenue - transport

                name_col = [c for c in df.columns if "place" in c or "market" in c][0]

                results.append({
                    "Category":category,
                    "Name":row[name_col],
                    "Distance_km":round(dist,2),
                    "Net Profit":round(net_profit,2),
                    "Lat":row["latitude"],
                    "Lon":row["longitude"]
                })

    df_result = pd.DataFrame(results)

    if df_result.empty:
        st.error("❌ No alternatives found. Check dataset lat/lon.")
        st.stop()

    df_top10 = df_result.sort_values("Net Profit", ascending=False).head(10)
    df_top10.reset_index(drop=True, inplace=True)
    df_top10["Rank"] = df_top10.index + 1

    best = df_top10.iloc[0]

    # ---------------- METRICS ----------------
    col1,col2,col3,col4 = st.columns(4)

    col1.metric("💰 Base Price (₹/kg)", round(base_price,2))
    col2.metric("🏆 Best Market", best["Name"])
    col3.metric("🥇 Best Profit (₹)", best["Net Profit"])
    col4.metric("📦 Quantity (Qtl)", quantity_qtl)

    st.markdown("---")

    # ---------------- BAR CHART ----------------
    st.subheader("📊 Profit Comparison (Top 10)")

    fig = px.bar(df_top10,
                 x="Name",
                 y="Net Profit",
                 color="Category",
                 text="Net Profit")

    st.plotly_chart(fig, use_container_width=True)

    # ---------------- TABLE ----------------
    st.subheader("📋 Top 10 Ranked Alternatives")
    st.dataframe(df_top10[["Rank","Name","Category","Distance_km","Net Profit"]])

    # ---------------- MAP ----------------
    st.subheader("🗺 Market Location Map")

    m = folium.Map(location=[v_lat,v_lon], zoom_start=9)

    folium.Marker([v_lat,v_lon],
                  popup="Village",
                  icon=folium.Icon(color="black")).add_to(m)

    for _,row in df_top10.iterrows():
        folium.Marker([row["Lat"],row["Lon"]],
                      popup=f"Rank {row['Rank']} - {row['Name']}",
                      icon=folium.Icon(color="green")).add_to(m)

    st_folium(m, width=1000, height=500)

    # ---------------- VARIETY LOGIC ----------------
    st.subheader("🧠 Variety Filtering Logic")

    for cat, vals in variety_acceptance.items():
        if variety in vals:
            st.success(f"✔ {cat} accepts {variety}")
        else:
            st.error(f"✘ {cat} does NOT accept {variety}")
