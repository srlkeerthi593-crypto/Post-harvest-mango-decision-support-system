# ============================================================
# 🥭 FARMER PROFIT INTELLIGENCE SYSTEM
# 🚀 PHD-LEVEL PREMIUM VERSION
# ============================================================

import streamlit as st
import pandas as pd
import numpy as np
import folium
import requests
from streamlit_folium import st_folium
import plotly.graph_objects as go
import plotly.express as px

st.set_page_config(layout="wide")

st.title("🥭 Mango Profit Intelligence System")
st.subheader("🚜 Advanced Smart Marketing Decision Engine")

# ---------------- LOAD DATA ----------------
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

# ---------------- HELPERS ----------------
def detect_lat_lon(df):
    lat, lon = None, None
    for c in df.columns:
        if "lat" in c: lat = c
        if "lon" in c or "long" in c: lon = c
    return lat, lon

def detect_name(df):
    for c in df.columns:
        if any(x in c for x in ["place","market","panchayat","mandal","name"]):
            return c
    return df.columns[0]

def haversine(lat1, lon1, lat2, lon2):
    R = 6371
    lat1, lon1, lat2, lon2 = map(np.radians,[lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = np.sin(dlat/2)**2 + np.cos(lat1)*np.cos(lat2)*np.sin(dlon/2)**2
    return R * 2*np.arcsin(np.sqrt(a))

# Real Road Distance using OSRM
def road_distance(lat1, lon1, lat2, lon2):
    try:
        url = f"http://router.project-osrm.org/route/v1/driving/{lon1},{lat1};{lon2},{lat2}?overview=full&geometries=geojson"
        response = requests.get(url, timeout=5).json()
        distance_km = response["routes"][0]["distance"] / 1000
        geometry = response["routes"][0]["geometry"]
        return distance_km, geometry
    except:
        return haversine(lat1, lon1, lat2, lon2), None

# ---------------- SIDEBAR ----------------
st.sidebar.header("👨‍🌾 Farmer Details")

farmer_name = st.sidebar.text_input("Farmer Name")
mobile = st.sidebar.text_input("Mobile Number")

village_name_col = detect_name(villages)
v_lat_col, v_lon_col = detect_lat_lon(villages)

selected_village = st.sidebar.selectbox(
    "Select Village",
    villages[village_name_col].unique()
)

variety = st.sidebar.selectbox(
    "Select Variety",
    ["Banganapalli","Totapuri","Neelam","Rasalu"]
)

quantity_qtl = st.sidebar.number_input("Quantity (Quintals)", min_value=1, value=10)

if "run" not in st.session_state:
    st.session_state.run = False

if st.sidebar.button("🚀 Run Premium Analysis"):
    st.session_state.run = True

# ---------------- VARIETY RULES ----------------
variety_acceptance = {
    "Mandi":["Banganapalli","Totapuri","Neelam","Rasalu"],
    "Processing":["Totapuri","Neelam"],
    "Pulp":["Totapuri"],
    "Pickle":["Totapuri","Rasalu"],
    "Local Export":["Banganapalli"],
    "Abroad Export":["Banganapalli"]
}

margin_map = {
    "Mandi":0,
    "Processing":0.03,
    "Pulp":0.04,
    "Pickle":0.025,
    "Local Export":0.05,
    "Abroad Export":0.07
}

# ---------------- MAIN ----------------
if st.session_state.run:

    st.markdown(f"## 🙏🥭 Namaste **{farmer_name}**")
    st.markdown("### 📊 Advanced Profit Intelligence Dashboard")

    village_row = villages[villages[village_name_col]==selected_village].iloc[0]
    v_lat = village_row[v_lat_col]
    v_lon = village_row[v_lon_col]

    mandi_data = prices.merge(geo,on="market",how="left")
    lat_m, lon_m = detect_lat_lon(mandi_data)
    mandi_data = mandi_data.dropna(subset=[lat_m,lon_m])

    mandi_data["distance"] = mandi_data.apply(
        lambda r: haversine(v_lat,v_lon,r[lat_m],r[lon_m]),axis=1)

    nearest = mandi_data.loc[mandi_data["distance"].idxmin()]
    base_price = nearest["today_price(rs/kg)"]

    results=[]
    routes_dict={}

    category_dfs = {
        "Mandi":mandi_data,
        "Processing":processing,
        "Pulp":pulp,
        "Pickle":pickle_units,
        "Local Export":local_export,
        "Abroad Export":abroad_export
    }

    for cat,df in category_dfs.items():

        if variety not in variety_acceptance[cat]:
            continue

        lat,lon = detect_lat_lon(df)
        name_col = "market" if cat=="Mandi" else detect_name(df)

        if lat is None: continue

        for _,row in df.iterrows():
            if pd.notnull(row[lat]) and pd.notnull(row[lon]):

                dist, geometry = road_distance(v_lat,v_lon,row[lat],row[lon])

                transport = (dist/10)*2000*quantity_qtl
                revenue = base_price*(1+margin_map[cat])*100*quantity_qtl
                net = revenue - transport

                results.append({
                    "Category":cat,
                    "Name":row[name_col],
                    "Distance_km":round(dist,2),
                    "Transport Cost":round(transport,2),
                    "Net Profit":round(net,2),
                    "Profit per KM":round(net/dist if dist>0 else 0,2),
                    "Lat":row[lat],
                    "Lon":row[lon]
                })

                routes_dict[row[name_col]] = geometry

    df_top10 = pd.DataFrame(results).sort_values(
        "Net Profit",ascending=False).head(10).reset_index(drop=True)

    df_top10["Rank"]=df_top10.index+1
    best=df_top10.iloc[0]

    # ---------------- METRICS ----------------
    c1,c2,c3,c4 = st.columns(4)
    c1.metric("💰 Base Price (₹/kg)",round(base_price,2))
    c2.metric("🥇 Best Option",best["Name"])
    c3.metric("🏆 Net Profit (₹)",best["Net Profit"])
    c4.metric("📦 Quantity (Qtl)",quantity_qtl)

    st.markdown("---")

    # ---------------- BAR GRAPH ----------------
    st.subheader("📊 Profit Comparison")

    fig = px.bar(df_top10.sort_values("Net Profit"),
                 x="Net Profit",
                 y="Name",
                 color="Category",
                 orientation="h",
                 text="Net Profit")

    fig.update_layout(height=750)
    fig.update_traces(textposition="outside")
    st.plotly_chart(fig,width="stretch")

    # ---------------- SCATTER ANALYSIS ----------------
    st.subheader("📈 Distance vs Profit Analysis")

    scatter = px.scatter(df_top10,
                         x="Distance_km",
                         y="Net Profit",
                         size="Transport Cost",
                         color="Category",
                         hover_name="Name")

    st.plotly_chart(scatter,width="stretch")

    # ---------------- MAP WITH REAL ROUTES ----------------
    st.subheader("🗺 Real Road Routes to Top 10")

    m = folium.Map(location=[v_lat,v_lon],zoom_start=9)

    folium.Marker([v_lat,v_lon],
                  popup="🏡 Village",
                  icon=folium.Icon(color="black")).add_to(m)

    for _,row in df_top10.iterrows():

        folium.Marker(
            [row["Lat"],row["Lon"]],
            popup=f"🥭 Rank {row['Rank']} - {row['Name']}",
            icon=folium.Icon(color="green")
        ).add_to(m)

        geometry = routes_dict.get(row["Name"])
        if geometry:
            folium.GeoJson(geometry,
                           style_function=lambda x: {"color":"orange","weight":4}).add_to(m)

    st_folium(m,width=1100,height=650)

    # ---------------- TABLE ----------------
    st.subheader("📋 Detailed Comparison Table")
    st.dataframe(df_top10)

    # ---------------- VARIETY LOGIC ----------------
    st.subheader("🧠 Variety Acceptance Logic")

    for cat,vals in variety_acceptance.items():
        if variety in vals:
            st.success(f"✔ {cat} accepts {variety}")
        else:
            st.error(f"✘ {cat} does NOT accept {variety}")
