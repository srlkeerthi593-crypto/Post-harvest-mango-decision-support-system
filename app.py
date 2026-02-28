# ============================================================
# 🥭 MANGO MARKET DECISION INTELLIGENCE DASHBOARD 🥭
# Advanced Agricultural Profit Optimization System
# ============================================================

import streamlit as st
import pandas as pd
import numpy as np
import folium
from streamlit_folium import st_folium
import plotly.graph_objects as go

st.set_page_config(layout="wide")

st.title("🥭 Mango Market Decision Intelligence Dashboard 🥭")
st.subheader("📊 Advanced Agricultural Profit Optimization System 🥭")

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
    # This ensures real names are picked directly from CSV
    for c in df.columns:
        if c in ["market","place","unit_name","company_name","name"]:
            return c
    for c in df.columns:
        if any(x in c for x in ["place","market","name"]):
            return c
    return df.columns[0]

def haversine(lat1, lon1, lat2, lon2):
    R = 6371
    lat1, lon1, lat2, lon2 = map(np.radians,[lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = np.sin(dlat/2)**2 + np.cos(lat1)*np.cos(lat2)*np.sin(dlon/2)**2
    return R * 2*np.arcsin(np.sqrt(a))

# ---------------- SIDEBAR ----------------
st.sidebar.header("👨‍🌾 Farmer Details 🥭")

farmer_name = st.sidebar.text_input("Farmer Name 🥭")

selected_village = st.sidebar.selectbox(
    "Select Village 🏡",
    villages[detect_name(villages)].unique()
)

variety = st.sidebar.selectbox(
    "Select Variety 🥭",
    ["Banganapalli","Totapuri","Neelam","Rasalu"]
)

quantity_qtl = st.sidebar.number_input("Quantity (Quintals) 📦", min_value=1, value=10)

if "run" not in st.session_state:
    st.session_state.run = False

if st.sidebar.button("🚀 Run Smart Analysis 🥭"):
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

    st.markdown(f"## 🙏🥭 Namaste **{farmer_name}** 🥭")
    st.markdown("### 📈 Strategic Profit Intelligence Summary 🥭")

    village_row = villages[villages[detect_name(villages)]==selected_village].iloc[0]
    v_lat, v_lon = village_row[detect_lat_lon(villages)[0]], village_row[detect_lat_lon(villages)[1]]

    mandi_data = prices.merge(geo,on="market",how="left")
    lat_m, lon_m = detect_lat_lon(mandi_data)
    mandi_data = mandi_data.dropna(subset=[lat_m,lon_m])

    mandi_data["distance"] = mandi_data.apply(
        lambda r: haversine(v_lat,v_lon,r[lat_m],r[lon_m]),axis=1)

    nearest = mandi_data.loc[mandi_data["distance"].idxmin()]
    base_price = nearest["today_price(rs/kg)"]

    results=[]

    category_dfs = {
        "Mandi":mandi_data,
        "Processing":processing,
        "Pulp":pulp,
        "Pickle":pickle_units,
        "Local Export":local_export,
        "Abroad Export":abroad_export
    }

    for cat,df in category_dfs.items():
        if variety not in variety_acceptance[cat]: continue
        lat,lon = detect_lat_lon(df)
        name_col = detect_name(df)   # ensures real CSV names used
        if lat is None: continue

        for _,row in df.iterrows():
            if pd.notnull(row[lat]) and pd.notnull(row[lon]):
                dist = haversine(v_lat,v_lon,row[lat],row[lon])
                transport = (dist/10)*2000*quantity_qtl
                revenue = base_price*(1+margin_map[cat])*100*quantity_qtl
                net = revenue - transport

                results.append({
                    "Category":cat,
                    "Name":row[name_col],   # real names
                    "Distance_km":round(dist,2),
                    "Net Profit":round(net,2),
                    "Lat":row[lat],
                    "Lon":row[lon]
                })

    df_top10 = pd.DataFrame(results).drop_duplicates(subset=["Name","Category"])\
        .sort_values("Net Profit",ascending=False).head(10).reset_index(drop=True)

    df_top10["Rank"] = df_top10.index + 1
    best = df_top10.iloc[0]

    # ---------------- METRICS ----------------
    c1,c2,c3,c4 = st.columns(4)
    c1.metric("💰 Base Price (₹/kg)",round(base_price,2))
    c2.metric("🥇 Best Alternative 🥭",best["Name"])
    c3.metric("🏆 Net Profit (₹)",best["Net Profit"])
    c4.metric("📦 Quantity (Qtl)",quantity_qtl)

    st.markdown("---")

    st.success(f"📢🥭 Recommendation: Sell at **{best['Name']}** under "
               f"**{best['Category']}** for maximum estimated profit of ₹ {best['Net Profit']:,.0f} 🥭")

    # ---------------- BAR GRAPH ----------------
    st.subheader("📊🥭 Profit Comparison (Top 10 Alternatives)")

    df_sorted = df_top10.sort_values("Net Profit")

    fig = go.Figure()
    fig.add_trace(go.Bar(
        y=df_sorted["Name"],
        x=df_sorted["Net Profit"],
        orientation='h',
        text=[f"₹{x:,.0f}" for x in df_sorted["Net Profit"]],
        textposition="outside",
        marker=dict(
            color=df_sorted["Net Profit"],
            colorscale="Turbo",
            line=dict(color="black", width=1.5)
        )
    ))

    fig.update_layout(height=750, yaxis=dict(autorange="reversed"))
    st.plotly_chart(fig, width="stretch")

    # ---------------- MAP ----------------
    st.subheader("🗺🥭 Top 10 Alternatives with Routes")

    m = folium.Map(location=[v_lat,v_lon],zoom_start=9)

    folium.Marker([v_lat,v_lon],
                  popup="🏡 Village 🥭",
                  icon=folium.Icon(color="black")).add_to(m)

    for _,row in df_top10.iterrows():

        folium.Marker(
            [row["Lat"],row["Lon"]],
            popup=f"🥭 {row['Name']} ({row['Category']})",
            icon=folium.Icon(color="green")
        ).add_to(m)

        folium.PolyLine(
            [[v_lat,v_lon],[row["Lat"],row["Lon"]]],
            color="orange",
            weight=4,
            opacity=0.8
        ).add_to(m)

    st_folium(m,width=1100,height=600)
