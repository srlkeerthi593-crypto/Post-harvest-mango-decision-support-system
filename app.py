# ==========================================================
# 🥭 FARMER PROFIT INTELLIGENCE SYSTEM
# Mango Background + Registration + Variety Logic
# Uses REAL CSV Names (No Renaming)
# ==========================================================

import streamlit as st
import pandas as pd
import numpy as np
import base64
import os

st.set_page_config(layout="wide")

# ==========================================================
# BACKGROUND IMAGE (Your Mango Trees Image)
# Make sure mango_bg.jpg is in same folder as app.py
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

        .overlay {{
            background-color: rgba(0,0,0,0.75);
            padding: 25px;
            border-radius: 15px;
        }}

        h1,h2,h3,h4,h5,p,label {{
            color: white !important;
        }}
        </style>
        """,
        unsafe_allow_html=True
    )

set_bg("mango_bg.jpg")

# ==========================================================
# FARMER DATABASE
# ==========================================================

FARMER_DB = "farmers_database.csv"

if not os.path.exists(FARMER_DB):
    pd.DataFrame(columns=["Name","Mobile","Village"]).to_csv(FARMER_DB, index=False)

if "registered" not in st.session_state:
    st.session_state.registered = False

# ==========================================================
# SIDEBAR REGISTRATION
# ==========================================================

st.sidebar.title("👨‍🌾 Farmer Registration")

name = st.sidebar.text_input("Farmer Name")
mobile = st.sidebar.text_input("Mobile Number")
village = st.sidebar.text_input("Village")

if st.sidebar.button("Register Farmer"):

    if name and mobile and village:

        new_farmer = pd.DataFrame([[name,mobile,village]],
                                  columns=["Name","Mobile","Village"])

        new_farmer.to_csv(FARMER_DB, mode="a", header=False, index=False)

        st.session_state.registered = True
        st.session_state.farmer = {
            "Name": name,
            "Mobile": mobile,
            "Village": village
        }

        st.sidebar.success("Registration Successful")

    else:
        st.sidebar.error("Please fill all details")

if not st.session_state.registered:
    st.title("🔒 Please Register to Access Dashboard")
    st.stop()

farmer = st.session_state.farmer

# ==========================================================
# HEADER
# ==========================================================

st.markdown(
    f"""
    <div class="overlay">
    <h1 style="text-align:center;">🥭 Farmer Profit Intelligence System</h1>
    <h4 style="text-align:center;">Welcome {farmer['Name']}</h4>
    <p style="text-align:center;">
        Village: {farmer['Village']} | Mobile: {farmer['Mobile']}
    </p>
    </div>
    """,
    unsafe_allow_html=True
)

# ==========================================================
# LOAD YOUR CSV DATA (REAL DATA)
# ==========================================================

@st.cache_data
def load_data():
    df = pd.read_csv("cleaned_price_data.csv")
    df.columns = df.columns.str.strip()
    df["today_price(rs/kg)"] = pd.to_numeric(df["today_price(rs/kg)"], errors="coerce").fillna(0)
    return df

df = load_data()

# ==========================================================
# VARIETY ACCEPTANCE LOGIC (FROM YOUR COLAB CODE)
# ==========================================================

variety_acceptance = {
    "Mandi": ["Banganapalli","Totapuri","Neelam","Rasalu"],
    "Processing": ["Totapuri","Neelam"],
    "Pulp": ["Totapuri"],
    "Pickle": ["Totapuri","Rasalu"],
    "Local Export": ["Banganapalli"],
    "Abroad Export": ["Banganapalli"]
}

# ==========================================================
# ANALYSIS SECTION
# ==========================================================

st.sidebar.title("📊 Market Analysis")

variety = st.sidebar.selectbox(
    "Select Mango Variety",
    ["Banganapalli","Totapuri","Neelam","Rasalu"]
)

TONNES = st.sidebar.number_input("Enter Quantity (Tonnes)", 1, 100, 10)

if st.sidebar.button("Run Smart Analysis"):

    # Step 1: Determine allowed categories
    allowed_categories = []

    for category, varieties in variety_acceptance.items():
        if variety in varieties:
            allowed_categories.append(category)

    # Step 2: Filter using revenue_type column from YOUR CSV
    filtered_df = df[df["revenue_type"].isin(allowed_categories)]

    if filtered_df.empty:
        st.error("No suitable markets available for selected variety.")
        st.stop()

    # Step 3: Profit Calculation
    filtered_df["Revenue"] = filtered_df["today_price(rs/kg)"] * TONNES * 1000
    filtered_df["TransportCost"] = 8000
    filtered_df["NetProfit"] = filtered_df["Revenue"] - filtered_df["TransportCost"]

    top10 = filtered_df.sort_values("NetProfit", ascending=False).head(10)

    best = top10.iloc[0]

    st.markdown('<div class="overlay">', unsafe_allow_html=True)

    # KPI Cards
    col1,col2,col3,col4 = st.columns(4)

    col1.metric("Selected Variety", variety)
    col2.metric("Best Market", best["market"])
    col3.metric("Base Price (₹/kg)", best["today_price(rs/kg)"])
    col4.metric("Best Profit (₹)", f"{int(best['NetProfit']):,}")

    st.markdown("### ✅ Suitable Alternatives (Based on Variety Logic)")

    # IMPORTANT: Using EXACT names from CSV
    st.dataframe(
        top10[["market","revenue_type","today_price(rs/kg)","NetProfit"]],
        use_container_width=True
    )

    st.markdown("</div>", unsafe_allow_html=True)
