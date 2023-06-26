import folium
import streamlit as st
from streamlit_folium import folium_static
from folium.plugins import Draw
import geopandas as gpd
from shapely.geometry import LineString
import geojson
from geopandas.tools import overlay

# Set the path to the counties GeoJSON file
counties_geojson = "C:/Users/simra/Desktop/Shapefiles/georef-united-states-of-america-county.geojson"

# Read the counties GeoJSON file as a GeoDataFrame
counties_data = gpd.read_file(counties_geojson)

# Simplify the geometries with a tolerance value
tolerance = 0.025
counties_data = counties_data.geometry.simplify(tolerance)

# Create the initial map
m = folium.Map(location=[37.0902, -95.7129], zoom_start=4, control_scale=True)
folium.GeoJson(counties_data).add_to(m)

# Add the Draw plugin to enable drawing on the map
draw = Draw(export=True, filename="geodata.geojson")
draw.add_to(m)

# Display the map in Streamlit
folium_static(m)

def miles_to_meters(distance):
    return distance * 1

def add_intersecting_polygons_to_map(linestring, buffer_distance):
    buffered_line = linestring.buffer(buffer_distance)
    intersecting_polygons = counties_data[counties_data.geometry.intersects(buffered_line)]

    p = folium.Map(location=[37.0902, -95.7129], zoom_start=4, control_scale=True)
    style_function = lambda x: {'fillColor': 'green', 'color': 'black', 'weight': 1, 'fillOpacity': 0.6}
    intersecting_geojson = gpd.GeoSeries(intersecting_polygons.geometry).to_json()
    folium.GeoJson(intersecting_geojson, style_function=style_function).add_to(p)
    folium_static(p)

    return intersecting_polygons

def make_linestring():
    uploaded_file = st.file_uploader("Upload GeoJSON file", type="geojson")
    buffer_distance_miles = st.selectbox("Buffer Distance (miles)", [0.5, 1, 2, 5, 10])

    if uploaded_file is not None:
        data = geojson.load(uploaded_file)
        if data["type"] == "FeatureCollection":
            features = data["features"]
            for feature in features:
                geometry = feature["geometry"]
                if geometry["type"] == "Polygon":
                    coordinates = geometry["coordinates"]
                    st.write("Polygon Coordinates:")
                    st.write(coordinates)
                elif geometry["type"] == "LineString":
                    coordinates = geometry["coordinates"]
                    linestring = LineString(coordinates)
                    buffer_distance_meters = miles_to_meters(buffer_distance_miles)
                    intersecting_polygons = add_intersecting_polygons_to_map(linestring, buffer_distance_meters)

                    # Create a GeoDataFrame from the intersecting polygons
                    write_polygons = gpd.GeoDataFrame(geometry=intersecting_polygons.geometry)

                    st.write("Intersecting Counties:")
                    st.write(write_polygons)

make_linestring()
