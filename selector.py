# Geospatial Querying Tool
# County Shapefile: https://www.census.gov/geographies/mapping-files/time-series/geo/carto-boundary-file.html


#----
# Required Packages
#----
import folium
import streamlit as st
from streamlit_folium import st_folium
from folium.plugins import Draw
import geopandas as gpd
import pandas as pd
from shapely.geometry import LineString
import geojson
#----

# Harcoded data

shp = "https://www2.census.gov/geo/tiger/GENZ2018/shp/cb_2018_us_county_20m.zip"

#----
# Page Setup

st.set_page_config(
layout="wide",
page_title="County-Selector"
)

st.title("US County Selector")
st.write("THIS IS A TEST")

with st.sidebar:
    st.write("## Map Options")

    st.write("## Pick Color for County Boundary")

    color = st.color_picker('Boundary Color', '#000000')  # Default color if the checkbox is selected
    colorfill = st.color_picker('Fill Color', '#A9A9A9') # Default color if the checkbox is selected

    st.write("Refresh Map")
    if st.button("Clear Selected Polygons"):
        st.cache_data.clear()
        st.session_state["markers"] = []

tab1, tab2, tab3 = st.tabs(['Manual Draw Option', 'Road Network Option', 'Add/Change Basemap'])

with tab1:

    st.write("## Manual Draw Option")
    st.write(
        "To select counties, draw a line using the draw tool on the map AND enter a buffer distance in miles."
    )
    bd = st.text_input("Buffer Distance (miles)") # Add default buffer value
    st.write(
        "Upload CSV File to merge. CSV file should have a field named 'FIPS', which includes the 5-digit county code."
        )
    fd = st.file_uploader("Upload CSV file")

with tab2:
    st.write("## Road Network Option")
    roads = st.file_uploader("Upload Road Network Here")
    st.write(
            " To use the Road Network Option, upload a zipped shapefile below AND enter a buffer value in miles."
            )
    road_buffer = st.text_input("Buffer Road Distance (miles)") 
    st.write(
        "Upload CSV File to merge with roads data. CSV file should have a field named 'FIPS', which includes the 5-digit county code."
        )
    rd = st.file_uploader("Upload CSV file (for roads)")

with tab3:

    st.write("## Select Basemap Layer")
    st.write("Upload Your Base Layer")

    # cbsa = "https://www2.census.gov/geo/tiger/GENZ2018/shp/cb_2018_us_cbsa_20m.zip"
    # csa = "https://www2.census.gov/geo/tiger/GENZ2018/shp/cb_2018_us_csa_20m.zip"
    # state = "https://www2.census.gov/geo/tiger/GENZ2018/shp/cb_2018_us_state_20m.zip"

    basemap_change = st.file_uploader("Enter zipped shapefile here")

    bm_bd = st.text_input("Buffer Distance for Line")

    # if st.button("CBSA"):
    #     basemap_button = cbsa
    # if st.button("CSA"):
    #     basemap_button = csa
    # if st.button("State"):
    #      basemap_button = state

    # shp = st.file_uploader("Upload Any .SHP data here")
    # if shp is None:

#----

# Functions

# Map Functions
@st.cache_resource
def map_data():
    counties_data = "https://www2.census.gov/geo/tiger/GENZ2018/shp/cb_2018_us_county_20m.zip"
    counties_data = gpd.read_file(counties_data)
    return counties_data

def create_map():
    style_func = lambda x: {'fillColor': colorfill, 'color': color, 'weight': 0.5, 'fillOpacity': 0.6}
    m = folium.Map(location=[38, -80.5], zoom_start=4, control_scale=True)
    counties_data=map_data()
    folium.GeoJson(counties_data, style_function=style_func).add_to(m) #Standard CRS for all Leaflet/Folium is EPSG:4326/WGS 84
    draw = Draw()
    draw.add_to(m)
    return m

# Map


if 'markers' not in st.session_state:
    st.session_state["markers"] = []

fg = folium.FeatureGroup(name="Markers")
for marker in st.session_state["markers"]:
    fg.add_child(marker)

m = create_map()

map = st_folium(m,
feature_group_to_add=fg,
width=1800,  
height=500)

