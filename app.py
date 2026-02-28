# ===============================================================
# 🥭 GEO-BI REALISTIC ROUTING MANGO INTELLIGENCE SYSTEM
# Real OSM Routing + Profit Optimization
# ===============================================================

import streamlit as st
import pandas as pd
import requests
import random
import folium
from streamlit_folium import st_folium

st.set_page_config(layout="wide")

# ===============================================================
# LOAD DATA
# ===============================================================

@st.cache_data
def load_all_data():
    price = pd.read_csv("cleaned_price_data.csv")
    geo = pd.read_csv("cleaned_geolocations.csv")
    local = pd.read_csv("cleaned_local_export.csv")
    pickle_units = pd.read_csv("cleaned_pickle_units.csv")
    pulp = pd.read_csv("Pulp_units_merged_lat_long.csv")
    villages = pd.read_csv("Village_data.csv")

    return price, geo, local, pickle_units, pulp, villages

price_df, geo_df, local_df, pickle_df, pulp_df, village_df = load_all_data()

# ===============================================================
# RANDOM VILLAGE SELECTION
# ===============================================================

random_village = village_df.sample(1).iloc[0]

village_lat = random_village["Latitude"]
village_lon = random_village["Longitude"]
village_name = random_village["Gram Panchayat"]

st.title("🌍 Geo-BI Mango Alternative Optimizer")
st.subheader(f"Selected Village: {village_name}")

# ===============================================================
# MERGE ALL ALTERNATIVES
# ===============================================================

mandis = price_df[["market","lat","long","revenue_type","today_price(rs/kg)"]]
mandis.columns = ["name","lat","lon","category","price"]

local_df2 = local_df[["hub_/_firm_name","latitude","longitude"]]
local_df2.columns = ["name","lat","lon"]
local_df2["category"] = "Local Export"
local_df2["price"] = price_df["today_price(rs/kg)"].mean() * 1.15

pickle_df2 = pickle_df[["firm_name","latitude","longitude"]]
pickle_df2.columns = ["name","lat","lon"]
pickle_df2["category"] = "Pickle"
pickle_df2["price"] = price_df["today_price(rs/kg)"].mean() * 1.10

pulp_df2 = pulp_df[["Facility Name","Latitude","Longitude"]]
pulp_df2.columns = ["name","lat","lon"]
pulp_df2["category"] = "Pulp"
pulp_df2["price"] = price_df["today_price(rs/kg)"].mean() * 1.20

all_alternatives = pd.concat(
    [mandis, local_df2, pickle_df2, pulp_df2],
    ignore_index=True
)

# ===============================================================
# REAL OSM ROUTING FUNCTION (OSRM API)
# ===============================================================

def get_route_distance(lat1, lon1, lat2, lon2):
    url = f"http://router.project-osrm.org/route/v1/driving/{lon1},{lat1};{lon2},{lat2}?overview=full&geometries=geojson"
    response = requests.get(url)
    data = response.json()

    if "routes" in data:
        distance_km = data["routes"][0]["distance"] / 1000
        geometry = data["routes"][0]["geometry"]
        return distance_km, geometry
    else:
        return None, None

# ===============================================================
# PROCESS ROUTING
# ===============================================================

results = []

for _, row in all_alternatives.iterrows():
    dist, geom = get_route_distance(
        village_lat, village_lon,
        row["lat"], row["lon"]
    )

    if dist is None:
        continue

    if dist <= 80:

        transport_cost = dist * 2000
        revenue = row["price"] * 1000 * 10
        net_profit = revenue - transport_cost

        results.append({
            "name": row["name"],
            "category": row["category"],
            "distance_km": dist,
            "price": row["price"],
            "net_profit": net_profit,
            "geometry": geom,
            "lat": row["lat"],
            "lon": row["lon"]
        })

results_df = pd.DataFrame(results)

if results_df.empty:
    st.error("No alternatives within 80 km.")
    st.stop()

# ===============================================================
# TOP 10 CLOSEST
# ===============================================================

top10 = results_df.sort_values("distance_km").head(10)

# 2 PER CATEGORY
top2_per_cat = (
    results_df.sort_values("net_profit", ascending=False)
    .groupby("category")
    .head(2)
)

# ===============================================================
# DISPLAY TABLES
# ===============================================================

st.subheader("🏆 Top 10 Closest Alternatives")
st.dataframe(top10[["name","category","distance_km","net_profit"]])

st.subheader("📊 Top 2 Per Category (Most Profitable)")
st.dataframe(top2_per_cat[["name","category","distance_km","net_profit"]])

# ===============================================================
# OSM REAL ROUTE MAP
# ===============================================================

st.subheader("🗺 Real OSM Routing Map")

m = folium.Map(location=[village_lat, village_lon], zoom_start=9)

# Village Marker
folium.Marker(
    [village_lat, village_lon],
    popup="Village",
    icon=folium.Icon(color="red")
).add_to(m)

# Add Routes
for _, row in top10.iterrows():

    folium.Marker(
        [row["lat"], row["lon"]],
        popup=f"{row['name']} | ₹{int(row['net_profit'])}",
        icon=folium.Icon(color="green")
    ).add_to(m)

    folium.GeoJson(row["geometry"]).add_to(m)

st_folium(m, width=1200)
