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
    background-color: #f5f9f4;
}
h1, h2, h3 {
    font-weight: 900 !important;
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
@st.cache_data
def load_data():
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

    return villages, prices, geo, processing, pulp, pickle_units, local_export, abroad_export

villages, prices, geo, processing, pulp, pickle_units, local_export, abroad_export = load_data()

# ============================================================
# ⚙ CONFIG
# ============================================================
RADIUS_KM = 80
TRANSPORT_RATE = 2000
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

variety = st.sidebar.selectbox("🥭 Mango Variety",
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

def detect_cols(df):
    name = [c for c in df.columns if any(x in c for x in ["name","market","firm","facility","hub","place"])]
    lat = [c for c in df.columns if "lat" in c]
    lon = [c for c in df.columns if "lon" in c]
    return name[0], lat[0], lon[0]

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
            st.error(f"✘ {cat} NOT Suitable")

    # ========================================================
    # 📈 BASE PRICE
    # ========================================================
    mandi_data = prices.merge(geo, on="market", how="left")
    mandi_data = mandi_data.dropna(subset=["latitude","longitude"])

    mandi_data["distance"] = mandi_data.apply(
        lambda r: haversine(v_lat,v_lon,r["latitude"],r["longitude"]), axis=1)

    nearest = mandi_data.loc[mandi_data["distance"].idxmin()]
    base_price = nearest["today_price(rs/kg)"]

    st.info(f"📍 Nearest Market: **{nearest['market']}**")
    st.info(f"💰 Base Price: ₹ {base_price} / kg")

    # ========================================================
    # 📦 COLLECT OPTIONS
    # ========================================================
    datasets = {
        "Mandi": mandi_data,
        "Processing": processing,
        "Pulp": pulp,
        "Pickle": pickle_units,
        "Local Export": local_export,
        "Abroad Export": abroad_export
    }

    category_params = {
        "Mandi": {"margin":0, "color":"blue"},
        "Processing": {"margin":0.03, "color":"orange"},
        "Pulp": {"margin":0.04, "color":"purple"},
        "Pickle": {"margin":0.025, "color":"cadetblue"},
        "Local Export": {"margin":0.05, "color":"darkgreen"},
        "Abroad Export": {"margin":0.07, "color":"red"},
    }

    results = []

    for cat, df in datasets.items():
        if variety not in variety_acceptance[cat]:
            continue

        name_col, lat_col, lon_col = detect_cols(df)

        for _, row in df.iterrows():
            if pd.notnull(row[lat_col]) and pd.notnull(row[lon_col]):

                try:
                    route = requests.get(
                        f"http://router.project-osrm.org/route/v1/driving/"
                        f"{v_lon},{v_lat};{row[lon_col]},{row[lat_col]}"
                        f"?overview=false", timeout=10).json()

                    if "routes" in route:
                        km = route["routes"][0]["distance"]/1000
                    else:
                        km = haversine(v_lat,v_lon,row[lat_col],row[lon_col])
                except:
                    km = haversine(v_lat,v_lon,row[lat_col],row[lon_col])

                if km > RADIUS_KM:
                    continue

                margin = category_params[cat]["margin"]

                adjusted_price = base_price * (1 + margin)
                revenue = adjusted_price * 1000 * quantity
                transport = (km/10)*TRANSPORT_RATE*quantity
                risk = revenue*((SPOILAGE_PER_10KM*(km/10))+HANDLING_RISK)
                net = revenue - transport - risk

                results.append({
                    "Type":cat,
                    "Name":row[name_col],
                    "Distance_km":round(km,2),
                    "Net_Profit":round(net,2),
                    "Lat":row[lat_col],
                    "Lon":row[lon_col],
                    "Color":category_params[cat]["color"]
                })

    df = pd.DataFrame(results)

    df_top10 = df.sort_values("Distance_km").head(10).reset_index(drop=True)
    df_top10["Rank"] = df_top10.index+1

    # ========================================================
    # 🏆 BEST OPTION
    # ========================================================
    best = df_top10.loc[df_top10["Net_Profit"].idxmax()]

    col1, col2 = st.columns(2)
    col1.metric("🏆 Most Profitable Option", best["Name"])
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

    m = folium.Map(location=[v_lat,v_lon], zoom_start=10)

    folium.Marker([v_lat,v_lon],
                  popup=f"Village: {village_name}",
                  icon=folium.Icon(color="black")).add_to(m)

    for _, row in df_top10.iterrows():
        folium.Marker(
            [row["Lat"],row["Lon"]],
            popup=f"Rank {row['Rank']}<br>{row['Type']}<br>{row['Name']}",
            icon=folium.Icon(color=row["Color"])
        ).add_to(m)

    st_folium(m, width=1100, height=500)

    st.subheader("🏅 Ranked Top 10 Alternatives")
    st.dataframe(df_top10)
