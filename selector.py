import folium
import streamlit as st
from streamlit_folium import folium_static, st_folium
from folium.plugins import Draw
import geopandas as gpd
import pandas as pd
from shapely.geometry import LineString
import geojson

st.title("US County Selector")

#Set the path to the counties GeoJSON file
counties_geojson = "C:/Users/simra/Desktop/Shapefiles/georef-united-states-of-america-county.geojson"

#Read the counties GeoJSON file as a GeoDataFrame
counties_data = gpd.read_file(counties_geojson)

#Simplify the geometries with a tolerance value
tolerance = 0.025
counties_data = counties_data.geometry.simplify(tolerance)

#Create the initial map
style_func = lambda x: {'fillColor': 'none', 'color': 'blue', 'weight': 0.5, 'fillOpacity': 0.6}
m = folium.Map(location=[37.0902, -95.7129], zoom_start=4, control_scale=True, width = 700, height = 500)
folium.GeoJson(counties_data, style_function=style_func).add_to(m)

#Add the Draw plugin to enable drawing on the map
draw = Draw(export=True, filename="geodata.geojson")
draw.add_to(m)
print(draw)

#Display the map in Streamlit
map = st_folium(m)

def distance_conversion(distance):
    return distance * 1.6

def add_intersecting_polygons_to_map(linestring, buffer_distance):
    buffered_line = linestring.buffer(buffer_distance)
    intersecting_polygons = counties_data[counties_data.geometry.intersects(buffered_line)]

    #p = folium.Map(location=[37.0902, -95.7129], zoom_start=4, control_scale=True)
    style_function = lambda x: {'fillColor': 'green', 'color': 'black', 'weight': 1, 'fillOpacity': 0.6}
    intersecting_geojson = gpd.GeoSeries(intersecting_polygons.geometry).to_json()
    folium.GeoJson(intersecting_geojson, style_function=style_function).add_to(m)
    global map
    map = st_folium(m)
    #folium_static(p)

    return intersecting_polygons

def make_linestring():
    #uploaded_file = st.file_uploader("Upload GeoJSON file", type="geojson")
    buffer_distance_miles = st.selectbox("Buffer Distance (miles)", [0.5, 1, 2, 5, 10])

    if "last_active_drawing" in map and "geometry" in map["last_active_drawing"] and "coordinates" in map["last_active_drawing"]["geometry"]:
      linestring = LineString(map["last_active_drawing"]["geometry"]["coordinates"])  

    buffer_distance_meters = distance_conversion(buffer_distance_miles)
    intersecting_polygons = add_intersecting_polygons_to_map(linestring, buffer_distance_meters)

    write_polygons = gpd.GeoDataFrame(geometry=intersecting_polygons.geometry)
    st.write(write_polygons)
                    

make_linestring()