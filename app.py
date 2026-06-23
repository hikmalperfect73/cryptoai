import streamlit as st
import pandas as pd
import numpy as np
import pickle
import matplotlib.pyplot as plt
from tensorflow.keras.models import load_model
import os
import yfinance as yf
from datetime import datetime
from sklearn.metrics import mean_absolute_error, r2_score

import db
import auth

# ===== CONFIG =====
st.set_page_config(
    page_title="CryptoAI — Prediksi BTC & ETH",
    page_icon="₿",
    layout="wide"
)

# ===== STYLE BIRU =====
st.markdown("""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;600;700;800&display=swap');

  html, body, [data-testid="stAppViewContainer"] {
    background: linear-gradient(135deg, #020b18 0%, #041428 50%, #020d1f 100%);
    font-family: 'Plus Jakarta Sans', sans-serif;
  }
  .stApp { background: transparent; }

  [data-testid="stSidebar"] {
    background: linear-gradient(180deg, #020e1f 0%, #031524 100%) !important;
    border-right: 1px solid rgba(59,130,246,0.25);
  }

  div[data-testid="metric-container"] {
    background: rgba(59,130,246,0.07);
    border: 1px solid rgba(59,130,246,0.2);
    border-radius: 16px;
    padding: 20px;
  }

  div[data-testid="metric-container"]:hover {
    border-color: rgba(59,130,246,0.5);
    background: rgba(59,130,246,0.12);
    transition: all 0.2s;
  }

  .stButton > button,
  .stFormSubmitButton > button,
  button[kind="formSubmit"],
  button[kind="primaryFormSubmit"] {
    background: linear-gradient(135deg, #1d4ed8, #2563eb) !important;
    color: white !important;
    border: none !important;
    border-radius: 12px !important;
    font-weight: 700 !important;
    box-shadow: 0 4px 14px rgba(29,78,216,0.35) !important;
    transition: all 0.2s !important;
  }
  .stButton > button:hover,
  .stFormSubmitButton > button:hover,
  button[kind="formSubmit"]:hover,
  button[kind="primaryFormSubmit"]:hover {
    box-shadow: 0 6px 20px rgba(29,78,216,0.5) !important;
    transform: translateY(-1px);
  }

  h1, h2, h3 { color: #e0f2fe !important; }
  hr { border-color: rgba(59,130,246,0.15) !important; }
  .stDataFrame { background: rgba(59,130,246,0.05) !important; border-radius: 12px; }

  .stTabs [data-baseweb="tab-list"] {
    background: rgba(59,130,246,0.08);
    border-radius: 12px;
    padding: 4px;
    gap: 4px;
  }
  .stTabs [data-baseweb="tab"] {
    background: transparent;
    color: #93c5fd;
    border-radius: 10px;
    font-weight: 600;
  }
  .stTabs [aria-selected="true"] {
    background: linear-gradient(135deg, #1d4ed8, #0ea5e9) !important;
    color: white !important;
  }

  .stTextInput input, .stNumberInput input {
    background: rgba(59,130,246,0.08) !important;
    color: #e0f2fe !important;
    border: 1px solid rgba(59,130,246,0.2) !important;
    border-radius: 10px !important;
  }
  .stTextInput input:focus, .stNumberInput input:focus {
    border-color: #2563eb !important;
    box-shadow: 0 0 0 2px rgba(37,99,235,0.25) !important;
  }
  .stSelectbox > div > div {
    background: rgba(59,130,246,0.08) !important;
    color: #e0f2fe !important;
    border: 1px solid rgba(59,130,246,0.2) !important;
  }
  .stCaption { color: #475569 !important; }

  /* ===== Form Login/Daftar: bungkus jadi card biru, bukan kotak polos ===== */
  [data-testid="stForm"] {
    background: rgba(59,130,246,0.06);
    border: 1px solid rgba(59,130,246,0.25);
    border-radius: 20px;
    padding: 28px 26px 8px;
    box-shadow: 0 8px 32px rgba(2,11,24,0.4);
  }
  [data-testid="stForm"] label {
    color: #93c5fd !important;
    font-weight: 600 !important;
    font-size: 13px !important;
  }
</style>
""", unsafe_allow_html=True)

