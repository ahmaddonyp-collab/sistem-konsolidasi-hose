import streamlit as st
import pandas as pd
from utils import process_core_data
from charts import generate_executive_summary

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
                    # Pemanggilan core logic dari utils.py
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
                
                # Pemanggilan fungsi visualisasi dari charts.py
                if jenis_analisis == "Executive Summary":
                    fig, buf = generate_executive_summary(df_dashboard, format_gambar)
                    
                    st.pyplot(fig)
                    
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
