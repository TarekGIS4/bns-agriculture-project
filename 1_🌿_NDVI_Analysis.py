import streamlit as st
import geemap.foliumap as geemap
import ee
from google.oauth2 import service_account

# تهيئة المصادقة مباشرة من secrets.toml
credentials = ee.ServiceAccountCredentials(
    email=st.secrets["GEE_SERVICE_KEY"]["client_email"],
    key_data=st.secrets["GEE_SERVICE_KEY"]["private_key"]
)
ee.Initialize(credentials)

# تعريف المنطقة
roi = ee.FeatureCollection("projects/ee-risgis897/assets/beni-gov")

# دالة تقنيع السحب للاندسات 5
def maskL5(image):
    qaMask = image.select('QA_PIXEL').bitwiseAnd(int('11111', 2)).eq(0)
    saturationMask = image.select('QA_RADSAT').eq(0)
    opticalBands = image.select('SR_B.').multiply(0.0000275).add(-0.2)
    thermalBand = image.select('ST_B6').multiply(0.00341802).add(149.0)
    return image.addBands(opticalBands, None, True) \
        .addBands(thermalBand, None, True) \
        .updateMask(qaMask) \
        .updateMask(saturationMask)

# دالة تقنيع السحب للاندسات 8
def maskL8(image):
    qaMask = image.select('QA_PIXEL').bitwiseAnd(int('11111', 2)).eq(0)
    saturationMask = image.select('QA_RADSAT').eq(0)
    opticalBands = image.select('SR_B.').multiply(0.0000275).add(-0.2)
    thermalBands = image.select('ST_B.*').multiply(0.00341802).add(149.0)
    return image.addBands(opticalBands, None, True) \
        .addBands(thermalBands, None, True) \
        .updateMask(qaMask) \
        .updateMask(saturationMask)

# دالة حساب NDVI للاندسات 5
def calculateNDVI_L5(image):
    ndvi = image.normalizedDifference(['SR_B4', 'SR_B3']).rename('NDVI')
    return image.addBands(ndvi)

# دالة حساب NDVI للاندسات 8
def calculateNDVI_L8(image):
    ndvi = image.normalizedDifference(['SR_B5', 'SR_B4']).rename('NDVI')
    return image.addBands(ndvi)

# تحميل بيانات لاندسات 5
landsat5 = ee.ImageCollection("LANDSAT/LT05/C02/T1_L2") \
    .filterBounds(roi) \
    .filterDate('1984-01-01', '2011-12-31') \
    .map(maskL5) \
    .map(calculateNDVI_L5)

# تحميل بيانات لاندسات 8
landsat8 = ee.ImageCollection("LANDSAT/LC08/C02/T1_L2") \
    .filterBounds(roi) \
    .filterDate('2013-01-01', '2023-12-31') \
    .map(maskL8) \
    .map(calculateNDVI_L8)

# إنشاء سلسلة زمنية سنوية
years = list(range(1984, 2024))
annual_ndvi = []

for year in years:
    start = ee.Date.fromYMD(year, 1, 1)
    end = ee.Date.fromYMD(year, 12, 31)
    
    # جمع بيانات السنة
    l5_year = landsat5.filterDate(start, end)
    l8_year = landsat8.filterDate(start, end)
    
    # دمج المجموعات
    combined = ee.ImageCollection(l5_year.merge(l8_year))
    
    # حساب المتوسط وإضافة للسلسلة إذا وجدت صور
    if combined.size().getInfo() > 0:
        image = combined.select('NDVI').median().clip(roi).set("year", year)
        annual_ndvi.append(image)

# إنشاء مجموعة الصور للسلسلة الزمنية
if len(annual_ndvi) > 0:
    ndvi_series = ee.ImageCollection.fromImages(annual_ndvi)
    available_years = [img.get('year').getInfo() for img in annual_ndvi]
    layer_names = [f"NDVI {y}" for y in available_years]
    
    # إعدادات العرض
    ndvi_vis = {
        'min': 0.1,
        'max': 0.8,
        'palette': ['white', 'yellow', 'yellowgreen', 'green', 'darkgreen']
    }

    # واجهة ستريمليت
    st.set_page_config(layout="wide")
    st.title("🌾 مشروع تخرج: تحليل ومتابعة الغطاء النباتي بمنطقة الظهير الصحراوي لبني سويف")

    # عرض الخريطة
    m = geemap.Map(center=[29.1, 30.6], zoom=9)
    m.addLayer(roi, {}, "منطقة الدراسة", True)
    
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
        st.error(f"خطأ في ts_inspector: {str(e)}")
        selected_year = st.selectbox("اختر السنة لعرض NDVI", available_years)
        selected_ndvi = ndvi_series.filter(ee.Filter.eq('year', selected_year)).first()
        m.addLayer(selected_ndvi, ndvi_vis, f"NDVI {selected_year}")
    
    m.to_streamlit(height=600)
else:
    st.error("لم يتم العثور على بيانات NDVI للمنطقة المحددة.")