# ===== KONFIGURASI KOIN YANG DIDUKUNG =====
KOIN_CONFIG = {
    "BTC": {
        "label": "₿ Bitcoin (BTC)",
        "csv": "data/btc_harian.csv",
        "model_file": "model_btc.keras",
        "scaler_file": "scaler_btc.pkl",
        "ticker": "BTC-USD",
        "simbol": "₿",
    },
    "ETH": {
        "label": "Ξ Ethereum (ETH)",
        "csv": "data/eth_harian.csv",
        "model_file": "model_eth.keras",
        "scaler_file": "scaler_eth.pkl",
        "ticker": "ETH-USD",
        "simbol": "Ξ",
    },
}

# ===== INIT DATABASE =====
try:
    db.init_db()
except Exception as e:
    st.error(
        "⚠️ Gagal terhubung ke database MySQL. Pastikan environment variable "
        "MYSQLHOST, MYSQLUSER, MYSQLPASSWORD, MYSQLDATABASE, MYSQLPORT sudah "
        "diatur dengan benar di Railway (Variables tab pada service ini)."
    )
    st.caption(f"Detail teknis: {e}")
    st.stop()

# ===== GATE LOGIN: hentikan render dashboard jika belum login =====
if not auth.is_logged_in():
    auth.tampilkan_form_auth()
    st.stop()

USER_ID = st.session_state['user_id']
USERNAME = st.session_state['username']

# ===== PILIHAN KOIN AKTIF (disimpan sebagai preferensi per-user) =====
koin_tersimpan = db.get_preferensi(USER_ID, 'koin_aktif', default='BTC')
if koin_tersimpan not in KOIN_CONFIG:
    koin_tersimpan = 'BTC'

if 'koin_aktif' not in st.session_state:
    st.session_state['koin_aktif'] = koin_tersimpan

KOIN = st.session_state['koin_aktif']
cfg = KOIN_CONFIG[KOIN]


# ===== AUTO-UPDATE DATA HARGA =====
def auto_update_data(path_data, ticker):
    """
    Cek apakah data harian sudah up-to-date. Jika data terakhir lebih dari
    1 hari yang lalu, tarik data baru dari yFinance dan gabungkan ke CSV.
    Return: (status: str, jumlah_baris_baru: int)
    """
    df_cek = pd.read_csv(path_data)
    tanggal_terakhir = pd.to_datetime(df_cek['Date'].iloc[-1])
    hari_ini = datetime.now()

    if (hari_ini - tanggal_terakhir).days <= 1:
        return "up_to_date", 0

    try:
        # start = H+1 dari tanggal terakhir (hindari tarik ulang baris yang
        # sudah ada). end = besok, karena parameter `end` di yfinance itu
        # EKSKLUSIF — tanpa +1 hari, data hari ini sendiri tidak ikut tertarik.
        tanggal_mulai = tanggal_terakhir + pd.Timedelta(days=1)
        tanggal_akhir = hari_ini + pd.Timedelta(days=1)

        btc_baru = yf.download(
            ticker,
            start=str(tanggal_mulai.date()),
            end=str(tanggal_akhir.date()),
            auto_adjust=True,
            progress=False
        )
    except Exception:
        return "gagal_fetch", 0

    if len(btc_baru) == 0:
        return "tidak_ada_data_baru", 0

    if isinstance(btc_baru.columns, pd.MultiIndex):
        btc_baru.columns = btc_baru.columns.get_level_values(0)

    btc_baru = btc_baru[['Open', 'High', 'Low', 'Close', 'Volume']].copy()
    btc_baru.index.name = 'Date'
    btc_baru = btc_baru.reset_index()
    btc_baru['Date'] = pd.to_datetime(btc_baru['Date']).dt.strftime('%Y-%m-%d')

    df_gabung = pd.concat([df_cek, btc_baru], ignore_index=True)
    df_gabung = df_gabung.dropna(subset=['Date', 'Close']).drop_duplicates(subset='Date')
    df_gabung = df_gabung.sort_values('Date').reset_index(drop=True)

    baris_sebelum = len(df_cek)
    df_gabung.to_csv(path_data, index=False)
    baris_baru = len(df_gabung) - baris_sebelum

    if baris_baru == 0:
        return "tidak_ada_data_baru", 0

    return "berhasil", baris_baru


