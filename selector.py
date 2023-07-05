


#----
#Required Packages
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


st.set_page_config(
    page_title="County-Selector"
)


st.title("US County Selector")

# Initializing marker (dynamically adding layers)

if 'markers' not in st.session_state:
    st.session_state["markers"] = []

# Set the path to the counties GeoJSON file
counties_dat = "C:/Users/simra/Desktop/Shapefiles/cb_2018_us_county_20m/cb_2018_us_county_20m.shp"

# Read the counties GeoJSON file as a GeoDataFrame
counties_data = gpd.read_file(counties_dat)

with st.sidebar:
    if st.button('Refresh Map'):
        st.session_state["markers"] = []

    st.write("Pick Color for County Boundary")

    color = st.color_picker('Pick A Color', '#000000')  # Default color if the checkbox is selected

    st.write("## Upload Section")
    st.write(
        "To select counties, draw a line using the draw tool on the map AND enter a buffer distance in miles."
    )
    bd = st.text_input("Buffer Distance (miles)")
    st.write(
        "Upload CSV File to merge. CSV file should have a field named 'FIPS', which includes the 5-digit county code."
        )
    fd = st.file_uploader("Upload CSV file")


# Create the initial map
style_func = lambda x: {'fillColor': 'grey', 'color': color, 'weight': 0.5, 'fillOpacity': 0.6}
style = {'fillColor': '#00FFFFFF', 'lineColor': '#00FFFFFF'}

m = folium.Map(location=[37.0902, -66.7129], zoom_start=4, control_scale=True)
folium.GeoJson(counties_data, style_function=style_func, 
               tooltip=folium.features.GeoJsonTooltip(fields=['NAME', 'GEOID'], aliases=['County Name: ', 'FIPS: '])).add_to(m)

fg = folium.FeatureGroup(name="Markers")

for marker in st.session_state["markers"]:
    fg.add_child(marker)


# Add the Draw plugin to enable drawing on the map
draw = Draw()
draw.add_to(m)

# Display the map in Streamlit
map = st_folium(m,
    feature_group_to_add=fg,
    width=1800,  
    height=500)

#Functions

def distance_conversion(distance):
    return distance * 0.01 * 2


def add_intersecting_polygons_to_map(linestring, buffer_distance):
    buffered_line = linestring.buffer(buffer_distance)
    intersecting_polygons = counties_data[counties_data.geometry.intersects(buffered_line)]

    intersect = folium.GeoJson(intersecting_polygons,
                               tooltip=folium.features.GeoJsonTooltip(fields=['NAME', 'GEOID'], aliases=['Selected County Name: ', 'FIPS: ']))
    buffer = folium.GeoJson(buffered_line)
    st.session_state["markers"].append(buffer)
    st.session_state["markers"].append(intersect)

    global map
    #map = st_folium(m)

    return intersecting_polygons


def make_linestring():
    # Buffered distances
    buffer_dist = bd
    buffer_distance_miles = int(buffer_dist) if buffer_dist else None

    # Calling from data stored in st_folium
    if "last_active_drawing" in map and "geometry" in map["last_active_drawing"] and \
            "coordinates" in map["last_active_drawing"]["geometry"] is not None:
        linestring = LineString(map["last_active_drawing"]["geometry"]["coordinates"])
    else:
        linestring = LineString()

    if linestring and buffer_distance_miles:
        buffer_distance_meters = distance_conversion(buffer_distance_miles)
        intersecting_polygons = add_intersecting_polygons_to_map(linestring, buffer_distance_meters)

        merged_data = counties_data.merge(intersecting_polygons, how="right", on="geometry")
        display_data = merged_data[['STATEFP_x', 'COUNTYFP_x', 'GEOID_x', 'NAME_x']]
        display_data.columns = ['STATE CODE', 'COUNTY CODE', 'FIPS', 'COUNTY NAME']
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
       

display_data = make_linestring()
upload_csv(display_data)



#add_road_network_map()