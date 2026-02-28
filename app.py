import streamlit as st
import pandas as pd
import numpy as np
import folium
from streamlit_folium import st_folium

# --------------------------------------------------
# 🎨 PAGE SETTINGS
# --------------------------------------------------
st.set_page_config(page_title="Farmer Profit Intelligence System", layout="wide")

st.markdown("""
<style>
[data-testid="stAppViewContainer"] {
    background-color: #f5f9f4;
}
.block-container {
    background-color: white;
    padding: 2rem;
    border-radius: 15px;
}
</style>
""", unsafe_allow_html=True)

st.title("🥭 Farmer Profit Intelligence System")
st.caption("Smart Mango Marketing Decision Engine 🚀")

# --------------------------------------------------
# 📂 LOAD ALL YOUR CSV FILES
# --------------------------------------------------
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

# Clean column names (prevents KeyError)
for df in [price_data, processing, pulp, village, abroad, cold, fpo, geo, local_export, pickle_units]:
    df.columns = df.columns.str.strip()

# --------------------------------------------------
# 🧑‍🌾 FARMER INPUT
# --------------------------------------------------
st.sidebar.header("📝 Farmer Details")

farmer_name = st.sidebar.text_input("👨‍🌾 Farmer Name")
mobile = st.sidebar.text_input("📱 Mobile Number")

village_col = village.columns[0]
village_name = st.sidebar.selectbox("🏡 Select Village", village[village_col].dropna().unique())

variety = st.sidebar.selectbox("🥭 Select Mango Variety", price_data["Variety"].dropna().unique())

quantity = st.sidebar.number_input("📦 Quantity (Quintals)", min_value=1)

run = st.sidebar.button("🚀 Run Smart Analysis")

# --------------------------------------------------
# 🚚 TRANSPORT COST FUNCTION
# ₹2000 per quintal per 10 km
# --------------------------------------------------
def transport_cost(distance, qty):
    return (distance / 10) * 2000 * qty

# --------------------------------------------------
# 🚀 RUN ANALYSIS
# --------------------------------------------------
if run:

    st.subheader("🔎 Variety Filtering Logic Used")

    st.info(f"""
    ✔ Step 1: Filtered all alternatives where Variety = **{variety}**  
    ✔ Step 2: Revenue = Price × Quantity  
    ✔ Step 3: Transport Cost = (Distance ÷ 10) × 2000 × Quantity  
    ✔ Step 4: Net Profit = Revenue − Transport Cost  
    ✔ Step 5: Ranked Top 10 alternatives  
    """)

    # --------------------------------------------------
    # FILTER BY VARIETY
    # --------------------------------------------------
    filtered_price = price_data[price_data["Variety"] == variety]

    # Merge geo to get Latitude, Longitude, Distance
    merged = pd.merge(filtered_price, geo, on="Name", how="left")

    # Revenue
    merged["Revenue"] = merged["Price_per_quintal"] * quantity

    # Transport
    merged["Transport_Cost"] = merged["Distance_km"].apply(lambda d: transport_cost(d, quantity))

    # Net Profit
    merged["Net_Profit"] = merged["Revenue"] - merged["Transport_Cost"]

    # Ranking
    merged = merged.sort_values("Net_Profit", ascending=False)
    merged["Rank"] = range(1, len(merged) + 1)

    top10 = merged.head(10)

    # --------------------------------------------------
    # 🏆 BEST RECOMMENDATION
    # --------------------------------------------------
    best = top10.iloc[0]

    col1, col2, col3 = st.columns(3)
    col1.metric("🏆 Best Alternative", best["Name"])
    col2.metric("💰 Best Net Profit (₹)", int(best["Net_Profit"]))
    col3.metric("📦 Quantity (Quintals)", quantity)

    # --------------------------------------------------
    # 📊 BAR GRAPH
    # --------------------------------------------------
    st.subheader("📊 Profit Comparison – Top 10 Alternatives")

    st.bar_chart(top10.set_index("Name")["Net_Profit"])

    # --------------------------------------------------
    # 🗺 OSM MAP
    # --------------------------------------------------
    st.subheader("🗺 Location Map – Top 10 Alternatives")

    village_lat = village[village[village_col] == village_name]["Latitude"].values[0]
    village_lon = village[village[village_col] == village_name]["Longitude"].values[0]

    m = folium.Map(location=[village_lat, village_lon], zoom_start=8)

    # Village Marker
    folium.Marker(
        [village_lat, village_lon],
        tooltip="🏡 Village",
        icon=folium.Icon(color="black")
    ).add_to(m)

    # Top 10 Markers
    for _, row in top10.iterrows():
        folium.Marker(
            [row["Latitude"], row["Longitude"]],
            tooltip=f"{row['Rank']}️⃣ {row['Name']} - ₹{int(row['Net_Profit'])}",
            icon=folium.Icon(color="green")
        ).add_to(m)

    st_folium(m, width=1100, height=500)

    # --------------------------------------------------
    # 📋 RANKED TABLE
    # --------------------------------------------------
    st.subheader("🏅 Ranked Alternatives (1–10)")

    st.dataframe(top10[[
        "Rank",
        "Name",
        "Price_per_quintal",
        "Distance_km",
        "Transport_Cost",
        "Net_Profit"
    ]])

