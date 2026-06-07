import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import os
import urllib.request
import io

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

font_reg_p, font_bold_p = load_poppins_fonts()

try:
    font_regular = fm.FontProperties(fname=font_reg_p)
    font_bold = fm.FontProperties(fname=font_bold_p)
except:
    font_regular = fm.FontProperties(family='sans-serif')
    font_bold = fm.FontProperties(family='sans-serif', weight='bold')

# ==========================================
# 1. KONFIGURASI NAVIGASI HALAMAN (SIDEBAR)
# ==========================================
st.set_page_config(
    page_title="Sistem Konsolidasi Data Hose Delivery",
    page_icon="⛽",
    layout="wide"
)

st.sidebar.markdown("# 🧭 Menu Navigasi")
halaman = st.sidebar.radio(
    "Pilih Halaman Aplikasi:",
    ["Konsolidasi Data", "Executive Dashboard"]
)

st.sidebar.markdown("---")
st.sidebar.caption("Sistem Konsolidasi & Visualisasi Data HOSE Delivery v2.0")

# Pipeline Pembersihan Fungsi Bersama (Shared Core Pipeline)
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


# ==========================================
# HALAMAN 1: KONSOLIDASI DATA
# ==========================================
if halaman == "Konsolidasi Data":
    st.title("⛽ Sistem Konsolidasi Data Hose Delivery")
    st.markdown("Aplikasi web universal untuk membersihkan, merapikan, dan mengonsolidasikan banyak file laporan mentah HOSE Delivery Excel (.xlsx) menjadi satu file Master CSV.")
    st.markdown("---")

    row1_col1, row1_col2 = st.columns(2)
    with row1_col1:
        st.markdown("### 📋 Unggah File Mentah Excel")
        uploaded_files = st.file_uploader("Pilih dan unggah satu atau beberapa file laporan (.xlsx)", type=['xlsx'], accept_multiple_files=True, key="upload_page1")
    with row1_col2:
        st.markdown("### 💾 Nama File Output")
        nama_output = st.text_input("Tentukan nama file hasil ekspor akhir", value="HOSE_Master_Consolidated", key="out_page1")
        st.caption("Format otomatis berupa .csv")

    st.markdown("---")

    start_date = None
    end_date = None

    row2_col1, row2_col2 = st.columns(2)
    with row2_col1:
        st.markdown("### 📅 Filter Tanggal Operasional")
        use_filter = st.checkbox("Aktifkan Batasan Tanggal Operasional", value=False, key="filter_page1")
        if use_filter:
            col_start, col_end = st.columns(2)
            with col_start: start_date = st.date_input("Tanggal Awal:", key="s_p1")
            with col_end: end_date = st.date_input("Tanggal Akhir:", key="e_p1")
    with row2_col2:
        st.markdown("### 🧪 Filter Transaksi Pump Test")
        use_pump_test_filter = st.checkbox("Eliminasi Transaksi Pump Test / Tera Pompa", value=False, key="pump_page1")

    st.markdown("---")

    if uploaded_files:
        if use_filter and start_date > end_date:
            st.error("❌ Kesalahan: Tanggal Awal tidak boleh melewati Tanggal Akhir!")
        else:
            if st.button("🚀 Mulai Konsolidasi Data", type="primary", use_container_width=True):
                with st.spinner('Sedang mengolah data...'):
                    df_final = process_core_data(uploaded_files, use_filter, start_date, end_date, use_pump_test_filter)
                    if not df_final.empty:
                        st.session_state['shared_df'] = df_final
                        
                        st.success(f"🎉 Sukses! Sebanyak **{len(df_final):,} baris data transaksi** siap diunduh.")
                        st.dataframe(df_final.head(10), use_container_width=True)
                        csv_data = df_final.to_csv(index=False).encode('utf-8')
                        st.download_button(
                            label="📥 Unduh File Master Hasil Konsolidasi (.csv)",
                            data=csv_data,
                            file_name=f"{nama_output}.csv",
                            mime="text/csv",
                            type="primary",
                            use_container_width=True
                        )
                    else:
                        st.warning("⚠️ Data kosong setelah difilter.")
    else:
        st.info("💡 Petunjuk: Silakan unggah minimal satu file mentah laporan Excel (.xlsx) di atas untuk mengaktifkan sistem.")