status_update, jumlah_baru = auto_update_data(cfg["csv"], cfg["ticker"])


# ===== LOAD MODEL & EVALUASI =====
def hitung_evaluasi(model, scaler, df, lookback=60):
    """
    Hitung ulang MAE & R2 dari 20% data terakhir (data test), persis
    seperti skema split di train.py, supaya metrik di dashboard selalu
    sinkron dengan model yang sedang dipakai (tidak perlu update manual).
    """
    harga = df['Close'].values.reshape(-1, 1)
    harga_scaled = scaler.transform(harga)

    X, y = [], []
    for i in range(lookback, len(harga_scaled)):
        X.append(harga_scaled[i - lookback:i, 0])
        y.append(harga_scaled[i, 0])
    X, y = np.array(X), np.array(y)
    X = X.reshape(X.shape[0], X.shape[1], 1)

    split = int(len(X) * 0.8)
    X_test, y_test = X[split:], y[split:]

    if len(X_test) == 0:
        return None, None

    y_pred_scaled = model.predict(X_test, verbose=0)
    y_pred = scaler.inverse_transform(y_pred_scaled)
    y_actual = scaler.inverse_transform(y_test.reshape(-1, 1))

    mae = mean_absolute_error(y_actual, y_pred)
    r2 = r2_score(y_actual, y_pred)
    return mae, r2


@st.cache_resource
def load_everything(koin):
    cfg_lokal = KOIN_CONFIG[koin]
    model = load_model(cfg_lokal["model_file"])
    with open(cfg_lokal["scaler_file"], 'rb') as f:
        scaler = pickle.load(f)
    df = pd.read_csv(cfg_lokal["csv"])
    mae, r2 = hitung_evaluasi(model, scaler, df)
    return model, scaler, df, mae, r2


def prediksi(model, scaler, df, hari=7):
    harga = df['Close'].values[-60:].reshape(-1, 1)
    scaled = scaler.transform(harga)
    hasil = []
    seq = scaled.copy()
    for _ in range(hari):
        X = seq[-60:].reshape(1, 60, 1)
        p = model.predict(X, verbose=0)
        hasil.append(p[0][0])
        seq = np.append(seq, p, axis=0)
    return scaler.inverse_transform(np.array(hasil).reshape(-1, 1)).flatten()


model, scaler, df, mae_model, r2_model = load_everything(KOIN)
r2_pct = f"{r2_model*100:.1f}%" if r2_model is not None else "N/A"

harga_terakhir = df['Close'].iloc[-1]
harga_kemarin  = df['Close'].iloc[-2]
perubahan      = ((harga_terakhir - harga_kemarin) / harga_kemarin) * 100
pred           = prediksi(model, scaler, df, 7)
chg7           = ((pred[6] - harga_terakhir) / harga_terakhir) * 100
last_date      = df['Date'].iloc[-1] if 'Date' in df.columns else ''
tahun_akhir    = last_date[:4] if last_date else "2026"

# Sinyal
if chg7 > 5:
    sinyal = "⚡ STRONG BUY"; warna_s = "#10b981"; warna_bg = "rgba(16,185,129,0.12)"
elif chg7 > 1:
    sinyal = "🟢 BUY"; warna_s = "#34d399"; warna_bg = "rgba(52,211,153,0.08)"
elif chg7 < -5:
    sinyal = "🔴 STRONG SELL"; warna_s = "#f43f5e"; warna_bg = "rgba(244,63,94,0.12)"
elif chg7 < -1:
    sinyal = "🟠 SELL"; warna_s = "#fb923c"; warna_bg = "rgba(251,146,60,0.08)"
else:
    sinyal = "⚪ HOLD"; warna_s = "#fbbf24"; warna_bg = "rgba(251,191,36,0.08)"