if roads is not None:
    roads_gdf = gpd.read_file(roads)
    style1 = {'lineColor': '#000000'}
    roads_map = folium.GeoJson(roads_gdf, style_function= lambda x: style1).add_to(m)
    st.session_state["markers"].append(roads_map)

# Manual Draw Option Functions

def distance_conversion(distance): #Convert to miles. Buffer radius.
    return distance * 0.016 

@st.cache_data
def make_linestring():
    # Calling from data stored in st_folium
    if "coordinates" in map["last_active_drawing"]["geometry"] is not None:
        linestring = LineString(map["last_active_drawing"]["geometry"]["coordinates"])

        counties_data = map_data()

        # Creating buffer
        if linestring and bd is not None:
            buffer_dist = bd
            buffer_distance = int(buffer_dist) if buffer_dist else 1
            buffer_distance_miles = distance_conversion(buffer_distance)
            buffered_line = linestring.buffer(buffer_distance_miles)

            # Spatial join for buffer and counties (or other basemap layer)
            bl = gpd.GeoDataFrame(gpd.GeoSeries(buffered_line))
            bl.columns = ['geometry']
            bl.set_geometry("geometry", inplace=True)
            bl.set_crs("EPSG:4269", inplace=True, allow_override=True)
            counties_data.set_crs("EPSG:4326", inplace=True, allow_override=True)

            intersecting_polygons = gpd.sjoin(counties_data, bl, op='intersects').drop_duplicates(subset='GEOID')
            selected_polygons = intersecting_polygons

            # Adding joined polygons/markers/lines to map
            style2 = {'lineColor': '#000000'}
            intersect = folium.GeoJson(intersecting_polygons, style_function= lambda x: style2).add_to(m)
            buffer = folium.GeoJson(buffered_line)
            st.session_state["markers"].append(buffer) #Send data to session state
            st.session_state["markers"].append(intersect)

            # Displaying data table
            display_data = selected_polygons[['STATEFP', 'GEOID', 'NAME']]
            display_data.columns = ['STATE CODE', 'FIPS', 'COUNTY NAME']
            st.write("Counties Intersecting with Buffer")
            st.write(display_data)

            # Download button
            download_data(display_data)

            # Merge Data and create export
            uploaded_file = fd 
            if uploaded_file is not None:
                csv_data_merged = pd.read_csv(uploaded_file)
                csv_data_merged['FIPS'] = csv_data_merged['FIPS'].astype(int)
                display_data['FIPS'] = display_data['FIPS'].astype(int)
                merged_csv = display_data.merge(csv_data_merged, how='inner', on='FIPS')
                merged_csv['FIPS'] = merged_csv['FIPS'].astype(str)
                merged_csv['FIPS'] = merged_csv['FIPS'].str.zfill(5)
                st.write(merged_csv)

                if st.button('Create Merged CSV'):
                    csv_merged = merged_csv.to_csv(index=False)
                    st.download_button(label='Click to download', data=csv_merged, file_name='data_merged.csv', mime='text/csv')

        return display_data


def download_data(selected_data):
    if st.button('Create CSV'):
        csv_data = selected_data.to_csv(index=False)
        st.download_button(label = 'Download CSV', data = csv_data, file_name="data.csv", mime="text/csv")
    return None

# Road Network Option Functions

