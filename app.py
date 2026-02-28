import streamlit as st
import pandas as pd
import numpy as np
import folium
from streamlit_folium import st_folium

# -------------------------------------
# 🎨 Page Config
# -------------------------------------
st.set_page_config(layout="wide")

# -------------------------------------
# 🌅 Mango Background Image
# -------------------------------------
page_bg = """
<style>
[data-testid="stAppViewContainer"] {
background-image: url("mango dashboard.webp");
background-size: cover;
background-position: center;
background-attachment: fixed;
}
[data-testid="stHeader"] {
background: rgba(0,0,0,0);
}
</style>
"""
st.markdown(page_bg, unsafe_allow_html=True)

st.title("🥭 Farmer Profit Intelligence System")

# -------------------------------------
# 📂 Load All Your CSV Files
# -------------------------------------
price_data = pd.read_csv("cleaned_price_data.csv")
processing = pd.read_csv("cleaned_processing_facilities.csv")
pulp = pd.read_csv("Pulp_units_merged_lat_long.csv")
village = pd.read_csv("Village data.csv")
abroad = pd.read_csv("cleaned_abroad_export.csv")
cold = pd.read_csv("cleaned_cold_storage.csv")
fpo = pd.read_csv("cleaned_fpo.csv")
geo = pd.read_csv("cleaned_geo_locations.csv")
local_export = pd.read_csv("cleaned_local_export.csv")
pickle_units = pd.read_csv("cleaned_pickle_units.csv")

# -------------------------------------
# 🧑‍🌾 Farmer Input Panel
# -------------------------------------
st.sidebar.header("📝 Farmer Details")

name = st.sidebar.text_input("👨‍🌾 Farmer Name")
mobile = st.sidebar.text_input("📱 Mobile Number")
village_name = st.sidebar.selectbox("🏡 Select Village", village["Village"].unique())
variety = st.sidebar.selectbox("🥭 Mango Variety", price_data["Variety"].unique())
quantity = st.sidebar.number_input("📦 Quantity (Quintals)", min_value=1)

run = st.sidebar.button("🚀 Run Smart Analysis")

# -------------------------------------
# 🚚 Transport Cost Logic
# ₹2000 per quintal per 10 km
# -------------------------------------
def transport_cost(distance, qty):
    return (distance/10) * 2000 * qty

# -------------------------------------
# 🚀 Run Analysis
# -------------------------------------
if run:

    st.subheader("🔍 Variety Filtering Logic Used")

    st.info(f"""
    ✔ Filtered all datasets where Variety = {variety}  
    ✔ Transport cost = (Distance / 10) × 2000 × Quantity  
    ✔ Net Profit = (Price × Quantity) - Transport Cost  
    ✔ Ranked Top 10 alternatives  
    """)

    # -----------------------------
    # FILTER ALL DATASETS
    # -----------------------------
    filtered_price = price_data[price_data["Variety"] == variety]

    # Merge geo coordinates
    merged = pd.merge(filtered_price, geo, on="Name", how="left")

    # Revenue
    merged["Revenue"] = merged["Price_per_quintal"] * quantity

    # Transport cost
    merged["Transport_Cost"] = merged.apply(
        lambda x: transport_cost(x["Distance_km"], quantity), axis=1
    )

    # Net profit
    merged["Net_Profit"] = merged["Revenue"] - merged["Transport_Cost"]

    # Ranking
    merged = merged.sort_values(by="Net_Profit", ascending=False)
    merged["Rank"] = range(1, len(merged)+1)

    top10 = merged.head(10)

    # -------------------------------------
    # 🏆 Best Alternative
    # -------------------------------------
    best = top10.iloc[0]

    st.success(f"🏆 Best Alternative: {best['Name']}")
    st.success(f"💰 Expected Net Profit: ₹ {int(best['Net_Profit'])}")

    # -------------------------------------
    # 📊 Bar Chart Comparison
    # -------------------------------------
    st.subheader("📊 Profit Comparison (Top 10 Alternatives)")
    st.bar_chart(top10.set_index("Name")["Net_Profit"])

    # -------------------------------------
    # 🗺 OSM MAP
    # -------------------------------------
    st.subheader("🗺 Top 10 Alternatives Location Map")

    village_lat = village[village["Village"] == village_name]["Latitude"].values[0]
    village_lon = village[village["Village"] == village_name]["Longitude"].values[0]

    m = folium.Map(location=[village_lat, village_lon], zoom_start=8)

    # Village marker
    folium.Marker(
        [village_lat, village_lon],
        tooltip="🏡 Village",
        icon=folium.Icon(color="black")
    ).add_to(m)

    # Market markers
    for _, row in top10.iterrows():
        folium.Marker(
            [row["Latitude"], row["Longitude"]],
            tooltip=f"{row['Rank']}️⃣ {row['Name']} ₹{int(row['Net_Profit'])}",
            icon=folium.Icon(color="green")
        ).add_to(m)

    st_folium(m, width=1100, height=500)

    # -------------------------------------
    # 📋 Ranked Table
    # -------------------------------------
    st.subheader("🏅 Ranked Alternatives")

    st.dataframe(top10[[
        "Rank",
        "Name",
        "Price_per_quintal",
        "Distance_km",
        "Transport_Cost",
        "Net_Profit"
    ]])