# ===== SIDEBAR =====
with st.sidebar:
    st.markdown(f"""
    <div style='text-align:center; padding:20px 0 10px'>
      <div style='width:56px; height:56px;
           background:linear-gradient(135deg,#1d4ed8,#0ea5e9);
           border-radius:16px; display:flex;
           align-items:center; justify-content:center;
           font-size:28px; margin:0 auto 12px;
           box-shadow:0 4px 20px rgba(59,130,246,0.4)'>{cfg['simbol']}</div>
      <div style='font-size:18px; font-weight:800; color:#e0f2fe'>CryptoAI</div>
      <div style='font-size:12px; color:#475569'>Prediksi {KOIN} dengan LSTM</div>
    </div>
    """, unsafe_allow_html=True)

    # ===== INFO AKUN & TOMBOL LOGOUT =====
    st.markdown(f"""
    <div style='background:rgba(59,130,246,0.08); border:1px solid rgba(59,130,246,0.2);
         border-radius:12px; padding:10px 14px; margin-bottom:6px;
         display:flex; align-items:center; gap:8px'>
      <span style='font-size:18px'>👤</span>
      <span style='color:#e0f2fe; font-size:13px; font-weight:600'>{USERNAME}</span>
    </div>
    """, unsafe_allow_html=True)
    if st.button("🚪 Keluar", use_container_width=True):
        auth.logout()
        st.rerun()

    st.divider()

    # ===== SWITCH KOIN BTC/ETH =====
    st.markdown("**🪙 Pilih Koin**")
    pilihan = st.selectbox(
        "Koin yang dianalisis",
        options=list(KOIN_CONFIG.keys()),
        index=list(KOIN_CONFIG.keys()).index(KOIN),
        format_func=lambda k: KOIN_CONFIG[k]["label"],
        label_visibility="collapsed",
    )
    if pilihan != KOIN:
        st.session_state['koin_aktif'] = pilihan
        db.set_preferensi(USER_ID, 'koin_aktif', pilihan)
        st.rerun()

    st.divider()
    st.markdown("**📊 Data Real-time**")
    st.metric(f"Harga {KOIN}", f"${harga_terakhir:,.0f}", f"{perubahan:+.2f}%")
    st.metric("Prediksi Besok", f"${pred[0]:,.0f}",
              f"{((pred[0]-harga_terakhir)/harga_terakhir*100):+.2f}%")

    if status_update == "berhasil":
        st.caption(f"🔄 Data diperbarui · +{jumlah_baru} baris baru")
    elif status_update == "gagal_fetch":
        st.caption("⚠️ Gagal ambil data terbaru dari yFinance")
    elif status_update == "tidak_ada_data_baru":
        st.caption("ℹ️ Tidak ada data baru tersedia")
    else:
        st.caption("✅ Data sudah terbaru")

    st.divider()
    st.markdown(f"""
    <div style='background:rgba(59,130,246,0.08);
         border:1px solid rgba(59,130,246,0.2);
         border-radius:12px; padding:14px'>
      <div style='font-size:11px; color:#475569;
           text-transform:uppercase; letter-spacing:0.1em;
           margin-bottom:8px'>AI Signal</div>
      <div style='font-size:20px; font-weight:800;
           color:{warna_s}'>{sinyal}</div>
      <div style='font-size:12px; color:#475569;
           margin-top:4px'>7 hari: {chg7:+.2f}%</div>
    </div>
    """, unsafe_allow_html=True)

    st.divider()
    st.markdown(f"""
    <div style='font-size:12px; color:#475569'>
      <b style='color:#93c5fd'>Koin:</b> {KOIN}<br>
      <b style='color:#93c5fd'>Model:</b> LSTM<br>
      <b style='color:#93c5fd'>Dataset:</b> 2017–{tahun_akhir}<br>
      <b style='color:#93c5fd'>R² Score:</b> {r2_pct}<br>
      <b style='color:#93c5fd'>Data terakhir:</b> {last_date}
    </div>
    """, unsafe_allow_html=True)

