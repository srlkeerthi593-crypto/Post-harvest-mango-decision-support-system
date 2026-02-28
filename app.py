# ============================================================
# 🥭 FARMER PROFIT INTELLIGENCE SYSTEM
# 🚀 FINAL PRODUCTION VERSION
# ============================================================

import streamlit as st
import pandas as pd
import numpy as np
import folium
from streamlit_folium import st_folium
import plotly.graph_objects as go

st.set_page_config(layout="wide")

st.title("🥭 Mango Profit Intelligence Dashboard")
st.markdown("### 🚜 Smart AI Decision Support for Farmers")

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

# ---------------- SIDEBAR ----------------
st.sidebar.header("👨‍🌾 Farmer Details")

farmer_name = st.sidebar.text_input("👤 Farmer Name")
mobile = st.sidebar.text_input("📱 Mobile Number")

village_name_col = detect_name(villages)
v_lat_col, v_lon_col = detect_lat_lon(villages)

selected_village = st.sidebar.selectbox(
    "🏡 Select Village",
    villages[village_name_col].unique()
)

variety = st.sidebar.selectbox(
    "🥭 Select Variety",
    ["Banganapalli","Totapuri","Neelam","Rasalu"]
)

quantity_qtl = st.sidebar.number_input(
    "📦 Quantity (Quintals)",
    min_value=1,
    value=10
)

if "run_analysis" not in st.session_state:
    st.session_state.run_analysis = False

if st.sidebar.button("🚀 Run Smart Mango Analysis"):
    st.session_state.run_analysis = True

# ---------------- VARIETY LOGIC ----------------
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

category_colors = {
    "Mandi":"blue",
    "Processing":"orange",
    "Pulp":"purple",
    "Pickle":"cadetblue",
    "Local Export":"green",
    "Abroad Export":"red"
}

# ---------------- MAIN ANALYSIS ----------------
if st.session_state.run_analysis:

    st.markdown(f"## 🙏🥭 Namaste **{farmer_name}**")
    st.markdown("### 📊 Here is your Smart Mango Profit Report")

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

                dist = haversine(v_lat,v_lon,row[lat],row[lon])

                transport = (dist/10)*2000*quantity_qtl
                revenue = base_price*(1+margin_map[cat])*100*quantity_qtl
                net = revenue - transport

                results.append({
                    "Category":cat,
                    "Name":row[name_col],
                    "Distance_km":round(dist,2),
                    "Net Profit":round(net,2),
                    "Lat":row[lat],
                    "Lon":row[lon]
                })

    df_top10 = pd.DataFrame(results).sort_values(
        "Net Profit",ascending=False).head(10).reset_index(drop=True)

    df_top10["Rank"]=df_top10.index+1
    best=df_top10.iloc[0]

    # ---------------- METRICS ----------------
    c1,c2,c3,c4 = st.columns(4)
    c1.metric("💰 Base Price (₹/kg)",round(base_price,2))
    c2.metric("🥇 Best Market",best["Name"])
    c3.metric("🏆 Expected Profit (₹)",best["Net Profit"])
    c4.metric("📦 Quantity (Qtl)",quantity_qtl)

    st.markdown("---")

    # ---------------- PROFESSIONAL BAR GRAPH ----------------
    st.subheader("📊🥭 Top 10 Profit Comparison")

    fig = go.Figure()

    fig.add_trace(go.Bar(
        y=df_top10["Name"],
        x=df_top10["Net Profit"],
        orientation='h',
        text=df_top10["Net Profit"],
        textposition="outside",
        marker_color="darkgreen"
    ))

    fig.update_layout(
        height=650,
        xaxis_title="Net Profit (₹)",
        yaxis_title="Market Name",
        yaxis=dict(autorange="reversed")
    )

    st.plotly_chart(fig,width="stretch")

    # ---------------- MAP WITH ROUTES ----------------
    st.subheader("🗺🥭 Route Map to Top 10 Markets")

    m = folium.Map(location=[v_lat,v_lon],zoom_start=9)

    folium.Marker([v_lat,v_lon],
                  popup="🏡 Village",
                  icon=folium.Icon(color="black")).add_to(m)

    for _,row in df_top10.iterrows():

        color = "gold" if row["Rank"]==1 else category_colors[row["Category"]]

        folium.Marker(
            [row["Lat"],row["Lon"]],
            popup=f"🥭 Rank {row['Rank']} - {row['Name']}",
            icon=folium.Icon(color=color)
        ).add_to(m)

        folium.PolyLine(
            locations=[[v_lat,v_lon],[row["Lat"],row["Lon"]]],
            color=color,
            weight=3,
            opacity=0.7
        ).add_to(m)

    st_folium(m,width=1100,height=600)

    # ---------------- DOWNLOAD REPORT ----------------
    csv = df_top10.to_csv(index=False).encode("utf-8")
    st.download_button("📄 Download Top 10 Report",csv,
                       "Top10_Mango_Profit_Report.csv","text/csv")

    # ---------------- SMS RECOMMENDATION ----------------
    st.subheader("📱🥭 Farmer Recommendation Message")

    recommendation = f"""
Namaste {farmer_name},

Best selling option for your {quantity_qtl} quintals of {variety} mango:
Market: {best['Name']}
Expected Profit: ₹{best['Net Profit']}

- Mango Profit Intelligence System
"""

    st.text_area("Ready to Send",recommendation,height=150)

    # ---------------- VARIETY LOGIC ----------------
    st.subheader("🧠 Variety Acceptance Rules")

    for cat,vals in variety_acceptance.items():
        if variety in vals:
            st.success(f"✔ {cat} accepts {variety}")
        else:
            st.error(f"✘ {cat} does NOT accept {variety}")
