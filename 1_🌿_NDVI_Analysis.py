import streamlit as st
import geemap.foliumap as geemap
import ee
from google.oauth2 import service_account

import json


# تهيئة المصادقة مباشرة من secrets.toml
credentials = ee.ServiceAccountCredentials(
    email=st.secrets["GEE_SERVICE_KEY"]["client_email"],
    key_data=st.secrets["GEE_SERVICE_KEY"]["private_key"]
)
ee.Initialize(credentials)

# =================== تعريف المنطقة ===================
roi = ee.FeatureCollection("projects/ee-risgis897/assets/beni-gov")

# =================== تحميل بيانات Landsat ===================
landsat5 = ee.ImageCollection("LANDSAT/LT05/C02/T1_L2") \
    .filterBounds(roi) \
    .filterDate('1984-01-01', '2011-12-31')

landsat8 = ee.ImageCollection("LANDSAT/LC08/C02/T1_L2") \
    .filterBounds(roi) \
    .filterDate('2013-01-01', '2024-12-31')

# =================== دالة حساب NDVI ===================
def calculate_ndvi(image):
    sensor = ee.String(image.get('SPACECRAFT_ID'))
    red = ee.Algorithms.If(sensor.match('LANDSAT_8'), image.select('SR_B4'), image.select('SR_B3'))
    nir = ee.Algorithms.If(sensor.match('LANDSAT_8'), image.select('SR_B5'), image.select('SR_B4'))
    ndvi = ee.Image(nir).subtract(ee.Image(red)).divide(ee.Image(nir).add(ee.Image(red))).rename('NDVI')
    return ndvi.set('year', image.date().get('year'))

# =================== تطبيق NDVI ودمج المجموعات ===================
ndvi5 = landsat5.map(lambda img: img.multiply(0.0000275).add(-0.2)).map(calculate_ndvi)
ndvi8 = landsat8.map(lambda img: img.multiply(0.0000275).add(-0.2)).map(calculate_ndvi)
merged = ndvi5.merge(ndvi8)

# =================== إنشاء سلاسل زمنية ===================
years = list(range(1984, 2025))
annual_ndvi = []
for year in years:
    start = ee.Date.fromYMD(year, 1, 1)
    end = ee.Date.fromYMD(year, 12, 31)
    image = merged.filterDate(start, end).median().clip(roi).set("year", year)
    annual_ndvi.append(image)

ndvi_series = ee.ImageCollection(annual_ndvi)
layer_names = [f"NDVI {y}" for y in years]

# =================== إعدادات العرض ===================
ndvi_vis = {
    'min': 0.2,
    'max': 0.8,
    'palette': ['white', 'yellow', 'green']
}

# =================== Streamlit واجهة ===================
st.set_page_config(layout="wide")
st.title("🌾 مشروع تخرج: تحليل ومتابعة الغطاء النباتي بمنطقة الظهير الصحراوي لبني سويف")

m = geemap.Map(center=[29.1, 30.6], zoom=9)
m.ts_inspector(
    right_ts=ndvi_series,
    left_ts=ndvi_series,
    left_names=layer_names,
    right_names=layer_names,
    left_vis=ndvi_vis,
    right_vis=ndvi_vis,
)
m.to_streamlit(height=600)