# ==========================================
# HALAMAN 2: EXECUTIVE DASHBOARD
# ==========================================
elif halaman == "Executive Dashboard":
    st.title("📊 Executive Dashboard Analisis")
    st.markdown("Halaman khusus manajemen eksekutif untuk melihat visualisasi ringkasan performa penjualan dan operasional SPBU.")
    st.markdown("---")

    row1_col1, row1_col2 = st.columns(2)
    with row1_col1:
        st.markdown("### 📋 Unggah File Mentah Excel")
        uploaded_files = st.file_uploader("Pilih dan unggah satu atau beberapa file laporan (.xlsx)", type=['xlsx'], accept_multiple_files=True, key="upload_page2")
        
        if not uploaded_files and 'shared_df' in st.session_state:
            st.success("🔄 Terdeteksi otomatis: Menggunakan data aktif dari halaman Konsolidasi Data.")
    with row1_col2:
        st.markdown("### 💾 Nama File Output")
        nama_output = st.text_input("Tentukan nama file gambar hasil unduhan", value="Executive_Summary_Report", key="out_page2")

    st.markdown("---")

    start_date = None
    end_date = None

    row2_col1, row2_col2 = st.columns(2)
    with row2_col1:
        st.markdown("### 📅 Filter Tanggal Operasional")
        use_filter = st.checkbox("Aktifkan Batasan Tanggal Operasional", value=False, key="filter_page2")
        if use_filter:
            col_start, col_end = st.columns(2)
            with col_start: start_date = st.date_input("Tanggal Awal:", key="s_p2")
            with col_end: end_date = st.date_input("Tanggal Akhir:", key="e_p2")
    with row2_col2:
        st.markdown("### 🧪 Filter Transaksi Pump Test")
        use_pump_test_filter = st.checkbox("Eliminasi Transaksi Pump Test / Tera Pompa", value=False, key="pump_page2")

    st.markdown("---")

    row3_col1, row3_col2 = st.columns(2)
    with row3_col1:
        st.markdown("### 🎨 Pilih Jenis Analisis & Grafik")
        jenis_analisis = st.selectbox(
            "Pilih visualisasi data yang ingin ditampilkan:",
            ["Executive Summary"] 
        )
    with row3_col2:
        st.markdown("### 🖼️ Format Gambar Unduhan")
        format_gambar = st.radio(
            "Pilih format file gambar output:",
            ["PNG", "JPG"],
            horizontal=True
        )

    st.markdown("---")

    df_dashboard = pd.DataFrame()
    
    if uploaded_files:
        if use_filter and start_date > end_date:
            st.error("❌ Kesalahan: Tanggal Awal tidak boleh melewati Tanggal Akhir!")
        else:
            df_dashboard = process_core_data(uploaded_files, use_filter, start_date, end_date, use_pump_test_filter)
    elif 'shared_df' in st.session_state:
        df_dashboard = st.session_state['shared_df']

    if not df_dashboard.empty:
        if st.button("📊 Generate Visualisasi Data", type="primary", use_container_width=True):
            with st.spinner('Sedang menghitung metrik eksekutif...'):
                
                # --- KALKULASI INTERNAL METRIK OPERASIONAL ---
                total_tx = len(df_dashboard)
                
                # FIX MAJOR: Trik "Business Date" untuk membunuh jebakan tumpahan shift 05:59 pagi
                if 'Time' in df_dashboard.columns:
                    dt_combined = pd.to_datetime(df_dashboard['Date'].astype(str) + ' ' + df_dashboard['Time'].astype(str), errors='coerce')
                    # Tarik mundur 6 jam agar shift 3 keesokan paginya dikembalikan ke kalender hari operasional aslinya
                    business_dates = dt_combined - pd.Timedelta(hours=6)
                else:
                    business_dates = pd.to_datetime(df_dashboard['Date'], errors='coerce')
                
                # Sekarang sistem menghitung hari dan bulan murni berdasarkan Kalender Bisnis, bukan fisik.
                unique_b_dates = pd.to_datetime(business_dates.dt.date.dropna().unique())
                
                num_days = len(unique_b_dates)
                num_days = 1 if num_days == 0 else num_days 
                
                if len(unique_b_dates) > 0:
                    num_months = np.sum(1 / unique_b_dates.days_in_month)
                else:
                    num_months = 1
                num_months = 1 if num_months == 0 else num_months
                
                daily_tx = total_tx / num_days
                hourly_tx = total_tx / (num_days * 24)
                
                total_val = df_dashboard['Value (Rp.)'].sum()
                daily_val = total_val / num_days
                monthly_val = total_val / num_months
                
                total_vol = df_dashboard['Volume (L)'].sum()
                daily_vol = total_vol / num_days
                monthly_vol = total_vol / num_months
                
                pertalite_vol = df_dashboard[df_dashboard['Product'].astype(str).str.upper().str.strip() == 'PERTALITE']['Volume (L)'].sum()
                jbkp_share = (pertalite_vol / total_vol * 100) if total_vol > 0 else 0
                jbu_share = 100 - jbkp_share
                
                metrics = {
                    'daily_tx': daily_tx, 'hourly_tx': hourly_tx,
                    'daily_val': daily_val, 'monthly_val': monthly_val,
                    'daily_vol': daily_vol, 'monthly_vol': monthly_vol,
                    'jbkp_share': jbkp_share, 'jbu_share': jbu_share
                }

                # --- PROSES MENGGAMBAR METRIK KE MATPLOTLIB (RASIO 16:8) ---
                fig, axs = plt.subplots(2, 4, figsize=(16, 8), facecolor='#0e1117')
                fig.subplots_adjust(hspace=0.25, wspace=0.25, left=0.04, right=0.96, top=0.94, bottom=0.06)
                
                labels = [
                    ["Daily Transactions", "Hourly Transactions", "Daily Sales Value (IDR)", "Monthly Sales Value (IDR)"],
                    ["Daily Sales Volume (L)", "Monthly Sales Volume (L)", "JBKP Vol. Share (%)", "JBU Vol. Share (%)"]
                ]
                
                values = [
                    [f"{metrics['daily_tx']:,.1f}", f"{metrics['hourly_tx']:,.2f}", f"Rp {metrics['daily_val']:,.0f}", f"Rp {metrics['monthly_val']:,.0f}"],
                    [f"{metrics['daily_vol']:,.1f} L", f"{metrics['monthly_vol']:,.1f} L", f"{metrics['jbkp_share']:.2f}%", f"{metrics['jbu_share']:.2f}%"]
                ]
                
                for r in range(2):
                    for c in range(4):
                        ax = axs[r, c]
                        ax.set_facecolor('#1e222b') 
                        
                        for spine in ax.spines.values():
                            spine.set_color('#2d323f')
                            spine.set_linewidth(1.5)
                        
                        ax.set_xticks([])
                        ax.set_yticks([])
                        
                        ax.text(0.5, 0.68, labels[r][c].upper(), color='#9ca3af', fontsize=14, 
                                ha='center', va='center', fontproperties=font_regular)
                        
                        current_label = labels[r][c]
                        if "Value" in current_label:
                            text_color = "#10b981" 
                        elif "JBKP" in current_label:
                            text_color = "#f59e0b" 
                        elif "JBU" in current_label:
                            text_color = "#3b82f6" 
                        else:
                            text_color = "#ffffff" 
                            
                        ax.text(0.5, 0.33, values[r][c], color=text_color, fontsize=20, 
                                ha='center', va='center', fontproperties=font_bold)

                st.pyplot(fig)
                
                buf = io.BytesIO()
                fmt = format_gambar.lower()
                if fmt == "jpg":
                    fmt = "jpeg" 
                    
                fig.savefig(buf, format=fmt, facecolor=fig.get_facecolor(), edgecolor='none', bbox_inches='tight', dpi=150)
                
                st.markdown("### 📥 Sesi Unduh Gambar Laporan:")
                st.download_button(
                    label=f"📥 Download Dashboard Ringkasan ({format_gambar})",
                    data=buf.getvalue(),
                    file_name=f"{nama_output}.{format_gambar.lower()}",
                    mime=f"image/{format_gambar.lower()}",
                    type="primary",
                    use_container_width=True
                )
    else:
        st.info("💡 Petunjuk: Silakan unggah file mentah Excel (.xlsx) pada Fitur 1 atau lakukan konsolidasi data terlebih dahulu di Halaman 1.")