# ===== HEADER =====
st.markdown(f"""
<div style='background:linear-gradient(135deg,
     rgba(29,78,216,0.25), rgba(14,165,233,0.2), rgba(59,130,246,0.15));
     border:1px solid rgba(59,130,246,0.35);
     border-radius:24px; padding:32px; margin-bottom:24px;
     position:relative; overflow:hidden;
     box-shadow:0 8px 32px rgba(29,78,216,0.2)'>
  <div style='position:absolute; top:-60px; right:-60px;
       width:250px; height:250px; border-radius:50%;
       background:radial-gradient(circle,
       rgba(14,165,233,0.15), transparent)'></div>
  <div style='position:absolute; bottom:-40px; left:-40px;
       width:180px; height:180px; border-radius:50%;
       background:radial-gradient(circle,
       rgba(29,78,216,0.12), transparent)'></div>
  <div style='font-size:13px; font-weight:700; color:#38bdf8;
       letter-spacing:0.12em; text-transform:uppercase;
       margin-bottom:8px'>⚡ Live AI Trading Dashboard</div>
  <h1 style='font-size:36px; font-weight:800; margin:0 0 8px;
       background:linear-gradient(135deg,#e0f2fe,#7dd3fc);
       -webkit-background-clip:text;
       -webkit-text-fill-color:transparent'>
    {cfg['simbol']} CryptoAI — Prediksi Harga {KOIN}
  </h1>
  <p style='color:#7dd3fc; margin:0; font-size:15px'>
    Model LSTM · Dataset 2017–{tahun_akhir} · Data terakhir: {last_date}
  </p>
</div>
""", unsafe_allow_html=True)

# ===== METRICS =====
c1, c2, c3, c4 = st.columns(4)
c1.metric("💰 Harga Terakhir",  f"${harga_terakhir:,.0f}", f"{perubahan:+.2f}%")
c2.metric("🔮 Prediksi Besok",  f"${pred[0]:,.0f}",
          f"{((pred[0]-harga_terakhir)/harga_terakhir*100):+.2f}%")
c3.metric("📈 Harga Tertinggi", f"${df['High'].max():,.0f}")
c4.metric("📉 Harga Terendah",  f"${df['Low'].min():,.0f}")

st.divider()

# ===== TABS =====
tab1, tab2, tab3 = st.tabs([
    "📊 Grafik & Prediksi",
    "🔔 Sinyal Trading",
    "📝 Jurnal Trading"
])

# ========== TAB 1 ==========
with tab1:
    col1, col2 = st.columns([2, 1])

    with col1:
        st.subheader(f"📈 Grafik Harga + Prediksi LSTM — {KOIN}")
        fig, ax = plt.subplots(figsize=(12, 5))
        fig.patch.set_facecolor('#020b18')
        ax.set_facecolor('#020b18')

        hist = df['Close'].tail(90).values
        ax.plot(hist, color='#38bdf8', linewidth=2.5, label='Historis')
        ax.fill_between(range(len(hist)), hist, hist.min(),
                        alpha=0.12, color='#38bdf8')

        x_pred = range(len(hist)-1, len(hist)-1+len(pred))
        ax.plot(list(x_pred), pred,
                color='#10b981', linewidth=2.5,
                linestyle='--', marker='o', markersize=7,
                label='Prediksi LSTM',
                markerfacecolor='#34d399',
                markeredgecolor='white', markeredgewidth=1.5)
        ax.fill_between(list(x_pred), pred*0.95, pred*1.05,
                        alpha=0.12, color='#10b981')

        ax.tick_params(colors='#475569')
        for sp in ax.spines.values():
            sp.set_color('#0c1f35')
        ax.set_ylabel('Harga (USD)', color='#475569')
        ax.legend(facecolor='#020b18', labelcolor='#e0f2fe',
                  fontsize=11, framealpha=0.8)
        ax.grid(axis='y', color='#0c1f35', linewidth=0.7)
        ax.grid(axis='x', color='#0c1f35', linewidth=0.3)
        st.pyplot(fig)

    with col2:
        st.subheader("🔮 Detail Prediksi")
        colors = ['#38bdf8','#60a5fa','#818cf8',
                  '#a78bfa','#c084fc','#e879f9','#f472b6']
        for i, p in enumerate(pred):
            chg = ((p - harga_terakhir) / harga_terakhir) * 100
            c = colors[i]
            st.markdown(f"""
            <div style='background:rgba(59,130,246,0.06);
                 border:1px solid {c}44;
                 border-left:3px solid {c};
                 border-radius:12px; padding:12px 16px;
                 margin-bottom:8px'>
              <div style='display:flex; justify-content:space-between'>
                <span style='color:#93c5fd; font-size:12px;
                  font-weight:600'>Hari +{i+1}</span>
                <span style='color:{"#10b981" if chg>=0 else "#f43f5e"};
                  font-weight:700; font-size:13px'>
                  {"▲" if chg>=0 else "▼"} {chg:+.2f}%
                </span>
              </div>
              <div style='font-size:22px; font-weight:800;
                color:#e0f2fe; margin-top:4px'>${p:,.0f}</div>
            </div>
            """, unsafe_allow_html=True)

