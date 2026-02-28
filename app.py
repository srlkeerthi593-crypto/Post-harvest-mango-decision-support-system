import streamlit as st
import pandas as pd
import numpy as np
import folium
from streamlit_folium import st_folium

# ---------------------------------------------------
# 🎨 PAGE CONFIG
# ---------------------------------------------------
st.set_page_config(page_title="Farmer Profit Intelligence System", layout="wide")

# ---------------------------------------------------
# 🎨 LIGHT BACKGROUND WITH SMALL MANGO PATTERN
# ---------------------------------------------------
st.markdown("""
<style>
[data-testid="stAppViewContainer"] {
    background-color: #f9fbf7;
}

.block-container {
    background-color: white;
    padding: 2rem;
    border-radius: 15px;
    box-shadow: 0px 4px 15px rgba(0,0,0,0.05);
}
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------
# 🏷 TITLE
# ---------------------------------------------------
st.title("🥭 Farmer Profit Intelligence System")
st.caption("Smart Mango Marketing Decision Engine 🚀")

# ---------------------------------------------------
# 📂 LOAD YOUR CSV FILES
# ---------------------------------------------------
price_data = pd.read_csv("cleaned_price_data.csv")
village_data = pd.read_csv("Village data.csv")
geo_data = pd.read_csv("cleaned_geo_locations.csv")

# Clean column names automatically (prevents KeyError)
for df in [price_data, village_data, geo_data]:
    df.columns = df.columns.str.strip()

# ---------------------------------------------------
# 🧑‍🌾 SIDEBAR – FARMER DETAILS
# ---------------------------------------------------
st.sidebar.header("📝 Farmer Details")

farmer_name = st.sidebar.text_input("👨‍🌾 Farmer Name")
mobile = st.sidebar.text_input("📱 Mobile Number")

village_column = village_data.columns[0]
village_name = st.sidebar.selectbox("🏡 Select Village", village_data[village_column].dropna().unique())

variety_column = "Variety"
variety = st.sidebar.selectbox("🥭 Select Mango Variety", price_data[variety_column].dropna().unique())

quantity = st.sidebar.number_input("📦 Quantity (Quintals)", min_value=1)

run = st.sidebar.button("🚀 Run Smart Analysis")

# ---------------------------------------------------
# 🚚 TRANSPORT COST FUNCTION
# ₹2000 per quintal per 10 km
# ---------------------------------------------------
def calculate_transport(distance, qty):
    return (distance / 10) * 2000 * qty

# ---------------------------------------------------
# 🚀 RUN ANALYSIS
# ---------------------------------------------------
if run:

    st.subheader("🔎 Variety Filtering Logic Used")

    st.info(f"""
    ✔ Step 1: Filtered alternatives where Variety = **{variety}**  
    ✔ Step 2: Revenue = Price × Quantity  
    ✔ Step 3: Transport Cost = (Distance ÷ 10) × 2000 × Quantity  
    ✔ Step 4: Net Profit = Revenue − Transport Cost  
    ✔ Step 5: Ranked Top 10 based on Net Profit  
    """)

    # -------------------------------------------
    # FILTER BASED ON VARIETY
    # -------------------------------------------
    filtered = price_data[price_data["Variety"] == variety]

    # Merge geo data to get lat, long, distance
    merged = pd.merge(filtered, geo_data, on="Name", how="left")

    # Revenue
    merged["Revenue"] = merged["Price_per_quintal"] * quantity

    # Transport cost
    merged["Transport_Cost"] = merged["Distance_km"].apply(
        lambda d: calculate_transport(d, quantity)
    )

    # Net Profit
    merged["Net_Profit"] = merged["Revenue"] - merged["Transport_Cost"]

    # Ranking
    merged = merged.sort_values("Net_Profit", ascending=False)
    merged["Rank"] = range(1, len(merged) + 1)

    top10 = merged.head(10)

    # -------------------------------------------
    # 🏆 BEST ALTERNATIVE
    # -------------------------------------------
    best = top10.iloc[0]

    col1, col2, col3 = st.columns(3)

    col1.metric("💰 Best Profit (₹)", int(best["Net_Profit"]))
    col2.metric("🏆 Best Alternative", best["Name"])
    col3.metric("📦 Quantity (Quintals)", quantity)

    # -------------------------------------------
    # 📊 BAR GRAPH
    # -------------------------------------------
    st.subheader("📊 Top 10 Alternatives Profit Comparison")

    st.bar_chart(top10.set_index("Name")["Net_Profit"])

    # -------------------------------------------
    # 🗺 OSM MAP
    # -------------------------------------------
    st.subheader("🗺 Top 10 Alternatives Location Map")

    village_lat = village_data[village_data[village_column] == village_name]["Latitude"].values[0]
    village_lon = village_data[village_data[village_column] == village_name]["Longitude"].values[0]

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

    # -------------------------------------------
    # 📋 RANKED TABLE
    # -------------------------------------------
    st.subheader("🏅 Ranked Alternatives (1–10)")

    st.dataframe(top10[[
        "Rank",
        "Name",
        "Price_per_quintal",
        "Distance_km",
        "Transport_Cost",
        "Net_Profit"
    ]])
