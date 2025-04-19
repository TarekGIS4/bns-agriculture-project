import streamlit as st
import ee
from google.oauth2 import service_account
import geemap.foliumap as geemap

# Initialize Earth Engine from Streamlit secrets
try:
    credentials_dict = st.secrets["ee_service_account"]
    credentials = service_account.Credentials.from_service_account_info(credentials_dict)
    ee.Initialize(credentials, project=credentials_dict["project_id"])
except Exception as e:
    st.error(f"Failed to initialize Earth Engine: {e}")
    st.stop()



# Region of Interest
try:
    roi = ee.FeatureCollection("projects/ee-risgis897/assets/beni-gov")
except Exception as e:
    st.error(f"Failed to load ROI: {e}")
    st.stop()

# Landsat 5 and 8 ImageCollections
try:
    landsat5 = ee.ImageCollection("LANDSAT/LT05/C02/T1_L2") \
        .filterBounds(roi) \
        .filterDate('1984-01-01', '2011-12-31')

    landsat8 = ee.ImageCollection("LANDSAT/LC08/C02/T1_L2") \
        .filterBounds(roi) \
        .filterDate('2013-01-01', '2024-12-31')
except Exception as e:
    st.error(f"Failed to load Landsat data: {e}")
    st.stop()


# Function to calculate NDVI based on satellite
def calculate_ndvi(image):
    sensor = ee.String(image.get('SPACECRAFT_ID'))
    b_red = ee.Algorithms.If(sensor.match('LANDSAT_8'), 'SR_B4', 'SR_B3')
    b_nir = ee.Algorithms.If(sensor.match('LANDSAT_8'), 'SR_B5', 'SR_B4')
    ndvi = image.normalizedDifference([b_nir, b_red]).rename('NDVI')
    return image.addBands(ndvi).set('year', image.date().get('year'))


# Merge and calculate NDVI
try:
    merged = landsat5.merge(landsat8).map(calculate_ndvi)
except Exception as e:
    st.error(f"Failed to merge and calculate NDVI: {e}")
    st.stop()


# Time series from 1984 to 2024
years = list(range(1984, 2025))


def yearly_composite(year):
    start = ee.Date.fromYMD(year, 1, 1)
    end = ee.Date.fromYMD(year, 12, 31)
    filtered = merged.filterDate(start, end)
    median = filtered.select('NDVI').median().clip(roi)
    return median.set('year', year)


try:
    ndvi_list = ee.ImageCollection([yearly_composite(y) for y in years])
except Exception as e:
    st.error(f"Failed to create yearly NDVI composite: {e}")
    st.stop()


# Visualization parameters
layer_names = ['NDVI ' + str(y) for y in years]
ndvi_vis = {
    'min': -1,
    'max': 1,
    'palette': [
        'blue',  # water or negative NDVI areas
        'white',  # areas without vegetation
        'yellow',  # beginning of vegetation
        'green',  # medium vegetation cover
        'darkgreen'  # dense vegetation cover
    ]
}

# Streamlit app
st.title("NDVI Time Series Analysis")

# Map display
try:
    Map = geemap.Map(center=[29.1, 30.6], zoom=9)
    Map.ts_inspector(
        right_ts=ndvi_list,
        left_ts=ndvi_list,
        left_names=layer_names,
        right_names=layer_names,
        left_vis=ndvi_vis,
        right_vis=ndvi_vis,
        width='100%',
        height='600px'
    )

    Map.addLayerControl()
    # Map.add_inspector() # Removed inspector due to potential issues
    Map.to_streamlit(height=600)  # Correct way to display map in Streamlit

except Exception as e:
    st.error(f"Failed to display map: {e}")
    st.stop()
