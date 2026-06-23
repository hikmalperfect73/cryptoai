"""
auth.py — Logika autentikasi: daftar, login, keluar, dan form UI-nya.

Password TIDAK PERNAH disimpan dalam bentuk asli. Saat daftar, password
diubah jadi hash satu arah dengan bcrypt. Saat login, password yang
diketik diuji terhadap hash tersimpan — bukan dibandingkan langsung.
"""

import bcrypt
import streamlit as st
import db


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')


def cek_password(password: str, password_hash: str) -> bool:
    return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))


def is_logged_in() -> bool:
    return st.session_state.get('user_id') is not None


def login(username: str, password: str) -> tuple[bool, str]:
    """Return (berhasil, pesan)."""
    user = db.get_user_by_username(username)
    if not user:
        return False, "Username belum terdaftar."
    if not cek_password(password, user['password_hash']):
        return False, "Password salah."

    st.session_state['user_id'] = user['id']
    st.session_state['username'] = user['username']
    return True, "Login berhasil."


def daftar(username: str, password: str, konfirmasi: str) -> tuple[bool, str]:
    """Return (berhasil, pesan)."""
    username = username.strip()

    if len(username) < 3:
        return False, "Username minimal 3 karakter."
    if len(password) < 6:
        return False, "Password minimal 6 karakter."
    if password != konfirmasi:
        return False, "Konfirmasi password tidak cocok."
    if db.get_user_by_username(username):
        return False, "Username sudah dipakai, pilih yang lain."

    berhasil = db.create_user(username, hash_password(password))
    if not berhasil:
        return False, "Username sudah dipakai, pilih yang lain."
    return True, "Akun berhasil dibuat! Silakan login."


def logout():
    for key in ('user_id', 'username'):
        st.session_state.pop(key, None)


