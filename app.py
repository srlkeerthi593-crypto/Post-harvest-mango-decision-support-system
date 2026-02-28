# ==========================================================
# 🥭 FARMER PROFIT INTELLIGENCE SYSTEM (FINAL STABLE VERSION)
# Background + Registration + Real CSV Filtering
# ==========================================================

import streamlit as st
import pandas as pd
import os

st.set_page_config(layout="wide")

# ==========================================================
# 🔥 FORCE BACKGROUND IMAGE (WORKS ON STREAMLIT CLOUD)
# ==========================================================

BACKGROUND_IMAGE_URL = "PASTE_RAW_URL_HERE"

st.markdown(f"""
<style>
html, body, [data-testid="stAppViewContainer"] {{
    background: url("{BACKGROUND_IMAGE_URL}") no-repeat center center fixed;
    background-size: cover;
}}

[data-testid="stHeader"] {{
    background: transparent;
}}

.overlay {{
    background-color: rgba(0,0,0,0.85);
    padding: 30px;
    border-radius: 20px;
}}

h1,h2,h3,h4,h5,p,label {{
    color: white !important;
}}

[data-testid="stMetricValue"] {{
    color: #00FF7F !important;
    font-weight: bold;
}}
</style>
""", unsafe_allow_html=True)

# ==========================================================
# 👨‍🌾 FARMER REGISTRATION DATABASE
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
        new_data = pd.DataFrame([[name,mobile,village]],
                                columns=["Name","Mobile","Village"])
        new_data.to_csv(FARMER_DB, mode="a", header=False, index=False)

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
    st.title("🔒 Please Register First")
    st.stop()

farmer = st.session_state.farmer

# ==========================================================
# HEADER
# ==========================================================

st.markdown(f"""
<div class="overlay">
<h1 style="text-align:center;">🥭 Farmer Profit Intelligence System</h1>
<h4 style="text-align:center;">Smart Mango Marketing Decision Engine</h4>
<p style="text-align:center;">
Farmer: {farmer['Name']} | Village: {farmer['Village']} | Mobile: {farmer['Mobile']}
</p>
</div>
""", unsafe_allow_html=True)

# ==========================================================
# LOAD CSV DATA (FAST + SAFE)
# ==========================================================

@st.cache_data
def load_data():
    df = pd.read_csv("cleaned_price_data.csv")
    df.columns = df.columns.str.strip()
    df["revenue_type"] = df["revenue_type"].astype(str).str.strip()
    df["today_price(rs/kg)"] = pd.to_numeric(
        df["today_price(rs/kg)"], errors="coerce"
    ).fillna(0)
    return df

df = load_data()

# ==========================================================
# 🧠 VARIETY LOGIC (FROM YOUR ORIGINAL COLAB)
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
# MARKET ANALYSIS
# ==========================================================

st.sidebar.title("📊 Market Analysis")

variety = st.sidebar.selectbox(
    "Select Mango Variety",
    ["Banganapalli","Totapuri","Neelam","Rasalu"]
)

TONNES = st.sidebar.number_input("Enter Quantity (Tonnes)", 1, 100, 10)

if st.sidebar.button("Run Smart Analysis"):

    allowed_categories = []

    for category, varieties in variety_acceptance.items():
        if variety in varieties:
            allowed_categories.append(category)

    filtered_df = df[df["revenue_type"].isin(allowed_categories)]

    if filtered_df.empty:
        st.error("No suitable alternatives found for selected variety.")
        st.stop()

    # Profit Calculation
    filtered_df["Revenue"] = filtered_df["today_price(rs/kg)"] * TONNES * 1000
    filtered_df["TransportCost"] = 8000
    filtered_df["NetProfit"] = filtered_df["Revenue"] - filtered_df["TransportCost"]

    top10 = filtered_df.sort_values("NetProfit", ascending=False).head(10)

    best = top10.iloc[0]

    st.markdown('<div class="overlay">', unsafe_allow_html=True)

    col1,col2,col3,col4 = st.columns(4)

    col1.metric("Selected Variety", variety)
    col2.metric("Best Market", best["market"])
    col3.metric("Base Price (₹/kg)", best["today_price(rs/kg)"])
    col4.metric("Best Profit (₹)", f"{int(best['NetProfit']):,}")

    st.markdown("### ✅ Suitable Alternatives (From Your CSV)")

    st.dataframe(
        top10[["market","revenue_type","today_price(rs/kg)","NetProfit"]],
        use_container_width=True
    )

    st.markdown("</div>", unsafe_allow_html=True)
