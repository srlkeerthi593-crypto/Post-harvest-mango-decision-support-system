# ==========================================================
# 🥭 FARMER PROFIT INTELLIGENCE SYSTEM
# Professional Dashboard Version
# ==========================================================

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(layout="wide")

# ==========================================================
# PROFESSIONAL CSS STYLING
# ==========================================================

st.markdown("""
<style>
.big-title {
    text-align:center;
    font-size:40px;
    font-weight:700;
}
.subtitle {
    text-align:center;
    font-size:18px;
    color:gray;
}
.kpi-card {
    background-color:#f8f9fa;
    padding:20px;
    border-radius:12px;
    box-shadow:0 2px 6px rgba(0,0,0,0.1);
    text-align:center;
}
.section-box {
    background-color:white;
    padding:20px;
    border-radius:12px;
    box-shadow:0 2px 8px rgba(0,0,0,0.1);
}
</style>
""", unsafe_allow_html=True)

# ==========================================================
# HEADER
# ==========================================================

st.markdown('<div class="big-title">🥭 Farmer Profit Intelligence System</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Smart Mango Marketing Decision Engine</div>', unsafe_allow_html=True)

st.image(
    "https://images.unsplash.com/photo-1598514982886-87a5eecb1c0c",
    use_container_width=True
)

# ==========================================================
# LOAD DATA (FAST CACHE)
# ==========================================================

@st.cache_data(show_spinner=False)
def load_data():
    df = pd.read_csv("cleaned_price_data.csv")
    df["today_price(rs/kg)"] = pd.to_numeric(df["today_price(rs/kg)"], errors="coerce").fillna(0)
    df["yesterday_price(rs/kg)"] = pd.to_numeric(df["yesterday_price(rs/kg)"], errors="coerce").fillna(0)
    return df

df = load_data()

# ==========================================================
# SIDEBAR
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

    df["BasePrice"] = df["today_price(rs/kg)"]
    df["TotalRevenue"] = df["BasePrice"] * TONNES * 1000

    # Dummy distance calculation (can replace with haversine later)
    df["Distance"] = np.random.uniform(20, 30, len(df))

    df["TransportCost"] = df["Distance"] * 10
    df["NetProfit"] = df["TotalRevenue"] - df["TransportCost"] * 1000

    top10 = df.sort_values("NetProfit", ascending=False).head(10)
    best = top10.iloc[0]

    # ======================================================
    # KPI ROW
    # ======================================================

    col1, col2, col3, col4 = st.columns(4)

    col1.markdown(f"""
    <div class="kpi-card">
        <h4>Base Price (₹/kg)</h4>
        <h2>{round(best['BasePrice'],2)}</h2>
    </div>
    """, unsafe_allow_html=True)

    col2.markdown(f"""
    <div class="kpi-card">
        <h4>Total Revenue (₹)</h4>
        <h2>{int(best['TotalRevenue']):,}</h2>
    </div>
    """, unsafe_allow_html=True)

    col3.markdown(f"""
    <div class="kpi-card">
        <h4>Best Market</h4>
        <h2>{best['market']}</h2>
    </div>
    """, unsafe_allow_html=True)

    col4.markdown(f"""
    <div class="kpi-card">
        <h4>Best Profit (₹)</h4>
        <h2 style="color:green;">{int(best['NetProfit']):,}</h2>
    </div>
    """, unsafe_allow_html=True)

    # ======================================================
    # PROFIT CHART
    # ======================================================

    st.markdown("## 📈 Profit Comparison")

    fig = px.bar(
        top10,
        x="market",
        y="NetProfit",
        color="NetProfit",
        color_continuous_scale="Greens",
        text_auto=True
    )

    fig.update_layout(
        template="plotly_white",
        xaxis_title="Market",
        yaxis_title="Net Profit (₹)"
    )

    st.plotly_chart(fig, use_container_width=True)

    # ======================================================
    # TOP 10 TABLE
    # ======================================================

    st.markdown("## 📋 Top 10 Closest Markets")

    table = top10[["market", "Distance", "NetProfit"]].copy()
    table = table.rename(columns={
        "market": "Market",
        "Distance": "Distance (km)",
        "NetProfit": "Net Profit (₹)"
    })

    st.dataframe(table, use_container_width=True)

    # ======================================================
    # MAP (FAST PLOTLY MAP)
    # ======================================================

    st.markdown("## 🗺 Market Location Map")

    if "lat" in df.columns and "long" in df.columns:

        map_fig = px.scatter_mapbox(
            top10,
            lat="lat",
            lon="long",
            hover_name="market",
            hover_data=["NetProfit"],
            zoom=8,
            height=500
        )

        map_fig.update_layout(
            mapbox_style="open-street-map",
            margin={"r":0,"t":0,"l":0,"b":0}
        )

        st.plotly_chart(map_fig, use_container_width=True)
