# ==========================================================
# 🥭 FARMER PROFIT INTELLIGENCE SYSTEM
# Mango Background + Variety Based Alternatives
# ==========================================================

import streamlit as st
import pandas as pd
import numpy as np
import base64
import os

st.set_page_config(layout="wide")

# ==========================================================
# BACKGROUND IMAGE (YOUR MANGO TREES IMAGE)
# ==========================================================

def set_bg(image_file):
    with open(image_file, "rb") as f:
        data = f.read()
    encoded = base64.b64encode(data).decode()

    st.markdown(
        f"""
        <style>
        .stApp {{
            background-image: url("data:image/jpg;base64,{encoded}");
            background-size: cover;
            background-position: center;
            background-attachment: fixed;
        }}

        .main-overlay {{
            background-color: rgba(0, 0, 0, 0.75);
            padding: 25px;
            border-radius: 15px;
        }}

        h1,h2,h3,h4,h5,p {{
            color: white;
        }}
        </style>
        """,
        unsafe_allow_html=True
    )

set_bg("mango_bg.jpg")

# ==========================================================
# FARMER REGISTRATION (MANDATORY)
# ==========================================================

FARMER_DB = "farmers_database.csv"

if not os.path.exists(FARMER_DB):
    pd.DataFrame(columns=["Name","Mobile","Village"]).to_csv(FARMER_DB, index=False)

if "registered" not in st.session_state:
    st.session_state.registered = False

st.sidebar.title("👨‍🌾 Farmer Registration")

name = st.sidebar.text_input("Farmer Name")
mobile = st.sidebar.text_input("Mobile Number")
village = st.sidebar.text_input("Village")

if st.sidebar.button("Register Farmer"):
    if name and mobile and village:
        new = pd.DataFrame([[name,mobile,village]],
                           columns=["Name","Mobile","Village"])
        new.to_csv(FARMER_DB, mode="a", header=False, index=False)

        st.session_state.registered = True
        st.session_state.farmer = {"Name":name,"Mobile":mobile,"Village":village}
        st.sidebar.success("Registration Successful")
    else:
        st.sidebar.error("Fill all details")

if not st.session_state.registered:
    st.title("🔒 Please Register to Access Dashboard")
    st.stop()

farmer = st.session_state.farmer

# ==========================================================
# HEADER
# ==========================================================

st.markdown(
    f"""
    <div class="main-overlay">
    <h1 style="text-align:center;">🥭 Farmer Profit Intelligence System</h1>
    <h4 style="text-align:center;">Welcome {farmer['Name']}</h4>
    </div>
    """,
    unsafe_allow_html=True
)

# ==========================================================
# LOAD CSV DATA
# ==========================================================

@st.cache_data
def load_data():
    df = pd.read_csv("cleaned_price_data.csv")
    df["today_price(rs/kg)"] = pd.to_numeric(df["today_price(rs/kg)"], errors="coerce").fillna(0)
    return df

df = load_data()

# ==========================================================
# ANALYSIS SECTION
# ==========================================================

st.sidebar.title("📊 Market Analysis")

variety = st.sidebar.selectbox("Select Mango Variety",
                               df["place"].unique())

TONNES = st.sidebar.number_input("Enter Quantity (Tonnes)", 1, 100, 10)

if st.sidebar.button("Run Smart Analysis"):

    # Filter by selected variety (using CSV values)
    variety_df = df[df["place"] == variety]

    if variety_df.empty:
        st.error("No data found for selected variety")
        st.stop()

    variety_df["Revenue"] = variety_df["today_price(rs/kg)"] * TONNES * 1000
    variety_df["TransportCost"] = 8000
    variety_df["NetProfit"] = variety_df["Revenue"] - variety_df["TransportCost"]

    top10 = variety_df.sort_values("NetProfit", ascending=False).head(10)

    best = top10.iloc[0]

    st.markdown('<div class="main-overlay">', unsafe_allow_html=True)

    # ======================================================
    # KPI CARDS
    # ======================================================

    col1,col2,col3,col4 = st.columns(4)

    col1.metric("Base Price (₹/kg)", best["today_price(rs/kg)"])
    col2.metric("Total Revenue (₹)", f"{int(best['Revenue']):,}")
    col3.metric("Best Market", best["market"])
    col4.metric("Best Profit (₹)", f"{int(best['NetProfit']):,}")

    # ======================================================
    # SUITABLE ALTERNATIVES
    # ======================================================

    st.markdown("### ✅ Suitable Market Alternatives")

    st.dataframe(
        top10[["market","today_price(rs/kg)","NetProfit"]],
        use_container_width=True
    )

    st.markdown("</div>", unsafe_allow_html=True)
