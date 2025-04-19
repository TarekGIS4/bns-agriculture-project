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

# إضافة مؤشر تحميل
with st.spinner('جاري تحميل البيانات الجغرافية...'):
    # تعريف المنطقة
    roi = ee.FeatureCollection("projects/ee-risgis897/assets/beni-gov")

    # دالة معالجة لاندسات 5
    def maskL5(image):
        qaMask = image.select('QA_PIXEL').bitwiseAnd(parseInt('11111', 2)).eq(0)
        saturationMask = image.select('QA_RADSAT').eq(0)
        opticalBands = image.select('SR_B.').multiply(0.0000275).add(-0.2)
        thermalBand = image.select('ST_B6').multiply(0.00341802).add(149.0)
        return image.addBands(opticalBands, None, True) \
            .addBands(thermalBand, None, True) \
            .updateMask(qaMask) \
            .updateMask(saturationMask)

    # دالة معالجة لاندسات 8
    def maskL8(image):
        qaMask = image.select('QA_PIXEL').bitwiseAnd(parseInt('11111', 2)).eq(0)
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

    # تجهيز بيانات لاندسات 5
    landsat5 = ee.ImageCollection("LANDSAT/LT05/C02/T1_L2") \
        .filterBounds(roi) \
        .filterDate('1984-01-01', '2011-12-31') \
        .map(maskL5) \
        .map(calculateNDVI_L5)

    # تجهيز بيانات لاندسات 8
    landsat8 = ee.ImageCollection("LANDSAT/LC08/C02/T1_L2") \
        .filterBounds(roi) \
        .filterDate('2013-01-01', '2023-12-31') \
        .map(maskL8) \
        .map(calculateNDVI_L8)

    # استخراج سلسلة زمنية سنوية
    years = list(range(1984, 2024))
    annual_ndvi = []
    
    # إنشاء البيانات السنوية
    for year in years:
        start = ee.Date.fromYMD(year, 1, 1)
        end = ee.Date.fromYMD(year, 12, 31)
        
        # جمع بيانات لاندسات 5
        l5_year = landsat5.filterDate(start, end)
        
        # جمع بيانات لاندسات 8
        l8_year = landsat8.filterDate(start, end)
        
        # دمج البيانات
        combined = ee.ImageCollection(l5_year.merge(l8_year))
        
        # حساب المتوسط والقص حسب المنطقة
        if combined.size().getInfo() > 0:  # التحقق من وجود صور
            image = combined.select('NDVI').median().clip(roi).set("year", year)
            annual_ndvi.append(image)

    # فحص وجود بيانات
    if len(annual_ndvi) > 0:
        ndvi_series = ee.ImageCollection.fromImages(annual_ndvi)
        layer_names = [f"NDVI {y}" for y in years if y in [img.get('year').getInfo() for img in annual_ndvi]]
        
        # إعدادات العرض
        ndvi_vis = {
            'min': 0.1,
            'max': 0.8,
            'palette': ['white', 'yellow', 'yellowgreen', 'green', 'darkgreen']
        }
    else:
        st.error("لم يتم العثور على بيانات NDVI للمنطقة المحددة")

# واجهة ستريمليت
st.set_page_config(layout="wide")
st.title("🌾 مشروع تخرج: تحليل ومتابعة الغطاء النباتي بمنطقة الظهير الصحراوي لبني سويف")

# عرض الخريطة
if 'ndvi_series' in locals():
    m = geemap.Map(center=[29.1, 30.6], zoom=9)
    
    # عرض صورة NDVI واحدة للتأكد من وجود البيانات
    first_ndvi = ndvi_series.first()
    m.addLayer(first_ndvi, ndvi_vis, "NDVI First Available Year")
    
    # إضافة صورة أساسية للتحقق من التطابق الجغرافي
    m.addLayer(roi, {}, "منطقة الدراسة", True)
    
    # استخدام ts_inspector مع التأكد من توفر البيانات
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
        st.error(f"خطأ في ts_inspector: {e}")
        # استخدام طريقة بديلة
        years_avail = [img.get('year').getInfo() for img in annual_ndvi]
        selected_year = st.selectbox("اختر السنة لعرض NDVI", years_avail)
        selected_ndvi = ndvi_series.filter(ee.Filter.eq('year', selected_year)).first()
        m.addLayer(selected_ndvi, ndvi_vis, f"NDVI {selected_year}")

    m.to_streamlit(height=600)
else:
    st.error("لم يتم تحميل بيانات NDVI. تأكد من صحة منطقة الدراسة وتوفر الصور.")

