# ==========================================================
# 🥭 FARMER PROFIT INTELLIGENCE SYSTEM
# With Registration + Background Image
# ==========================================================

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import os

st.set_page_config(layout="wide")

# ==========================================================
# SET BACKGROUND IMAGE (YOUR UPLOADED IMAGE)
# ==========================================================

def set_bg():
    st.markdown(
        f"""
        <style>
        .stApp {{
            background-image: url("mango_bg.jpg");
            background-size: cover;
            background-position: center;
            background-attachment: fixed;
        }}
        .overlay {{
            background-color: rgba(0,0,0,0.75);
            padding: 20px;
            border-radius: 15px;
        }}
        </style>
        """,
        unsafe_allow_html=True
    )

set_bg()

# ==========================================================
# FARMER DATABASE
# ==========================================================

FARMER_DB = "farmers_database.csv"

if not os.path.exists(FARMER_DB):
    pd.DataFrame(columns=["Name", "Mobile", "Village", "District"]).to_csv(FARMER_DB, index=False)

if "registered" not in st.session_state:
    st.session_state.registered = False

# ==========================================================
# REGISTRATION
# ==========================================================

st.sidebar.title("👨‍🌾 Farmer Registration")

name = st.sidebar.text_input("Farmer Name")
mobile = st.sidebar.text_input("Mobile Number")
village_reg = st.sidebar.text_input("Village")
district = st.sidebar.text_input("District")

if st.sidebar.button("Register Farmer"):

    if name and mobile and village_reg and district:

        new_farmer = pd.DataFrame([[name, mobile, village_reg, district]],
                                  columns=["Name", "Mobile", "Village", "District"])

        new_farmer.to_csv(FARMER_DB, mode="a", header=False, index=False)

        st.session_state.registered = True
        st.session_state.farmer = {
            "Name": name,
            "Mobile": mobile,
            "Village": village_reg,
            "District": district
        }

        st.sidebar.success("✅ Registration Successful!")

    else:
        st.sidebar.error("⚠ Fill all details")

# Stop dashboard if not registered
if not st.session_state.registered:
    st.title("🔒 Please Register to Access Dashboard")
    st.stop()

farmer = st.session_state.farmer

# ==========================================================
# HEADER SECTION
# ==========================================================

st.markdown(
    f"""
    <div class="overlay">
        <h1 style="text-align:center; color:white;">🥭 Farmer Profit Intelligence System</h1>
        <h4 style="text-align:center; color:lightgreen;">
            Welcome {farmer['Name']}
        </h4>
    </div>
    """,
    unsafe_allow_html=True
)

# ==========================================================
# FARMER DETAILS SECTION
# ==========================================================

st.markdown(
    f"""
    <div class="overlay">
        <h3 style="color:white;">👨‍🌾 Farmer Details</h3>
        <p style="color:white;">
        <b>Name:</b> {farmer['Name']} <br>
        <b>Mobile:</b> {farmer['Mobile']} <br>
        <b>Village:</b> {farmer['Village']} <br>
        <b>District:</b> {farmer['District']}
        </p>
    </div>
    """,
    unsafe_allow_html=True
)

# ==========================================================
# LOAD MARKET DATA
# ==========================================================

@st.cache_data
def load_data():
    df = pd.read_csv("cleaned_price_data.csv")
    df["today_price(rs/kg)"] = pd.to_numeric(df["today_price(rs/kg)"], errors="coerce").fillna(0)
    return df

df = load_data()

# ==========================================================
# ANALYSIS PANEL
# ==========================================================

st.sidebar.title("📊 Market Analysis")

TONNES = st.sidebar.number_input("Enter Quantity (Tonnes)", min_value=1, value=10)

if st.sidebar.button("Run Smart Analysis"):

    df["Revenue"] = df["today_price(rs/kg)"] * TONNES * 1000
    df["TransportCost"] = 8000
    df["NetProfit"] = df["Revenue"] - df["TransportCost"]

    top10 = df.sort_values("NetProfit", ascending=False).head(10)
    best = top10.iloc[0]

    st.markdown('<div class="overlay">', unsafe_allow_html=True)

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Base Price (₹/kg)", best["today_price(rs/kg)"])
    col2.metric("Total Revenue (₹)", f"{int(best['Revenue']):,}")
    col3.metric("Best Market", best["market"])
    col4.metric("Best Profit (₹)", f"{int(best['NetProfit']):,}")

    st.markdown("### 📈 Profit Comparison")

    fig = px.bar(top10,
                 x="market",
                 y="NetProfit",
                 color="NetProfit",
                 color_continuous_scale="greens")

    st.plotly_chart(fig, use_container_width=True)

    st.markdown("### 📋 Top 10 Markets")

    st.dataframe(top10[["market", "NetProfit"]], use_container_width=True)

    st.markdown("</div>", unsafe_allow_html=True)

