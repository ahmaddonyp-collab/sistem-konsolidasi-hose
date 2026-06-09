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
    
    if 'Time' in df_dashboard.columns:
        dt_combined = pd.to_datetime(df_dashboard['Date'].astype(str) + ' ' + df_dashboard['Time'].astype(str), errors='coerce')
        business_dates = dt_combined - pd.Timedelta(hours=6)
    else:
        dt_combined = pd.to_datetime(df_dashboard['Date'], errors='coerce')
        business_dates = dt_combined
        
    unique_b_dates = pd.to_datetime(business_dates.dt.date.dropna().unique())
    num_days = len(unique_b_dates)
    num_days = 1 if num_days == 0 else num_days
    
    df_dashboard['Physical_Hour'] = dt_combined.dt.hour
    hourly_counts = df_dashboard.groupby('Physical_Hour')['ID'].count().reindex(range(24), fill_value=0)
    hourly_avg = hourly_counts / num_days
    
    fig, ax = plt.subplots(figsize=(16, 8), facecolor='#0e1117')
    ax.set_facecolor('#1e222b')
    
    ax.plot(range(24), hourly_avg.values, marker='o', color='#3b82f6', linewidth=3, markersize=8, label='Rata-rata Transaksi')
    ax.fill_between(range(24), hourly_avg.values, color='#3b82f6', alpha=0.15)
    
    ax.set_xlabel("Waktu Operasional (Jam)", color='#ffffff', fontsize=12, fontproperties=font_regular, labelpad=12) 
    ax.set_ylabel("Rata-Rata Jumlah Transaksi", color='#9ca3af', fontsize=12, fontproperties=font_regular, labelpad=12)
    
    ax.set_xticks(range(24))
    ax.set_xticklabels([f"{h:02d}:00" for h in range(24)], rotation=0, color='#9ca3af', fontproperties=font_regular, fontsize=10)
    
    y_max = max(hourly_avg.values) if max(hourly_avg.values) > 0 else 1
    label_offset = y_max * 0.02
    
    for x, y in zip(range(24), hourly_avg.values):
        ax.text(x, y + label_offset, f"{y:.0f}", color='#ffffff', fontsize=10, fontproperties=font_bold, ha='center', va='bottom')
    
    ax.set_ylim(bottom=0, top=y_max + (label_offset * 4))
    ax.tick_params(colors='#9ca3af', labelsize=10)
    for label in ax.get_yticklabels():
        label.set_fontproperties(font_regular)
        
    for spine in ax.spines.values():
        spine.set_color('#2d323f')
        spine.set_linewidth(1.5)
        
    ax.grid(True, linestyle='--', alpha=0.1, color='#ffffff')
    
    buf = io.BytesIO()
    fmt = "jpeg" if format_gambar.lower() == "jpg" else format_gambar.lower()
    fig.savefig(buf, format=fmt, facecolor=fig.get_facecolor(), edgecolor='none', bbox_inches='tight', dpi=150)
    return fig, buf

