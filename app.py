import streamlit as st
import pandas as pd
import numpy as np
import requests
import folium
from streamlit_folium import st_folium

# ============================================================
# 🎨 PAGE CONFIG
# ============================================================
st.set_page_config(page_title="Farmer Decision Support System", layout="wide")

st.markdown("""
<style>
[data-testid="stAppViewContainer"] {
    background-color: #f4f9f4;
}
h1, h2, h3 {
    font-weight: 800 !important;
}
.stMetric label {
    font-weight: bold !important;
}
</style>
""", unsafe_allow_html=True)

st.title("🥭 Farmer Profit Intelligence System")
st.markdown("### 🚀 Smart Mango Marketing Decision Engine")

# ============================================================
# 📂 LOAD DATA
# ============================================================
villages = pd.read_csv("Village data.csv")
prices = pd.read_csv("cleaned_price_data.csv")
geo = pd.read_csv("cleaned_geo_locations.csv")
processing = pd.read_csv("cleaned_processing_facilities.csv")
pulp = pd.read_csv("Pulp_units_merged_lat_long.csv")
pickle_units = pd.read_csv("cleaned_pickle_units.csv")
local_export = pd.read_csv("cleaned_local_export.csv")
abroad_export = pd.read_csv("cleaned_abroad_export.csv")

for df in [villages, prices, geo, processing,
           pulp, pickle_units, local_export, abroad_export]:
    df.columns = df.columns.str.strip().str.lower()

# ============================================================
# ⚙ CONFIG
# ============================================================
RADIUS_KM = 80
TRANSPORT_RATE = 2000   # per 10km per tonne
SPOILAGE_PER_10KM = 0.004
HANDLING_RISK = 0.002

# ============================================================
# 👨‍🌾 FARMER INPUT
# ============================================================
st.sidebar.header("📝 Farmer Details")

farmer_name = st.sidebar.text_input("👨‍🌾 Farmer Name")
mobile = st.sidebar.text_input("📱 Mobile Number")

village_col = [c for c in villages.columns if "village" in c][0]
village_name = st.sidebar.selectbox("🏡 Select Village",
                                    villages[village_col].dropna().unique())

variety = st.sidebar.selectbox("🥭 Select Mango Variety",
                               ["Banganapalli","Totapuri","Neelam","Rasalu"])

quantity = st.sidebar.number_input("📦 Quantity (Tonnes)", min_value=1)

run = st.sidebar.button("🚀 Run Smart Analysis")

# ============================================================
# 📍 HELPER FUNCTIONS
# ============================================================
def haversine(lat1, lon1, lat2, lon2):
    R = 6371
    lat1, lon1, lat2, lon2 = map(np.radians,[lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = np.sin(dlat/2)**2 + np.cos(lat1)*np.cos(lat2)*np.sin(dlon/2)**2
    return R * 2*np.arcsin(np.sqrt(a))

# ============================================================
# 🚀 RUN LOGIC
# ============================================================
if run:

    village_row = villages[villages[village_col] == village_name].iloc[0]
    v_lat = village_row[[c for c in villages.columns if "lat" in c][0]]
    v_lon = village_row[[c for c in villages.columns if "lon" in c][0]]

    # ========================================================
    # 🌱 VARIETY LOGIC
    # ========================================================
    variety_acceptance = {
        "Mandi": ["Banganapalli","Totapuri","Neelam","Rasalu"],
        "Processing": ["Totapuri","Neelam"],
        "Pulp": ["Totapuri"],
        "Pickle": ["Totapuri","Rasalu"],
        "Local Export": ["Banganapalli"],
        "Abroad Export": ["Banganapalli"]
    }

    st.subheader("🔎 Variety Filtering Logic")
    for cat, vals in variety_acceptance.items():
        if variety in vals:
            st.success(f"✔ {cat} ACCEPTS {variety}")
        else:
            st.error(f"✘ {cat} NOT suitable")

    # ========================================================
    # 📈 BASE PRICE
    # ========================================================
    mandi_data = prices.merge(geo, on="market", how="left")
    mandi_data = mandi_data.dropna(subset=["latitude","longitude"])

    mandi_data["distance"] = mandi_data.apply(
        lambda r: haversine(v_lat,v_lon,r["latitude"],r["longitude"]), axis=1)

    nearest = mandi_data.loc[mandi_data["distance"].idxmin()]
    base_price = nearest["today_price(rs/kg)"]

    st.info(f"📌 Nearest Market: **{nearest['market']}**")
    st.info(f"💰 Base Price: ₹ {base_price} / kg")

    # ========================================================
    # 📦 COLLECT ALTERNATIVES
    # ========================================================
    all_options = []

    datasets = {
        "Mandi": mandi_data,
        "Processing": processing,
        "Pulp": pulp,
        "Pickle": pickle_units,
        "Local Export": local_export,
        "Abroad Export": abroad_export
    }

    for cat, df in datasets.items():
        if variety not in variety_acceptance[cat]:
            continue

        name_col = [c for c in df.columns if any(x in c for x in ["name","market","firm","facility"])][0]
        lat_col = [c for c in df.columns if "lat" in c][0]
        lon_col = [c for c in df.columns if "lon" in c][0]

        for _, row in df.iterrows():
            if pd.notnull(row[lat_col]) and pd.notnull(row[lon_col]):
                km = haversine(v_lat,v_lon,row[lat_col],row[lon_col])
                if km <= RADIUS_KM:
                    adjusted_price = base_price
                    revenue = adjusted_price * 1000 * quantity
                    transport = (km/10)*TRANSPORT_RATE*quantity
                    risk = revenue*((SPOILAGE_PER_10KM*(km/10))+HANDLING_RISK)
                    net = revenue - transport - risk

                    all_options.append({
                        "Type":cat,
                        "Name":row[name_col],
                        "Distance_km":round(km,2),
                        "Net_Profit":round(net,2),
                        "Lat":row[lat_col],
                        "Lon":row[lon_col]
                    })

    df = pd.DataFrame(all_options)

    df_top10 = df.sort_values("Distance_km").head(10).reset_index(drop=True)
    df_top10["Rank"] = df_top10.index+1

    # ========================================================
    # 🏆 BEST OPTION
    # ========================================================
    best = df_top10.loc[df_top10["Net_Profit"].idxmax()]

    col1, col2 = st.columns(2)
    col1.metric("🏆 Most Profitable", best["Name"])
    col2.metric("💰 Net Profit (₹)", best["Net_Profit"])

    # ========================================================
    # 📊 BAR GRAPH
    # ========================================================
    st.subheader("📊 Profit Comparison")
    st.bar_chart(df_top10.set_index("Name")["Net_Profit"])

    # ========================================================
    # 🗺 MAP
    # ========================================================
    st.subheader("🗺 Top 10 Location Map")

    m = folium.Map(location=[v_lat, v_lon], zoom_start=9)

    folium.Marker([v_lat,v_lon], tooltip="Village",
                  icon=folium.Icon(color="black")).add_to(m)

    for _, row in df_top10.iterrows():
        folium.Marker(
            [row["Lat"],row["Lon"]],
            tooltip=f"Rank {row['Rank']} - {row['Name']}",
            icon=folium.Icon(color="green")
        ).add_to(m)

    st_folium(m, width=1100, height=500)

    # ========================================================
    # 📋 TABLE
    # ========================================================
    st.subheader("🏅 Ranked Top 10 Alternatives")
    st.dataframe(df_top10)
