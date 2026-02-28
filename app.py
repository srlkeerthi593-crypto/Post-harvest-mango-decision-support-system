import streamlit as st
import pandas as pd
import numpy as np
import requests
import folium
from streamlit_folium import st_folium

# ==========================================================
# PAGE SETTINGS
# ==========================================================
st.set_page_config(layout="wide")

st.markdown("""
<style>
[data-testid="stAppViewContainer"] {
    background-color: #f4f7f2;
}
h1,h2,h3,h4 {
    font-weight:900 !important;
}
</style>
""", unsafe_allow_html=True)

st.title("🥭 Farmer Profit Intelligence System")
st.markdown("### 🚀 Smart Mango Marketing Decision Engine")

# ==========================================================
# SAFE DATA LOADER
# ==========================================================
@st.cache_data
def load_all():
    files = {
        "villages":"Village data.csv",
        "prices":"cleaned_price_data.csv",
        "geo":"cleaned_geo_locations.csv",
        "processing":"cleaned_processing_facilities.csv",
        "pulp":"Pulp_units_merged_lat_long.csv",
        "pickle":"cleaned_pickle_units.csv",
        "local":"cleaned_local_export.csv",
        "abroad":"cleaned_abroad_export.csv"
    }

    data = {}
    for key,path in files.items():
        df = pd.read_csv(path)
        df.columns = df.columns.str.strip().str.lower()
        data[key] = df
    return data

data = load_all()

# ==========================================================
# CONFIG
# ==========================================================
RADIUS_KM = 80
TRANSPORT_RATE = 2000
SPOILAGE_PER_10KM = 0.004
HANDLING_RISK = 0.002

# ==========================================================
# HELPER FUNCTIONS
# ==========================================================
def haversine(lat1, lon1, lat2, lon2):
    R = 6371
    lat1, lon1, lat2, lon2 = map(np.radians,[lat1, lon1, lat2, lon2])
    dlat = lat2-lat1
    dlon = lon2-lon1
    a = np.sin(dlat/2)**2 + np.cos(lat1)*np.cos(lat2)*np.sin(dlon/2)**2
    return R*2*np.arcsin(np.sqrt(a))

def detect_cols(df):
    name = [c for c in df.columns if any(x in c for x in ["name","market","firm","facility","hub","village"])]
    lat = [c for c in df.columns if "lat" in c]
    lon = [c for c in df.columns if "lon" in c]
    if name and lat and lon:
        return name[0],lat[0],lon[0]
    return None,None,None

# ==========================================================
# SIDEBAR INPUT
# ==========================================================
st.sidebar.header("📝 Farmer Details")

farmer_name = st.sidebar.text_input("👨‍🌾 Farmer Name")
mobile = st.sidebar.text_input("📱 Mobile Number")

village_df = data["villages"]
village_col = [c for c in village_df.columns if "village" in c][0]

village_name = st.sidebar.selectbox("🏡 Select Village",
                                    village_df[village_col].dropna().unique())

variety = st.sidebar.selectbox("🥭 Mango Variety",
                               ["Banganapalli","Totapuri","Neelam","Rasalu"])

quantity = st.sidebar.number_input("📦 Quantity (Tonnes)", min_value=1)

run = st.sidebar.button("🚀 Run Smart Analysis")

