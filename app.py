# ==========================================================
# 🥭 FARMER PROFIT INTELLIGENCE DASHBOARD
# Uses ONLY Your CSV Files
# Light Professional Theme + OSM Routing
# ==========================================================

import streamlit as st
import pandas as pd
import requests
import folium
from streamlit_folium import st_folium
import plotly.express as px

st.set_page_config(layout="wide")

# ==========================================================
# 🎨 LIGHT PROFESSIONAL STYLE
# ==========================================================

st.markdown("""
<style>
body {
    background-color: #f4f6f9;
}
.card {
    background-color: white;
    padding: 18px;
    border-radius: 10px;
    box-shadow: 0px 3px 8px rgba(0,0,0,0.08);
}
</style>
""", unsafe_allow_html=True)

st.title("🥭 Farmer Profit Intelligence System")
st.subheader("🚜 Smart Mango Marketing Decision Engine")

# ==========================================================
# 📂 LOAD YOUR CSV FILES
# ==========================================================

@st.cache_data
def load_data():
    price_df = pd.read_csv("cleaned_price_data.csv")
    village_df = pd.read_csv("Village_data.csv")
    return price_df, village_df

price_df, village_df = load_data()

# ==========================================================
# 🧠 VARIETY FILTERING LOGIC (VISIBLE)
# ==========================================================

variety_logic = {
    "Banganapalli": ["Mandi","Local Export","Abroad Export"],
    "Totapuri": ["Mandi","Processing","Pulp","Pickle"],
    "Neelam": ["Mandi","Processing"],
    "Rasalu": ["Mandi","Pickle"]
}

st.markdown("### 🧠 Variety Logic Used for Filtering")
st.info(variety_logic)

# ==========================================================
# 👨‍🌾 FARMER REGISTRATION
# ==========================================================

st.sidebar.header("👨‍🌾 Farmer Registration")

farmer_name = st.sidebar.text_input("Farmer Name")
mobile_number = st.sidebar.text_input("Mobile Number")

village = st.sidebar.selectbox(
    "Select Village",
    village_df["Gram Panchayat"].unique()
)

variety = st.sidebar.selectbox(
    "Select Mango Variety",
    list(variety_logic.keys())
)

quantity = st.sidebar.number_input(
    "Quantity (Quintals)",
    min_value=1,
    max_value=5000,
    value=100
)

# ==========================================================
# 🌍 OSM ROUTING FUNCTION
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
# 🚀 RUN ANALYSIS
# ==========================================================

if st.sidebar.button("🚀 Run Smart Analysis"):

    selected_village = village_df[
        village_df["Gram Panchayat"] == village
    ].iloc[0]

    v_lat = selected_village["Latitude"]
    v_lon = selected_village["Longitude"]

    allowed_types = variety_logic[variety]

    filtered_df = price_df[
        price_df["revenue_type"].isin(allowed_types)
    ]

    results = []

    st.info("🔄 Calculating Real OSM Road Distances...")

    for _, row in filtered_df.iterrows():

        dist, geometry = get_route(
            v_lat,
            v_lon,
            row["lat"],
            row["long"]
        )

        if dist and dist <= 80:

            # 🚛 Transport Cost
            transport_cost = (dist / 10) * 2000 * quantity

            # 💰 Revenue
            revenue = row["today_price(rs/kg)"] * 100 * quantity

            profit = revenue - transport_cost

            results.append({
                "Alternative Name": row["market"],  # EXACT CSV NAME
                "Distance (km)": round(dist,2),
                "Transport Cost (₹)": round(transport_cost,2),
                "Profit (₹)": round(profit,2),
                "lat": row["lat"],
                "lon": row["long"],
                "route": geometry
            })

    results_df = pd.DataFrame(results)

    if results_df.empty:
        st.error("❌ No alternatives found within 80 km radius.")
        st.stop()

    # ======================================================
    # 🔢 RANKING (1 to 10)
    # ======================================================

    results_df = results_df.sort_values("Profit (₹)", ascending=False).head(10)
    results_df.reset_index(drop=True, inplace=True)
    results_df.index += 1
    results_df.index.name = "Rank"

    best_option = results_df.iloc[0]

    # ======================================================
    # 📊 BAR GRAPH
    # ======================================================

    st.markdown("## 📊 Top 10 Alternative Profit Comparison")

    fig = px.bar(
        results_df,
        x="Alternative Name",
        y="Profit (₹)",
        text="Profit (₹)",
        color="Profit (₹)",
        color_continuous_scale="Greens"
    )

    fig.update_layout(
        xaxis_tickangle=-45,
        plot_bgcolor="white"
    )

    st.plotly_chart(fig, use_container_width=True)

    # ======================================================
    # 📋 RANKED TABLE
    # ======================================================

    st.markdown("## 🏆 Ranked Alternatives (1–10)")

    st.dataframe(
        results_df[[
            "Alternative Name",
            "Distance (km)",
            "Transport Cost (₹)",
            "Profit (₹)"
        ]],
        use_container_width=True
    )

    # ======================================================
    # 🥇 BEST RECOMMENDATION
    # ======================================================

    st.success(f"""
    🥇 Recommended Best Alternative:

    **{best_option['Alternative Name']}**

    💰 Estimated Profit: ₹{int(best_option['Profit (₹)']):,}
    """)

    # ======================================================
    # 🗺 OSM ROUTING MAP
    # ======================================================

    st.markdown("## 🗺 Real OSM Routing Map (Top 10 Alternatives)")

    m = folium.Map(location=[v_lat, v_lon], zoom_start=9)

    # Village marker
    folium.Marker(
        [v_lat, v_lon],
        popup="Village",
        icon=folium.Icon(color="red")
    ).add_to(m)

    for rank, row in results_df.iterrows():

        folium.Marker(
            [row["lat"], row["lon"]],
            popup=f"""
            Rank: {rank}<br>
            {row['Alternative Name']}<br>
            Distance: {row['Distance (km)']} km<br>
            Profit: ₹{int(row['Profit (₹)'])}
            """,
            icon=folium.Icon(color="green")
        ).add_to(m)

        route_coords = [(coord[1], coord[0]) for coord in row["route"]]

        folium.PolyLine(
            route_coords,
            weight=3
        ).add_to(m)

    st_folium(m, width=1200)
