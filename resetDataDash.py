import streamlit as st
import pandas as pd
import os
from PIL import Image
import plotly.express as px

# 🎨 Page setup
st.set_page_config(
    page_title="ReSet Dashboard",
    page_icon="kent_icon.ico",
    layout="wide"
)

# ================================
# 🏠 SIDEBAR – Secure Upload & Filters
# ================================
with st.sidebar:
    st.title("📂 Upload & Filters")

    # Upload Excel or CSV file
    uploaded_file = st.file_uploader("📄 Upload your data file (.csv or .xlsx)", type=["csv", "xlsx"])

    # Optional image upload
    uploaded_image = st.file_uploader("🖼️ Upload an image (optional)", type=["jpg", "png"])

    st.markdown("---")
    st.markdown(
        """
        <div style='
            padding: 10px;
            background-color: #2E8B57;
            border-radius: 8px;
            color: white;
            text-align: center;
            font-weight: bold;
            font-size: 14px;
            margin-top: 20px;
        '>
            🚀 Developed by Reset Moncton Team
        </div>
        """,
        unsafe_allow_html=True
    )

# ================================
# 📊 HEADER
# ================================
st.markdown("<h1 style='text-align: center; color: #2E8B57;'>RESET SUPPORTED PROGRAMS</h1>", unsafe_allow_html=True)
st.markdown("---")

# ================================
# 📅 FILE PROCESSING
# ================================
if uploaded_file:
    ext = os.path.splitext(uploaded_file.name)[-1]
    reset_df = None

    if ext == ".csv":
        df = pd.read_csv(uploaded_file)
    elif ext in [".xls", ".xlsx"]:
        xls = pd.ExcelFile(uploaded_file, engine="openpyxl")
        df = pd.read_excel(xls, sheet_name=0)

        if "Reset_Update" in xls.sheet_names:
            reset_df = pd.read_excel(xls, sheet_name="Reset_Update")
    else:
        st.error("Unsupported file format.")
        st.stop()

    # Filters
    col_f1, col_f2 = st.columns(2)
    with col_f1:
        vendors = sorted(df['Vendor'].dropna().unique())
        selected_vendor = st.selectbox("🔍 Select a Vendor", vendors)
    with col_f2:
        vendor_df = df[df['Vendor'] == selected_vendor]
        programs = sorted(vendor_df['Program'].dropna().unique())
        selected_program = st.selectbox("🎯 Select a Program", programs)

    filtered_df = vendor_df[vendor_df['Program'] == selected_program]

    # ================================
    # 📅 METRICS
    # ================================
    num_stores = filtered_df['Store'].nunique() if 'Store' in filtered_df.columns else 0
    num_bags = filtered_df['Bag'].nunique() if 'Bag' in filtered_df.columns else 0
    num_maint = len(filtered_df)
    avg_maint_per_bag = round(num_maint / num_bags, 2) if num_bags else 0

    num_resets = 0
    if reset_df is not None:
        num_resets = len(reset_df[
            (reset_df['Vendor'] == selected_vendor) &
            (reset_df['Program'] == selected_program)
        ])

    st.markdown("### 📊 Overview")
    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("🏪 Number of Stores", num_stores)
    col2.metric("👜 Number of Bags", num_bags)
    col3.metric("🛠️ Maintenance Records", num_maint)
    col4.metric("📊 Avg. Maint. per Bag", avg_maint_per_bag)
    col5.metric("🔁 Resets / Updates", num_resets)

    st.markdown("---")

    # ================================
    # 📊 CHARTS WITH TABS
    # ================================
    st.markdown("### 📉 Charts")
    tab1, tab2 = st.tabs(["📊 Maintenance per Store", "🔁 Resets per Program"])

    with tab1:
        if 'Store' in filtered_df.columns:
            store_chart = filtered_df.groupby('Store').size().reset_index(name='Maintenance Count')
            fig = px.bar(store_chart, x='Store', y='Maintenance Count',
                         title='<b>Maintenance Count per Store</b>',
                         labels={'Store': '<b>Store</b>', 'Maintenance Count': '<b>Maintenance Count</b>'},
                         template='plotly_dark',
                         color='Maintenance Count',
                         color_continuous_scale='Blues')
            fig.update_layout(
                title_font_size=20,
                font=dict(size=12, color='white'),
                xaxis_title_font=dict(size=14, color='white'),
                yaxis_title_font=dict(size=14, color='white'),
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)'
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("No 'Store' column found for plotting.")

    with tab2:
        if reset_df is not None:
            vendor_resets = reset_df[reset_df['Vendor'] == selected_vendor]
            if not vendor_resets.empty:
                reset_by_program = vendor_resets.groupby('Program').size().reset_index(name='Reset Count')
                reset_by_program = reset_by_program.sort_values(by='Reset Count', ascending=True)

                fig = px.bar(reset_by_program,
                             x='Reset Count', y='Program', orientation='h',
                             title=f"Resets / Updates for {selected_vendor}",
                             template='plotly_dark',
                             color='Reset Count',
                             color_continuous_scale='Aggrnyl')
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No Reset/Update records found for this vendor.")
        else:
            st.warning("No Reset_Update data found.")

    st.markdown("---")

    # ================================
    # 🖼️ IMAGE DISPLAY
    # ================================
    st.markdown("### 🖼️ Program Image")
    if uploaded_image:
        image = Image.open(uploaded_image)
        st.image(image, caption="Uploaded Image", use_column_width=True)
    else:
        st.info("Upload an image to display it here.")

else:
    st.info("Please upload a valid data file in the sidebar.")