# ==========================================
# GENERATOR GAMBAR: RATA-RATA TRANSAKSI PER HARI
# ==========================================
def generate_daily_transactions_chart(df_dashboard, format_gambar):
    font_regular, font_bold = get_fonts()
    
    if 'Time' in df_dashboard.columns:
        dt_combined = pd.to_datetime(df_dashboard['Date'].astype(str) + ' ' + df_dashboard['Time'].astype(str), errors='coerce')
        business_combined = dt_combined - pd.Timedelta(hours=6)
    else:
        dt_combined = pd.to_datetime(df_dashboard['Date'], errors='coerce')
        business_combined = dt_combined
        
    unique_b_dates = pd.Series(business_combined.dt.date.dropna().unique())
    unique_days_of_week = pd.to_datetime(unique_b_dates).dt.dayofweek
    days_occurrence = unique_days_of_week.value_counts().reindex(range(7), fill_value=1)
    days_occurrence = days_occurrence.replace(0, 1) 
    
    df_dashboard['Business_DayofWeek'] = business_combined.dt.dayofweek
    daily_counts = df_dashboard.groupby('Business_DayofWeek')['ID'].count().reindex(range(7), fill_value=0)
    daily_avg = daily_counts / days_occurrence
    
    fig, ax = plt.subplots(figsize=(16, 8), facecolor='#0e1117')
    ax.set_facecolor('#1e222b')
    
    ax.plot(range(7), daily_avg.values, marker='o', color='#f59e0b', linewidth=3, markersize=10, label='Rata-rata Harian')
    ax.fill_between(range(7), daily_avg.values, color='#f59e0b', alpha=0.12)
    
    ax.set_xlabel("Hari Operasional", color='#ffffff', fontsize=12, fontproperties=font_regular, labelpad=12) 
    ax.set_ylabel("Rata-Rata Jumlah Transaksi", color='#9ca3af', fontsize=12, fontproperties=font_regular, labelpad=12)
    
    nama_hari = ['Senin', 'Selasa', 'Rabu', 'Kamis', 'Jumat', 'Sabtu', 'Minggu']
    ax.set_xticks(range(7))
    ax.set_xticklabels(nama_hari, color='#9ca3af', fontproperties=font_regular, fontsize=11)
    
    y_max = max(daily_avg.values) if max(daily_avg.values) > 0 else 1
    label_offset = y_max * 0.02
    
    for x, y in zip(range(7), daily_avg.values):
        ax.text(x, y + label_offset, f"{y:.0f}", color='#ffffff', fontsize=11, fontproperties=font_bold, ha='center', va='bottom')
        
    ax.set_ylim(bottom=0, top=y_max + (label_offset * 4))
    ax.tick_params(colors='#9ca3af', labelsize=10)
    for label in ax.get_yticklabels():
        label.set_fontproperties(font_regular)
        
    for spine in ax.spines.values():
        spine.set_color('#2d323f')
        spine.set_linewidth(1.5)
        
    ax.grid(True, linestyle='--', alpha=0.1, color='#ffffff')
    
    buf = io.BytesIO()
    fmt = "jpeg" if format_gambar.lower() == "jpg" else format_gambar.lower()
    fig.savefig(buf, format=fmt, facecolor=fig.get_facecolor(), edgecolor='none', bbox_inches='tight', dpi=150)
    return fig, buf