def tampilkan_form_auth():
    """
    Render halaman Login & Daftar dengan tema "night-city + koin melayang"
    — background dibangun dari CSS/SVG murni (bintang, siluet kota,
    candlestick chart neon, koin BTC/ETH bercahaya), sementara form input
    tetap memakai widget asli Streamlit (st.form, st.text_input, dst) agar
    validasi dan submit tetap berfungsi normal lewat fungsi login()/daftar().

    Dipanggil HANYA ketika belum ada user yang login (is_logged_in() == False).
    """
    st.markdown("""
    <style>
      /* ===================================================================
         BACKGROUND HALAMAN LOGIN — night sky + skyline + koin + candlestick
         Catatan: ini HANYA berlaku selagi form auth ditampilkan, karena
         dirender lewat st.markdown di awal tampilkan_form_auth().
      =================================================================== */
      [data-testid="stAppViewContainer"] > .main {
        background:
          radial-gradient(ellipse 700px 380px at 12% 28%, rgba(247,147,26,0.16), transparent 60%),
          radial-gradient(ellipse 500px 300px at 88% 20%, rgba(98,126,234,0.14), transparent 60%),
          linear-gradient(180deg, #020611 0%, #061229 35%, #0a1c3d 65%, #0d2347 100%) !important;
        background-attachment: fixed !important;
      }

      .auth-stars {
        position: fixed; inset: 0; z-index: 0; pointer-events: none;
        background-image:
          radial-gradient(1px 1px at 8% 12%, white, transparent),
          radial-gradient(1px 1px at 22% 30%, white, transparent),
          radial-gradient(1.5px 1.5px at 35% 8%, white, transparent),
          radial-gradient(1px 1px at 48% 22%, white, transparent),
          radial-gradient(1px 1px at 62% 35%, white, transparent),
          radial-gradient(1.5px 1.5px at 75% 14%, white, transparent),
          radial-gradient(1px 1px at 88% 28%, white, transparent),
          radial-gradient(1px 1px at 95% 10%, white, transparent);
        background-repeat: repeat;
        background-size: 100% 45%;
        opacity: 0.5;
        animation: auth-twinkle 4s ease-in-out infinite alternate;
      }
      @keyframes auth-twinkle { from { opacity: 0.32; } to { opacity: 0.58; } }

      .auth-koin {
        position: fixed; z-index: 0; pointer-events: none;
        display: flex; align-items: center; justify-content: center;
        border-radius: 50%; font-weight: 800; font-family: inherit;
      }
      .auth-koin-btc {
        width: 84px; height: 84px; left: 6%; top: 16%; font-size: 36px;
        color: #fff7e8;
        background: radial-gradient(circle at 35% 30%, #ffc266, #f7931a 55%, #c2740a 100%);
        box-shadow: 0 0 70px 14px rgba(247,147,26,0.5), 0 0 26px 4px rgba(255,200,80,0.55), inset 0 0 16px rgba(255,255,255,0.3);
        animation: auth-float-a 7s ease-in-out infinite;
      }
      .auth-koin-eth {
        width: 60px; height: 60px; right: 8%; top: 12%; font-size: 26px;
        color: #f3f4ff;
        background: radial-gradient(circle at 35% 30%, #8a9bff, #627eea 55%, #3b4dab 100%);
        box-shadow: 0 0 38px 6px rgba(98,126,234,0.45), inset 0 0 12px rgba(255,255,255,0.25);
        animation: auth-float-b 8.5s ease-in-out infinite;
      }
      .auth-koin-btc-2 {
        width: 40px; height: 40px; left: 12%; top: 62%; font-size: 17px;
        color: #fff7e8;
        background: radial-gradient(circle at 35% 30%, #ffc266, #f7931a 55%, #c2740a 100%);
        box-shadow: 0 0 22px 4px rgba(247,147,26,0.4);
        opacity: 0.75;
        animation: auth-float-d 9s ease-in-out infinite;
      }
      .auth-koin-eth-2 {
        width: 34px; height: 34px; right: 14%; top: 56%; font-size: 15px;
        color: #f3f4ff;
        background: radial-gradient(circle at 35% 30%, #8a9bff, #627eea 55%, #3b4dab 100%);
        box-shadow: 0 0 20px 3px rgba(98,126,234,0.4);
        opacity: 0.75;
        animation: auth-float-c 6s ease-in-out infinite;
      }
      @keyframes auth-float-a { 0%,100% { transform: translateY(0) rotate(0deg); } 50% { transform: translateY(-18px) rotate(4deg); } }
      @keyframes auth-float-b { 0%,100% { transform: translateY(0) rotate(0deg); } 50% { transform: translateY(14px) rotate(-5deg); } }
      @keyframes auth-float-c { 0%,100% { transform: translateY(0); } 50% { transform: translateY(-12px); } }
      @keyframes auth-float-d { 0%,100% { transform: translateY(0); } 50% { transform: translateY(13px); } }

      .auth-skyline {
        position: fixed; bottom: 0; left: 0; right: 0; height: 30%; z-index: 0; pointer-events: none;
        background: linear-gradient(180deg, transparent 0%, rgba(2,6,17,0.5) 45%, rgba(2,6,17,0.94) 100%);
      }
      .auth-skyline svg { position:absolute; bottom:0; width:100%; height:100%; }

      .auth-candles {
        position: fixed; top: 0; left: 0; right: 0; height: 55%; z-index: 0; pointer-events: none;
        opacity: 0.3;
        filter: drop-shadow(0 0 6px rgba(56,189,248,0.35));
        animation: auth-chart-pulse 5s ease-in-out infinite alternate;
      }
      @keyframes auth-chart-pulse { from { opacity: 0.2; } to { opacity: 0.36; } }

      /* ===== Card form: bungkus jadi modal melayang dgn backdrop blur ===== */
      .auth-card-wrap [data-testid="stVerticalBlockBorderWrapper"],
      .auth-card-wrap [data-testid="stForm"] {
        background: rgba(10,22,45,0.55) !important;
        backdrop-filter: blur(18px);
        -webkit-backdrop-filter: blur(18px);
        border: 1px solid rgba(125,211,252,0.18) !important;
        border-radius: 22px !important;
        box-shadow: 0 24px 70px rgba(0,0,0,0.5);
      }
      .auth-card-wrap [data-testid="stForm"] label {
        color: #93c5fd !important;
        font-weight: 700 !important;
        font-size: 12.5px !important;
        text-transform: uppercase;
        letter-spacing: 0.03em;
      }
    </style>

    <div class="auth-stars"></div>
    <svg class="auth-candles" viewBox="0 0 1440 350" preserveAspectRatio="none">
      <g stroke="#1d4ed8" stroke-width="1" opacity="0.22">
        <line x1="0" y1="70" x2="1440" y2="70"/>
        <line x1="0" y1="150" x2="1440" y2="150"/>
        <line x1="0" y1="230" x2="1440" y2="230"/>
      </g>
      <g stroke-width="2">
        <line x1="50"  y1="180" x2="50"  y2="250" stroke="#34d399"/>
        <rect x="40"  y="200" width="20" height="35" fill="#34d399"/>
        <line x1="95"  y1="150" x2="95"  y2="220" stroke="#f43f5e"/>
        <rect x="85"  y="160" width="20" height="32" fill="#f43f5e"/>
        <line x1="140" y1="120" x2="140" y2="195" stroke="#34d399"/>
        <rect x="130" y="135" width="20" height="40" fill="#34d399"/>
        <line x1="185" y1="95"  x2="185" y2="170" stroke="#34d399"/>
        <rect x="175" y="105" width="20" height="45" fill="#34d399"/>
        <line x1="230" y1="115" x2="230" y2="185" stroke="#f43f5e"/>
        <rect x="220" y="125" width="20" height="35" fill="#f43f5e"/>
        <line x1="1210" y1="100" x2="1210" y2="175" stroke="#34d399"/>
        <rect x="1200" y="110" width="20" height="42" fill="#34d399"/>
        <line x1="1255" y1="130" x2="1255" y2="200" stroke="#f43f5e"/>
        <rect x="1245" y="140" width="20" height="36" fill="#f43f5e"/>
        <line x1="1300" y1="80"  x2="1300" y2="155" stroke="#34d399"/>
        <rect x="1290" y="90"  width="20" height="44" fill="#34d399"/>
        <line x1="1345" y1="105" x2="1345" y2="180" stroke="#34d399"/>
        <rect x="1335" y="115" width="20" height="40" fill="#34d399"/>
        <line x1="1390" y1="60"  x2="1390" y2="140" stroke="#34d399"/>
        <rect x="1380" y="70"  width="20" height="46" fill="#34d399"/>
      </g>
    </svg>
    <div class="auth-koin auth-koin-btc">₿</div>
    <div class="auth-koin auth-koin-eth">Ξ</div>
    <div class="auth-koin auth-koin-btc-2">₿</div>
    <div class="auth-koin auth-koin-eth-2">Ξ</div>
    <div class="auth-skyline">
      <svg viewBox="0 0 1440 250" preserveAspectRatio="none">
        <g fill="#03101f">
          <rect x="0" y="120" width="70" height="130"/>
          <rect x="80" y="80" width="50" height="170"/>
          <rect x="140" y="140" width="65" height="110"/>
          <rect x="215" y="60" width="44" height="190"/>
          <rect x="270" y="110" width="80" height="140"/>
          <rect x="360" y="35" width="40" height="215"/>
          <rect x="410" y="95" width="68" height="155"/>
          <rect x="490" y="70" width="52" height="180"/>
          <rect x="555" y="130" width="75" height="120"/>
          <rect x="640" y="20" width="36" height="230"/>
          <rect x="685" y="90" width="60" height="160"/>
          <rect x="755" y="120" width="70" height="130"/>
          <rect x="835" y="50" width="46" height="200"/>
          <rect x="890" y="100" width="65" height="150"/>
          <rect x="965" y="70" width="50" height="180"/>
          <rect x="1025" y="135" width="72" height="115"/>
          <rect x="1110" y="30" width="38" height="220"/>
          <rect x="1155" y="95" width="60" height="155"/>
          <rect x="1225" y="125" width="68" height="125"/>
          <rect x="1305" y="65" width="48" height="185"/>
          <rect x="1365" y="105" width="75" height="145"/>
        </g>
        <g fill="#ffce6b" fill-opacity="0.5">
          <rect x="25" y="150" width="6" height="8"/><rect x="95" y="105" width="6" height="8"/>
          <rect x="160" y="175" width="6" height="8"/><rect x="230" y="85" width="6" height="8"/>
          <rect x="290" y="145" width="6" height="8"/><rect x="375" y="60" width="6" height="8"/>
          <rect x="430" y="120" width="6" height="8"/><rect x="505" y="95" width="6" height="8"/>
          <rect x="575" y="160" width="6" height="8"/><rect x="655" y="45" width="6" height="8"/>
          <rect x="775" y="150" width="6" height="8"/><rect x="910" y="125" width="6" height="8"/>
          <rect x="1045" y="165" width="6" height="8"/><rect x="1175" y="115" width="6" height="8"/>
          <rect x="1325" y="90" width="6" height="8"/>
        </g>
      </svg>
    </div>

    <div style='text-align:center; padding:36px 0 8px; position:relative; z-index:2'>
      <div style='width:60px; height:60px;
           background:linear-gradient(135deg,#1d4ed8,#0ea5e9);
           border-radius:16px; display:flex; align-items:center;
           justify-content:center; font-size:28px; margin:0 auto 12px;
           box-shadow:0 8px 24px rgba(29,78,216,0.5)'>₿</div>
      <div style='font-size:24px; font-weight:800; color:#f0f7ff'>Masuk ke CryptoAI</div>
      <div style='font-size:13px; color:rgba(148,180,219,0.85); margin-top:4px'>
        Dashboard prediksi BTC & ETH dengan LSTM
      </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="auth-card-wrap">', unsafe_allow_html=True)
    col_kiri, col_tengah, col_kanan = st.columns([1, 1.2, 1])
    with col_tengah:
        tab_login, tab_daftar = st.tabs(["🔑 Masuk", "📝 Daftar"])

        with tab_login:
            with st.form("form_login"):
                u = st.text_input("Email", key="login_user", placeholder="nama@email.com")
                p = st.text_input("Password", type="password", key="login_pass", placeholder="••••••••")
                submit = st.form_submit_button("Masuk", type="primary", use_container_width=True)
            if submit:
                ok, pesan = login(u, p)
                if ok:
                    st.success(pesan)
                    st.rerun()
                else:
                    st.error(pesan)
            st.markdown(
                "<div style='text-align:center; font-size:12.5px; color:rgba(148,180,219,0.7); margin-top:4px'>"
                "Belum punya akun? Buka tab <b style='color:#7dd3fc'>Daftar</b> di atas.</div>",
                unsafe_allow_html=True
            )

        with tab_daftar:
            with st.form("form_daftar"):
                u = st.text_input("Email", key="daftar_user", placeholder="nama@email.com")
                p = st.text_input("Password", type="password", key="daftar_pass", placeholder="Minimal 6 karakter")
                p2 = st.text_input("Konfirmasi Password", type="password", key="daftar_pass2", placeholder="Ulangi password")
                submit = st.form_submit_button("Buat Akun", type="primary", use_container_width=True)
            if submit:
                ok, pesan = daftar(u, p, p2)
                if ok:
                    st.success(pesan + " Silakan pindah ke tab Masuk.")
                else:
                    st.error(pesan)
    st.markdown('</div>', unsafe_allow_html=True)
