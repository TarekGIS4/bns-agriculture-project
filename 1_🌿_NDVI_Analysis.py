import streamlit as st
import geemap.foliumap as geemap
import ee
from google.oauth2 import service_account

# تهيئة المصادقة
credentials = ee.ServiceAccountCredentials(
    email=st.secrets["GEE_SERVICE_KEY"]["client_email"],
    key_data=st.secrets["GEE_SERVICE_KEY"]["private_key"]
)
ee.Initialize(credentials)

# تعريف المنطقة
roi = ee.FeatureCollection("projects/ee-risgis897/assets/beni-gov")

# دالة تقنيع السحب المحسنة
def maskL5(image):
    qa = image.select('QA_PIXEL')
    cloud_mask = qa.bitwiseAnd(1 << 3).eq(0)  # Bit 3: Cloud
    shadow_mask = qa.bitwiseAnd(1 << 4).eq(0)  # Bit 4: Cloud shadow
    opticalBands = image.select('SR_B.').multiply(0.0000275).add(-0.2)
    thermalBand = image.select('ST_B6').multiply(0.00341802).add(149.0)
    return image.addBands(opticalBands).addBands(thermalBand)\
        .updateMask(cloud_mask.And(shadow_mask))

def maskL8(image):
    qa = image.select('QA_PIXEL')
    cloud_mask = qa.bitwiseAnd(1 << 3).eq(0)
    shadow_mask = qa.bitwiseAnd(1 << 4).eq(0)
    opticalBands = image.select('SR_B.').multiply(0.0000275).add(-0.2)
    thermalBands = image.select('ST_B.*').multiply(0.00341802).add(149.0)
    return image.addBands(opticalBands).addBands(thermalBands)\
        .updateMask(cloud_mask.And(shadow_mask))

# دالة حساب NDVI مع توحيد الدقة
def calculateNDVI_L5(image):
    ndvi = image.normalizedDifference(['SR_B4', 'SR_B3']).rename('NDVI')
    return image.addBands(ndvi).reproject('EPSG:4326', scale=30)

def calculateNDVI_L8(image):
    ndvi = image.normalizedDifference(['SR_B5', 'SR_B4']).rename('NDVI')
    return image.addBands(ndvi).reproject('EPSG:4326', scale=30)

# تحميل البيانات مع معالجة متسلسلة
landsat5 = ee.ImageCollection("LANDSAT/LT05/C02/T1_L2")\
    .filterBounds(roi)\
    .filterDate('1984-01-01', '2011-12-31')\
    .map(maskL5)\
    .map(calculateNDVI_L5)

landsat8 = ee.ImageCollection("LANDSAT/LC08/C02/T1_L2")\
    .filterBounds(roi)\
    .filterDate('2013-01-01', '2023-12-31')\
    .map(maskL8)\
    .map(calculateNDVI_L8)

# إنشاء سلسلة زمنية باستخدام Earth Engine
def create_annual_image(year):
    start = ee.Date.fromYMD(year, 1, 1)
    end = ee.Date.fromYMD(year, 12, 31)
    
    l5 = landsat5.filterDate(start, end)
    l8 = landsat8.filterDate(start, end)
    combined = l5.merge(l8)
    
    return ee.Algorithms.If(
        combined.size().gt(0),
        combined.select('NDVI').median().clip(roi).set('year', year),
        None
    )

years = ee.List.sequence(1984, 2023)
annual_ndvi = years.map(create_annual_image)
ndvi_series = ee.ImageCollection(annual_ndvi).filter(ee.Filter.notNull(['year']))

# استخراج السنوات المتاحة
available_years = ndvi_series.aggregate_array('year').getInfo()
valid_years = sorted([int(y) for y in available_years if y is not None])
layer_names = [f"NDVI {y}" for y in valid_years]

# إعدادات الواجهة
ndvi_vis = {
    'min': 0.1,
    'max': 0.8,
    'palette': ['white', 'yellow', 'yellowgreen', 'green', 'darkgreen']
}

st.set_page_config(layout="wide")
st.title("🌾 تحليل الغطاء النباتي ببني سويف")

# تحليل الاتجاه الزمني
trend = ndvi_series.select('NDVI').reduce(ee.Reducer.linearFit())

# عرض الخريطة
m = geemap.Map(center=[29.1, 30.6], zoom=9)
m.addLayer(roi, {}, "منطقة الدراسة")
m.addLayer(trend.select('scale'), {'min': -0.01, 'max': 0.01}, 'اتجاه NDVI')

try:
    m.ts_inspector(
        left_ts=ndvi_series,
        right_ts=ndvi_series,
        left_names=layer_names,
        right_names=layer_names,
        left_vis=ndvi_vis,
        right_vis=ndvi_vis,
    )
except Exception as e:
    st.warning("وضع العرض المبسط بسبب محدودية البيانات")
    selected_year = st.selectbox("اختر السنة", valid_years)
    selected_img = ndvi_series.filter(ee.Filter.eq('year', selected_year)).first()
    m.addLayer(selected_img, ndvi_vis, f"NDVI {selected_year}")

m.to_streamlit(height=600)

# إضافة تحليل إحصائي
st.subheader("التحليل الإحصائي")
st.write("""
- **معدل التغير السنوي:** {:.4f} 
- **فترة الدراسة:** 1984-2023
- **عدد السنوات الفعالة:** {}
""".format(
    trend.select('scale').reduceRegion(
        reducer=ee.Reducer.mean(),
        geometry=roi,
        scale=30
    ).get('scale').getInfo(),
    len(valid_years)
))




