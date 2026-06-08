import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import io
from utils import load_poppins_fonts

# ==========================================
# INISIALISASI FONT POPPINS
# ==========================================
def get_fonts():
    font_reg_p, font_bold_p = load_poppins_fonts()
    try:
        font_regular = fm.FontProperties(fname=font_reg_p)
        font_bold = fm.FontProperties(fname=font_bold_p)
    except:
        font_regular = fm.FontProperties(family='sans-serif')
        font_bold = fm.FontProperties(family='sans-serif', weight='bold')
    return font_regular, font_bold

# ==========================================
# GENERATOR GAMBAR: EXECUTIVE SUMMARY
# ==========================================
def generate_executive_summary(df_dashboard, format_gambar):
    font_regular, font_bold = get_fonts()
    
    total_tx = len(df_dashboard)
    
    if 'Time' in df_dashboard.columns:
        dt_combined = pd.to_datetime(df_dashboard['Date'].astype(str) + ' ' + df_dashboard['Time'].astype(str), errors='coerce')
        business_dates = dt_combined - pd.Timedelta(hours=6)
    else:
        business_dates = pd.to_datetime(df_dashboard['Date'], errors='coerce')
    
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

    buf = io.BytesIO()
    fmt = "jpeg" if format_gambar.lower() == "jpg" else format_gambar.lower()
    fig.savefig(buf, format=fmt, facecolor=fig.get_facecolor(), edgecolor='none', bbox_inches='tight', dpi=150)
    return fig, buf

# ==========================================
# GENERATOR GAMBAR: RATA-RATA TRANSAKSI PER JAM
# ==========================================
def generate_hourly_transactions_chart(df_dashboard, format_gambar):
    font_regular, font_bold = get_fonts()
    
    # 1. Hitung jumlah hari kalender bisnis murni
    if 'Time' in df_dashboard.columns:
        dt_combined = pd.to_datetime(df_dashboard['Date'].astype(str) + ' ' + df_dashboard['Time'].astype(str), errors='coerce')
        business_dates = dt_combined - pd.Timedelta(hours=6)
    else:
        dt_combined = pd.to_datetime(df_dashboard['Date'], errors='coerce')
        business_dates = dt_combined
        
    unique_b_dates = pd.to_datetime(business_dates.dt.date.dropna().unique())
    num_days = len(unique_b_dates)
    num_days = 1 if num_days == 0 else num_days
    
    # 2. Ekstrak jam fisik
    df_dashboard['Physical_Hour'] = dt_combined.dt.hour
    
    # 3. Grouping hitung total ID transaksi per jam
    hourly_counts = df_dashboard.groupby('Physical_Hour')['ID'].count().reindex(range(24), fill_value=0)
    
    # 4. Hitung rata-rata jumlah transaksi per jam
    hourly_avg = hourly_counts / num_days
    
    # --- PROSES MENGGAMBAR GRAFIK LINE (RASIO 16:8) ---
    fig, ax = plt.subplots(figsize=(16, 8), facecolor='#0e1117')
    ax.set_facecolor('#1e222b')
    
    # Menggambar Garis Tren Utama
    ax.plot(range(24), hourly_avg.values, marker='o', color='#3b82f6', linewidth=3, markersize=8, label='Rata-rata Transaksi')
    ax.fill_between(range(24), hourly_avg.values, color='#3b82f6', alpha=0.15)
    
    # PENYESUAIAN 2: Menghapus total judul paling atas agar tampilan lebih clean
    # ax.set_title(...) dihapus total
    
    # Konfigurasi Sumbu Grafik
    ax.set_xlabel("Waktu Operasional (Jam)", color='#9ca3af', fontsize=12, fontproperties=font_regular, labelpad=12)
    
    # PENYESUAIAN 1: Menghilangkan akhiran "(ID)" pada label sumbu Y
    ax.set_ylabel("Rata-Rata Jumlah Transaksi", color='#9ca3af', fontsize=12, fontproperties=font_regular, labelpad=12)
    
    # Kustomisasi Sumbu X (00:00 s.d 23:00)
    ax.set_xticks(range(24))
    ax.set_xticklabels([f"{h:02d}:00" for h in range(24)], rotation=0, color='#9ca3af', fontproperties=font_regular, fontsize=10)
    
    # PENYESUAIAN 3: Menambahkan Data Label berbentuk bulat tanpa desimal di setiap titik jam
    # Menghitung offset dinamis di atas titik agar teks tidak menempel pas di bulatan marker
    y_max = max(hourly_avg.values) if max(hourly_avg.values) > 0 else 1
    label_offset = y_max * 0.02
    
    for x, y in zip(range(24), hourly_avg.values):
        ax.text(
            x, 
            y + label_offset, 
            f"{y:.0f}", # Format tanpa desimal (.0f)
            color='#ffffff', 
            fontsize=10, 
            fontproperties=font_bold,
            ha='center', 
            va='bottom'
        )
    
    # Mengatur batas atas sumbu Y sedikit lebih tinggi agar data label teratas tidak terpotong garis tepi
    ax.set_ylim(bottom=0, top=y_max + (label_offset * 4))
    
    # Pengaturan font dan warna penanda angka sumbu Y
    ax.tick_params(colors='#9ca3af', labelsize=10)
    for label in ax.get_yticklabels():
        label.set_fontproperties(font_regular)
        
    # Set warna border card grafik
    for spine in ax.spines.values():
        spine.set_color('#2d323f')
        spine.set_linewidth(1.5)
        
    # Berikan garis kisi-kisi (Grid) yang tipis dan elegan
    ax.grid(True, linestyle='--', alpha=0.1, color='#ffffff')
    
    # --- SIMPAN KE MEMORY SEBAGAI BYTE (SIAP UNDUH) ---
    buf = io.BytesIO()
    fmt = "jpeg" if format_gambar.lower() == "jpg" else format_gambar.lower()
    fig.savefig(buf, format=fmt, facecolor=fig.get_facecolor(), edgecolor='none', bbox_inches='tight', dpi=150)
    
    return fig, buf
