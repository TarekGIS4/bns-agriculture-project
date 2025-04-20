import streamlit as st

# إضافة اللوجو في أعلى الصفحة
col1, col2, col3 = st.columns([1, 8, 1])

# في العمود الأول (يسار) إضافة اللوجو الأول
with col1:
    st.image("https://d.top4top.io/p_3396wqyxt1.png", width=100)  # اللوجو الأول
    st.image("https://f.top4top.io/p_3396bpsyi1.png", width=100)  # اللوجو الثاني

# في العمود الأوسط إضافة عنوان الصفحة
with col2:
    st.markdown("# Landsat 5 و Landsat 8  بيانات الاقمار الصناعية المستخدمة")  # عنوان الصفحة 

# في العمود الثالث (يمين) إضافة اللوجو الجديد
with col3:
    st.image("https://d.top4top.io/p_33967cx431.png", width=100)  # اللوجو الجديد

# عرض الجدول
st.write("""
| **Band**         | **Usage**                           | **Landsat 5 TM (µm)** | **Landsat 8 OLI/TIRS (µm)** | **Spatial Resolution** |
|------------------|-------------------------------------|-----------------------|----------------------------|------------------------|
| **SR_B1**        | Blue (Water and Snow)               | 0.45 – 0.52           | 0.43 – 0.45 (Coastal)      | 30m                    |
| **SR_B2**        | Green (Vegetation)                  | 0.52 – 0.60           | 0.45 – 0.51 (Blue)         | 30m                    |
| **SR_B3**        | Red (Vegetation, Soil)              | 0.63 – 0.69           | 0.53 – 0.59 (Green)        | 30m                    |
| **SR_B4**        | NIR (Water and Vegetation)          | 0.76 – 0.90           | 0.64 – 0.67 (Red)          | 30m                    |
| **SR_B5**        | SWIR-1 (Moisture)                   | 1.55 – 1.75           | 0.85 – 0.88 (NIR)          | 30m                    |
| **SR_B6**        | TIR (Thermal)                       | 10.40 – 12.50         | 1.57 – 1.65 (SWIR-1)       | 120/100m               |
| **SR_B7**        | SWIR-2 (Rock Discrimination)        | 2.08 – 2.35           | 2.11 – 2.29 (SWIR-2)       | 30m                    |
| **SR_B10/11**    | -                                   | Not Available         | 10.60 – 12.51 (Thermal)    | 100m                   |

### معلومات إضافية:

| **Property**      | **Landsat 5**     | **Landsat 8**     |
|-------------------|-------------------|-------------------|
| **Sensor Type**   | TM (Thematic Mapper) | OLI/TIRS         |
| **Operational Years** | 1984 – 2012   | 2013 – Present    |
| **Temporal Resolution** | 16 days      | 16 days           |
| **Number of Bands**   | 7              | 11                |
| **Calibration Type**   | SR (Surface Reflectance) | SR (Surface Reflectance) |
""")
import pandas as pd
import streamlit as st
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

# تعريف البيانات في شكل DataFrame
data = {"""
| **Band**         | **Usage**                           | **Landsat 5 TM (µm)** | **Landsat 8 OLI/TIRS (µm)** | **Spatial Resolution** |
|------------------|-------------------------------------|-----------------------|----------------------------|------------------------|
| **SR_B1**        | Blue (Water and Snow)               | 0.45 – 0.52           | 0.43 – 0.45 (Coastal)      | 30m                    |
| **SR_B2**        | Green (Vegetation)                  | 0.52 – 0.60           | 0.45 – 0.51 (Blue)         | 30m                    |
| **SR_B3**        | Red (Vegetation, Soil)              | 0.63 – 0.69           | 0.53 – 0.59 (Green)        | 30m                    |
| **SR_B4**        | NIR (Water and Vegetation)          | 0.76 – 0.90           | 0.64 – 0.67 (Red)          | 30m                    |
| **SR_B5**        | SWIR-1 (Moisture)                   | 1.55 – 1.75           | 0.85 – 0.88 (NIR)          | 30m                    |
| **SR_B6**        | TIR (Thermal)                       | 10.40 – 12.50         | 1.57 – 1.65 (SWIR-1)       | 120/100m               |
| **SR_B7**        | SWIR-2 (Rock Discrimination)        | 2.08 – 2.35           | 2.11 – 2.29 (SWIR-2)       | 30m                    |
| **SR_B10/11**    | -                                   | Not Available         | 10.60 – 12.51 (Thermal)    | 100m                   |

### معلومات إضافية:

| **Property**      | **Landsat 5**     | **Landsat 8**     |
|-------------------|-------------------|-------------------|
| **Sensor Type**   | TM (Thematic Mapper) | OLI/TIRS         |
| **Operational Years** | 1984 – 2012   | 2013 – Present    |
| **Temporal Resolution** | 16 days      | 16 days           |
| **Number of Bands**   | 7              | 11                |
| **Calibration Type**   | SR (Surface Reflectance) | SR (Surface Reflectance) |
"""
}

df = pd.DataFrame(data)

# عرض الجدول في الصفحة
st.write(df)

# زر تحميل CSV
csv = df.to_csv(index=False).encode('utf-8')
st.download_button(
    label="Download as CSV",
    data=csv,
    file_name="landsat_comparison.csv",
    mime="text/csv"
)

# وظيفة لتحويل DataFrame إلى PDF
def convert_df_to_pdf(df):
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    c.setFont("Helvetica", 10)
    text_object = c.beginText(40, 750)
    
    # رأس الجدول
    text_object.textLine("Band\tUsage\tLandsat 5 TM (µm)\tLandsat 8 OLI/TIRS (µm)\tSpatial Resolution")
    
    # البيانات
    for index, row in df.iterrows():
        text_object.textLine(f"{row['Band']}\t{row['Usage']}\t{row['Landsat 5 TM (µm)']}\t{row['Landsat 8 OLI/TIRS (µm)']}\t{row['Spatial Resolution']}")
    
    c.drawText(text_object)
    c.showPage()
    c.save()

    buffer.seek(0)
    return buffer

# زر تحميل PDF
pdf = convert_df_to_pdf(df)
st.download_button(
    label="Download as PDF",
    data=pdf,
    file_name="landsat_comparison.pdf",
    mime="application/pdf"
)
