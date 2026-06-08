import pandas as pd
import numpy as np
import os
import urllib.request
import streamlit as st

# ==========================================
# FUNGSIONAL: DOWNLOAD FONT POPPINS OTOMATIS
# ==========================================
@st.cache_data(show_spinner=False)
def load_poppins_fonts():
    reg_url = "https://github.com/google/fonts/raw/main/ofl/poppins/Poppins-Regular.ttf"
    bold_url = "https://github.com/google/fonts/raw/main/ofl/poppins/Poppins-Bold.ttf"
    
    reg_path = "Poppins-Regular.ttf"
    bold_path = "Poppins-Bold.ttf"
    
    if not os.path.exists(reg_path):
        try:
            urllib.request.urlretrieve(reg_url, reg_path)
        except:
            pass
            
    if not os.path.exists(bold_path):
        try:
            urllib.request.urlretrieve(bold_url, bold_path)
        except:
            pass
            
    return reg_path, bold_path

# ==========================================
# PIPELINE PEMBERSIHAN (ETL CORE LOGIC)
# ==========================================
def process_core_data(uploaded_files, use_filter, start_date, end_date, use_pump_test_filter):
    list_raw_df = []
    for file in uploaded_files:
        try:
            raw_df = pd.read_excel(file)
            list_raw_df.append(raw_df)
        except Exception as e:
            st.error(f"Gagal membaca file {file.name}: {e}")
            
    if not list_raw_df:
        return pd.DataFrame()
        
    df = pd.concat(list_raw_df, ignore_index=True)
    df.columns = df.columns.str.strip()

    if 'ID' in df.columns:
        df['ID_clean'] = df['ID'].astype(str).str.upper().str.strip()
        df = df[df['ID_clean'] != 'TOTAL']
        df = df.drop(columns=['ID_clean'])

    kolom_angka = ['Price', 'Volume (L)', 'Value (Rp.)']
    for col in kolom_angka:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
    df = df.dropna(subset=[col for col in kolom_angka if col in df.columns])

    if 'Date' in df.columns:
        df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
        if use_filter and start_date and end_date:
            batas_awal = pd.to_datetime(start_date) + pd.Timedelta(hours=6)
            batas_akhir = pd.to_datetime(end_date) + pd.Timedelta(days=1, hours=6)
            df = df[(df['Date'] >= batas_awal) & (df['Date'] < batas_akhir)]

    if df.empty:
        return df

    if 'ID' in df.columns:
        df = df.drop_duplicates(subset=['ID'], keep='first')

    jam = df['Date'].dt.hour
    kondisi_shift = [
        (jam >= 6) & (jam < 14),
        (jam >= 14) & (jam < 22),
        (jam >= 22) | (jam < 6)
    ]
    df['Shift'] = np.select(kondisi_shift, ['1', '2', '3'], default='Unknown')
    
    if 'Time' in df.columns:
        df['Time'] = pd.to_datetime(df['Time']).dt.strftime('%H:%M:%S')
    df['Date'] = df['Date'].dt.strftime('%Y-%m-%d')

    if 'Pu / H / Product' in df.columns:
        split_php = df['Pu / H / Product'].str.split(r'\s*/\s*', expand=True)
        if split_php.shape[1] >= 3:
            df['Pump'] = split_php[0]
            df['Hose'] = split_php[1]
            df['Product'] = split_php[2]
        else:
            df['Pump'] = split_php[0] if split_php.shape[1] > 0 else '-'
            df['Hose'] = split_php[1] if split_php.shape[1] > 1 else '-'
            df['Product'] = '-'
        df = df.drop(columns=['Pu / H / Product'])

    if 'Payment' in df.columns:
        split_payment = df['Payment'].str.split(n=1, expand=True)
        df['Payment_Method'] = split_payment[0]
        if split_payment.shape[1] > 1:
            df['License_Plate'] = split_payment[1].fillna('-')
        else:
            df['License_Plate'] = '-'
        df = df.drop(columns=['Payment'])

    if use_pump_test_filter and 'Payment_Method' in df.columns:
        df = df[~df['Payment_Method'].astype(str).str.upper().str.strip().isin(['PUMP', 'PUMP_TEST', 'PUMPTEST'])]

    df = df.sort_values(by=['Date', 'Time']).reset_index(drop=True)
    return df