# ========== TAB 2 ==========
with tab2:
    st.subheader(f"🔔 Sinyal Trading AI — {KOIN}")
    st.markdown(f"""
    <div style='background:{warna_bg};
         border:2px solid {warna_s}55;
         border-radius:20px; padding:36px;
         text-align:center; margin-bottom:24px'>
      <div style='font-size:12px; font-weight:700;
           color:#475569; letter-spacing:0.14em;
           text-transform:uppercase; margin-bottom:12px'>
        REKOMENDASI AI — 7 HARI KE DEPAN
      </div>
      <div style='font-size:52px; font-weight:800;
           color:{warna_s}; margin-bottom:8px'>{sinyal}</div>
      <div style='font-size:15px; color:#93c5fd'>
        Perubahan 7 hari: <b style='color:{warna_s}'>{chg7:+.2f}%</b>
        &nbsp;|&nbsp; Confidence: {r2_pct}
      </div>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)

    with col1:
        tren_7  = df['Close'].tail(7).mean()
        tren_30 = df['Close'].tail(30).mean()
        st.markdown("""
        <div style='background:rgba(59,130,246,0.08);
             border:1px solid rgba(59,130,246,0.2);
             border-radius:16px; padding:16px; margin-bottom:8px'>
          <div style='font-size:13px; font-weight:700;
               color:#60a5fa'>📊 Analisis Tren</div>
        </div>
        """, unsafe_allow_html=True)
        if tren_7 > tren_30:
            st.success("MA7 > MA30 → **UPTREND** 📈")
        else:
            st.error("MA7 < MA30 → **DOWNTREND** 📉")
        st.metric("MA 7 Hari",  f"${tren_7:,.0f}")
        st.metric("MA 30 Hari", f"${tren_30:,.0f}")

    with col2:
        vol     = df['Close'].tail(30).std()
        vol_pct = (vol / harga_terakhir) * 100
        st.markdown("""
        <div style='background:rgba(251,191,36,0.08);
             border:1px solid rgba(251,191,36,0.2);
             border-radius:16px; padding:16px; margin-bottom:8px'>
          <div style='font-size:13px; font-weight:700;
               color:#fbbf24'>💹 Volatilitas</div>
        </div>
        """, unsafe_allow_html=True)
        if vol_pct > 5:
            st.warning(f"Volatilitas **TINGGI**: {vol_pct:.1f}%")
        else:
            st.success(f"Volatilitas **RENDAH**: {vol_pct:.1f}%")
        st.metric("Std Deviasi 30H", f"${vol:,.0f}")
        st.metric("Volatilitas %",   f"{vol_pct:.2f}%")

    with col3:
        target_beli = harga_terakhir * 0.97
        target_jual = pred[2]
        stop_loss   = harga_terakhir * 0.95
        st.markdown("""
        <div style='background:rgba(16,185,129,0.08);
             border:1px solid rgba(16,185,129,0.2);
             border-radius:16px; padding:16px; margin-bottom:8px'>
          <div style='font-size:13px; font-weight:700;
               color:#10b981'>🎯 Target Harga</div>
        </div>
        """, unsafe_allow_html=True)
        st.metric("🟢 Target Beli",  f"${target_beli:,.0f}")
        st.metric("🎯 Target Jual",  f"${target_jual:,.0f}")
        st.metric("🛑 Stop Loss",    f"${stop_loss:,.0f}",
                  "-5%", delta_color="inverse")

    st.divider()
    st.warning("⚠️ Sinyal hanya untuk keperluan skripsi, bukan saran investasi!")

# ========== TAB 3 — JURNAL (per-user, per-koin, lewat MySQL) ==========
with tab3:
    st.subheader(f"📝 Jurnal Trading — {KOIN}")
    st.caption(
        f"Jurnal ini khusus milik akun **{USERNAME}** untuk koin **{KOIN}** — "
        f"tidak terlihat oleh pengguna lain, dan terpisah dari jurnal koin lainnya."
    )

    df_jurnal = pd.DataFrame(db.get_jurnal(USER_ID, koin=KOIN))

    with st.expander("➕ Tambah Catatan Trading", expanded=True):
        col1, col2 = st.columns(2)
        with col1:
            tgl    = st.date_input("📅 Tanggal")
            jenis  = st.selectbox("📌 Jenis", ["BUY", "SELL"])
            h_beli = st.number_input("💵 Harga Beli ($)",
                                      value=float(harga_terakhir), step=100.0)
        with col2:
            h_jual  = st.number_input("💰 Harga Jual ($)",
                                       value=float(pred[0]), step=100.0)
            jumlah  = st.number_input(f"{cfg['simbol']} Jumlah {KOIN}",
                                       value=0.01, step=0.001, format="%.4f")
            catatan = st.text_input("📝 Catatan")

        pl     = (h_jual - h_beli) * jumlah
        pl_pct = ((h_jual - h_beli) / h_beli * 100)

        st.markdown(f"""
        <div style='background:{"rgba(16,185,129,0.1)" if pl>=0 else "rgba(244,63,94,0.1)"};
             border:1px solid {"rgba(16,185,129,0.3)" if pl>=0 else "rgba(244,63,94,0.3)"};
             border-radius:12px; padding:16px; text-align:center'>
          <div style='font-size:12px; color:#475569'>Estimasi Profit/Loss</div>
          <div style='font-size:28px; font-weight:800;
               color:{"#10b981" if pl>=0 else "#f43f5e"}'>
            {"+" if pl>=0 else ""}${pl:,.2f}
          </div>
          <div style='font-size:13px;
               color:{"#10b981" if pl>=0 else "#f43f5e"}'>{pl_pct:+.2f}%</div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("💾 Simpan ke Jurnal", type="primary", use_container_width=True):
            db.tambah_jurnal(
                USER_ID, KOIN, str(tgl), jenis, h_beli, h_jual, jumlah, round(pl, 2), catatan
            )
            st.success("✅ Berhasil disimpan!")
            st.rerun()

    if len(df_jurnal) > 0:
        st.divider()
        st.subheader("📋 Riwayat Trading")
        total_profit = df_jurnal['profit_loss'].sum()
        total_trade  = len(df_jurnal)
        win_trade    = len(df_jurnal[df_jurnal['profit_loss'] > 0])
        winrate      = (win_trade/total_trade*100) if total_trade > 0 else 0

        c1,c2,c3,c4 = st.columns(4)
        c1.metric("💰 Total P/L",    f"${total_profit:,.2f}")
        c2.metric("📊 Total Trade",  total_trade)
        c3.metric("🏆 Win Rate",     f"{winrate:.1f}%")
        c4.metric("✅ Profit Trade", win_trade)

        kolom_tampil = ['tanggal','koin','jenis','harga_beli','harga_jual','jumlah_koin','profit_loss','catatan']
        st.dataframe(df_jurnal[kolom_tampil], use_container_width=True)

        col1, col2 = st.columns(2)
        with col1:
            csv = df_jurnal[kolom_tampil].to_csv(index=False)
            st.download_button("⬇️ Download Jurnal CSV", csv,
                               f"jurnal_{KOIN}_{USERNAME}.csv", "text/csv",
                               use_container_width=True)
        with col2:
            if st.button("🗑️ Hapus Semua", use_container_width=True):
                db.hapus_semua_jurnal(USER_ID, koin=KOIN)
                st.rerun()
    else:
        st.info(f"📭 Belum ada catatan untuk {KOIN}. Tambahkan di atas!")

st.divider()
st.markdown(f"""
<div style='display:flex; justify-content:space-between; align-items:center;
     padding:16px 0; border-top:1px solid rgba(59,130,246,0.15)'>
  <div style='font-size:12px; color:#475569'>
    ⚠️ Aplikasi ini untuk keperluan skripsi saja, bukan saran investasi.
  </div>
  <div style='font-size:13px; font-weight:700;
       background:linear-gradient(135deg,#38bdf8,#818cf8);
       -webkit-background-clip:text; -webkit-text-fill-color:transparent'>
    ₿ CryptoAI · Dibuat oleh Hikmal Herdiansyah · {tahun_akhir}
  </div>
</div>
""", unsafe_allow_html=True)
