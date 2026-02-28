## ==========================================================
# 🥭 FARMER PROFIT INTELLIGENCE SYSTEM
# OSM Routing + Profit Engine + Dashboard
# ==========================================================

import streamlit as st
import pandas as pd
import plotly.express as px
import requests
import folium
from streamlit_folium import st_folium
import base64

st.set_page_config(layout="wide")

# ==========================================================
# 🖼 BANNER
# ==========================================================

def set_banner():
    with open("mango_dashboard.webp", "rb") as f:
        img = base64.b64encode(f.read()).decode()

    st.markdown(f"""
        <style>
        .banner {{
            background-image: url("data:image/webp;base64,{img}");
            background-size: cover;
            padding: 120px 20px;
            border-radius: 12px;
            text-align: center;
            color: white;
        }}
        .card {{
            background: #f4f6f9;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 2px 2px 8px rgba(0,0,0,0.1);
            text-align: center;
        }}
        </style>
    """, unsafe_allow_html=True)

    st.markdown("""
        <div class="banner">
            <h1>🥭 Farmer Profit Intelligence System</h1>
            <h4>Smart Mango Marketing Decision Engine</h4>
        </div>
    """, unsafe_allow_html=True)

set_banner()

# ==========================================================
# LOAD DATA
# ==========================================================

@st.cache_data
def load_data():
    price = pd.read_csv("cleaned_price_data.csv")
    villages = pd.read_csv("Village_data.csv")
    return price, villages

price_df, village_df = load_data()

# ==========================================================
# VARIETY LOGIC
# ==========================================================

variety_acceptance = {
    "Banganapalli": ["Mandi","Local Export","Abroad Export"],
    "Totapuri": ["Mandi","Processing","Pulp","Pickle"],
    "Neelam": ["Mandi","Processing"],
    "Rasalu": ["Mandi","Pickle"]
}

# ==========================================================
# SIDEBAR INPUT
# ==========================================================

st.sidebar.header("👨‍🌾 Farmer Registration")

farmer = st.sidebar.text_input("Farmer Name")
phone = st.sidebar.text_input("Phone Number")

village = st.sidebar.selectbox(
    "Village",
    village_df["Gram Panchayat"].unique()
)

variety = st.sidebar.selectbox(
    "Variety",
    list(variety_acceptance.keys())
)

quantity = st.sidebar.number_input("Quantity (Tonnes)", 1, 100, 10)

# ==========================================================
# ROUTING FUNCTION
# ==========================================================

def get_route(lat1, lon1, lat2, lon2):
    url = f"http://router.project-osrm.org/route/v1/driving/{lon1},{lat1};{lon2},{lat2}?overview=full&geometries=geojson"
    r = requests.get(url)
    data = r.json()

    if "routes" in data:
        route = data["routes"][0]
        distance_km = route["distance"] / 1000
        geometry = route["geometry"]["coordinates"]
        return distance_km, geometry
    return None, None

# ==========================================================
# ANALYSIS
# ==========================================================

if st.sidebar.button("Run Smart Analysis"):

    selected_village = village_df[
        village_df["Gram Panchayat"] == village
    ].iloc[0]

    v_lat = selected_village["Latitude"]
    v_lon = selected_village["Longitude"]

    allowed = variety_acceptance[variety]

    filtered = price_df[
        price_df["revenue_type"].isin(allowed)
    ]

    results = []

    st.info("Calculating real road routes using OSM...")

    for _, row in filtered.iterrows():

        distance, geometry = get_route(
            v_lat,
            v_lon,
            row["lat"],
            row["long"]
        )

        if distance and distance <= 80:

            transport_cost = distance * 2000
            revenue = row["today_price(rs/kg)"] * 1000 * quantity
            profit = revenue - transport_cost

            results.append({
                "market": row["market"],
                "distance_km": round(distance,2),
                "transport_cost": round(transport_cost,2),
                "profit": round(profit,2),
                "price": row["today_price(rs/kg)"],
                "lat": row["lat"],
                "lon": row["long"],
                "route": geometry
            })

    results_df = pd.DataFrame(results)

    if results_df.empty:
        st.error("No alternatives within 80 km")
        st.stop()

    top10 = results_df.sort_values("distance_km").head(10)
    best = top10.sort_values("profit", ascending=False).iloc[0]

    # ======================================================
    # KPI CARDS
    # ======================================================

    col1, col2, col3, col4 = st.columns(4)

    col1.markdown(f"""
    <div class="card">
    <h5>Base Price (₹/kg)</h5>
    <h2>{best['price']}</h2>
    </div>
    """, unsafe_allow_html=True)

    col2.markdown(f"""
    <div class="card">
    <h5>Total Revenue (₹)</h5>
    <h2>{int(best['price']*1000*quantity):,}</h2>
    </div>
    """, unsafe_allow_html=True)

    col3.markdown(f"""
    <div class="card">
    <h5>Best Market</h5>
    <h2>{best['market']}</h2>
    </div>
    """, unsafe_allow_html=True)

    col4.markdown(f"""
    <div class="card">
    <h5>Best Profit (₹)</h5>
    <h2>{int(best['profit']):,}</h2>
    </div>
    """, unsafe_allow_html=True)

    # ======================================================
    # BAR GRAPH
    # ======================================================

    st.markdown("## 📊 Profit Comparison")

    fig = px.bar(
        top10,
        x="market",
        y="profit",
        text="profit",
        color="profit",
        color_continuous_scale="Greens"
    )

    fig.update_layout(xaxis_tickangle=-40)
    st.plotly_chart(fig, use_container_width=True)

    # ======================================================
    # TABLE
    # ======================================================

    st.markdown("## 📋 Top 10 Closest Alternatives")

    st.dataframe(
        top10[["market","distance_km","transport_cost","profit"]],
        use_container_width=True
    )

    # ======================================================
    # OSM ROUTING MAP
    # ======================================================

    st.markdown("## 🗺 OSM Routing Map")

    m = folium.Map(location=[v_lat, v_lon], zoom_start=9)

    # Village marker
    folium.Marker(
        [v_lat, v_lon],
        popup="Village",
        icon=folium.Icon(color="red")
    ).add_to(m)

    # Add each route
    for _, row in top10.iterrows():

        folium.Marker(
            [row["lat"], row["lon"]],
            popup=f"""
            {row['market']} <br>
            Distance: {row['distance_km']} km <br>
            Transport: ₹{int(row['transport_cost'])} <br>
            Profit: ₹{int(row['profit'])}
            """,
            icon=folium.Icon(color="green")
        ).add_to(m)

        # Draw route line
        route_coords = [(coord[1], coord[0]) for coord in row["route"]]

        folium.PolyLine(
            route_coords,
            color="blue",
            weight=3
        ).add_to(m)

    st_folium(m, width=1200)