def add_road_buffer():
    counties_data = map_data()
    if roads is not None:

        # Creating buffer
        road_buffer_dist = road_buffer
        road_buffer_distance = int(road_buffer_dist) if road_buffer_dist else 1 
        road_buffer_distance_miles = distance_conversion(road_buffer_distance)

        #roads_gdf = gpd.read_file(roads)
        road_buffer_geo = roads_gdf['geometry']
        road_buffered_line = road_buffer_geo.buffer(road_buffer_distance_miles)

        # Spatial join for buffer and counties (or other basemap layer)
        rbl = gpd.GeoDataFrame(gpd.GeoSeries(road_buffered_line))
        rbl.columns = ['geometry']
        rbl.set_geometry("geometry", inplace=True)
        rbl.set_crs("EPSG:4326", inplace=True, allow_override=True)
        counties_data.set_crs("EPSG:4326", inplace=True, allow_override=True)

        intersecting_road_polygons = gpd.sjoin(counties_data, rbl, op='intersects').drop_duplicates(subset='GEOID')
        road_selected_polygons = intersecting_road_polygons

        # Adding joined polygons/markers/lines to map
        intersect_road = folium.GeoJson(road_selected_polygons)
        buffer_road = folium.GeoJson(road_buffered_line)
        st.session_state["markers"].append(intersect_road) #Send data to session state
        st.session_state["markers"].append(buffer_road)     

        # Displaying Data Table
        display_data_roads = road_selected_polygons[['STATEFP', 'GEOID', 'NAME']]
        display_data_roads.columns = ['STATE CODE', 'FIPS', 'COUNTY NAME']
        st.write("Counties Intersecting with Roads and Buffer")
        st.write(display_data_roads)

        # Download button
        download_data(display_data_roads)

        # Merge Data and create export
        uploaded_file_rd = rd 
        if uploaded_file_rd is not None:
            csv_data_merged_rd = pd.read_csv(uploaded_file_rd)
            csv_data_merged_rd['FIPS'] = csv_data_merged_rd['FIPS'].astype(int)
            display_data_roads['FIPS'] = display_data_roads['FIPS'].astype(int)
            merged_csv_rd = display_data_roads.merge(csv_data_merged_rd, how='inner', on='FIPS')
            merged_csv_rd['FIPS'] = merged_csv_rd['FIPS'].astype(str)
            merged_csv_rd['FIPS'] = merged_csv_rd['FIPS'].str.zfill(5)
            st.write(merged_csv_rd)

            if st.button('Create Merged CSV'):
                csv_merged_rd = merged_csv_rd.to_csv(index=False)
                st.download_button(label='Click to download', data=csv_merged_rd, file_name='data_merged_roads.csv', mime='text/csv')

        return display_data_roads
    
# Change Basemap Functions
@st.cache_data
def change_basemap():
    #Load Basemap
    basemap = basemap_change
    basemap_gdf = gpd.read_file(basemap)

    basemap_gdf_map = folium.GeoJson(basemap_gdf)
    st.session_state["markers"].append(basemap_gdf_map)

    return basemap_gdf

@st.cache_data
def make_ls_basemap():
    #load Basemap from function
    basemap_new = change_basemap()

    if "coordinates" in map["last_active_drawing"]["geometry"] is not None:
        ls = LineString(map["last_active_drawing"]["geometry"]["coordinates"]) 


        # Buffer for linestring
        bm_ls = bm_bd
        bm_buffer_distance = int(bm_ls) if bm_ls else 1
        buffer_distance_miles = distance_conversion(bm_buffer_distance)
        bm_buffered_line = ls.buffer(buffer_distance_miles)

        # Spatial Join
        bm_bl = gpd.GeoDataFrame(gpd.GeoSeries(bm_buffered_line))
        bm_bl.columns = ['geometry']
        bm_bl.set_geometry("geometry", inplace = True)
        bm_bl.set_crs("EPSG:4269", inplace=True, allow_override=True)

        intersecting_poly_basemap = gpd.sjoin(basemap_new, bm_bl, op="intersects").drop_duplicates(subset='GEOID')

        # Adding polygons to map
        bm_intersect = folium.GeoJson(intersecting_poly_basemap)
        st.session_state["markers"].append(bm_intersect)
        bm_buffer = folium.GeoJson(bm_buffered_line)
        st.session_state["markers"].append(bm_buffer)

        # Display Data Table
        # display = intersecting_poly_basemap[['GEOID', 'NAME']]
        # display.columns = ['FIPS', 'NAME']
        st.write("Geographies/Markers/Lines intersecting with Buffer")
        st.write(intersecting_poly_basemap)

        return intersecting_poly_basemap

#----
if basemap_change is not None:
    make_ls_basemap()

add_road_buffer()

#make_linestring()


# Issues:

# Add different colors for selected polygons
# Cache optimization
# Set up changing basemap
# Why won't buffer take value under 1?
# Add functionality recognize uploaded type in change basemap option





