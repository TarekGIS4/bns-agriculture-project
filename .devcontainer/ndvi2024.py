

import ee
import geemap
import datetime


# In[2]:


# تفعيل Earth Engine
ee.Initialize(project='ee-risgis897')


# In[3]:


# 👇 المنطقة اللي بنشتغل عليها
roi = ee.FeatureCollection("projects/ee-risgis897/assets/beni-gov")


# In[4]:


# 🛰️ صور Landsat 5 و 8
landsat5 = ee.ImageCollection("LANDSAT/LT05/C02/T1_L2") \
            .filterBounds(roi) \
            .filterDate('1984-01-01', '2011-12-31')

landsat8 = ee.ImageCollection("LANDSAT/LC08/C02/T1_L2") \
            .filterBounds(roi) \
            .filterDate('2013-01-01', '2024-12-31')


# In[5]:


# 🧪 دالة لحساب NDVI حسب نوع الساتلايت
def calculate_ndvi(image):
    b_red = ee.String('SR_B3')
    b_nir = ee.String('SR_B4')
    bqa = 'QA_PIXEL'


# In[6]:


def calculate_ndvi(image):
   # نحدد اسم الباندات حسب نوع القمر الصناعي باستخدام regex match
   sensor = ee.String(image.get('SPACECRAFT_ID'))

   b_red = ee.Algorithms.If(sensor.match('LANDSAT_8'), 'SR_B4', 'SR_B3')
   b_nir = ee.Algorithms.If(sensor.match('LANDSAT_8'), 'SR_B5', 'SR_B4')

   ndvi = image.normalizedDifference([b_nir, b_red]).rename('NDVI')
   return image.addBands(ndvi).set('year', image.date().get('year'))



# In[7]:


merged = landsat5.merge(landsat8).map(calculate_ndvi)



# In[8]:


# 🗓️ التايم سيريز من 1984 إلى 2024
years = list(range(1984, 2025))

def yearly_composite(year):
    start = ee.Date.fromYMD(year, 1, 1)
    end = ee.Date.fromYMD(year, 12, 31)
    filtered = merged.filterDate(start, end)
    median = filtered.select('NDVI').median().clip(roi)
    return median.set('year', year)

ndvi_list = ee.ImageCollection([yearly_composite(y) for y in years])


# In[9]:


# 🎨 إعداد الأسماء والعرض
layer_names = ['NDVI ' + str(y) for y in years]
ndvi_vis = {
    'min': -1,
    'max': 1,
    'palette': [
        'blue',     # مياه أو مناطق سالبة NDVI
        'white',    # مناطق بدون نباتات
        'yellow',   # بداية وجود نباتات
        'green',    # غطاء نباتي متوسط
        'darkgreen' # غطاء نباتي كثيف
    ]
}


# In[10]:


# 🗺️ الخريطة السحرية
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

# ✅ إضافة مفتاح الطبقات
Map.addLayerControl()

# ✅ إضافة زر الأدوات (🔧)
Map.add_inspector()








Map


# In[ ]:
