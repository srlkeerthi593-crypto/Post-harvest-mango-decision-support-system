# ============================================================
# 🥭 FARMER PROFIT INTELLIGENCE SYSTEM
# 🧠 AI PREDICTION MODE ACTIVATED
# ============================================================

import streamlit as st
import pandas as pd
import numpy as np
import folium
import requests
from streamlit_folium import st_folium
import plotly.express as px
from sklearn.preprocessing import MinMaxScaler

st.set_page_config(layout="wide")

st.title("🥭 Mango Profit Intelligence System")
st.subheader("🧠 AI-Powered Smart Decision Engine")

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

def road_distance(lat1, lon1, lat2, lon2):
    try:
        url = f"http://router.project-osrm.org/route/v1/driving/{lon1},{lat1};{lon2},{lat2}?overview=false"
        r = requests.get(url, timeout=5).json()
        return r["routes"][0]["distance"] / 1000
    except:
        return haversine(lat1, lon1, lat2, lon2)

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

if st.sidebar.button("🚀 Run AI Analysis"):

    st.markdown(f"## 🙏🥭 Namaste **{farmer_name}**")
    st.markdown("### 🤖 AI Smart Profit Dashboard Activated")

    village_row = villages[villages[village_name_col]==selected_village].iloc[0]
    v_lat = village_row[v_lat_col]
    v_lon = village_row[v_lon_col]

    mandi_data = prices.merge(geo,on="market",how="left")
    lat_m, lon_m = detect_lat_lon(mandi_data)
    mandi_data = mandi_data.dropna(subset=[lat_m,lon_m])

    mandi_data["distance"] = mandi_data.apply(
        lambda r: haversine(v_lat,v_lon,r[lat_m],r[lon_m]),axis=1)

    nearest = mandi_data.loc[mandi_data["distance"].idxmin()]

    today_price = nearest["today_price(rs/kg)"]
    yesterday_price = nearest["yesterday_price(rs/kg)"]

    # --------- AI PRICE PREDICTION ----------
    trend = today_price - yesterday_price
    predicted_price = today_price + (0.6 * trend)

    st.metric("📈 AI Predicted Tomorrow Price (₹/kg)", round(predicted_price,2))

    margin_map = {
        "Mandi":0,
        "Processing":0.03,
        "Pulp":0.04,
        "Pickle":0.025,
        "Local Export":0.05,
        "Abroad Export":0.07
    }

    category_dfs = {
        "Mandi":mandi_data,
        "Processing":processing,
        "Pulp":pulp,
        "Pickle":pickle_units,
        "Local Export":local_export,
        "Abroad Export":abroad_export
    }

    results=[]

    for cat,df in category_dfs.items():

        lat,lon = detect_lat_lon(df)
        name_col = "market" if cat=="Mandi" else detect_name(df)

        if lat is None: continue

        for _,row in df.iterrows():
            if pd.notnull(row[lat]):

                dist = road_distance(v_lat,v_lon,row[lat],row[lon])
                transport = (dist/10)*2000*quantity_qtl

                spoilage = 0.005*(dist/10)
                revenue = predicted_price*(1+margin_map[cat])*100*quantity_qtl
                revenue_after_spoil = revenue*(1-spoilage)

                net = revenue_after_spoil - transport

                results.append({
                    "Category":cat,
                    "Name":row[name_col],
                    "Distance_km":round(dist,2),
                    "Transport Cost":round(transport,2),
                    "Net Profit":round(net,2),
                    "Spoilage %":round(spoilage*100,2)
                })

    df_ai = pd.DataFrame(results).sort_values(
        "Net Profit",ascending=False).head(10).reset_index(drop=True)

    # --------- AI SMART SCORE ----------
    scaler = MinMaxScaler()

    df_ai["Profit_N"] = scaler.fit_transform(df_ai[["Net Profit"]])
    df_ai["Distance_N"] = 1 - scaler.fit_transform(df_ai[["Distance_km"]])
    df_ai["Transport_N"] = 1 - scaler.fit_transform(df_ai[["Transport Cost"]])

    df_ai["AI Score"] = (
        0.4*df_ai["Profit_N"] +
        0.3*df_ai["Distance_N"] +
        0.3*df_ai["Transport_N"]
    )

    df_ai = df_ai.sort_values("AI Score",ascending=False)
    df_ai["Rank"]=range(1,len(df_ai)+1)

    best=df_ai.iloc[0]

    st.success(f"🏆 AI Recommendation: {best['Name']}")

    # --------- CHART ----------
    fig = px.bar(df_ai,
                 x="AI Score",
                 y="Name",
                 color="Category",
                 orientation="h",
                 text="AI Score")

    st.plotly_chart(fig,width="stretch")

    # --------- TABLE ----------
    st.dataframe(df_ai)

    # --------- MAP ----------
    m = folium.Map(location=[v_lat,v_lon],zoom_start=9)

    folium.Marker([v_lat,v_lon],
                  popup="Village",
                  icon=folium.Icon(color="black")).add_to(m)

    for _,row in df_ai.iterrows():
        folium.Marker(
            [row["Distance_km"]*0+v_lat,row["Distance_km"]*0+v_lon],
            popup=row["Name"],
            icon=folium.Icon(color="green")
        )

    st_folium(m,width=1100,height=600)