# ==========================================================
# RUN SYSTEM
# ==========================================================
if run:

    # ------------------------------------------------------
    # GET VILLAGE LOCATION
    # ------------------------------------------------------
    village_row = village_df[village_df[village_col]==village_name]
    if village_row.empty:
        st.error("Village not found in dataset")
        st.stop()

    v_lat = village_row[[c for c in village_df.columns if "lat" in c][0]].values[0]
    v_lon = village_row[[c for c in village_df.columns if "lon" in c][0]].values[0]

    # ------------------------------------------------------
    # VARIETY LOGIC
    # ------------------------------------------------------
    variety_acceptance = {
        "Mandi": ["Banganapalli","Totapuri","Neelam","Rasalu"],
        "Processing": ["Totapuri","Neelam"],
        "Pulp": ["Totapuri"],
        "Pickle": ["Totapuri","Rasalu"],
        "Local Export": ["Banganapalli"],
        "Abroad Export": ["Banganapalli"]
    }

    st.subheader("🔎 Variety Filtering Logic")
    for cat,vals in variety_acceptance.items():
        if variety in vals:
            st.success(f"✔ {cat} ACCEPTS {variety}")
        else:
            st.error(f"✘ {cat} NOT Suitable")

    # ------------------------------------------------------
    # BASE PRICE
    # ------------------------------------------------------
    prices = data["prices"]
    geo = data["geo"]

    if "market" not in prices.columns:
        st.error("Market column missing in price dataset")
        st.stop()

    mandi = prices.merge(geo,on="market",how="left")
    mandi = mandi.dropna(subset=["latitude","longitude"])

    mandi["distance"] = mandi.apply(
        lambda r:haversine(v_lat,v_lon,r["latitude"],r["longitude"]),axis=1)

    if mandi.empty:
        st.error("No mandi data available")
        st.stop()

    nearest = mandi.loc[mandi["distance"].idxmin()]
    base_price = nearest["today_price(rs/kg)"]

    st.info(f"📍 Nearest Market: {nearest['market']}")
    st.info(f"💰 Base Price: ₹ {base_price}/kg")

    # ------------------------------------------------------
    # COLLECT ALL OPTIONS
    # ------------------------------------------------------
    datasets = {
        "Mandi":mandi,
        "Processing":data["processing"],
        "Pulp":data["pulp"],
        "Pickle":data["pickle"],
        "Local Export":data["local"],
        "Abroad Export":data["abroad"]
    }

    category_margin = {
        "Mandi":0,
        "Processing":0.03,
        "Pulp":0.04,
        "Pickle":0.025,
        "Local Export":0.05,
        "Abroad Export":0.07
    }

    results = []

    for cat,df in datasets.items():

        if variety not in variety_acceptance[cat]:
            continue

        name_col,lat_col,lon_col = detect_cols(df)
        if not name_col:
            continue

        for _,row in df.iterrows():
            if pd.notnull(row[lat_col]) and pd.notnull(row[lon_col]):

                km = haversine(v_lat,v_lon,row[lat_col],row[lon_col])
                if km > RADIUS_KM:
                    continue

                adjusted_price = base_price*(1+category_margin[cat])
                revenue = adjusted_price*1000*quantity
                transport = (km/10)*TRANSPORT_RATE*quantity
                risk = revenue*((SPOILAGE_PER_10KM*(km/10))+HANDLING_RISK)
                net = revenue-transport-risk

                results.append({
                    "Type":cat,
                    "Name":row[name_col],
                    "Distance_km":round(km,2),
                    "Net_Profit":round(net,2),
                    "Lat":row[lat_col],
                    "Lon":row[lon_col]
                })

    df = pd.DataFrame(results)

    if df.empty:
        st.error("No alternatives found within radius.")
        st.stop()

    df_top10 = df.sort_values("Distance_km").head(10).reset_index(drop=True)
    df_top10["Rank"]=df_top10.index+1

    # ------------------------------------------------------
    # BEST OPTION
    # ------------------------------------------------------
    best = df_top10.loc[df_top10["Net_Profit"].idxmax()]

    col1,col2,col3 = st.columns(3)
    col1.metric("🏆 Best Alternative",best["Name"])
    col2.metric("💰 Net Profit (₹)",best["Net_Profit"])
    col3.metric("📦 Quantity (Tonnes)",quantity)

    # ------------------------------------------------------
    # BAR GRAPH
    # ------------------------------------------------------
    st.subheader("📊 Profit Comparison (Top 10)")
    st.bar_chart(df_top10.set_index("Name")["Net_Profit"])

    # ------------------------------------------------------
    # MAP
    # ------------------------------------------------------
    st.subheader("🗺 Market Location Map")

    m = folium.Map(location=[v_lat,v_lon],zoom_start=10)
    folium.Marker([v_lat,v_lon],tooltip="Village",
                  icon=folium.Icon(color="black")).add_to(m)

    for _,row in df_top10.iterrows():
        folium.Marker(
            [row["Lat"],row["Lon"]],
            tooltip=f"Rank {row['Rank']} - {row['Name']}",
            icon=folium.Icon(color="green")
        ).add_to(m)

    st_folium(m,width=1100,height=500)

    st.subheader("🏅 Ranked Top 10 Alternatives")
    st.dataframe(df_top10)
