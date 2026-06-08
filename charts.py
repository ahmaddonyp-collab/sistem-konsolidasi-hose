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
    
    # --- KALKULASI INTERNAL METRIK OPERASIONAL ---
    total_tx = len(df_dashboard)
    
    # Trik "Business Date" untuk membunuh jebakan tumpahan shift 05:59 pagi
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

    # --- SIMPAN KE MEMORY SEBAGAI BYTE (SIAP UNDUH) ---
    buf = io.BytesIO()
    fmt = "jpeg" if format_gambar.lower() == "jpg" else format_gambar.lower()
        
    fig.savefig(buf, format=fmt, facecolor=fig.get_facecolor(), edgecolor='none', bbox_inches='tight', dpi=150)
    
    return fig, buf