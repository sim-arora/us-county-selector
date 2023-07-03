import folium
import streamlit as st
from streamlit_folium import folium_static, st_folium
from folium.plugins import Draw
import geopandas as gpd
import pandas as pd
from shapely.geometry import LineString
import geojson

st.title("US County Selector")

#Todo
#Simplify geojson geometry
#Join tables and print intersecting polygons geometry
#Correct the buffer distance
#Improve the map


#Set the path to the counties GeoJSON file
counties_geojson = "C:/Users/aroras4/Desktop/Shapefiles/cb_2018_us_county_20m.shp"

#Read the counties GeoJSON file as a GeoDataFrame
counties_data = gpd.read_file(counties_geojson)

#Simplify the geometries with a tolerance value
tolerance = 0.025
counties_data = counties_data.geometry.simplify(tolerance)

#Create the initial map
style_func = lambda x: {'fillColor': 'none', 'color': 'blue', 'weight': 0.5, 'fillOpacity': 0.6}
m = folium.Map(width=500 ,height=500 ,location=[37.0902, -95.7129], zoom_start=4, control_scale=True)
folium.GeoJson(counties_data, style_function=style_func).add_to(m)

#Add the Draw plugin to enable drawing on the map
draw = Draw(export=True, filename="geodata.geojson")
draw.add_to(m)

#Display the map in Streamlit
map = st_folium(m)

#Correct this function
def distance_conversion(distance):
    return distance * 0.016

#Intersecting polygons functions, right now adds an extra map
def add_intersecting_polygons_to_map(linestring, buffer_distance):
    buffered_line = linestring.buffer(buffer_distance)
    intersecting_polygons = counties_data[counties_data.geometry.intersects(buffered_line)]

    style_function = lambda x: {'fillColor': 'green', 'color': 'black', 'weight': 1, 'fillOpacity': 0.6}
    intersecting_geojson = gpd.GeoSeries(intersecting_polygons.geometry).to_json()
    folium.GeoJson(intersecting_geojson, style_function=style_function).add_to(m)

    global map
    map = st_folium(m)   
    return intersecting_polygons

def make_linestring():

    #Buffered distances
    buffer_distance_miles = st.selectbox("Buffer Distance (miles)", [0.5, 1, 2, 5, 10])
    buffer_distance_meters = distance_conversion(buffer_distance_miles)

    #Calling from data stores in st_folium
    if "last_active_drawing" in map and "geometry" in map["last_active_drawing"] and "coordinates" in map["last_active_drawing"]["geometry"] is not None:
      linestring = LineString(map["last_active_drawing"]["geometry"]["coordinates"])  

    intersecting_polygons = add_intersecting_polygons_to_map(linestring, buffer_distance_meters)

    #writing polygons selected
    write_polygons = gpd.GeoDataFrame(geometry=intersecting_polygons.geometry)
    st.write(write_polygons)
                    

make_linestring()