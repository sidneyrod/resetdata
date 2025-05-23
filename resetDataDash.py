import streamlit as st
import pandas as pd
import os
from PIL import Image
import plotly.express as px
import base64
from io import BytesIO
import zipfile
import tempfile

# Set page configuration
st.set_page_config(page_title="ReSet Dashboard", page_icon="kent_icon.ico", layout="wide")

# Hide Streamlit default header and footer
st.markdown("""
    <style>
        header {visibility: hidden;}
        footer {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

# Global list for temporary image directories
temp_img_dirs = []

# Sidebar for file uploads
with st.sidebar:
    st.markdown("### 📁 Upload & Filters")
    uploaded_file = st.file_uploader("📄 Upload your .xlsm, .xlsx or .csv file", type=["xlsm", "xlsx", "csv"])
    uploaded_zips = st.file_uploader("🖼️ Upload .zip file(s) with images", type=["zip"], accept_multiple_files=True)
    st.markdown("---")
    st.markdown(
        '''
        <div style='background: linear-gradient(145deg, #2E8B57, #3fa76c); padding: 15px; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.3); color: white; text-align: center; font-size: 15px; line-height: 1.6; margin-top: 20px;'>
            <div style="font-size: 22px; margin-bottom: 8px;">✨ Team</div>
            <div>📝 <strong>Designed by</strong><br>Gabriela Reis</div>
            <div style="margin-top: 8px;">💻 <strong>Developed by</strong><br>Sidney Rodrigues</div>
        </div>
        ''',
        unsafe_allow_html=True
    )

    # Extract zip files if uploaded
    if uploaded_zips:
        for uploaded_zip in uploaded_zips:
            temp_dir = tempfile.TemporaryDirectory()
            with zipfile.ZipFile(uploaded_zip, "r") as zip_ref:
                zip_ref.extractall(temp_dir.name)
            temp_img_dirs.append(temp_dir.name)

# Function to convert image to base64
def image_to_base64(path):
    with open(path, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode()

# Function to read uploaded file
@st.cache_data(show_spinner="🗓️ Reading file...")
def read_file(file):
    filename = file.name.lower()
    if filename.endswith(".csv"):
        return pd.read_csv(file), pd.DataFrame(), pd.DataFrame()

    xls = pd.ExcelFile(file, engine="openpyxl")

    # Try to find the main sheet called "Data" (case insensitive)
    main_sheet = None
    for sheet in xls.sheet_names:
        if str(sheet).strip().lower() == "data":
            main_sheet = sheet
            break
    if main_sheet is None:
        main_sheet = xls.sheet_names[0]  # Fallback to the first sheet

    data_df = pd.read_excel(xls, sheet_name=main_sheet)

    # Map column names from Portuguese to standard English names
    column_mapping = {
        'Finalizado Em': 'FinishTime',
        'Title': 'Store',
        'ScanValue': 'bay number',
        'Fornecedor': 'Vendor',
        'Programa': 'Program',
    }
    for original, new in column_mapping.items():
        if original in data_df.columns and new not in data_df.columns:
            data_df[new] = data_df[original]

    try:
        summary_df = pd.read_excel(xls, sheet_name="Summary")
    except:
        summary_df = pd.DataFrame()

    try:
        reset_df = pd.read_excel(xls, sheet_name="Reset_Update")
    except:
        reset_df = pd.DataFrame()

    return data_df, summary_df, reset_df

# Load logo
logo_base64 = ""
if os.path.exists("assets/logo_kent.jpeg"):
    logo_base64 = image_to_base64("assets/logo_kent.jpeg")

st.markdown(f"""
<div style='text-align: center; margin: 0; padding: 0;'>
    <img src='data:image/jpeg;base64,{logo_base64}' width='200' style='border-radius: 10px; margin-bottom: 15px;' />
    <h1 style='color: #2E8B57; font-weight: 700; font-size: 2.5em; margin: 0;'>Reset Supported Programs</h1>
    <hr style='border: 1px solid #2E8B57; margin: 6px auto 0 auto; width: 100%;'>
</div>
""", unsafe_allow_html=True)

# Process uploaded file
if uploaded_file:
    data_df, summary_df, reset_df = read_file(uploaded_file)

    if 'FinishTime' in data_df.columns:
        data_df['FinishTime'] = pd.to_datetime(data_df['FinishTime'], errors='coerce', dayfirst=True)

    for col in ['bay number', 'Vendor', 'Program', 'Store']:
        if col in data_df.columns:
            data_df[col] = data_df[col].astype(str).str.upper().str.strip()

    default_vendor = data_df['Vendor'].dropna().unique()[0]
    default_program = data_df[data_df['Vendor'] == default_vendor]['Program'].dropna().unique()[0]

    # Filters
    st.markdown("""
        <style>
            .label-style {
                font-weight: 600;
                color: white;
                font-size: 15px;
                margin-bottom: 4px;
                display: block;
            }
            div[data-baseweb="select"] {
                font-size: 15px;
            }
        </style>
    """, unsafe_allow_html=True)

    col_v1, col_v2 = st.columns([1, 1])
    with col_v1:
        st.markdown("<span class='label-style'>🔎 Select a Vendor</span>", unsafe_allow_html=True)
        selected_vendor = st.selectbox("", sorted(data_df['Vendor'].dropna().unique()), key="vendor", label_visibility="collapsed")

    with col_v2:
        vendor_programs = sorted(data_df[data_df['Vendor'] == selected_vendor]['Program'].dropna().unique())
        st.markdown("<span class='label-style'>🎯 Select a Program</span>", unsafe_allow_html=True)
        selected_program = st.selectbox("", vendor_programs, key="program", label_visibility="collapsed")

    filtered_df = data_df[(data_df['Vendor'] == selected_vendor) & (data_df['Program'] == selected_program)]

    # Period analyzed
    valid_dates_df = filtered_df[filtered_df['FinishTime'].notna()]
    if not valid_dates_df.empty:
        start_date = valid_dates_df['FinishTime'].min().date()
        end_date = valid_dates_df['FinishTime'].max().date()
        st.markdown(f"""
        <div style='display: flex; justify-content: center; margin: 5px 0 30px 0;'>
            <div style='background-color: #2E8B57; color: white; padding: 10px 20px; border-radius: 12px; font-size: 15px; font-weight: 500;'>
                🗓️ Period analyzed: <strong>{start_date.strftime('%b %d, %Y')}</strong> to <strong>{end_date.strftime('%b %d, %Y')}</strong>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # KPIs
    num_stores = filtered_df['Store'].nunique()
    num_bays = filtered_df['bay number'].nunique()
    num_maint = len(filtered_df)
    avg_per_bay = round(num_maint / num_bays, 2) if num_bays else 0
    num_resets = len(reset_df[(reset_df['Vendor'].str.upper().str.strip() == selected_vendor) & (reset_df['Program'].str.upper().str.strip() == selected_program)]) if not reset_df.empty else 0

    col_left, col_right = st.columns([1, 1], gap="medium")

    with col_left:
        st.markdown("### 📊 Overview")
        st.markdown("""
        <style>
        .kpi-box {
            background-color: #1E1E1E;
            border-radius: 16px;
            padding: 20px;
            text-align: center;
            box-shadow: 0 4px 10px rgba(0,0,0,0.4);
        }
        .kpi-title {
            font-size: 18px;
            font-weight: 600;
            color: white;
            margin-bottom: 10px;
        }
        .kpi-value {
            font-size: 32px;
            font-weight: bold;
            color: white;
        }
        </style>
        """, unsafe_allow_html=True)

        st.markdown(f"""
        <div style='display: grid; grid-template-columns: 1fr 1fr; gap: 10px;'>
            <div class='kpi-box'><div class='kpi-title'>🏪 Stores</div><div class='kpi-value'>{num_stores}</div></div>
            <div class='kpi-box'><div class='kpi-title'>📦 Bays</div><div class='kpi-value'>{num_bays}</div></div>
            <div class='kpi-box'><div class='kpi-title'>🚰 Maintenances</div><div class='kpi-value'>{num_maint}</div></div>
            <div class='kpi-box'><div class='kpi-title'>🔁 Resets / Updates</div><div class='kpi-value'>{num_resets}</div></div>
            <div class='kpi-box' style='grid-column: span 2;'><div class='kpi-title'>📉 Avg. per Bay</div><div class='kpi-value'>{avg_per_bay}</div></div>
        </div>
        """, unsafe_allow_html=True)

        # Store list
        store_list = sorted(filtered_df['Store'].unique())
        if store_list:
            st.markdown("""
            <div style='margin-top: 35px;'>
                <h3 style='margin-bottom: 12px; color: white; font-size: 24px;'>🏪 Store List</h3>
            </div>
            """, unsafe_allow_html=True)

            cards = []
            for store in store_list:
                cards.append(f"<div style='background-color: #333; color: white; padding: 6px 12px; border-radius: 8px; font-size: 14px; box-shadow: 0 2px 6px rgba(0,0,0,0.3);'>{store}</div>")
            stores_div = "<div style='display: flex; flex-wrap: wrap; gap: 10px;'>" + "".join(cards) + "</div>"
            st.markdown(stores_div, unsafe_allow_html=True)

    with col_right:
        # render program image
        st.markdown("### 🖼️ Bay Image")
        image = None
        image_caption = ""

        # try all zip folders
        for zip_dir in temp_img_dirs:
            for file in os.listdir(zip_dir):
                if file.lower().startswith(selected_program.lower()) and file.lower().endswith(('.jpg', '.png', '.jpeg')):
                    image_path = os.path.join(zip_dir, file)
                    image = Image.open(image_path)
                    image_caption = file
                    break
            if image:
                break

        # if not found, check local image folder
        if image is None:
            image_dir = os.path.join(os.getcwd(), "images")
            if os.path.exists(image_dir):
                for file in os.listdir(image_dir):
                    if file.lower().startswith(selected_program.lower()) and file.lower().endswith(('.jpg', '.png', '.jpeg')):
                        image_path = os.path.join(image_dir, file)
                        image = Image.open(image_path)
                        image_caption = file
                        break

        if image:
            buffered = BytesIO()
            image.save(buffered, format="PNG")
            img_base64 = base64.b64encode(buffered.getvalue()).decode()

            st.markdown(f"""
            <div style='text-align: center;'>
                <img src='data:image/png;base64,{img_base64}' style='max-height: 430px; width: auto; border-radius: 10px; box-shadow: 0 4px 10px rgba(0,0,0,0.4);'/>
                <div style='color: #ccc; font-size: 14px; margin-top: 8px;'>{image_caption}</div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.info(f"No image found for program '{selected_program}'.")

    # Charts section
    st.markdown("---")
    st.markdown("### 📈 Charts")

    col_chart, _ = st.columns([1, 1])
    with col_chart:
        st.markdown("<span class='label-style'>📌 Select Chart Type</span>", unsafe_allow_html=True)
        chart_type = st.selectbox(
            "",
            ["Maintenance by Month", "Resets by Program", "Maintenance by Store", "Resets by Store"],
            key="chart",
            label_visibility="collapsed"
        )

    # Chart theme logic
    if "Maintenance" in chart_type:
        selected_template = "plotly_dark"
        selected_color_scale = "Teal"
    else:
        selected_template = "plotly_dark"
        selected_color_scale = "Blues"

    # Charts
    if chart_type == "Maintenance by Month":
        if 'FinishTime' in filtered_df.columns:
            month_df = filtered_df.dropna(subset=['FinishTime'])
            month_df['Month'] = month_df['FinishTime'].dt.to_period('M').astype(str)
            chart_df = month_df.groupby('Month').size().reset_index(name='Maintenance Count')
            fig = px.bar(chart_df, x='Month', y='Maintenance Count',
                         title='Maintenance Count per Month',
                         template=selected_template, color='Maintenance Count',
                         color_continuous_scale=selected_color_scale)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("Column 'FinishTime' not found in the file.")

    elif chart_type == "Resets by Program":
        reset_chart_df = reset_df[
            (reset_df['Vendor'].str.upper().str.strip() == selected_vendor) &
            (reset_df['Program'].str.upper().str.strip() == selected_program)
        ] if not reset_df.empty else pd.DataFrame()

        if not reset_chart_df.empty:
            reset_chart_df = reset_chart_df.groupby('Program').size().reset_index(name='Reset Count')
            fig = px.bar(reset_chart_df, x='Reset Count', y='Program', orientation='h',
                         title='Resets / Updates per Program',
                         template=selected_template, color='Reset Count',
                         color_continuous_scale=selected_color_scale)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No reset/update data available for this selection.")

    elif chart_type == "Maintenance by Store":
        if 'Store' in filtered_df.columns:
            chart_df = filtered_df.groupby('Store').size().reset_index(name='Maintenance Count')
            fig = px.bar(chart_df, x='Store', y='Maintenance Count',
                         title='Maintenance Count by Store',
                         template=selected_template, color='Maintenance Count',
                         color_continuous_scale=selected_color_scale)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("Column 'Store' not found.")

    elif chart_type == "Resets by Store":
        reset_chart_df = reset_df[
            (reset_df['Vendor'].str.upper().str.strip() == selected_vendor) &
            (reset_df['Program'].str.upper().str.strip() == selected_program)
        ] if not reset_df.empty else pd.DataFrame()

        if 'Store' in reset_chart_df.columns and not reset_chart_df.empty:
            chart_df = reset_chart_df.groupby('Store').size().reset_index(name='Reset Count')
            fig = px.bar(chart_df, x='Store', y='Reset Count',
                         title='Resets / Updates by Store',
                         template=selected_template, color='Reset Count',
                         color_continuous_scale=selected_color_scale)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No reset/update data available per store for this selection.")


