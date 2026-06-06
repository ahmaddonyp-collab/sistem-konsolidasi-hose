import streamlit as st
import pandas as pd
import numpy as np

# ==========================================
# 1. KONFIGURASI HALAMAN STREAMLIT (UNIVERSAL)
# ==========================================
st.set_page_config(
    page_title="Sistem Konsolidasi Data Hose Delivery",
    page_icon="⛽",
    layout="wide"
)

st.title("⛽ Sistem Konsolidasi Data Hose Delivery")
st.markdown("Aplikasi web universal untuk membersihkan, merapikan, dan mengonsolidasikan banyak file laporan mentah HOSE Delivery Excel (.xlsx) menjadi satu file Master CSV.")
st.markdown("---")

# ==========================================
# 2. ANTARMUKA PENGGUNA (GRID MULTI-SECTION 2x2)
# ==========================================

# BARIS PERTAMA: UNGGAH FILE & NAMA OUTPUT
row1_col1, row1_col2 = st.columns(2)

with row1_col1:
    st.markdown("### 📋 Unggah File Mentah Excel")
    uploaded_files = st.file_uploader(
        "Pilih dan unggah satu atau beberapa file laporan (.xlsx)", 
        type=['xlsx'], 
        accept_multiple_files=True,
        key="uploader_master"
    )

with row1_col2:
    st.markdown("### 💾 Nama File Output")
    nama_output = st.text_input(
        "Tentukan nama file hasil ekspor akhir", 
        value="HOSE_Master_Consolidated",
        key="output_master"
    )
    st.caption("Format otomatis berupa .csv (tidak perlu menuliskan '.csv' di kolom)")

st.markdown("---")

# BARIS KEDUA: FILTER TANGGAL & FILTER PUMP TEST
row2_col1, row2_col2 = st.columns(2)

with row2_col1:
    st.markdown("### 📅 Filter Tanggal Operasional")
    use_filter = st.checkbox("Aktifkan Batasan Tanggal Operasional", value=False)
    
    if use_filter:
        col_start, col_end = st.columns(2)
        with col_start:
            start_date = st.date_input("Tanggal Awal:")
        with col_end:
            end_date = st.date_input("Tanggal Akhir:")
        st.caption("ℹ️ *Logika 3 Shift otomatis menjaga transaksi transisi pukul 00:00 - 05:59 WIB tetap masuk ke hari operasional sebelumnya.*")

with row2_col2:
    st.markdown("### 🧪 Filter Transaksi Pump Test")
    use_pump_test_filter = st.checkbox(
        "Eliminasi Transaksi Pump Test / Tera Pompa", 
        value=False,
        help="Centang untuk membuang transaksi uji coba mesin agar mendapatkan data murni penjualan riil ke konsumen."
    )

st.markdown("---")

# ==========================================
# 3. LOGIKA EKSEKUSI DATA
# ==========================================
if uploaded_files:
    if use_filter and start_date > end_date:
        st.error("❌ Kesalahan: Tanggal Awal tidak boleh melewati Tanggal Akhir!")
    else:
        if st.button("🚀 Mulai Konsolidasi Data", type="primary", use_container_width=True):
            
            with st.spinner('Sedang mengolah dan menyatukan seluruh data laporan...'):
                
                # --- LANGKAH A: KONSOLIDASI FILE MENTAH ---
                list_raw_df = []
                for file in uploaded_files:
                    try:
                        raw_df = pd.read_excel(file)
                        list_raw_df.append(raw_df)
                    except Exception as e:
                        st.error(f"Gagal membaca file {file.name}: {e}")
                
                if list_raw_df:
                    df = pd.concat(list_raw_df, ignore_index=True)
                    
                    # --- LANGKAH B: PEMBERSIHAN AWAL ---
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

                    # --- LANGKAH C: FITUR FILTER TANGGAL OPERASIONAL ---
                    if 'Date' in df.columns:
                        df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
                        
                        if use_filter:
                            batas_awal = pd.to_datetime(start_date) + pd.Timedelta(hours=6)
                            batas_akhir = pd.to_datetime(end_date) + pd.Timedelta(days=1, hours=6)
                            df = df[(df['Date'] >= batas_awal) & (df['Date'] < batas_akhir)]

                    # --- LANGKAH D: KONDISI DATASET KOSONG ---
                    if df.empty:
                        st.warning("⚠️ Data kosong. Tidak ada transaksi yang lolos kriteria filter operasional yang ditentukan.")
                    else:
                        if 'ID' in df.columns:
                            df = df.drop_duplicates(subset=['ID'], keep='first')

                        # --- LANGKAH E: RE-LAYOUT & TRANSFORMASI ---
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

                        # --- LANGKAH F: FILTER PUMP TEST ---
                        if use_pump_test_filter and 'Payment_Method' in df.columns:
                            df = df[~df['Payment_Method'].astype(str).str.upper().str.strip().isin(['PUMP', 'PUMP_TEST', 'PUMPTEST'])]

                        df = df.sort_values(by=['Date', 'Time']).reset_index(drop=True)

                        # --- LANGKAH G: PENYUSUNAN STRUKTUR KOLOM AKHIR ---
                        urutan_kolom_final = [
                            'ID', 'Date', 'Time', 'Shift', 
                            'Pump', 'Hose', 'Product', 
                            'Price', 'Volume (L)', 'Value (Rp.)', 
                            'Payment_Method', 'License_Plate'
                        ]
                        df_final = df[[col for col in urutan_kolom_final if col in df.columns]]

                        # --- LANGKAH H: ANTARMUKA UNDUHAN (DOWNLOAD SECTION) ---
                        st.success(f"🎉 Sukses Konsolidasi! Sebanyak **{len(df_final):,} baris data transaksi** siap diunduh.")
                        
                        st.markdown("### 📊 Preview Data Master Hasil Konsolidasi:")
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
    st.info("💡 Petunjuk: Silakan unggah minimal satu file mentah laporan Excel (.xlsx) di atas untuk mengaktifkan sistem.")