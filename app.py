# ==========================================================
# 🥭 FARMER PROFIT INTELLIGENCE SYSTEM
# ==========================================================

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import folium
from streamlit_folium import st_folium

st.set_page_config(layout="wide")

# ==========================================================
# HEADER WITH BANNER
# ==========================================================

st.markdown("""
<div style="text-align:center;">
    <h1>🥭 Farmer Profit Intelligence System</h1>
    <h4>Smart Mango Marketing Decision Engine</h4>
</div>
""", unsafe_allow_html=True)

st.image(
    "https://images.unsplash.com/photo-1621263764928-df1444c5e859",
    use_container_width=True
)

# ==========================================================
# LOAD DATA
# ==========================================================

@st.cache_data
def load_data():
    df = pd.read_csv("cleaned_price_data.csv")
    return df

df = load_data()

# Clean numeric columns
df["today_price(rs/kg)"] = pd.to_numeric(df["today_price(rs/kg)"], errors="coerce").fillna(0)
df["yesterday_price(rs/kg)"] = pd.to_numeric(df["yesterday_price(rs/kg)"], errors="coerce").fillna(0)

# ==========================================================
# SIDEBAR CONTROL PANEL
# ==========================================================

st.sidebar.title("📊 Analysis Control Panel")

village = st.sidebar.text_input("Enter Village Name", "Ramapuram")
variety = st.sidebar.selectbox("Select Mango Variety", ["Banganapalli", "Totapuri"])
TONNES = st.sidebar.number_input("Enter Quantity (Tonnes)", min_value=1, value=10)

run = st.sidebar.button("Run Smart Analysis")

# ==========================================================
# MAIN ANALYSIS
# ==========================================================

if run:

    # Use today price
    df["BasePrice"] = df["today_price(rs/kg)"]

    # Revenue calculation
    df["Total Revenue"] = df["BasePrice"] * TONNES * 1000

    # Simple profit formula (you can refine later)
    transport_cost = 5 * df["lat"].sub(df["lat"].mean()).abs()
    df["Net Profit"] = df["Total Revenue"] - (transport_cost * 1000)

    df_sorted = df.sort_values("Net Profit", ascending=False)
    top10 = df_sorted.head(10)

    best_market = top10.iloc[0]

    # ======================================================
    # KPI CARDS
    # ======================================================

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Base Price (₹/kg)", round(best_market["BasePrice"], 2))
    col2.metric("Total Revenue (₹)", f"{int(best_market['Total Revenue']):,}")
    col3.metric("Best Market", best_market["market"])
    col4.metric("Best Profit (₹)", f"{int(best_market['Net Profit']):,}")

    # ======================================================
    # PROFIT BAR CHART
    # ======================================================

    st.markdown("### 📈 Profit Comparison")

    fig = px.bar(
        top10,
        x="market",
        y="Net Profit",
        color="Net Profit",
        color_continuous_scale="Greens"
    )

    st.plotly_chart(fig, use_container_width=True)

    # ======================================================
    # TOP 10 TABLE
    # ======================================================

    st.markdown("### 📋 Top 10 Closest Markets")

    table = top10[["market", "Net Profit"]].copy()
    table["Net Profit"] = table["Net Profit"].round(0)

    st.dataframe(table, use_container_width=True)

    # ======================================================
    # MAP
    # ======================================================

    st.markdown("### 🗺 Market Location Map")

    m = folium.Map(
        location=[df["lat"].mean(), df["long"].mean()],
        zoom_start=9
    )

    # Village marker
    folium.Marker(
        [df["lat"].mean(), df["long"].mean()],
        popup="Village",
        icon=folium.Icon(color="black")
    ).add_to(m)

    for _, row in top10.iterrows():
        folium.Marker(
            [row["lat"], row["long"]],
            popup=f"{row['market']} - ₹{int(row['Net Profit'])}",
            icon=folium.Icon(color="green")
        ).add_to(m)

    st_folium(m, use_container_width=True)


