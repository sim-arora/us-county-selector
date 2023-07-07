# Geospatial Querying Tool
# County Shapefile: https://www.census.gov/geographies/mapping-files/time-series/geo/carto-boundary-file.html


#----
# Required Packages
#----
import folium
import streamlit as st
from streamlit_folium import folium_static, st_folium
from folium.plugins import Draw
import geopandas as gpd
import pandas as pd
from shapely.geometry import LineString, Polygon
import geojson
#----

#----
# Page Setup

st.set_page_config(
    layout="wide",
    page_title="County-Selector"
)

st.title("US County Selector")

st.write("This tool displays US County Boundaries from US Census Bureau's Cartographic Boundary Files. Draw a line to create a buffer (in miles) to select and display the intersecting counties. Additionally, you can add a road network file (.shp) from the sidebar and enter a buffer distance to highlight the intersecting counties. The resulting table can be converted into a .csv file. To add your own data to the selected counties, upload a .csv file with a FIPS code field in the sidebar.")

with st.sidebar:
    st.write("## Map Options")

    if st.button('Refresh Map'):
        st.session_state["markers"] = []

    st.write("Pick Color for County Boundary")

    color = st.color_picker('Color Selector', '#000000')  # Default color if the checkbox is selected

    st.write("## Manual Draw Option")
    st.write(
        "To select counties, draw a line using the draw tool on the map AND enter a buffer distance in miles."
    )
    bd = st.text_input("Buffer Distance (miles)")
    st.write(
        "Upload CSV File to merge. CSV file should have a field named 'FIPS', which includes the 5-digit county code."
        )
    fd = st.file_uploader("Upload CSV file")

    st.write("## Road Network Option")
    roads = st.file_uploader("Upload Road Network Here")
    road_buffer = st.text_input("Buffer Road Distance (miles)")

#---

#----
# Basemap with US Counties

# Initializing session state for streamlit
if 'markers' not in st.session_state:
    st.session_state["markers"] = []

fg = folium.FeatureGroup(name="Markers")
for marker in st.session_state["markers"]:
    fg.add_child(marker)

# Set the path to the counties GeoJSON file
counties_dat = "c:/Users/aroras4/Desktop/Shapefiles/cb_2018_us_county_20m.shp"

# Read the counties GeoJSON file as a geodataframe
counties_data = gpd.read_file(counties_dat)

# Create the initial map
style_func = lambda x: {'fillColor': 'grey', 'color': color, 'weight': 0.5, 'fillOpacity': 0.6}
style = {'fillColor': '#00FFFFFF', 'lineColor': '#00FFFFFF'}
m = folium.Map(location=[38, -80.5], zoom_start=4, control_scale=True)
folium.GeoJson(counties_data, style_function=style_func, 
               tooltip=folium.features.GeoJsonTooltip(fields=['NAME', 'GEOID'], aliases=['County Name: ', 'FIPS: '])).add_to(m)

# Folium draw plugin for draw features
draw = Draw()
draw.add_to(m)

# Display the map 
map = st_folium(m,
    feature_group_to_add=fg,
    width=1800,  
    height=500)

# Road Network Uploader

def add_road_network_map():
    intersecting_roads = gpd.sjoin(counties_data, roads_gdf, op="intersects").drop_duplicates(subset=['GEOID'])
    intersecting_roads_map = folium.GeoJson(intersecting_roads,
                                            tooltip=folium.features.GeoJsonTooltip(fields=['NAME', 'GEOID'], aliases=['Selected County Name: ', 'FIPS: ']))

    display_data_road = intersecting_roads[['STATEFP', 'COUNTYFP', 'GEOID', 'NAME']]
    display_data_road.columns = ['STATE CODE', 'COUNTY CODE', 'FIPS', 'COUNTY NAME']

    st.session_state["markers"].append(intersecting_roads_map)
    st.write("Counties Intersecting with Road Network and Buffer")
    st.write(display_data_road)
    roads_csv_data = display_data_road.to_csv(index=False)

    global map
    return roads_csv_data



if roads is not None:
    roads_gdf = gpd.read_file(roads)
    style1 = {'lineColor': '#000000'}
    roads_map = folium.GeoJson(roads_gdf, style_function= lambda x: style1).add_to(m)
    st.session_state["markers"].append(roads_map)
    add_road_network_map()

#----


#---
# Functions

def add_intersecting_polygons_to_map(linestring, buffer_distance):
    buffered_line = linestring.buffer(buffer_distance)
    intersecting_polygons = counties_data[counties_data.geometry.intersects(buffered_line)]

    intersect = folium.GeoJson(intersecting_polygons,
                               tooltip=folium.features.GeoJsonTooltip(fields=['NAME', 'GEOID'], aliases=['Selected County Name: ', 'FIPS: ']))
    buffer = folium.GeoJson(buffered_line)
    st.session_state["markers"].append(buffer) #Send data to session state
    st.session_state["markers"].append(intersect)

    global map

    return intersecting_polygons

def distance_conversion(distance): #Convert to miles. Buffer radius.
    return distance * 0.016 


def make_linestring():
    buffer_dist = bd
    buffer_distance_miles = int(buffer_dist) if buffer_dist else None

    # Calling from data stored in st_folium
    if "last_active_drawing" in map is not None and "geometry" in map["last_active_drawing"] is not None and \
            "coordinates" in map["last_active_drawing"]["geometry"] is not None:
        linestring = LineString(map["last_active_drawing"]["geometry"]["coordinates"])
    else:
        linestring = LineString()

        return linestring

    if linestring and buffer_distance_miles:
        buffer_distance_meters = distance_conversion(buffer_distance_miles)
        intersecting_polygons = add_intersecting_polygons_to_map(linestring, buffer_distance_meters)

        merged_data = counties_data.merge(intersecting_polygons, how="right", on="geometry")
        display_data = merged_data[['STATEFP_x', 'COUNTYFP_x', 'GEOID_x', 'NAME_x']]
        display_data.columns = ['STATE CODE', 'COUNTY CODE', 'FIPS', 'COUNTY NAME']
        st.write("Counties Intersecting with Line and Buffer")
        st.write(display_data)

        if st.button('Create CSV'):
            csv_data = display_data.to_csv(index=False)
            st.download_button(label='Click to download', data=csv_data, file_name='data.csv', mime='text/csv')

        return display_data
    else:
        st.warning("Please provide both the linestring and buffer distance.")


def upload_csv(display_data):
    uploaded_file = fd
    if uploaded_file is not None:
        csv_data = pd.read_csv(uploaded_file)
        csv_data['FIPS'] = csv_data['FIPS'].astype(int)
        display_data['FIPS'] = display_data['FIPS'].astype(int) 
        merged_csv = display_data.merge(csv_data, how="inner", on="FIPS")
        st.write(merged_csv)
    
        if st.button('Create Merged CSV'):
            csv_data = merged_csv.to_csv(index=False)
            st.download_button(label='Click to download', data=csv_data, file_name='data_merged.csv', mime='text/csv')

    return None


#----
# Calling functions

display_data = make_linestring()
upload_csv(display_data)

#----