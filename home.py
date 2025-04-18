import streamlit as st
import leafmap.foliumap as leafmap

st.set_page_config(layout="wide")

st.sidebar.title("عن المشروع")
st.sidebar.info("مشروع تخرج الفرقة الرابعة كلية آداب جامعة بني سويف\nبرنامج مساحة ونظم معلومات جغرافية")
logo = "https://i.ibb.co/KpW5J9m/20110405173531.png"
st.sidebar.image(logo)

st.title("🛰️ مشروع مراقبة الغطاء النباتي (NDVI) باستخدام الأقمار الصناعية")

st.markdown(
    """
    هذا التطبيق يتيح تحليل السلاسل الزمنية لمؤشر NDVI من سنة 1984 إلى 2024، باستخدام بيانات Landsat 5 و 8 داخل الظهير الصحراوي لمحافظة بني سويف، مصر.
    """
)

m = leafmap.Map(minimap_control=True)
m.add_basemap("Esri.WorldImagery")
m.to_streamlit(height=500)
