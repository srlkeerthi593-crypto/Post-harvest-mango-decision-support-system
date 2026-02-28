# ============================================================
# 🥭 FARMER PROFIT INTELLIGENCE SYSTEM
# Smart Mango Marketing Decision Engine
# Streamlit Final Stable Version
# ============================================================

import streamlit as st
import pandas as pd
import numpy as np
import requests
import folium
from streamlit_folium import st_folium
import plotly.express as px

# ---------------- PAGE CONFIG ----------------
st.set_page_config(layout="wide")

st.markdown("""
    <style>
    body {background-color: #f7f9fc;}
    .big-font {font-size:22px !important; font-weight:bold;}
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

    datasets = [villages, prices, geo, processing,
                pulp, pickle_units, local_export, abroad_export]

    for df in datasets:
        df.columns = df.columns.str.strip().str.lower()

    return villages, prices, geo, processing, pulp, pickle_units, local_export, abroad_export

villages, prices, geo, processing, pulp, pickle_units, local_export, abroad_export = load_data()

# ---------------- HELPER FUNCTIONS ----------------
def detect_cols(df):
    name, lat, lon = None, None, None
    for c in df.columns:
        if "lat" in c:
            lat = c
        if "lon" in c:
            lon = c
        if any(x in c for x in ["name","village","market","firm","facility","place","panchayat","hub"]):
            name = c
    return name, lat, lon

def haversine(lat1, lon1, lat2, lon2):
    R = 6371
    lat1, lon1, lat2, lon2 = map(np.radians,[lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = np.sin(dlat/2)**2 + np.cos(lat1)*np.cos(lat2)*np.sin(dlon/2)**2
    return R * 2*np.arcsin(np.sqrt(a))

# ---------------- SIDEBAR ----------------
st.sidebar.header("📝 Farmer Details")

farmer_name = st.sidebar.text_input("👨‍🌾 Farmer Name")
mobile = st.sidebar.text_input("📱 Mobile Number")

village_col, v_lat_col, v_lon_col = detect_cols(villages)
villages[village_col] = villages[village_col].astype(str)

selected_village = st.sidebar.selectbox("🏡 Select Village",
                                         villages[village_col].unique())

variety = st.sidebar.selectbox("🥭 Select Variety",
                               ["Banganapalli","Totapuri","Neelam","Rasalu"])

quantity_qtl = st.sidebar.number_input("📦 Quantity (Quintals)", min_value=1, value=10)

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

# ---------------- MAIN ANALYSIS ----------------
if run:

    village_row = villages[villages[village_col] == selected_village].iloc[0]
    v_lat = village_row[v_lat_col]
    v_lon = village_row[v_lon_col]

    # ---- Base Price ----
    mandi_data = prices.merge(geo, how="left")
    name_col_m, lat_col_m, lon_col_m = detect_cols(mandi_data)

    mandi_data = mandi_data.dropna(subset=[lat_col_m, lon_col_m])

    mandi_data["dist"] = mandi_data.apply(
        lambda r: haversine(v_lat,v_lon,r[lat_col_m],r[lon_col_m]), axis=1
    )

    nearest = mandi_data.loc[mandi_data["dist"].idxmin()]
    base_price = nearest[[c for c in mandi_data.columns if "price" in c][0]]

    # ---- Collect Alternatives ----
    category_dfs = {
        "Mandi": mandi_data,
        "Processing": processing,
        "Pulp": pulp,
        "Pickle": pickle_units,
        "Local Export": local_export,
        "Abroad Export": abroad_export
    }

    results = []

    for category, df in category_dfs.items():

        if variety not in variety_acceptance[category]:
            continue

        name_col, lat_col, lon_col = detect_cols(df)

        for _, row in df.iterrows():
            if pd.notnull(row[lat_col]) and pd.notnull(row[lon_col]):

                dist = haversine(v_lat, v_lon, row[lat_col], row[lon_col])

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

                results.append({
                    "Category":category,
                    "Name":row[name_col],
                    "Distance_km":round(dist,2),
                    "Revenue":round(revenue,2),
                    "Transport":round(transport,2),
                    "Net Profit":round(net_profit,2),
                    "Lat":row[lat_col],
                    "Lon":row[lon_col]
                })

    df_result = pd.DataFrame(results)
    df_top10 = df_result.sort_values("Net Profit", ascending=False).head(10)
    df_top10.reset_index(drop=True, inplace=True)
    df_top10["Rank"] = df_top10.index+1

    best = df_top10.iloc[0]

    # ---------------- SUMMARY CARDS ----------------
    col1,col2,col3,col4 = st.columns(4)

    col1.metric("💰 Base Price (₹/kg)", round(base_price,2))
    col2.metric("📈 Total Revenue (₹)", round(best["Revenue"],2))
    col3.metric("🏆 Best Option", best["Name"])
    col4.metric("🥇 Best Profit (₹)", round(best["Net Profit"],2))

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
    st.subheader("📋 Top 10 Best Alternatives Ranked")

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

    # ---------------- VARIETY LOGIC DISPLAY ----------------
    st.subheader("🧠 Variety Filtering Logic")

    for cat, vals in variety_acceptance.items():
        if variety in vals:
            st.success(f"✔ {cat} accepts {variety}")
        else:
            st.error(f"✘ {cat} does NOT accept {variety}")