# ==========================================
# GENERATOR GAMBAR: SALES MOVEMENT BY MONTH (DUAL AXIS)
# ==========================================
def generate_monthly_movement_chart(df_dashboard, format_gambar):
    font_regular, font_bold = get_fonts()
    
    if 'Time' in df_dashboard.columns:
        dt_combined = pd.to_datetime(df_dashboard['Date'].astype(str) + ' ' + df_dashboard['Time'].astype(str), errors='coerce')
        business_combined = dt_combined - pd.Timedelta(hours=6)
    else:
        business_combined = pd.to_datetime(df_dashboard['Date'], errors='coerce')
    
    df_dashboard['B_Date'] = business_combined.dt.date
    df_dashboard['B_Month'] = business_combined.dt.to_period('M')
    
    list_months = sorted(df_dashboard['B_Month'].unique())
    
    monthly_data = []
    for month in list_months:
        temp_df = df_dashboard[df_dashboard['B_Month'] == month]
        
        unique_days = temp_df['B_Date'].nunique()
        unique_days = 1 if unique_days == 0 else unique_days
        
        avg_val_day = temp_df['Value (Rp.)'].sum() / unique_days
        avg_vol_day = temp_df['Volume (L)'].sum() / unique_days
        
        monthly_data.append({
            'Month_Label': month.strftime('%b %Y'),
            'Avg_Value': avg_val_day,
            'Avg_Volume': avg_vol_day
        })
    
    res_df = pd.DataFrame(monthly_data)
    
    fig, ax1 = plt.subplots(figsize=(16, 8), facecolor='#0e1117')
    ax1.set_facecolor('#1e222b')
    
    # AXIS 1: BAR untuk Sales Value (Rupiah) - Kiri
    color_val = '#8b5cf6' 
    bars = ax1.bar(res_df['Month_Label'], res_df['Avg_Value'] / 1_000_000, 
                   color=color_val, alpha=0.8, width=0.6, label='Avg Daily Sales (Juta Rp)')
    
    # AXIS 2: LINE untuk Sales Volume (Liter) - Kanan
    ax2 = ax1.twinx()
    color_vol = '#f97316' 
    line = ax2.plot(res_df['Month_Label'], res_df['Avg_Volume'], 
                    color=color_vol, marker='o', linewidth=4, markersize=12, 
                    label='Avg Daily Volume (L)')
    
    # KONTRAK UTAMA JUDUL SUMBU X (Putih)
    ax1.set_xlabel("Bulan Operasional", color='#ffffff', fontsize=12, fontproperties=font_regular, labelpad=15)
    
    # FIX TOTAL: Memaksa label teks nama bulan di sumbu X berwarna PUTIH CERNA
    ax1.tick_params(axis='x', colors='#ffffff', labelsize=11)
    
    ax1.set_ylabel("Rata-Rata Penjualan (Juta Rp)", color=color_val, fontsize=12, fontproperties=font_bold, labelpad=15)
    ax1.tick_params(axis='y', labelcolor='#9ca3af', labelsize=11)
    
    ax2.set_ylabel("Rata-Rata Volume (Liter)", color=color_vol, fontsize=12, fontproperties=font_bold, labelpad=15)
    ax2.tick_params(axis='y', labelcolor='#9ca3af', labelsize=11)
    
    # Integrasi Properti Font & Warna pada Sumbu
    for tick in ax1.get_yticklabels(): tick.set_fontproperties(font_regular)
    for tick in ax2.get_yticklabels(): tick.set_fontproperties(font_regular)
    for tick in ax1.get_xticklabels(): 
        tick.set_fontproperties(font_regular)
        tick.set_color('#ffffff') # Double-lock warna putih di sumbu X
    
    # DATA LABEL: Rupiah (Di atas Bar)
    for bar in bars:
        height = bar.get_height()
        ax1.text(bar.get_x() + bar.get_width()/2., height + (height * 0.02),
                 f"{height:,.1f} Jt", ha='center', va='bottom', color='#ffffff', 
                 fontproperties=font_bold, fontsize=11)
                 
    # DATA LABEL: Volume (Di bawah titik garis)
    vol_max = max(res_df['Avg_Volume']) if max(res_df['Avg_Volume']) > 0 else 1
    for i, txt in enumerate(res_df['Avg_Volume']):
        ax2.text(i, txt - (vol_max * 0.04), 
                 f"{txt:,.0f} L", ha='center', va='top', color='#ffffff', 
                 fontproperties=font_bold, fontsize=11, 
                 bbox=dict(facecolor=color_vol, alpha=0.8, edgecolor='none', boxstyle='round,pad=0.4'))

    # Padding batas sumbu Y
    vol_min = min(res_df['Avg_Volume'])
    ax2.set_ylim(bottom=vol_min - (vol_max * 0.1), top=vol_max + (vol_max * 0.1))

    for ax in [ax1, ax2]:
        for spine in ax.spines.values():
            spine.set_color('#2d323f')
            spine.set_linewidth(1.5)
            
    ax1.grid(True, axis='y', linestyle='--', alpha=0.1, color='#ffffff')
    
    buf = io.BytesIO()
    fmt = "jpeg" if format_gambar.lower() == "jpg" else format_gambar.lower()
    fig.savefig(buf, format=fmt, facecolor=fig.get_facecolor(), edgecolor='none', bbox_inches='tight', dpi=150)
    return fig, buf
