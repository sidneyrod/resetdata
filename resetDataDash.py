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
# 🎛️ SIDEBAR – File paths and filters
# ================================
with st.sidebar:
    st.title("📂 Upload & Filters")

    # File path input
    excel_path = st.text_input("📄 Enter data file path (.csv or .xlsx)", value="")

    # Image folder path
    image_folder = st.text_input("🖼️ Enter image folder path", value="")

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
# 📁 File processing
# ================================
if os.path.exists(excel_path):
    ext = os.path.splitext(excel_path)[-1]
    reset_df = None  # placeholder for Reset_Update

    # Excel or CSV
    if ext == ".csv":
        df = pd.read_csv(excel_path)
    elif ext in [".xls", ".xlsx"]:
        xls = pd.ExcelFile(excel_path, engine="openpyxl")
        df = pd.read_excel(xls, sheet_name=0)

        # Try loading Reset_Update sheet
        if "Reset_Update" in xls.sheet_names:
            reset_df = pd.read_excel(xls, sheet_name="Reset_Update")
    else:
        st.error("Unsupported file format. Please use .csv or .xlsx.")
        st.stop()

    # Filters
    col_f1, col_f2 = st.columns(2)
    with col_f1:
        vendors = sorted(df['Vendor'].dropna().unique())
        selected_vendor = st.selectbox("🔎 Select a Vendor", vendors)
    with col_f2:
        vendor_df = df[df['Vendor'] == selected_vendor]
        programs = sorted(vendor_df['Program'].dropna().unique())
        selected_program = st.selectbox("🎯 Select a Program", programs)

    # Apply filters
    filtered_df = vendor_df[vendor_df['Program'] == selected_program]

    # ================================
    # 📌 METRICS CARDS (with Resets/Updates)
    # ================================
    num_stores = filtered_df['Store'].nunique() if 'Store' in filtered_df.columns else 0
    num_bags = filtered_df['Bag'].nunique() if 'Bag' in filtered_df.columns else 0
    num_maint = len(filtered_df)
    avg_maint_per_bag = round(num_maint / num_bags, 2) if num_bags else 0

    # Count Reset/Update
    num_resets = 0
    if reset_df is not None:
        num_resets = len(reset_df[
            (reset_df['Vendor'] == selected_vendor) &
            (reset_df['Program'] == selected_program)
        ])

    st.markdown("### 📈 Overview")
    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("🏪 Number of Stores", num_stores)
    col2.metric("👜 Number of Bags", num_bags)
    col3.metric("🛠️ Maintenance Records", num_maint)
    col4.metric("📊 Avg. Maint. per Bag", avg_maint_per_bag)
    col5.metric("🔁 Resets / Updates", num_resets)

    st.markdown("---")

    # ================================
    # 📊 INTERACTIVE CHARTS with TABS
    # ================================
    st.markdown("### 📉 Charts")

    tab1, tab2 = st.tabs(["📊 Maintenance per Store", "🔁 Resets per Program"])

    with tab1:
        if 'Store' in filtered_df.columns:
            store_chart = filtered_df.groupby('Store').size().reset_index(name='Maintenance Count')
            fig = px.bar(store_chart, x='Store', y='Maintenance Count',
                         title='Maintenance Count per Store',
                         labels={'Maintenance Count': 'Total'},
                         template='plotly_white')
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
                             x='Reset Count',
                             y='Program',
                             orientation='h',
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
    # 🖼️ VENDOR IMAGE
    # ================================
    st.markdown("### 🖼️ Program Image")
    image_name = selected_vendor.strip() + ".jpg"
    image_path = os.path.join(image_folder, image_name)

    if os.path.exists(image_path):
        image = Image.open(image_path)
        st.image(image, caption=f"Image for {selected_vendor}", use_column_width=True)
    else:
        st.info(f"No image found for '{selected_vendor}'.")

else:
    st.info("Please enter a valid file path in the sidebar.")
